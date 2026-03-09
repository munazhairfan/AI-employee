# Complete System Test Guide

**Date:** 2026-02-27  
**Status:** Ready to Test  
**Time Required:** 5 minutes

---

## 🎯 What We'll Test

We'll simulate a **real business scenario**:
1. Customer receives WhatsApp message requesting invoice
2. System detects message
3. AI analyzes and creates draft
4. Human reviews and approves
5. System executes action

---

## 📁 Test Scenario

**Scenario:** Customer sends WhatsApp message:
> "Hi, please send invoice #12345 for $500 to ABC Corp, due next Friday"

**Expected Flow:**
```
WhatsApp Message → AI Analysis → Draft Created → Human Review → Approval
```

---

## 🚀 Step-by-Step Test

### Step 1: Verify AI is Working

```bash
python test_ai_agent.py
```

**Expected:** All 6 tests PASS ✅

---

### Step 2: Create Test Input File

Create a test WhatsApp message file:

**File:** `AI_Employee_Vault/Needs_Action/WHATSAPP_test_001.md`

```bash
# Create the directory if it doesn't exist
mkdir AI_Employee_Vault\Needs_Action

# Create test file
echo ^---^>type: whatsapp
^---^>from: +1234567890
^---^>timestamp: 2026-02-27T10:30:00
^---^>

# Message Content

**From:** +1234567890
**Received:** 2026-02-27 10:30 AM
**Message:**
Hi, please send invoice #12345 for $500 to ABC Corp, due next Friday
^> AI_Employee_Vault\Needs_Action\WHATSAPP_test_001.md
```

**Or manually create the file** with this content:

```markdown
---
type: whatsapp
from: +1234567890
timestamp: 2026-02-27T10:30:00
---

# Message Content

**From:** +1234567890
**Received:** 2026-02-27 10:30 AM
**Message:**
Hi, please send invoice #12345 for $500 to ABC Corp, due next Friday
```

---

### Step 3: Run the Orchestrator

```bash
python src/orchestrator.py
```

**What happens:**
1. Orchestrator scans `Needs_Action/` folder
2. Finds `WHATSAPP_test_001.md`
3. Calls Groq AI to analyze message
4. Creates draft in `Pending_Approval/`
5. Logs to `Logs/`

**Expected Output:**
```
============================================================
AI Employee Vault - Orchestrator
============================================================
Scanning AI_Employee_Vault/Needs_Action...

Found 1 file(s) to process

Processing WHATSAPP_test_001.md...
  - Detected type: whatsapp
  - Using Groq API (llama-3.3-70b-versatile)...
  - AI analysis complete
  - Creating draft...
  - Draft created: whatsapp_Draft_2026-02-27_10-30-00.md
  - Confidence: 95.0%
  - Human review: Not required

Moving WHATSAPP_test_001.md to Processed...

Done! Press Ctrl+C to stop.
```

---

### Step 4: Check the Draft

Open the created draft file:

```bash
type Pending_Approval\whatsapp_Draft_*.md
```

**Expected Content:**
```markdown
---
type: whatsapp_draft
status: pending_review
generated_at: 2026-02-27T10:30:00
requires_human_review: false
ai_confidence_average: 95.0
---

# Draft: Whatsapp

## Action Details

**From:** +1234567890

## Original Message

Hi, please send invoice #12345 for $500 to ABC Corp, due next Friday

## Suggested Reply

Hi! Thanks for reaching out. I'll prepare invoice #12345 for $500 and send it over within the hour. Should I send it to this number or a different email?

Appreciate your patience! 🙏

## Extracted Information (With Source Citations)

| Field | Value | Source Text | Confidence |
|-------|-------|-------------|------------|
| sender | +1234567890 | "from frontmatter" | 100% |
| intent | Request invoice | "please send invoice" | 100% |
| amount | 500 | "$500" | 100% |
| customer | ABC Corp | "to ABC Corp" | 100% |
| invoice_number | 12345 | "invoice #12345" | 100% |
| due_date | next Friday | "due next Friday" | 100% |

## Human Review Required

**NO** - All extractions high confidence (≥80%)

---

## Approval Actions

- [ ] Approve (send reply manually via WhatsApp)
- [ ] Reject (add your reason below)
- [ ] Edit (add your changes/notes below)
```

---

### Step 5: Review the AI Extraction

Check the **Extracted Information** table:

✅ **All fields extracted correctly:**
- Invoice number: 12345 (from "invoice #12345")
- Amount: $500 (from "$500")
- Customer: ABC Corp (from "to ABC Corp")
- Due date: next Friday (from "due next Friday")

✅ **Source citations present** for every field

✅ **Confidence scores** all 100%

✅ **No hallucination** - AI only extracted what was in the message

---

### Step 6: Check the Audit Log

Open the log file:

```bash
type Logs\*.json
```

**Expected:** AI decision logged with full details:
```json
{
  "timestamp": "2026-02-27T10:30:00",
  "log_type": "ai_decision",
  "draft_id": "whatsapp_Draft_2026-02-27_10-30-00.md",
  "action_type": "whatsapp",
  "input_summary": {
    "source_file": "WHATSAPP_test_001.md",
    "content_preview": "Hi, please send invoice #12345..."
  },
  "ai_output_summary": {
    "extracted_fields_count": 6,
    "average_confidence": 95.0,
    "requires_human_review": false
  },
  ...
}
```

---

## 🧪 Test 2: Incomplete Information (Hallucination Prevention)

Now test that AI **doesn't hallucinate** when info is missing.

### Create Test File with Missing Info

**File:** `AI_Employee_Vault/Needs_Action/EMAIL_test_002.md`

```markdown
---
type: email
---

# Message

Send email about the meeting
```

### Run Orchestrator Again

```bash
python src/orchestrator.py
```

### Check the Draft

```bash
type Pending_Approval\email_Draft_*.md
```

**Expected:**
```markdown
---
requires_human_review: true
ai_confidence_average: 25.0
---

## Extracted Information

| Field | Value | Source Text | Confidence |
|-------|-------|-------------|------------|
| to | UNKNOWN | Not mentioned | 0% |
| subject | UNKNOWN | Not mentioned | 0% |

## Human Review Required

**YES** - to: Not mentioned (0%); subject: Not mentioned (0%)

**Action:** Human must provide recipient email and meeting details
```

✅ **AI correctly marked missing fields as UNKNOWN**  
✅ **AI flagged for human review**  
✅ **No hallucination - didn't invent email address or subject!**

---

## 🧪 Test 3: Email Draft Generation

### Create Test File

**File:** `AI_Employee_Vault/Needs_Action/EMAIL_test_003.md`

```markdown
---
type: email
---

Send email to john@example.com with subject "Project Update" and body "The project is on track, will deliver by Friday"
```

### Run Orchestrator

```bash
python src/orchestrator.py
```

### Check Draft

```bash
type Pending_Approval\email_Draft_*.md
```

**Expected:** Complete email draft with:
- ✅ To: john@example.com
- ✅ Subject: Project Update
- ✅ Professional email body
- ✅ All fields extracted with citations

---

## 📊 Test Results Checklist

After running all tests, verify:

### AI Functionality
- [ ] Groq API working (no errors)
- [ ] AI extracts information correctly
- [ ] Source citations present for all fields
- [ ] Confidence scores calculated
- [ ] Missing info marked as UNKNOWN

### Anti-Hallucination
- [ ] AI doesn't invent missing information
- [ ] Low confidence triggers human review
- [ ] All extractions traceable to source text

### System Integration
- [ ] Orchestrator detects files in Needs_Action/
- [ ] Drafts created in Pending_Approval/
- [ ] Audit logs created in Logs/
- [ ] Files moved to Processed/ after handling

---

## 🎯 Quick Test Command

Run all tests at once:

```bash
# 1. Test AI agent
python test_ai_agent.py

# 2. Create test input
echo ---^>type: whatsapp^>---^>^>^># Message^>^>Hi, please send invoice #12345 for $500^> > AI_Employee_Vault\Needs_Action\test.md

# 3. Run orchestrator
python src/orchestrator.py

# 4. Check draft
dir Pending_Approval
```

---

## ❓ Troubleshooting

### "No AI model available"
**Fix:** Check `.env` has Groq API key:
```bash
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

### "Draft not created"
**Check:**
1. File in correct folder: `AI_Employee_Vault/Needs_Action/`
2. File has correct format (markdown with frontmatter)
3. Orchestrator running without errors

### "AI returned wrong extraction"
**Check:**
1. Input message is clear
2. Groq API key is valid
3. Review AI output in Logs/*.json

---

## ✅ Success Criteria

Your system is working correctly if:

1. ✅ AI extracts facts from messages
2. ✅ Every extraction has source citation
3. ✅ Missing info marked as UNKNOWN
4. ✅ Low confidence triggers human review
5. ✅ Drafts created in Pending_Approval/
6. ✅ Full audit trail in Logs/

---

## 🎉 Next Steps

Once tests pass:

1. **Test with real data:** Use actual WhatsApp/Email messages
2. **Customize prompts:** Edit system prompts in `src/ai_agent.py`
3. **Add more actions:** LinkedIn, Facebook, etc.
4. **Deploy to production:** Set up cloud infrastructure

---

**Your AI agent is fully operational!** 🚀

---

*Last Updated: 2026-02-27*
