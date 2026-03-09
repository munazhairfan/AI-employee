# WhatsApp Business API Setup Guide

**Date:** 2026-03-01  
**Status:** Ready for Setup

---

## 🎯 What You Need

To enable WhatsApp messaging, you need **WhatsApp Business API** credentials from Meta.

---

## 📋 Step-by-Step Setup

### Step 1: Create Meta Developer Account

1. **Go to:** https://developers.facebook.com/
2. **Click:** "Get Started" or "Log In"
3. **Sign in** with Facebook account
4. **Accept** developer terms

---

### Step 2: Create WhatsApp Business App

1. **Go to:** https://business.facebook.com/wa/manage/applications/
2. **Click:** "Create App"
3. **Select:** "Business" type
4. **Fill in:**
   - App Name: "AI Employee Vault"
   - Business Account: Your business
5. **Click:** "Create App"

---

### Step 3: Add WhatsApp Product

1. In your app dashboard, **scroll down**
2. **Click:** "Add Product"
3. **Select:** "WhatsApp"
4. **Click:** "Set Up"

---

### Step 4: Get Your Credentials

**You'll see:**
- **Phone Number ID** - Copy this!
- **Access Token** - Click "Copy"

**Save these:**
```
Phone Number ID: 123456789012345
Access Token: EAAB... (long string)
```

---

### Step 5: Add to .env File

**Open:** `D:\AI\Hackathon-0\.env`

**Add:**
```bash
# WhatsApp Business API
WHATSAPP_API_KEY=EAAB...your-access-token-here
META_PHONE_NUMBER_ID=123456789012345
```

**Save the file.**

---

### Step 6: Test WhatsApp

**Run:**
```bash
python src/whatsapp_api.py
```

**Expected:**
```
Testing WhatsApp Business API...
============================================================
[OK] SUCCESS: WhatsApp sent to +923080311205
Message ID: wamid.HBgN...
```

**Check your phone** - you'll receive the test message!

---

## 🧪 Test from Dashboard

### Step 1: Create WhatsApp Task

**In dashboard (http://localhost:3000):**

Type:
```
WhatsApp to +923080311205: Hello from AI Employee Vault!
```

**Click:** "Analyze & Create Task"

### Step 2: Approve

**Click:** "Approve"

**Result:**
```
Task approved!

WhatsApp sent to +923080311205
```

**Check your phone** - message received! ✅

---

## 💰 Pricing

### Free Tier:
- **First 1000 conversations/month:** FREE
- **User-initiated:** Free (customer messages you first)
- **Business-initiated:** ~$0.005 per message

### Example Costs:
- 100 messages/day = ~$1.50/month
- 10 messages/day = ~$0.15/month

---

## 🔧 Troubleshooting

### Error: "credentials not configured"

**Fix:**
1. Check `.env` file has credentials
2. Restart dashboard: `python dashboard_server.py`

---

### Error: "Invalid phone number"

**Fix:**
- Phone must include country code
- Example: `+923001234567` (not `03001234567`)

---

### Error: "Template not found"

**Fix:**
- For first message to a number, use template messages
- Or wait for customer to message you first

---

## ✅ Success Checklist

- [ ] Meta Developer account created
- [ ] WhatsApp Business App created
- [ ] Phone Number ID copied
- [ ] Access Token copied
- [ ] Added to `.env` file
- [ ] Test script works (`python src/whatsapp_api.py`)
- [ ] Dashboard WhatsApp works

---

## 📚 Resources

- **Official Docs:** https://developers.facebook.com/docs/whatsapp
- **API Reference:** https://developers.facebook.com/docs/whatsapp/cloud-api/reference
- **Pricing:** https://developers.facebook.com/docs/whatsapp/pricing

---

**Once configured, WhatsApp will work 100% reliably!** 📱✅
