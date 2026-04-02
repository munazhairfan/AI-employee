import sys
import time
import logging
import email
from pathlib import Path
from datetime import datetime
from base64 import urlsafe_b64decode
from abc import abstractmethod

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str = 'AI_Employee_Vault', credentials_path: str = 'credentials.json', check_interval: int = 60):
        super().__init__(vault_path, check_interval)
        self.credentials_path = Path(credentials_path)
        self.service = None
        self._processed_ids = set()
        self._load_processed_ids()

    def _authenticate(self):
        """Authenticate and build Gmail service. Auto-runs OAuth if needed."""
        creds = None
        token_path = Path('token.json')

        # Try to load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), ['https://www.googleapis.com/auth/gmail.readonly'])

        # If no valid creds, try to auto-run OAuth setup
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Auto-run OAuth setup if credentials.json exists
                creds = self._auto_run_oauth()
                
        if not creds:
            raise Exception("Gmail authentication failed. Please run: python scripts/setup_gmail_oauth.py")

        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail service authenticated")
    
    def _auto_run_oauth(self):
        """Automatically run OAuth setup if credentials.json exists."""
        creds_file = Path('credentials.json')
        
        # Check if credentials.json exists
        if not creds_file.exists():
            self.logger.error("credentials.json not found!")
            self.logger.error("To setup Gmail:")
            self.logger.error("1. Follow docs/GMAIL_SETUP_GUIDE.md")
            self.logger.error("2. Or run: python scripts/setup_gmail_oauth.py")
            return None
        
        # Check if token.json exists but is invalid
        token_path = Path('token.json')
        if token_path.exists():
            self.logger.info("Token expired/invalid, re-running OAuth...")
        else:
            self.logger.info("No token found, running OAuth setup...")
        
        try:
            # Import OAuth libraries
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            # Run OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_file),
                ['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            self.logger.info("Opening browser for OAuth...")
            self.logger.info("Please login and grant permissions")
            
            # Run local server for OAuth callback
            creds = flow.run_local_server(
                port=0,
                open_browser=True,
                success_message="Authentication successful! You can close this window.",
                authorization_prompt_message="Please visit this URL: {url}"
            )
            
            # Save token
            token_path.write_text(creds.to_json())
            self.logger.info(f"✓ Token saved to: {token_path}")
            
            return creds
            
        except Exception as e:
            self.logger.error(f"OAuth setup failed: {e}")
            self.logger.error("Manual setup: python scripts/setup_gmail_oauth.py")
            return None

    def _load_processed_ids(self):
        """Load already processed email IDs from cache file."""
        cache_file = Path('data/AI_Employee_Vault/.processed_emails.txt')
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self._processed_ids = set(line.strip() for line in f if line.strip())

    def _save_processed_id(self, msg_id: str):
        """Save processed email ID to cache file."""
        cache_file = Path('data/AI_Employee_Vault/.processed_emails.txt')
        with open(cache_file, 'a') as f:
            f.write(f"{msg_id}\n")
        self._processed_ids.add(msg_id)

    def _decode_snippet(self, snippet: str) -> str:
        """Decode base64url encoded snippet."""
        try:
            return urlsafe_b64decode(snippet + '=' * (-len(snippet) % 4)).decode('utf-8', errors='replace')
        except Exception:
            return snippet

    def _get_email_body(self, msg) -> str:
        """Extract plain text body from email message."""
        body = ""
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'body' in part:
                    data = part['body'].get('data', '')
                    if data:
                        body = urlsafe_b64decode(data + '=' * (-len(data) % 4)).decode('utf-8', errors='replace')
                        break
        elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            data = msg['payload']['body']['data']
            body = urlsafe_b64decode(data + '=' * (-len(data) % 4)).decode('utf-8', errors='replace')
        return body

    def _get_header(self, headers: list, name: str) -> str:
        """Extract specific header from email headers."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''
    
    def _clean_email_body(self, body: str) -> str:
        """Remove tracking links but keep meaningful content."""
        if not body:
            return ''
        
        # Remove LinkedIn tracking URLs but keep job info
        lines = body.split('\n')
        cleaned_lines = []
        
        for line in lines:
            original_line = line
            
            # Clean tracking parameters from URLs but keep the text
            if 'linkedin.com' in line:
                # Keep job titles, company names, locations
                if any(x in line.lower() for x in ['view job', 'apply with', 'remote', 'designer', 'developer', 'engineer']):
                    # Extract just the job info before the URL
                    if 'View job:' in line:
                        line = line.split('View job:')[0].strip()
                    elif 'Apply with' in line:
                        # Keep the job title and company
                        line = line.split('https://')[0].strip()
                # Remove pure tracking links
                elif 'trackingId=' in line or 'trk=' in line or 'lipi=' in line:
                    continue
                elif 'linkedin.com/comm' in line:
                    continue
            
            # Remove footer section
            if any(x in line.lower() for x in [
                '© 20', 'linkedin corporation', 'privacy policy', 'terms of service',
                'unsubscribe', 'manage your', 'edit alert'
            ]):
                break
            
            # Remove very long URLs (likely tracking)
            if len(line) > 300 and 'http' in line:
                continue
            
            # Keep meaningful content
            if line.strip():
                cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines)

    def check_for_updates(self) -> list:
        """Get unread important messages that haven't been processed."""
        if not self.service:
            try:
                self._authenticate()
            except Exception as e:
                # Only log once, then silently skip
                if not hasattr(self, '_auth_failed'):
                    self.logger.error(f"Gmail authentication failed: {e}")
                    self.logger.warning("Gmail watcher disabled - run OAuth setup or disable Gmail watcher")
                    self._auth_failed = True
                return []

        unread_msgs = []
        try:
            # Fetch unread messages from inbox
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q='is:unread',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            for msg_data in messages:
                msg_id = msg_data['id']
                
                # Skip already processed emails
                if msg_id in self._processed_ids:
                    continue

                # Fetch full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date', 'X-Priority']
                ).execute()

                headers = msg['payload'].get('headers', [])
                subject = self._get_header(headers, 'Subject')
                from_addr = self._get_header(headers, 'From')
                date_str = self._get_header(headers, 'Date')
                priority = self._get_header(headers, 'X-Priority')

                # Determine priority
                if priority in ['1', '2']:
                    priority_level = 'high'
                elif priority == '3':
                    priority_level = 'normal'
                else:
                    priority_level = 'normal'

                # Process ALL emails (AI will decide importance)
                # Removed keyword filtering - let AI decide what's important
                is_important = True

                if is_important:
                    # Parse date
                    try:
                        received_date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
                    except Exception:
                        received_date = datetime.now()

                    unread_msgs.append({
                        'id': msg_id,
                        'from': from_addr,
                        'subject': subject,
                        'received': received_date.isoformat(),
                        'priority': priority_level,
                        'snippet': msg['payload'].get('snippet', '')
                    })

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")

        return unread_msgs

    def create_action_file(self, item: dict) -> Path:
        """Create EMAIL_{id}.md file in watchers/output/ folder for AI processing."""
        # Fetch full message with body
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=item['id'],
                format='full'
            ).execute()
            body = self._get_email_body(msg)
        except Exception as e:
            self.logger.error(f"Error fetching email body: {e}")
            body = self._decode_snippet(item.get('snippet', ''))
        
        # Clean up the body - remove LinkedIn tracking, footers, etc.
        cleaned_body = self._clean_email_body(body)
        
        # Save to watchers/output/ for AI processor
        output_dir = Path('data/watcher_output')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.fromisoformat(item['received']).strftime('%Y-%m-%d_%H-%M-%S')
        action_file = output_dir / f"gmail_{timestamp}_{item['id']}.md"
        
        content = f"""---
type: email
source: gmail
from: {item['from']}
subject: {item['subject']}
received: {item['received']}
priority: {item['priority']}
---

# Message Content

{cleaned_body if cleaned_body else item.get('snippet', 'No content available')}

"""

        with open(action_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"Created action file: {action_file.name}")
        
        # Mark as processed
        self._save_processed_id(item['id'])

        return action_file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    watcher = GmailWatcher()
    watcher.run()
