"""
WhatsApp Integration - Direct Playwright (opens browser from dashboard)
Sends messages by NAME (uses WhatsApp's contact search)
No phone number needed for saved contacts!
"""
import asyncio
from pathlib import Path
import re

SESSION_PATH = Path('data/whatsapp_session')
SESSION_PATH.mkdir(parents=True, exist_ok=True)


def send_whatsapp(phone: str, message: str, contact_name: str = None) -> dict:
    """
    Send WhatsApp using Playwright - opens browser if needed
    
    Args:
        phone: Phone number (optional if contact_name provided)
        message: Message text
        contact_name: Contact name from saved contacts (optional)
    
    Returns:
        dict with success status
    """
    try:
        result = asyncio.run(_send_async(phone, message, contact_name))
        return result
    except Exception as e:
        return {'success': False, 'error': str(e), 'details': {}}


async def _send_async(phone: str, message: str, contact_name: str = None) -> dict:
    """Send WhatsApp message - opens visible browser"""
    from playwright.async_api import async_playwright

    # Determine who to send to
    if contact_name:
        search_query = contact_name  # Use name for saved contacts
        print(f"\n  Sending to: {contact_name} (by name)")
    elif phone:
        search_query = phone  # Use number for unsaved contacts
        print(f"\n  Sending to: {phone} (by number)")
    else:
        return {'success': False, 'error': 'No phone or contact name provided', 'details': {}}

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

        # CRITICAL: Wait for chat list to fully load
        print("  Waiting for chat list to load...")

        try:
            await page.wait_for_selector('#pane-side', timeout=60000)
            print("  Chat list found!")
            await page.wait_for_timeout(5000)
        except:
            await context.close()
            return {'success': False, 'error': 'Chat list did not load. Check internet connection.', 'details': {}}

        # Now send message using NAME or NUMBER
        try:
            # Find search box
            search = await page.query_selector('div[role="search"] input')
            if not search:
                search = await page.query_selector('#side input[placeholder*="Search"]')

            if not search:
                await context.close()
                return {'success': False, 'error': 'Search box not found', 'details': {}}

            # Click and type the NAME or NUMBER
            await search.click()
            await page.wait_for_timeout(500)
            await page.keyboard.type(search_query)
            await page.wait_for_timeout(3000)

            # Press Enter to open chat
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(5000)  # Longer wait for chat to open

            # Check if chat opened successfully
            chat_header = await page.query_selector('header')
            if not chat_header:
                await context.close()
                return {'success': False, 'error': f'Chat not found: {search_query}', 'details': {}}

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

            # Wait for message to actually send
            print("  Waiting for message to send...")
            await page.wait_for_timeout(5000)

            # Verify message was sent
            sent_messages = await page.query_selector_all('span[title^="Sent"], span[title^="Delivered"], div.message-out')
            if len(sent_messages) > 0:
                print(f"  ✓ Message confirmed sent! ({len(sent_messages)} messages in chat)")
            else:
                print("  ⚠️  Could not verify message was sent")

            await context.close()
            return {
                'success': True, 
                'message': f'Sent to {contact_name or phone}', 
                'details': {
                    'phone': phone,
                    'contact_name': contact_name,
                    'search_query': search_query
                }
            }

        except Exception as e:
            await context.close()
            return {'success': False, 'error': f'Send failed: {str(e)}', 'details': {}}


def execute_whatsapp_task(content, task_file):
    """Execute WhatsApp task - supports both name and phone"""
    import re

    # Extract phone from table
    phone_match = re.search(r'\|\s*customer_phone\s*\|\s*([^\|]+)\s*\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract contact name from table (customer_name field)
    name_match = re.search(r'\|\s*customer_name\s*\|\s*([^\|]+)\s*\|', content)
    contact_name = name_match.group(1).strip() if name_match else None
    
    # Fallback: Extract from "from" field (for watcher messages)
    if not contact_name:
        from_match = re.search(r'\|\s*from\s*\|\s*([^\|]+)\s*\|', content)
        contact_name = from_match.group(1).strip() if from_match else None

    # Extract message - try multiple patterns
    message = None

    # Pattern 1: From Intent line
    intent_match = re.search(r"\*\*Intent:\*\*.*?with content ['\"](.+?)['\"]", content)
    if intent_match:
        message = intent_match.group(1)
        print(f"[DEBUG] Extracted from Intent (pattern 1): {message}")

    # Pattern 2: From suggested_reply
    if not message:
        message_match = re.search(r'\|\s*suggested_reply\s*\|\s*([^\|]+)\s*\|', content)
        if message_match:
            message = message_match.group(1).strip()
            print(f"[DEBUG] Extracted from table (pattern 2): {message}")
    
    # Pattern 3: From message_content field
    if not message:
        msg_content_match = re.search(r'\|\s*message_content\s*\|\s*([^\|]+)\s*\|', content)
        if msg_content_match:
            message = msg_content_match.group(1).strip()
            print(f"[DEBUG] Extracted message_content (pattern 3): {message}")

    # Clean phone (remove %, spaces, etc.)
    if phone and '%' in phone:
        phone = phone.split('%')[0].strip()

    # Clean message
    if message:
        message = message.replace('**', '').replace('*', '').strip()
        # Remove surrounding quotes
        if (message.startswith("'") and message.endswith("'")) or \
           (message.startswith('"') and message.endswith('"')):
            message = message[1:-1]

    print(f"[FINAL] Contact Name: {contact_name}")
    print(f"[FINAL] Phone: {phone}")
    print(f"[FINAL] Message: {message}")

    # Determine what to use
    if not contact_name and not phone:
        return {'success': False, 'error': 'WhatsApp failed: Missing both contact name and phone number', 'details': {}}
    if not message or len(message) < 2:
        return {'success': False, 'error': 'WhatsApp failed: Missing message content', 'details': {}}

    # Send using name if available, otherwise use phone
    return send_whatsapp(phone, message, contact_name)
