# Email (Gmail) Watcher - Complete Summary

**Date:** 2026-03-03  
**Status:** ✅ Working  
**Location:** `watchers/gmail_watcher.py`

---

## 📋 Overview

The Gmail Watcher **automatically monitors your Gmail inbox** for new emails and creates task files for AI processing.

---

## 🔄 How It Works

### Complete Flow:

```
1. Gmail Watcher runs every 60 seconds
        ↓
2. Connects to Gmail API (OAuth2 authenticated)
        ↓
3. Fetches unread emails from INBOX
        ↓
4. Skips already processed emails (by ID)
        ↓
5. For each new email:
   - Extracts: From, Subject, Date, Priority
   - Downloads full email body
   - Cleans content (removes tracking, footers)
        ↓
6. Creates task file in: data/watcher_output/gmail_TIMESTAMP_ID.md
        ↓
7. Saves email ID to processed list (prevents duplicates)
        ↓
8. AI Processor picks up the file
        ↓
9. AI analyzes and creates task in Needs_Action/
        ↓
10. Task appears in Dashboard for approval
```

---

## 📁 File Structure

### Input:
- **Gmail Inbox** (unread emails only)

### Output:
```
data/
├── watcher_output/
│   └── gmail_2026-03-03_10-30-00_abc123.md  ← Created for each new email
├── AI_Employee_Vault/
│   └── .processed_emails.txt  ← Cache of processed email IDs
```

### Task File Format:
```markdown
---
type: email
source: gmail
from: sender@example.com
subject: Invoice Request
received: 2026-03-03T10:30:00
priority: normal
---

# Message Content

Hi, I need an invoice for the consulting work we did last month.
The amount is $1500. Please send it to accounts@company.com.

Thanks,
John from ABC Corp
```

---

## 🔧 Configuration

### Constructor:
```python
GmailWatcher(
    vault_path='AI_Employee_Vault',      # Where to store data
    credentials_path='credentials.json', # OAuth credentials
    check_interval=60                    # Check every 60 seconds
)
```

### Files Needed:
1. **`credentials.json`** - Gmail API OAuth credentials (download from Google Cloud Console)
2. **`token.json`** - Auto-created on first run (stores refresh token)
3. **`.processed_emails.txt`** - Auto-created cache of processed email IDs

---

## 🔐 Authentication

### OAuth2 Flow:
1. **First run:** Opens browser for Gmail authorization
2. **User grants permission** to read emails
3. **`token.json` created** with refresh token
4. **Future runs:** Auto-refresh token (no browser needed)

### Scopes:
```python
['https://www.googleapis.com/auth/gmail.readonly']
```
**Only reads emails** - cannot send or modify

---

## 📧 Email Processing

### What Gets Processed:
- ✅ **All unread emails** in INBOX
- ✅ **Maximum 10 emails** per check (prevents overload)
- ✅ **Skips processed emails** (by Gmail message ID)

### Email Data Extracted:
```python
{
    'id': 'gmail_message_id',          # Unique Gmail ID
    'from': 'sender@example.com',       # Sender address
    'subject': 'Email Subject',         # Subject line
    'received': '2026-03-03T10:30:00',  # ISO timestamp
    'priority': 'normal',               # normal/high
    'snippet': 'Email preview text'
}
```

### Body Cleaning:
The `_clean_email_body()` method removes:
- ❌ LinkedIn tracking URLs (`trackingId=`, `trk=`, `lipi=`)
- ❌ Email footers (© LinkedIn, unsubscribe links)
- ❌ Very long URLs (>300 chars)
- ✅ **Keeps:** Job titles, company names, meaningful content

---

## 🔄 Integration with AI Processor

### Watcher Output → AI Processor:

1. **Watcher creates:** `data/watcher_output/gmail_TIMESTAMP_ID.md`
2. **AI Processor monitors:** `data/watcher_output/` folder
3. **AI reads** the email file
4. **AI analyzes** content and intent
5. **AI creates task** in `AI_Employee_Vault/Needs_Action/`
6. **Task appears** in Dashboard

### Example AI Analysis:
**Input (from Gmail):**
```
From: john@abccorp.com
Subject: Invoice Request
Body: Hi, I need an invoice for $1500...
```

**AI Output (task file):**
```markdown
---
type: email_send
customer_email: accounts@company.com
---

**Intent:** Send email to accounts@company.com with content 'Invoice for $1500'
```

---

## 🛠️ Running the Watcher

### Standalone:
```bash
cd D:\AI\Hackathon-0
python watchers/gmail_watcher.py
```

### Output:
```
2026-03-03 10:30:00 - INFO - Gmail service authenticated
2026-03-03 10:30:05 - INFO - Created action file: gmail_2026-03-03_10-30-05_abc123.md
```

### With Dashboard:
The watcher runs automatically when you start the dashboard system.

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Check Interval** | 60 seconds |
| **Max Emails/Check** | 10 |
| **Processing Time** | ~2-5 seconds per email |
| **Duplicate Prevention** | Gmail message ID cache |

---

## 🔍 Debugging

### Check if Running:
```bash
# Look for recent files in watcher_output
dir data\watcher_output\gmail_*.md /OD
```

### Check Processed Emails:
```bash
# View cache of processed email IDs
type data\AI_Employee_Vault\.processed_emails.txt
```

### Test Authentication:
```bash
python -c "
from watchers.gmail_watcher import GmailWatcher
watcher = GmailWatcher()
watcher._authenticate()
print('Authentication successful!')
"
```

---

## ⚠️ Common Issues

### Issue 1: "No valid credentials"
**Solution:**
1. Download `credentials.json` from Google Cloud Console
2. Run watcher - it will create `token.json` automatically
3. Grant permission in browser

### Issue 2: "No emails processed"
**Solution:**
1. Check if emails are unread
2. Check `.processed_emails.txt` - emails might already be processed
3. Delete `.processed_emails.txt` to reprocess all emails

### Issue 3: "Authentication failed"
**Solution:**
1. Delete `token.json`
2. Run watcher again
3. Re-authorize in browser

---

## 📝 Key Methods

| Method | Purpose |
|--------|---------|
| `_authenticate()` | OAuth2 authentication with Gmail |
| `check_for_updates()` | Fetch unread emails from Gmail API |
| `create_action_file()` | Create task file for AI processing |
| `_clean_email_body()` | Remove tracking/footers from email |
| `_save_processed_id()` | Save email ID to prevent reprocessing |

---

## 🎯 Summary

**Gmail Watcher:**
- ✅ **Monitors** Gmail inbox every 60 seconds
- ✅ **Fetches** unread emails via Gmail API
- ✅ **Extracts** sender, subject, body, priority
- ✅ **Cleans** content (removes tracking)
- ✅ **Creates** task files for AI processing
- ✅ **Prevents** duplicates (by email ID)
- ✅ **Integrates** with AI Processor → Dashboard

**Result:** Every new email automatically becomes an AI task! 📧✨

---

*Last Updated: 2026-03-03*
