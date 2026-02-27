# ✅ Instagram Integration - Official API (COMPLETE)

## Status: ✅ READY (Using Official Instagram Graph API)

---

## What Changed

### Before (Browser Automation)
- ❌ Unreliable
- ❌ Kept failing
- ❌ Instagram detected automation
- ❌ UI selectors kept breaking

### After (Official API)
- ✅ Reliable
- ✅ Official method
- ✅ Won't get blocked
- ✅ Stable API

---

## Setup Summary

### Requirements

1. **Instagram Business or Creator Account** (free to convert)
2. **Facebook Page** connected to Instagram
3. **Facebook App** with Instagram permissions
4. **Page Access Token** with instagram_content_publish permission

### Quick Setup (15 minutes)

1. **Convert Instagram to Business** (2 min)
   - Instagram Settings → Account → Switch to Professional

2. **Connect to Facebook Page** (2 min)
   - Facebook Page Settings → Instagram → Connect

3. **Add Instagram to Facebook App** (3 min)
   - Developers → Your App → Add Products
   - Add: Instagram Basic Display + Instagram Graph API

4. **Get Access Token** (5 min)
   - Graph API Explorer → Get Token
   - Permissions: instagram_basic, instagram_content_publish
   - Copy token

5. **Get Instagram User ID** (3 min)
   ```bash
   python setup_instagram.py
   ```

6. **Add to .env** (1 min)
   ```bash
   INSTAGRAM_BUSINESS_USER_ID=17841400000000000
   INSTAGRAM_ACCESS_TOKEN=EAAB...
   ```

---

## How to Post

### Post via MCP Server

```bash
curl -X POST http://localhost:3005/post_instagram \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your caption",
    "image_url": "https://i.imgur.com/your-image.jpg"
  }'
```

### Post via Python

```bash
python watchers/instagram_poster_api.py "Caption" "https://i.imgur.com/image.jpg"
```

### Full AI Employee Vault Flow

1. Orchestrator creates draft
2. Human approves
3. MCP calls Instagram API
4. **Post published!**

---

## Important: Image URLs

Instagram API requires **publicly accessible image URLs**:

**❌ Won't Work:**
- `C:\Users\You\Pictures\image.jpg` (local file)
- `D:\AI\image.jpg` (local file)

**✅ Will Work:**
- `https://i.imgur.com/abc123.jpg`
- `https://yoursite.com/image.jpg`
- `https://cdn.example.com/posts/image.png`

**Upload to Imgur (free):**
1. Go to https://imgur.com/upload
2. Upload image
3. Copy "Direct link" (ends in .jpg)
4. Use that URL

---

## Testing

### Step 1: Upload Test Image to Imgur

Go to https://imgur.com/upload, upload any image, copy direct link.

### Step 2: Post to Instagram

```bash
curl -X POST http://localhost:3005/post_instagram \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test from AI Employee Vault! 🎉",
    "image_url": "https://i.imgur.com/YOUR_IMAGE.jpg"
  }'
```

### Step 3: Check Instagram

Open Instagram → Your profile → **Post should be there!**

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/post_instagram` | POST | Create Instagram post |

**Request:**
```json
{
  "content": "Your caption",
  "image_url": "https://example.com/image.jpg",
  "draft_file": "Pending_Approval/Instagram_Draft.md"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": "17895123456789012",
  "permalink": "https://www.instagram.com/p/ABC123/",
  "caption": "Your caption",
  "image_url": "https://example.com/image.jpg"
}
```

---

## Troubleshooting

### "Instagram not configured"

Add to `.env`:
```bash
INSTAGRAM_BUSINESS_USER_ID=17841400000000000
INSTAGRAM_ACCESS_TOKEN=EAAB...
```

### "Invalid access token"

Token expired (60 days). Generate new one:
1. Graph API Explorer
2. Get Token → Page Access Token
3. Update `.env`

### "Image URL not accessible"

Use a public URL:
- Upload to Imgur
- Use your website CDN
- Don't use local file paths

### "Permissions not approved"

For development, no approval needed. For production:
1. App Review → Submit
2. Wait for approval

---

## Comparison: API vs Browser

| Feature | Browser Automation | Official API |
|---------|-------------------|--------------|
| **Reliability** | ❌ Poor | ✅ Excellent |
| **Setup** | Easy | Medium |
| **Cost** | Free | Free |
| **Limits** | None | 25/hour, 200/day |
| **Image Source** | Local files | Public URLs |
| **Stability** | Breaks often | Stable |
| **Recommended** | ❌ No | ✅ YES |

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `watchers/instagram_poster_api.py` | ✅ NEW | Post via API |
| `setup_instagram.py` | ✅ NEW | Get Business User ID |
| `src/social_mcp.js` | ✅ UPDATED | Uses API now |
| `.env.example` | ✅ UPDATED | Instagram config |
| `INSTAGRAM_API_SETUP.md` | ✅ NEW | Full setup guide |

---

## Summary

**✅ Instagram Integration: COMPLETE (Official API)**

- ✅ Reliable posting
- ✅ Official method
- ✅ Won't get blocked
- ✅ Free to use
- ✅ Integrated with MCP
- ✅ Ready for production

**Only requires:**
1. Instagram Business account (free)
2. Facebook Page (free)
3. Access token (free, 60 days)

---

**🎉 Instagram is now ready with the OFFICIAL API - no more automation issues!**
