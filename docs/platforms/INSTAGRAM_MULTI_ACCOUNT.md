# Instagram Multi-Account Support

## Status: ✅ COMPLETE

---

## How Multi-Account Works

Each account uses a **separate browser session**:

```
Account: "personal"  →  instagram_session_personal/
Account: "business"  →  instagram_session_business/
Account: "default"   →  instagram_session_default/
```

---

## Usage

### Post to Default Account

```bash
python watchers/instagram_poster.py "Caption" "image.jpg"
# Uses: instagram_session_default/
```

### Post to Business Account

```bash
python watchers/instagram_poster.py "Business update" "pic.jpg" "business"
# Uses: instagram_session_business/
```

### Post to Personal Account

```bash
python watchers/instagram_poster.py "My day" "selfie.jpg" "personal"
# Uses: instagram_session_personal/
```

---

## First Time Setup Per Account

### Account 1: Personal

```bash
python watchers/instagram_poster.py "Test" "image.jpg" "personal"
```

1. Browser opens
2. **Log in with personal account**
3. Session saved to `instagram_session_personal/`
4. Future posts auto-login

### Account 2: Business

```bash
python watchers/instagram_poster.py "Test" "image.jpg" "business"
```

1. Browser opens (new session)
2. **Log in with business account**
3. Session saved to `instagram_session_business/`
4. Future posts auto-login

---

## Via MCP Server

### Post to Default Account

```bash
curl -X POST http://localhost:3005/post_instagram \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Great post!",
    "image_path": "C:/path/to/image.jpg"
  }'
```

### Post to Specific Account

```bash
curl -X POST http://localhost:3005/post_instagram \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Business update",
    "image_path": "C:/path/to/image.jpg",
    "account_name": "business"
  }'
```

---

## Managing Accounts

### List All Accounts

```bash
dir instagram_session_*
```

Shows all account sessions:
```
instagram_session_personal/
instagram_session_business/
instagram_session_default/
```

### Delete an Account Session

```bash
# Delete business account session
rmdir /s instagram_session_business
```

Next post to "business" will require login again.

---

## Use Cases

### Social Media Agency

Manage multiple client accounts:

```bash
# Client 1
python instagram_poster.py "Client 1 post" "client1.jpg" "client1"

# Client 2
python instagram_poster.py "Client 2 post" "client2.jpg" "client2"

# Client 3
python instagram_poster.py "Client 3 post" "client3.jpg" "client3"
```

### Personal + Business

```bash
# Personal posts
python instagram_poster.py "Weekend vibes" "fun.jpg" "personal"

# Business posts
python instagram_poster.py "New product launch" "product.jpg" "business"
```

---

## Integration with AI Employee Vault

### Draft for Specific Account

In `Pending_Approval/Instagram_Draft.md`:

```markdown
---
type: instagram_draft
account: business
---

# Instagram Post Draft

**Account:** Business

**Caption:** New product launching soon!

**Image:** /path/to/product.jpg
```

### Orchestrator Posts to Correct Account

```python
# Extract account from draft
account = metadata.get('account', 'default')

# Call MCP with account
requests.post('http://localhost:3005/post_instagram', json={
    'content': caption,
    'image_path': image,
    'account_name': account
})
```

---

## Session Storage

| Account | Session Folder | Created |
|---------|----------------|---------|
| default | `instagram_session_default/` | First post |
| personal | `instagram_session_personal/` | First post |
| business | `instagram_session_business/` | First post |
| client1 | `instagram_session_client1/` | First post |

**Sessions persist** across reboots, browser updates, etc.

---

## Security

### Session Safety

- ✅ Sessions stored locally
- ✅ No passwords saved in code
- ✅ Each account isolated
- ✅ No API keys needed

### Best Practices

1. **Don't share session folders** - Contains login cookies
2. **Use account names carefully** - "client1" not "Client Name"
3. **Logout properly** - Delete session folder to logout

---

## Troubleshooting

### Wrong Account Posted

Check account name in command:
```bash
# Wrong - posts to default
python instagram_poster.py "Post" "img.jpg"

# Correct - posts to business
python instagram_poster.py "Post" "img.jpg" "business"
```

### Session Corrupted

Delete and re-login:
```bash
rmdir /s instagram_session_business
python instagram_poster.py "Test" "img.jpg" "business"
# Log in again
```

### Too Many Accounts

List and clean up:
```bash
dir instagram_session_*
rmdir /s instagram_session_oldclient
```

---

## Summary

**✅ Instagram Multi-Account: COMPLETE**

- ✅ Separate sessions per account
- ✅ Auto-login for all accounts
- ✅ MCP integration supports accounts
- ✅ Orchestrator can specify account
- ✅ 100% FREE - No API keys

**Post to unlimited accounts from one script!**

---

**🎉 Instagram multi-account support is ready!**
