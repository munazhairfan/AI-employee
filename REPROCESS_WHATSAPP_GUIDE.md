# Re-Processing WhatsApp Messages for Testing

## Problem
Once WhatsApp messages are processed, they're marked as "processed" and never checked again. This makes testing difficult.

---

## ✅ Solutions Created

### **1. Reset Cache Script**
**File:** `scripts\reset_whatsapp_cache.bat`

**What it does:**
- Clears WhatsApp message cache (`.processed_whatsapp.txt`)
- Clears processor log (`watcher_processed_log.json`)
- Optionally deletes watcher output files

**Usage:**
```bash
scripts\reset_whatsapp_cache.bat
```

**Options:**
- **Option 1:** Clear cache only (keeps output files for reference)
- **Option 2:** Full reset (deletes everything)

---

### **2. Test Message Generator**
**File:** `scripts\create_test_whatsapp_message.bat`

**What it does:**
- Creates fake WhatsApp message files
- Tests AI processing without sending real messages
- Customizable sender, phone, and message

**Usage:**
```bash
scripts\create_test_whatsapp_message.bat
```

---

## Testing Workflows

### **Workflow A: Test with Real WhatsApp Messages**

1. **Reset cache:**
   ```bash
   scripts\reset_whatsapp_cache.bat
   # Choose Option 1
   ```

2. **Start WhatsApp watcher** from dashboard

3. **Send real message** from your phone

4. **Wait for processing** (up to 5 minutes)

5. **Check dashboard** → Pending Tasks

6. **Click task** to view details

7. **Approve/Reject**

**Repeat:** Run reset script again to re-process same messages

---

### **Workflow B: Test with Fake Messages (Faster)**

1. **Run test generator:**
   ```bash
   scripts\create_test_whatsapp_message.bat
   # Enter test message or use defaults
   ```

2. **Wait for AI processor** (up to 5 minutes)
   
   **OR trigger manually:**
   ```bash
   python src\watcher_processor.py
   # Let it run one cycle, then Ctrl+C
   ```

3. **Check dashboard** → Pending Tasks

4. **Click task** to view details

**Repeat:** Run generator again with different messages

---

### **Workflow C: Manual File Creation (Advanced)**

1. **Create file manually:**
   ```bash
   # Create in: data/watcher_output/
   # Name: whatsapp_YYYYMMDD_HHMMSS.md
   ```

2. **Add content:**
   ```markdown
   ---
   source: whatsapp_watcher
   from: Test User
   phone: 923001234567
   received: 2025-04-02T10:30:00
   ---

   ## Original Message
   **From:** Test User
   **Phone:** 923001234567
   
   **Message:**
   Hi, this is a test message
   ```

3. **Wait for processor** or run manually

---

## What Each Script Does

### **reset_whatsapp_cache.bat**

```
┌─────────────────────────────────────────┐
│ Before Reset                            │
├─────────────────────────────────────────┤
│ ✓ Message processed                     │
│ ✓ Hash in .processed_whatsapp.txt       │
│ ✓ File in watcher_output/               │
│ ✓ Task in Pending_Approval/             │
│ ✓ Logged in watcher_processed_log.json  │
└─────────────────────────────────────────┘
              ↓
         [RESET]
              ↓
┌─────────────────────────────────────────┐
│ After Reset (Option 1)                  │
├─────────────────────────────────────────┤
│ ✗ Hash removed from cache               │
│ ✓ File still in watcher_output/         │
│ ✓ Task still in Pending_Approval/       │
│ ✗ Log cleared                           │
└─────────────────────────────────────────┘

Result: Watcher will re-process messages as "new"
```

---

### **create_test_whatsapp_message.bat**

```
Creates file:
data/watcher_output/whatsapp_test_20250402_103000.md

Content:
---
source: whatsapp_watcher
from: Test User (+923001234567)
phone: 923001234567
received: 2025-04-02 10:30:00
subject: WhatsApp message from Test User
---

## Original Message
**From:** Test User (+923001234567)
**Phone:** 923001234567
**Received:** 2025-04-02 10:30:00

**Message Content:**
```
Hi, can you send me the invoice for last month? Thanks!
```

---

## Context for AI
This is an UNREAD WhatsApp message that needs a reply.
```

Processor picks it up → Creates task → Appears in dashboard
```

---

## File Locations

| File/Folder | Purpose |
|-------------|---------|
| `data/AI_Employee_Vault/.processed_whatsapp.txt` | WhatsApp message cache (hashes) |
| `data/watcher_output/*.md` | Watcher output files |
| `data/watcher_processed_log.json` | Processor log (which files processed) |
| `data/AI_Employee_Vault/Pending_Approval/*.md` | AI-created tasks |

---

## Quick Commands

### **Reset Everything:**
```bash
scripts\reset_whatsapp_cache.bat
# Choose Option 2
```

### **Create Test Message:**
```bash
scripts\create_test_whatsapp_message.bat
```

### **Manually Trigger Processor:**
```bash
python src\watcher_processor.py
# Wait 30 seconds, then Ctrl+C
```

### **View Processed Messages:**
```bash
type data\AI_Employee_Vault\.processed_whatsapp.txt
```

### **View Watcher Output:**
```bash
dir data\watcher_output\*.md
```

---

## Troubleshooting

### **"Messages not re-processing after reset"**

**Cause:** Messages already marked as "read" in WhatsApp Web

**Fix:**
1. Reset cache (Option 2)
2. Stop WhatsApp watcher
3. Send NEW messages (different from before)
4. Start watcher

---

### **"Processor not picking up test files"**

**Cause:** Processor runs every 5 minutes

**Fix:**
```bash
# Run processor manually
python src\watcher_processor.py
# Wait for it to process files (30 seconds)
# Press Ctrl+C to stop
```

---

### **"Task created but phone missing"**

**Cause:** WhatsApp Web doesn't expose phone for this contact

**Fix:**
1. Edit test file manually
2. Add phone number in metadata
3. Or enter phone manually when approving

---

## Testing Checklist

### **Test Phone Extraction:**
- [ ] Reset cache (Option 1)
- [ ] Start WhatsApp watcher
- [ ] Send message from contact with phone
- [ ] Check logs: `Phone from data-id: 923001234567`
- [ ] Check watcher output file has phone
- [ ] Verify task has phone in metadata

### **Test Message Context:**
- [ ] Create test message (real or fake)
- [ ] Wait for AI to process
- [ ] Click task in dashboard
- [ ] Modal shows original message
- [ ] Modal shows sender info
- [ ] Modal shows phone number

### **Test Approval:**
- [ ] Click task to view details
- [ ] Check phone extracted
- [ ] Click Approve
- [ ] Message sent successfully

---

## Summary

| Need | Solution |
|------|----------|
| Re-process messages | `reset_whatsapp_cache.bat` |
| Test without real messages | `create_test_whatsapp_message.bat` |
| Manual control | Edit files in `data/watcher_output/` |
| Force processing | `python src\watcher_processor.py` |

---

**Status:** ✅ Ready for Testing

**Documentation:** 
- `scripts/TESTING_WHATSAPP.md` - Full testing guide
- `WHATSAPP_FIXES_COMPLETE.md` - Complete fix documentation
