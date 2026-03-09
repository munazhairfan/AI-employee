# Groq API Setup - FREE, Fast, No Installation

**Date:** 2026-02-27  
**Cost:** FREE (30 req/min)  
**Installation:** NOT Required!

---

## 🚀 Quick Setup (2 Minutes)

### Step 1: Get FREE Groq API Key

1. **Visit:** https://console.groq.com/keys
2. **Sign up** (free account)
3. **Click "Create API Key"**
4. **Copy the key** (starts with `gsk_`)

**No credit card required!** ✅

---

### Step 2: Add to .env

Open `.env` file and replace:

```bash
GROQ_API_KEY=your-groq-api-key-here
```

With your actual key:

```bash
GROQ_API_KEY=gsk_abc123your-actual-key-here
GROQ_MODEL=llama3-70b-8192
```

---

### Step 3: Test

```bash
python test_ai_agent.py
```

**Expected output:**
```
============================================================
  AI AGENT TEST SUITE
============================================================

Primary Model: Groq
Model Name: llama3-70b-8192
Groq Available: True
...

[OK] AI model available
[OK] Basic reasoning works
...

Total: 6/6 tests passed

[SUCCESS] All tests passed! AI agent is ready.
```

---

## 📊 Groq FREE Tier Limits

| Limit | Value |
|-------|-------|
| **Requests/minute** | 30 |
| **Requests/day** | ~43,200 |
| **Tokens/request** | Up to 8192 |
| **Cost** | FREE |

---

## 🎯 Is 30 req/min Enough for You?

### Personal Use (1 user):
- **Typical:** 0.03 req/min
- **Limit:** 30 req/min
- **Usage:** **0.1% of limit** ✅

### Small Team (10 users):
- **Typical:** 0.8 req/min
- **Limit:** 30 req/min
- **Usage:** **2.7% of limit** ✅

### Small Business (100 users):
- **Typical:** 8.3 req/min
- **Limit:** 30 req/min
- **Usage:** **28% of limit** ✅

### Production (1000+ users):
- **Typical:** 83 req/min
- **Limit:** 30 req/min
- **Usage:** **277% - EXCEEDS LIMIT** ❌

**Verdict:** Perfect for development and up to 100 users! ✅

---

## 💰 When You Need More (Future)

If you exceed 30 req/min (100+ active users):

### Option 1: Groq Paid Tier
- Higher limits
- Still cheap (~$0.0001/1K tokens)

### Option 2: Multiple FREE APIs
```python
# System automatically rotates between:
# - Groq (FREE)
# - Together AI (free credits)
# - Qwen API (paid but cheap)
```

### Option 3: Upgrade to Production API
- OpenAI GPT-4
- Anthropic Claude
- Custom GPU server

---

## 🧪 Usage Examples

### Test Basic Reasoning
```bash
python -c "
from src.ai_agent import ai_reasoning
result = ai_reasoning('Send invoice for $500 to ABC Corp')
print(result)
"
```

### Run Orchestrator
```bash
python orchestrator.py
```

### Create Test Draft
```bash
# 1. Create file in AI_Employee_Vault/Needs_Action/
echo "Send email to test@example.com about project" > AI_Employee_Vault/Needs_Action/test.md

# 2. Run orchestrator
python orchestrator.py

# 3. Check Pending_Approval/ for draft
```

---

## 🔑 Get Your Groq Key NOW

**Direct link:** https://console.groq.com/keys

**Steps:**
1. Click link
2. Sign up (free)
3. Create API key
4. Copy to `.env`

**Total time: 2 minutes!**

---

## ❓ FAQ

### Q: Is Groq really free?
**A:** Yes! Free tier includes 30 requests/minute, no credit card required.

### Q: Do I need to install anything?
**A:** NO! Just get API key and configure `.env`. That's it!

### Q: What models are available?
**A:** 
- `llama3-70b-8192` (Meta Llama3 70B)
- `llama3-8b-8192` (Meta Llama3 8B)
- `mixtral-8x7b-32768` (Mistral Mixtral)
- `gemma-7b-it` (Google Gemma)

### Q: How fast is Groq?
**A:** Very! Typically 1-3 seconds per request (faster than Ollama local).

### Q: Is my data safe?
**A:** Data is sent to Groq's servers. For sensitive data, use local Ollama instead.

### Q: What happens if I hit the limit?
**A:** API returns rate limit error. System can be configured to retry or fallback to another API.

---

## 🎉 Summary

**To use Groq API:**
1. ✅ Get FREE API key (2 min) - https://console.groq.com/keys
2. ✅ Configure `.env` (30 sec)
3. ✅ Test (1 min)

**No installation required!** ✅  
**No disk space needed!** ✅  
**Works immediately!** ✅  
**FREE forever!** ✅

**Ready to go!** 🚀

---

*Last Updated: 2026-02-27*
