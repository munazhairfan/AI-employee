# Security & Privacy Guide

## ⚠️ CRITICAL: Before Pushing to GitHub

This project contains sensitive data that should **NEVER** be committed to version control.

---

## Files You Must NOT Commit

### 1. Authentication Files (CRITICAL)
| File | Contains | Risk |
|------|----------|------|
| `.env` | Email password, Odoo credentials | **HIGH** - Account compromise |
| `credentials.json` | Google OAuth client secret | **HIGH** - API abuse |
| `token.json` | Gmail access tokens | **HIGH** - Email access |

### 2. Session Data (CRITICAL)
| Folder | Contains | Risk |
|--------|----------|------|
| `whatsapp_session/` | WhatsApp Web login cookies | **HIGH** - WhatsApp access |

### 3. Business Data (HIGH)
| Folder | Contains | Risk |
|--------|----------|------|
| `AI_Employee_Vault/` | Invoices, emails, business docs | **HIGH** - Confidential data |
| `Logs/` | Action logs, error traces | **MEDIUM** - Business intelligence |

### 4. Database Files
| Folder | Contains | Risk |
|--------|----------|------|
| `postgres_data/` | Database files | **MEDIUM** - Data exposure |
| `odoo_data/` | Odoo ERP data | **MEDIUM** - Business data |

---

## Cleanup Steps (Do This First)

### Step 1: Remove Sensitive Files from Git Cache
```bash
# Untrack sensitive files (they'll remain on disk but won't be committed)
git rm --cached .env
git rm --cached credentials.json
git rm --cached token.json
git rm --cached -r whatsapp_session/
git rm --cached -r AI_Employee_Vault/
git rm --cached -r Logs/
```

### Step 2: Verify What Will Be Committed
```bash
# See what files Git will track
git status

# Preview what would be committed
git ls-files --stage
```

### Step 3: Create Clean Commit
```bash
git add .
git commit -m "Initial commit - AI Employee Vault (sanitized)"
```

---

## Setup Instructions for New Users

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Hackathon-0
```

### 2. Create Your .env File
```bash
# Copy the template
copy .env.example .env

# Edit .env with your actual credentials
```

### 3. Get Gmail Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Place in project root (DO NOT COMMIT)

### 4. Get Gmail App Password
1. Go to [Google Account](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Generate password for "Mail"
4. Add to `.env` as `EMAIL_PASS`

### 5. Install Dependencies
```bash
# Python
pip install -r requirements.txt
playwright install chromium

# Node.js
npm install
```

### 6. Run Gmail Setup (First Time Only)
```bash
python src/setup_auth.py
# This creates token.json (DO NOT COMMIT)
```

---

## Git Configuration

### Recommended Global Settings
```bash
# Never commit .env files
git config --global core.excludesfile ~/.gitignore_global
```

### Add to Global .gitignore (~/.gitignore_global)
```
# Secrets
.env
*.pem
*.key
credentials.json
token.json

# Sessions
whatsapp_session/

# Logs
*.log
Logs/
```

---

## If You Accidentally Committed Secrets

### 1. If Just Pushed (No One Else Cloned)
```bash
# Remove from last commit
git reset --soft HEAD~1
git reset HEAD .env credentials.json token.json
git commit -m "Your commit message"

# Force push (WARNING: only if solo project)
git push --force
```

### 2. If Public for a While
```bash
# Use BFG Repo-Cleaner (recommended)
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

java -jar bfg.jar --delete-files .env
java -jar bfg.jar --delete-files credentials.json
java -jar bfg.jar --delete-files token.json

# Then force push
git push --force
```

### 3. Rotate Compromised Credentials IMMEDIATELY
- **Gmail**: Change password, revoke app passwords
- **OAuth**: Delete and recreate credentials in Google Cloud Console
- **Odoo**: Change admin password

---

## Security Best Practices

### 1. Use Environment Variables
```python
# Good
from dotenv import load_dotenv
load_dotenv()
email = os.getenv('EMAIL_USER')

# Bad - NEVER DO THIS
email = "your-email@gmail.com"  # Never hardcode credentials!
```

### 2. Use .env.example Pattern
- Commit `.env.example` with placeholder values
- Never commit `.env` with real values

### 3. Regular Audits
```bash
# Search for accidentally committed secrets
git log -p --all | grep -i "password\|secret\|token"

# Check for large files
git ls-files -s | sort -rn | head -20
```

### 4. Use Secret Scanning
- Enable GitHub Secret Scanning on your repository
- Consider tools like `git-secrets` or `truffleHog`

---

## Quick Checklist Before Pushing

- [ ] `.env` file is in `.gitignore`
- [ ] `credentials.json` is in `.gitignore`
- [ ] `token.json` is in `.gitignore`
- [ ] `whatsapp_session/` is in `.gitignore`
- [ ] `AI_Employee_Vault/` is in `.gitignore`
- [ ] `Logs/` is in `.gitignore`
- [ ] No hardcoded passwords in code
- [ ] No hardcoded email addresses in code
- [ ] `.env.example` exists with placeholder values
- [ ] `git status` shows no sensitive files

---

## Emergency Contacts

If you accidentally expose credentials:

1. **Gmail/Google**: https://myaccount.google.com/permissions
2. **Revoke Access**: https://myaccount.google.com/apppasswords
3. **Change Password**: https://myaccount.google.com/security

---

*Last Updated: 2026-02-21*
*Version: 1.0*
