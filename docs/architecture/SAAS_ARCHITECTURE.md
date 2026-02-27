# AI Employee Vault - SaaS Architecture Plan

**Version:** 1.0  
**Date:** 2026-02-26  
**Status:** Ready for Implementation  
**Approach:** Option A - Start Simple (Hybrid SaaS)

---

## 📋 Executive Summary

### What We're Building

A **hybrid SaaS platform** where:
- **You host**: Central vault database + API servers (cloud)
- **Customers run**: Local agent on their computers
- **Customers can**: Bring their own Odoo OR use yours later

### Key Design Principles

1. ✅ **Keep existing code** - LinkedIn, WhatsApp, Facebook code stays 95% the same
2. ✅ **Multi-tenant** - Multiple companies use the same platform
3. ✅ **Data isolation** - Each customer's data is completely separate
4. ✅ **Low cost** - Use free tiers, no server needed initially
5. ✅ **Easy distribution** - Customers download and run locally

---

## 🏗️ Complete Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  YOUR CLOUD INFRASTRUCTURE (Free Tiers)                                  │
│  No physical server needed - all managed services                        │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  CENTRAL VAULT DATABASE                                           │  │
│  │  Service: Supabase Free Tier (PostgreSQL)                         │  │
│  │  Cost: FREE (up to 500MB, 50k users)                              │  │
│  │  URL: https://xxxxx.supabase.co                                   │  │
│  │                                                                   │  │
│  │  Schema: Multi-tenant with customer_id isolation                  │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ customers                                                   │  │  │
│  │  │ ├── id (UUID)                                               │  │  │
│  │  │ ├── company_name                                            │  │  │
│  │  │ ├── email                                                   │  │  │
│  │  │ ├── subscription (basic/pro/enterprise)                     │  │  │
│  │  │ ├── odoo_url (optional - if they bring own Odoo)            │  │  │
│  │  │ └── created_at                                              │  │  │
│  │  │                                                             │  │  │
│  │  │ users                                                       │  │  │
│  │  │ ├── id (UUID)                                               │  │  │
│  │  │ ├── customer_id (FK → customers.id)                         │  │  │
│  │  │ ├── email                                                   │  │  │
│  │  │ ├── name                                                    │  │  │
│  │  │ ├── api_key (unique, auto-generated)                        │  │  │
│  │  │ └── created_at                                              │  │  │
│  │  │                                                             │  │  │
│  │  │ whatsapp_sessions                                           │  │  │
│  │  │ ├── user_id (FK → users.id)                                 │  │  │
│  │  │ ├── session_data (encrypted JSONB)                          │  │  │
│  │  │ ├── phone_number                                            │  │  │
│  │  │ └── status                                                  │  │  │
│  │  │                                                             │  │  │
│  │  │ email_tokens                                                │  │  │
│  │  │ ├── user_id (FK → users.id)                                 │  │  │
│  │  │ ├── access_token (encrypted)                                │  │  │
│  │  │ ├── refresh_token (encrypted)                               │  │  │
│  │  │ └── expires_at                                              │  │  │
│  │  │                                                             │  │  │
│  │  │ linkedin_tokens                                             │  │  │
│  │  │ ├── user_id (FK → users.id)                                 │  │  │
│  │  │ ├── access_token (encrypted)                                │  │  │
│  │  │ ├── refresh_token (encrypted)                               │  │  │
│  │  │ └── urn                                                     │  │  │
│  │  │                                                             │  │  │
│  │  │ facebook_tokens                                             │  │  │
│  │  │ ├── user_id (FK → users.id)                                 │  │  │
│  │  │ ├── access_token (encrypted)                                │  │  │
│  │  │ └── page_id                                                 │  │  │
│  │  │                                                             │  │  │
│  │  │ action_logs                                                 │  │  │
│  │  │ ├── id                                                      │  │  │
│  │  │ ├── user_id (FK → users.id)                                 │  │  │
│  │  │ ├── action_type                                             │  │  │
│  │  │ ├── status                                                  │  │  │
│  │  │ └── timestamp                                               │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              │ HTTPS API Calls                          │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  API SERVERS (Serverless Functions)                               │  │
│  │  Service: Vercel Functions / Cloudflare Workers                   │  │
│  │  Cost: FREE (up to 100k requests/month)                           │  │
│  │                                                                   │  │
│  │  Endpoints:                                                       │  │
│  │  ├── POST /api/v1/auth/register          # New customer signup    │  │
│  │  ├── POST /api/v1/auth/login             # Customer login         │  │
│  │  ├── GET  /api/v1/users/:id/tokens       # Get user's tokens      │  │
│  │  ├── POST /api/v1/oauth/:platform/start  # Start OAuth flow       │  │
│  │  ├── GET  /api/v1/oauth/:platform/callback # OAuth callback       │  │
│  │  ├── POST /api/v1/actions/send-whatsapp  # Send WhatsApp message  │  │
│  │  ├── POST /api/v1/actions/send-email     # Send email             │  │
│  │  ├── POST /api/v1/actions/post-linkedin  # Post to LinkedIn       │  │
│  │  ├── POST /api/v1/actions/post-facebook  # Post to Facebook       │  │
│  │  ├── GET  /api/v1/odoo/invoices          # Get invoices (Odoo)    │  │
│  │  └── POST /api/v1/odoo/create-invoice    # Create invoice (Odoo)  │  │
│  │                                                                   │  │
│  │  Security:                                                        │  │
│  │  - API key authentication (from users.api_key)                    │  │
│  │  - Row-level security (RLS) in PostgreSQL                         │  │
│  │  - Encryption for sensitive tokens                                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              │ HTTPS                                     │
│                              ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  WEB DASHBOARD (Optional - for customers)                         │  │
│  │  Service: Vercel / Netlify Free Tier                              │  │
│  │  Cost: FREE                                                       │  │
│  │                                                                   │  │
│  │  Features:                                                        │  │
│  │  - Customer signup/login                                          │  │
│  │  - Connect social accounts (OAuth buttons)                        │  │
│  │  - Configure Odoo settings                                        │  │
│  │  - View activity logs                                             │  │
│  │  - Manage team members                                            │  │
│  │  - Subscription management                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (API calls)
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Customer A     │  │  Customer B     │  │  Customer C     │
│  (ABC Corp)     │  │  (XYZ Ltd)      │  │  (John Doe)     │
│                 │  │                 │  │                 │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │  Local    │  │  │  │  Local    │  │  │  │  Local    │  │
│  │  Agent    │  │  │  │  Agent    │  │  │  │  Agent    │  │
│  │           │  │  │  │           │  │  │  │           │  │
│  │  Runs on: │  │  │  │  Runs on: │  │  │  │  Runs on: │  │
│  │  Windows  │  │  │  │  Mac      │  │  │  │  Linux    │  │
│  │  PC       │  │  │  │  PC       │  │  │  │  PC       │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
│                 │  │                 │  │                 │
│  Components:    │  │  Components:    │  │  Components:    │
│  - Watchers     │  │  - Watchers     │  │  - Watchers     │
│  - Orchestrator │  │  - Orchestrator │  │  - Orchestrator │
│  - Cloud Client │  │  - Cloud Client │  │  - Cloud Client │
│  - Skills       │  │  - Skills       │  │  - Skills       │
│                 │  │                 │  │                 │
│  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │
│  │  Odoo     │  │  │  │  Odoo     │  │  │  No Odoo    │  │
│  │  (Local   │  │  │  │  (Cloud   │  │  │  (Just      │  │
│  │  Docker)  │  │  │  │  Odoo.sh) │  │  │  WhatsApp,  │  │
│  │           │  │  │  │           │  │  │  LinkedIn)  │  │
│  │  URL:     │  │  │  │  URL:     │  │  │             │  │
│  │  local-   │  │  │  │  abc.odoo │  │  │             │  │
│  │  host:    │  │  │  │  .com     │  │  │             │  │
│  │  8069     │  │  │  │           │  │  │             │  │
│  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 🔐 Security: How Data Isolation Works

### Your Concern: "Won't one user see another's data?"

**Answer: NO - Three layers of protection:**

### Layer 1: Database Row-Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE whatsapp_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY "Users can only see own sessions"
ON whatsapp_sessions
FOR ALL
USING (
    user_id = current_setting('app.current_user_id')::uuid
);

-- Similar policies for all token tables
CREATE POLICY "Users can only see own tokens"
ON email_tokens
FOR ALL
USING (
    user_id = current_setting('app.current_user_id')::uuid
);
```

**What this means:**
- Even if someone hacks the API, PostgreSQL **rejects** queries for other users' data
- Database enforces isolation at the lowest level
- Supabase has this built-in

---

### Layer 2: API Authentication

```javascript
// Every API call requires API key
POST /api/v1/actions/send-whatsapp
Headers:
  Authorization: Bearer sk_live_abc123xyz

// API validates:
// 1. API key exists in database
// 2. API key belongs to this user
// 3. User belongs to active customer
```

**What this means:**
- No API key = no access
- Wrong API key = rejected
- API key from Customer A ≠ access to Customer B's data

---

### Layer 3: Encryption at Rest

```javascript
// Tokens are encrypted before storing
const encrypted = encrypt(token, process.env.ENCRYPTION_KEY);

// Database stores:
{
  user_id: "uuid-123",
  access_token: "aes256:encrypted:blob:here"  // Can't read without key
}
```

**What this means:**
- Even if someone accesses the database directly, tokens are encrypted
- Each customer's data encrypted with their key
- You (platform) can't read customer tokens either

---

### Security Comparison

| Approach | Security Level | Industry Standard? |
|----------|---------------|-------------------|
| **Single DB with RLS** | ✅ High (PostgreSQL RLS + encryption) | ✅ Yes (Stripe, Slack use this) |
| Separate DB per customer | ✅ Maximum isolation | ❌ Overkill for MVP |
| No isolation | ❌ Dangerous | ❌ Never do this |

**Verdict:** Single DB with RLS is **industry standard** and **secure**.

---

## 💰 Cost: No Server Needed!

### Your Concern: "I don't have a server"

**Answer: You don't need one! Use free tiers:**

| Component | Service | Free Tier | Paid (when needed) |
|-----------|---------|-----------|-------------------|
| **Database** | Supabase | ✅ FREE (500MB, 50k users) | $25/month |
| **API Server** | Vercel Functions | ✅ FREE (100k req/month) | $20/month |
| **Web Dashboard** | Vercel | ✅ FREE (unlimited) | $20/month |
| **File Storage** | Supabase Storage | ✅ FREE (1GB) | $10/month |
| **Total** | | **$0/month** | **$55-75/month** |

### When Do You Pay?

- **0-100 customers**: $0/month (all free tiers)
- **100-1000 customers**: $25-50/month (upgrade database)
- **1000+ customers**: $75-150/month (upgrade everything)

**Revenue needed to break even:**
- 2-3 customers on Pro plan ($49/month) = covers all costs
- After that, pure profit!

---

## 📦 How Customers Get Your Software

### Distribution Options (No Server Needed)

### Option 1: GitHub Releases (Recommended for Start)

```
1. Customer visits: github.com/yourusername/ai-employee-vault/releases
2. Downloads: AI-Employee-Vault-Setup.exe (Windows)
3. Runs installer
4. Opens app, signs up with email
5. Gets API key automatically
6. Starts using!
```

**Cost:** FREE (GitHub is free)

---

### Option 2: Direct Download from Website

```
1. Customer visits: yourplatform.com
2. Clicks "Download for Windows"
3. File hosted on:
   - GitHub Releases (free)
   - Cloudflare R2 (free 10GB/month)
   - AWS S3 ($0.023/GB/month)
3. Runs installer
```

**Cost:** FREE to ~$1/month

---

### Option 3: Docker Container (Technical Customers)

```bash
docker pull yourusername/ai-employee-vault
docker run -d ai-employee-vault
```

**Cost:** FREE (Docker Hub free tier)

---

## 🏃 How It Works in Practice

### Customer Journey

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Customer Signs Up                                       │
│                                                                  │
│  1. Downloads local agent from your website/GitHub              │
│  2. Runs installer                                              │
│  3. Opens app, sees signup form                                 │
│  4. Enters: name, email, company name, password                 │
│  5. Clicks "Sign Up"                                            │
│  6. Local agent calls: POST /api/v1/auth/register               │
│  7. API creates: customer + user in database                    │
│  8. API returns: api_key                                        │
│  9. Local agent saves api_key locally                           │
│  10. Customer is logged in!                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Customer Connects WhatsApp                              │
│                                                                  │
│  1. In local agent, clicks "Connect WhatsApp"                   │
│  2. Local agent calls: POST /api/v1/oauth/whatsapp/start        │
│  3. API generates QR code, returns to local agent               │
│  4. Local agent shows QR code in app                            │
│  5. Customer scans QR with phone                                │
│  6. WhatsApp Web authenticates                                  │
│  7. Local agent calls: POST /api/v1/oauth/whatsapp/callback     │
│  8. API saves session to database (encrypted, with user_id)     │
│  9. WhatsApp connected!                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Customer Uses the System                                │
│                                                                  │
│  1. Drops file in: C:\AI_Employee_Vault\Drop\invoice.csv        │
│  2. Local agent's file watcher detects                          │
│  3. Orchestrator processes file                                 │
│  4. Needs to send WhatsApp?                                     │
│     → Calls: POST /api/v1/actions/send-whatsapp                 │
│     → Includes: api_key in headers                              │
│     → API validates key, gets user's session, sends message     │
│  5. Needs to post LinkedIn?                                     │
│     → Calls: POST /api/v1/actions/post-linkedin                 │
│     → Includes: api_key in headers                              │
│     → API validates key, gets user's token, posts               │
│  6. Action logged to database                                   │
│  7. Customer sees result in local agent                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure (After Reorganization)

```
D:\AI\Hackathon-0\
├── local-agent/              # NEW: Packaged local agent
│   ├── src/                  # Your existing code
│   │   ├── orchestrator.py
│   │   ├── watchers/
│   │   ├── skills/
│   │   └── cloud_client.py   # NEW: Calls cloud API
│   ├── package.json
│   └── build-config.json     # For creating .exe
│
├── cloud-api/                # NEW: Serverless API functions
│   ├── api/
│   │   ├── auth/
│   │   │   ├── register.js
│   │   │   └── login.js
│   │   ├── oauth/
│   │   │   ├── [platform]/
│   │   │   │   ├── start.js
│   │   │   │   └── callback.js
│   │   ├── actions/
│   │   │   ├── send-whatsapp.js
│   │   │   ├── send-email.js
│   │   │   ├── post-linkedin.js
│   │   │   └── post-facebook.js
│   │   └── odoo/
│   │       ├── get-invoices.js
│   │       └── create-invoice.js
│   ├── lib/
│   │   ├── database.js
│   │   └── encryption.js
│   └── vercel.json
│
├── web-dashboard/            # NEW: Customer web portal (optional)
│   ├── pages/
│   │   ├── index.js          # Landing page
│   │   ├── dashboard.js      # User dashboard
│   │   └── settings.js       # Account settings
│   └── vercel.json
│
├── docs/
│   └── architecture/
│       ├── Architecture.md
│       ├── MULTIUSER_ARCHITECTURE.md
│       └── SAAS_ARCHITECTURE.md  # THIS FILE
│
├── src/                    # Your existing code (stays for now)
├── watchers/               # Your existing watchers
├── servers/                # Your existing servers (for local testing)
├── scripts/                # Your existing scripts
└── skills/                 # Your existing skills
```

---

## 🚀 Implementation Plan

### Phase 1: Setup Cloud Infrastructure (Day 1-2)

**Tasks:**
1. Create Supabase account (free)
2. Create PostgreSQL database
3. Run schema SQL (create tables)
4. Enable Row-Level Security (RLS)
5. Get database URL and API keys

**Files to Create:**
- `cloud-api/database-schema.sql`
- `cloud-api/vercel.json`
- `cloud-api/lib/database.js`

**Cost:** $0

---

### Phase 2: Create API Functions (Day 3-5)

**Tasks:**
1. Setup Vercel account (free)
2. Create auth functions (register, login)
3. Create OAuth functions (start, callback)
4. Create action functions (send WhatsApp, post LinkedIn)
5. Deploy to Vercel

**Files to Create:**
- `cloud-api/api/auth/register.js`
- `cloud-api/api/auth/login.js`
- `cloud-api/api/oauth/whatsapp/start.js`
- `cloud-api/api/oauth/linkedin/start.js`
- `cloud-api/api/actions/send-whatsapp.js`
- `cloud-api/api/actions/post-linkedin.js`

**Cost:** $0

---

### Phase 3: Update Local Agent (Day 6-8)

**Tasks:**
1. Create `local-agent/src/cloud_client.py`
2. Update orchestrator to use cloud client
3. Add API key storage (local config file)
4. Add signup/login flow
5. Test with cloud API

**Files to Create:**
- `local-agent/src/cloud_client.py`
- `local-agent/src/auth.py`
- `local-agent/config.json`

**Code Changes:**
```python
# OLD (from .env)
LINKEDIN_TOKEN = os.getenv('LINKEDIN_TOKEN')

# NEW (from cloud API)
from cloud_client import get_user_tokens
tokens = get_user_tokens(API_KEY)
LINKEDIN_TOKEN = tokens['linkedin']['access_token']
```

**Cost:** $0

---

### Phase 4: Package Local Agent (Day 9-10)

**Tasks:**
1. Create installer script
2. Build .exe for Windows
3. Build .dmg for Mac
4. Upload to GitHub Releases
5. Test installation on clean PC

**Tools:**
- PyInstaller (Python to .exe)
- or Electron (if you want GUI)

**Cost:** $0

---

### Phase 5: Launch MVP (Day 11-14)

**Tasks:**
1. Create landing page (simple HTML)
2. Add download links
3. Add signup form
4. Test with 2-3 beta customers
5. Fix bugs

**Cost:** $0

---

## 📊 Data Flow Examples

### Example 1: New Customer Signup

```
Customer (Local PC)                    Cloud API (Vercel)              Database (Supabase)
      │                                      │                                │
      │  POST /api/v1/auth/register          │                                │
      │  {name, email, company, password}    │                                │
      ├─────────────────────────────────────>│                                │
      │                                      │                                │
      │                                      │  INSERT INTO customers         │
      │                                      │  INSERT INTO users             │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │                                      │  Returns: user_id, api_key     │
      │                                      │<───────────────────────────────┤
      │                                      │                                │
      │  Returns: {api_key, user_id}         │                                │
      │<─────────────────────────────────────┤                                │
      │                                      │                                │
      │  Saves api_key to local config       │                                │
      │                                      │                                │
```

---

### Example 2: Connect WhatsApp

```
Customer (Local PC)                    Cloud API (Vercel)              Database (Supabase)
      │                                      │                                │
      │  POST /api/v1/oauth/whatsapp/start   │                                │
      │  Headers: Authorization: Bearer sk_… │                                │
      ├─────────────────────────────────────>│                                │
      │                                      │                                │
      │                                      │  Validate API key              │
      │                                      │  SELECT * FROM users           │
      │                                      │  WHERE api_key = ?             │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │                                      │  Returns: user_id              │
      │                                      │<───────────────────────────────┤
      │                                      │                                │
      │                                      │  Generate QR code              │
      │                                      │                                │
      │  Returns: {qr_code, session_id}      │                                │
      │<─────────────────────────────────────┤                                │
      │                                      │                                │
      │  Shows QR code to customer           │                                │
      │  Customer scans with phone           │                                │
      │                                      │                                │
      │  WhatsApp Web authenticated!         │                                │
      │                                      │                                │
      │  POST /api/v1/oauth/whatsapp/callback│                                │
      │  {session_data, session_id}          │                                │
      ├─────────────────────────────────────>│                                │
      │                                      │                                │
      │                                      │  Encrypt session_data          │
      │                                      │  INSERT INTO whatsapp_sessions │
      │                                      │  WHERE user_id = ?             │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │  Returns: {status: "connected"}      │                                │
      │<─────────────────────────────────────┤                                │
      │                                      │                                │
```

---

### Example 3: Send WhatsApp Message

```
Customer (Local PC)                    Cloud API (Vercel)              WhatsApp Web
      │                                      │                                │
      │  Drop file: invoice.csv              │                                │
      │  File watcher detects                │                                │
      │  Orchestrator processes              │                                │
      │  Determines: send WhatsApp           │                                │
      │                                      │                                │
      │  POST /api/v1/actions/send-whatsapp  │                                │
      │  Headers: Authorization: Bearer sk_… │                                │
      │  Body: {phone, message}              │                                │
      ├─────────────────────────────────────>│                                │
      │                                      │                                │
      │                                      │  Validate API key              │
      │                                      │  Get user_id from database     │
      │                                      │                                │
      │                                      │  GET user's session            │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │                                      │  Returns: session_data         │
      │                                      │<───────────────────────────────┤
      │                                      │                                │
      │                                      │  Use whatsapp-web.js           │
      │                                      │  client.sendMessage()          │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │                                      │  Message sent!                 │
      │                                      │                                │
      │                                      │  Log action to database        │
      │                                      ├───────────────────────────────>│
      │                                      │                                │
      │  Returns: {status: "sent", id: …}    │                                │
      │<─────────────────────────────────────┤                                │
      │                                      │                                │
      │  Update Dashboard.md                 │                                │
      │  Move to Done/                       │                                │
      │                                      │                                │
```

---

## 🔒 Security Checklist

### ✅ What We're Doing Right

- [x] Row-Level Security (RLS) in PostgreSQL
- [x] API key authentication for all endpoints
- [x] Encryption for sensitive tokens (AES-256)
- [x] HTTPS for all communication
- [x] No plaintext passwords (bcrypt hashing)
- [x] Rate limiting on API endpoints
- [x] Input validation on all endpoints
- [x] CORS restrictions
- [x] Environment variables for secrets

### ⚠️ What to Add Later (When Paid Customers)

- [ ] Audit logging (who accessed what when)
- [ ] Two-factor authentication (2FA)
- [ ] IP whitelisting for enterprise customers
- [ ] SOC 2 compliance
- [ ] Regular security audits

---

## 📈 Scaling Plan

### Growth Stages

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: 0-100 Customers (Current Plan)                        │
│                                                                  │
│  Infrastructure:                                                 │
│  - Database: Supabase Free (500MB)                              │
│  - API: Vercel Free (100k requests/month)                       │
│  - Dashboard: Vercel Free                                       │
│  - Total Cost: $0/month                                         │
│                                                                  │
│  Team: You (solo founder)                                       │
│  Support: Email + GitHub Issues                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ At ~100 customers, upgrade to:
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: 100-1000 Customers                                     │
│                                                                  │
│  Infrastructure:                                                 │
│  - Database: Supabase Pro ($25/month)                           │
│  - API: Vercel Pro ($20/month)                                  │
│  - Dashboard: Vercel Pro ($20/month)                            │
│  - Monitoring: Sentry ($25/month)                               │
│  - Total Cost: ~$90/month                                       │
│                                                                  │
│  Revenue Needed: 2-3 Pro customers ($49/month)                  │
│  Team: You + 1 part-time support                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ At ~1000 customers, upgrade to:
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: 1000-10000 Customers                                   │
│                                                                  │
│  Infrastructure:                                                 │
│  - Database: Supabase Team ($50/month) or self-hosted           │
│  - API: Vercel Enterprise or dedicated servers                  │
│  - CDN: Cloudflare ($200/month)                                 │
│  - Monitoring: Sentry Business ($100/month)                     │
│  - Total Cost: ~$500-1000/month                                 │
│                                                                  │
│  Revenue Needed: 20-30 Pro customers                            │
│  Team: 3-5 people (dev, support, sales)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 What Makes This Different

### vs. Traditional SaaS

| Traditional SaaS | Our Hybrid Approach |
|-----------------|---------------------|
| Everything in cloud | Cloud + local agent |
| Monthly server costs | Free tiers initially |
| Complex deployment | Simple download & run |
| Customer data on your server | Customer data encrypted, isolated |
| Need server from day 1 | No server needed |

### vs. Pure Local Software

| Pure Local Software | Our Hybrid Approach |
|--------------------|---------------------|
| No cloud dependency | Cloud for auth + tokens |
| Customer manages everything | We manage OAuth, tokens |
| Hard to update | Easy updates via cloud API |
| No central analytics | Can track usage (with permission) |
| Piracy risk | API key required |

---

## ❓ FAQ

### Q: Can customers use this without internet?

**A:** Partially. Local watchers work offline, but actions (send WhatsApp, post LinkedIn) need internet to call cloud API.

---

### Q: What if Supabase goes down?

**A:** Customers can't authenticate or execute new actions, but local watchers continue working. Consider backup database provider later.

---

### Q: Can I migrate to separate databases later?

**A:** Yes! Start with single DB, migrate high-value customers to dedicated DBs later. Common pattern.

---

### Q: How do I handle GDPR/data deletion?

**A:** Add `DELETE /api/v1/users/:id` endpoint that cascades deletes to all user data. Supabase has GDPR tools.

---

### Q: What about backups?

**A:** Supabase includes automatic daily backups (free tier). Can restore from dashboard.

---

### Q: Can customers export their data?

**A:** Add `GET /api/v1/users/:id/export` endpoint that returns all user data as JSON/CSV.

---

## 📝 Next Steps

### Immediate (This Week)

1. ✅ Read this document thoroughly
2. ✅ Create Supabase account
3. ✅ Create database schema
4. ✅ Create Vercel account
5. ✅ Deploy first API function (health check)

### Short-term (Next 2 Weeks)

1. Implement auth API (register, login)
2. Implement OAuth API (WhatsApp, LinkedIn)
3. Update local agent with cloud client
4. Test end-to-end with fake customer

### Medium-term (Next Month)

1. Create simple landing page
2. Package local agent as .exe
3. Upload to GitHub Releases
4. Get 2-3 beta customers

---

## 📞 Support

For questions about this architecture:
- Review this document first
- Check `docs/architecture/` for details
- Create GitHub issue for discussions

---

**Last Updated:** 2026-02-26  
**Version:** 1.0  
**Status:** Ready for Implementation

---

## Appendix A: Database Schema (Complete SQL)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    subscription TEXT DEFAULT 'basic' CHECK (subscription IN ('basic', 'pro', 'enterprise')),
    odoo_url TEXT,
    odoo_db TEXT,
    odoo_user TEXT,
    odoo_pass TEXT,
    stripe_customer_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (employees of customers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    api_key TEXT UNIQUE DEFAULT 'sk_' || md5(random()::text),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WhatsApp sessions
CREATE TABLE whatsapp_sessions (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL,
    phone_number TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'expired')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email tokens
CREATE TABLE email_tokens (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LinkedIn tokens
CREATE TABLE linkedin_tokens (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    urn TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Facebook tokens
CREATE TABLE facebook_tokens (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    page_id TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Instagram tokens
CREATE TABLE instagram_tokens (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    instagram_user_id TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- X (Twitter) tokens
CREATE TABLE x_tokens (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    access_token_secret TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Action logs
CREATE TABLE action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    status TEXT NOT NULL,
    request_data JSONB,
    response_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row-Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE linkedin_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE facebook_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE instagram_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE x_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can see own record"
ON users FOR SELECT
USING (id = current_setting('app.current_user_id')::uuid);

CREATE POLICY "Users can update own record"
ON users FOR UPDATE
USING (id = current_setting('app.current_user_id')::uuid);

-- RLS Policies for token tables (example: whatsapp_sessions)
CREATE POLICY "Users can see own sessions"
ON whatsapp_sessions FOR SELECT
USING (user_id = current_setting('app.current_user_id')::uuid);

CREATE POLICY "Users can insert own sessions"
ON whatsapp_sessions FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id')::uuid);

CREATE POLICY "Users can update own sessions"
ON whatsapp_sessions FOR UPDATE
USING (user_id = current_setting('app.current_user_id')::uuid);

-- Similar policies for all token tables...

-- RLS Policies for action_logs
CREATE POLICY "Users can see own logs"
ON action_logs FOR SELECT
USING (user_id = current_setting('app.current_user_id')::uuid);

CREATE POLICY "Users can insert own logs"
ON action_logs FOR INSERT
WITH CHECK (user_id = current_setting('app.current_user_id')::uuid);

-- Indexes for performance
CREATE INDEX idx_users_customer_id ON users(customer_id);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_action_logs_user_id ON action_logs(user_id);
CREATE INDEX idx_action_logs_created_at ON action_logs(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_whatsapp_sessions_updated_at BEFORE UPDATE ON whatsapp_sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- (Add similar triggers for all token tables)
```

---

## Appendix B: Environment Variables Template

```bash
# .env for Cloud API (Vercel)

# Supabase Database
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...  # Keep secret!

# Encryption
ENCRYPTION_KEY=your-32-character-secret-key-here

# OAuth Credentials (for your platform's OAuth apps)
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
LINKEDIN_REDIRECT_URI=https://your-api.vercel.app/api/v1/oauth/linkedin/callback

FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret
FACEBOOK_REDIRECT_URI=https://your-api.vercel.app/api/v1/oauth/facebook/callback

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_USER=notifications@yourplatform.com
SMTP_PASS=your-app-password

# Stripe (for payments - add later)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

**END OF DOCUMENT**
