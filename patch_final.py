# Patch to add name search AND fix message extraction order

with open('src/whatsapp_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add name extraction
old_phone = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract message - try multiple patterns in order of preference'''

new_phone = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract customer_name for searching by name
    name_match = re.search(r'\\|\\s*customer_name\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    customer_name = name_match.group(1).strip() if name_match else None
    
    # Extract message - try multiple patterns in STRICT order (table FIRST)'''

if old_phone in content:
    content = content.replace(old_phone, new_phone)
    print('1. Added name extraction')

# 2. Fix pattern order - table FIRST, Intent LAST
old_patterns = '''    # Pattern 1: Extract from Intent line - look for "with content '...'"
    intent_match = re.search(r"\\*\\*Intent:\\*\\*.*?with content ['\\\"](.+?)['\\\"]", content)
    if intent_match:
        message = intent_match.group(1)
        print(f"[DEBUG] Extracted from Intent (pattern 1): {message}")

    # Pattern 2: Look for quoted text after "Send WhatsApp message"
    if not message:
        send_match = re.search(r"Send WhatsApp message.*?['\\\"](.+?)['\\\"]$", content, re.MULTILINE)
        if send_match:
            message = send_match.group(1)
            print(f"[DEBUG] Extracted from Send pattern (pattern 2): {message}")

    # Pattern 3: From table (suggested_reply field)
    if not message:
        message_match = re.search(r'\\|\\s*suggested_reply\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
        if message_match:
            message = message_match.group(1).strip()
            print(f"[DEBUG] Extracted from table (pattern 3): {message}")'''

new_patterns = '''    # Pattern 1: From table (suggested_reply) - MOST RELIABLE
    message_match = re.search(r'\\|\\s*suggested_reply\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    if message_match:
        message = message_match.group(1).strip()
        # Remove trailing % and confidence
        if '%' in message:
            message = message.split('%')[0].strip()
        print(f"[DEBUG] Extracted from table (pattern 1): {message}")
    
    # Pattern 2: From Intent line - look for "with content '...'"
    if not message:
        intent_match = re.search(r"with content ['\\\"](.+?)['\\\"]", content)
        if intent_match:
            message = intent_match.group(1)
            print(f"[DEBUG] Extracted 'with content' (pattern 2): {message}")
    
    # Pattern 3: Last resort - clean Intent line
    if not message:
        intent_full = re.search(r'\\*\\*Intent:\\*\\*\\s*(.+?)(?:\\n|$)', content)
        if intent_full:
            full_intent = intent_full.group(1).strip()
            # Extract from "with content"
            content_match = re.search(r"with content ['\\\"](.+?)['\\\"]", full_intent)
            if content_match:
                message = content_match.group(1)
            else:
                message = full_intent
            print(f"[DEBUG] Extracted from Intent cleanup (pattern 3): {message}")'''

if old_patterns in content:
    content = content.replace(old_patterns, new_patterns)
    print('2. Fixed pattern order (table first)')

# 3. Add search logic (use name if available)
old_print = '''    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")
    
    if not phone:'''

new_print = '''    # Use name for search if available, otherwise phone
    search_query = customer_name if (customer_name and customer_name != 'UNKNOWN') else phone
    print(f"[DEBUG] Search by: {search_query}")
    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")
    
    if not search_query:'''

if old_print in content:
    content = content.replace(old_print, new_print)
    print('3. Added search logic')

# 4. Update send_whatsapp call
old_call = '''    return send_whatsapp(phone, message)'''
new_call = '''    return send_whatsapp(search_query, message)'''

if old_call in content:
    content = content.replace(old_call, new_call)
    print('4. Updated send_whatsapp call')

# Save
with open('src/whatsapp_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\\nDONE! All patches applied!')
