# 📘 Facebook OAuth Setup Guide

## Multi-User Facebook Page Posting

---

## Part 1: Create Facebook App

### Step 1: Go to Facebook Developers

Open: **https://developers.facebook.com/apps/**

### Step 2: Create New App

1. Click **"Create App"**
2. Select use case: **"Other"** → **Next**
3. Select app type: **"Business"** → **Next**
4. Fill in:
   - **App Name**: AI Employee Vault (or your app name)
   - **App Contact Email**: your@email.com
5. Click **"Create App"**

### Step 3: Add Facebook Login Product

1. In your app dashboard, find **"Add Products"**
2. Click **"+"** next to **"Facebook Login"**
3. Configure Facebook Login:
   - **Valid OAuth Redirect URIs**: Add this URL
     ```
     http://localhost:3007/auth/facebook/callback
     ```
   - Click **Save**

### Step 4: Get App Credentials

1. Go to **Settings → Basic**
2. Copy these values:
   - **App ID**: `123456789012345`
   - **App Secret**: `abc123def456...`

---

## Part 2: Configure Environment

### Step 1: Copy Environment Template

```bash
cp .env.example .env
```

### Step 2: Add Facebook Credentials

Open `.env` and add:

```bash
# Facebook OAuth
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abc123def456...
```

### Step 3: Install Dependencies

```bash
npm install
```

### Step 4: Start Facebook OAuth Server

```bash
node facebook_oauth_server.js
```

You should see:
```
============================================================
Facebook OAuth Server
============================================================
Server running on http://localhost:3007
...
```

---

## Part 3: Connect Facebook Account

### Step 1: Open Browser

Go to: **http://localhost:3007**

### Step 2: Click Connect Button

Click **"📘 Connect with Facebook"**

### Step 3: Authorize on Facebook

1. Facebook will ask you to sign in
2. Review permissions:
   - ✅ Manage your Pages
   - ✅ View your Pages
   - ✅ Email
3. Click **"Continue"** or **"Allow"**

### Step 4: Select a Page

After authorizing, you'll see:
- Your Facebook profile info
- List of Pages you admin
- Test posting form

**Each page has its own access token!**

---

## Part 4: Test Posting

### Option A: From the Web Page

Use the form on the success page:
1. Select a Page from dropdown
2. Write your post
3. Click "Post to Facebook Page"

### Option B: Command Line

```bash
node test_facebook_post.js "Hello from AI Employee Vault!"
```

### Option C: API Call

```bash
curl -X POST http://localhost:3007/post \
  -H "Content-Type: application/json" \
  -d '{
    "facebook_id": "YOUR_ID",
    "page_id": "PAGE_ID",
    "content": "Test post!"
  }'
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│ User clicks "Connect Facebook"                              │
│     ↓                                                       │
│ Redirects to Facebook OAuth                                 │
│     ↓                                                       │
│ User authorizes app                                         │
│     ↓                                                       │
│ Facebook redirects to /callback with code                   │
│     ↓                                                       │
│ Server exchanges code → access token                        │
│     ↓                                                       │
│ Server fetches user profile + pages                         │
│     ↓                                                       │
│ Store in database: { token, pages[], page_access_tokens }   │
│     ↓                                                       │
│ User can now post to their Pages!                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Difference from LinkedIn

| LinkedIn | Facebook |
|----------|----------|
| Posts to personal profile | Posts to **Facebook Pages** |
| URN: `urn:li:person:xxx` | Page ID: `123456789` |
| One token per user | One **page access token** per Page |
| Personal profile posting | Business Page posting |

**Important:** You must admin at least one Facebook Page to use this!

---

## Database Structure

Stored in `facebook_users.json`:

```json
{
  "users": [
    {
      "id": "user_1708636800000_abc123",
      "facebook_id": "100012345678901",
      "name": "John Doe",
      "email": "john@example.com",
      "access_token": "EAABsbCS1iHgBO...",
      "pages": [
        {
          "id": "112233445566778",
          "name": "My Business Page",
          "access_token": "EAABsbCS1iHgBO...page_token"
        }
      ],
      "created_at": "2026-02-23T...",
      "updated_at": "2026-02-23T..."
    }
  ]
}
```

---

## API Endpoints

### `GET /auth/facebook`
Start OAuth flow.

### `GET /auth/facebook/callback`
Facebook OAuth callback.

### `POST /post`
Post to Facebook Page.

**Body:**
```json
{
  "facebook_id": "100012345678901",
  "page_id": "112233445566778",
  "content": "Your post content"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "112233445566778_987654321",
  "post_url": "https://www.facebook.com/112233445566778_987654321",
  "page": "My Business Page",
  "user": "John Doe"
}
```

### `GET /users`
List connected users and their Pages.

### `GET /health`
Health check.

---

## Required Facebook Permissions

| Permission | Purpose |
|------------|---------|
| `pages_manage_posts` | Create posts on Pages |
| `pages_read_engagement` | View Page engagement |
| `pages_show_list` | List Pages user admins |
| `email` | Get user's email |

---

## Troubleshooting

### ❌ "Redirect URI mismatch"

**Fix:** Add exact URL to Facebook app:
```
http://localhost:3007/auth/facebook/callback
```

### ❌ "No pages found"

**Reason:** You don't admin any Facebook Pages

**Fix:** 
1. Create a Facebook Page: https://www.facebook.com/pages/create
2. Or use a Page where you're an admin

### ❌ "Permissions not granted"

**Fix:** 
1. Go to Facebook app settings
2. Make sure all required permissions are added
3. Re-authorize the app

### ❌ "Token expired"

Facebook page access tokens are long-lived but can expire.

**Fix:** User needs to reconnect their Facebook account.

---

## Testing Commands

```bash
# Check server status
curl http://localhost:3007/health

# List connected users
curl http://localhost:3007/users

# Start server
node facebook_oauth_server.js
```

---

## Integration with AI Employee Vault

```javascript
// Post to user's Facebook Page
async function postToFacebook(userId, pageId, content) {
    const response = await axios.post('http://localhost:3007/post', {
        facebook_id: userId,      // User's Facebook ID
        page_id: pageId,          // Page ID to post to
        content: content
    });
    
    return response.data.post_url;
}
```

---

## Production Deployment

### 1. Update Redirect URI

For production:
```
https://yourdomain.com/auth/facebook/callback
```

### 2. App Review

Facebook requires **App Review** for production use:

1. Go to **App Review** in Facebook Developer dashboard
2. Submit each permission for review
3. Provide screencast showing how you use the permissions
4. Wait for approval (can take days/weeks)

### 3. Use HTTPS

Facebook requires HTTPS for production.

### 4. Upgrade Database

Replace JSON file with PostgreSQL/MySQL for production.

---

## Summary

| Feature | Facebook OAuth |
|---------|----------------|
| Posts to | Facebook Pages |
| Auth | OAuth 2.0 |
| Multi-user | ✅ Yes |
| Auto token refresh | ⚠️ Page tokens are long-lived |
| App Review Required | ✅ For production |
| Personal Profile Posting | ❌ No (Facebook limitation) |

---

**🎉 Ready! Open http://localhost:3007 and connect your Facebook account!**
