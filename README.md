# AI Employee Vault

Automated document and communication processing pipeline with AI-powered orchestration.

---

## Project Structure

```
D:\AI\Hackathon-0\
├── src/                      # Core source code
│   ├── base_watcher.py       # Abstract base class for watchers
│   ├── orchestrator.py       # Main processing orchestrator
│   ├── scheduler.py          # Task scheduler
│   ├── setup_auth.py         # Gmail OAuth setup
│   └── mcp_server.js         # MCP action server (email sending)
│
├── watchers/                 # Input watchers
│   ├── filesystem_watcher.py # Bronze: File drop watcher
│   ├── gmail_watcher.py      # Silver: Gmail watcher
│   └── whatsapp_watcher.py   # Silver: WhatsApp watcher
│
├── skills/                   # Agent skill definitions
│   ├── SKILL_read_needs_action.md
│   ├── SKILL_move_to_done.md
│   ├── SKILL_update_dashboard.md
│   ├── SKILL_post_linkedin.md
│   ├── SKILL_reasoning_loop.md
│   └── SKILL_approval_workflow.md
│
├── tests/                    # Test files
│   └── test_silver.py        # Silver tier integration test
│
├── docs/                     # Documentation
│   └── GMAIL_SETUP.md        # Gmail API setup guide
│
├── AI_Employee_Vault/        # Working vault (created at runtime)
│   ├── Drop/                 # Input folder for files
│   ├── Needs_Action/         # Queue for pending items
│   ├── Plans/                # Generated action plans
│   ├── Pending_Approval/     # Awaiting human approval
│   ├── Done/                 # Completed items
│   └── Dashboard.md          # Activity log
│
├── credentials.json          # Google OAuth credentials (user-provided)
├── token.json                # Google OAuth token (auto-generated)
└── README.md                 # This file
```

---

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install watchdog google-auth google-auth-oauthlib google-api-python-client schedule playwright

# Playwright browsers
playwright install chromium

# Node.js dependencies (for MCP server)
npm init -y
npm install express nodemailer cors body-parser
```

### 2. Setup Gmail (Optional)

```bash
# Follow docs/GMAIL_SETUP.md to get credentials.json
python src/setup_auth.py
```

### 3. Run the System

```bash
# Option A: Run scheduler (recommended)
python src/scheduler.py

# Option B: Run components separately
python watchers/filesystem_watcher.py  # Terminal 1
python src/orchestrator.py             # Terminal 2
```

### 4. Test It

```bash
# Drop a file
echo "Test content" > AI_Employee_Vault\Drop\test.txt

# Check Needs_Action folder
dir AI_Employee_Vault\Needs_Action

# Check Dashboard
type AI_Employee_Vault\Dashboard.md
```

---

## Tiers

### Bronze Tier
- ✅ File system watcher
- ✅ Basic orchestrator
- ✅ Dashboard updates

### Silver Tier
- ✅ Gmail watcher
- ✅ WhatsApp watcher
- ✅ Reasoning loop (Plan.md creation)
- ✅ Approval workflow
- ✅ MCP server (email sending)
- ✅ LinkedIn auto-posting
- ✅ Scheduler

---

## How It Works

```
1. USER DROPS FILE → Drop/
         ↓
2. WATCHER detects → copies to Needs_Action/
         ↓
3. ORCHESTRATOR reads → creates Plan.md
         ↓
4. APPROVAL CHECK:
   ├─ Sensitive? → Pending_Approval/ → User approves → Execute
   └─ Normal? → Execute directly
         ↓
5. ACTION:
   ├─ Email → MCP /send_email
   ├─ LinkedIn → Draft post
   └─ File → Archive
         ↓
6. MOVE TO Done/ + Update Dashboard.md
```

---

## Configuration

| Setting | File | Default |
|---------|------|---------|
| Vault path | All | `AI_Employee_Vault/` |
| Orchestrator interval | `orchestrator.py` | 60 seconds |
| Scheduler tasks | `scheduler.py` | 1-2 minutes |
| Gmail poll | `gmail_watcher.py` | 60 seconds |
| WhatsApp poll | `whatsapp_watcher.py` | 30 seconds |

---

## API Endpoints (MCP Server)

```bash
# Start server
node src/mcp_server.js

# Endpoints:
POST /send_email       # Create email approval request
POST /approve_email    # Approve/reject pending email
GET  /pending_emails   # List pending approvals
GET  /health           # Health check
```

---

## Testing

```bash
# Run silver tier test
python tests/test_silver.py
```

---

## Security Notes

- **credentials.json** and **token.json** contain sensitive data
- Never commit these files to Git
- Store in secure location
- Revoke access at: https://myaccount.google.com/permissions

---

## Troubleshooting

### Watcher not detecting files
- Ensure file has extension (.txt, .pdf, etc.)
- Check if watcher is running: look for log messages
- Verify Drop/ folder path

### Orchestrator not processing
- Check interval setting (default 60s)
- Look for errors in log output
- Verify Needs_Action/ has .md files

### Gmail authentication failed
- Run `python src/setup_auth.py` again
- Check credentials.json is valid
- Verify Gmail API is enabled in Google Cloud Console

---

## License

MIT
