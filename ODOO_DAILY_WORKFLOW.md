# 📅 Odoo Daily Workflow

## ⚡ Quick Start (Every Day)

### **Option A: Fully Automated (Recommended)**

1. **Run the auto-start configuration script (ONE TIME):**
   ```
   Double-click: scripts\configure_docker_autostart.bat
   ```
   This makes Docker Desktop start automatically when you log in.

2. **Every morning, just run:**
   ```
   Double-click: START.bat
   ```
   
   This automatically:
   - ✅ Starts Docker Desktop (if not running)
   - ✅ Waits for Docker to be ready (~60 seconds)
   - ✅ Starts Odoo containers
   - ✅ Starts Dashboard + AI Processor

3. **Open Dashboard**
   - Browser: http://localhost:3000

---

### **Option B: Manual Start (If you didn't configure auto-start)**

1. **Start Docker Desktop**
   - Windows Key → Type "Docker Desktop" → Open
   - Wait for whale icon 🐳 to turn **green** (~30 seconds)

2. **Run START.bat**
   ```
   Double-click: START.bat
   ```
   
   This automatically:
   - ✅ Checks Docker is running
   - ✅ Starts Odoo containers
   - ✅ Starts Dashboard + AI Processor

3. **Open Dashboard**
   - Browser: http://localhost:3000

---

## 🔄 What Happens When You Create an Invoice Task

```
You type in dashboard:
  "Create invoice for ABC Corp, $5000 for consulting services"
       ↓
AI analyzes → Creates task in Pending_Approval/
       ↓
You click "✓ Approve"
       ↓
Dashboard calls Odoo API (http://localhost:8069)
       ↓
Odoo creates invoice automatically
       ↓
Success message + Invoice number shown
```

---

## ⚠️ If Docker Is NOT Running

When you approve an invoice, you'll see:

```
❌ ERROR: Cannot connect to Odoo at http://localhost:8069
```

**Fix:** Start Docker Desktop → Run `docker compose up -d` → Try again

---

## 🛑 Evening Shutdown

**Option 1: Stop Everything**
- Close "AI Employee Vault Dashboard" window
- Docker containers keep running (that's OK)

**Option 2: Stop Odoo Too**
```bash
docker compose stop
```

**Option 3: Leave Everything Running**
- Just close dashboard
- Odoo keeps running (uses ~200MB RAM)
- Next morning: Just start dashboard

---

## 📋 Daily Checklist

| Time | Action | Required? |
|------|--------|-----------|
| Morning | Run `START.bat` | ✅ Yes |
| During day | Create/approve tasks | As needed |
| Evening | Close dashboard | ✅ Yes |
| Evening | Stop Docker | ❌ Optional (leave running) |

**Note:** If you didn't run the auto-start script, you'll need to start Docker Desktop manually each morning.

---

## 🔧 Useful Commands

```bash
# Check if Odoo is running
docker ps

# Start Odoo
docker compose up -d

# Stop Odoo
docker compose stop

# Restart Odoo
docker compose restart

# View Odoo logs
docker compose logs odoo

# Stop and remove everything (reset)
docker compose down -v
```

---

## 🎯 Summary

| Component | Starts When | Frequency |
|-----------|-------------|-----------|
| Docker Desktop | Windows login (if auto-start configured) | Once per day |
| Odoo Containers | START.bat (auto) | Once per day |
| Dashboard | START.bat (auto) | Once per day |
| AI Processor | Dashboard starts it | Once per day |
| Watchers | You click "Start" | As needed |

---

## 💡 Pro Tips

1. **Run auto-start script** - Execute `scripts\configure_docker_autostart.bat` once to auto-start Docker
2. **Leave Docker running** - If you use Odoo frequently, leave Docker running all day (uses ~200MB RAM)
3. **START.bat is smart** - It will wait for Docker to start before launching Odoo

---

**That's it!** Just run `START.bat` - it handles everything! 🚀
