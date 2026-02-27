"""
WhatsApp Sender - Calls Local Agent HTTP API
Sends WhatsApp messages via connected local agent
"""

import requests
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Local Agent API URL
LOCAL_AGENT_API = os.getenv('LOCAL_AGENT_API', 'http://localhost:3001')


def send_whatsapp_local(phone: str, message: str) -> dict:
    """
    Send WhatsApp message via local agent HTTP API
    
    The local agent has an active WhatsApp Web session.
    We call its HTTP API to send messages.
    
    Args:
        phone: Phone number (with country code)
        message: Message text
        
    Returns:
        dict with success status
    """
    try:
        # Call local agent API
        response = requests.post(
            f'{LOCAL_AGENT_API}/send',
            json={
                'phone': phone,
                'message': message
            },
            timeout=30
        )
        
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            logger.info(f"WhatsApp sent to {phone} via HTTP API")
            return {
                'success': True,
                'message': 'Message sent successfully',
                'data': result
            }
        else:
            logger.error(f"WhatsApp send failed: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'Failed to send message'),
                'data': result
            }
            
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to local agent API")
        return {
            'success': False,
            'error': 'Cannot connect to local agent. Make sure it is running (npm start)'
        }
    except requests.exceptions.Timeout:
        logger.error("WhatsApp send timeout")
        return {
            'success': False,
            'error': 'Timeout after 30 seconds'
        }
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def check_local_agent_status() -> bool:
    """Check if local agent API is running"""
    try:
        response = requests.get(f'{LOCAL_AGENT_API}/health', timeout=5)
        return response.status_code == 200
    except:
        return False
