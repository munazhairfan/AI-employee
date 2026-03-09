"""
WhatsApp Integration - Direct Playwright (opens browser from dashboard)
No local agent needed - works directly from dashboard
"""
import asyncio
from pathlib import Path
import re

SESSION_PATH = Path('data/whatsapp_session')
SESSION_PATH.mkdir(parents=True, exist_ok=True)


def send_whatsapp(phone: str, message: str) -> dict:
    """Send WhatsApp using Playwright - opens browser if needed"""
    try:
        result = asyncio.run(_send_async(phone, message))
        return result
    except Exception as e:
        return {'success': False, 'error': str(e), 'details': {}}


async def _send_async(phone: str, message: str) -> dict:
    """Send WhatsApp message - opens visible browser"""
    from playwright.async_api import async_playwright
    
    # Clean phone number
    clean_phone = ''.join(c for c in phone if c.isdigit())
    
    async with async_playwright() as p:
        # Launch VISIBLE browser (shows QR if session expired, chats if not)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH.absolute()),
            headless=False,  # VISIBLE - shows QR or chats
            args=['--no-sandbox']
        )
        
        page = context.pages[0]
        
        # Go to WhatsApp Web
        await page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=60000)
        
        # Wait for page to load
        await page.wait_for_timeout(5000)
        
        # Check if QR code is shown (session expired)
        qr = await page.query_selector('canvas[data-icon="qr-placeholder"]')
        
        if qr:
            print("\n  QR Code Required!")
            print("  Please scan QR code in the browser window:")
            print("  1. Open WhatsApp on phone")
            print("  2. Settings > Linked Devices > Link a Device")
            print("  3. Scan QR code in browser")
            print("  Waiting for scan...\n")
            
            # Wait for QR to be scanned (max 3 minutes)
            for i in range(180):
                await page.wait_for_timeout(1000)
                qr_check = await page.query_selector('canvas[data-icon="qr-placeholder"]')
                if not qr_check:
                    print("  QR scanned!\n")
                    # Wait for chats to load after scan
                    await page.wait_for_timeout(5000)
                    break
                if i % 20 == 0 and i > 0:
                    print(f"  Waiting for QR scan... ({i}s)")
            else:
                await context.close()
                return {'success': False, 'error': 'QR code not scanned within 3 minutes', 'details': {}}
        
        # CRITICAL: Wait for chat list to fully load (not just page)
        print("  Waiting for chat list to load...")
        
        # Wait for the chat list panel to appear
        try:
            await page.wait_for_selector('#pane-side', timeout=60000)
            print("  Chat list found!")
            
            # Extra wait for chats to render
            await page.wait_for_timeout(5000)
        except:
            await context.close()
            return {'success': False, 'error': 'Chat list did not load. Please check your internet connection.', 'details': {}}
        
        # Now send message
        try:
            # Find search box
            search = await page.query_selector('div[role="search"] input')
            if not search:
                search = await page.query_selector('#side input[placeholder*="Search"]')
            
            if not search:
                await context.close()
                return {'success': False, 'error': 'Search box not found', 'details': {}}
            
            # Click and type
            await search.click()
            await page.wait_for_timeout(500)
            await page.keyboard.type(clean_phone)
            await page.wait_for_timeout(3000)
            
            # Press Enter to open chat
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(5000)  # Longer wait for chat to open
            
            # Find message input
            msg_box = await page.query_selector('footer div[contenteditable="true"]')
            if not msg_box:
                await context.close()
                return {'success': False, 'error': 'Message input not found', 'details': {}}
            
            # Click, type message
            await msg_box.click()
            await page.wait_for_timeout(500)
            await page.keyboard.type(message)
            await page.wait_for_timeout(1000)
            
            # CLICK the send button (more reliable than Enter)
            send_button = await page.query_selector('button[aria-label="Send"]')
            if send_button:
                await send_button.click()
                print("  Message sent (via send button)!")
            else:
                # Fallback to Enter
                await page.keyboard.press('Enter')
                print("  Message sent (via Enter)!")
            
            # CRITICAL: Wait for message to actually send (watch for tick marks)
            print("  Waiting for message to send...")
            await page.wait_for_timeout(5000)
            
            # Verify message was sent (check for at least one tick)
            sent_messages = await page.query_selector_all('span[title^="Sent"], span[title^="Delivered"], div.message-out')
            if len(sent_messages) > 0:
                print(f"  ✓ Message confirmed sent! ({len(sent_messages)} messages in chat)")
            else:
                print("  ⚠️  Could not verify message was sent")
            
            await context.close()
            return {'success': True, 'message': f'Sent to {clean_phone}', 'details': {'phone': clean_phone}}
        
        except Exception as e:
            await context.close()
            return {'success': False, 'error': f'Send failed: {str(e)}', 'details': {}}


def execute_whatsapp_task(content, task_file):
    """Execute WhatsApp task"""
    import re
    
    # Extract phone from table
    phone_match = re.search(r'\|\s*customer_phone\s*\|\s*([^\|]+)\s*\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract message - try multiple patterns in order of preference
    message = None
    
    # Pattern 1: Extract from Intent line - look for "with content '...'"
    intent_match = re.search(r"\*\*Intent:\*\*.*?with content ['\"](.+?)['\"]", content)
    if intent_match:
        message = intent_match.group(1)
        print(f"[DEBUG] Extracted from Intent (pattern 1): {message}")
    
    # Pattern 2: Look for quoted text after "Send WhatsApp message"
    if not message:
        send_match = re.search(r"Send WhatsApp message.*?['\"](.+?)['\"]$", content, re.MULTILINE)
        if send_match:
            message = send_match.group(1)
            print(f"[DEBUG] Extracted from Send pattern (pattern 2): {message}")
    
    # Pattern 3: From table (suggested_reply field)
    if not message:
        message_match = re.search(r'\|\s*suggested_reply\s*\|\s*([^\|]+)\s*\|', content)
        if message_match:
            message = message_match.group(1).strip()
            print(f"[DEBUG] Extracted from table (pattern 3): {message}")
    
    # Pattern 4: Last resort - use the whole Intent line and clean it
    if not message:
        intent_full = re.search(r'\*\*Intent:\*\*\s*(.+?)(?:\n|$)', content)
        if intent_full:
            message = intent_full.group(1).strip()
            # Try to clean it
            if 'with content' in message:
                clean_match = re.search(r"with content ['\"]?(.+?)['\"]?$", message)
                if clean_match:
                    message = clean_match.group(1)
            print(f"[DEBUG] Extracted from Intent cleanup (pattern 4): {message}")
    
    # Clean phone (remove %, spaces, etc.)
    if phone and '%' in phone:
        phone = phone.split('%')[0].strip()
    
    # Clean message (remove markdown, quotes)
    if message:
        message = message.replace('**', '').replace('*', '').strip()
        # Remove surrounding quotes
        if (message.startswith("'") and message.endswith("'")) or \
           (message.startswith('"') and message.endswith('"')):
            message = message[1:-1]
    
    print(f"[FINAL] Phone: {phone}")
    print(f"[FINAL] Message: {message}")
    
    if not phone:
        return {'success': False, 'error': 'Missing phone number'}
    if not message or len(message) < 2:
        return {'success': False, 'error': 'Missing message content'}
    
    return send_whatsapp(phone, message)
