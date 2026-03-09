# Simple patch - just add name extraction, don't touch message patterns

with open('src/whatsapp_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add name extraction after phone extraction
old = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract message'''

new = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract customer_name for searching by name
    name_match = re.search(r'\\|\\s*customer_name\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    customer_name = name_match.group(1).strip() if name_match else None
    
    # Extract message'''

if old in content:
    content = content.replace(old, new)
    print('1. Added name extraction')
else:
    print('FAIL: Pattern not found')
    exit()

# Add search logic before print statements
old_print = '''    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")
    
    if not phone:'''

new_print = '''    # Search by name if available, otherwise phone
    search_query = customer_name if (customer_name and customer_name != 'UNKNOWN') else phone
    print(f"[DEBUG] Search: {search_query}")
    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")
    
    if not search_query:'''

if old_print in content:
    content = content.replace(old_print, new_print)
    print('2. Added search logic')
else:
    print('FAIL: Print pattern not found')
    exit()

# Update send_whatsapp call
old_call = '''    return send_whatsapp(phone, message)'''
new_call = '''    return send_whatsapp(search_query, message)'''

if old_call in content:
    content = content.replace(old_call, new_call)
    print('3. Updated send call')
else:
    print('FAIL: Call pattern not found')
    exit()

# Save
with open('src/whatsapp_integration.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\\nSUCCESS! All patches applied!')
print('Now searches by NAME if available, otherwise PHONE')
print('Message extraction unchanged (still works as before)')
