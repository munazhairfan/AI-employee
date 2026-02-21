import re

def parse_email_request(content: str):
    content_lower = content.lower()
    
    email_indicators = ['send email', 'send an email', 'email to', 'email:', 
                        'send mail', 'send a mail', 'compose email', 'to:']
    if not any(ind in content_lower for ind in email_indicators):
        return None
    
    email_data = {'to': None, 'subject': None, 'body': None}
    
    # Pattern 1: "to: email" format (structured, one per line)
    to_match = re.search(r'^to:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content, re.IGNORECASE | re.MULTILINE)
    subject_match = re.search(r'^subject:\s*(.+)$', content, re.IGNORECASE | re.MULTILINE)
    body_match = re.search(r'^body:\s*(.+)$', content, re.IGNORECASE | re.MULTILINE)
    
    if to_match:
        email_data['to'] = to_match.group(1).strip()
    if subject_match:
        email_data['subject'] = subject_match.group(1).strip()
    if body_match:
        email_data['body'] = body_match.group(1).strip()
    
    if email_data['to']:
        return email_data
    
    return None

# Test
content = """---
type: file_drop
original_name: email_request.txt
size: 129
---

to: m.irfan.ahmed543@gmail.com
subject: Project update
body: Hi munazha, the project is on track.
"""

print("Testing parse_email_request")
result = parse_email_request(content)
print(f"Result: {result}")
