"""
LinkedIn Integration - Actually Create Posts
Connects dashboard approvals to real LinkedIn posting
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LinkedIn API Configuration
LINKEDIN_TOKEN = os.getenv('LINKEDIN_TOKEN', '')
LINKEDIN_PERSON_URN = os.getenv('LINKEDIN_PERSON_URN', '')

# LinkedIn API Endpoints
LINKEDIN_API_BASE = 'https://api.linkedin.com/v2'


def post_to_linkedin(text, visibility='PUBLIC'):
    """
    Create a post on LinkedIn
    
    Args:
        text: Post content (max 3000 characters)
        visibility: 'PUBLIC' or 'CONNECTIONS'
    
    Returns:
        dict with success status and post details
    """
    try:
        # Check credentials
        if not LINKEDIN_TOKEN or LINKEDIN_TOKEN.startswith('your-'):
            return {
                'success': False,
                'error': 'LinkedIn credentials not configured. Add LINKEDIN_TOKEN to .env',
                'details': {'status': 'credentials_missing'}
            }
        
        if not LINKEDIN_PERSON_URN:
            return {
                'success': False,
                'error': 'LinkedIn Person URN not configured. Add LINKEDIN_PERSON_URN to .env',
                'details': {'status': 'urn_missing'}
            }
        
        # Prepare post content
        headers = {
            'Authorization': f'Bearer {LINKEDIN_TOKEN}',
            'Content-Type': 'application/json',
            'LinkedIn-Version': '202402',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        # LinkedIn post API endpoint (using ugC API)
        url = f'{LINKEDIN_API_BASE}/ugcPosts'
        
        # Create post payload for ugCPosts endpoint
        payload = {
            'author': f'urn:li:person:{LINKEDIN_PERSON_URN.replace("urn:li:person:", "")}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': text
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': visibility
            }
        }
        
        # Send request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check response
        if response.status_code == 201:
            post_id = response.json().get('id', 'Unknown')
            return {
                'success': True,
                'message': f'LinkedIn post created successfully',
                'details': {
                    'post_id': post_id,
                    'visibility': visibility,
                    'status': 'published'
                }
            }
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'HTTP {response.status_code}')
            return {
                'success': False,
                'error': f'LinkedIn API error: {error_msg}',
                'details': {
                    'status_code': response.status_code,
                    'error_data': error_data
                }
            }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}',
            'details': {'status': 'network_error'}
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error posting to LinkedIn: {str(e)}',
            'details': {'status': 'error'}
        }


def execute_linkedin_task(content, task_file):
    """
    Execute LinkedIn posting task from dashboard

    Args:
        content: Task markdown content
        task_file: Task filename

    Returns:
        dict with execution result
    """
    # Extract post content from task - try multiple fields
    post_text = extract_field(content, 'post_content')

    if not post_text:
        # Try message_content as fallback
        post_text = extract_field(content, 'message_content')

    if not post_text:
        # Try to extract from intent
        import re
        intent_match = re.search(r'\*\*Intent:\*\*\s*(.+?)(?:\(|$)', content)
        if intent_match:
            post_text = intent_match.group(1).strip()

    if not post_text:
        # Last resort: get content after "## Original Message"
        import re
        content_match = re.search(r'## Original Message\s*\n+```\s*(.+?)\s*```', content, re.DOTALL)
        if content_match:
            post_text = content_match.group(1).strip()

    if not post_text:
        return {
            'success': False,
            'error': 'Cannot post: No content found',
            'details': {'missing_field': 'post_content or message_content'}
        }

    # Post to LinkedIn
    result = post_to_linkedin(post_text)

    return result


def extract_field(content, field_name):
    """Extract field value from task markdown content"""
    import re
    
    # Look for field in markdown table
    pattern = rf'\|\s*{field_name}\s*\|\s*([^\|]+)\s*\|'
    match = re.search(pattern, content)
    
    if match:
        value = match.group(1).strip()
        if value.lower() in ['unknown', 'not mentioned', 'null', 'none']:
            return None
        return value
    
    return None


# Test function
if __name__ == "__main__":
    print("Testing LinkedIn Integration...")
    print("=" * 60)
    
    # Test post
    test_text = f"Test post from AI Employee Vault - {Path(__file__).name}\n\nThis is an automated test to verify LinkedIn integration is working."
    
    result = post_to_linkedin(test_text)
    
    if result['success']:
        print(f"[OK] SUCCESS: LinkedIn post created!")
        print(f"   Post ID: {result['details'].get('post_id')}")
        print(f"   Check your LinkedIn profile!")
    else:
        print(f"[ERROR] FAILED: {result['error']}")
        print("\nTroubleshooting:")
        print("1. Get LinkedIn access token from: https://developer.linkedin.com")
        print("2. Add to .env file:")
        print("   LINKEDIN_TOKEN=your-access-token")
        print("   LINKEDIN_PERSON_URN=urn:li:person:YOUR_ID")
        print("3. Make sure token has 'w_member_social' permission")
