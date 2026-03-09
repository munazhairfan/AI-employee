# AI Agent Integration Plan

**Version:** 1.0  
**Date:** 2026-02-27  
**Status:** Ready for Implementation  
**Priority:** CRITICAL - Zero Hallucination, Zero Wrong Logic

---

## 📋 Executive Summary

This document details the integration of an AI agent into the AI Employee Vault system at **both local and SaaS levels**, with **mandatory anti-hallucination safeguards**.

### Core Principles

1. ✅ **Zero Hallucination** - AI extracts facts only, never invents information
2. ✅ **Human-in-the-Loop** - All AI suggestions require human approval before execution
3. ✅ **Source Citation** - Every AI extraction must cite its source text
4. ✅ **Confidence Scoring** - AI rates confidence, low scores trigger mandatory human review
5. ✅ **Full Audit Trail** - All AI decisions logged for review and accountability

---

## 🏗️ Architecture Overview

### Current State (Local-Only)

```
┌─────────────────────────────────────────────────────────────┐
│  Customer's Computer (Local Execution)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Gmail      │  │   WhatsApp   │  │    File      │      │
│  │   Watcher    │  │   Watcher    │  │   Watcher    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ▼                                 │
│              ┌────────────────────────┐                     │
│              │   orchestrator.py      │                     │
│              │   + SKILL_*.md files   │                     │
│              │   - Runs locally       │                     │
│              │   - Uses Claude CLI    │                     │
│              │   - Creates drafts     │                     │
│              └───────────┬────────────┘                     │
│                          │                                  │
│                          ▼                                  │
│         ┌────────────────────────────────┐                 │
│         │   Pending_Approval/            │                 │
│         │   - Draft files (.md)          │                 │
│         │   - Human reviews & approves   │                 │
│         └────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

**Limitations:**
- ❌ Requires user to install Python, Node.js, dependencies
- ❌ User must keep computer on 24/7
- ❌ No centralized audit trail
- ❌ Each user manages their own credentials
- ❌ Hard to distribute updates

---

### Target State (Hybrid SaaS)

```
┌─────────────────────────────────────────────────────────────┐
│  CLOUD INFRASTRUCTURE (Vercel + Supabase)                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  AI Agent Service (24/7 Processing)                   │ │
│  │  Service: Vercel Edge Functions / Railway / Fly.io    │ │
│  │                                                       │ │
│  │  Components:                                          │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 1. Input Validation Layer                       │  │ │
│  │  │    - Authenticate user (API key)                │  │ │
│  │  │    - Validate input format                      │  │ │
│  │  │    - Rate limiting                              │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 2. Constrained AI Processing                    │  │ │
│  │  │    - Extract facts ONLY (no generation)         │  │ │
│  │  │    - Source citation required                   │  │ │
│  │  │    - Confidence scoring                         │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 3. Draft Generation & Validation                │  │ │
│  │  │    - Check required fields                      │  │ │
│  │  │    - Flag missing information                   │  │ │
│  │  │    - Store in pending_approval table            │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │ 4. Audit Logging                                │  │ │
│  │  │    - Log all AI decisions                       │  │ │
│  │  │    - Track human approvals/rejections           │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Supabase Database (PostgreSQL)                       │ │
│  │                                                       │ │
│  │  Tables:                                              │ │
│  │  - customers (multi-tenant isolation)                 │ │
│  │  - users (authentication, API keys)                   │ │
│  │  - pending_approval (AI-generated drafts)             │ │
│  │  - action_logs (execution audit trail)                │ │
│  │  - ai_audit_log (AI decision tracking)                │ │
│  │  - whatsapp_sessions, email_tokens, linkedin_tokens   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Web Dashboard (Optional)                             │ │
│  │  - User signup/login                                  │ │
│  │  - View pending drafts                                │ │
│  │  - Approve/reject actions                             │ │
│  │  - View audit logs                                    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS (Authenticated API)
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Customer A     │ │  Customer B     │ │  Customer C     │
│  (Local Agent)  │ │  (Local Agent)  │ │  (Web Only)     │
│                 │ │                 │ │                 │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ Watchers  │  │ │  │ Watchers  │  │ │  │  Browser  │  │
│  │ (Python)  │  │ │  │ (Python)  │  │ │  │  Dashboard│  │
│  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └───────────┘  │
│        │        │ │        │        │ │                 │
│        ▼        │ │        ▼        │ │                 │
│  Send to Cloud │ │  Send to Cloud │ │  Direct HTTPS    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🤖 AI Agent Design

### Anti-Hallucination Safeguards

#### Guard 1: Constrained Prompting

```python
SYSTEM_PROMPT = """
You are a data extraction assistant for AI Employee Vault.

CRITICAL RULES:
1. Extract facts ONLY from the provided message/file content
2. NEVER invent amounts, dates, names, or details
3. For each extracted field, cite the exact source text
4. If information is not explicitly stated, mark as "UNKNOWN"
5. Rate your confidence (0-100%) for each extraction
6. Fields with <80% confidence require human review

EXAMPLE INPUT:
"Hi, please send invoice for $500 to John"

EXAMPLE OUTPUT:
{
    "action": "create_invoice",
    "fields": {
        "amount": {
            "value": 500,
            "currency": "USD",
            "source_text": "invoice for $500",
            "confidence": 100
        },
        "recipient": {
            "value": "John",
            "source_text": "to John",
            "confidence": 90,
            "note": "Full name not provided"
        },
        "due_date": {
            "value": null,
            "source_text": null,
            "confidence": 0,
            "reason": "No due date mentioned in message"
        }
    },
    "requires_human_review": true,
    "review_reason": "recipient confidence <80%, due_date unknown"
}
"""
```

#### Guard 2: Source Citation Requirement

```python
def validate_extraction(extraction: dict) -> tuple[bool, list[str]]:
    """
    Validate that all extracted fields have source citations.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    for field_name, field_data in extraction.get('fields', {}).items():
        # Check source_text exists for non-null values
        if field_data.get('value') is not None:
            if not field_data.get('source_text'):
                errors.append(f"{field_name}: missing source citation")
        
        # Check confidence score exists
        if 'confidence' not in field_data:
            errors.append(f"{field_name}: missing confidence score")
        elif field_data['confidence'] < 0 or field_data['confidence'] > 100:
            errors.append(f"{field_name}: invalid confidence score")
    
    return len(errors) == 0, errors
```

#### Guard 3: Confidence-Based Routing

```python
def requires_human_review(extraction: dict) -> tuple[bool, str]:
    """
    Determine if extraction requires human review.
    Returns (needs_review, reason)
    """
    fields = extraction.get('fields', {})
    
    # Check for any low-confidence fields
    for field_name, field_data in fields.items():
        confidence = field_data.get('confidence', 0)
        if confidence < 80:
            return True, f"{field_name} confidence too low ({confidence}%)"
        
        if field_data.get('value') is None:
            return True, f"{field_name} not found in source"
    
    # Check if extraction itself flagged for review
    if extraction.get('requires_human_review'):
        return True, extraction.get('review_reason', 'AI flagged for review')
    
    return False, ""
```

#### Guard 4: Mandatory Audit Logging

```python
def log_ai_decision(draft_id: str, user_id: str, input_data: dict, 
                    ai_output: dict, human_action: str = None):
    """
    Log all AI decisions to audit trail.
    """
    supabase.table('ai_audit_log').insert({
        'draft_id': draft_id,
        'user_id': user_id,
        'input_data': input_data,
        'ai_output': ai_output,
        'human_action': human_action,  # 'approved', 'rejected', 'modified'
        'human_modified_data': None,   # Filled if human changed AI output
        'created_at': datetime.now().isoformat()
    })
```

---

## 📁 File Structure

### Current (Local)

```
D:\AI\Hackathon-0\
├── src/
│   └── orchestrator.py          # Main AI agent logic
├── watchers/
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   └── filesystem_watcher.py
├── skills/
│   ├── SKILL_reasoning_loop.md
│   ├── SKILL_generate_email_draft.md
│   ├── SKILL_generate_whatsapp_draft.md
│   └── SKILL_approval_handler.md
├── AI_Employee_Vault/
│   ├── Needs_Action/            # Input files
│   ├── Plans/                   # AI-generated plans
│   └── Pending_Approval/        # Drafts for human review
└── Logs/
    └── *.json                   # Audit logs
```

### Target (SaaS + Local Agent)

```
D:\AI\Hackathon-0\
├── cloud-api/                    # NEW: Vercel serverless functions
│   ├── api/
│   │   ├── triggers/
│   │   │   ├── whatsapp.js      # WhatsApp webhook handler
│   │   │   ├── gmail.js         # Gmail webhook handler
│   │   │   └── file-drop.js     # File system trigger
│   │   ├── actions/
│   │   │   ├── send-whatsapp.js
│   │   │   ├── send-email.js
│   │   │   ├── post-linkedin.js
│   │   │   └── create-invoice.js
│   │   ├── ai-agent/
│   │   │   ├── process.js       # Main AI processing
│   │   │   ├── prompts.js       # AI prompt definitions
│   │   │   └── validation.js    # Anti-hallucination guards
│   │   └── users/
│   │       ├── register.js
│   │       └── dashboard.js
│   ├── lib/
│   │   ├── supabase.js          # Database client
│   │   ├── ai-client.js         # AI model client
│   │   └── validation.js        # Input validation
│   ├── package.json
│   └── vercel.json
│
├── local-agent/                  # NEW: Lightweight watcher
│   ├── watchers/
│   │   ├── gmail_watcher.py
│   │   ├── whatsapp_watcher.py
│   │   └── filesystem_watcher.py
│   ├── cloud_client.py          # Cloud API integration
│   ├── config.py                # Configuration
│   └── requirements.txt
│
├── src/                          # Keep for local-only mode
│   └── orchestrator.py
├── watchers/                     # Keep for local-only mode
│   └── *.py
├── skills/                       # Keep AI prompts
│   └── SKILL_*.md
│
└── docs/
    └── architecture/
        ├── SAAS_ARCHITECTURE.md
        └── AI_AGENT_INTEGRATION.md  # THIS DOCUMENT
```

---

## 🔄 Complete Flow Examples

### Flow 1: WhatsApp Message Processing (SaaS Mode)

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Local Agent Detects Message                             │
├─────────────────────────────────────────────────────────────────┤
│ Customer's Computer                                             │
│                                                                 │
│ whatsapp_watcher.py:                                            │
│   - Detects new message: "Send invoice for $500"               │
│   - Packages data:                                              │
│     {                                                           │
│       "user_id": "user_abc123",                                 │
│       "from": "+1234567890",                                    │
│       "message": "Send invoice for $500",                       │
│       "timestamp": "2026-02-27T10:30:00Z"                       │
│     }                                                           │
│   - Sends to cloud API                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Cloud API Receives & Validates                          │
├─────────────────────────────────────────────────────────────────┤
│ Vercel Function: /api/v1/triggers/whatsapp                      │
│                                                                 │
│ 1. Authenticate user (API key validation)                       │
│ 2. Validate input format (required fields present)              │
│ 3. Rate limiting (max 100 requests/minute)                      │
│ 4. Log to input_audit table                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: AI Agent Processing (Constrained)                       │
├─────────────────────────────────────────────────────────────────┤
│ cloud-api/ai-agent/process.js                                   │
│                                                                 │
│ 1. Call AI with constrained prompt:                             │
│    SYSTEM: "Extract facts ONLY, cite sources, rate confidence"  │
│    USER: {message: "Send invoice for $500"}                     │
│                                                                 │
│ 2. AI Response:                                                 │
│    {                                                            │
│      "action": "create_invoice",                                │
│      "fields": {                                                │
│        "amount": {                                              │
│          "value": 500,                                          │
│          "source_text": "invoice for $500",                     │
│          "confidence": 100                                      │
│        },                                                       │
│        "customer": {                                            │
│          "value": null,                                         │
│          "source_text": null,                                   │
│          "confidence": 0,                                       │
│          "reason": "Customer not mentioned"                     │
│        }                                                        │
│      },                                                         │
│      "requires_human_review": true,                             │
│      "review_reason": "customer unknown"                        │
│    }                                                            │
│                                                                 │
│ 3. Validate AI output (source citations, confidence scores)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Store Draft in Database                                 │
├─────────────────────────────────────────────────────────────────┤
│ Supabase: pending_approval table                                │
│                                                                 │
│ Insert:                                                         │
│ {                                                               │
│   "id": "draft_xyz789",                                         │
│   "user_id": "user_abc123",                                     │
│   "action_type": "create_invoice",                              │
│   "draft_data": { ... AI output ... },                          │
│   "status": "pending",                                          │
│   "requires_human_review": true,                                │
│   "review_reason": "customer unknown",                          │
│   "created_at": "2026-02-27T10:30:05Z"                          │
│ }                                                               │
│                                                                 │
│ Return to local agent:                                          │
│ { "draft_id": "draft_xyz789", "status": "pending_approval" }    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Human Review (Dashboard)                                │
├─────────────────────────────────────────────────────────────────┤
│ Web Dashboard or Local UI                                       │
│                                                                 │
│ Shows:                                                          │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Draft #xyz789 - Create Invoice                            │  │
│ │                                                           │  │
│ │ Extracted Data:                                           │  │
│ │ ✓ Amount: $500 (confidence: 100%)                         │  │
│ │   Source: "invoice for $500"                              │  │
│ │                                                           │  │
│ │ ✗ Customer: UNKNOWN                                       │  │
│ │   Reason: Customer not mentioned in message               │  │
│ │   [Action Required: Add customer details]                 │  │
│ │                                                           │  │
│ │ [✅ Approve] [❌ Reject] [✏️ Edit & Approve]            │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ Human clicks "Edit & Approve", adds customer details            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Execute Approved Action                                 │
├─────────────────────────────────────────────────────────────────┤
│ Vercel Function: /api/v1/actions/create-invoice                 │
│                                                                 │
│ 1. Verify draft approval status                                 │
│ 2. Call Odoo API to create invoice                              │
│ 3. Log to action_logs table                                     │
│ 4. Update ai_audit_log with human_action: "approved_modified"   │
│ 5. Return success                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 2: Local Mode (No Cloud)

```
┌─────────────────────────────────────────────────────────────────┐
│ Local Execution (orchestrator.py)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Watchers detect new file in Needs_Action/                    │
│                                                                 │
│ 2. orchestrator.py reads file                                   │
│                                                                 │
│ 3. Call Claude CLI for AI reasoning:                            │
│    subprocess.run(['claude', 'Execute', 'skills/SKILL_*.md'])   │
│                                                                 │
│ 4. AI generates draft in Pending_Approval/                      │
│                                                                 │
│ 5. Human reviews draft file locally                             │
│                                                                 │
│ 6. Human approves → orchestrator executes action                │
│                                                                 │
│ 7. Log to Logs/*.json                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Plan

### Phase 1: Local AI Enhancement (1-2 days)

**Goal:** Add anti-hallucination guards to existing local setup

**Tasks:**
- [ ] Update `SKILL_reasoning_loop.md` with source citation requirement
- [ ] Add confidence scoring to all SKILL files
- [ ] Update `orchestrator.py` to validate AI output
- [ ] Add mandatory human review for low-confidence extractions
- [ ] Enhance audit logging in `Logs/*.json`

**Files to Modify:**
```
skills/SKILL_reasoning_loop.md
skills/SKILL_generate_email_draft.md
skills/SKILL_generate_whatsapp_draft.md
src/orchestrator.py
```

---

### Phase 2: Cloud API Foundation (3-5 days)

**Goal:** Deploy basic cloud infrastructure

**Tasks:**
- [ ] Create Supabase project (free tier)
- [ ] Set up database schema (customers, users, pending_approval, action_logs)
- [ ] Create Vercel project
- [ ] Implement authentication API (`/api/v1/auth/*`)
- [ ] Implement user registration/login
- [ ] Create API key management

**Files to Create:**
```
cloud-api/
├── api/auth/register.js
├── api/auth/login.js
├── api/users/me.js
├── lib/supabase.js
├── package.json
└── vercel.json
```

---

### Phase 3: AI Agent Cloud Integration (5-7 days)

**Goal:** Migrate AI processing to cloud with anti-hallucination guards

**Tasks:**
- [ ] Create AI processing function (`/api/v1/ai-agent/process`)
- [ ] Implement constrained prompting
- [ ] Add source citation validation
- [ ] Add confidence scoring
- [ ] Implement confidence-based routing (auto vs. human review)
- [ ] Create draft storage in Supabase
- [ ] Implement audit logging

**Files to Create:**
```
cloud-api/
├── api/ai-agent/process.js
├── api/ai-agent/prompts.js
├── api/ai-agent/validation.js
└── lib/ai-client.js
```

---

### Phase 4: Local Agent Development (3-5 days)

**Goal:** Create lightweight local agent for watchers

**Tasks:**
- [ ] Create `local-agent/` directory structure
- [ ] Migrate watchers to local-agent
- [ ] Add cloud API client
- [ ] Implement authentication
- [ ] Add offline mode (queue when cloud unavailable)
- [ ] Create configuration management

**Files to Create:**
```
local-agent/
├── watchers/gmail_watcher.py
├── watchers/whatsapp_watcher.py
├── watchers/filesystem_watcher.py
├── cloud_client.py
├── config.py
└── requirements.txt
```

---

### Phase 5: Trigger Handlers (3-5 days)

**Goal:** Connect local agents to cloud AI

**Tasks:**
- [ ] Create WhatsApp trigger handler
- [ ] Create Gmail trigger handler
- [ ] Create file-drop trigger handler
- [ ] Implement webhook endpoints
- [ ] Add input validation
- [ ] Add rate limiting

**Files to Create:**
```
cloud-api/
├── api/triggers/whatsapp.js
├── api/triggers/gmail.js
└── api/triggers/file-drop.js
```

---

### Phase 6: Action Executors (5-7 days)

**Goal:** Implement cloud-based action execution

**Tasks:**
- [ ] Create WhatsApp sender
- [ ] Create email sender
- [ ] Create LinkedIn poster
- [ ] Create Facebook poster
- [ ] Create invoice generator (Odoo integration)
- [ ] Add approval verification before execution

**Files to Create:**
```
cloud-api/
├── api/actions/send-whatsapp.js
├── api/actions/send-email.js
├── api/actions/post-linkedin.js
├── api/actions/post-facebook.js
└── api/actions/create-invoice.js
```

---

### Phase 7: Web Dashboard (5-7 days)

**Goal:** Create web UI for draft approval

**Tasks:**
- [ ] Create dashboard HTML/CSS/JS
- [ ] Implement user authentication UI
- [ ] Create pending drafts list view
- [ ] Create draft detail view
- [ ] Implement approve/reject/edit actions
- [ ] Add audit log viewer
- [ ] Deploy to Vercel

**Files to Create:**
```
cloud-api/
├── public/
│   ├── index.html
│   ├── dashboard.html
│   ├── login.html
│   └── js/
│       ├── auth.js
│       └── dashboard.js
└── api/users/dashboard.js
```

---

### Phase 8: Testing & Validation (3-5 days)

**Goal:** Comprehensive testing of anti-hallucination guards

**Tasks:**
- [ ] Test source citation validation
- [ ] Test confidence scoring accuracy
- [ ] Test human review routing
- [ ] Test audit log completeness
- [ ] Load testing
- [ ] Security audit

**Files to Create:**
```
tests/
├── test_ai_hallucination_guards.js
├── test_ai_hallucination_guards.py
└── test_cloud_api.js
```

---

## 🗄️ Database Schema

### Supabase Tables

```sql
-- Customers (multi-tenant isolation)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    subscription TEXT DEFAULT 'basic',
    odoo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users (authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    api_key TEXT UNIQUE DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pending Approvals (AI-generated drafts)
CREATE TABLE pending_approval (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action_type TEXT NOT NULL,
    draft_data JSONB NOT NULL,
    status TEXT DEFAULT 'pending',
    requires_human_review BOOLEAN DEFAULT true,
    review_reason TEXT,
    human_modified_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    executed_at TIMESTAMP
);

-- Action Logs (execution audit trail)
CREATE TABLE action_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    draft_id UUID REFERENCES pending_approval(id),
    action_type TEXT NOT NULL,
    status TEXT NOT NULL,
    result JSONB,
    error TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- AI Audit Log (AI decision tracking)
CREATE TABLE ai_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID REFERENCES pending_approval(id),
    user_id UUID REFERENCES users(id),
    input_data JSONB NOT NULL,
    ai_output JSONB NOT NULL,
    human_action TEXT,  -- 'approved', 'rejected', 'approved_modified'
    human_modified_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Platform Tokens (OAuth credentials)
CREATE TABLE whatsapp_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_data JSONB NOT NULL,
    phone_number TEXT,
    status TEXT DEFAULT 'disconnected',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE email_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE linkedin_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    urn TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Row Level Security (RLS)
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_approval ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies (example for users table)
CREATE POLICY "Users can view own data"
    ON users FOR SELECT
    USING (auth.uid()::text = id::text);

CREATE POLICY "Users can insert own data"
    ON users FOR INSERT
    WITH CHECK (auth.uid()::text = id::text);
```

---

## 🔐 Security Considerations

### Authentication

```javascript
// API key authentication middleware
function authenticateUser(req, res, next) {
    const apiKey = req.headers['authorization']?.replace('Bearer ', '');
    
    if (!apiKey) {
        return res.status(401).json({ error: 'API key required' });
    }
    
    // Look up user by API key
    const { data: user } = await supabase
        .from('users')
        .select('id, customer_id, email')
        .eq('api_key', apiKey)
        .single();
    
    if (!user) {
        return res.status(401).json({ error: 'Invalid API key' });
    }
    
    req.user = user;
    next();
}
```

### Encryption

```javascript
// Encrypt sensitive tokens before storing
import { encrypt, decrypt } from '@supabase/encryption';

async function storeToken(userId, platform, tokenData) {
    const encrypted = await encrypt(
        JSON.stringify(tokenData),
        process.env.ENCRYPTION_KEY
    );
    
    await supabase
        .from(`${platform}_tokens`)
        .insert({
            user_id: userId,
            encrypted_data: encrypted
        });
}
```

### Rate Limiting

```javascript
// Prevent abuse
import rateLimit from 'express-rate-limit';

const triggerLimiter = rateLimit({
    windowMs: 60 * 1000,  // 1 minute
    max: 100,             // 100 requests per minute
    message: 'Too many requests'
});

app.use('/api/v1/triggers/*', triggerLimiter);
```

---

## 📊 Monitoring & Observability

### Metrics to Track

```javascript
// Log key metrics
const metrics = {
    ai_processing: {
        total_requests: 0,
        successful_extractions: 0,
        hallucinations_prevented: 0,  // Low confidence → human review
        average_confidence_score: 0,
        average_processing_time_ms: 0
    },
    human_review: {
        total_drafts: 0,
        approved: 0,
        rejected: 0,
        modified: 0,
        average_review_time_minutes: 0
    },
    execution: {
        total_actions: 0,
        successful: 0,
        failed: 0
    }
};
```

### Alerting

```javascript
// Alert on suspicious AI behavior
if (averageConfidence < 70) {
    // Send alert to admin
    await sendAlert('Low AI confidence detected', {
        averageConfidence,
        timeWindow: 'last hour'
    });
}

if (rejectionRate > 50) {
    // High rejection rate - AI may need tuning
    await sendAlert('High draft rejection rate', {
        rejectionRate,
        timeWindow: 'last 24 hours'
    });
}
```

---

## 🎯 Success Criteria

### Phase 1 (Local Enhancement)
- [ ] All AI extractions include source citations
- [ ] Confidence scoring implemented for all action types
- [ ] Low-confidence drafts automatically flagged for human review
- [ ] Audit logs include AI decision data

### Phase 2-7 (SaaS Implementation)
- [ ] Cloud API deployed and authenticated
- [ ] Local agent successfully sends triggers to cloud
- [ ] AI processing includes all anti-hallucination guards
- [ ] Human review workflow functional
- [ ] Action execution verified with approval checks
- [ ] Full audit trail in Supabase

### Anti-Hallucination Validation
- [ ] Zero invented amounts/dates/names in test scenarios
- [ ] All extractions cite source text
- [ ] Confidence scores accurately reflect extraction certainty
- [ ] Human review catches all low-confidence extractions
- [ ] Audit logs complete for all AI decisions

---

## 📚 Related Documents

- `SAAS_ARCHITECTURE.md` - Overall SaaS architecture
- `MULTIUSER_ARCHITECTURE.md` - Multi-tenant design
- `SKILL_reasoning_loop.md` - AI reasoning prompts
- `../SECURITY.md` - Security guidelines

---

## 🔄 Next Steps

1. **Review this document** and confirm architecture
2. **Start Phase 1** - Enhance local AI with anti-hallucination guards
3. **Set up Supabase** - Create free tier project
4. **Create Vercel project** - Prepare cloud infrastructure
5. **Begin implementation** - Follow implementation plan above

---

*Last Updated: 2026-02-27*  
*Status: Ready for Implementation*
