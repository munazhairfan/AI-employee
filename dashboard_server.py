"""
AI Employee Vault - Unified Dashboard Server
Single server that handles:
- Web dashboard
- Intent analysis
- Task orchestration
- Watcher management

Run: python dashboard_server.py
Access: http://localhost:3000
"""

import os
import json
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
from urllib.parse import urlparse, parse_qs
import subprocess
import sys

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from intent_analyzer import analyze_intent, create_task_file, DROP_FOLDER, NEEDS_ACTION
from ai_agent import get_model_info
from odoo_integration import execute_approved_task, extract_field
from email_integration import execute_email_task, send_gmail_email
from linkedin_integration import execute_linkedin_task, post_to_linkedin
from whatsapp_integration import execute_whatsapp_task, send_whatsapp

# Configuration
import socket

def find_free_port():
    """Find an available port"""
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# Try port 3000 first, if busy find another
PORT = 3000
try:
    test_socket = socket.socket()
    test_socket.bind(('localhost', PORT))
    test_socket.close()
except OSError:
    PORT = find_free_port()
    print(f"[INFO] Port 3000 busy, using port {PORT} instead")

DASHBOARD_PATH = Path('public/dashboard.html')
PENDING_APPROVAL = Path('data/AI_Employee_Vault/Pending_Approval')
DONE_FOLDER = Path('data/AI_Employee_Vault/Done')
LOGS_DIR = Path('Logs')

# System state
system_state = {
    'watchers_running': False,
    'ai_available': False,
    'ai_model': 'Unknown',
    'pending_count': 0,
    'processed_today': 0,
    'last_activity': None
}

# Background processes
watchers = {}


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler for dashboard API"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        
        # API endpoints
        if parsed.path == '/api/status':
            self.send_json_response(get_system_status())
        
        elif parsed.path == '/api/pending':
            self.send_json_response(get_pending_tasks())
        
        elif parsed.path == '/api/to-review':
            self.send_json_response(get_to_review_tasks())
        
        elif parsed.path.startswith('/api/to-review/'):
            # Get full content of specific To_Review item
            task_id = parsed.path.split('/')[-1]
            result = get_to_review_item_content(task_id)
            self.send_json_response(result)
        
        elif parsed.path == '/api/activity':
            self.send_json_response(get_recent_activity())
        
        elif parsed.path == '/api/ai-info':
            self.send_json_response(get_model_info())
        
        # Serve dashboard
        elif parsed.path == '/' or parsed.path == '/dashboard':
            self.serve_dashboard()
        
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        # API endpoints
        if parsed.path == '/api/analyze':
            # Analyze text message
            text = data.get('text', '')
            result = analyze_intent(text)
            self.send_json_response(result)
        
        elif parsed.path == '/api/create-task':
            # Create task from text with retry on rate limit
            text = data.get('text', '')
            
            # Try AI analysis with retries for rate limit
            max_retries = 3
            intent_data = None
            
            for attempt in range(max_retries):
                try:
                    intent_data = analyze_intent(text)
                    if intent_data and intent_data.get('primary_intent'):
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)
                        print(f"[Dashboard] Rate limited. Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        # All retries failed
                        self.send_json_response({
                            'success': False,
                            'error': f'AI service is busy. Please wait 60 seconds and try again. (Groq rate limit)',
                            'retry_after': 60
                        })
                        return
            
            if not intent_data or not intent_data.get('primary_intent'):
                self.send_json_response({
                    'success': False,
                    'error': 'AI failed to analyze. Please try again with more details.',
                    'retry_after': 30
                })
                return
            
            task_file = create_task_file(intent_data, text, 'web_input.txt')
            self.send_json_response({
                'success': True,
                'task_file': str(task_file),
                'intent': intent_data.get('primary_intent'),
                'category': intent_data.get('category', 'unknown')
            })
        
        elif parsed.path == '/api/approve':
            # Approve a task
            task_id = data.get('task_id')
            result = approve_task(task_id)
            self.send_json_response(result)
        
        elif parsed.path == '/api/reject':
            # Reject a task
            task_id = data.get('task_id')
            reason = data.get('reason', '')
            result = reject_task(task_id, reason)
            self.send_json_response(result)
        
        elif parsed.path == '/api/mark-done':
            # Mark To_Review item as done
            task_id = data.get('task_id')
            result = mark_review_as_done(task_id)
            self.send_json_response(result)
        
        elif parsed.path == '/api/archive-review':
            # Archive To_Review item
            task_id = data.get('task_id')
            result = archive_review_task(task_id)
            self.send_json_response(result)
        
        elif parsed.path == '/api/start-watchers':
            # Start background watchers
            start_watchers()
            self.send_json_response({'success': True, 'message': 'Watchers started'})
        
        elif parsed.path == '/api/stop-watchers':
            # Stop background watchers
            stop_watchers()
            self.send_json_response({'success': True, 'message': 'Watchers stopped'})
        
        elif parsed.path == '/api/process-drop-folder':
            # Process drop folder now
            result = process_drop_folder_now()
            self.send_json_response(result)
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def serve_dashboard(self):
        """Serve the dashboard HTML"""
        dashboard_path = Path('public') / 'dashboard.html'
        
        if not dashboard_path.exists():
            # Create default dashboard
            create_dashboard_html()
        
        self.path = '/public/dashboard.html'
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def get_system_status():
    """Get current system status"""
    # Count pending tasks
    pending_count = len(list(PENDING_APPROVAL.glob('*.md'))) if PENDING_APPROVAL.exists() else 0
    
    # Count processed today
    today = datetime.now().strftime('%Y-%m-%d')
    processed_count = 0
    if DONE_FOLDER.exists():
        for f in DONE_FOLDER.glob(f'*{today}*.md'):
            processed_count += 1
    
    # Check AI
    ai_info = get_model_info()
    
    return {
        'watchers_running': system_state['watchers_running'],
        'ai_available': ai_info['fallback_available'],
        'ai_model': f"{ai_info['primary']} ({ai_info['model']})",
        'pending_count': pending_count,
        'processed_today': processed_count,
        'last_activity': system_state.get('last_activity'),
        'drop_folder': str(DROP_FOLDER.absolute()),
        'needs_action': str(NEEDS_ACTION.absolute())
    }


def get_pending_tasks():
    """Get list of pending tasks from Needs_Action and Pending_Approval folders"""
    tasks = []

    # Check BOTH folders (where tasks might be created)
    folders_to_check = [NEEDS_ACTION, PENDING_APPROVAL]

    for folder in folders_to_check:
        if not folder.exists():
            continue

        for md_file in sorted(folder.glob('*.md'), reverse=True):
            content = md_file.read_text(encoding='utf-8')

            # Extract metadata
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False

            for line in lines:
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        break

                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            # Extract first line of content
            content_preview = ""
            for line in lines:
                if line.strip() and not line.startswith('---') and not line.startswith('#'):
                    content_preview = line[:100]
                    break

            tasks.append({
                'id': md_file.stem,
                'file': md_file.name,
                'type': metadata.get('type', 'unknown'),
                'created': metadata.get('created', ''),
                'confidence': metadata.get('ai_confidence', '0'),
                'requires_review': metadata.get('requires_human_review', 'false'),
                'preview': content_preview,
                'auto_generated': metadata.get('auto_generated', 'false'),
                # Extract intent and missing info for better display
                'intent': extract_intent(content),
                'missing_info': extract_missing_info(content)
            })

    return tasks


def extract_intent(content):
    """Extract the intent/suggested action from task content"""
    lines = content.split('\n')
    in_intent_section = False
    intent_lines = []
    
    for line in lines:
        if '**Intent:**' in line:
            in_intent_section = True
            intent_text = line.split('**Intent:**')[1].strip()
            if intent_text:
                return intent_text
        elif in_intent_section:
            if line.strip() and not line.startswith('**'):
                intent_lines.append(line.strip())
            elif line.startswith('##'):
                break
    
    if intent_lines:
        return ' '.join(intent_lines[:2])
    
    return content_preview


def extract_missing_info(content):
    """Extract list of missing information from task"""
    missing = []
    lines = content.split('\n')
    in_missing_section = False
    
    for line in lines:
        # Look for the Missing Information section in markdown
        if '## ⚠️ Missing Information' in line or '## Missing Information' in line:
            in_missing_section = True
            continue
        
        if in_missing_section:
            # Only extract checkbox items (- [ ])
            if line.strip().startswith('- [ ]'):
                field = line.replace('- [ ]', '').strip()
                # Filter out non-field text (like button labels)
                if field and not any(x in field.lower() for x in ['approve', 'reject', 'edit', 'need more']):
                    missing.append(field)
            # Stop at next section
            elif line.strip().startswith('**Human review') or line.strip().startswith('##'):
                break
    
    return missing


def get_to_review_tasks():
    """Get list of tasks in To_Review folder"""
    tasks = []
    
    # Check both possible locations
    to_review_paths = [
        Path('data/AI_Employee_Vault/To_Review'),
        Path('AI_Employee_Vault/To_Review')
    ]
    
    for to_review_path in to_review_paths:
        if not to_review_path.exists():
            continue
        
        for md_file in sorted(to_review_path.glob('*.md'), reverse=True):
            content = md_file.read_text(encoding='utf-8')
            
            # Extract metadata
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            
            for line in lines:
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        break
                
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Extract AI summary
            ai_summary = metadata.get('ai_summary', 'Review this item')
            expires = metadata.get('expires', '')
            
            tasks.append({
                'id': md_file.stem,
                'file': md_file.name,
                'type': metadata.get('type', 'unknown'),
                'created': metadata.get('created', ''),
                'summary': ai_summary,
                'expires': expires,
                'from': metadata.get('from', 'Unknown'),
                'subject': metadata.get('what', 'Item to review')
            })
        
        # If we found tasks, return them
        if tasks:
            break
    
    return tasks


def get_to_review_item_content(task_id):
    """Get full content of a specific To_Review item"""
    to_review_paths = [
        Path('data/AI_Employee_Vault/To_Review'),
        Path('AI_Employee_Vault/To_Review')
    ]
    
    for to_review_path in to_review_paths:
        if not to_review_path.exists():
            continue
        
        task_file = to_review_path / f'{task_id}.md'
        if task_file.exists():
            content = task_file.read_text(encoding='utf-8')
            
            # Extract metadata
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            content_start = False
            
            for line in lines:
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        in_frontmatter = False
                        content_start = True
                        continue
                
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Get content after frontmatter
            content_text = ""
            if content_start:
                content_text = content.split('---', 2)[-1].strip()
            
            return {
                'id': task_id,
                'type': metadata.get('type', 'unknown'),
                'from': metadata.get('from', 'Unknown'),
                'received': metadata.get('received', 'Unknown'),
                'subject': metadata.get('what', 'Item to review'),
                'summary': metadata.get('ai_summary', 'Review this item'),
                'content': content_text
            }
    
    return {'error': 'Task not found'}


def get_recent_activity():
    """Get recent activity from logs"""
    activities = []
    
    # Get today's log
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOGS_DIR / f'{today}.json'
    
    if log_file.exists():
        try:
            content = log_file.read_text(encoding='utf-8')
            logs = json.loads(content)
            
            # Get last 20 entries
            for entry in logs[-20:]:
                activities.append({
                    'time': entry.get('timestamp', '')[-8:],
                    'action': entry.get('action', ''),
                    'result': entry.get('result', '')[:100]
                })
        except:
            pass
    
    return activities


def approve_task(task_id):
    """Approve a pending task and EXECUTE the action"""
    try:
        # Find the file - check ALL possible folders
        folders_to_check = [
            NEEDS_ACTION,
            PENDING_APPROVAL,
            Path('data/AI_Employee_Vault/Needs_Action'),
            Path('data/AI_Employee_Vault/Pending_Approval')
        ]
        
        task_file = None
        for folder in folders_to_check:
            potential_file = folder / f'{task_id}.md'
            if potential_file.exists():
                task_file = potential_file
                break
        
        if not task_file:
            print(f"[ERROR] Task file not found: {task_id}")
            return {'success': False, 'error': 'Task not found'}

        # Read task content
        content = task_file.read_text(encoding='utf-8')
        print(f"[DEBUG] Task content: {content[:200]}...")

        # Extract task type
        task_type = 'unknown'
        for line in content.split('\n'):
            if line.startswith('type:'):
                task_type = line.split(':')[1].strip()
                break

        print(f"[DEBUG] Task type: {task_type}")

        # EXECUTE the action
        print(f"[DEBUG] Executing task: {task_type}")
        action_result = execute_approved_task(task_type, content, task_file.name)

        print(f"[DEBUG] Execute result: {action_result}")

        # Mark as approved
        content = content.replace('[ ] Approve', '[x] Approve')
        content = content.replace('[ ] Edit', '[x] Edit')

        # Move to Done
        done_path = Path('data/AI_Employee_Vault/Done') / task_file.name
        done_path.parent.mkdir(parents=True, exist_ok=True)
        task_file.rename(done_path)

        # Log
        log_activity('task_approved', f'{task_type}: {task_file.name} - {action_result.get("message", "Success")}')

        return {'success': action_result.get('success', False), 'message': action_result.get('message', 'Task executed'), 'details': action_result.get('details', {})}

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Approve failed: {error_trace}")
        return {'success': False, 'error': f'Approval failed: {str(e)}', 'details': {'traceback': error_trace}}


def execute_approved_task(task_type, content, filename):
    """Execute action based on task type"""
    try:
        result = {'action': task_type, 'message': '', 'status': 'success'}
        
        if task_type == 'odoo_invoice' or task_type == 'email_invoice':
            # Extract details from task content
            customer_name = extract_field(content, 'customer_name')
            amount = extract_field(content, 'amount')
            description = extract_field(content, 'product_service') or 'Invoice item'
            invoice_number = extract_field(content, 'invoice_number')
            
            # Check for required fields
            if not customer_name:
                return {
                    'success': False,
                    'error': 'Cannot create invoice: Missing customer name',
                    'details': {'missing_field': 'customer_name'}
                }
            
            if not amount:
                return {
                    'success': False,
                    'error': 'Cannot create invoice: Missing amount',
                    'details': {'missing_field': 'amount'}
                }
            
            # Create invoice in Odoo
            from odoo_integration import create_odoo_invoice
            odoo_result = create_odoo_invoice(customer_name, amount, description, invoice_number)
            
            if odoo_result['success']:
                return {
                    'success': True,
                    'message': f"Invoice {odoo_result.get('invoice_number', 'N/A')} created in Odoo",
                    'details': odoo_result
                }
            else:
                return {
                    'success': False,
                    'error': f"Odoo error: {odoo_result.get('error', 'Unknown error')}",
                    'details': odoo_result
                }
        
        elif task_type == 'email_send':
            # Execute email sending via Gmail
            email_result = execute_email_task(content, filename)
            
            if email_result['success']:
                return {
                    'success': True,
                    'message': f"Email sent to {email_result['details'].get('to', 'recipient')}",
                    'details': email_result['details']
                }
            else:
                return {
                    'success': False,
                    'error': f"Email failed: {email_result.get('error', 'Unknown error')}",
                    'details': email_result.get('details', {})
                }
        
        elif task_type == 'whatsapp_reply':
            # Execute WhatsApp (your working code)
            whatsapp_result = execute_whatsapp_task(content, filename)
            
            if whatsapp_result['success']:
                return {
                    'success': True,
                    'message': f"WhatsApp sent to {whatsapp_result['details'].get('phone', 'recipient')}",
                    'details': whatsapp_result['details']
                }
            else:
                return {
                    'success': False,
                    'error': f"WhatsApp failed: {whatsapp_result.get('error', 'Unknown error')}",
                    'details': whatsapp_result.get('details', {})
                }
        
        elif task_type == 'linkedin_post' or task_type == 'linkedin':
            # Execute LinkedIn posting
            linkedin_result = execute_linkedin_task(content, filename)
            
            if linkedin_result['success']:
                return {
                    'success': True,
                    'message': f"LinkedIn post created! {linkedin_result['details'].get('post_id', '')}",
                    'details': linkedin_result['details']
                }
            else:
                return {
                    'success': False,
                    'error': f"LinkedIn failed: {linkedin_result.get('error', 'Unknown error')}",
                    'details': linkedin_result.get('details', {})
                }
        
        else:
            return {
                'success': True,
                'message': f'Task marked as completed (type: {task_type})',
                'details': {'status': 'completed'}
            }
    
    except Exception as e:
        import logging
        logging.error(f"Error executing task {task_type}: {str(e)}")
        return {
            'success': False,
            'error': f'Execution error: {str(e)}',
            'details': {'exception': str(e)}
        }


def reject_task(task_id, reason=''):
    """Reject a pending task"""
    # Check in NEEDS_ACTION folder (where tasks actually are)
    task_file = NEEDS_ACTION / f'{task_id}.md'

    if not task_file.exists():
        return {'success': False, 'error': 'Task not found'}

    # Add rejection reason
    content = task_file.read_text(encoding='utf-8')
    content = content.replace('[ ] Reject', f'[x] Reject\n\n**Reason:** {reason}')
    task_file.write_text(content, encoding='utf-8')

    # Move to Rejected folder
    rejected_path = Path('data/AI_Employee_Vault/Rejected') / task_file.name
    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    task_file.rename(rejected_path)

    log_activity('task_rejected', str(task_file))

    return {'success': True, 'message': 'Task rejected'}


def mark_review_as_done(task_id):
    """Mark To_Review item as done"""
    to_review_path = Path('data/AI_Employee_Vault/To_Review')
    task_file = to_review_path / f'{task_id}.md'

    if not task_file.exists():
        return {'success': False, 'error': 'Task not found'}

    # Mark as done
    content = task_file.read_text(encoding='utf-8')
    content = content.replace("[ ] I've reviewed this", "[x] I've reviewed this")
    task_file.write_text(content, encoding='utf-8')

    # Move to Done folder
    done_path = Path('data/AI_Employee_Vault/Done') / task_file.name
    done_path.parent.mkdir(parents=True, exist_ok=True)
    task_file.rename(done_path)

    log_activity('review_marked_done', str(task_file))

    return {'success': True, 'message': 'Marked as done'}


def archive_review_task(task_id):
    """Archive To_Review item"""
    to_review_path = Path('data/AI_Employee_Vault/To_Review')
    task_file = to_review_path / f'{task_id}.md'

    if not task_file.exists():
        return {'success': False, 'error': 'Task not found'}

    # Move to Done folder (archived)
    done_path = Path('data/AI_Employee_Vault/Done') / task_file.name
    done_path.parent.mkdir(parents=True, exist_ok=True)
    task_file.rename(done_path)

    log_activity('review_archived', str(task_file))

    return {'success': True, 'message': 'Archived'}


def start_watchers():
    """Start background watchers"""
    if system_state['watchers_running']:
        return
    
    # In production, this would start actual watcher processes
    # For now, just simulate
    system_state['watchers_running'] = True
    log_activity('watchers_started', 'Background watchers started')


def stop_watchers():
    """Stop background watchers"""
    system_state['watchers_running'] = False
    log_activity('watchers_stopped', 'Background watchers stopped')


def process_drop_folder_now():
    """Process drop folder immediately"""
    try:
        result = subprocess.run(
            ['python', 'src/intent_analyzer.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            'success': True,
            'output': result.stdout,
            'error': result.stderr
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def log_activity(action, result):
    """Log activity"""
    system_state['last_activity'] = f'{datetime.now().strftime("%H:%M")} - {action}'


def create_dashboard_html():
    """Create professional dashboard HTML"""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Employee Vault - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: #2c3e50;
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        
        header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .status-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .status-card h3 {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        
        .status-card .value {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .status-card .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 10px;
        }
        
        .status.active {
            background: #27ae60;
            color: white;
        }
        
        .status.inactive {
            background: #95a5a6;
            color: white;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .card-header {
            padding: 20px;
            border-bottom: 1px solid #ecf0f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-header h2 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .card-body {
            padding: 20px;
        }
        
        .drop-zone {
            border: 2px dashed #bdc3c7;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        
        .drop-zone:hover {
            border-color: #3498db;
            background: #f8f9fa;
        }
        
        .drop-zone p {
            color: #7f8c8d;
            margin-bottom: 15px;
        }
        
        textarea {
            width: 100%;
            min-height: 100px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 12px;
            font-family: inherit;
            resize: vertical;
            margin-bottom: 15px;
        }
        
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #2980b9;
        }
        
        button.success {
            background: #27ae60;
        }
        
        button.success:hover {
            background: #229954;
        }
        
        button.danger {
            background: #e74c3c;
        }
        
        button.danger:hover {
            background: #c0392b;
        }
        
        .task-list {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .task-item {
            padding: 15px;
            border: 1px solid #ecf0f1;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        
        .task-item:last-child {
            margin-bottom: 0;
        }
        
        .task-item .meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .task-item .type {
            background: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        .task-item .confidence {
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .task-item .preview {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .task-item .actions {
            display: flex;
            gap: 10px;
        }
        
        .activity-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .activity-item {
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
            font-size: 14px;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-item .time {
            color: #7f8c8d;
            font-size: 12px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
        
        .refresh-btn {
            background: transparent;
            border: 1px solid #bdc3c7;
            color: #7f8c8d;
            padding: 5px 15px;
        }
        
        .refresh-btn:hover {
            background: #ecf0f1;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>AI Employee Vault - Dashboard</h1>
        </div>
    </header>
    
    <div class="container">
        <!-- Status Bar -->
        <div class="status-bar">
            <div class="status-card">
                <h3>AI Agent</h3>
                <div class="value" id="ai-model">Loading...</div>
                <span class="status inactive" id="ai-status">Checking...</span>
            </div>
            
            <div class="status-card">
                <h3>Watchers</h3>
                <div class="value" id="watcher-status">Stopped</div>
                <span class="status inactive" id="watcher-indicator">Offline</span>
            </div>
            
            <div class="status-card">
                <h3>Pending Tasks</h3>
                <div class="value" id="pending-count">0</div>
                <span class="status" style="background: #f39c12; color: white;">Awaiting Review</span>
            </div>
            
            <div class="status-card">
                <h3>Processed Today</h3>
                <div class="value" id="processed-count">0</div>
                <span class="status active">Completed</span>
            </div>
        </div>
        
        <!-- Main Grid -->
        <div class="main-grid">
            <!-- Create Task -->
            <div class="card">
                <div class="card-header">
                    <h2>Create New Task</h2>
                    <button class="refresh-btn" onclick="processDropFolder()">Process Drop Folder</button>
                </div>
                <div class="card-body">
                    <div class="drop-zone">
                        <p>Drop TXT files in: <strong id="drop-folder-path">drop_folder/</strong></p>
                        <p>or type a message below:</p>
                    </div>
                    
                    <textarea id="task-input" placeholder="Example: Customer John needs invoice #12345 for $500 sent to john@example.com"></textarea>
                    
                    <button onclick="createTask()">Analyze & Create Task</button>
                    
                    <div id="analysis-result" style="margin-top: 20px; display: none;">
                        <h4 style="margin-bottom: 10px;">AI Analysis:</h4>
                        <pre id="analysis-output" style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 12px; overflow-x: auto;"></pre>
                    </div>
                </div>
            </div>
            
            <!-- Pending Tasks -->
            <div class="card">
                <div class="card-header">
                    <h2>Pending Approval</h2>
                    <button class="refresh-btn" onclick="loadPendingTasks()">Refresh</button>
                </div>
                <div class="card-body">
                    <div class="task-list" id="task-list">
                        <div class="loading">Loading tasks...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Activity Log -->
        <div class="card">
            <div class="card-header">
                <h2>Recent Activity</h2>
                <button class="refresh-btn" onclick="loadActivity()">Refresh</button>
            </div>
            <div class="card-body">
                <div class="activity-list" id="activity-list">
                    <div class="loading">Loading activity...</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // API base URL
        const API = '';
        
        // Load initial data
        loadStatus();
        loadPendingTasks();
        loadActivity();
        
        // Auto-refresh every 10 seconds
        setInterval(() => {
            loadStatus();
            loadPendingTasks();
        }, 10000);
        
        async function loadStatus() {
            try {
                const res = await fetch(`${API}/api/status`);
                const data = await res.json();
                
                document.getElementById('ai-model').textContent = data.ai_model;
                document.getElementById('ai-status').textContent = data.ai_available ? 'Active' : 'Unavailable';
                document.getElementById('ai-status').className = `status ${data.ai_available ? 'active' : 'inactive'}`;
                
                document.getElementById('watcher-status').textContent = data.watchers_running ? 'Running' : 'Stopped';
                document.getElementById('watcher-indicator').textContent = data.watchers_running ? 'Online' : 'Offline';
                document.getElementById('watcher-indicator').className = `status ${data.watchers_running ? 'active' : 'inactive'}`;
                
                document.getElementById('pending-count').textContent = data.pending_count;
                document.getElementById('processed-count').textContent = data.processed_today;
                document.getElementById('drop-folder-path').textContent = data.drop_folder;
            } catch (err) {
                console.error('Status error:', err);
            }
        }
        
        async function loadPendingTasks() {
            try {
                const res = await fetch(`${API}/api/pending`);
                const tasks = await res.json();
                
                const container = document.getElementById('task-list');
                
                if (tasks.length === 0) {
                    container.innerHTML = '<div class="loading">No pending tasks</div>';
                    return;
                }
                
                container.innerHTML = tasks.map(task => `
                    <div class="task-item">
                        <div class="meta">
                            <span class="type">${task.type}</span>
                            <span class="confidence">Confidence: ${task.confidence}%</span>
                        </div>
                        <div class="preview">${task.preview}</div>
                        <div class="actions">
                            <button class="success" onclick="approveTask('${task.id}')">Approve</button>
                            <button class="danger" onclick="rejectTask('${task.id}')">Reject</button>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                console.error('Load tasks error:', err);
            }
        }
        
        async function loadActivity() {
            try {
                const res = await fetch(`${API}/api/activity`);
                const activities = await res.json();
                
                const container = document.getElementById('activity-list');
                
                if (activities.length === 0) {
                    container.innerHTML = '<div class="loading">No recent activity</div>';
                    return;
                }
                
                container.innerHTML = activities.map(act => `
                    <div class="activity-item">
                        <span class="time">${act.time}</span>
                        <strong>${act.action}</strong>: ${act.result}
                    </div>
                `).join('');
            } catch (err) {
                console.error('Activity error:', err);
            }
        }
        
        async function createTask() {
            const text = document.getElementById('task-input').value;
            
            if (!text.trim()) {
                alert('Please enter a message');
                return;
            }
            
            try {
                const res = await fetch(`${API}/api/create-task`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                
                const result = await res.json();
                
                if (result.success) {
                    document.getElementById('analysis-output').textContent = JSON.stringify(result, null, 2);
                    document.getElementById('analysis-result').style.display = 'block';
                    document.getElementById('task-input').value = '';
                    
                    // Reload tasks
                    loadPendingTasks();
                    loadStatus();
                    
                    alert('Task created successfully!');
                } else {
                    alert('Error: ' + (result.error || 'Unknown error'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
        
        async function approveTask(taskId) {
            if (!confirm('Approve this task?')) return;
            
            try {
                const res = await fetch(`${API}/api/approve`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId })
                });
                
                const result = await res.json();
                
                if (result.success) {
                    loadPendingTasks();
                    loadStatus();
                    alert('Task approved!');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
        
        async function rejectTask(taskId) {
            const reason = prompt('Reason for rejection (optional):');
            if (reason === null) return;
            
            try {
                const res = await fetch(`${API}/api/reject`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId, reason: reason || 'No reason provided' })
                });
                
                const result = await res.json();
                
                if (result.success) {
                    loadPendingTasks();
                    loadStatus();
                    alert('Task rejected');
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
        
        async function processDropFolder() {
            try {
                const res = await fetch(`${API}/api/process-drop-folder`, {
                    method: 'POST'
                });
                
                const result = await res.json();
                
                if (result.success) {
                    alert('Drop folder processed! Check Needs_Action folder.');
                    loadPendingTasks();
                    loadStatus();
                } else {
                    alert('Error: ' + (result.error || 'Unknown error'));
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
    </script>
</body>
</html>
"""
    
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_PATH.write_text(html, encoding='utf-8')
    print(f"[INFO] Dashboard created: {DASHBOARD_PATH}")


def run_server():
    """Run the dashboard server"""
    # Create dashboard if not exists
    if not DASHBOARD_PATH.exists():
        create_dashboard_html()
    
    # Start server
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print("=" * 60)
        print("  AI Employee Vault - Dashboard Server")
        print("=" * 60)
        print()
        print(f"  Dashboard: http://localhost:{PORT}")
        print(f"  Drop Folder: {DROP_FOLDER.absolute()}")
        print()
        print("  Features:")
        print("  - Drop TXT files for AI analysis")
        print("  - Type messages directly")
        print("  - Approve/Reject tasks")
        print("  - Real-time status")
        print()
        print("  Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped")


if __name__ == "__main__":
    run_server()
