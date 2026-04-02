"""
WhatsApp Watcher - Monitors WhatsApp Web for unread messages
Now includes automatic contact database lookup for phone extraction
"""

import sys
import time
import logging
import json
import re
from pathlib import Path
from datetime import datetime
from abc import abstractmethod

from playwright.sync_api import sync_playwright

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.base_watcher import BaseWatcher

# Contact database for phone extraction
CONTACTS_FILE = Path('data/whatsapp_contacts.json')
CONTACTS = {}

# Load contacts if available
if CONTACTS_FILE.exists():
    try:
        CONTACTS = json.loads(CONTACTS_FILE.read_text(encoding='utf-8'))
        print(f"[INFO] Loaded {len(CONTACTS)} contacts from database")
    except:
        print(f"[WARN] Could not load contact database")


class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str = 'AI_Employee_Vault', session_path: str = 'whatsapp_session', check_interval: int = 30):
        super().__init__(vault_path, check_interval)
        self.session_path = Path(session_path)
        self._processed_messages = set()
        self._load_processed_messages()

    def _load_processed_messages(self):
        """Load already processed message hashes from cache file."""
        cache_file = Path('data/AI_Employee_Vault') / '.processed_whatsapp.txt'
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                self._processed_messages = set(line.strip() for line in f if line.strip())

    def _save_processed_message(self, msg_hash: str):
        """Save processed message hash to cache file."""
        cache_file = Path('data/AI_Employee_Vault') / '.processed_whatsapp.txt'
        with open(cache_file, 'a', encoding='utf-8') as f:
            f.write(f"{msg_hash}\n")
        self._processed_messages.add(msg_hash)

    def _hash_message(self, text: str, chat: str) -> str:
        """Create a simple hash for message deduplication."""
        return f"{chat}:{text[:50]}"

    def _extract_phone_from_row(self, row, chat_name: str) -> str:
        """
        Extract phone number - only reliable methods.
        Phone is optional now since we send by name!
        """
        import re
        
        # METHOD 1: Contact Database (BEST - 100% reliable if contact exists)
        if chat_name in CONTACTS:
            phone = CONTACTS[chat_name]
            self.logger.info(f"✓ Database lookup: {chat_name} -> {phone}")
            return phone
        
        # METHOD 2: Check if chat name IS a phone number (unsaved contacts)
        title_elem = row.query_selector('span[title]')
        if title_elem:
            title_text = title_elem.get_attribute('title')
            digits_only = re.sub(r'\D', '', title_text)
            if len(digits_only) >= 10:
                self.logger.info(f"✓ Phone from title: {chat_name} -> {digits_only}")
                return digits_only
        
        # That's it! Phone is optional - we send by name
        self.logger.debug(f"No phone extracted for: {chat_name} (will send by name)")
        return "NOT_EXTRACTED"

    def check_for_updates(self) -> list:
        """Check WhatsApp Web for ALL unread messages."""
        unread_messages = []

        try:
            with sync_playwright() as p:
                # Launch browser with persistent session
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage'],
                    timeout=60000
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                try:
                    # Navigate to WhatsApp
                    self.logger.info("Opening WhatsApp Web...")
                    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)

                    # Wait longer for page to load
                    self.logger.info("Waiting for page to load (30 seconds max)...")
                    time.sleep(5)

                    # Try multiple selectors to find chat list
                    chat_rows = []
                    selectors = [
                        'div[role="row"]',
                        'div[data-testid="chat"]',
                        'div[class*="chat-list"] div[role="listitem"]',
                        'div[class*="_ak4d"]'
                    ]

                    for selector in selectors:
                        try:
                            page.wait_for_selector(selector, timeout=5000)
                            chat_rows = page.query_selector_all(selector)
                            if chat_rows:
                                self.logger.info(f"Found chat list using: {selector}")
                                break
                        except:
                            continue

                    if not chat_rows:
                        self.logger.error("Could not find chat list - page may not be loaded")
                        self.logger.info("Please check if you're logged in to WhatsApp Web")
                        time.sleep(10)  # Give time to inspect
                        return []

                    # Get unread messages
                    unread_messages = self._check_messages_in_page(page, chat_rows)

                except Exception as e:
                    self.logger.error(f"Error accessing WhatsApp Web: {e}")
                    self.logger.info("If QR code shows, please scan it")
                    time.sleep(10)

                finally:
                    browser.close()

        except Exception as e:
            self.logger.error(f"Error in WhatsApp watcher: {e}")

        return unread_messages

    def _check_messages_in_page(self, page, chat_rows) -> list:
        """Check for unread messages - look for GREEN UNREAD COUNT BADGE"""
        unread_messages = []

        try:
            # Wait for chat list
            page.wait_for_selector('div[role="row"]', timeout=5000)
            time.sleep(2)

            # Find all chat rows
            chat_rows = page.query_selector_all('div[role="row"]')
            self.logger.info(f"Found {len(chat_rows)} chat rows")

            for idx, row in enumerate(chat_rows):
                try:
                    # Get chat name from the span with title
                    chat_name_elem = row.query_selector('span[title]')
                    if not chat_name_elem:
                        continue
                    chat_name = chat_name_elem.get_attribute('title')
                    if not chat_name:
                        continue

                    # Check if it's a group (has ~ prefix before the message)
                    # In your HTML: <span>~ zohaibsamia64</span> means it's a group
                    is_group = False
                    preview_div = row.query_selector('div._ak8k')  # This div contains the message preview
                    if preview_div:
                        preview_html = preview_div.inner_text()
                        # Groups show "~ username" before the message
                        if preview_html.strip().startswith('~'):
                            is_group = True
                            self.logger.info(f"Skipping group: {chat_name}")

                    # Skip groups - only process single chats
                    if is_group:
                        continue

                    # Get the ACTUAL message text from the correct location
                    # In your HTML, the message is in: div._ak8k > span[dir="ltr"]
                    msg_elem = None
                    if preview_div:
                        # Look for the span with the actual message (dir="ltr")
                        msg_elem = preview_div.query_selector('span[dir="ltr"]')

                    if msg_elem:
                        msg_text = msg_elem.inner_text().strip()
                    else:
                        # Fallback: get all text from preview div and clean it
                        if preview_div:
                            full_text = preview_div.inner_text()
                            # Remove the "~ username" part if present
                            if full_text.startswith('~'):
                                # Find the ": " separator and get text after it
                                parts = full_text.split(': ', 1)
                                if len(parts) > 1:
                                    msg_text = parts[1].strip()
                                else:
                                    msg_text = ""
                            else:
                                msg_text = full_text.strip()
                        else:
                            msg_text = ""

                    if not msg_text or len(msg_text) < 2:
                        continue

                    self.logger.info(f"Chat {idx}: {chat_name} - '{msg_text[:50]}...'")

                    # Look for unread badge - WhatsApp uses aria-label="X unread messages"
                    has_unread = False

                    # Check for aria-label containing "unread messages" or "unread message"
                    unread_badge = row.query_selector('[aria-label*="unread messages"], [aria-label*="unread message"]')
                    if unread_badge:
                        has_unread = True
                        aria_text = unread_badge.get_attribute('aria-label')
                        self.logger.info(f"Found unread badge: {aria_text}")

                    # Also check for the green badge with numbers (999+, 99+, etc.)
                    if not has_unread:
                        all_spans = row.query_selector_all('span')
                        for span in all_spans:
                            span_text = span.inner_text().strip()
                            if span_text and (span_text.isdigit() or span_text == '999+' or span_text == '99+'):
                                has_unread = True
                                self.logger.info(f"Found unread count: {span_text}")
                                break

                    if has_unread:
                        self.logger.info(f"✓ UNREAD from {chat_name}: {msg_text[:50]}...")

                        # Extract phone number with multiple fallback methods
                        # Methods 1-3 only (non-invasive, no clicking)
                        phone = self._extract_phone_from_row(row, chat_name)

                        unread_messages.append({
                            'text': msg_text,
                            'chat': chat_name,
                            'phone': phone,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        self.logger.debug(f"Read: {chat_name}")

                except Exception as e:
                    self.logger.debug(f"Error parsing row {idx}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking messages: {e}")

        return unread_messages

    def create_action_file(self, item: dict) -> Path:
        """Create whatsapp_{timestamp}.md file in data/watcher_output/ folder."""
        msg_hash = self._hash_message(item['text'], item['chat'])

        self.logger.info(f"Checking if message already processed... (hash: {msg_hash})")

        # Skip if already processed
        if msg_hash in self._processed_messages:
            self.logger.warning(f"Message already processed, skipping: {item['chat']}")
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

        # Save to watcher_output folder (where processor looks)
        watcher_output = Path('data/watcher_output')
        watcher_output.mkdir(parents=True, exist_ok=True)
        action_file = watcher_output / f"whatsapp_{timestamp}.md"

        self.logger.info(f"Creating action file: {action_file}")

        content = f"""---
source: whatsapp_watcher
from: {item['chat']}
phone: {item.get('phone', '') or 'NOT_EXTRACTED'}
received: {item['timestamp']}
subject: WhatsApp message from {item['chat']}
---

## Message

**From:** {item['chat']}

**Content:**
{item['text']}
"""

        action_file.write_text(content, encoding='utf-8')
        self.logger.info(f"SUCCESS: Created action file: {action_file.name}")

        # Mark as processed
        self._save_processed_message(msg_hash)

        return action_file

    def run(self):
        """Run WhatsApp watcher with PERSISTENT browser - no reopening"""
        self.logger.info("Starting WhatsApp watcher with persistent browser...")

        try:
            with sync_playwright() as p:
                # Launch browser ONCE and keep it open
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage'],
                    timeout=120000  # 2 minutes timeout for initial load
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Initial load - wait longer for WhatsApp to load chats
                self.logger.info("Opening WhatsApp Web for the first time...")
                self.logger.info("If QR code shows, please scan it now")
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=120000)

                # Wait for chat list with MUCH longer timeout
                self.logger.info("Waiting for chat list to load (up to 2 minutes)...")
                self.logger.info("WhatsApp may take time to load all chats")
                time.sleep(15)  # Initial wait

                # Try to find chat list - wait up to 2 minutes
                chat_rows = []
                selectors = [
                    'div[role="row"]',
                    'div[data-testid="chat"]',
                    'div[class*="_ak4d"]'
                ]

                # Try for 2 minutes (24 attempts x 5 seconds)
                for attempt in range(24):
                    for selector in selectors:
                        try:
                            chat_rows = page.query_selector_all(selector)
                            if chat_rows and len(chat_rows) > 0:
                                self.logger.info(f"✓ Found {len(chat_rows)} chats using: {selector}")
                                break
                        except Exception as e:
                            self.logger.debug(f"Selector {selector} failed: {e}")

                    if chat_rows and len(chat_rows) > 0:
                        break

                    if (attempt + 1) % 6 == 0:  # Every 30 seconds
                        self.logger.info(f"Still loading chats... ({attempt+1}/24 attempts)")
                        self.logger.info("Keep browser open - don't close it")
                    time.sleep(5)

                if not chat_rows or len(chat_rows) == 0:
                    self.logger.error("Could not find chat list after 2 minutes")
                    self.logger.info("Please check:")
                    self.logger.info("  1. Are you logged in to WhatsApp Web?")
                    self.logger.info("  2. Do you see chats in the browser?")
                    self.logger.info("  3. Is your internet connection working?")
                    self.logger.info("Keeping browser open for 5 minutes for manual inspection...")
                    time.sleep(300)  # Keep open 5 minutes for inspection
                    browser.close()
                    return

                self.logger.info(f"✓ Chat list loaded successfully with {len(chat_rows)} chats")

                # Now keep checking without reopening browser
                check_count = 0
                while True:
                    try:
                        check_count += 1
                        self.logger.info(f"\nChecking for messages... (check #{check_count})")

                        # Don't navigate - just work with the current page
                        # The page is already loaded, just need to check for updates
                        time.sleep(2)  # Small wait for any updates to render

                        # Try to get fresh chat rows from current page
                        try:
                            fresh_chat_rows = page.query_selector_all('div[role="row"]')
                            if fresh_chat_rows and len(fresh_chat_rows) > 0:
                                chat_rows = fresh_chat_rows
                                self.logger.debug(f"Updated chat rows: {len(chat_rows)}")
                        except Exception as nav_err:
                            self.logger.debug(f"Could not refresh chat rows: {nav_err}")
                            # Continue with existing chat_rows

                        # Get unread messages
                        items = self._check_messages_in_page(page, chat_rows)

                        if items:
                            self.logger.info(f"✓ Found {len(items)} unread message(s)!")
                            for item in items:
                                self.create_action_file(item)
                        else:
                            self.logger.info("No unread messages")

                        # Wait before next check
                        self.logger.info(f"Waiting {self.check_interval} seconds...")
                        time.sleep(self.check_interval)

                    except KeyboardInterrupt:
                        self.logger.info("\nStopping watcher...")
                        break
                    except Exception as e:
                        self.logger.error(f"Error in check loop: {e}")
                        time.sleep(10)

                browser.close()

        except Exception as e:
            self.logger.error(f"Error in WhatsApp watcher: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))
    ])

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
                headless=False,
                args=['--disable-gpu', '--no-sandbox']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://web.whatsapp.com', wait_until='networkidle')

            print("\nScan the QR code with WhatsApp on your phone...")
            print("Waiting for login (60 seconds max)...")

            try:
                page.wait_for_selector('div[role="row"]', timeout=60000)
                print("\nLogin detected - starting monitoring...")
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
