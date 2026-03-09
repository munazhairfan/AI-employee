# Quick Start Guide

## Project Status: ✅ Reorganized

All files have been organized into a clean, scalable structure.

---

## New Structure Overview

```
├── src/           - Core Python code (orchestrator, scheduler, watchdog)
├── watchers/      - Input monitors (Gmail, WhatsApp, File watchers)
├── servers/       - MCP & OAuth servers (NEW!)
├── scripts/       - Test & utility scripts (NEW!)
├── skills/        - Agent skill definitions
├── docs/          - Documentation (reorganized!)
├── data/          - Sessions & user data (NEW!)
└── config/        - Configuration files (NEW!)
```

---

## Quick Commands

### Start All Servers

```bash
# Terminal 1 - Odoo MCP
node servers/odoo_mcp.js

# Terminal 2 - Social MCP
node servers/social_mcp.js

# Terminal 3 - WhatsApp MCP
node servers/whatsapp_mcp.js

# Terminal 4 - Email MCP
node servers/mcp_server.js
```

### Start Watchers

```bash
# Terminal 5 - Gmail Watcher
python watchers/gmail_watcher.py

# Terminal 6 - WhatsApp Watcher
python watchers/whatsapp_watcher.py

# Terminal 7 - File Watcher
python watchers/filesystem_watcher.py
```

### Start Core Services

```bash
# Terminal 8 - Orchestrator
python src/orchestrator.py

# Terminal 9 - Watchdog (process monitor)
python src/watchdog.py
```

---

## Testing

```bash
# Test LinkedIn
node scripts/test_linkedin.js

# Test Facebook
node scripts/test_facebook_mcp.js

# Test OAuth posting
node scripts/test_oauth_post.js

# Run integration tests
python tests/test_silver.py
```

---

## OAuth Setup (Multi-User)

### LinkedIn
```bash
node servers/linkedin_oauth_server.js
# Visit: http://localhost:3006/auth/linkedin/start
```

### Facebook
```bash
node servers/facebook_oauth_server.js
# Visit: http://localhost:3007/auth/facebook/start
```

---

## Documentation

| Document | Location |
|----------|----------|
| Full README | `README.md` |
| Architecture | `docs/architecture/Architecture.md` |
| Multi-User Plan | `docs/architecture/MULTIUSER_ARCHITECTURE.md` |
| Platform Guides | `docs/platforms/` |
| Reorganization Summary | `docs/REORGANIZATION_SUMMARY.md` |

---

## Next Steps

### 1. Review Multi-User Architecture
See `docs/architecture/MULTIUSER_ARCHITECTURE.md` for implementing multi-user support for WhatsApp and Email.

### 2. Install Multi-User Dependencies
```bash
npm install whatsapp-web.js qrcode better-sqlite3 googleapis open
pip install better-sqlite3
```

### 3. Implement WhatsApp Multi-User
- Create `servers/whatsapp_oauth_server.js`
- Update `servers/whatsapp_mcp.js` for multi-user
- Update orchestrator for user selection

### 4. Implement Email Multi-User
- Create `servers/email_oauth_server.js`
- Update `servers/mcp_server.js` for multi-user
- Update orchestrator for user selection

---

## File Locations

### Looking for...

| File Type | Location |
|-----------|----------|
| MCP Servers | `servers/*.js` |
| OAuth Servers | `servers/*oauth*.js` |
| Test Scripts | `scripts/test_*.js`, `scripts/test_*.py` |
| Setup Scripts | `scripts/setup_*.py`, `scripts/setup_*.js` |
| Platform Docs | `docs/platforms/` |
| Session Data | `data/` |
| User Mappings | `data/*.json` |

---

## Troubleshooting

### Can't find a file?
```bash
# Search in servers/
dir servers /S /B | findstr "filename"

# Search in scripts/
dir scripts /S /B | findstr "filename"
```

### Import errors after move?
All imports have been verified. If you encounter issues:
- Check the new file location
- Update relative paths if needed

---

*Last Updated: 2026-02-26*
