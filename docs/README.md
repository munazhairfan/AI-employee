# AI Employee Vault - Gold Tier

Automated document and communication processing pipeline with AI-powered orchestration and multi-platform social media integration.

---

## 🏗️ Project Structure

```
D:\AI\Hackathon-0\
├── src/                      # Core source code
│   ├── base_watcher.py       # Abstract base class for watchers
│   ├── orchestrator.py       # Main processing orchestrator
│   ├── scheduler.py          # Task scheduler
│   ├── scheduler_audit.py    # Weekly audit scheduler
│   ├── ralph_loop.py         # AI reasoning loop
│   ├── watchdog.py           # Process monitoring
│   ├── setup_auth.py         # Gmail OAuth setup
│   ├── odoo_setup.py         # Odoo database setup
│   ├── postgres_setup.py     # PostgreSQL setup
│   └── process_bank_csv.py   # Bank CSV processor
│
├── watchers/                 # Input watchers (polling services)
│   ├── filesystem_watcher.py # Bronze: File drop watcher
│   ├── gmail_watcher.py      # Silver: Gmail watcher
│   ├── whatsapp_watcher.py   # Silver: WhatsApp watcher
│   ├── facebook_watcher.py   # Facebook watcher
│   ├── instagram_watcher.py  # Instagram watcher
│   └── x_watcher.py          # X/Twitter watcher
│
├── servers/                  # MCP & OAuth servers
│   ├── mcp_server.js         # Email MCP (port 3000)
│   ├── odoo_mcp.js           # Odoo ERP MCP (port 3004)
│   ├── social_mcp.js         # Social media MCP (port 3005)
│   ├── whatsapp_mcp.js       # WhatsApp MCP (port 3006)
│   ├── linkedin_oauth_server.js  # LinkedIn OAuth (port 3006)
│   ├── facebook_oauth_server.js  # Facebook OAuth (port 3007)
│   ├── whatsapp/             # WhatsApp senders
│   └── instagram/            # Instagram posters
│
├── scripts/                  # Utility & test scripts
│   ├── test_*.js             # JavaScript test files
│   ├── test_*.py             # Python test files
│   ├── setup_*.py            # Setup scripts
│   ├── check_token*.js       # Token utilities
│   ├── find_urn*.js          # URN lookup utilities
│   ├── get_*.js              # OAuth helper scripts
│   └── refresh_token.js      # Token refresh utility
│
├── skills/                   # Agent skill definitions
│   ├── SKILL_read_needs_action.md
│   ├── SKILL_reasoning_loop.md
│   ├── SKILL_approval_workflow.md
│   ├── SKILL_generate_email_draft.md
│   ├── SKILL_generate_linkedin_draft.md
│   ├── SKILL_generate_whatsapp_draft.md
│   ├── SKILL_cross_domain_integration.md
│   └── SKILL_weekly_audit.md
│
├── tests/                    # Integration tests
│   └── test_silver.py        # Silver tier test
│
├── docs/                     # Documentation
│   ├── architecture/         # System architecture docs
│   ├── platforms/            # Platform-specific guides
│   ├── guides/               # How-to guides
│   └── GMAIL_SETUP.md        # Gmail API setup
│
├── config/                   # Configuration files
│
├── data/                     # Runtime data & sessions
│   ├── instagram_session_default/
│   ├── whatsapp_session/
│   ├── odoo_config/
│   ├── facebook_users.json
│   └── linkedin_users.json
│
├── AI_Employee_Vault/        # Working vault (created at runtime)
│   ├── Drop/                 # Input folder for files
│   ├── Needs_Action/         # Queue for pending items
│   ├── Plans/                # Generated action plans
│   ├── Pending_Approval/     # Awaiting human approval
│   ├── Done/                 # Completed items
│   ├── Briefings/            # Executive reports
│   └── Dashboard.md          # Real-time status
│
├── Logs/                     # Execution logs
│   ├── {date}.json           # Daily action logs
│   ├── ralph_*.log           # Reasoning loop logs
│   └── watchdog.log          # Process monitoring logs
│
├── .env.example              # Environment variables template
├── docker-compose.yml        # Odoo + PostgreSQL containers
├── package.json              # Node.js dependencies
└── requirements.txt          # Python dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Playwright browsers (for WhatsApp automation)
playwright install chromium

# Node.js dependencies
npm install
```

### 2. Configure Environment

```bash
# Copy and edit environment file
copy .env.example .env

# Fill in your credentials in .env:
# - Gmail credentials (optional)
# - Odoo credentials
# - Social media API tokens (or use OAuth)
```

### 3. Start Odoo (Optional - for ERP integration)

```bash
docker compose up -d
```

### 4. Start Servers

```bash
# Odoo MCP (ERP integration)
node servers/odoo_mcp.js

# Social MCP (LinkedIn, Facebook, Instagram, X)
node servers/social_mcp.js

# Email MCP (Gmail sending)
node servers/mcp_server.js

# WhatsApp MCP (WhatsApp Web automation)
node servers/whatsapp_mcp.js

# LinkedIn OAuth (multi-user support)
node servers/linkedin_oauth_server.js

# Facebook OAuth (multi-user support)
node servers/facebook_oauth_server.js
```

### 5. Start Watchers (Separate Terminals)

```bash
# Gmail watcher
python watchers/gmail_watcher.py

# WhatsApp watcher
python watchers/whatsapp_watcher.py

# File watcher
python watchers/filesystem_watcher.py

# Facebook/Instagram/X watchers
python watchers/facebook_watcher.py
python watchers/instagram_watcher.py
python watchers/x_watcher.py
```

### 6. Start Orchestrator

```bash
# Main orchestrator (processes Needs_Action/)
python src/orchestrator.py

# Weekly audit scheduler (runs Sundays 8AM)
python src/scheduler_audit.py

# Process watchdog (auto-restarts dead processes)
python src/watchdog.py
```

---

## 📊 Platform Status

| Platform | Status | Cost | Multi-User |
|----------|--------|------|------------|
| **Email (Gmail)** | ✅ Complete | Free | ❌ Single |
| **LinkedIn** | ✅ Complete | Free | ✅ Yes |
| **WhatsApp** | ✅ Complete | **Free** | ❌ Single |
| **Facebook** | ✅ Complete | Free | ✅ Yes |
| **Instagram** | ⚠️ Partial | Free | ❌ No |
| **X/Twitter** | ⚠️ Partial | Free | ❌ No |
| **Odoo ERP** | ✅ Complete | Free | ✅ Yes |

---

## 🔄 Data Flow

```
1. INPUT → Watchers detect changes
   ├── Gmail (new emails)
   ├── WhatsApp (new messages)
   ├── File System (Drop/*.csv)
   └── Social Media (mentions, comments)

2. QUEUE → Needs_Action/
   └── Creates *.md files with context

3. PROCESS → Orchestrator reads & plans
   ├── Creates Plans/*_Plan.md
   ├── Generates drafts for approval
   └── Logs to Logs/{date}.json

4. APPROVE → Human reviews Pending_Approval/
   ├── Auto-execute (non-sensitive)
   └── Manual approval (external actions)

5. EXECUTE → MCP servers perform actions
   ├── Email MCP → Send email
   ├── Social MCP → Post to LinkedIn/FB
   ├── WhatsApp MCP → Send WhatsApp
   └── Odoo MCP → Create invoice/partner

6. ARCHIVE → Move to Done/ + Update Dashboard.md
```

---

## 🛠️ Available Scripts

### Test Scripts
```bash
# Run integration tests
python tests/test_silver.py

# Test specific platforms
node scripts/test_linkedin.js
node scripts/test_facebook_mcp.js
node scripts/test_oauth_post.js
```

### Setup Scripts
```bash
# Gmail OAuth setup
python scripts/setup_auth.py

# Instagram setup
python scripts/setup_instagram.py

# LinkedIn setup
node scripts/setup_linkedin.js
```

### OAuth Utilities
```bash
# Get OAuth authorization URL
node scripts/get_auth_url.js

# Exchange code for access token
node scripts/get_access_token.js

# Refresh expired token
node scripts/refresh_token.js

# Check token permissions
node scripts/check_token.js
python scripts/check_token_perms.py
```

---

## 🔧 Configuration

### Environment Variables (.env)

| Variable | Purpose | Default |
|----------|---------|---------|
| `EMAIL_USER` | Gmail address | - |
| `EMAIL_PASS` | Gmail app password | - |
| `ODOO_URL` | Odoo instance URL | `http://localhost` |
| `ODOO_PORT` | Odoo port | `8069` |
| `ODOO_DB` | Odoo database | `ai_employee_db` |
| `ODOO_USER` | Odoo username | `admin` |
| `ODOO_PASS` | Odoo password | `admin` |
| `LINKEDIN_TOKEN` | LinkedIn access token | - |
| `CLIENT_ID` | LinkedIn OAuth client ID | - |
| `CLIENT_SECRET` | LinkedIn OAuth secret | - |
| `FACEBOOK_TOKEN` | Facebook page token | - |
| `USE_WHATSAPP_WEB` | Use WhatsApp Web automation | `true` |

### Server Ports

| Server | Port | Purpose |
|--------|------|---------|
| Email MCP | 3000 | Gmail sending |
| Odoo MCP | 3004 | ERP integration |
| Social MCP | 3005 | Social media posts |
| WhatsApp MCP | 3006 | WhatsApp Web |
| LinkedIn OAuth | 3006 | LinkedIn OAuth |
| Facebook OAuth | 3007 | Facebook OAuth |

---

## 📁 Vault Folders

| Folder | Purpose |
|--------|---------|
| `Drop/` | Incoming files (CSV, documents) |
| `Needs_Action/` | Input queue from watchers |
| `Plans/` | Generated action plans |
| `Pending_Approval/` | Awaiting human review |
| `Done/` | Completed items |
| `Briefings/` | Executive reports |
| `Inbox/` | Temporary processing |
| `Processed/` | Alternative archive |
| `Rejected/` | Rejected items |

---

## 🔒 Security

- **Never commit `.env`** - Contains sensitive credentials
- **Never commit `token.json`** - OAuth tokens
- **Never commit `credentials.json`** - Google OAuth credentials
- Store all secrets in secure location
- Revoke access: https://myaccount.google.com/permissions

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `docs/architecture/Architecture.md` | System architecture |
| `docs/COMPLETE_STATUS.md` | Platform completion status |
| `docs/platforms/WHATSAPP_WEB_FREE.md` | WhatsApp free automation |
| `docs/platforms/LINKEDIN_OAUTH.md` | LinkedIn OAuth setup |
| `docs/platforms/FACEBOOK_SETUP.md` | Facebook setup |
| `docs/GMAIL_SETUP.md` | Gmail API setup |
| `SECURITY.md` | Security guidelines |

---

## 🐛 Troubleshooting

### Watcher not detecting files
- Ensure file has extension (.txt, .pdf, .csv)
- Check watcher is running (look for log messages)
- Verify Drop/ folder path

### OAuth authentication failed
- Run the appropriate OAuth server
- Visit the authorization URL
- Ensure redirect URI matches in developer console
- Check token hasn't expired

### Odoo connection failed
- Ensure Docker containers are running: `docker compose ps`
- Check credentials in `.env` match Odoo admin
- Verify port 8069 is not in use

### MCP server not responding
- Check server is running: `curl http://localhost:3000/health`
- Verify port is not blocked by firewall
- Check logs for error messages

---

## 📝 License

MIT

---

## 🎯 Next Steps

### Immediate Priorities
1. **Multi-user WhatsApp support** - Add user session management
2. **Multi-user Email support** - Add Gmail OAuth for multiple users
3. **Complete Instagram integration** - Full orchestrator connection
4. **Complete X/Twitter integration** - Full orchestrator connection

### Deployment
1. Deploy to production server (Railway, Vercel, or self-hosted)
2. Configure production domain
3. Update OAuth redirect URIs
4. Set up SSL certificates
5. Configure production database
