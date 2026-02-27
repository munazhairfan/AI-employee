# WhatsApp File Format Guide

## 📁 File Location

Save files in: `AI_Employee_Vault/Needs_Action/`

Filename: `whatsapp_*.md` or `*_whatsapp.md`

---

## 📝 File Format

```markdown
---
type: whatsapp
phone: +923001234567
message: Your message here
---

# WhatsApp Message Request

**To:** +923001234567  
**Message:** Your message here

## Any additional details (optional)

More context about the message...
```

---

## 🔑 Required Fields (in frontmatter)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `type` | string | `whatsapp` | Must be "whatsapp" |
| `phone` | string | `+923001234567` | Phone with country code |
| `message` | string | `Hello!` | Message text |

---

## ✅ Example Files

### Example 1: Simple Message

```markdown
---
type: whatsapp
phone: +923001234567
message: Hello! This is a test.
---

# WhatsApp Message
```

### Example 2: Customer Notification

```markdown
---
type: whatsapp
phone: +923009876543
message: Dear Customer, your order #12345 has been shipped. Thank you!
---

# Order Notification

**Customer:** John Doe  
**Order:** #12345  
**Status:** Shipped
```

### Example 3: Appointment Reminder

```markdown
---
type: whatsapp
phone: +923001112233
message: Reminder: You have an appointment tomorrow at 3:00 PM.
---

# Appointment Reminder

**Patient:** Jane Smith  
**Date:** Tomorrow  
**Time:** 3:00 PM
```

### Example 4: Multiple Recipients (Create Separate Files)

**File 1:** `whatsapp_customer1.md`
```markdown
---
type: whatsapp
phone: +923001111111
message: Special offer for you!
---

# Customer 1 Message
```

**File 2:** `whatsapp_customer2.md`
```markdown
---
type: whatsapp
phone: +923002222222
message: Special offer for you!
---

# Customer 2 Message
```

---

## 📱 Phone Number Format

**✅ Correct:**
- `+923001234567` (with + and country code)
- `+14155551234` (US number)
- `+447911123456` (UK number)

**❌ Wrong:**
- `03001234567` (missing country code)
- `92-300-1234567` (has dashes)
- `+92 300 1234567` (has spaces)

---

## 🚀 How It Works

1. **Create file** in `Needs_Action/`
2. **Orchestrator reads** the file
3. **Extracts** phone and message from frontmatter
4. **Sends** via local agent (WhatsApp Web)
5. **Moves** file to `Processed/`
6. **Logs** to Dashboard.md

---

## 🧪 Test File (Already Created)

A test file is already created for you:

**Location:** `AI_Employee_Vault/Needs_Action/test_whatsapp.md`

**Content:**
```markdown
---
type: whatsapp
phone: +923001234567
message: Hello! This is a test message from AI Employee Vault.
---

# WhatsApp Message Request
```

---

## ✅ Quick Template (Copy-Paste)

```markdown
---
type: whatsapp
phone: +[country code][number]
message: [your message]
---

# WhatsApp Message

**To:** [name/number]
**Message:** [your message]

## Details

[Any additional information]
```

---

## 🐛 Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `type: whatsapp` | Add it in frontmatter |
| Phone without + | Add country code with + |
| No message field | Add `message: your text` |
| File in wrong folder | Put in `Needs_Action/` |
| Wrong file extension | Use `.md` extension |

---

**Ready to send WhatsApp messages?** 

Just create a `.md` file with the format above and drop it in `Needs_Action/`! 🚀
