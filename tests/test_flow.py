import sys
sys.path.insert(0, '.')
from src.orchestrator import parse_email_request, check_requires_approval, parse_frontmatter
from pathlib import Path

# Read test file
test_file = Path("AI_Employee_Vault/Needs_Action/test_email.txt.md")
if not test_file.exists():
    # Check without .md
    test_file = Path("AI_Employee_Vault/Needs_Action/test_email.txt")
    
if test_file.exists():
    content = test_file.read_text(encoding='utf-8')
    print(f"=== File Content ===")
    print(content)
    print()
    
    metadata = parse_frontmatter(content)
    print(f"=== Metadata ===")
    print(f"Type: {metadata.get('type', 'unknown')}")
    print()
    
    result = parse_email_request(content)
    print(f"=== Email Parser Result ===")
    print(f"Result: {result}")
    print()
    
    needs_approval = check_requires_approval(content, metadata, metadata.get('type', 'unknown'))
    print(f"=== Approval Check ===")
    print(f"Needs approval: {needs_approval}")
else:
    print(f"File not found: {test_file}")
    print("\nLooking for .md files in Needs_Action:")
    for f in Path("AI_Employee_Vault/Needs_Action").glob("*.md"):
        print(f"  - {f.name}")
