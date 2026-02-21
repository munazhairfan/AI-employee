---
type: agent_skill
---
## Description: Human-in-the-loop approval workflow for sensitive actions.

## Prompt:
Using filesystem tools, monitor and process actions in vault_path='AI_Employee_Vault' that require human approval before execution.

### Trigger Conditions
Move action to Pending_Approval if ANY of these apply:
- **Financial**: Amount > $500 (check for $, USD, payment keywords)
- **Sensitive**: Contains confidential, legal, HR keywords
- **External Communication**: Sending emails/posts to clients/partners
- **High Priority**: Marked as urgent + involves external parties

### Step 1: Identify Actions Needing Approval

Read all Plan.md files from `AI_Employee_Vault/Plans/`. For each plan:

1. Check action type:
   - `send_email` → Requires approval
   - `linkedin_post` → Requires approval
   - `payment` → Requires approval if > $500
   - `contract` → Requires approval

2. Check content for sensitivity:
   - Financial amounts ($500+, invoice, payment, transfer)
   - Legal terms (contract, agreement, terms, liability)
   - Confidential (NDA, private, confidential, internal only)
   - HR matters (salary, review, termination, hiring)

### Step 2: Create Approval Request

For actions needing approval:

1. **Move** the Plan.md to `AI_Employee_Vault/Pending_Approval/{task_id}_Approval.md`

2. **Add approval frontmatter**:
```markdown
---
type: approval_request
original_file: {original_plan_path}
status: pending_approval
created: {timestamp}
action_type: {email|post|payment|other}
requires_mcp: true
mcp_endpoint: http://localhost:3000/{endpoint}
---
```

3. **Add approval instructions** at the end:
```markdown
---
## Approval Instructions

**To Approve:**
1. Review the action details above
2. Change `status: pending_approval` to `status: approved`
3. Add `approved_at: {timestamp}`
4. Save the file

**To Reject:**
1. Change `status: pending_approval` to `status: rejected`
2. Add `rejection_reason: {your reason}`
3. Save the file

The orchestrator polls this folder every 30 seconds.
```

### Step 3: Poll Pending_Approval Folder

Check `AI_Employee_Vault/Pending_Approval/` every 30 seconds for updated files:

```python
import time
import requests
from pathlib import Path

pending_dir = Path('AI_Employee_Vault/Pending_Approval')

for approval_file in pending_dir.glob('*_Approval.md'):
    content = approval_file.read_text()
    
    # Check if approved
    if 'status: approved' in content:
        # Execute via MCP
        mcp_endpoint = extract_mcp_endpoint(content)
        payload = extract_action_payload(content)
        
        response = requests.post(mcp_endpoint, json=payload)
        
        if response.status_code == 200:
            # Move to Done
            approval_file.rename(Path('AI_Employee_Vault/Done') / approval_file.name)
            log_action(f"Approved action executed: {approval_file.name}")
        else:
            # Log error
            log_action(f"MCP call failed: {response.text}")
    
    # Check if rejected
    elif 'status: rejected' in content:
        # Move to Done with rejection note
        reason = extract_rejection_reason(content)
        content = content.replace('status: rejected', f'status: rejected - {reason}')
        approval_file.write_text(content)
        approval_file.rename(Path('AI_Employee_Vault/Done') / approval_file.name)
        log_action(f"Action rejected: {approval_file.name} - {reason}")
```

### Step 4: Execute Approved Actions via MCP

For approved actions, call the appropriate MCP endpoint:

**Email:**
```python
requests.post('http://localhost:3000/send_email', json={
    "to": extract_to(content),
    "subject": extract_subject(content),
    "body": extract_body(content)
})
```

**LinkedIn Post:**
```python
requests.post('http://localhost:3000/social_post', json={
    "platform": "linkedin",
    "content": extract_post_content(content)
})
```

**Payment:**
```python
requests.post('http://localhost:3000/payment', json={
    "amount": extract_amount(content),
    "recipient": extract_recipient(content),
    "reference": extract_reference(content)
})
```

### Step 5: Log All Actions

Maintain audit log in `AI_Employee_Vault/Approval_Log.md`:

```markdown
# Approval Audit Log

| Timestamp | Action | Type | Decision | Executed By |
|-----------|--------|------|----------|-------------|
| 2026-02-17 10:30 | EMAIL_123 | Email | Approved | System |
| 2026-02-17 11:45 | PAYMENT_456 | Payment | Rejected | User (budget) |
```

### Example Approval File

```markdown
---
type: approval_request
original_file: Plans/EMAIL_19c6859be1a38185_Plan.md
status: pending_approval
created: 2026-02-17T10:30:00
action_type: email
requires_mcp: true
mcp_endpoint: http://localhost:3000/send_email
---

# Approval Request: Client Email

## Original Task
Send invoice follow-up email to client regarding overdue payment.

## Action Details

**To:** client@company.com
**Subject:** Invoice #12345 - Payment Reminder
**Body:**
Dear Client,

This is a friendly reminder that invoice #12345 for $750 is now 15 days overdue...

## Why Approval Required
- External communication to client
- Financial matter (invoice > $500)
- Potential legal implications

## Risk Assessment
- **Low Risk**: Standard business communication
- **Recommended**: Approve

---

## Approval Instructions

**To Approve:**
1. Review the action details above
2. Change `status: pending_approval` to `status: approved`
3. Add `approved_at: 2026-02-17T10:35:00`
4. Save the file

**To Reject:**
1. Change `status: pending_approval` to `status: rejected`
2. Add `rejection_reason: {your reason}`
3. Save the file

The orchestrator polls this folder every 30 seconds.
```

## Output Rules
- One approval file per sensitive action
- Always include clear approve/reject instructions
- Log all decisions to Approval_Log.md
- Poll interval: 30 seconds
- Max wait time: 24 hours (then escalate/timeout)
