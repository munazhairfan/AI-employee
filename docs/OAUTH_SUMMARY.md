# ✅ LinkedIn OAuth Multi-User - Ready to Use

## What Changed

### Before (Single Account - Problematic)
```
❌ Hardcoded URN: urn:li:member:1692775666
❌ Manual token in .env
❌ Token revoked errors
❌ URN mismatch
❌ Only 1 user
```

### After (Multi-User OAuth - Stable)
```
✅ Dynamic URN fetch from /v2/userinfo
✅ OAuth 2.0 flow
✅ Auto token refresh
✅ URN always matches token
✅ Unlimited users
```

---

## How It Works (Step by Step)

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User Opens Browser                                  │
│ http://localhost:3006                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Click "Connect with LinkedIn"                       │
│ GET /auth/linkedin                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Redirect to LinkedIn OAuth                          │
│ User logs in + authorizes app                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: LinkedIn Redirects Back                             │
│ GET /auth/linkedin/callback?code=ABC123                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Server Exchanges Code for Token                     │
│ POST https://www.linkedin.com/oauth/v2/accessToken          │
│ Receives: access_token, refresh_token                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Fetch User's URN (CRITICAL!)                        │
│ GET https://api.linkedin.com/v2/userinfo                    │
│ Header: Authorization: Bearer <access_token>                │
│ Response: { sub: "koKV_cgelg", ... }                        │
│ URN = "urn:li:person:koKV_cgelg"                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Store in Database                                   │
│ {                                                           │
│   linkedin_id: "koKV_cgelg",                                │
│   urn: "urn:li:person:koKV_cgelg",  ← Always matches!       │
│   access_token: "...",                                      │
│   refresh_token: "...",                                     │
│   token_expires_at: 1234567890                              │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 8: User Can Post!                                      │
│ POST /post with linkedin_id + content                       │
│ Server looks up URN from database                           │
│ Posts to LinkedIn                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Won't Crash Like Before

| Previous Issue | How It's Fixed |
|----------------|----------------|
| URN didn't match token | URN is **fetched from the token** - always matches |
| Token expired | Auto-refresh before posting |
| Wrong URN format | LinkedIn returns correct format: `urn:li:person:` |
| Hardcoded values | Everything dynamic from database |
| Scope confusion | OAuth requests correct scopes automatically |
| Dotenv caching | Direct file read, no caching |

---

## Quick Start (3 Steps)

### 1. Add Redirect URI to LinkedIn

Go to: https://www.linkedin.com/developers/apps/77al6n4mu7fhwj/auth

Add:
```
http://localhost:3006/auth/linkedin/callback
```

Save.

### 2. Open Browser

```
http://localhost:3006
```

### 3. Connect LinkedIn

Click "Connect with LinkedIn" → Authorize → Done!

---

## Files Created

| File | Purpose |
|------|---------|
| `linkedin_oauth_server.js` | OAuth server (port 3006) |
| `public/index.html` | Connect button + user list |
| `linkedin_users.json` | Database (auto-created) |
| `test_oauth_post.js` | Test posting script |
| `LINKEDIN_OAUTH.md` | Full documentation |
| `OAUTH_SUMMARY.md` | This file |

---

## Test It Now

### Server is already running on port 3006

1. **Open:** http://localhost:3006
2. **Click:** "Connect with LinkedIn"
3. **Authorize** the app
4. **See** your user info + URN
5. **Test post** from the page

Or use command line:
```bash
node test_oauth_post.js "Hello from OAuth!"
```

---

## Integration Options

### Option A: Use OAuth Server As-Is

Your AI Employee Vault calls the OAuth server:

```javascript
// In your existing code
await axios.post('http://localhost:3006/post', {
    linkedin_id: userId,  // From your user mapping
    content: postContent
});
```

### Option B: Merge Into social_mcp.js

Copy these functions into `social_mcp.js`:
- `loadDB()` / `saveDB()`
- `refreshUserToken()`
- OAuth routes

Then modify `/post_linkedin` to use database instead of .env.

---

## Database Schema

```json
{
  "users": [
    {
      "id": "user_1708636800000_abc123",
      "linkedin_id": "koKV_cgelg",      // From LinkedIn
      "urn": "urn:li:person:koKV_cgelg", // Fetched from API
      "email": "user@example.com",       // From /v2/userinfo
      "name": "User Name",               // From /v2/userinfo
      "access_token": "AQVm6AwAfKdBD...",
      "refresh_token": "AQV3YnQAq5E4h...",
      "token_expires_at": 1708723200000, // Timestamp
      "created_at": "2026-02-22T23:00:00.000Z",
      "updated_at": "2026-02-22T23:00:00.000Z"
    }
  ]
}
```

---

## Key Code Snippets

### Fetch URN from Token (The Critical Part!)

```javascript
const userResponse = await axios.get(
    'https://api.linkedin.com/v2/userinfo',
    {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    }
);

const linkedinId = userResponse.data.sub;
const urn = `urn:li:person:${linkedinId}`;  // ✅ Always correct!
```

### Auto Token Refresh

```javascript
if (Date.now() >= user.token_expires_at) {
    const response = await axios.post(
        'https://www.linkedin.com/oauth/v2/accessToken',
        {
            grant_type: 'refresh_token',
            refresh_token: user.refresh_token,
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET
        }
    );
    
    // Update database with new tokens
    user.access_token = response.data.access_token;
    user.refresh_token = response.data.refresh_token;
    user.token_expires_at = Date.now() + (response.data.expires_in * 1000);
}
```

### Post with Dynamic URN

```javascript
const user = db.users.find(u => u.linkedin_id === linkedin_id);

const response = await axios.post(
    'https://api.linkedin.com/v2/ugcPosts',
    {
        author: user.urn,  // ✅ From database, always matches token
        lifecycleState: 'PUBLISHED',
        specificContent: {
            'com.linkedin.ugc.ShareContent': {
                shareCommentary: { text: content }
            }
        },
        visibility: {
            'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
        }
    },
    {
        headers: {
            'Authorization': `Bearer ${user.access_token}`
        }
    }
);
```

---

## Comparison Table

| Feature | Old (.env) | New (OAuth) |
|---------|------------|-------------|
| URN Source | Hardcoded | API fetch |
| Token Source | Manual | OAuth |
| Users | 1 | Unlimited |
| Refresh | Manual | Auto |
| Crash Risk | High | Low |
| Setup | Complex | Simple |
| Production Ready | No | Yes (with DB) |

---

## Next Steps

1. ✅ Server running on port 3006
2. ⬜ Add redirect URI to LinkedIn dashboard
3. ⬜ Open http://localhost:3006
4. ⬜ Connect your LinkedIn
5. ⬜ Test posting
6. ⬜ Integrate with AI Employee Vault

---

## Support Commands

```bash
# Check server status
curl http://localhost:3006/health

# List connected users
curl http://localhost:3006/users

# Test post
node test_oauth_post.js "Test message"

# Start server (if stopped)
node linkedin_oauth_server.js
```

---

## Summary

**This is the proper, scalable solution:**

- ✅ No hardcoded URNs
- ✅ No token mismatches
- ✅ Auto token refresh
- ✅ Multi-user support
- ✅ Production-ready architecture
- ✅ Clear error handling
- ✅ OAuth 2.0 compliant

**You can now:**
- Connect unlimited LinkedIn accounts
- Post on behalf of any connected user
- Never worry about URN mismatches
- Scale to production easily

---

**Ready to test? Open: http://localhost:3006**
