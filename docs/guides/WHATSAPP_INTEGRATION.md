# WhatsApp Integration Guide

**Status:** Ready to integrate with orchestrator

---

## 🎯 What Was Built

### 1. Cloud API Client (`src/cloud_client.py`)

Calls cloud API to send WhatsApp messages.

**Usage:**
```python
from src.cloud_client import send_whatsapp_message

result = send_whatsapp_message(
    phone='+1234567890',
    message='Hello from AI Employee Vault!'
)

if result['success']:
    print("Message sent!")
else:
    print(f"Error: {result['error']}")
```

---

### 2. Local WhatsApp Sender (`src/whatsapp_sender.py`)

Sends messages via your connected local agent (WhatsApp Web session).

**Usage:**
```python
from src.whatsapp_sender import send_whatsapp_local

result = send_whatsapp_local(
    phone='+1234567890',
    message='Hello!'
)

if result['success']:
    print("Message sent via WhatsApp Web!")
```

---

## 📋 How to Integrate with Orchestrator

### Option A: Use Local Agent (Recommended)

Your local agent already has WhatsApp Web connected. Use `whatsapp_sender.py`:

**In your orchestrator.py, add this function:**

```python
from src.whatsapp_sender import send_whatsapp_local

def execute_whatsapp_action(phone: str, message: str) -> bool:
    """Send WhatsApp message via local agent"""
    result = send_whatsapp_local(phone, message)
    
    if result['success']:
        log_action('whatsapp.send', f'Sent to {phone}')
        return True
    else:
        log_action('whatsapp.failed', f'Failed: {result["error"]}')
        return False
```

**Then call it when processing plans:**

```python
# In your main orchestrator loop
if action_type == 'send_whatsapp':
    success = execute_whatsapp_action(
        phone=extract_phone(plan_file),
        message=extract_message(plan_file)
    )
    
    if success:
        move_to_done(file)
    else:
        move_to_pending(file)
```

---

### Option B: Use Cloud API

If you want to log actions to cloud API:

```python
from src.cloud_client import send_whatsapp_message, test_connection

# Check if cloud API is available
if test_connection():
    result = send_whatsapp_message(phone, message)
    # Logs to cloud automatically
```

---

## 🧪 Test It

### Test Local Sender

```python
# tests/test_whatsapp.py
from src.whatsapp_sender import send_whatsapp_local

result = send_whatsapp_local(
    phone='+923001234567',  # Your test number
    message='Test from orchestrator!'
)

print(result)
# Should print: {'success': True, 'message': 'Message sent successfully'}
```

Run:
```bash
python tests/test_whatsapp.py
```

---

## 📊 Flow Diagram

```
┌─────────────────┐
│  Orchestrator   │
│  (orchestrator.py)
└────────┬────────┘
         │
         │ Detects WhatsApp action
         │ from Plan.md
         │
         ▼
┌─────────────────┐
│ whatsapp_sender │
│ (src/whatsapp_sender.py)
└────────┬────────┘
         │
         │ Calls local agent
         │ via subprocess
         │
         ▼
┌─────────────────┐
│ Local Agent     │
│ (WhatsApp Web)  │
│ - Already running
│ - Session active
└────────┬────────┘
         │
         │ Sends message via
         │ WhatsApp Web
         │
         ▼
┌─────────────────┐
│ Recipient       │
│ Gets message    │
└─────────────────┘
```

---

## ✅ What You Need to Do

### 1. Keep Local Agent Running

Make sure this is always running:
```bash
cd local-agent
npm start
```

### 2. Add Integration to Orchestrator

Edit `src/orchestrator.py` and add:

```python
from src.whatsapp_sender import send_whatsapp_local

# Add this where you process actions
def process_whatsapp_action(plan_data):
    phone = extract_phone(plan_data)
    message = extract_message(plan_data)
    
    result = send_whatsapp_local(phone, message)
    
    if result['success']:
        move_to_done(plan_data['file'])
        log_action('whatsapp.sent', f'To: {phone}')
    else:
        move_to_pending(plan_data['file'])
        log_action('whatsapp.failed', result['error'])
```

### 3. Test

1. Run your orchestrator
2. Drop a file that triggers WhatsApp action
3. Check if message is sent

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to local agent" | Make sure `npm start` is running in local-agent |
| "WhatsApp disconnected" | Re-run `npm start` in local-agent |
| "Timeout after 35 seconds" | Check phone number format (+country code) |
| Message not sent | Check WhatsApp session is active |

---

## 🎯 Next Steps

After integration:

1. **Test end-to-end** - Drop file → Orchestrator → WhatsApp sent
2. **Add error handling** - Retry failed messages
3. **Add logging** - Log all sent messages to Dashboard.md
4. **Add approval flow** - Require approval before sending

---

**Ready to integrate?** 

Just add the import and call `send_whatsapp_local()` in your orchestrator!
