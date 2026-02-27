# Phase 1 Setup Guide - Cloud Infrastructure

**Status:** Ready to execute  
**Time Required:** 15-20 minutes  
**Prerequisites:** Email address, 15 minutes of focus

---

## 📋 What We're Doing

Setting up the cloud infrastructure for multi-tenant SaaS:
1. Create Supabase account (database)
2. Run database schema
3. Get API credentials
4. Test locally

---

## Step 1: Create Supabase Account (5 minutes)

### 1.1 Sign Up

1. Go to https://supabase.com
2. Click "Start your project" or "Sign In"
3. Sign up with GitHub (recommended) or email

### 1.2 Create New Project

1. Click "New Project"
2. Fill in:
   - **Name:** `ai-employee-vault` (or your choice)
   - **Database Password:** Choose a strong password (save it!)
   - **Region:** Choose closest to you (e.g., East US for US)
3. Click "Create new project"
4. Wait 2-3 minutes for database to be ready

### 1.3 Get Database Credentials

1. In your project dashboard, click **Settings** (left sidebar)
2. Click **API**
3. Copy these two values:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **Service Role Key:** `eyJhbGc...` (long string, keep secret!)

**⚠️ IMPORTANT:** 
- Service Role Key bypasses RLS - NEVER share it or commit to Git
- Project URL is public - okay to share
- Save these somewhere safe (password manager recommended)

---

## Step 2: Run Database Schema (5 minutes)

### 2.1 Open SQL Editor

1. In Supabase dashboard, click **SQL Editor** (left sidebar)
2. Click **New Query**

### 2.2 Run Schema

1. Open file: `cloud-api/database-schema.sql`
2. Copy **ALL** contents
3. Paste into Supabase SQL Editor
4. Click **Run** (or press Ctrl+Enter)

### 2.3 Verify Success

You should see:
- ✅ "Success. No rows returned" for each table
- ✅ Green checkmarks next to each statement
- ✅ Tables appear in "Table Editor" (left sidebar)

**Expected Tables:**
- customers
- users
- whatsapp_sessions
- email_tokens
- linkedin_tokens
- facebook_tokens
- instagram_tokens
- x_tokens
- action_logs
- schema_version

### 2.4 Get Your Test API Key

1. In Supabase, click **Table Editor**
2. Click **users** table
3. You should see one row (test user created by schema)
4. Copy the **api_key** value (starts with `sk_`)

**Save this key** - you'll need it for testing!

---

## Step 3: Configure Environment (2 minutes)

### 3.1 Create .env.local

1. Open `cloud-api/.env.example`
2. Copy it and rename to `.env.local` (in same folder)

### 3.2 Fill in Values

Edit `cloud-api/.env.local`:

```env
# Replace with YOUR values from Step 1.3
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...your-key-here

# Generate encryption key (run command below)
ENCRYPTION_KEY=paste-generated-key-here
```

### 3.3 Generate Encryption Key

Run this command in PowerShell/CMD:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Copy the output (64 characters) and paste as `ENCRYPTION_KEY`

**⚠️ IMPORTANT:** Save this key too - you'll need it for deployment!

---

## Step 4: Install Dependencies (3 minutes)

### 4.1 Install Node.js (if not installed)

1. Go to https://nodejs.org
2. Download LTS version (18.x or newer)
3. Run installer
4. Restart terminal after installation

### 4.2 Install Dependencies

Open terminal in project root:

```bash
cd cloud-api
npm install
```

**Expected output:**
- `added 50 packages in 30s` (approximately)

If you see errors:
- Check Node.js version: `node --version` (must be 18+)
- Try deleting `node_modules` and running again

---

## Step 5: Test Locally (5 minutes)

### 5.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 5.2 Start Development Server

```bash
cd cloud-api
npm run dev
```

**Expected output:**
```
> ai-employee-vault-cloud-api@1.0.0 dev
> vercel dev

▲  Development server ready at http://localhost:3000
```

### 5.3 Test Health Endpoint

Open browser or use curl:

```bash
curl http://localhost:3000/api/v1/health
```

**Expected response:**
```json
{
  "status": "ok",
  "message": "AI Employee Vault API is running",
  "version": "1.0.0",
  "timestamp": "2026-02-26T12:00:00.000Z"
}
```

✅ **If you see this, the API is working!**

### 5.4 Test Registration

```bash
curl -X POST http://localhost:3000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"company_name\":\"Test Corp\",\"email\":\"test@example.com\",\"password\":\"testpass123\",\"name\":\"Test User\"}"
```

**Expected response:**
```json
{
  "success": true,
  "customer_id": "...",
  "user_id": "...",
  "api_key": "sk_...",
  "subscription": "basic"
}
```

✅ **Save the api_key from response!**

### 5.5 Test Login

```bash
curl -X POST http://localhost:3000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"testpass123\"}"
```

**Expected response:**
```json
{
  "success": true,
  "user_id": "...",
  "customer_id": "...",
  "api_key": "sk_...",
  "name": "Test User",
  "role": "admin"
}
```

---

## ✅ Success Checklist

After completing all steps, you should have:

- [ ] Supabase account created
- [ ] Project running at `https://xxxxx.supabase.co`
- [ ] Database schema applied (10 tables created)
- [ ] `.env.local` file with real credentials
- [ ] Local API server running at `http://localhost:3000`
- [ ] Health endpoint working
- [ ] Registration endpoint working
- [ ] Login endpoint working
- [ ] Test API key saved

---

## 🐛 Troubleshooting

### Problem: "Missing Supabase environment variables"

**Solution:** Check `.env.local` exists and has correct values:
```env
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
```

### Problem: "Module not found: @supabase/supabase-js"

**Solution:** Run `npm install` in `cloud-api/` folder

### Problem: "Port 3000 already in use"

**Solution:** 
- Close other apps using port 3000
- Or edit `vercel.json` to use different port

### Problem: "Database relation 'customers' does not exist"

**Solution:** 
- Re-run `database-schema.sql` in Supabase SQL Editor
- Check Table Editor to verify tables exist

### Problem: "Invalid API key" when testing

**Solution:**
- Check API key from `users` table in Supabase
- Make sure you're copying the full key (starts with `sk_`)

---

## 🎯 What's Next?

After Phase 1 is complete:

### Phase 2: OAuth Endpoints (Next Session)
- WhatsApp OAuth start/callback
- LinkedIn OAuth start/callback
- Facebook OAuth start/callback
- Google OAuth (for Gmail)

### Phase 3: Action Endpoints
- send-whatsapp
- send-email
- post-linkedin
- post-facebook

### Phase 4: Local Agent Integration
- Update orchestrator to use cloud API
- Add cloud client to local agent
- Test end-to-end flow

---

## 📞 Need Help?

1. Check `cloud-api/README.md` for detailed API docs
2. Check `DEVELOPMENT_CONTEXT.md` for project status
3. Check Supabase dashboard for database errors
4. Check terminal for error messages

---

## 🔐 Security Reminders

**NEVER commit these files:**
- `.env.local` (contains secrets)
- Any file with `SUPABASE_SERVICE_KEY`
- Any file with `ENCRYPTION_KEY`

**ALWAYS keep secret:**
- Supabase Service Role Key
- Encryption Key
- Customer API keys

**Safe to share:**
- Supabase Project URL
- Database schema (no data)
- API endpoint code

---

**Last Updated:** 2026-02-26  
**Status:** Ready to execute  
**Next Action:** Follow steps 1-5 above
