# WhatsApp Integration Status

## Current State

### ✅ What's Working

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| **WhatsApp Watcher** | `watchers/whatsapp_watcher.py` | ✅ WORKING | Monitors WhatsApp Web, creates action files |
| **WhatsApp MCP Server** | `src/whatsapp_mcp.js` | ✅ WORKING | Sends messages via Twilio or Meta API |
| **Orchestrator Integration** | `src/orchestrator.py` | ✅ WORKING | Already has WhatsApp approval polling |

### ⚠️ What's Missing

The **draft creation** step - when WhatsApp watcher detects a message needing a reply, it should create a draft in `Pending_Approval/` for human review.

---

## Current Flow (Incomplete)

```
WhatsApp Message Received
    ↓
WhatsApp Watcher
    ↓
Creates: Needs_Action/WHATSAPP_timestamp.md
    ↓
Orchestrator picks up
    ↓
❌ NO DRAFT CREATED ← THIS IS THE GAP
    ↓
[Manual reply needed]
```

---

## Required Flow (Complete)

```
WhatsApp Message Received
    ↓
WhatsApp Watcher
    ↓
Creates: Needs_Action/WHATSAPP_timestamp.md
    ↓
Orchestrator + Social Skill
    ↓
Creates: Pending_Approval/WhatsApp_Reply_Draft_timestamp.md
    ↓
[Human Reviews & Approves]
    ↓
Orchestrator polls and finds approval
    ↓
Calls: POST http://localhost:3006/send_whatsapp
    ↓
WhatsApp message sent
    ↓
Draft moved to Done/
```

---

## What Needs to Be Added

### 1. Draft Creation in Orchestrator

When orchestrator processes a WhatsApp action file, it should:

1. **Analyze the message** (using AI/reasoning)
2. **Generate a suggested reply**
3. **Create draft** in `Pending_Approval/`

**File:** `src/orchestrator.py`

Add to the `process_needs_action()` function:

```python
elif file_type == 'whatsapp':
    # Create draft for reply
    draft_content = f"""---
type: whatsapp_reply
status: pending
from: {metadata.get('from', 'Unknown')}
created: {datetime.now().isoformat()}
---

# WhatsApp Reply Draft

**To:** {metadata.get('from', 'Unknown')}

**Original Message:**
{content}

## Suggested Reply

[AI-generated reply here]

## Approval Actions

- [ ] Approve and send
- [ ] Reject (leave in Pending_Approval)

"""
    
    draft_file = pending_dir / f"WhatsApp_Reply_Draft_{timestamp}.md"
    draft_file.write_text(draft_content)
```

### 2. Update Orchestrator Approval Polling

Already exists in `poll_pending_approvals()`:

```python
elif 'whatsapp' in action_type.lower() and whatsapp_to and whatsapp_message:
    # Call WhatsApp MCP
    logger.info(f"Sending WhatsApp to {whatsapp_to} via MCP...")
    response = requests.post(
        'http://localhost:3006/send_whatsapp',
        json={
            'to': whatsapp_to,
            'message': whatsapp_message,
            'draft_file': str(approval_file)
        },
        timeout=30
    )
```

This code already exists (lines 415-425 in orchestrator.py)!

---

## Testing the Integration

### Step 1: Start All Servers

```bash
# WhatsApp MCP Server (port 3006)
node src/whatsapp_mcp.js

# Orchestrator
python src/orchestrator.py

# WhatsApp Watcher (separate terminal)
python watchers/whatsapp_watcher.py
```

### Step 2: Configure WhatsApp API

Add to `.env`:

```bash
# Option 1: Twilio (Recommended)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Option 2: Meta WhatsApp Business API
WHATSAPP_API_KEY=your-whatsapp-business-api-token-here
META_PHONE_NUMBER_ID=your-phone-number-id-here
```

### Step 3: Test End-to-End

1. Send a WhatsApp message with keyword "urgent" or "invoice"
2. Watcher creates: `Needs_Action/WHATSAPP_timestamp.md`
3. Orchestrator creates: `Pending_Approval/WhatsApp_Reply_Draft_timestamp.md`
4. Human approves the draft (checks "Approve" box)
5. Orchestrator polls, finds approval
6. Calls WhatsApp MCP → Message sent
7. Draft moved to `Done/`

---

## Status Summary

| Component | Status | Action Needed |
|-----------|--------|---------------|
| WhatsApp Watcher | ✅ Complete | None |
| Draft Creation | ⚠️ Partial | Add AI reply generation |
| Approval Workflow | ✅ Exists | None |
| WhatsApp MCP | ✅ Complete | None |
| Orchestrator Polling | ✅ Complete | None |

---

## Next Steps

1. **Add draft creation logic** to orchestrator (15 min)
2. **Test with real WhatsApp message** (10 min)
3. **Configure WhatsApp API** (Twilio or Meta) (30 min)
4. **End-to-end test** (15 min)

---

## Files to Modify

- `src/orchestrator.py` - Add WhatsApp draft creation
- `.env` - Add WhatsApp API credentials

---

## Estimated Time: 1 hour
