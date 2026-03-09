"""
WhatsApp Business API - Official & Reliable
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY', '')
META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID', '')


def send_whatsapp(phone: str, message: str) -> dict:
    """Send WhatsApp via official Business API"""
    
    # Check credentials
    if not WHATSAPP_API_KEY or not META_PHONE_NUMBER_ID:
        return {
            'success': False,
            'error': 'WhatsApp API credentials not configured. Add WHATSAPP_API_KEY and META_PHONE_NUMBER_ID to .env',
            'details': {'status': 'credentials_missing'}
        }
    
    # Validate phone
    if not phone or not phone.startswith('+'):
        return {
            'success': False,
            'error': 'Phone number must include country code (e.g., +923001234567)',
            'details': {'status': 'invalid_phone'}
        }
    
    try:
        # WhatsApp Business API endpoint
        url = f'https://graph.facebook.com/v17.0/{META_PHONE_NUMBER_ID}/messages'
        
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Remove + from phone for API
        phone_clean = phone.lstrip('+')
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': phone_clean,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')
            return {
                'success': True,
                'message': f'WhatsApp sent to {phone}',
                'details': {
                    'phone': phone,
                    'message_id': message_id,
                    'status': 'sent'
                }
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
            return {
                'success': False,
                'error': f'WhatsApp API error: {error_msg}',
                'details': {
                    'status_code': response.status_code,
                    'error_data': error_data
                }
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'WhatsApp error: {str(e)}',
            'details': {'status': 'error'}
        }


def execute_whatsapp_task(content, task_file):
    """Execute WhatsApp task from dashboard"""
    import re
    
    # Extract from markdown
    phone_match = re.search(r'\|\s*customer_phone\s*\|\s*([^\|]+)\s*\|', content)
    message_match = re.search(r'\|\s*(?:message|suggested_reply)\s*\|\s*([^\|]+)\s*\|', content)
    
    phone = phone_match.group(1).strip() if phone_match else None
    message = message_match.group(1).strip() if message_match else None
    
    if not phone:
        return {'success': False, 'error': 'Missing phone number'}
    if not message:
        return {'success': False, 'error': 'Missing message'}
    
    return send_whatsapp(phone, message)


if __name__ == "__main__":
    print("Testing WhatsApp Business API...")
    print("=" * 60)
    
    # Test
    test_phone = "+923080311205"
    test_message = "Test from AI Employee Vault - WhatsApp Business API"
    
    result = send_whatsapp(test_phone, test_message)
    
    if result['success']:
        print(f"[OK] SUCCESS: {result['message']}")
        print(f"Message ID: {result['details'].get('message_id')}")
    else:
        print(f"[ERROR] {result['error']}")
        print("\nTo fix:")
        print("1. Go to: https://developers.facebook.com/docs/whatsapp")
        print("2. Create WhatsApp Business App")
        print("3. Get API credentials")
        print("4. Add to .env:")
        print("   WHATSAPP_API_KEY=your-token")
        print("   META_PHONE_NUMBER_ID=your-phone-id")
