# AI Agent Setup Guide

**Date:** 2026-02-27  
**Status:** Ready for Use

---

## 🤖 AI Agent Options

You have **two options** for the AI agent:

### Option A: Ollama (FREE, Local, Recommended for Development)

**Pros:**
- ✅ 100% Free
- ✅ Runs locally (privacy)
- ✅ No API keys needed
- ✅ Works offline

**Cons:**
- ❌ Requires local resources (RAM, CPU/GPU)
- ❌ Slower than cloud options
- ❌ Model quality depends on what you download

**Best for:** Development, testing, privacy-sensitive use

---

### Option B: OpenAI API (Paid, Cloud, Production)

**Pros:**
- ✅ Best quality models (GPT-4)
- ✅ Fast response times
- ✅ No local resources needed
- ✅ Reliable

**Cons:**
- ❌ Costs money (~$0.01-0.03 per request)
- ❌ Requires internet
- ❌ Data sent to OpenAI

**Best for:** Production, high-volume use

---

## 🚀 Quick Start

### Option A: Ollama Setup (5 minutes)

#### Step 1: Install Ollama

**Windows:**
```powershell
# Download and run installer from:
https://ollama.com/download/windows
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Step 2: Pull a Model

```bash
# Recommended model (8GB RAM minimum)
ollama pull llama3

# Alternative (smaller, 4GB RAM)
ollama pull mistral

# Alternative (code-focused)
ollama pull codellama
```

#### Step 3: Start Ollama

```bash
# Ollama usually runs automatically after install
# To start manually:
ollama serve
```

#### Step 4: Test Ollama

```bash
ollama run llama3 "Hello, how are you?"
```

You should see a response.

#### Step 5: Configure .env

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

#### Step 6: Test AI Agent

```bash
cd src
python ai_agent.py
```

You should see:
```
AI Agent Model Test
==================================================
Primary Model: Ollama (llama3)
Ollama Available: True
...
```

---

### Option B: OpenAI API Setup (2 minutes)

#### Step 1: Get API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

#### Step 2: Configure .env

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini  # Cost-effective option
```

#### Step 3: Test AI Agent

```bash
cd src
python ai_agent.py
```

You should see:
```
AI Agent Model Test
==================================================
Primary Model: OpenAI (gpt-4o-mini)
OpenAI Available: True
...
```

---

## 🧪 Testing the AI Agent

### Test 1: Basic Reasoning

```bash
cd src
python -c "
from ai_agent import ai_reasoning
result = ai_reasoning('Send invoice for \$500 to ABC Corp')
print(result)
"
```

Expected output:
```json
{
  "task_summary": "Create and send invoice",
  "fields": {
    "amount": {"value": 500, "source_text": "\$500", "confidence": 100},
    "customer": {"value": "ABC Corp", "source_text": "to ABC Corp", "confidence": 100}
  },
  "action_type": "invoice",
  "requires_human_review": false
}
```

---

### Test 2: Email Draft

```bash
cd src
python -c "
from ai_agent import ai_generate_email_draft
result = ai_generate_email_draft('Send email to john@example.com about project update')
print(result)
"
```

---

### Test 3: WhatsApp Reply

```bash
cd src
python -c "
from ai_agent import ai_generate_whatsapp_reply
result = ai_generate_whatsapp_reply('Hi, please send invoice for \$500')
print(result)
"
```

---

## 🔧 Troubleshooting

### Ollama Not Available

**Error:** `Cannot connect to Ollama`

**Fix:**
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Check if model is installed
ollama pull llama3
```

---

### OpenAI API Error

**Error:** `OPENAI_API_KEY not set`

**Fix:**
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY=sk-...` is set
3. Make sure key is valid (not expired)

---

### JSON Parse Error

**Error:** `JSON parse error`

**Cause:** AI model returned non-JSON response

**Fix:**
- Lower temperature (already set to 0.1)
- Try different model
- Check system prompt is being sent

---

### Slow Response Times (Ollama)

**Symptom:** Takes >30 seconds for response

**Fix:**
1. Use smaller model: `ollama pull mistral`
2. Update OLLAMA_MODEL in `.env`:
   ```bash
   OLLAMA_MODEL=mistral
   ```
3. Close other applications (free up RAM)

---

## 📊 Model Comparison

| Model | Size | RAM Required | Speed | Quality | Best For |
|-------|------|--------------|-------|---------|----------|
| **llama3** | 8B | 8GB | Medium | Good | General use |
| **llama3.1** | 8B | 8GB | Medium | Better | Improved reasoning |
| **mistral** | 7B | 4GB | Fast | Good | Low-resource systems |
| **codellama** | 7B | 4GB | Fast | Good (code) | Code-related tasks |
| **gpt-4o-mini** | Cloud | N/A | Very Fast | Excellent | Production |
| **gpt-4** | Cloud | N/A | Fast | Best | Complex tasks |

---

## 🔐 Security Notes

### Ollama (Local)
- ✅ All processing happens on your machine
- ✅ No data leaves your computer
- ✅ Safe for sensitive information

### OpenAI (Cloud)
- ⚠️ Data sent to OpenAI servers
- ⚠️ Review OpenAI's privacy policy
- ⚠️ Don't send highly sensitive data
- ✅ API key encrypted in transit

---

## 💰 Cost Estimates (OpenAI)

**Model:** `gpt-4o-mini`

- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens

**Typical usage:**
- Email draft: ~500 tokens = ~$0.0003
- WhatsApp reply: ~300 tokens = ~$0.0002
- Invoice extraction: ~400 tokens = ~$0.0002

**1000 requests/day** ≈ **$0.20-0.50/day**

---

## 🎯 Anti-Hallucination Guarantees

Both models enforce:

1. ✅ **Extract ONLY** - No invention of facts
2. ✅ **Source Citations** - Every field cited
3. ✅ **Confidence Scoring** - 0-100% for each field
4. ✅ **Mark Unknown** - Missing info flagged
5. ✅ **Human Review** - Required for <80% confidence

---

## 📁 Files Created

- `src/ai_agent.py` - Main AI agent module
- `.env.example` - Updated with AI config
- `docs/AI_AGENT_SETUP.md` - This guide

---

## ✅ Verification Checklist

- [ ] Ollama installed OR OpenAI key obtained
- [ ] Model downloaded (Ollama) or configured (OpenAI)
- [ ] `.env` file created with correct settings
- [ ] `python ai_agent.py` runs successfully
- [ ] Test reasoning returns valid JSON
- [ ] Test email draft works
- [ ] Test WhatsApp reply works

---

## 🚀 Next Steps

1. ✅ Complete setup above
2. Run orchestrator: `python orchestrator.py`
3. Place test file in `AI_Employee_Vault/Needs_Action/`
4. Watch AI generate drafts with anti-hallucination guards
5. Review drafts in `Pending_Approval/`
6. Approve/reject manually

---

*Last Updated: 2026-02-27*
