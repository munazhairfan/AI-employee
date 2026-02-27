# Gold Tier Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOLD TIER SYSTEM                                   │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Gmail      │    │  WhatsApp    │    │   File       │                  │
│  │   Watcher    │    │   Watcher    │    │   Watcher    │                  │
│  │  (120s)      │    │  (120s)      │    │  (60s)       │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│                             ▼                                               │
│                  ┌─────────────────────┐                                    │
│                  │   Needs_Action/     │                                    │
│                  │   (Input Queue)     │                                    │
│                  └──────────┬──────────┘                                    │
│                             │                                               │
│              ┌──────────────┼──────────────┐                                │
│              │              │              │                                │
│              ▼              ▼              ▼                                │
│     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│     │   Orchestrator │  │   Cross-Domain │  │   Social       │             │
│     │   (Main Loop)  │  │   Integration  │  │   MCP          │             │
│     │   + Retries    │  │   Skill        │  │   (Clipboard)  │             │
│     │   + Logging    │  │                │  │                │             │
│     └───────┬────────┘  └───────┬────────┘  └───────┬────────┘             │
│             │                   │                   │                       │
│             └───────────────────┼───────────────────┘                       │
│                                 │                                           │
│             ┌───────────────────┼───────────────────┐                       │
│             │                   │                   │                       │
│             ▼                   ▼                   ▼                       │
│    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│    │    Plans/       │ │  Pending_       │ │    Done/        │             │
│    │  (Action Plans) │ │  Approval/      │ │  (Completed)    │             │
│    │                 │ │  (Human Review) │ │                 │             │
│    └─────────────────┘ └─────────────────┘ └─────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Vault Directory Structure

```
AI_Employee_Vault/
│
├── Drop/                   # Incoming files (CSV, documents)
│   └── *.csv              # Invoice drops, data imports
│
├── Needs_Action/          # Input queue for orchestrator
│   ├── *gmail*.md         # Gmail watcher output
│   ├── *whatsapp*.md      # WhatsApp watcher output
│   ├── *file*.md          # File watcher output
│   ├── *facebook*.md      # Facebook watcher output
│   ├── *instagram*.md     # Instagram watcher output
│   └── *x*.md             # X/Twitter watcher output
│
├── Plans/                 # Generated action plans
│   ├── *_Plan.md          # Standard plans
│   └── *_Integrated_Plan.md  # Cross-domain merged plans
│
├── Pending_Approval/      # Awaiting human review
│   ├── *_Approval.md      # Approval requests
│   └── LinkedIn_Draft_*.md  # Social media drafts
│
├── Done/                  # Completed items
│   └── *.md               # Archived processed files
│
├── Briefings/             # Executive reports
│   └── CEO_Briefing_*.md  # Weekly audit output
│
└── Dashboard.md           # Real-time status summary
```

## External Integrations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                    │
│                                                                              │
│  ┌─────────────────┐         ┌─────────────────┐         ┌───────────────┐ │
│  │   Odoo ERP      │         │   Social Media  │         │   Email/SMS   │ │
│  │   (localhost)   │         │   Platforms     │         │   Gateways    │ │
│  │                 │         │                 │         │               │ │
│  │  Port: 8069     │         │  - Facebook     │         │  - Gmail API  │ │
│  │  MCP: 3004      │         │  - Instagram    │         │  - WhatsApp   │ │
│  │                 │         │  - X/Twitter    │         │  - SMTP       │ │
│  │  - Invoices     │         │  - LinkedIn     │         │               │ │
│  │  - Partners     │         │                 │         │               │ │
│  │  - Accounting   │         │                 │         │               │ │
│  └────────┬────────┘         └────────┬────────┘         └───────┬───────┘ │
│           │                           │                         │         │
│           │ JSON-RPC                  │ MCP (port 3005)         │ API     │
│           │                           │ + Clipboard             │         │
│           ▼                           ▼                         ▼         │
│  ┌─────────────────┐         ┌─────────────────┐         ┌───────────────┐ │
│  │  odoo_mcp.js    │         │  social_mcp.js  │         │  Email/SMS    │ │
│  │  (port 3004)    │         │  (port 3005)    │         │  Modules      │ │
│  └─────────────────┘         └─────────────────┘         └───────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Process Monitoring (Watchdog)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WATCHDOG SYSTEM                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      watchdog.py (Background)                        │   │
│  │                         Check Interval: 30s                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│         ┌────────────────────┼────────────────────┐                        │
│         │                    │                    │                        │
│         ▼                    ▼                    ▼                        │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│  │  Check PID  │      │  Detect     │      │  Restart    │                │
│  │  Status     │─────▶│  Dead       │─────▶│  Process    │                │
│  │             │      │  Process    │      │  (max 3/hr) │                │
│  └─────────────┘      └─────────────┘      └─────────────┘                │
│                                                                              │
│  Monitored Processes:                                                        │
│  ├── gmail_watcher.py                                                       │
│  ├── whatsapp_watcher.py                                                    │
│  ├── file_watcher.py                                                        │
│  ├── orchestrator.py                                                        │
│  ├── facebook_watcher.py                                                    │
│  ├── instagram_watcher.py                                                   │
│  └── x_watcher.py                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Invoice to Briefing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     INVOICE → BRIEFING FLOW                                  │
│                                                                              │
│  1. DROP INVOICE                                                            │
│     Drop/*.csv ──▶ file_watcher.py ──▶ Needs_Action/*.md                    │
│                                                                              │
│  2. PROCESS INVOICE                                                         │
│     Needs_Action ──▶ orchestrator.py ──▶ Odoo MCP (create_invoice)          │
│                                                                              │
│  3. GENERATE SOCIAL                                                         │
│     Business keywords ──▶ social_mcp.js ──▶ LinkedIn Draft (clipboard)      │
│                                                                              │
│  4. WEEKLY AUDIT (Sunday 8AM)                                               │
│     scheduler_audit.py ──▶ SKILL_weekly_audit.md ──▶ Ralph Loop             │
│                                                                              │
│  5. CEO BRIEFING                                                            │
│     Briefings/CEO_Briefing_{date}.md                                        │
│     ├── Revenue Summary (PKR)                                               │
│     ├── Overdue Invoices                                                    │
│     └── Action Suggestions                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Logging Architecture

```
Logs/
├── {date}.json              # Daily action log (orchestrator)
│   [
│     {"timestamp": "...", "action": "...", "result": "...", "error": null},
│     ...
│   ]
│
├── ralph_{task}.log         # Ralph Loop execution logs
├── watchdog.log             # Process monitoring logs
└── test_results_{date}.json # Integration test results
```

## API Endpoints

### Odoo MCP (port 3004)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Connection status |
| `/create_invoice` | POST | Create customer invoice |
| `/read_invoices` | POST | List invoices (filter by state) |
| `/search_partner` | POST | Search customers/vendors |
| `/create_partner` | POST | Create new partner |

### Social MCP (port 3005)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server status |
| `/post_draft_fb` | POST | Facebook draft (clipboard + browser) |
| `/post_draft_ig` | POST | Instagram draft (clipboard + browser) |
| `/post_draft_x` | POST | X/Twitter draft (clipboard + browser) |

---

## Lessons Learned Template

### Format

```markdown
## Lesson: {Title}

**Date:** YYYY-MM-DD
**Category:** {Bug | Optimization | Design | Integration}
**Severity:** {Critical | High | Medium | Low}

### Problem
{Description of the issue}

### Root Cause
{What caused it}

### Solution
{How it was fixed}

### Prevention
{How to avoid in future}
```

### Documented Lessons

---

## Lesson: Odoo 19 Authentication Response Format

**Date:** 2026-02-20
**Category:** Integration
**Severity:** High

### Problem
Odoo MCP authentication was failing with "Invalid credentials" error despite correct username/password.

### Root Cause
Odoo 19 changed the JSON-RPC authentication response format:
- **Old format (Odoo <19):** `{"uid": 2}`
- **New format (Odoo 19):** `2` (direct number)

The code was checking `result.uid` which doesn't exist in Odoo 19.

### Solution
Updated `authenticate()` function in `odoo_mcp.js`:
```javascript
// Odoo 19 returns uid directly as a number, not as {uid: ...}
const uid = typeof result === 'number' ? result : (result && result.uid);
```

### Prevention
- Always check API documentation for version-specific changes
- Add version detection in integration code
- Test with actual Odoo version before deployment

---

## Lesson: search_read Domain Parameter

**Date:** 2026-02-20
**Category:** Bug
**Severity:** Medium

### Problem
Invoice reading returned 0 results even though invoices existed in database.

### Root Cause
The `search_read` method expects domain as a **positional argument**, not in kwargs:
```python
# WRONG - domain in kwargs
executeMethod('account.move', 'search_read', [], {'domain': [...]})

# CORRECT - domain as first arg
executeMethod('account.move', 'search_read', [domain], kwargs)
```

### Solution
Fixed `read_invoices` endpoint in `odoo_mcp.js`:
```javascript
const invoices = await executeMethod('account.move', 'search_read', [domain], kwargs);
```

### Prevention
- Test Odoo methods with direct database verification
- Document Odoo API parameter order in comments
- Add integration tests that verify data round-trip

---

## Lesson: Docker Compose Credentials Mismatch

**Date:** 2026-02-20
**Category:** Configuration
**Severity:** High

### Problem
Docker-compose.yml had different credentials than MCP server defaults:
- docker-compose: `USER=odoo`, `PASSWORD=odoo`
- odoo_mcp.js defaults: `admin`/`admin`

### Solution
1. Added Odoo credentials to `.env` file:
```
ODOO_DB=ai_employee_db
ODOO_USER=admin
ODOO_PASS=admin
```

2. Updated documentation with correct credentials

### Prevention
- Use environment variables consistently across all configs
- Document credentials in single source of truth
- Add credential validation on startup

---

## Lesson: Ralph Loop Infinite Retry Prevention

**Date:** 2026-02-20
**Category:** Design
**Severity:** Medium

### Problem
Ralph Loop could potentially retry forever if task never completes.

### Solution
Implemented multiple safeguards:
1. **Max iterations:** 10 retries maximum
2. **Multiple completion checks:** 
   - `TASK_COMPLETE` marker in output
   - New file in `/Done` folder
   - Completion keywords in output
3. **Timeout per iteration:** 10 minutes
4. **Restart counting:** Track restarts per hour (watchdog)

### Prevention
- Always implement circuit breakers in retry logic
- Log all retry attempts for debugging
- Alert on max retry threshold reached

---

## Lesson: Cross-Domain Integration Complexity

**Date:** 2026-02-20
**Category:** Design
**Severity:** Low

### Problem
Linking personal (WhatsApp/Gmail) and business (LinkedIn/FB) communications requires fuzzy matching.

### Challenges
- Email format variations
- Phone number formats (+1 vs 001)
- Name variations (John vs John Doe)
- Time zone differences

### Solution
Created `SKILL_cross_domain_integration.md` with:
1. Multiple link types (email, phone, name, topic, time)
2. Confidence scoring for partial matches
3. Human review flag for uncertain links
4. Separate plans per client when ambiguous

### Prevention
- Start with exact matching, add fuzzy later
- Always allow human override
- Log matching decisions for improvement

---

## Quick Reference

### Start All Services

```bash
# Odoo (Docker)
docker compose up -d

# Odoo MCP
node odoo_mcp.js

# Social MCP
node social_mcp.js

# Watchdog (background)
start /B python watchdog.py

# Orchestrator
python src/orchestrator.py
```

### Test Integration

```bash
python test_gold.py
```

### Check Status

```bash
# Watchdog status
python watchdog.py --status

# Odoo health
curl http://localhost:3004/health

# Social MCP health
curl http://localhost:3005/health
```

---

*Last Updated: 2026-02-20*
*Version: Gold Tier 1.0*
