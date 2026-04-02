# Gmail Watcher - Complete Setup Guide

## ✅ What You Need

1. **Google Account** with Gmail enabled
2. **15-20 minutes** for initial setup
3. **credentials.json** from Google Cloud Console

---

## 📋 Step-by-Step Setup

### **Step 1: Create Google Cloud Project** (5 min)

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com
   ```

2. **Create New Project:**
   - Click "Select Project" (top bar)
   - Click "New Project"
   - Name: `AI Employee Vault`
   - Click "Create"
   - Wait for project to be created

3. **Enable Gmail API:**
   - Click "APIs & Services" → "Library" (left sidebar)
   - Search for: `Gmail API`
   - Click on "Gmail API"
   - Click "Enable" button
   - Wait for it to enable

---

### **Step 2: Create OAuth Credentials** (5 min)

1. **Go to Credentials:**
   - Click "APIs & Services" → "Credentials"
   - Click "Create Credentials" (top)
   - Select "OAuth client ID"

2. **Configure OAuth Consent Screen** (if prompted):
   - User type: "External"
   - App name: `AI Employee Vault`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip (click "Save and Continue")
   - Test users: Add your Google account email
   - Click "Save and Continue"

3. **Create OAuth Client:**
   - Application type: **Desktop app**
   - Name: `AI Employee Vault`
   - Click "Create"

4. **Download Credentials:**
   - Click "Download JSON"
   - Save file as: `credentials.json`
   - **IMPORTANT:** Move to project folder:
     ```
     D:\AI\Hackathon-0\credentials.json
     ```

---

### **Step 3: Run OAuth Setup Script** (2 min)

1. **Open Terminal in Project:**
   ```bash
   cd D:\AI\Hackathon-0
   ```

2. **Run Setup Script:**
   ```bash
   python scripts\setup_gmail_oauth.py
   ```

3. **Follow Prompts:**
   - Browser opens automatically
   - Login to your Google account
   - Grant Gmail permissions
   - Browser closes automatically

4. **Verify Success:**
   ```
   ✅ GMAIL OAUTH SETUP COMPLETE!
   Token saved to: D:\AI\Hackathon-0\token.json
   ```

---

### **Step 4: Start Gmail Watcher** (1 min)

1. **Open Dashboard:**
   ```
   http://localhost:3000
   ```

2. **Go to Watchers:**
   - Click "Watchers" in sidebar
   - Find Gmail card

3. **Start Gmail Watcher:**
   - Click "Start" on Gmail card
   - Should start without errors!

4. **Verify It Works:**
   - Check terminal logs
   - Should see: `Gmail service authenticated`
   - Should NOT see auth errors

---

## 🧪 Test It

### **Send Test Email:**

1. **From different email account:**
   - Send email to your Gmail
   - Subject: `Test from AI Employee`
   - Body: `This is a test message`

2. **Wait 60 seconds:**
   - Gmail watcher checks every 60 seconds
   - Should detect unread email

3. **Check Logs:**
   ```
   ✓ Found 1 unread message(s)!
   ✓ Created action file: gmail_20260403_*.md
   ```

4. **Check Dashboard:**
   - Go to "Pending Tasks" or "To Review"
   - Should see email task

---

## 🐛 Troubleshooting

### **"credentials.json not found"**

**Fix:**
```
1. Download from Google Cloud Console
2. Save as: D:\AI\Hackathon-0\credentials.json
3. Run setup script again
```

---

### **"OAuth consent screen not configured"**

**Fix:**
```
1. Go to: APIs & Services → OAuth consent screen
2. Fill in required fields
3. Add your email as test user
4. Click "Save and Continue" through all steps
5. Run setup script again
```

---

### **"Gmail API not enabled"**

**Fix:**
```
1. Go to: APIs & Services → Library
2. Search: Gmail API
3. Click "Enable"
4. Run setup script again
```

---

### **"Token expired" or "Invalid token"**

**Fix:**
```bash
# Delete old token
del token.json

# Run setup again
python scripts\setup_gmail_oauth.py
```

---

### **"Gmail watcher still shows auth error"**

**Check:**
```bash
# Verify token.json exists
dir token.json

# Check credentials.json is valid
type credentials.json
```

**If files exist:**
```bash
# Delete and recreate token
del token.json
python scripts\setup_gmail_oauth.py
```

---

## 📝 File Locations

| File | Purpose | Location |
|------|---------|----------|
| **credentials.json** | OAuth client credentials | Project root |
| **token.json** | Your access token | Project root |
| **.processed_emails.txt** | Processed email cache | data/AI_Employee_Vault/ |

---

## 🎯 Expected Flow

```
1. Gmail watcher starts
   ↓
2. Loads token.json
   ↓
3. Authenticates with Google
   ↓
4. Checks for unread emails
   ↓
5. Finds unread emails
   ↓
6. Creates action files
   ↓
7. AI processes emails
   ↓
8. Tasks appear in dashboard
```

---

## 🏆 Success Indicators

**Setup Complete:**
- ✅ credentials.json exists
- ✅ token.json exists
- ✅ No auth errors in logs

**Watcher Working:**
- ✅ `Gmail service authenticated` in logs
- ✅ Checks every 60 seconds
- ✅ Creates files for new emails
- ✅ No repeated auth errors

---

## 🎉 Quick Start Summary

```bash
# 1. Get credentials.json from Google Cloud
# 2. Run OAuth setup
python scripts\setup_gmail_oauth.py

# 3. Start dashboard
python dashboard_server.py

# 4. Start Gmail watcher from dashboard
# (Click "Start" on Gmail card)

# 5. Send test email and verify it works!
```

---

**Status:** ✅ Ready to setup
**Time Required:** 15-20 minutes (one-time)
**Support:** Check troubleshooting section if issues
