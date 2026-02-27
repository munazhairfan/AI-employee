# Instagram API Setup Guide - Official & Reliable

## Why API Instead of Browser Automation?

| Browser Automation | Official API |
|-------------------|--------------|
| ❌ Unreliable | ✅ Reliable |
| ❌ Gets blocked | ✅ Official method |
| ❌ UI changes break it | ✅ Stable API |
| ❌ Slow | ✅ Fast |
| ⚠️ Free but flaky | ✅ Free & stable |

---

## Prerequisites

### 1. Instagram Business or Creator Account

**Personal accounts won't work!** You need:

- **Instagram Business Account** (recommended), OR
- **Instagram Creator Account**

**Convert to Business (Free):**
1. Open Instagram → Settings
2. Account → Switch to Professional Account
3. Choose "Business" or "Creator"
4. Done!

### 2. Facebook Page

Your Instagram Business account must be connected to a Facebook Page.

**Connect Instagram to Page:**
1. Go to your Facebook Page
2. Settings → Instagram
3. Connect Account → Log in to Instagram
4. Done!

### 3. Facebook App with Instagram Permissions

You already have a Facebook App from earlier! Just add Instagram permissions.

---

## Step-by-Step Setup

### Step 1: Add Instagram Permissions to Facebook App

1. Go to: https://developers.facebook.com/apps/
2. Select your app
3. Click "Add Products" → Add these:
   - ✅ **Instagram Basic Display**
   - ✅ **Instagram Graph API**
4. Save

### Step 2: Get Page Access Token

1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click "Get Token" → "Get Page Access Token"
4. Select your Page
5. Add these permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
6. Click "Generate Token"
7. **Copy the token** (looks like: `EAABsbCS1iHgBO...`)

### Step 3: Get Your Page ID

In Graph API Explorer, run:
```
GET /me?fields=id,name
```

Or go to your Facebook Page → About section → Copy Page ID

### Step 4: Get Instagram Business User ID

Run the setup script:

```bash
python setup_instagram.py
```

Enter:
- **Page Access Token** (from Step 2)
- **Page ID** (from Step 3)

It will output your **Instagram Business User ID** (looks like: `17841400000000000`)

### Step 5: Add to .env

Open `.env` and add:

```bash
# Instagram API
INSTAGRAM_BUSINESS_USER_ID=17841400000000000
INSTAGRAM_ACCESS_TOKEN=EAABsbCS1iHgBO...
```

---

## How to Post

### Method 1: Python Script

```bash
python watchers/instagram_poster_api.py "Your caption" "https://example.com/image.jpg"
```

**Important:** Image must be a **public URL** (not local file).

**Host your image on:**
- Your website: `https://yoursite.com/image.jpg`
- Imgur: `https://i.imgur.com/abc123.jpg`
- Cloudinary, AWS S3, etc.

### Method 2: Via MCP Server

```bash
curl -X POST http://localhost:3005/post_instagram \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your caption",
    "image_url": "https://example.com/image.jpg"
  }'
```

### Method 3: Full AI Employee Vault Flow

1. Orchestrator creates draft
2. Human approves
3. MCP calls Instagram API
4. Post published!

---

## Testing

### Quick Test

```bash
# Use a publicly accessible image
python watchers/instagram_poster_api.py "Test from AI!" "https://i.imgur.com/your-test-image.jpg"
```

### Check Result

1. Open Instagram
2. Go to your profile
3. **Post should appear!**

---

## Troubleshooting

### "Instagram Business account not connected"

**Fix:**
1. Go to Facebook Page Settings
2. Instagram → Connect Account
3. Log in to your Instagram Business account

### "Invalid access token"

**Fix:**
1. Token expired (they last 60 days)
2. Generate new token in Graph API Explorer
3. Update `.env` with new token

### "Image URL not accessible"

Instagram needs a **public URL**:
- ❌ `C:\Users\You\Pictures\image.jpg` (local file)
- ✅ `https://i.imgur.com/abc123.jpg` (public URL)

**Upload image to Imgur (free):**
1. Go to https://imgur.com/upload
2. Upload your image
3. Copy direct link (ends in .jpg)
4. Use that URL

### "Permissions not approved"

For development mode, you can use the app without review. For production:
1. Go to App Review in Facebook Developer Dashboard
2. Submit for review
3. Wait for approval (1-2 weeks)

---

## API Limits

| Limit | Value |
|-------|-------|
| **Posts per hour** | 25 |
| **Posts per day** | 200 |
| **Token expiry** | 60 days |
| **Cost** | FREE |

---

## Token Refresh

Access tokens expire after 60 days. To refresh:

1. Go to Graph API Explorer
2. Generate new token
3. Update `.env`

Or use the refresh token flow (more complex).

---

## Summary

**✅ Instagram API Setup:**

1. ✅ Instagram Business/Creator account
2. ✅ Connected to Facebook Page
3. ✅ Facebook App with Instagram permissions
4. ✅ Get Page Access Token
5. ✅ Get Instagram Business User ID
6. ✅ Add to .env
7. ✅ Post using public image URL

**Once set up, posting is reliable and automatic!**

---

**🎉 Instagram posting via official API - no more browser automation issues!**
