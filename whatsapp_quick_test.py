"""
WhatsApp Quick Test - Run this yourself
"""

from playwright.sync_api import sync_playwright
import time

print("\n" + "=" * 60)
print("WHATSAPP QUICK TEST")
print("=" * 60)
print("\nThis will open a browser window.")
print("\nPLEASE TELL ME:")
print("1. Did a browser window open? (Yes/No)")
print("2. What do you see? (QR code / Chat list / Blank page)")
print("3. Are there unread messages? (Yes/No)")
print("\nStarting in 3 seconds...")
time.sleep(3)

with sync_playwright() as p:
    print("\n[1/3] Launching browser...")
    browser = p.chromium.launch_persistent_context(
        user_data_dir='whatsapp_session',
        headless=False,
        args=['--disable-gpu', '--no-sandbox']
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("[2/3] Opening WhatsApp Web...")
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)
    
    print("[3/3] Waiting 30 seconds...")
    print("\n" + "=" * 60)
    print("LOOK AT THE BROWSER WINDOW NOW!")
    print("=" * 60)
    print("\nWhat do you see?")
    print("- QR code?")
    print("- Chat list with messages?")
    print("- Blank/error page?")
    print("\n(Tell me what you see so I can fix the code)")
    print("\nWaiting 30 seconds...")
    
    time.sleep(30)
    
    print("\nClosing browser...")
    browser.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nNow tell me what you saw in the browser window!")
