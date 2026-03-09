import re

# Simulate actual task file content
content = """---
type: whatsapp_reply
auto_generated: true
customer_name: Sar Dard
customer_phone: +923242815608
ai_confidence: 100
---

# AI-Generated Task

**Intent:** Send WhatsApp message to Sar Dard with the given content

**Priority:** NORMAL

## Extracted Information

| Field | Value | Confidence |
|-------|-------|------------|
| customer_name | Sar Dard | 100% |
| customer_phone | +923242815608 | 100% |

## Suggested Reply

| suggested_reply | Hello! We are testing again for naming convention. | 100% |

---

## Approval Actions

- [ ] Approve
"""

print("=== TESTING MESSAGE EXTRACTION ===\n")

# Pattern 1: From table (suggested_reply) - MOST RELIABLE
message_match = re.search(r'\|\s*suggested_reply\s*\|\s*([^\|]+)\s*\|', content)
if message_match:
    message = message_match.group(1).strip()
    if '%' in message:
        message = message.split('%')[0].strip()
    print(f"OK Pattern 1 (TABLE): '{message}'")
else:
    print("FAIL Pattern 1: NOT FOUND")

# Pattern 2: From Intent line
if not message:
    intent_match = re.search(r"with content ['\"](.+?)['\"]", content)
    if intent_match:
        message = intent_match.group(1)
        print(f"OK Pattern 2 (with content): '{message}'")
    else:
        print("FAIL Pattern 2: NOT FOUND")

# Pattern 3: Intent cleanup
if not message:
    intent_full = re.search(r'\*\*Intent:\*\*\s*(.+?)(?:\n|$)', content)
    if intent_full:
        message = intent_full.group(1).strip()
        print(f"OK Pattern 3 (Intent): '{message}'")
    else:
        print("FAIL Pattern 3: NOT FOUND")

print(f"\n=== FINAL MESSAGE: '{message}' ===")
print("EXPECTED: 'Hello! We are testing again for naming convention.'")
