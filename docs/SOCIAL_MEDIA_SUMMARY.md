# 📱 Social Media Integration - Multi-User OAuth

Complete OAuth system for LinkedIn and Facebook with multi-user support.

---

## Overview

Both systems follow the same pattern:
- ✅ Each user connects their **own** account
- ✅ Posts go to **their** profile/page, not yours
- ✅ OAuth 2.0 authentication
- ✅ Automatic token/URN fetching
- ✅ No hardcoded values
- ✅ Production-ready architecture

---

## Quick Comparison

| Feature | LinkedIn | Facebook |
|---------|----------|----------|
| **Server Port** | 3006 | 3007 |
| **Posts To** | Personal Profile | Facebook Pages |
| **OAuth URL** | `/auth/linkedin` | `/auth/facebook` |
| **Database** | `linkedin_users.json` | `facebook_users.json` |
| **Test Script** | `test_oauth_post.js` | `test_facebook_post.js` |
| **Setup Guide** | `SETUP_LINKEDIN.md` | `FACEBOOK_SETUP.md` |

---

## Start Both Servers

```bash
# LinkedIn OAuth Server (Port 3006)
node linkedin_oauth_server.js

# Facebook OAuth Server (Port 3007)
node facebook_oauth_server.js
```

---

## User Flow (Same for Both)

```
1. User opens web page
   ↓
2. Clicks "Connect [Platform]"
   ↓
3. Authorizes on [Platform]
   ↓
4. Token + ID fetched automatically
   ↓
5. Stored in database
   ↓
6. User can now post!
```

---

## LinkedIn Setup

### 1. Add Redirect URL to LinkedIn App

```
http://localhost:3006/auth/linkedin/callback
```

### 2. Open Browser

```
http://localhost:3006
```

### 3. Connect & Test

```bash
# Connect via browser, then test:
node test_oauth_post.js "Hello LinkedIn!"
```

**Documentation:** `SETUP_LINKEDIN.md`

---

## Facebook Setup

### 1. Create Facebook App

- Go to: https://developers.facebook.com/apps/
- Create app → Add "Facebook Login"
- Add redirect URI:
  ```
  http://localhost:3007/auth/facebook/callback
  ```

### 2. Configure .env

```bash
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
```

### 3. Open Browser

```
http://localhost:3007
```

### 4. Connect & Test

```bash
# Connect via browser, then test:
node test_facebook_post.js "Hello Facebook!"
```

**Documentation:** `FACEBOOK_SETUP.md`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Employee Vault                        │
│                          ↓                                  │
│              Generates content for user                     │
│                          ↓                                  │
│         ┌────────────────┴────────────────┐                │
│         ↓                                  ↓                │
│  LinkedIn OAuth Server           Facebook OAuth Server     │
│  (Port 3006)                     (Port 3007)               │
│         ↓                                  ↓                │
│  linkedin_users.json             facebook_users.json       │
│  - User tokens                   - User tokens             │
│  - URNs (auto-fetched)           - Page IDs                │
│  - Auto refresh                  - Page access tokens      │
│         ↓                                  ↓                │
│  Posts to user's LinkedIn        Posts to user's FB Page   │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Example

### Post to LinkedIn for User

```javascript
// Get user's LinkedIn ID from your database
const linkedinId = getUserLinkedInId(userId);

// Post to their LinkedIn
await axios.post('http://localhost:3006/post', {
    linkedin_id: linkedinId,
    content: 'Generated post content'
});
```

### Post to Facebook for User

```javascript
// Get user's Facebook ID and Page ID
const facebookId = getUserFacebookId(userId);
const pageId = getUserFacebookPageId(userId);

// Post to their Facebook Page
await axios.post('http://localhost:3007/post', {
    facebook_id: facebookId,
    page_id: pageId,
    content: 'Generated post content'
});
```

---

## Database Examples

### LinkedIn User

```json
{
  "id": "user_123",
  "linkedin_id": "koKV_cgelg",
  "urn": "urn:li:person:koKV_cgelg",
  "email": "user@example.com",
  "name": "John Doe",
  "access_token": "AQVm6AwAfKdBD...",
  "refresh_token": "AQV3YnQAq5E4h...",
  "token_expires_at": 1708723200000
}
```

### Facebook User

```json
{
  "id": "user_456",
  "facebook_id": "100012345678901",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "access_token": "EAABsbCS1iHgBO...",
  "pages": [
    {
      "id": "112233445566778",
      "name": "My Business Page",
      "access_token": "EAABsbCS1iHgBO...page_token"
    }
  ]
}
```

---

## Key Points

### ✅ Multi-User Support

Each user has their own token and ID:
- User A connects → Posts to User A's LinkedIn/FB
- User B connects → Posts to User B's LinkedIn/FB
- **No one is connected to your account**

### ✅ Dynamic ID Fetching

- LinkedIn: URN fetched from `/v2/userinfo`
- Facebook: Page IDs fetched from `/me/accounts`
- **No hardcoded IDs**

### ✅ Auto Token Management

- LinkedIn: Auto-refresh before expiry
- Facebook: Long-lived page tokens
- **No manual token updates**

---

## Testing

### Check Server Status

```bash
# LinkedIn
curl http://localhost:3006/health

# Facebook
curl http://localhost:3007/health
```

### List Connected Users

```bash
# LinkedIn
curl http://localhost:3006/users

# Facebook
curl http://localhost:3007/users
```

### Test Posting

```bash
# LinkedIn
node test_oauth_post.js "Hello LinkedIn!"

# Facebook
node test_facebook_post.js "Hello Facebook!"
```

---

## Files Created

| File | Purpose |
|------|---------|
| `linkedin_oauth_server.js` | LinkedIn OAuth server |
| `facebook_oauth_server.js` | Facebook OAuth server |
| `public/index.html` | LinkedIn connect UI |
| `public/facebook.html` | Facebook connect UI |
| `test_oauth_post.js` | LinkedIn test script |
| `test_facebook_post.js` | Facebook test script |
| `linkedin_users.json` | LinkedIn database (auto-created) |
| `facebook_users.json` | Facebook database (auto-created) |

---

## Documentation

| File | Content |
|------|---------|
| `SETUP_LINKEDIN.md` | LinkedIn step-by-step setup |
| `FACEBOOK_SETUP.md` | Facebook step-by-step setup |
| `LINKEDIN_OAUTH_README.md` | LinkedIn API reference |
| `SOCIAL_MEDIA_SUMMARY.md` | This file |

---

## Production Deployment

### 1. Update Redirect URIs

```
LinkedIn: https://yourdomain.com/auth/linkedin/callback
Facebook: https://yourdomain.com/auth/facebook/callback
```

### 2. Use Real Database

Replace JSON files with PostgreSQL/MySQL:

```javascript
// Example with Sequelize
const user = await User.findOne({ where: { linkedin_id } });
```

### 3. Add User Authentication

Require login before connecting social accounts:

```javascript
app.get('/auth/linkedin', requireAuth, (req, res) => {
    // ...
});
```

### 4. App Review (Facebook Only)

Facebook requires app review for production use.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Redirect URI mismatch | Check URI in app settings exactly matches |
| No users connected | Open browser and connect account first |
| Token expired | Reconnect account or check auto-refresh |
| No pages (Facebook) | User must admin at least one Facebook Page |
| Server won't start | Check if port 3006/3007 is already in use |

---

## Summary

Both systems are now ready:

| Platform | Status | Port | Users |
|----------|--------|------|-------|
| LinkedIn | ✅ Ready | 3006 | Multi-user |
| Facebook | ✅ Ready | 3007 | Multi-user |

**Each user connects their own account and posts to their own profile/page!**

---

**🚀 Start both servers and open:**
- LinkedIn: http://localhost:3006
- Facebook: http://localhost:3007
