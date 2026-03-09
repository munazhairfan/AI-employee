# Quick AI Setup - No Installation Required!

**Date:** 2026-02-27  
**Installation:** NOT Required! ✅

---

## 🎯 Answer to Your Questions

### ❓ Does Ollama take lots of space?

**Yes!** Ollama requires:
- **Download:** 3-6 GB for models
- **RAM:** 4-8 GB while running
- **Disk:** 5-10 GB total

### ❓ Can I use Qwen API instead?

**YES!** ✅ Qwen API (or DeepSeek) is **RECOMMENDED** because:
- ✅ **No installation** needed
- ✅ **No disk space** required
- ✅ **Works immediately** with API key
- ✅ **Pay-per-use** (cheap, ~$0.001-0.01 per request)
- ✅ **High quality** models

---

## 🚀 Quick Start with Qwen API (2 Minutes)

### Step 1: Get Qwen API Key

1. Go to: **https://dashscope.console.aliyun.com/**
2. Sign in (Alibaba Cloud account)
3. Navigate to **API Keys**
4. Click **"Create New Key"**
5. Copy the key (starts with `sk-`)

**Note:** New users get **free credits** for testing!

---

### Step 2: Configure .env

Create `.env` file in project root:

```bash
# Copy template
cp .env.example .env
```

Edit `.env` and add your Qwen API key:

```bash
# AI Agent Configuration
QWEN_API_KEY=sk-your-qwen-key-here
QWEN_MODEL=qwen-plus
```

That's it! **No installation needed!** ✅

---

### Step 3: Test AI Agent

```bash
python test_ai_agent.py
```

Expected output:
```
============================================================
  AI AGENT TEST SUITE
============================================================

Primary Model: Qwen (qwen-plus)
Qwen Available: True
...

✅ PASS: Model Availability
✅ PASS: Basic Reasoning
✅ PASS: Email Draft
...

Total: 6/6 tests passed
🎉 All tests passed! AI agent is ready.
```

---

## 💰 Qwen API Pricing

**Free Tier:**
- New users: **Free credits** (~$5-10 worth)
- Enough for **hundreds of test requests**

**Pay-per-use** (after free credits):
- **qwen-plus:** ~$0.002 per 1K tokens
- **Typical request:** 500-1000 tokens
- **Cost per request:** ~$0.001-0.002

**Example:**
- 100 email drafts ≈ **$0.10-0.20**
- 1000 WhatsApp replies ≈ **$0.50-1.00**

Much cheaper than OpenAI! 💰

---

## 🔄 Alternative: DeepSeek API

Another great option (also no installation):

### Get DeepSeek API Key

1. Go to: **https://platform.deepseek.com/**
2. Sign up
3. Get API key

### Configure .env

```bash
DEEPSEEK_API_KEY=your-deepseek-key-here
DEEPSEEK_MODEL=deepseek-chat
```

**Pricing:**
- Similar to Qwen (~$0.001-0.002 per request)
- High quality models
- Fast response times

---

## 📊 Comparison: API vs Local

| Feature | Qwen/DeepSeek API | Ollama (Local) |
|---------|-------------------|----------------|
| **Installation** | ❌ None needed | ✅ 3-6 GB download |
| **Disk Space** | ✅ 0 GB | ❌ 5-10 GB |
| **RAM Usage** | ✅ 0 GB | ❌ 4-8 GB |
| **Setup Time** | ✅ 2 minutes | ❌ 10-15 minutes |
| **Cost** | ~$0.001/request | ✅ Free |
| **Internet** | ❌ Required | ✅ Not needed |
| **Privacy** | ⚠️ Data sent to cloud | ✅ 100% local |
| **Speed** | ✅ Fast (1-3 sec) | ⚠️ Medium (5-10 sec) |
| **Quality** | ✅ Excellent | ⚠️ Good |

**Recommendation:** Use **Qwen API** for development/testing ✅

---

## 🎯 Complete Setup (3 Steps)

### 1. Get API Key (1 min)
```
https://dashscope.console.aliyun.com/
→ Sign in → API Keys → Create Key
```

### 2. Configure .env (30 sec)
```bash
cp .env.example .env
# Edit .env: Add QWEN_API_KEY=sk-...
```

### 3. Test (1 min)
```bash
python test_ai_agent.py
```

**Total time: 2-3 minutes** ⏱️

---

## 🧪 Usage Examples

### Example 1: Test Reasoning
```bash
python -c "
from src.ai_agent import ai_reasoning
result = ai_reasoning('Send invoice for $500 to ABC Corp')
print(result)
"
```

### Example 2: Generate Email Draft
```bash
python -c "
from src.ai_agent import ai_generate_email_draft
result = ai_generate_email_draft('Email john@example.com about meeting tomorrow')
print(result)
"
```

### Example 3: Run Orchestrator
```bash
python orchestrator.py
```

---

## 🔑 Get Your Qwen API Key NOW

**Direct Link:** https://dashscope.console.aliyun.com/apiKey

**Steps:**
1. Click link above
2. Sign in (or create Alibaba Cloud account)
3. Click "Create New Key"
4. Copy the key
5. Paste into `.env`

**Done!** ✅ No installation, no disk space used!

---

## ❓ FAQ

### Q: Is Qwen API free?
**A:** New users get free credits (~$5-10). After that, pay-per-use (~$0.001/request).

### Q: Do I need to install anything?
**A:** **NO!** Just get API key and configure `.env`. That's it!

### Q: What if I don't have Qwen API key yet?
**A:** You can use DeepSeek API instead (same setup process).

### Q: Can I switch between APIs later?
**A:** Yes! Just change `.env` configuration.

### Q: Is my data safe with Qwen API?
**A:** Data is sent to Alibaba Cloud servers. For sensitive data, use local Ollama instead.

### Q: How much does it cost for 1000 requests?
**A:** Approximately **$1-2** for 1000 requests (varies by model and token count).

---

## 🎉 Summary

**To use Qwen API:**
1. ✅ Get API key (2 min) - https://dashscope.console.aliyun.com/
2. ✅ Configure `.env` (30 sec)
3. ✅ Test (1 min)

**No installation required!** ✅  
**No disk space needed!** ✅  
**Works immediately!** ✅

**Ready to go!** 🚀

---

*Last Updated: 2026-02-27*
