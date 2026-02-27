"""
WhatsApp Web Sender - Super Simple Debug
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

print("="*60)
print("WhatsApp Sender - Debug Mode")
print("="*60)

contact = sys.argv[1] if len(sys.argv) > 1 else "Rockstar"
message = sys.argv[2] if len(sys.argv) > 2 else "Test"

print(f"\nContact: {contact}")
print(f"Message: {message}")
print("\nStarting browser...")

try:
    with sync_playwright() as p:
        print("✓ Playwright started")
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=Path('whatsapp_session'),
            headless=False,
            args=['--window-size=1920,1080']
        )
        print("✓ Browser launched")
        
        page = browser.pages[0]
        
        print("Loading WhatsApp Web...")
        page.goto('https://web.whatsapp.com', wait_until='networkidle', timeout=30000)
        print("✓ WhatsApp Web loaded")
        
        time.sleep(5)
        
        # Save screenshot
        page.screenshot(path='debug_whatsapp_1.png')
        print("✓ Screenshot 1 saved: debug_whatsapp_1.png")
        
        print(f"\nSearching for '{contact}'...")
        page.keyboard.press('Control+n')
        time.sleep(1)
        page.keyboard.type(contact)
        time.sleep(3)
        
        page.screenshot(path='debug_whatsapp_2.png')
        print("✓ Screenshot 2 saved: debug_whatsapp_2.png")
        
        print("Selecting contact...")
        page.keyboard.press('Enter')
        time.sleep(5)
        
        page.screenshot(path='debug_whatsapp_3.png')
        print("✓ Screenshot 3 saved: debug_whatsapp_3.png")
        
        print(f"\nTyping message: '{message}'")
        page.keyboard.type(message)
        time.sleep(2)
        
        page.screenshot(path='debug_whatsapp_4.png')
        print("✓ Screenshot 4 saved: debug_whatsapp_4.png")
        
        print("Sending...")
        
        # Try send button first
        try:
            send_btn = page.locator('[aria-label="Send"]').first
            send_btn.click()
            print("✓ Clicked send button")
        except:
            print("Send button not found, pressing Enter")
            page.keyboard.press('Enter')
        
        time.sleep(3)
        
        page.screenshot(path='debug_whatsapp_5.png')
        print("✓ Screenshot 5 saved: debug_whatsapp_5.png")
        
        print("\nChecking if message was sent...")
        try:
            bubbles = page.locator('div[data-testid="bubble-message"]').all()
            print(f"Found {len(bubbles)} message bubbles")
            
            if bubbles:
                last = bubbles[-1].inner_text()
                print(f"Last message: {last[:50]}")
        except Exception as e:
            print(f"Could not check bubbles: {e}")
        
        browser.close()
        print("\n✓ Browser closed")
        
        print("\n" + "="*60)
        print("DONE! Check the debug_whatsapp_*.png files")
        print("="*60)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nMake sure:")
    print("1. WhatsApp Web is logged in")
    print("2. Contact 'Rockstar' exists in your WhatsApp")
    print("3. Internet is working")
