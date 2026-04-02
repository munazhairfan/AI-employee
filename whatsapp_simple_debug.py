"""
WhatsApp Simple Debug - Just shows what's on the page
"""

from playwright.sync_api import sync_playwright
import time

print("=" * 60)
print("WHATSAPP SIMPLE DEBUG")
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
    
    print("\nWaiting 10 seconds for page to load...")
    print("If QR code shows, scan it now!")
    time.sleep(10)
    
    # Take screenshot
    page.screenshot(path='whatsapp_debug.png')
    print("\n✓ Screenshot saved: whatsapp_debug.png")
    
    # Save page HTML
    html = page.content()
    with open('whatsapp_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ HTML saved: whatsapp_debug.html")
    
    # Try to find chat rows with different selectors
    selectors_to_try = [
        'div[role="row"]',
        'div[class*="chat"]',
        'div[class*="row"]',
        'div[class*="list"]',
        'div[class*="chatlist"]',
        'div[data-testid="chat"]',
        'div[data-testid="chat-list"]',
        'div[class*="unread"]',
    ]
    
    print("\n\nTrying different selectors:")
    print("=" * 60)
    
    for selector in selectors_to_try:
        try:
            elements = page.query_selector_all(selector)
            print(f"✓ '{selector}' → Found {len(elements)} elements")
            
            if len(elements) > 0:
                # Get details of first element
                first = elements[0]
                print(f"    First element class: {first.get_attribute('class')}")
                print(f"    First element text: {first.inner_text()[:100]}")
        except Exception as e:
            print(f"✗ '{selector}' → Error: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("KEEP BROWSER OPEN - Inspect it manually!")
    print("=" * 60)
    print("\n1. Open whatsapp_debug.png to see screenshot")
    print("2. Open whatsapp_debug.html in browser to inspect HTML")
    print("3. Right-click on an unread chat → Inspect Element")
    print("4. Tell me the class/aria-label of the unread badge")
    print("\nPress Enter when done...")
    input()
    
    browser.close()
