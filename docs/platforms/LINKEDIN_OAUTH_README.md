# LinkedIn OAuth Integration for AI Employee Vault

Multi-user LinkedIn posting system with OAuth 2.0 authentication.

## Features

- ✅ **Multi-user support** - Each user connects their own LinkedIn
- ✅ **OAuth 2.0** - Secure, LinkedIn-approved authentication
- ✅ **Auto token refresh** - Tokens refresh automatically before expiry
- ✅ **Dynamic URN fetching** - No hardcoded values, always matches token
- ✅ **Production ready** - Easy to deploy and scale
- ✅ **Open source friendly** - Clear setup, well documented

---

## Quick Start

### Prerequisites

1. Node.js 16+ installed
2. LinkedIn Developer App created

### 1. Install Dependencies

```bash
npm install express axios dotenv
```

### 2. Configure Environment

Create `.env` file:

```bash
# LinkedIn App Credentials
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret

# Server Port
PORT=3006
```

### 3. Configure LinkedIn App

1. Go to: https://www.linkedin.com/developers/apps
2. Select your app (or create new one)
3. Go to **Auth** tab
4. Add **OAuth 2.0 Redirect URL**:
   ```
   http://localhost:3006/auth/linkedin/callback
   ```
5. Click **Update**

### 4. Start OAuth Server

```bash
node linkedin_oauth_server.js
```

### 5. Connect LinkedIn Account

1. Open: http://localhost:3006
2. Click **"Connect with LinkedIn"**
3. Authorize the application
4. Your account is now connected!

### 6. Test Posting

```bash
node test_oauth_post.js "Hello from AI Employee Vault!"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
│                          ↓                                  │
│              Clicks "Connect LinkedIn"                      │
│                          ↓                                  │
│              Redirects to LinkedIn OAuth                    │
│                          ↓                                  │
│              User authorizes app                            │
│                          ↓                                  │
│              Callback with code                             │
│                          ↓                                  │
│         Server exchanges code → tokens                      │
│                          ↓                                  │
│         Fetches URN from /v2/userinfo                       │
│                          ↓                                  │
│         Stores in database (JSON/SQL)                       │
│                          ↓                                  │
│         User can now post!                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### `GET /`
Home page with "Connect LinkedIn" button and user list.

### `GET /auth/linkedin`
Start OAuth flow. Redirects user to LinkedIn.

**Query params:**
- `user_id` (optional) - Your internal user ID

### `GET /auth/linkedin/callback`
LinkedIn OAuth callback. Handles:
1. Code exchange → access token + refresh token
2. Fetch user info + URN from `/v2/userinfo`
3. Store in database
4. Auto token refresh on future requests

### `POST /post`
Post to LinkedIn on behalf of a user.

**Request:**
```json
{
  "linkedin_id": "koKV_cgelg",
  "content": "Your post content here"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "urn:li:share:7431480073066532864",
  "post_url": "https://www.linkedin.com/feed/update/urn:li:share:7431480073066532864",
  "user": "John Doe"
}
```

### `GET /users`
List all connected users (tokens hidden).

### `GET /health`
Health check endpoint.

---

## Database

### Default (JSON File)

Stored as `linkedin_users.json`:

```json
{
  "users": [
    {
      "id": "user_1708636800000_abc123",
      "linkedin_id": "koKV_cgelg",
      "urn": "urn:li:person:koKV_cgelg",
      "email": "user@example.com",
      "name": "John Doe",
      "access_token": "AQVm6AwAfKdBD...",
      "refresh_token": "AQV3YnQAq5E4h...",
      "token_expires_at": 1708723200000,
      "created_at": "2026-02-22T23:00:00.000Z",
      "updated_at": "2026-02-22T23:00:00.000Z"
    }
  ]
}
```

### Production (PostgreSQL/SQLite)

Replace `loadDB()` and `saveDB()` with database queries:

```javascript
// Example with Sequelize/TypeORM
const user = await User.findOne({ where: { linkedin_id } });
await user.update({ access_token, refresh_token, urn });
```

---

## Integration with AI Employee Vault

### Option 1: HTTP API Call

From your existing code:

```javascript
// Post to LinkedIn
async function postToLinkedIn(userId, content) {
    const response = await axios.post('http://localhost:3006/post', {
        linkedin_id: userId,  // User's LinkedIn ID
        content: content
    });
    
    return response.data.post_url;
}
```

### Option 2: Merge into social_mcp.js

Copy OAuth logic into your existing MCP server and replace `.env` token usage with database lookups.

---

## Token Management

### Automatic Refresh

Tokens refresh automatically before posting:

```javascript
if (Date.now() >= user.token_expires_at) {
    await refreshUserToken(user);
}
```

### Token Lifetimes

| Token | Expires |
|-------|---------|
| Access Token | 60 days |
| Refresh Token | 1 year |

### Manual Token Refresh

```bash
node manual_refresh.js
```

---

## Security

| Feature | Implementation |
|---------|----------------|
| CSRF Protection | State parameter validation |
| Token Storage | JSON file (upgrade to encrypted DB) |
| Scope Limiting | Only necessary permissions requested |
| No Hardcoded Secrets | All from environment variables |

### Production Recommendations

1. **Encrypt refresh tokens** in database
2. **Use HTTPS** for redirect URIs
3. **Add rate limiting** on `/post` endpoint
4. **Implement user authentication** before connecting LinkedIn
5. **Use proper database** (PostgreSQL/MySQL)

---

## Troubleshooting

### "Redirect URI mismatch"

Ensure redirect URI in LinkedIn dashboard **exactly matches**:
```
http://localhost:3006/auth/linkedin/callback
```

### "Invalid state parameter"

State expired or already used. Click "Connect LinkedIn" again.

### "Token expired"

Server auto-refreshes. If refresh fails, user needs to reconnect.

### "ACCESS_DENIED"

User revoked app access. Reconnect LinkedIn account.

### "No users connected yet"

Run `node linkedin_oauth_server.js` and connect via browser first.

---

## Testing

### Check Server Status

```bash
curl http://localhost:3006/health
```

### List Connected Users

```bash
curl http://localhost:3006/users
```

### Test Posting

```bash
node test_oauth_post.js "Test message"
```

### Start Server

```bash
node linkedin_oauth_server.js
```

---

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3006
CMD ["node", "linkedin_oauth_server.js"]
```

### Environment Variables

```bash
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
PORT=3006
NODE_ENV=production
```

### Production Redirect URL

Update for production:
```
https://yourdomain.com/auth/linkedin/callback
```

---

## Files

| File | Purpose |
|------|---------|
| `linkedin_oauth_server.js` | Main OAuth server |
| `public/index.html` | Connect UI |
| `linkedin_users.json` | User database (auto-created) |
| `test_oauth_post.js` | Test posting script |
| `.env.example` | Environment template |

---

## License

MIT License - Feel free to use in your projects!

---

## Support

For issues:
1. Check server logs
2. Verify redirect URI in LinkedIn dashboard
3. Ensure scopes: `r_liteprofile w_member_social email openid`
4. Check `linkedin_users.json` for user data

---

## Credits

Built for AI Employee Vault - Automated document and communication processing pipeline.
