# 🚀 AI Employee Vault - Unified Startup Guide

## ✅ **SYSTEM IS NOW UNIFIED!**

Everything starts from the dashboard. Watchers start only when you click their Start buttons.

---

## 🎯 **HOW TO START - SIMPLE**

### **Option 1: Double-Click (Easiest)**

1. **Double-click:** `START.bat`
2. **Wait 10 seconds**
3. **Open browser:** http://localhost:3000
4. **Done!**

### **Option 2: Command Line**

```bash
cd D:\AI\Hackathon-0
python dashboard_server.py
```

**Then open:** http://localhost:3000

---

## 📋 **WHAT STARTS AUTOMATICALLY**

When you start the dashboard:

| Component | Starts When | Purpose |
|-----------|-------------|---------|
| **Dashboard Server** | Immediately | Web interface |
| **AI Processor** | Automatically | Processes all tasks, moves files to Pending_Approval/To_Review |

**You DON'T need to start these manually!**

---

## ▶️ **WHAT STARTS MANUALLY (Click to Start)**

These only start when YOU click their Start buttons in the dashboard:

| Watcher | How to Start | What It Does |
|---------|--------------|--------------|
| **WhatsApp Watcher** | Click "▶ Start" on WhatsApp card | Monitors WhatsApp for new unread messages |
| **Gmail Watcher** | Click "▶ Start" on Gmail card | Monitors Gmail for new emails |
| **LinkedIn Watcher** | Click "▶ Start" on LinkedIn card | Monitors LinkedIn for notifications |

**To Stop:** Click "⏹ Stop" on any watcher card

---

## 🎮 **DASHBOARD CONTROLS**

### **Status Cards:**

1. **🧠 AI Agent** - Shows AI status (always running)
2. **📧 Gmail Watcher** - Start/Stop button
3. **📱 WhatsApp Watcher** - Start/Stop button
4. **💼 LinkedIn Watcher** - Start/Stop button
5. **⏳ Pending Tasks** - Shows count of tasks awaiting approval
6. **✅ Processed Today** - Shows count of completed tasks

### **Main Sections:**

1. **Create New Task** - Type message or drop files
2. **Quick Post** - Create LinkedIn posts
3. **Pending Approval** - Tasks waiting for your approval
4. **To Review** - Informational items (no action needed)

---

## 🔄 **COMPLETE WORKFLOW**

### **Manual Task Creation:**

1. Type message in dashboard input
2. Click "Analyze & Create Task"
3. AI analyzes and creates task
4. Task appears in Pending Approval or To Review
5. Click "Approve" to execute (or "Reject")

### **Automatic Monitoring (Watchers):**

1. Click "▶ Start" on watcher (WhatsApp/Gmail/LinkedIn)
2. Watcher monitors for new messages
3. New messages auto-create tasks
4. Tasks appear in Pending Approval or To Review
5. Review and approve/reject

### **AI Processing:**

- **Starts automatically** with dashboard
- **Processes all tasks** from:
  - Dashboard input
  - WhatsApp Watcher
  - Gmail Watcher
  - LinkedIn Watcher
  - Drop folder files
- **Categorizes** as Actionable → Pending_Approval or Informational → To_Review

---

## 🛑 **HOW TO STOP**

### **Stop Everything:**

**Close the "AI Employee Vault Dashboard" window** (Ctrl+C in terminal)

This stops:
- Dashboard Server
- AI Processor
- All running watchers

### **Stop Individual Watchers:**

Click "⏹ Stop" on any watcher card

---

## 📁 **FOLDER STRUCTURE**

```
data/AI_Employee_Vault/
├── Needs_Action/       # Temporary (tasks being processed)
├── Pending_Approval/   # Tasks waiting for your approval
├── To_Review/          # Informational items (read only)
├── Done/               # Completed tasks
└── Archived/           # Old archived items
```

---

## ✅ **TESTING THE SYSTEM**

### **Test 1: Manual Task**

1. Open dashboard: http://localhost:3000
2. Type: `"Test message"`
3. Click "Analyze & Create Task"
4. Wait 30 seconds
5. Check "Pending Approval" or "To Review" - task should appear

### **Test 2: WhatsApp Watcher**

1. Click "▶ Start" on WhatsApp Watcher
2. Send WhatsApp message to your number
3. Wait 60 seconds
4. Check "Pending Approval" or "To Review" - message should appear

### **Test 3: Approval**

1. Find task in "Pending Approval"
2. Click "✓ Approve"
3. Action executes (WhatsApp sends, email sends, etc.)
4. Task moves to "Done"

---

## 🔧 **TROUBLESHOOTING**

### **Dashboard won't start:**

```bash
# Check if port 3000 is in use
netstat -ano | findstr :3000

# If in use, kill the process or use different port
```

### **Watcher won't start:**

- Check credentials in `.env` file
- Check watcher logs in terminal window
- Restart dashboard

### **Tasks not appearing:**

- Wait 60 seconds (processor runs every 60s)
- Check AI is available (check status card)
- Check Groq API key in `.env`

### **Approval fails:**

- Check task has all required info
- Check WhatsApp/Gmail/LinkedIn credentials
- Check error message in dashboard

---

## 📝 **QUICK REFERENCE**

### **Start Commands:**

```bash
# Everything (recommended)
START.bat

# Or manually
python dashboard_server.py
```

### **URLs:**

- **Dashboard:** http://localhost:3000
- **Odoo (if using):** http://localhost:8069

### **Key Files:**

- `.env` - Your credentials (API keys, passwords)
- `dashboard_server.py` - Main server
- `src/watcher_processor.py` - AI processor (auto-starts)
- `watchers/whatsapp_watcher.py` - WhatsApp monitor
- `watchers/gmail_watcher.py` - Gmail monitor

---

## 🎯 **SUMMARY**

**Before (Broken):**
- ❌ Multiple terminals needed
- ❌ Processor had to be started manually
- ❌ Confusing startup process
- ❌ Things kept crashing

**Now (Unified):**
- ✅ One command starts everything
- ✅ Processor auto-starts with dashboard
- ✅ Watchers start only when you click
- ✅ Everything controlled from dashboard
- ✅ Clean, simple, reliable

---

**Ready to use! Just run `START.bat` and go!** 🚀
