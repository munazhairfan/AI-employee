"""
Cloud API Client for Local Agent
Calls cloud API to send WhatsApp messages
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
CLOUD_API_URL = os.getenv('CLOUD_API_URL', 'http://localhost:3000')
API_KEY = os.getenv('API_KEY', '')


def get_headers():
    """Get authentication headers for cloud API"""
    return {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }


def send_whatsapp_message(phone: str, message: str) -> dict:
    """
    Send WhatsApp message via cloud API
    
    Args:
        phone: Phone number (with country code, e.g., +1234567890)
        message: Message text
        
    Returns:
        dict with success status and response data
    """
    if not API_KEY:
        return {
            'success': False,
            'error': 'API_KEY not configured'
        }
    
    try:
        response = requests.post(
            f'{CLOUD_API_URL}/api/v1/actions/send-whatsapp',
            headers=get_headers(),
            json={
                'phone': phone,
                'message': message
            },
            timeout=30
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            return {
                'success': True,
                'data': result,
                'message_id': result.get('action_id')
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'data': result
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Cannot connect to cloud API'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def test_connection() -> bool:
    """Test if cloud API is reachable"""
    try:
        response = requests.get(
            f'{CLOUD_API_URL}/api/v1/health',
            timeout=5
        )
        return response.status_code == 200
    except:
        return False
