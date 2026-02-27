# WhatsApp Test - Orchestrator Integration

**Purpose:** Test that orchestrator can send WhatsApp messages

---

## 📋 Prerequisites

1. **Local Agent Running**
   ```bash
   cd local-agent
   npm start
   ```
   Keep this running!

2. **Orchestrator Updated**
   - `src/orchestrator.py` has WhatsApp integration
   - `src/whatsapp_sender.py` exists
   - Import added at top of orchestrator

---

## 🧪 Test Method 1: Drop Test File

### Create Test File

Create: `AI_Employee_Vault/Needs_Action/test_whatsapp.md`

```markdown
---
type: whatsapp
phone: +923001234567
message: Hello from orchestrator test!
---

# WhatsApp Test Message

This is a test to verify orchestrator integration.

**Phone:** +923001234567
**Message:** Hello from orchestrator test!
```

### Run Orchestrator

```bash
cd src
python orchestrator.py
```

### Expected Output

```
Processing test_whatsapp.md...
Auto-sending WhatsApp message via local agent...
WhatsApp sent to +923001234567
Moved test_whatsapp.md to Processed (WhatsApp sent)
```

### Check Results

1. **Phone should receive message**: "Hello from orchestrator test!"
2. **File moved to**: `AI_Employee_Vault/Processed/test_whatsapp.md`
3. **Logs updated**: `Logs/today.json` has whatsapp_auto entry
4. **Dashboard updated**: `AI_Employee_Vault/Dashboard.md` has entry

---

## 🧪 Test Method 2: Direct Python Test

```bash
cd src
python -c "from whatsapp_sender import send_whatsapp_local; print(send_whatsapp_local('+923001234567', 'Test message'))"
```

**Expected:**
```python
{'success': True, 'message': 'Message sent successfully'}
```

---

## ✅ Success Checklist

- [ ] Local agent running (`npm start` in local-agent)
- [ ] Test file created in Needs_Action/
- [ ] Orchestrator running
- [ ] Message received on phone
- [ ] File moved to Processed/
- [ ] Logs updated

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Module not found: whatsapp_sender" | Run orchestrator from `src/` folder |
| "WhatsApp disconnected" | Restart local agent (`npm start`) |
| Message not sent | Check phone number format (+country code) |
| Timeout | Check local agent is running |

---

**Ready to test?** 

1. Make sure local agent is running
2. Create test file in Needs_Action/
3. Run orchestrator
4. Check your phone for message!
