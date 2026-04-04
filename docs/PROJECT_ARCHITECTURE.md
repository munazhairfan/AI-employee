# AI Employee Vault - Complete Architecture & Data Flow

## 📂 1. Project Structure

```
D:\AI\Hackathon-0\
├── 📄 START.bat                  # 🔑 Unified launcher (Docker + Dashboard + AI)
├── 📂 docs/                      # 📚 Documentation & Setup Guides
├── 📂 scripts/                   # 🛠️ Utilities (OAuth setup, Reset, Testers)
├── 📂 data/                      # 💾 Storage (The "Vault")
│   ├── AI_Employee_Vault/        #   Main task storage
│   │   ├── Pending_Approval/     #   → Awaiting user review
│   │   ├── To_Review/            #   → Informational items
│   │   ├── Done/                 #   → Completed tasks
│   │   └── Rejected/             #   → Rejected tasks
│   ├── watcher_output/           #   → Raw data from WhatsApp/Gmail (Left here if failed)
│   └── drop_folder/              #   → Files dropped via Dashboard UI
├── 📂 public/                    # 🌐 Web Interface
│   └── dashboard.html            #   Main UI (Tasks, Watchers, Drop Zone)
├── 📂 src/                       # 🧠 Core Logic
│   ├── dashboard_server.py       #   🔌 HTTP Server & API
│   ├── intent_analyzer.py        #   🤖 AI Classifier (Groq/Llama)
│   ├── watcher_processor.py      #   ⚙️ Background AI Worker
│   ├── whatsapp_integration.py   #   📱 WhatsApp Sender (By Name/Phone)
│   ├── odoo_integration.py       #   📄 Odoo Invoice Creator
│   └── linkedin_integration.py   #   💼 LinkedIn Poster
└── 📂 watchers/                  # 👁️ Monitoring Agents
    ├── whatsapp_watcher.py       #   Monitors WhatsApp Web
    └── gmail_watcher.py          #   Monitors Gmail API
```

---

## 🏗️ 2. Working Model

The system uses a **Centralized Threading Server** with **Asynchronous Background Workers**.

### **Key Components:**
1.  **The Dashboard Server (`dashboard_server.py`):**
    *   Acts as the brain and the face.
    *   Runs a `ThreadingHTTPServer` so multiple requests (approvals, clicks, status) don't block each other.
    *   Hosts the Web UI and exposes REST APIs (`/api/approve`, `/api/upload-drop`, etc.).
    *   Contains a "Processing Lock" to prevent double-clicks on approvals.

2.  **The Watchers (Background Threads):**
    *   **WhatsApp Watcher:** Uses Playwright to scan the DOM for unread badges. It extracts message text and contact names, then writes `.md` files to `watcher_output/`. It uses "Search-to-Reveal" to avoid marking chats as read.
    *   **Gmail Watcher:** Polls Gmail API for unread emails and writes `.md` files to `watcher_output/`.

3.  **The AI Processor (`watcher_processor.py`):**
    *   Runs every 5 minutes in the background.
    *   Scans `watcher_output/` for new files.
    *   **Validation:** Checks if the AI has extracted critical data (e.g., "Customer Name" and "Amount"). 
        *   *Pass:* It creates a task in `Pending_Approval/`.
        *   *Fail:* It logs an error and returns `False`, leaving the raw file in `watcher_output/` (it does not delete it).
    *   *Note: While it attempts to block "garbage" tasks, occasionally the AI may return deceptive placeholders (like "N/A") that slip through the filter.*

4.  **The AI Brain (`intent_analyzer.py`):**
    *   Connected via Groq API (Llama-3.3-70b).
    *   Analyzes raw text and determines:
        *   **Intent:** (e.g., `odoo_invoice`, `whatsapp_reply`, `informational`)
        *   **Entities:** Extracts specific data (Name, Amount, Message Content).
        *   **Actionability:** Decides if a human needs to approve it.

---

## 🌊 3. Data Flow (The Lifecycle of a Task)

### **Phase 1: Input (Detection)**
*   **Trigger:** A message arrives on WhatsApp or Gmail.
*   **Action:** The active Watcher detects the unread message.
*   **Storage:** Writes a raw file (e.g., `whatsapp_20260404...md`) into `data/watcher_output/`.

### **Phase 2: Intelligence (Processing)**
*   **Trigger:** The Processor wakes up (every 5 mins).
*   **Analysis:** Sends the raw text to the **AI Brain**.
*   **Validation:** 
    *   *Pass:* The AI extracted required details. A structured task is created in `data/AI_Employee_Vault/Pending_Approval/`.
    *   *Fail:* The Processor logs an error (e.g., `✗ BLOCKED: Missing critical info`) and **leaves the raw file in the `watcher_output/` folder**. It does not delete the file or create a task.

### **Phase 3: Review (Dashboard)**
*   **UI Update:** The Dashboard polls the API and shows the new task count.
*   **User Action:** User views the task.
    *   *Drop Zone:* If a file was dropped manually, the UI sends it directly to the Processor.
    *   *Approval:* User clicks **Approve**. The server sets a "Processing Lock" to prevent duplicates.

### **Phase 4: Execution (The "Do" Phase)**
*   **Routing:** `dashboard_server.py` looks at the `type:` field in the task file.
    *   **WhatsApp:** Calls `whatsapp_integration.py`. It searches for the contact by **Name** (since phones might be missing), types the message, and hits send.
    *   **Odoo:** Calls `odoo_integration.py`. It connects to the Dockerized Odoo instance and creates an Invoice via API.
*   **Feedback:** 
    *   *Success:* A toast notification appears. Task moves to `Done/`.
    *   *Failure:* The dashboard shows a **specific error toast** (e.g., "Execution Failed: could not convert string to float"). The task remains available for the user to see the error and decide what to do next.

---

## 🔌 4. Integration Map

| Integration | Protocol | Role | Status |
| :--- | :--- | :--- | :--- |
| **WhatsApp** | Playwright (Browser) | Detect messages, Reply by Name | ✅ **Working** |
| **Gmail** | Google API (OAuth2) | Detect emails, Read body | ✅ **Working** |
| **Odoo** | JSON-RPC (API) | Create Invoices automatically | ✅ **Working** |
| **AI Engine** | Groq API (Llama-3.3) | Classify Intent & Extract Data | ✅ **Working** |
| **Dashboard** | HTTP (Threading) | User Interface & Task Management | ✅ **Working** |

---

## 🚀 5. Startup Sequence

1.  **`START.bat`** is executed.
2.  **Docker Check:** Verifies Odoo/Postgres containers are running.
3.  **Server Launch:** Starts `dashboard_server.py` on port 3000.
4.  **Auto-Start:**
    *   The **AI Processor** thread starts automatically in the background.
    *   The **Watchers** wait for the user to click "Start" in the UI.

---

## 🛡️ 6. Safety Features & Limitations

1.  **Processing Lock:** Prevents the same task from running twice if the user double-clicks.
2.  **Attempted Validation:** The processor checks for critical data (Name, Amount). If the AI explicitly reports missing info, it blocks task creation. *Limitation: Occasionally, the AI might return "N/A" as a value, which the system might incorrectly accept as valid data.*
3.  **Threading:** UI remains responsive even if a task (like sending WhatsApp) takes time.
4.  **Error Reporting:** If a task fails during execution (e.g., Odoo is down), the dashboard provides a specific reason rather than a generic crash.
5.  **Non-Invasive Watcher:** WhatsApp Watcher uses DOM scanning and "Search-to-Reveal" rather than clicking, so it doesn't mark messages as read.
