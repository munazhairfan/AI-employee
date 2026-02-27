# Human-in-the-Loop Approval Workflow

## Overview

The system now implements **selective autonomy**:
- ✅ **Odoo Invoices**: Fully autonomous (NO approval required)
- ✅ **External Communications**: Approval required → Auto-executed via MCP after approval

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FILE DROPPED IN Drop/                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WATCHER → Needs_Action/                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR ANALYZES                                   │
│                                                                              │
│  Content Type                    Action                                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Invoice/Payment + Odoo        → Auto-create in Odoo (NO approval)          │
│  Email request                 → Draft + Approval → MCP sends               │
│  WhatsApp message              → Draft + Approval → MCP sends               │
│  LinkedIn post                 → Draft + Approval → MCP posts               │
│  Facebook post                 → Draft + Approval → MCP posts               │
│  X/Twitter post                → Draft + Approval → MCP posts               │
│  Instagram post                → Draft + Approval → MCP posts               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │   INVOICE (Auto)      │       │  EXTERNAL (Approval)  │
        │                       │       │                       │
        │ 1. Extract details    │       │ 1. Create draft in    │
        │ 2. Call Odoo MCP      │       │    Pending_Approval/  │
        │ 3. Create & post      │       │ 2. Wait for human     │
        │ 4. Move to Done       │       │ 3. Human marks [x]    │
        │                       │       │ 4. MCP executes       │
        │                       │       │ 5. Move to Done       │
        └───────────────────────┘       └───────────────────────┘
```

---

## Approval Process

### Step 1: Draft Creation

When you drop a file requesting external communication:

```
Drop/send_email_to_client.md
    ↓
Needs_Action/send_email_to_client.md
    ↓
Pending_Approval/Email_Draft_2026-02-22_14-30-00.md
```

Draft file format:
```markdown
---
type: email_draft
status: pending_review
generated_at: 2026-02-22T14:30:00
---

## Email Details

**To:** client@example.com
**Subject:** Invoice Follow-up

## Email Body

Dear Client,
This is a friendly reminder...

---

## Approval Actions

- [ ] Approve (execute manually)
- [ ] Reject (add your reason below)
- [ ] Edit (add your changes/notes below)
```

### Step 2: Human Review

Open the draft file in `Pending_Approval/` and review:
- ✅ Recipient correct?
- ✅ Content appropriate?
- ✅ Timing right?

### Step 3: Approve or Reject

**To Approve:**
```markdown
- [x] Approve (execute manually)
```

**To Reject:**
```markdown
- [x] Reject (add your reason below)

Client already contacted yesterday - no need to send again.
```

**To Edit:**
```markdown
- [ ] Edit (add your changes/notes below)

Please change the tone to be more friendly and add our phone number.
```

### Step 4: Auto-Execution

Orchestrator polls every 30 seconds:
- Detects `[x] Approve` mark
- Extracts content (email, message, post)
- Calls appropriate MCP endpoint
- MCP executes via API
- Moves draft to `Done/`

---

## Odoo Invoices (Autonomous)

### No Approval Required

When you drop an invoice-related file:

```
Drop/invoice_payment_received.md
    ↓
Needs_Action/invoice_payment_received.md
    ↓
Orchestrator detects: "invoice" + "payment" keywords
    ↓
Auto-extracts: partner_name, amount, description
    ↓
Calls: POST http://localhost:3004/post_invoice
    ↓
Odoo creates AND posts invoice
    ↓
Moves to Done/
```

### Example Invoice File

```markdown
---
type: invoice
partner_name: ABC Corporation
amount: 50000
description: Payment received for consulting services
---

Invoice payment received from ABC Corporation.
Amount: PKR 50,000
Date: 2026-02-22
Reference: INV-2026-001
```

**Result:** Invoice created and posted in Odoo automatically.

---

## MCP Endpoints Called After Approval

| Action | MCP Endpoint | Port | API Used |
|--------|--------------|------|----------|
| Email | `POST /send_approved_email` | 3000 | SMTP (Gmail) |
| WhatsApp | `POST /send_whatsapp` | 3006 | Twilio or Meta |
| LinkedIn | `POST /post_linkedin` | 3005 | LinkedIn API v2 |
| Facebook | `POST /post_facebook` | 3005 | Facebook Graph API |
| X/Twitter | `POST /post_x` | 3005 | Twitter API v2 |
| Instagram | `POST /post_instagram` | 3005 | Instagram Graph API |
| Odoo Invoice | `POST /post_invoice` | 3004 | Odoo JSON-RPC |

---

## Configuration Required

### .env Variables

```bash
# Email (for sending approved emails)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Odoo (autonomous invoice creation)
ODOO_URL=http://localhost
ODOO_PORT=8069
ODOO_DB=ai_employee_db
ODOO_USER=admin
ODOO_PASS=admin

# Social Media (for approved posts)
LINKEDIN_TOKEN=your-token
LINKEDIN_PERSON_URN=urn:li:member:YOUR_ID

X_TWITTER_TOKEN=your-bearer-token

FACEBOOK_TOKEN=your-page-token
FACEBOOK_PAGE_ID=your-page-id

INSTAGRAM_TOKEN=your-token
INSTAGRAM_USER_ID=your-user-id

# WhatsApp (choose one)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OR Meta
WHATSAPP_API_KEY=your-token
META_PHONE_NUMBER_ID=your-id
```

---

## Running the System

### Start All MCP Servers

```bash
# Terminal 1: Odoo MCP (port 3004)
node src/odoo_mcp.js

# Terminal 2: Social MCP (port 3005)
node src/social_mcp.js

# Terminal 3: Email MCP (port 3000)
node src/mcp_server.js

# Terminal 4: WhatsApp MCP (port 3006)
node src/whatsapp_mcp.js
```

### Start Orchestrator

```bash
# Terminal 5: Orchestrator
python src/orchestrator.py
```

### Test the Workflow

```bash
# Test approval workflow
python tests/test_approval_loop.py
```

---

## Safety Features

### 1. Approval Required for External Comms
- Emails NOT sent without approval
- Social posts NOT published without approval
- WhatsApp messages NOT sent without approval

### 2. Odoo Invoices Autonomous
- Safe because: Internal business records
- Can be reviewed in Odoo UI after creation
- No external communication involved

### 3. Rejection Workflow
- Rejected drafts moved to `Rejected/` folder
- Rejection reason logged to Dashboard.md
- Original file preserved for review

### 4. Execution Failure Handling
- If MCP call fails, draft stays in `Pending_Approval/`
- Error logged to Dashboard.md
- User can retry or edit

### 5. Logging
- All actions logged to `Logs/{date}.json`
- Dashboard.md updated with status
- Audit trail maintained

---

## Troubleshooting

### Draft Not Executing After Approval

**Check:**
1. MCP server running? (`curl http://localhost:3000/health`)
2. Credentials configured in .env?
3. Network connectivity to APIs?

**Logs:**
```bash
type Logs\{date}.json
```

### Odoo Invoice Not Creating

**Check:**
1. Odoo running? (`curl http://localhost:3004/health`)
2. Credentials correct?
3. Database exists?

### Social Posts Not Publishing

**Check:**
1. Token valid and not expired?
2. API permissions granted?
3. Rate limits exceeded?

---

## Best Practices

### 1. Review Drafts Promptly
- Check `Pending_Approval/` folder daily
- Approve/reject within 24 hours

### 2. Use Clear File Names
```
Good: send_email_to_abc_corp.md
Bad: email1.md
```

### 3. Include All Details
```markdown
---
type: email
to: client@example.com
subject: Invoice #12345
---

[Full email body]
```

### 4. Monitor Dashboard
```bash
type AI_Employee_Vault\Dashboard.md
```

### 5. Review Logs Regularly
```bash
type Logs\{date}.json
```

---

## Future Enhancements

### Potential Auto-Execution Candidates
- Internal notifications (Slack/Teams)
- Daily status reports
- Scheduled social media posts
- Recurring invoice reminders

### Enhanced Approval
- Multi-level approval (manager → director)
- Amount-based thresholds (< $1000 auto, > $1000 approval)
- Time-based auto-approval (if no response in 24h)

---

*Last Updated: 2026-02-22*
*Version: 2.0 - Selective Autonomy*
