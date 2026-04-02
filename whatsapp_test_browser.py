"""
WhatsApp Test - Just opens browser so you can see what's happening
"""

from playwright.sync_api import sync_playwright
import time

print("=" * 60)
print("WHATSAPP TEST - Manual Inspection")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir='whatsapp_session_test',
        headless=False,
        args=['--disable-gpu', '--no-sandbox']
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("\nOpening WhatsApp Web...")
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)
    
    print("\n" + "=" * 60)
    print("BROWSER IS OPEN")
    print("=" * 60)
    print("\nPlease check:")
    print("1. Do you see a QR code? → Scan it with your phone")
    print("2. Do you see chat list? → Tell me what you see")
    print("3. Are there unread messages? → Note which chats have green badges")
    print("\nKeep browser open for 2 minutes for inspection...")
    
    time.sleep(120)
    
    print("\nClosing browser...")
    browser.close()
