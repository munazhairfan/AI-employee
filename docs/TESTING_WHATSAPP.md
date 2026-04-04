# Testing WhatsApp Integration - Quick Guide

## Problem
Once WhatsApp messages are processed, the watcher marks them as "processed" and won't process them again. This makes testing difficult.

---

## Solution: Reset Cache Scripts

### **Option 1: Quick Reset (Recommended for Testing)**
Clears the cache so watcher re-processes existing messages.

**Run:**
```bash
scripts\reset_whatsapp_cache.bat
```

**Or:**
```bash
python scripts\reset_whatsapp_cache.py
```

**Then choose:** Option 1

**What it does:**
- ✅ Clears WhatsApp message cache
- ✅ Clears processor log
- ✅ Keeps watcher output files (for reference)
- ✅ Watcher will re-process all messages as "new"

---

### **Option 2: Full Reset (Complete Fresh Start)**
Deletes everything and starts over.

**Run:**
```bash
scripts\reset_whatsapp_cache.bat
```

**Then choose:** Option 2

**What it does:**
- ✅ Clears WhatsApp message cache
- ✅ Clears processor log
- ✅ Deletes all watcher output files
- ✅ Complete fresh start

---

## Testing Workflow

### **Test Phone Number Extraction:**

1. **Reset cache:**
   ```bash
   scripts\reset_whatsapp_cache.bat
   # Choose Option 1
   ```

2. **Start WhatsApp watcher** from dashboard

3. **Send test messages** from different contacts:
   - Contact with phone number saved
   - Contact with just name (no phone)
   - Unsaved number

4. **Check logs** for phone extraction:
   ```
   Phone from data-id: 923001234567
   ```

5. **Check watcher output files:**
   ```
   data/watcher_output/whatsapp_20250402_*.md
   ```

6. **Verify phone is in metadata:**
   ```markdown
   ---
   from: Uzaifa
   phone: 923001234567
   ---
   ```

---

### **Test Message Context Display:**

1. **Reset cache** (Option 1)

2. **Start WhatsApp watcher**

3. **Send test message** with clear content:
   ```
   Hi, can you send me the invoice for last month?
   ```

4. **Wait for AI to process** (up to 5 minutes)

5. **Go to dashboard → Pending Tasks**

6. **Click the task card**

7. **Modal should show:**
   - ✅ Task information (type, confidence, created)
   - ✅ Suggested action
   - ✅ Original message content
   - ✅ Sender name and phone
   - ✅ Received timestamp

---

### **Test Approval Flow:**

1. **Reset cache** (Option 1)

2. **Send test message**

3. **Wait for task to appear**

4. **Click task to view details**

5. **Check if phone extracted:**
   - If ✅ phone exists → Approve should work
   - If ❌ phone missing → Should show in "Missing Information"

6. **Click Approve**

7. **Check result:**
   - Success: Message sent
   - Failed: Check error message

---

## Manual Cache Reset (Advanced)

If scripts don't work, manually delete these files:

```bash
# WhatsApp message cache
data/AI_Employee_Vault/.processed_whatsapp.txt

# Processor log
data/watcher_processed_log.json

# Watcher output files (optional)
data/watcher_output/*.md
```

---

## Check What's Being Processed

### **View Processed Messages:**
```bash
# See which messages were already processed
type data/AI_Employee_Vault\.processed_whatsapp.txt
```

### **View Processor Log:**
```bash
# See which watcher files were processed
type data/watcher_processed_log.json
```

### **View Watcher Output:**
```bash
# See all watcher output files
dir data/watcher_output\*.md
```

---

## Common Issues

### **Issue: Watcher doesn't re-process after reset**

**Cause:** Browser session still has messages marked as read

**Fix:**
1. Reset cache (Option 2)
2. Stop WhatsApp watcher
3. Send NEW messages (not the same ones)
4. Start watcher again

---

### **Issue: Phone still not extracted**

**Cause:** WhatsApp Web doesn't expose phone data for this contact

**Fix:**
1. Check watcher logs for extraction method used
2. Try saving contact with phone number in WhatsApp
3. Or manually enter phone when approving task

---

### **Issue: Task not appearing after reset**

**Cause:** AI processor is slow (5 minute intervals)

**Fix:**
1. Wait up to 5 minutes
2. Or manually trigger processor:
   ```bash
   python src/watcher_processor.py
   # Let it run for one cycle, then Ctrl+C
   ```

---

## Quick Commands Reference

| Command | Purpose |
|---------|---------|
| `scripts\reset_whatsapp_cache.bat` | Reset cache (interactive) |
| `python scripts\reset_whatsapp_cache.py` | Reset cache (Python) |
| `dir data/watcher_output\*.md` | View watcher output files |
| `type data/AI_Employee_Vault\.processed_whatsapp.txt` | View processed messages |
| `type data/watcher_processed_log.json` | View processor log |

---

## Testing Checklist

- [ ] Reset cache (Option 1 or 2)
- [ ] Start WhatsApp watcher from dashboard
- [ ] Send test message(s)
- [ ] Check watcher logs for phone extraction
- [ ] Verify watcher output file created
- [ ] Wait for AI to process (up to 5 min)
- [ ] Check task appears in Pending Tasks
- [ ] Click task to view modal
- [ ] Verify original message shown
- [ ] Verify phone number shown
- [ ] Click Approve
- [ ] Check if message sent successfully

---

**Status:** ✅ Ready for Testing
