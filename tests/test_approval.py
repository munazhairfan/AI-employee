import re
import requests
from pathlib import Path

# Read the approval file
approval_file = Path("AI_Employee_Vault/Pending_Approval/FILE_fresh_test.txt_Approval.md")
content = approval_file.read_text(encoding='utf-8')

print("=== Approval File Content ===")
print(content[:500])
print()

# Check if approved
if 'status: approved\n' in content:
    print("✓ File is approved")
    
    # Extract metadata
    metadata = {}
    if '---' in content:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            meta_section = parts[1]
            for line in meta_section.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
    
    print(f"Action type: {metadata.get('action_type', 'unknown')}")
    print(f"MCP endpoint: {metadata.get('mcp_endpoint', '')}")
    
    # Extract email details
    to_match = re.search(r'\*\*To:\*\* (.+)', content)
    subject_match = re.search(r'\*\*Subject:\*\* (.+)', content)
    body_match = re.search(r'\*\*Body:\*\*\n(.+?)(?=\n\n|\n##|$)', content, re.DOTALL)
    
    if to_match:
        email_data = {
            'to': to_match.group(1).strip(),
            'subject': subject_match.group(1).strip() if subject_match else 'No subject',
            'body': body_match.group(1).strip() if body_match else ''
        }
        print(f"\n=== Email Data ===")
        print(f"To: {email_data['to']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Body: {email_data['body'][:50]}...")
        
        # Call MCP endpoint
        mcp_endpoint = metadata.get('mcp_endpoint', '')
        if mcp_endpoint:
            print(f"\n=== Calling MCP Endpoint ===")
            print(f"POST {mcp_endpoint}")
            try:
                response = requests.post(mcp_endpoint, json=email_data, timeout=10)
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
            except Exception as e:
                print(f"Error: {e}")
else:
    print("✗ File is NOT approved yet")
    print("Edit the file and change 'status: pending_approval' to 'status: approved'")
