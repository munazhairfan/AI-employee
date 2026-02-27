# 🚀 LinkedIn OAuth Setup Guide

## For Open Source Multi-User System

---

## Part 1: LinkedIn App Configuration (One Time)

### Step 1: Go to LinkedIn Developer Portal

Open: **https://www.linkedin.com/developers/apps**

### Step 2: Select Your App

Click on your app (or create new one if you don't have it)

### Step 3: Go to Auth Tab

Click **"Auth"** in the top navigation

### Step 4: Add Redirect URL

Find **"OAuth 2.0 Redirect URLs"** section

Add this URL:
```
http://localhost:3006/auth/linkedin/callback
```

Click **"Update"** button at the bottom

### Step 5: Verify Scopes

Make sure these scopes are available:
- ✅ `r_liteprofile` - Read basic profile
- ✅ `w_member_social` - Create posts
- ✅ `email` - Get email address
- ✅ `openid` - OpenID Connect

---

## Part 2: Local Setup

### Step 1: Copy Environment Template

```bash
cp .env.example .env
```

### Step 2: Fill in Your Credentials

Open `.env` and add:

```bash
# LinkedIn OAuth (Multi-User)
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
PORT=3006
```

### Step 3: Install Dependencies

```bash
npm install
```

### Step 4: Start OAuth Server

```bash
node linkedin_oauth_server.js
```

You should see:
```
============================================================
LinkedIn OAuth Server
============================================================
Server running on http://localhost:3006

Open in browser: http://localhost:3006
...
```

---

## Part 3: Connect Your LinkedIn Account

### Step 1: Open Browser

Go to: **http://localhost:3006**

### Step 2: Click Connect Button

Click **"🔗 Connect with LinkedIn"**

### Step 3: Authorize on LinkedIn

1. LinkedIn will ask you to sign in (if not already)
2. Click **"Allow"** to authorize the application
3. You'll be redirected back

### Step 4: Success!

You'll see:
- ✅ Your name
- ✅ Your email
- ✅ Your LinkedIn ID
- ✅ Your URN (automatically fetched!)

**This is the key difference:** The URN is fetched from LinkedIn automatically, so it always matches the token!

---

## Part 4: Test Posting

### Option A: From the Web Page

After connecting, use the form on the success page to post.

### Option B: Command Line

```bash
node test_oauth_post.js "Hello from AI Employee Vault!"
```

### Option C: API Call

```bash
curl -X POST http://localhost:3006/post \
  -H "Content-Type: application/json" \
  -d '{"linkedin_id":"YOUR_ID","content":"Test post!"}'
```

---

## Part 5: Verify Everything Works

### Check Connected Users

```bash
curl http://localhost:3006/users
```

Response:
```json
{
  "users": [
    {
      "id": "user_123456",
      "linkedin_id": "koKV_cgelg",
      "name": "Your Name",
      "email": "your@email.com",
      "urn": "urn:li:person:koKV_cgelg",
      "token_expires_at": "2026-04-23T..."
    }
  ]
}
```

### Check Server Health

```bash
curl http://localhost:3006/health
```

### Check Database File

Open `linkedin_users.json` - you should see your user data stored there.

---

## Troubleshooting

### ❌ "Redirect URI mismatch"

**Problem:** Redirect URL in LinkedIn dashboard doesn't match

**Fix:** 
1. Go to https://www.linkedin.com/developers/apps/77al6n4mu7fhwj/auth
2. Make sure this exact URL is added:
   ```
   http://localhost:3006/auth/linkedin/callback
   ```
3. Click Update
4. Try again

### ❌ "Invalid state parameter"

**Problem:** CSRF state expired or already used

**Fix:** Click "Connect with LinkedIn" again (it generates a new state)

### ❌ "No users connected yet"

**Problem:** Database is empty

**Fix:** 
1. Make sure server is running: `node linkedin_oauth_server.js`
2. Open browser: `http://localhost:3006`
3. Connect your LinkedIn account

### ❌ "Token expired"

**Problem:** Access token expired (60 days)

**Fix:** Server should auto-refresh. If not, reconnect the account.

### ❌ Server won't start

**Problem:** Port 3006 is already in use

**Fix:** 
```bash
# Windows
netstat -ano | findstr :3006
taskkill /F /PID <PID>

# Or change port in .env
PORT=3007
```

---

## How It Works (Simple Explanation)

```
1. User clicks "Connect LinkedIn"
        ↓
2. LinkedIn asks user to authorize
        ↓
3. LinkedIn gives us a code
        ↓
4. We exchange code → access token + refresh token
        ↓
5. We use token to ask LinkedIn: "Who is this user?"
        ↓
6. LinkedIn responds: "This is user koKV_cgelg"
        ↓
7. We build URN: "urn:li:person:koKV_cgelg"
        ↓
8. Store everything in database
        ↓
9. User can now post!
```

**Key Point:** The URN comes from LinkedIn API (step 6), so it ALWAYS matches the token!

---

## For Production Deployment

### 1. Update Redirect URL

Change to your production domain:
```
https://yourdomain.com/auth/linkedin/callback
```

### 2. Update .env

```bash
PORT=3006
NODE_ENV=production
CLIENT_ID=your_production_client_id
CLIENT_SECRET=your_production_client_secret
```

### 3. Use Real Database

Replace JSON file with PostgreSQL/MySQL:

```javascript
// Instead of fs.readFileSync
const user = await db.User.findOne({ where: { linkedin_id } });
```

### 4. Add HTTPS

LinkedIn requires HTTPS for production redirect URLs.

### 5. Add Authentication

Require login before connecting LinkedIn:

```javascript
app.get('/auth/linkedin', requireAuth, (req, res) => {
    // ...
});
```

---

## Summary Checklist

- [ ] LinkedIn app created
- [ ] Redirect URL added to LinkedIn app
- [ ] `.env` file created with credentials
- [ ] Dependencies installed (`npm install`)
- [ ] OAuth server running (`node linkedin_oauth_server.js`)
- [ ] Browser opened to http://localhost:3006
- [ ] LinkedIn account connected
- [ ] Test post successful
- [ ] Database file created (`linkedin_users.json`)

---

## Next Steps

1. ✅ Setup complete
2. ⬜ Integrate with AI Employee Vault
3. ⬜ Add more social platforms (Twitter, Facebook, etc.)
4. ⬜ Deploy to production
5. ⬜ Add user authentication
6. ⬜ Upgrade to PostgreSQL

---

## Support

- Full documentation: `LINKEDIN_OAUTH_README.md`
- Architecture details: `OAUTH_SUMMARY.md`
- API reference: `LINKEDIN_OAUTH.md`

**Questions?** Check the troubleshooting section or review the logs:
```bash
# Server logs show what's happening
node linkedin_oauth_server.js
```

---

**🎉 You're ready to go! Open http://localhost:3006 and connect your first LinkedIn account!**
