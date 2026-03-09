import re

# Read the file
with open('src/whatsapp_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the execute_whatsapp_task function and add name extraction
old_code = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract message'''

new_code = '''    # Extract phone from table
    phone_match = re.search(r'\\|\\s*customer_phone\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    phone = phone_match.group(1).strip() if phone_match else None
    
    # Extract customer_name for searching by name
    name_match = re.search(r'\\|\\s*customer_name\\s*\\|\\s*([^\\|]+)\\s*\\|', content)
    customer_name = name_match.group(1).strip() if name_match else None
    
    # Extract message'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print('SUCCESS: Added name extraction')
    
    # Also need to use customer_name for search
    old_search = '''    # Determine what to search for: name if available, otherwise phone
    search_query = None
    if customer_name and customer_name != 'UNKNOWN':
        search_query = customer_name
        print(f"[DEBUG] Will search by NAME: {customer_name}")
    elif phone:
        search_query = phone
        print(f"[DEBUG] Will search by PHONE: {phone}")'''
    
    if old_search not in content:
        # Add search logic before the print statements
        old_print = '''    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")'''
        
        new_print = '''    # Use name for search if available, otherwise phone
    search_query = customer_name if (customer_name and customer_name != 'UNKNOWN') else phone
    print(f"[DEBUG] Search by: {search_query}")
    print(f"[DEBUG] Phone: {phone}")
    print(f"[DEBUG] Message: {message}")'''
        
        if old_print in content:
            content = content.replace(old_print, new_print)
            print('SUCCESS: Added search logic')
    
    # Update send_whatsapp call to use search_query
    old_call = '''    return send_whatsapp(phone, message)'''
    new_call = '''    return send_whatsapp(search_query, message)'''
    
    if old_call in content:
        content = content.replace(old_call, new_call)
        print('SUCCESS: Updated send_whatsapp call')
    
    # Save
    with open('src/whatsapp_integration.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE!')
else:
    print('FAIL: Pattern not found')
