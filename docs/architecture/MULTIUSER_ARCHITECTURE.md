# Multi-User Architecture Plan - WhatsApp & Email

## Executive Summary

This document outlines the architecture for adding **multi-user support** to WhatsApp and Email (Gmail) platforms, matching the existing multi-user capabilities of LinkedIn and Facebook.

---

## Current Status

| Platform | Multi-User | Architecture |
|----------|------------|--------------|
| LinkedIn | ✅ Yes | OAuth 2.0 + User DB |
| Facebook | ✅ Yes | OAuth 2.0 + User DB |
| WhatsApp | ❌ No | Single session (WhatsApp Web) |
| Email (Gmail) | ❌ No | Single account (.env credentials) |

---

## Target Architecture

### Unified Multi-User Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MULTI-USER ARCHITECTURE                           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    OAuth Server (port 3006/3007)                  │   │
│  │                                                                   │   │
│  │  /auth/whatsapp/start    → Initiate WhatsApp Web QR scan         │   │
│  │  /auth/whatsapp/callback → Store session after QR scan           │   │
│  │  /auth/email/start       → Gmail OAuth 2.0 flow                  │   │
│  │  /auth/email/callback    → Store tokens                          │   │
│  │                                                                   │   │
│  │  Database: users.db                                               │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │ id │ platform │ user_id │ email/phone │ tokens │ session  │  │   │
│  │  ├────────────────────────────────────────────────────────────┤  │   │
│  │  │ 1  │ whatsapp │ uuid-1  │ +1234567890  │ {...}  │ active   │  │   │
│  │  │ 2  │ email    │ uuid-2  │ user@gmail.com │ {...} │ refreshed│  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Server (port 3005/3006)                    │   │
│  │                                                                   │   │
│  │  POST /send_whatsapp                                              │   │
│  │    Input: { user_id, phone, message }                            │   │
│  │    → Lookup user's WhatsApp session                              │   │
│  │    → Send via their session                                      │   │
│  │                                                                   │   │
│  │  POST /send_email                                                 │   │
│  │    Input: { user_id, to, subject, body }                         │   │
│  │    → Lookup user's Gmail tokens                                  │   │
│  │    → Send via their OAuth tokens                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Session Storage                                │   │
│  │                                                                   │   │
│  │  data/whatsapp_sessions/                                          │   │
│  │  ├── session_uuid-1.json  (WhatsApp Web cookies)                 │   │
│  │  ├── session_uuid-2.json                                         │   │
│  │  └── ...                                                         │   │
│  │                                                                   │   │
│  │  data/email_tokens/                                               │   │
│  │  ├── uuid-1.json  (Gmail OAuth tokens)                           │   │
│  │  ├── uuid-2.json                                                 │   │
│  │  └── ...                                                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: WhatsApp Multi-User (Estimated: 4-6 hours)

#### 1.1 Database Schema

```sql
CREATE TABLE whatsapp_users (
    id TEXT PRIMARY KEY,
    phone_number TEXT UNIQUE NOT NULL,
    display_name TEXT,
    session_path TEXT,
    status TEXT DEFAULT 'pending',  -- pending, active, expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);
```

#### 1.2 WhatsApp OAuth Server (`servers/whatsapp_oauth_server.js`)

```javascript
const express = require('express');
const { Client } = require('whatsapp-web.js');
const Database = require('better-sqlite3');
const QRCode = require('qrcode');

const app = express();
const PORT = 3008;
const db = new Database('data/whatsapp_users.db');

// Initialize database
db.exec(`
    CREATE TABLE IF NOT EXISTS whatsapp_users (
        id TEXT PRIMARY KEY,
        phone_number TEXT UNIQUE NOT NULL,
        display_name TEXT,
        session_path TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP
    )
`);

// Start OAuth flow - generate unique session ID
app.get('/auth/whatsapp/start', async (req, res) => {
    const userId = generateUUID();
    
    // Create new WhatsApp client with unique session
    const client = new Client({
        puppeteer: {
            userDataDir: `data/whatsapp_sessions/session_${userId}`
        }
    });
    
    client.on('qr', async (qr) => {
        // Generate QR code image for user to scan
        const qrImage = await QRCode.toDataURL(qr);
        res.json({ 
            user_id: userId, 
            qr_code: qrImage,
            status: 'scanning'
        });
    });
    
    client.on('ready', () => {
        // Save to database
        const userInfo = client.info;
        db.prepare(`
            INSERT OR REPLACE INTO whatsapp_users 
            (id, phone_number, display_name, session_path, status)
            VALUES (?, ?, ?, ?, 'active')
        `).run(userId, userInfo.wid.user, userInfo.pushname, 
               `data/whatsapp_sessions/session_${userId}`);
        
        client.destroy(); // Close connection after saving
    });
    
    client.initialize();
});

// Check authentication status
app.get('/auth/whatsapp/status/:user_id', (req, res) => {
    const { user_id } = req.params;
    const user = db.prepare('SELECT * FROM whatsapp_users WHERE id = ?').get(user_id);
    
    if (!user) {
        return res.json({ status: 'not_found' });
    }
    
    res.json({
        status: user.status,
        phone_number: user.phone_number,
        display_name: user.display_name
    });
});

// List all connected users
app.get('/auth/whatsapp/users', (req, res) => {
    const users = db.prepare('SELECT * FROM whatsapp_users WHERE status = "active"').all();
    res.json(users);
});

app.listen(PORT, () => {
    console.log(`WhatsApp OAuth server running on port ${PORT}`);
});
```

#### 1.3 Updated WhatsApp MCP (`servers/whatsapp_mcp.js`)

```javascript
const express = require('express');
const { Client } = require('whatsapp-web.js');
const Database = require('better-sqlite3');

const app = express();
const PORT = 3006;
const db = new Database('data/whatsapp_users.db');

// Session cache (in-memory for active sessions)
const sessions = new Map();

// Get or create WhatsApp client for user
function getClientForUser(userId) {
    if (sessions.has(userId)) {
        return sessions.get(userId);
    }
    
    const user = db.prepare('SELECT * FROM whatsapp_users WHERE id = ? AND status = "active"').get(userId);
    if (!user) {
        throw new Error('User not found or not active');
    }
    
    const client = new Client({
        puppeteer: {
            userDataDir: user.session_path
        }
    });
    
    client.initialize();
    sessions.set(userId, client);
    
    // Cleanup after 5 minutes of inactivity
    setTimeout(() => {
        client.destroy();
        sessions.delete(userId);
    }, 5 * 60 * 1000);
    
    return client;
}

// Send WhatsApp message
app.post('/send_message', async (req, res) => {
    const { user_id, phone, message } = req.body;
    
    try {
        const client = getClientForUser(user_id);
        
        // Format phone number
        const chatId = `${phone.replace(/\D/g, '')}@c.us`;
        
        // Send message
        const result = await client.sendMessage(chatId, message);
        
        res.json({
            success: true,
            message_id: result.id._serialized,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get user's WhatsApp info
app.get('/user/:user_id/info', (req, res) => {
    const { user_id } = req.params;
    const user = db.prepare('SELECT * FROM whatsapp_users WHERE id = ?').get(user_id);
    
    if (!user) {
        return res.status(404).json({ error: 'User not found' });
    }
    
    res.json(user);
});

app.listen(PORT, () => {
    console.log(`WhatsApp MCP server running on port ${PORT}`);
});
```

#### 1.4 Updated Orchestrator Integration

```python
# In orchestrator.py - WhatsApp draft generation

def generate_whatsapp_draft(file_path: Path) -> None:
    """Generate WhatsApp draft with user selection."""
    
    # Get available WhatsApp users
    response = requests.get('http://localhost:3008/auth/whatsapp/users')
    users = response.json()
    
    # Create draft with user selection
    draft = f"""# WhatsApp Message Draft

**Available Senders:**
{chr(10).join([f"- {u['id']}: {u['display_name']} ({u['phone_number']})" for u in users])}

**Recipient:** {extract_phone(file_path)}
**Message:** {extract_message(file_path)}

**Action Required:**
1. Choose sender user_id from above
2. Run: node scripts/send_whatsapp.py --user <user_id> --draft <draft_file>
"""
    
    # Save draft to Pending_Approval/
```

---

### Phase 2: Email (Gmail) Multi-User (Estimated: 4-6 hours)

#### 2.1 Database Schema

```sql
CREATE TABLE email_users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);
```

#### 2.2 Email OAuth Server (`servers/email_oauth_server.js`)

```javascript
const express = require('express');
const { google } = require('googleapis');
const Database = require('better-sqlite3');
const open = require('open');

const app = express();
const PORT = 3009;
const db = new Database('data/email_users.db');

// Initialize database
db.exec(`
    CREATE TABLE IF NOT EXISTS email_users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        display_name TEXT,
        access_token TEXT,
        refresh_token TEXT,
        token_expiry TIMESTAMP,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP
    )
`);

// OAuth2 client setup
const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    'http://localhost:3009/auth/email/callback'
);

// Start OAuth flow
app.get('/auth/email/start', (req, res) => {
    const userId = generateUUID();
    
    const authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: ['https://www.googleapis.com/auth/gmail.send'],
        state: userId,
        prompt: 'consent'
    });
    
    // Open browser for user to authorize
    open(authUrl);
    
    res.json({
        user_id: userId,
        auth_url: authUrl,
        status: 'authorizing'
    });
});

// OAuth callback
app.get('/auth/email/callback', async (req, res) => {
    const { code, state } = req.query;
    
    try {
        const { tokens } = await oauth2Client.getToken(code);
        
        // Get user info
        oauth2Client.setCredentials(tokens);
        const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
        const profile = await gmail.users.getProfile({ userId: 'me' });
        
        // Save to database
        db.prepare(`
            INSERT OR REPLACE INTO email_users 
            (id, email, display_name, access_token, refresh_token, token_expiry, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        `).run(
            state,
            profile.data.emailAddress,
            profile.data.displayName,
            tokens.access_token,
            tokens.refresh_token,
            new Date(tokens.expiry_date)
        );
        
        res.send(`
            <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>Email: ${profile.data.emailAddress}</p>
                    <p>You can close this window.</p>
                </body>
            </html>
        `);
    } catch (error) {
        res.status(500).send(`Authorization failed: ${error.message}`);
    }
});

// Refresh token
app.post('/auth/email/refresh/:user_id', (req, res) => {
    const { user_id } = req.params;
    const user = db.prepare('SELECT * FROM email_users WHERE id = ?').get(user_id);
    
    if (!user || !user.refresh_token) {
        return res.status(404).json({ error: 'User not found' });
    }
    
    oauth2Client.setCredentials({
        refresh_token: user.refresh_token
    });
    
    oauth2Client.refreshAccessToken((err, tokens) => {
        if (err) {
            return res.status(500).json({ error: err.message });
        }
        
        // Update database
        db.prepare(`
            UPDATE email_users 
            SET access_token = ?, token_expiry = ?
            WHERE id = ?
        `).run(tokens.access_token, new Date(tokens.expiry_date), user_id);
        
        res.json({ status: 'refreshed' });
    });
});

// List all connected users
app.get('/auth/email/users', (req, res) => {
    const users = db.prepare(`
        SELECT id, email, display_name, status, last_used 
        FROM email_users 
        WHERE status = 'active'
    `).all();
    res.json(users);
});

app.listen(PORT, () => {
    console.log(`Email OAuth server running on port ${PORT}`);
});
```

#### 2.3 Updated Email MCP (`servers/mcp_server.js`)

```javascript
const express = require('express');
const { google } = require('googleapis');
const Database = require('better-sqlite3');

const app = express();
const PORT = 3000;
const db = new Database('data/email_users.db');

// Get OAuth2 client for user
function getOAuthClient(userId) {
    const user = db.prepare('SELECT * FROM email_users WHERE id = ?').get(userId);
    
    if (!user) {
        throw new Error('User not found');
    }
    
    const oauth2Client = new google.auth.OAuth2(
        process.env.GOOGLE_CLIENT_ID,
        process.env.GOOGLE_CLIENT_SECRET
    );
    
    oauth2Client.setCredentials({
        access_token: user.access_token,
        refresh_token: user.refresh_token
    });
    
    return oauth2Client;
}

// Send email
app.post('/send_email', async (req, res) => {
    const { user_id, to, subject, body, cc, bcc } = req.body;
    
    try {
        const auth = getOAuthClient(user_id);
        const gmail = google.gmail({ version: 'v1', auth });
        
        // Create message
        const message = createMessage(to, subject, body, cc, bcc);
        
        // Send
        const result = await gmail.users.messages.send({
            userId: 'me',
            requestBody: message
        });
        
        res.json({
            success: true,
            message_id: result.data.id,
            thread_id: result.data.threadId
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// List user's emails
app.get('/user/:user_id/emails', async (req, res) => {
    const { user_id } = req.params;
    
    try {
        const auth = getOAuthClient(user_id);
        const gmail = google.gmail({ version: 'v1', auth });
        
        const result = await gmail.users.messages.list({
            userId: 'me',
            maxResults: 10
        });
        
        res.json(result.data.messages);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Email MCP server running on port ${PORT}`);
});
```

---

## Updated Vault Structure

```
data/
├── whatsapp_users.db          # WhatsApp user database
├── email_users.db             # Email user database
├── whatsapp_sessions/
│   ├── session_uuid-1/
│   ├── session_uuid-2/
│   └── ...
└── email_tokens/
    ├── uuid-1.json
    ├── uuid-2.json
    └── ...
```

---

## Updated .env Configuration

```bash
# ============================================================
# Multi-User OAuth Configuration
# ============================================================

# Google OAuth (for Gmail multi-user)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret

# WhatsApp (no API keys needed - uses QR code auth)

# Legacy single-user (for backward compatibility)
EMAIL_USER=legacy@gmail.com
EMAIL_PASS=legacy-app-password
USE_WHATSAPP_WEB=true
```

---

## API Endpoints Summary

### WhatsApp OAuth Server (port 3008)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/whatsapp/start` | GET | Start QR authentication |
| `/auth/whatsapp/status/:user_id` | GET | Check auth status |
| `/auth/whatsapp/users` | GET | List connected users |

### Email OAuth Server (port 3009)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/email/start` | GET | Start OAuth flow |
| `/auth/email/callback` | GET | OAuth callback |
| `/auth/email/refresh/:user_id` | POST | Refresh tokens |
| `/auth/email/users` | GET | List connected users |

### Updated MCP Servers

| Server | New Endpoint | Purpose |
|--------|--------------|---------|
| WhatsApp MCP | `GET /user/:user_id/info` | Get user info |
| Email MCP | `GET /user/:user_id/emails` | List user's emails |

---

## Migration Path

### For Existing Single-User Setup

1. **Keep backward compatibility** - Single-user .env credentials still work
2. **Auto-migrate on first run** - Create default user from .env
3. **Gradual transition** - Users can connect via OAuth while legacy continues

```python
# In orchestrator.py - backward compatibility

def get_email_user(user_id=None):
    """Get email user, with fallback to legacy."""
    
    if user_id:
        return db.get_user(user_id)
    
    # Fallback to legacy
    if os.getenv('EMAIL_USER'):
        return {
            'id': 'legacy',
            'email': os.getenv('EMAIL_USER'),
            'type': 'legacy'
        }
    
    raise Exception('No email user configured')
```

---

## Testing Checklist

### WhatsApp Multi-User

- [ ] Connect first user via QR code
- [ ] Connect second user via QR code
- [ ] Send message from user 1
- [ ] Send message from user 2
- [ ] Verify sessions persist after restart
- [ ] Test session cleanup (inactive users)
- [ ] Test token refresh

### Email Multi-User

- [ ] Connect first Gmail account
- [ ] Connect second Gmail account
- [ ] Send email from account 1
- [ ] Send email from account 2
- [ ] Verify token refresh works
- [ ] Test with expired tokens

---

## Security Considerations

1. **Session Encryption** - Encrypt stored session data
2. **Access Control** - Require API key for MCP endpoints
3. **Rate Limiting** - Prevent abuse (max 100 messages/hour per user)
4. **Audit Logging** - Log all send actions with user_id
5. **Session Expiry** - Auto-logout after 30 days inactivity

---

## Estimated Timeline

| Phase | Task | Time |
|-------|------|------|
| 1 | WhatsApp OAuth server | 2-3 hours |
| 1 | WhatsApp MCP updates | 1-2 hours |
| 1 | Orchestrator integration | 1 hour |
| 2 | Email OAuth server | 2-3 hours |
| 2 | Email MCP updates | 1-2 hours |
| 2 | Orchestrator integration | 1 hour |
| Both | Testing & documentation | 2-3 hours |
| **Total** | | **10-15 hours** |

---

## Dependencies to Add

```json
{
  "dependencies": {
    "whatsapp-web.js": "^1.26.0",
    "qrcode": "^1.5.3",
    "better-sqlite3": "^9.4.3",
    "googleapis": "^133.0.0",
    "open": "^10.0.0"
  }
}
```

```txt
# requirements.txt
whatsapp-web.py>=0.1.0
better-sqlite3>=9.0.0
```

---

## Next Steps

1. **Review and approve architecture**
2. **Install new dependencies**
3. **Implement WhatsApp OAuth server**
4. **Test WhatsApp multi-user**
5. **Implement Email OAuth server**
6. **Test Email multi-user**
7. **Update orchestrator for both**
8. **Full integration testing**
9. **Update documentation**

---

*Last Updated: 2026-02-26*
*Version: 1.0*
