# Quick Start - Reorganized Project

## 🚀 Start Everything

### Option 1: Start All (Recommended)

```bash
# Run these in 3 separate terminals:

# Terminal 1: Dashboard
python dashboard_server.py

# Terminal 2: Watcher Processor (checks every 30 sec)
python src/watcher_processor.py

# Terminal 3: Gmail Watcher (checks every 60 sec)
python watchers/gmail_watcher.py
```

### Option 2: Use Batch Files

```bash
# Dashboard
start_dashboard.bat

# Watcher Processor
start_watcher_processor.bat

# Gmail Watcher
start_gmail_watcher.bat
```

---

## 📁 New Folder Structure

**All data is now in `/data/` folder:**

```
data/
├── AI_Employee_Vault/
│   ├── Needs_Action/      # Actionable tasks
│   ├── Pending_Approval/  # Awaiting approval
│   ├── To_Review/         # Informational (read & mark done)
│   ├── Done/              # Completed
│   └── Rejected/          # Rejected
├── drop_folder/           # Drop files here
├── watcher_output/        # Watcher output (temporary)
└── whatsapp_session/      # WhatsApp session
```

**Tests are in `/tests/`:**
```bash
# Run tests
cd tests
python test_ai_agent.py
```

---

## 🧪 Test It

**1. Send yourself an email**

**2. Wait 90 seconds**

**3. Check folders:**
```bash
# Actionable tasks (approve → execute)
dir data\AI_Employee_Vault\Pending_Approval\

# Informational tasks (read → mark done)
dir data\AI_Employee_Vault\To_Review\
```

**4. Open dashboard:**
```
http://localhost:3000
```

---

## 💾 Backup Your Data

**Important! Backup regularly:**

```bash
xcopy /E /I data D:\Backup\AI_Employee_Vault_Data\
```

**The `/data/` folder is excluded from Git** for privacy and security.

---

## 🎯 What Changed

- ✅ All data in `/data/` folder
- ✅ Tests moved to `/tests/`
- ✅ Clean root directory
- ✅ `.gitignore` updated
- ✅ All paths updated in code

---

**Project is now clean, organized, and professional!** 🎉
