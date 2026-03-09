# Dashboard Approval Workflow Guide

**Date:** 2026-02-28  
**Status:** Complete

---

## 🎯 How Approval Works on Dashboard

### Complete Flow

```
1. You create task (type or drop file)
        ↓
2. AI analyzes and creates task file
        ↓
3. Task appears in "Pending Approval" section
        ↓
4. You click "Approve" button
        ↓
5. Dashboard executes the action
        ↓
6. Task moves to "Done" folder
        ↓
7. You see confirmation in "Recent Activity"
```

---

## 📋 What You See on Dashboard

### Pending Approval Section

Each task shows:

```
┌─────────────────────────────────────────────┐
│  odoo_invoice          Confidence: 95%      │
├─────────────────────────────────────────────┤
│  Customer John needs invoice #12345 for...  │
│                                             │
│  [Approve] [Reject]                         │
└─────────────────────────────────────────────┘
```

**Shows:**
- **Task Type:** odoo_invoice, email_send, whatsapp_reply, etc.
- **Confidence:** AI confidence score (0-100%)
- **Preview:** First 100 characters of task
- **Buttons:** Approve or Reject

---

## ✅ What Happens When You Click "Approve"

### By Task Type:

| Task Type | What Happens |
|-----------|--------------|
| **odoo_invoice** | Invoice creation triggered (needs Odoo MCP) |
| **email_send** | Email sending triggered (needs Gmail API) |
| **whatsapp_reply** | WhatsApp reply triggered (needs WhatsApp API) |
| **bank_payment** | Payment recorded in Odoo |
| **facebook_post** | Social media post scheduled |
| **linkedin_post** | LinkedIn post scheduled |
| **general_task** | Task marked as done |

**Currently:** Shows message about what WOULD happen (APIs not connected yet)

**In Production:** Would actually execute the action via API

---

## 🧪 Test the Approval Flow

### Step 1: Create Task

**In dashboard text box, type:**
```
Customer John needs invoice #12345 for $500
```

**Click:** "Analyze & Create Task"

---

### Step 2: See Task in Pending Approval

**Task appears with:**
- Type: `odoo_invoice`
- Confidence: 95%
- Preview: "Customer John needs invoice..."

---

### Step 3: Click "Approve"

**Confirmation dialog:**
```
Approve this task?
[OK] [Cancel]
```

**Click:** OK

---

### Step 4: See Result

**Alert shows:**
```
Task approved and executed: Invoice creation triggered (Odoo MCP required)
```

**Task disappears** from Pending Approval

**"Processed Today" counter increases**

**Recent Activity shows:**
```
10:30 AM - task_approved: odoo_invoice: invoice_... - Invoice creation triggered
```

---

## 📊 Where Tasks Go After Approval

### Approved Tasks:
```
Pending_Approval/  →  AI_Employee_Vault/Done/
```

### Rejected Tasks:
```
Pending_Approval/  →  AI_Employee_Vault/Rejected/
```

---

## 🔍 How to See What Happened

### Check Done Folder:

```bash
dir AI_Employee_Vault\Done\
```

**Shows:** All approved tasks with timestamps

---

### Check Activity Log:

**In dashboard:** Recent Activity section

**Or check files:**
```bash
type Logs\2026-02-28.json
```

---

## 🎯 Example Scenarios

### Scenario 1: Invoice Request

**Input:**
```
Customer ABC Corp needs invoice for consulting work, $2500
```

**AI Creates:**
- Type: `odoo_invoice`
- Entities: customer=ABC Corp, amount=2500

**You Approve:**
- Invoice creation triggered
- Task moves to Done
- Logged in activity

---

### Scenario 2: Email to Send

**Input:**
```
Send email to team about meeting tomorrow at 3pm
```

**AI Creates:**
- Type: `email_send`
- Entities: subject=Meeting, time=3pm

**You Approve:**
- Email sending triggered
- Task moves to Done
- Logged in activity

---

### Scenario 3: WhatsApp Reply

**Input:**
```
WhatsApp from +1234567890: When will my order ship?
```

**AI Creates:**
- Type: `whatsapp_reply`
- Entities: phone=+1234567890, intent=order_status

**You Approve:**
- WhatsApp reply triggered
- Task moves to Done
- Logged in activity

---

## 🚨 What If Approval Fails?

### Error Scenarios:

**Task not found:**
```
Error: Task not found
```
**Solution:** Refresh dashboard, task may have been processed already

**API not available:**
```
Invoice creation triggered (Odoo MCP required)
```
**Solution:** This is expected - APIs not connected yet. Task still marked as done.

---

## 📋 Current Limitations

### What Works NOW:

✅ AI analyzes intent correctly  
✅ Creates structured task files  
✅ Shows tasks in dashboard  
✅ Approve/Reject buttons work  
✅ Tasks move to Done/Rejected  
✅ Activity logged  

### What Needs API Integration:

❌ Odoo invoice auto-creation  
❌ Gmail auto-send  
❌ WhatsApp auto-send  
❌ Social media auto-post  

**These show "triggered" messages but don't actually execute yet.**

---

## 🎯 Next Steps for Full Automation

To make actions actually execute:

### 1. Odoo Integration
```bash
# Start Odoo MCP server
node servers/odoo_mcp.js
```

### 2. Gmail Integration
```bash
# Configure Gmail API
# Add credentials to .env
```

### 3. WhatsApp Integration
```bash
# Start WhatsApp server
node servers/whatsapp_mcp.js
```

**Then:** Approve button will actually execute these actions!

---

## ✅ Summary

**Current Flow:**
```
You create task → AI analyzes → You approve → Task marked done → Logged
```

**What You See:**
- Tasks in "Pending Approval"
- Click "Approve" button
- See confirmation message
- Task moves to "Done"
- Activity logged

**What's Missing:**
- Actual API execution (Odoo, Gmail, WhatsApp)
- Shows "triggered" messages instead

**Still Useful For:**
- Testing AI intent detection
- Workflow validation
- Approval process testing
- Activity logging

---

*Last Updated: 2026-02-28*
