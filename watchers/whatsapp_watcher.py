import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from abc import abstractmethod

from playwright.sync_api import sync_playwright

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str = 'AI_Employee_Vault', session_path: str = 'whatsapp_session', check_interval: int = 30):
        super().__init__(vault_path, check_interval)
        self.session_path = Path(session_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help']
        self._processed_messages = set()
        self._load_processed_messages()

    def _load_processed_messages(self):
        """Load already processed message hashes from cache file."""
        cache_file = self.vault_path / '.processed_whatsapp.txt'
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                self._processed_messages = set(line.strip() for line in f if line.strip())

    def _save_processed_message(self, msg_hash: str):
        """Save processed message hash to cache file."""
        cache_file = self.vault_path / '.processed_whatsapp.txt'
        with open(cache_file, 'a') as f:
            f.write(f"{msg_hash}\n")
        self._processed_messages.add(msg_hash)

    def _hash_message(self, text: str, chat: str) -> str:
        """Create a simple hash for message deduplication."""
        return f"{chat}:{text[:50]}"

    def check_for_updates(self) -> list:
        """Check WhatsApp Web for unread messages with important keywords."""
        unread_messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with persistent session (non-headless for reliability)
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,  # Use visible browser for reliability
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']
                )
                
                # Check if already logged in
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                try:
                    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
                    
                    # Wait for chat list to load
                    page.wait_for_selector('div[role="row"]', timeout=10000)
                    
                    # Give it a moment to fully load
                    time.sleep(3)
                    
                    # Find all chat rows with unread indicators
                    chat_rows = page.query_selector_all('div[role="row"]')
                    
                    for row in chat_rows:
                        try:
                            # Get chat name
                            chat_name_elem = row.query_selector('span[title]')
                            if not chat_name_elem:
                                continue
                            chat_name = chat_name_elem.get_attribute('title')
                            
                            # Get message text
                            msg_elem = row.query_selector('span[dir="auto"]')
                            if not msg_elem:
                                continue
                            msg_text = msg_elem.inner_text()
                            
                            # Check for unread indicator (green badge or similar)
                            unread_badge = row.query_selector('span[aria-label*="unread"]')
                            has_unread = unread_badge is not None
                            
                            # Also check for unread class
                            if not has_unread:
                                unread_class = row.query_selector('.akpnb')
                                has_unread = unread_class is not None
                            
                            if has_unread and msg_text:
                                # Check if message contains important keywords
                                msg_lower = msg_text.lower()
                                if any(kw in msg_lower for kw in self.keywords):
                                    unread_messages.append({
                                        'text': msg_text,
                                        'chat': chat_name,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                        except Exception as e:
                            self.logger.debug(f"Error parsing chat row: {e}")
                            continue
                            
                except Exception as e:
                    self.logger.error(f"Error accessing WhatsApp Web: {e}")
                    self.logger.info("Make sure you have scanned QR code previously")
                
                finally:
                    browser.close()
                    
        except Exception as e:
            self.logger.error(f"Error in WhatsApp watcher: {e}")
        
        return unread_messages

    def create_action_file(self, item: dict) -> Path:
        """Create WHATSAPP_{timestamp}.md file in Needs_Action folder."""
        msg_hash = self._hash_message(item['text'], item['chat'])
        
        self.logger.info(f"Checking if message already processed... (hash: {msg_hash})")
        
        # Skip if already processed
        if msg_hash in self._processed_messages:
            self.logger.warning(f"Message already processed, skipping: {item['chat']}")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        action_file = self.needs_action / f"WHATSAPP_{timestamp}.md"
        
        self.logger.info(f"Creating action file: {action_file}")
        
        content = f"""---
type: whatsapp
from: {item['chat']}
received: {item['timestamp']}
priority: high
status: pending
---

## WhatsApp Message

**From:** {item['chat']}

**Message:**
{item['text']}

## Suggested Actions

- [ ] Read and understand the message
- [ ] Reply on WhatsApp if needed
- [ ] Take action if urgent/request
- [ ] Archive or mark as read after processing

"""
        
        with open(action_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"SUCCESS: Created action file: {action_file.name}")
        
        # Mark as processed
        self._save_processed_message(msg_hash)
        
        return action_file

    def run(self):
        """Run WhatsApp watcher with persistent browser session and auto-reconnect."""
        self.logger.info("Starting WhatsApp watcher with persistent browser...")
        
        while True:  # Auto-restart loop
            try:
                with sync_playwright() as p:
                    # Launch browser ONCE and keep it open
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir=str(self.session_path),
                        headless=False,
                        args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1920,1080']
                    )
                    
                    page = browser.pages[0] if browser.pages else browser.new_page()
                    
                    # Navigate to WhatsApp Web once
                    self.logger.info("Loading WhatsApp Web...")
                    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
                    
                    try:
                        page.wait_for_selector('div[role="row"]', timeout=10000)
                        self.logger.info("WhatsApp Web loaded - monitoring for messages...")
                    except Exception:
                        self.logger.error("Could not load chat list. Please check if you're logged in.")
                        self.logger.info("If not logged in, scan QR code in the browser window")
                        # Wait for user to scan QR
                        try:
                            page.wait_for_selector('div[role="row"]', timeout=120000)
                            self.logger.info("Login detected - starting monitoring...")
                        except Exception as e:
                            self.logger.error(f"QR code scan timeout: {e}")
                            browser.close()
                            continue  # Restart the watcher
                    
                    # Keep checking for messages without reopening browser
                    check_count = 0
                    while True:
                        try:
                            check_count += 1
                            self.logger.info(f"Checking for messages... (check #{check_count})")
                            
                            # Navigate to main page to refresh
                            page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=15000)
                            time.sleep(3)  # Wait for content to load
                            
                            # Check for messages
                            items = self._check_messages_in_page(page)
                            
                            if items:
                                self.logger.info(f"Found {len(items)} new message(s) with keywords!")
                                for item in items:
                                    self.create_action_file(item)
                            else:
                                self.logger.info("No new messages with keywords")
                                
                        except Exception as e:
                            self.logger.error(f"Error checking messages: {e}")
                            # Try to recover by refreshing
                            try:
                                page.reload()
                                time.sleep(2)
                            except:
                                break  # Restart browser
                        
                        time.sleep(self.check_interval)
                    
            except Exception as e:
                self.logger.error(f"Browser crashed: {e}")
                self.logger.info("Restarting WhatsApp watcher in 5 seconds...")
                time.sleep(5)  # Wait before restarting


    def _check_messages_in_page(self, page) -> list:
        """Check for unread messages using existing page (no browser restart)."""
        unread_messages = []
        
        try:
            # Wait for chat list to be fully loaded
            page.wait_for_selector('div[role="row"]', timeout=5000)
            time.sleep(1)
            
            # Find all chat rows - try multiple selectors for compatibility
            chat_rows = page.query_selector_all('div[role="row"]')
            
            self.logger.debug(f"Found {len(chat_rows)} chat rows")
            
            for idx, row in enumerate(chat_rows):
                try:
                    # Get chat name - try multiple selectors
                    chat_name_elem = row.query_selector('span[title]')
                    if not chat_name_elem:
                        chat_name_elem = row.query_selector('div[tabindex="0"] span')
                    if not chat_name_elem:
                        continue
                    chat_name = chat_name_elem.get_attribute('title') or 'Unknown'
                    
                    # Get message text - try multiple selectors
                    msg_elem = row.query_selector('span[dir="auto"]')
                    if not msg_elem:
                        msg_elem = row.query_selector('span:last-child')
                    if not msg_elem:
                        continue
                    msg_text = msg_elem.inner_text()
                    
                    self.logger.debug(f"Chat {idx}: {chat_name} - '{msg_text[:50]}...'")
                    
                    # Check for unread indicator - multiple methods
                    has_unread = False
                    
                    # Method 1: Unread badge
                    unread_badge = row.query_selector('span[aria-label*="unread"]')
                    if unread_badge:
                        has_unread = True
                    
                    # Method 2: Unread class (green dot)
                    if not has_unread:
                        unread_class = row.query_selector('.akpnb, .x1lliihq, [class*="unread"]')
                        if unread_class:
                            has_unread = True
                    
                    # Method 3: Check for bold text (unread messages are bold)
                    if not has_unread:
                        bold_text = row.query_selector('span[style*="font-weight: bold"], span[style*="font-weight:700"]')
                        if bold_text:
                            has_unread = True
                    
                    if has_unread and msg_text:
                        self.logger.info(f"UNREAD from {chat_name}: {msg_text[:50]}...")
                        
                        # Check if message contains important keywords
                        msg_lower = msg_text.lower()
                        if any(kw in msg_lower for kw in self.keywords):
                            self.logger.info(f"KEYWORD MATCH in message from {chat_name}!")
                            unread_messages.append({
                                'text': msg_text,
                                'chat': chat_name,
                                'timestamp': datetime.now().isoformat()
                            })
                        else:
                            self.logger.debug(f"No keyword match in message from {chat_name}")
                            
                except Exception as e:
                    self.logger.debug(f"Error parsing chat row {idx}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
        
        return unread_messages


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Check if session exists
    session_dir = Path('whatsapp_session')
    
    if not session_dir.exists():
        # First-time setup
        print("=" * 60)
        print("WHATSAPP WATCHER - FIRST TIME SETUP")
        print("=" * 60)
        print("\nThis will open a browser for you to scan QR code.")
        print("1. A browser window will open to web.whatsapp.com")
        print("2. Scan the QR code with your WhatsApp mobile app")
        print("3. After login, the browser will close automatically")
        print("4. Session is saved for future runs")
        print("\nPress Enter to continue...")
        input()
        
        # First-time login flow
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                headless=False,  # Show browser for QR scan
                args=['--disable-gpu', '--no-sandbox']
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://web.whatsapp.com', wait_until='networkidle')
            
            print("\nScan the QR code with WhatsApp on your phone...")
            print("Waiting for login (60 seconds max)...")
            
            try:
                page.wait_for_selector('div[role="row"]', timeout=60000)
                print("\nLogin successful! Session saved.")
                time.sleep(3)
            except Exception:
                print("\nLogin timeout. Please run again and scan QR code.")
            
            browser.close()
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print("\nNow run: python whatsapp_watcher.py")
        print("(Runs in headless mode, checking every 30 seconds)")
    else:
        # Session exists, run watcher normally
        print("=" * 60)
        print("WHATSAPP WATCHER")
        print("=" * 60)
        print("Session found, starting watcher...")
        print("Checking WhatsApp every 30 seconds")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        watcher = WhatsAppWatcher()
        watcher.run()
