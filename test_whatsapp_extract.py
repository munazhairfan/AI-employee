import re

# Test content (simulating a real task file)
content = """---
type: whatsapp_reply
customer_name: Sar Dard
customer_phone: +923242815608
---

**Intent:** Send WhatsApp message to Sar Dard with the given content

## Suggested Reply

| suggested_reply | Hello! We are testing again for naming convention. | 100% |
"""

print("=== TESTING MESSAGE EXTRACTION ===\n")

# Pattern 1: Table field
message_match = re.search(r'\|\s*suggested_reply\s*\|\s*([^\|]+)\s*\|', content)
if message_match:
    message = message_match.group(1).strip()
    if '%' in message:
        message = message.split('%')[0].strip()
    print(f"OK Pattern 1 (table): '{message}'")
else:
    print("FAIL Pattern 1: NOT FOUND")

# Pattern 2: Intent line  
intent_full = re.search(r'\*\*Intent:\*\*\s*(.+?)(?:\n|$)', content)
if intent_full:
    print(f"OK Pattern 2 (intent): '{intent_full.group(1).strip()}'")
else:
    print("FAIL Pattern 2: NOT FOUND")

print("\n=== EXPECTED: 'Hello! We are testing again for naming convention.' ===")
