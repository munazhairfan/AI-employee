"""
WhatsApp DEBUG - Shows actual HTML structure so we can fix selectors
"""

from playwright.sync_api import sync_playwright
import time

print("=" * 60)
print("WHATSAPP DEBUG - Finding Unread Badge Selectors")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir='whatsapp_session',
        headless=False,
        args=['--disable-gpu', '--no-sandbox']
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("\nOpening WhatsApp Web...")
    page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
    
    print("Waiting for chat list...")
    page.wait_for_selector('div[role="row"]', timeout=10000)
    time.sleep(3)
    
    # Get all chat rows
    chat_rows = page.query_selector_all('div[role="row"]')
    print(f"\n✓ Found {len(chat_rows)} chat rows")
    
    for idx, row in enumerate(chat_rows[:10]):  # Check first 10 rows
        try:
            # Get chat name
            chat_name_elem = row.query_selector('span[title]')
            chat_name = chat_name_elem.get_attribute('title') if chat_name_elem else 'Unknown'
            
            # Get message text
            msg_elem = row.query_selector('span[dir="auto"]')
            msg_text = msg_elem.inner_text().strip()[:50] if msg_elem else 'Unknown'
            
            # Get ALL spans in this row
            all_spans = row.query_selector_all('span')
            
            print(f"\n--- Chat {idx}: {chat_name} ---")
            print(f"Message: '{msg_text}'")
            print(f"Total spans: {len(all_spans)}")
            
            # Check each span
            for i, span in enumerate(all_spans):
                span_text = span.inner_text().strip()
                span_class = span.get_attribute('class') or ''
                aria_label = span.get_attribute('aria-label') or ''
                
                # Only show spans with content
                if span_text or span_class or aria_label:
                    print(f"  Span {i}:")
                    if span_text:
                        print(f"    Text: '{span_text}'")
                    if span_class:
                        print(f"    Class: '{span_class}'")
                    if aria_label:
                        print(f"    Aria-label: '{aria_label}'")
                    
                    # Check if this looks like an unread badge
                    if span_text.isdigit() and len(span_text) <= 2:
                        print(f"    >>> NUMBER BADGE FOUND: {span_text}")
                    if 'unread' in span_class.lower():
                        print(f"    >>> UNREAD CLASS FOUND!")
                    if 'unread' in aria_label.lower():
                        print(f"    >>> UNREAD ARIA-LABEL FOUND!")
            
            # Check for divs too
            all_divs = row.query_selector_all('div')
            for i, div in enumerate(all_divs[:5]):  # First 5 divs
                div_class = div.get_attribute('class') or ''
                if 'unread' in div_class.lower() or 'badge' in div_class.lower():
                    print(f"  Div {i}: Class='{div_class}'")
            
        except Exception as e:
            print(f"Error on row {idx}: {e}")
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60)
    print("\nLook at the output above and tell me:")
    print("1. Which span has the unread count number?")
    print("2. What class does it have?")
    print("3. What aria-label does it have?")
    print("\nKeep browser open for inspection...")
    
    input("\nPress Enter when done inspecting...")
    browser.close()
