"""
Email Integration - Actually Send Emails via Gmail
Connects dashboard approvals to real Gmail sending
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Gmail Configuration
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASS = os.getenv('EMAIL_PASS', '')  # App password, not regular password

# SMTP Configuration for Gmail
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465  # SSL port


def send_gmail_email(to_email, subject, body, from_name='AI Employee Vault'):
    """
    Send email via Gmail SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
        from_name: Sender name (default: AI Employee Vault)
    
    Returns:
        dict with success status and email details
    """
    try:
        # Check credentials
        if not EMAIL_USER or EMAIL_PASS == 'your-16-char-app-password-here':
            return {
                'success': False,
                'error': 'Gmail credentials not configured. Add EMAIL_USER and EMAIL_PASS to .env',
                'details': {'status': 'credentials_missing'}
            }
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f'{from_name} <{EMAIL_USER}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send via Gmail SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            # Login
            server.login(EMAIL_USER, EMAIL_PASS)
            
            # Send
            server.send_message(msg)
        
        return {
            'success': True,
            'message': f'Email sent to {to_email}',
            'details': {
                'to': to_email,
                'subject': subject,
                'from': EMAIL_USER,
                'status': 'sent'
            }
        }
        
    except smtplib.SMTPAuthenticationError:
        return {
            'success': False,
            'error': 'Gmail authentication failed. Check your App Password.',
            'details': {'status': 'auth_failed'}
        }
    except smtplib.SMTPException as e:
        return {
            'success': False,
            'error': f'Gmail SMTP error: {str(e)}',
            'details': {'status': 'smtp_error'}
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error sending email: {str(e)}',
            'details': {'status': 'error'}
        }


def execute_email_task(content, task_file):
    """
    Execute email sending task from dashboard
    
    Args:
        content: Task markdown content
        task_file: Task filename
    
    Returns:
        dict with execution result
    """
    # Extract email details from task content
    to_email = extract_field(content, 'customer_email')
    subject = extract_field(content, 'subject')
    body = extract_field(content, 'email_body')
    
    # Check for required fields
    if not to_email:
        return {
            'success': False,
            'error': 'Cannot send email: Missing recipient email address',
            'details': {'missing_field': 'customer_email'}
        }
    
    if not subject:
        subject = 'No subject'
    
    if not body:
        body = 'No content'
    
    # Send email
    result = send_gmail_email(to_email, subject, body)
    
    return result


def extract_field(content, field_name):
    """Extract field value from task markdown content"""
    import re
    
    # Look for field in markdown table
    pattern = rf'\|\s*{field_name}\s*\|\s*([^\|]+)\s*\|'
    match = re.search(pattern, content)
    
    if match:
        value = match.group(1).strip()
        # Clean up common values
        if value.lower() in ['unknown', 'not mentioned', 'null', 'none']:
            return None
        return value
    
    # Try to extract from intent line
    intent_pattern = rf'\*\*Intent:\*\*\s*(.+?)(?:\(|$)'
    intent_match = re.search(intent_pattern, content)
    
    if intent_match and field_name == 'subject':
        intent_text = intent_match.group(1).strip()
        if 'about' in intent_text.lower():
            return intent_text.split('about')[1].strip()
    
    return None


# Test function
if __name__ == "__main__":
    print("Testing Gmail Integration...")
    print("=" * 60)
    
    # Test with your own email first
    test_email = EMAIL_USER if EMAIL_USER else 'test@example.com'
    
    result = send_gmail_email(
        to_email=test_email,
        subject='Test Email from AI Employee Vault',
        body='This is a test email to verify Gmail integration is working.\n\nIf you receive this, the integration is successful!'
    )
    
    if result['success']:
        print(f"[OK] SUCCESS: Email sent to {test_email}")
        print(f"   Check your inbox!")
    else:
        print(f"[ERROR] FAILED: {result['error']}")
        print("\nTroubleshooting:")
        print("1. Get Gmail App Password from: https://myaccount.google.com/apppasswords")
        print("2. Add to .env file:")
        print("   EMAIL_USER=your-email@gmail.com")
        print("   EMAIL_PASS=xxxx-xxxx-xxxx-xxxx (16 char app password)")
        print("3. Make sure 'Less secure app access' is enabled OR use App Password")
