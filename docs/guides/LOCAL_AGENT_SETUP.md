# Local Agent - Quick Setup Guide

**Time:** 5 minutes

---

## Step 1: Get Your API Key

### Option A: From Supabase
1. Go to Supabase dashboard
2. Click **Table Editor**
3. Click **users** table
4. Copy the **api_key** value (starts with `sk_`)

### Option B: From Phase 1 Test
If you saved the output from Phase 1 registration, use that API key.

---

## Step 2: Update .env File

1. Open: `local-agent/.env`
2. Replace `sk_your-actual-api-key-here` with your real API key
3. Save the file

Example:
```env
API_KEY=sk_abc123xyz456...
CLOUD_API_URL=http://localhost:3000
```

---

## Step 3: Install Dependencies

```bash
cd local-agent
npm install
```

**Wait for installation** (may take 2-3 minutes for whatsapp-web.js)

---

## Step 4: Connect WhatsApp

```bash
npm run connect-whatsapp
```

**What you'll see:**
```
🔌 Connecting to WhatsApp Web...

📱 SCAN THIS QR CODE:

[QR Code appears here]

Open WhatsApp > Settings > Linked Devices > Link a Device
```

---

## Step 5: Scan QR Code

1. Open WhatsApp on your phone
2. Go to **Settings** > **Linked Devices**
3. Tap **Link a Device**
4. Scan the QR code in your terminal

---

## Step 6: Success!

After scanning, you'll see:
```
✅ WhatsApp authenticated!
✅ Session saved to cloud API

🎉 WhatsApp Web is ready!

Connected as: Your Name
Phone: 1234567890

✅ WhatsApp is now connected and working!
```

---

## ✅ What Now?

**Keep this terminal running!** Your WhatsApp is now connected.

Next:
- Integrate with your existing orchestrator
- Send messages via WhatsApp Web
- Messages will be logged to cloud API

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| QR code not appearing | Wait 10 seconds, check terminal |
| "API_KEY missing" | Check `.env` file has correct key |
| Installation failed | Run `npm install` again |
| WhatsApp won't connect | Check phone has internet |

---

**Need help?** Check `local-agent/README.md` for more details!
