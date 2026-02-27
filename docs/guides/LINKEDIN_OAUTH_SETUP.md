# LinkedIn OAuth Setup Guide

**Time:** 10 minutes

---

## Step 1: Create LinkedIn Developer Account

1. Go to https://www.linkedin.com/developers
2. Sign in with your LinkedIn account
3. Accept developer terms

---

## Step 2: Create LinkedIn App

1. Click **"Create app"**
2. Fill in:
   - **App name:** AI Employee Vault
   - **Company:** Select your company (or create)
   - **Logo:** Upload any image (required)
   - **App description:** Automation tool for LinkedIn posts
3. Click **"Create app"**

---

## Step 3: Get Credentials

1. In your app dashboard, click **"Auth"** tab
2. Copy these values:
   - **Client ID:** `xxxxxxxxxxxx`
   - **Client Secret:** `xxxxxxxxxxxxxxxx`

---

## Step 4: Configure Redirect URL

1. In **Auth** tab, find "OAuth 2.0 Redirect URLs"
2. Add: `http://localhost:3002/auth/linkedin/callback`
3. Click **"Add"**
4. Click **"Update"**

---

## Step 5: Enable Permissions

1. Go to **"Permissions"** tab
2. Request these permissions:
   - `w_member_social` - Post on behalf of user
   - `r_basicprofile` - Read user profile
3. Click **"Request"**
4. Wait for approval (usually instant)

---

## Step 6: Configure .env

Create `servers/.env.linkedin`:

```env
LINKEDIN_CLIENT_ID=paste-your-client-id
LINKEDIN_CLIENT_SECRET=paste-your-client-secret
LINKEDIN_REDIRECT_URI=http://localhost:3002/auth/linkedin/callback
LINKEDIN_PORT=3002
```

---

## Step 7: Install Dependencies

```bash
cd servers
npm install express axios cors dotenv
```

---

## Step 8: Run OAuth Server

```bash
cd servers
node linkedin_oauth_server.js
```

You should see:
```
🔗 LinkedIn OAuth Server running
   Port: 3002
```

---

## Step 9: Test OAuth Flow

### 9.1 Start OAuth

Open browser or use curl:

```bash
curl "http://localhost:3002/auth/linkedin/start?user_id=test-user-1"
```

**Response:**
```json
{
  "success": true,
  "auth_url": "https://www.linkedin.com/oauth/v2/authorization?...",
  "state": "dGVzdC11c2VyLTE6MTIzNDU2Nzg5MA=="
}
```

### 9.2 Authorize

1. Copy the `auth_url` from response
2. Open in browser
3. Sign in to LinkedIn (if not already)
4. Click **"Allow"** to grant permissions

### 9.3 Get Tokens

Browser redirects to:
```
http://localhost:3002/auth/linkedin/callback?code=AQEDxxxxx&state=xxxxx
```

**Response (save these!):**
```json
{
  "success": true,
  "user_id": "test-user-1",
  "access_token": "AQEDxxxxx",
  "expires_in": 3600,
  "urn": "urn:li:person:ABC123"
}
```

---

## ✅ What You Have Now

| Item | Value | Save It |
|------|-------|---------|
| **Access Token** | `AQED...` | ✅ Yes |
| **URN** | `urn:li:person:ABC123` | ✅ Yes |
| **Expires In** | `3600` (1 hour) | ℹ️ Info |

---

## 🧪 Test Posting

Save the tokens, then we'll create a post endpoint to test.

---

## 📋 Next Steps

1. ✅ Run OAuth server
2. ✅ Get access token and URN
3. ⏳ Create post endpoint
4. ⏳ Integrate with orchestrator

---

**Ready to run?** 

```bash
cd servers
node linkedin_oauth_server.js
```

Then follow Step 9!
