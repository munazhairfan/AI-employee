# LinkedIn OAuth Multi-User Setup

## Overview

This is **Option B** - Multi-user OAuth flow where each user connects their own LinkedIn account.

## Why This Is Better

| Problem Before | Solution Now |
|----------------|--------------|
| Hardcoded URN mismatch | URN fetched dynamically from token |
| Token revoked errors | Fresh tokens via OAuth |
| Single account only | Multiple users supported |
| Manual token generation | Automatic OAuth flow |
| Confusing scope errors | Correct scopes requested automatically |

---

## Quick Start

### 1. Add Redirect URI to LinkedIn App

Go to: `https://www.linkedin.com/developers/apps/77al6n4mu7fhwj/auth`

Add this **OAuth 2.0 Redirect URL**:
```
http://localhost:3006/auth/linkedin/callback
```

Click **Update** to save.

### 2. Start the OAuth Server

```bash
node linkedin_oauth_server.js
```

### 3. Open in Browser

```
http://localhost:3006
```

### 4. Connect LinkedIn Account

1. Click **"Connect with LinkedIn"**
2. Authorize the application
3. You'll see your user info and URN
4. Test posting directly from the page

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User clicks "Connect LinkedIn"                             │
│     ↓                                                       │
│  Redirect to LinkedIn OAuth                                 │
│     ↓                                                       │
│  User authorizes app                                        │
│     ↓                                                       │
│  LinkedIn redirects to /callback with code                  │
│     ↓                                                       │
│  Server exchanges code → access token + refresh token       │
│     ↓                                                       │
│  Server calls /v2/userinfo → gets URN                       │
│     ↓                                                       │
│  Store in database: { token, refresh_token, urn, email }    │
│     ↓                                                       │
│  User can now post!                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Structure

Stored in `linkedin_users.json`:

```json
{
  "users": [
    {
      "id": "user_1708636800000_abc123",
      "linkedin_id": "koKV_cgelg",
      "urn": "urn:li:person:koKV_cgelg",
      "email": "user@example.com",
      "name": "User Name",
      "access_token": "AQVm6AwAfKdBD...",
      "refresh_token": "AQV3YnQAq5E4h...",
      "token_expires_at": 1708723200000,
      "created_at": "2026-02-22T23:00:00.000Z",
      "updated_at": "2026-02-22T23:00:00.000Z"
    }
  ]
}
```

---

## API Endpoints

### `GET /auth/linkedin`
Start OAuth flow. Redirects user to LinkedIn.

**Optional query param:** `?user_id=123` (your internal user ID)

### `GET /auth/linkedin/callback`
LinkedIn redirects here with `code` parameter.

Server automatically:
1. Exchanges code for tokens
2. Fetches user's URN
3. Stores in database
4. Shows success page

### `POST /post`
Post to LinkedIn on behalf of a user.

**Body:**
```json
{
  "linkedin_id": "koKV_cgelg",
  "content": "Hello LinkedIn!"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "urn:li:share:7431480073066532864",
  "post_url": "https://www.linkedin.com/feed/update/urn:li:share:7431480073066532864",
  "user": "User Name"
}
```

### `GET /users`
List all connected users (tokens hidden for security).

### `GET /health`
Health check endpoint.

---

## Token Management

### Automatic Refresh

When a user's token is expired, the server automatically refreshes it:

```javascript
if (Date.now() >= user.token_expires_at) {
    await refreshUserToken(user);
}
```

### Token Lifetimes

| Token Type | Expires |
|------------|---------|
| Access Token | 60 days |
| Refresh Token | 1 year |

---

## Integration with AI Employee Vault

To integrate with your existing social MCP server:

### Option 1: Call OAuth Server Directly

```javascript
// In your AI Employee Vault
const response = await axios.post('http://localhost:3006/post', {
    linkedin_id: 'koKV_cgelg',  // Get from your user mapping
    content: 'Post content here'
});
```

### Option 2: Merge with social_mcp.js

Copy the OAuth logic into `social_mcp.js` and use the same database.

---

## Security Features

| Feature | Purpose |
|---------|---------|
| CSRF State Parameter | Prevents cross-site request forgery |
| Secure Token Storage | Tokens in JSON file (upgrade to encrypted DB) |
| No Hardcoded Secrets | Everything from .env |
| Token Auto-Refresh | No manual intervention needed |
| Scope Validation | Only requests necessary permissions |

---

## Upgrading to Production

### 1. Use Real Database

Replace JSON file with SQLite/PostgreSQL:

```javascript
// Instead of fs.readFileSync
const user = await db.users.findOne({ where: { linkedin_id } });
```

### 2. Add User Authentication

Require login before connecting LinkedIn:

```javascript
app.get('/auth/linkedin', requireAuth, (req, res) => {
    // ...
});
```

### 3. Use HTTPS

LinkedIn requires HTTPS for production redirect URIs.

### 4. Store Refresh Token Securely

Encrypt refresh tokens in database:

```javascript
const encrypted = encrypt(refreshToken, process.env.ENCRYPTION_KEY);
```

### 5. Add Rate Limiting

Prevent abuse:

```javascript
const rateLimit = require('express-rate-limit');
app.use('/post', rateLimit({ windowMs: 60000, max: 10 }));
```

---

## Troubleshooting

### "Redirect URI mismatch"

Make sure the redirect URI in LinkedIn dashboard **exactly matches**:
```
http://localhost:3006/auth/linkedin/callback
```

### "Invalid state parameter"

State expired or was already used. Click "Connect LinkedIn" again.

### "Token expired"

Server should auto-refresh. If refresh fails, user needs to reconnect.

### "ACCESS_DENIED"

User revoked app access. Reconnect LinkedIn account.

---

## Testing

### Test OAuth Flow

1. Start server: `node linkedin_oauth_server.js`
2. Open: `http://localhost:3006`
3. Click "Connect with LinkedIn"
4. Authorize
5. Check `linkedin_users.json` for stored data

### Test Posting

From the success page, use the form to post.

Or use curl:
```bash
curl -X POST http://localhost:3006/post \
  -H "Content-Type: application/json" \
  -d '{"linkedin_id":"koKV_cgelg","content":"Test post!"}'
```

### Check Connected Users

```bash
curl http://localhost:3006/users
```

---

## Comparison: Single vs Multi-User

| Feature | Single (.env) | Multi-User (OAuth) |
|---------|---------------|-------------------|
| Setup | Manual token | Automatic OAuth |
| URN Source | Hardcoded | Fetched from API |
| Users | 1 | Unlimited |
| Token Refresh | Manual | Automatic |
| Best For | Personal automation | SaaS / Products |

---

## Next Steps

1. ✅ Add redirect URI to LinkedIn app
2. ✅ Start OAuth server
3. ✅ Connect your LinkedIn account
4. ✅ Test posting
5. ⬜ Integrate with AI Employee Vault
6. ⬜ Add user authentication
7. ⬜ Upgrade to production database

---

## Support

For issues:
1. Check server logs
2. Verify redirect URI in LinkedIn dashboard
3. Ensure scopes are correct: `r_liteprofile w_member_social email openid`
4. Check `linkedin_users.json` for stored data
