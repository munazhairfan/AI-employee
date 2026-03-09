# 🚀 Quick Reference Card

**For:** AI Employee Vault - Phase 1  
**Status:** Ready for setup  
**Time:** 20 minutes

---

## 📁 Files You Need

| File | Purpose | Action |
|------|---------|--------|
| `docs/guides/PHASE1_SETUP.md` | **Complete setup guide** | **READ THIS FIRST** |
| `cloud-api/database-schema.sql` | Database schema | Copy to Supabase |
| `cloud-api/.env.example` | Environment template | Copy to `.env.local` |
| `PHASE1_SUMMARY.md` | Progress summary | Reference |
| `DEVELOPMENT_CONTEXT.md` | Project context | Read before continuing |

---

## 🔗 Important URLs

| Service | URL | Action |
|---------|-----|--------|
| **Supabase** | https://supabase.com | Create account |
| **Vercel** | https://vercel.com | Deploy later |
| **Node.js** | https://nodejs.org | Install if needed |

---

## ⚡ Quick Commands

### Generate Encryption Key
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Install Dependencies
```bash
cd cloud-api
npm install
```

### Start Local Server
```bash
cd cloud-api
npm run dev
```

### Test Health
```bash
curl http://localhost:3000/api/v1/health
```

### Test Registration
```bash
curl -X POST http://localhost:3000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"company_name\":\"Test\",\"email\":\"test@test.com\",\"password\":\"testpass123\",\"name\":\"Test\"}"
```

### Test Login
```bash
curl -X POST http://localhost:3000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"password\":\"testpass123\"}"
```

---

## 📊 Environment Variables

Create `cloud-api/.env.local`:

```env
SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...YOUR-KEY-HERE
ENCRYPTION_KEY=64-character-hex-key-here
```

---

## ✅ Success Checklist

After setup, you should have:

- [ ] Supabase account created
- [ ] 10 tables in Supabase (check Table Editor)
- [ ] `.env.local` file with real values
- [ ] Local server running (http://localhost:3000)
- [ ] Health endpoint returns `{"status": "ok"}`
- [ ] Test API key saved from users table

---

## 🐛 Common Issues

| Error | Solution |
|-------|----------|
| "Missing Supabase environment variables" | Check `.env.local` exists |
| "Module not found" | Run `npm install` |
| "Port 3000 already in use" | Close other apps or restart |
| "Invalid API key" | Check users table in Supabase |

---

## 📞 Next Steps

1. ✅ Complete Phase 1 setup (20 min)
2. ⏳ Build Phase 2: OAuth endpoints
3. ⏳ Build Phase 3: Action endpoints
4. ⏳ Build Phase 4: Local agent

---

## 🔐 Security Reminders

**NEVER commit:**
- `.env.local`
- `SUPABASE_SERVICE_KEY`
- `ENCRYPTION_KEY`

**ALWAYS keep secret:**
- Service Role Key
- Encryption Key
- Customer API keys

---

**Ready? Open `docs/guides/PHASE1_SETUP.md` and start!** 🚀
