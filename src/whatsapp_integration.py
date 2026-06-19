"""
WhatsApp Integration - Queue-Based (Conflict-Free)
Drops message requests into a queue folder for the persistent watcher to process.
"""
import json
import time
from pathlib import Path
from datetime import datetime
import re

QUEUE_DIR = Path('data/whatsapp_outbound')
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

def send_whatsapp(phone: str, message: str, contact_name: str = None) -> dict:
    """
    Queue a WhatsApp message for the background controller to send.
    """
    task_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    task_file = QUEUE_DIR / f"{task_id}.json"
    
    # Clean data
    if phone:
        phone = re.sub(r'\D', '', str(phone))
    
    task_data = {
        'id': task_id,
        'phone': phone,
        'contact_name': contact_name,
        'message': message,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    try:
        # Drop the request into the queue
        task_file.write_text(json.dumps(task_data, indent=2), encoding='utf-8')
        print(f"[INFO] Message queued: {task_id} (Target: {contact_name or phone})")
        
        # Wait for status update (max 60 seconds)
        print(f"[INFO] Waiting for WhatsApp Controller to process...")
        start_time = time.time()
        while time.time() - start_time < 60:
            if task_file.exists():
                try:
                    current_data = json.loads(task_file.read_text(encoding='utf-8'))
                    status = current_data.get('status')
                    if status == 'sent':
                        return {'success': True, 'message': f'Sent to {contact_name or phone}'}
                    if status == 'failed':
                        return {'success': False, 'error': current_data.get('error', 'Unknown failure')}
                except:
                    pass
            else:
                # File might have been moved to a "processed" folder
                return {'success': True, 'message': f'Task {task_id} processed'}
                
            time.sleep(1)
            
        return {'success': False, 'error': 'WhatsApp watcher is not running. Start it from the dashboard first.'}
        
    except Exception as e:
        return {'success': False, 'error': f"Queue error: {str(e)}"}

def execute_whatsapp_task(content, task_file):
    """Execute WhatsApp task - extracts details and queues for sending"""
    # Extract phone from table
    phone_match = re.search(r'\|\s*customer_phone\s*\|\s*([^\|]+)\s*\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract contact name
    name_match = re.search(r'\|\s*customer_name\s*\|\s*([^\|]+)\s*\|', content)
    contact_name = name_match.group(1).strip() if name_match else None
    
    if not contact_name:
        from_match = re.search(r'\|\s*from\s*\|\s*([^\|]+)\s*\|', content)
        contact_name = from_match.group(1).strip() if from_match else None

    # Extract message
    message = None
    # Check multiple patterns for message content
    patterns = [
        r"\*\*Intent:\*\*.*?with content ['\"](.+?)['\"]",
        r'\|\s*suggested_reply\s*\|\s*([^\|]+)\s*\|',
        r'\|\s*message_content\s*\|\s*([^\|]+)\s*\|'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            message = match.group(1).strip()
            break

    if message:
        message = message.replace('**', '').replace('*', '').strip()
        if (message.startswith("'") and message.endswith("'")) or \
           (message.startswith('"') and message.endswith('"')):
            message = message[1:-1]

    if not contact_name and not phone:
        return {'success': False, 'error': 'Missing contact name or phone'}
    if not message:
        return {'success': False, 'error': 'Missing message content'}

    return send_whatsapp(phone, message, contact_name)
