# Gmail Watcher Setup Guide

## What You Need

1. **Google Cloud Project** with Gmail API enabled
2. **credentials.json** - OAuth credentials from Google
3. **token.json** - Your access token (created by setup script)

---

## Step-by-Step Setup

### Step 1: Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 2: Get Google Cloud Credentials

1. Go to **Google Cloud Console**: https://console.cloud.google.com/

2. **Create a new project** (or select existing):
   - Click project dropdown at top
   - Click "NEW PROJECT"
   - Name it (e.g., "Email Watcher")
   - Click "CREATE"

3. **Enable Gmail API**:
   - Search "Gmail API" in top search bar
   - Click "Gmail API"
   - Click "ENABLE"

4. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials" (left menu)
   - Click "+ CREATE CREDENTIALS" > "OAuth client ID"
   - If prompted, configure "OAuth consent screen":
     - User Type: "External"
     - App name: "Email Watcher"
     - User support email: your email
     - Developer contact: your email
     - Click "SAVE AND CONTINUE"
     - Skip scopes (click "SAVE AND CONTINUE")
     - Skip test users (click "SAVE AND CONTINUE")
   - Back to "Create OAuth client ID":
     - Application type: **Desktop app**
     - Name: "Email Watcher Desktop"
     - Click "CREATE"

5. **Download credentials.json**:
   - Click "DOWNLOAD JSON"
   - Save as `credentials.json` in `D:\AI\Hackathon-0\`

### Step 3: Run Authentication

```bash
cd D:\AI\Hackathon-0
python setup_auth.py
```

**What happens:**
- A browser window opens
- Sign in with your Google account
- Click "Allow" to grant Gmail read access
- Browser shows "Authentication successful"
- `token.json` is created in the project folder

### Step 4: Run Gmail Watcher

```bash
python gmail_watcher.py
```

---

## Troubleshooting

### "credentials.json not found"
- Make sure file is in `D:\AI\Hackathon-0\credentials.json`
- File must be named exactly `credentials.json` (not `.json.txt`)

### "Token expired" or "Invalid credentials"
- Delete `token.json`
- Run `python setup_auth.py` again

### "Gmail API not enabled"
- Go to Google Cloud Console
- Search "Gmail API"
- Click "ENABLE"

### Browser doesn't open
- Copy the URL shown in terminal
- Paste in browser manually
- Complete authentication
- Copy the success code if shown

---

## What Gets Created

```
D:\AI\Hackathon-0\
├── credentials.json    (you download from Google)
├── token.json          (created by setup_auth.py)
├── gmail_watcher.py    (the watcher script)
└── setup_auth.py       (authentication script)
```

## How It Works

1. **gmail_watcher.py** checks your Gmail every 60 seconds
2. Finds **unread, important** emails
3. Creates `EMAIL_{id}.md` files in `AI_Employee_Vault/Needs_Action/`
4. Orchestrator processes them (same as file drops)
5. Updates `Dashboard.md`
6. Moves to `Done/`

---

## Security Notes

- `token.json` = your access key, **keep it private**
- `credentials.json` = app config, **keep it private**
- Never commit these files to Git
- Token expires after 1 hour, but auto-refreshes
- Script only has **read** access to Gmail
