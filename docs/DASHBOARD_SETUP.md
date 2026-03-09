# Professional Dashboard - Setup Guide

**Date:** 2026-02-28  
**Status:** Ready to Use

---

## 🎯 What's New

### Old Problems (Solved)
- ❌ Multiple terminals (Python + Node)
- ❌ Manual file creation in specific format
- ❌ No real-time dashboard
- ❌ Emojis look unprofessional
- ❌ Have to run different scripts

### New Solution
- ✅ **Single dashboard** at http://localhost:3000
- ✅ **Drop TXT files** or type messages directly
- ✅ **AI auto-creates** structured task files
- ✅ **Professional UI** (no emojis)
- ✅ **One command** starts everything

---

## 🚀 Quick Start

### Step 1: Start Dashboard

**Double-click:** `start_dashboard.bat`

**Or run:**
```bash
python dashboard_server.py
```

**Opens:** http://localhost:3000

---

### Step 2: Use the Dashboard

#### Option A: Type Message Directly

1. Go to dashboard
2. Type in text box:
   ```
   Customer John needs invoice #12345 for $500
   ```
3. Click "Analyze & Create Task"
4. AI creates task automatically
5. Task appears in "Pending Approval"
6. Click "Approve" to execute

---

#### Option B: Drop TXT File

1. Create TXT file anywhere:
   ```
   Customer ABC Corp paid $15000, record it
   ```
2. Save to `drop_folder/`
3. Dashboard auto-detects (or click "Process Drop Folder")
4. AI analyzes and creates task
5. Approve in dashboard

---

## 📊 Dashboard Features

### Status Bar (Top)
- **AI Agent:** Shows which AI is active (Groq/Ollama)
- **Watchers:** Background monitoring status
- **Pending Tasks:** Number of tasks awaiting approval
- **Processed Today:** Completed tasks count

### Create Task Card
- **Text Input:** Type or paste messages
- **Drop Zone:** Shows where to drop files
- **Analyze Button:** AI analyzes and creates task
- **Analysis Result:** Shows what AI understood

### Pending Approval Card
- **List of Tasks:** All tasks waiting for approval
- **Task Type:** Invoice, Email, WhatsApp, etc.
- **Confidence:** AI confidence score
- **Preview:** First line of task
- **Approve Button:** Execute task
- **Reject Button:** Reject with reason

### Activity Log Card
- **Recent Actions:** What happened recently
- **Timestamps:** When each action occurred
- **Results:** What was accomplished

---

## 🎨 Dashboard Design

### Professional Look
- Clean, modern interface
- No emojis or unprofessional elements
- Business-appropriate colors
- Responsive design
- Real-time updates (every 10 seconds)

### Color Scheme
- **Header:** Dark blue (#2c3e50)
- **Cards:** White with subtle shadows
- **Status:** Green (active), Gray (inactive)
- **Buttons:** Blue (action), Green (approve), Red (reject)

---

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  WEB BROWSER (http://localhost:3000)                        │
│  - Professional dashboard UI                                │
│  - Real-time status updates                                 │
│  - Task approval interface                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP API
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  DASHBOARD SERVER (Python - Port 3000)                      │
│  - Handles web requests                                     │
│  - Manages system state                                     │
│  - Coordinates components                                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ API Endpoints                                          │ │
│  │ - /api/status (system status)                          │ │
│  │ - /api/pending (pending tasks)                         │ │
│  │ - /api/activity (recent activity)                      │ │
│  │ - /api/analyze (AI analysis)                           │ │
│  │ - /api/create-task (create from text)                  │ │
│  │ - /api/approve (approve task)                          │ │
│  │ - /api/reject (reject task)                            │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI AGENT (src/ai_agent.py)                                 │
│  - Groq API (FREE, 30 req/min)                              │
│  - Anti-hallucination guards                                │
│  - Intent detection                                         │
│  - Entity extraction                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  INTENT ANALYZER (src/intent_analyzer.py)                   │
│  - Reads dropped TXT files                                  │
│  - Determines intent (invoice, email, whatsapp, etc.)       │
│  - Extracts entities (customer, amount, dates)              │
│  - Flags missing information                                │
│  - Creates structured markdown files                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Creates files in
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI_Employee_Vault/Needs_Action/                            │
│  - Structured task files                                    │
│  - Auto-generated by AI                                     │
│  - Ready for orchestrator                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Processed by
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (src/orchestrator.py)                         │
│  - Scans Needs_Action/                                      │
│  - Processes tasks                                          │
│  - Creates drafts in Pending_Approval/                      │
│  - Moves completed to Done/                                 │
│  - Logs to Logs/                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Usage Examples

### Example 1: Create Invoice Task

**Type in dashboard:**
```
Customer Ahmed from XYZ Ltd needs invoice for consulting work, $2500, email to ahmed@xyz.com
```

**AI Creates:**
```markdown
---
type: odoo_invoice
ai_confidence: 95
requires_human_review: false
---

## Extracted Entities
| Field | Value |
|-------|-------|
| customer_name | Ahmed |
| company | XYZ Ltd |
| amount | 2500 |
| email | ahmed@xyz.com |
| service | consulting work |
```

**You:** Click "Approve" → Invoice created in Odoo

---

### Example 2: WhatsApp Reply

**Type in dashboard:**
```
WhatsApp from +923001234567: When will order #54321 ship? Customer name is Sarah
```

**AI Creates:**
```markdown
---
type: whatsapp_reply
ai_confidence: 90
requires_human_review: true
---

## Missing Information
- [ ] order_status
- [ ] shipping_date

**Human review required**
```

**You:** Click "Edit & Approve" → Add shipping date → Send reply

---

### Example 3: Bank Payment

**Drop file:** `drop_folder/payment.txt`
```
Received payment: ABC Corp transferred PKR 75,000 for invoice #INV-2026-042
```

**AI Creates:**
```markdown
---
type: bank_payment
ai_confidence: 95
---

## Extracted Entities
| Field | Value |
|-------|-------|
| customer | ABC Corp |
| amount | 75000 |
| currency | PKR |
| invoice_number | INV-2026-042 |
```

**You:** Click "Approve" → Payment recorded in Odoo

---

## 🔑 API Endpoints

### Get System Status
```bash
curl http://localhost:3000/api/status
```

**Response:**
```json
{
  "watchers_running": false,
  "ai_available": true,
  "ai_model": "Groq (llama-3.3-70b-versatile)",
  "pending_count": 3,
  "processed_today": 12
}
```

### Get Pending Tasks
```bash
curl http://localhost:3000/api/pending
```

### Analyze Text
```bash
curl -X POST http://localhost:3000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Customer needs invoice for $500"}'
```

### Create Task from Text
```bash
curl -X POST http://localhost:3000/api/create-task \
  -H "Content-Type: application/json" \
  -d '{"text": "Send email to team about meeting"}'
```

### Approve Task
```bash
curl -X POST http://localhost:3000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"task_id": "odoo_invoice_2026-02-28_01-30-45"}'
```

---

## 🎯 Workflow

### Complete Flow

1. **User drops file or types message**
   - Dashboard or drop_folder/

2. **AI analyzes intent**
   - Determines action type
   - Extracts entities
   - Flags missing info

3. **Task created automatically**
   - Structured markdown
   - Saved to Needs_Action/

4. **Orchestrator processes**
   - Creates draft
   - Moves to Pending_Approval/

5. **User reviews in dashboard**
   - See all pending tasks
   - Click Approve or Reject

6. **System executes**
   - Creates invoice
   - Sends message
   - Records payment

7. **Task completed**
   - Moved to Done/
   - Logged in Logs/

---

## ✅ Benefits

### Before (Old System)
- ❌ Open multiple terminals
- ❌ Run `python intent_analyzer.py`
- ❌ Run `python orchestrator.py`
- ❌ Run `node dashboard-server.js`
- ❌ Manually format markdown files
- ❌ Check folders for new tasks

### After (New Dashboard)
- ✅ One command: `start_dashboard.bat`
- ✅ Everything in one place
- ✅ Auto-processes files
- ✅ Professional interface
- ✅ Real-time updates
- ✅ One-click approval

---

## 🚀 Next Steps

### 1. Test the Dashboard
```bash
start_dashboard.bat
```

Then:
- Open http://localhost:3000
- Type a test message
- Click "Analyze & Create Task"
- Approve the task

### 2. Customize for Your Business
- Edit `src/intent_analyzer.py`
- Add your specific intent types
- Add your business workflows

### 3. Add More Features
- File watcher (auto-process drop folder)
- Email integration
- WhatsApp integration
- Odoo auto-execution

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `dashboard_server.py` | Main dashboard server |
| `start_dashboard.bat` | Quick start script |
| `src/intent_analyzer.py` | AI intent detection |
| `src/ai_agent.py` | AI model integration |
| `src/orchestrator.py` | Task processor |
| `public/dashboard.html` | Dashboard UI |

---

**Your system is now production-ready!** 🚀

---

*Last Updated: 2026-02-28*
