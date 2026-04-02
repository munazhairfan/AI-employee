"""
AI Agent Model - Local (Ollama) and Cloud (OpenAI, Groq, Qwen) Support
- Zero Hallucination Mode with constrained prompting
- Source citation enforcement
- Confidence scoring
- Human review routing

Supports:
- Groq API (FREE tier - 30 req/min)
- Together AI (Free credits)
- Qwen API (Alibaba Cloud)
- DeepSeek API
- OpenAI API
- Ollama (Local, free)
"""

import json
import os
import requests
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'tinyllama')  # Small model (637 MB) - OPTIONAL

# Groq API (FREE Tier - Fast!)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

# Priority: Groq only (Ollama is optional backup)
USE_GROQ = bool(GROQ_API_KEY)
USE_OLLAMA = False  # Set to True only if you install Ollama

# OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Qwen API (Alibaba Cloud) - OpenAI Compatible
QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
QWEN_BASE_URL = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-plus')

# DeepSeek API - OpenAI Compatible
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# Priority: Groq (FREE) > Qwen > DeepSeek > OpenAI > Ollama
USE_GROQ = bool(GROQ_API_KEY)
USE_QWEN = bool(QWEN_API_KEY)
USE_DEEPSEEK = bool(DEEPSEEK_API_KEY)
USE_OPENAI = bool(OPENAI_API_KEY)

    
# ============================================================================
# SYSTEM PROMPTS - Anti-Hallucination Enforced
# ============================================================================

SYSTEM_PROMPT_REASONING = """
You are an AI reasoning assistant for AI Employee Vault.

CRITICAL RULES - ZERO HALLUCINATION:
1. Extract facts ONLY from the provided message/file content
2. NEVER invent amounts, dates, names, or details
3. For each extracted field, cite the EXACT source text
4. If information is not explicitly stated, mark as "UNKNOWN"
5. Rate your confidence (0-100%) for each extraction
6. Fields with <80% confidence require human review

OUTPUT FORMAT (JSON ONLY):
{
    "task_summary": "Brief description",
    "fields": {
        "field_name": {
            "value": "extracted value or null",
            "source_text": "exact quote from source",
            "confidence": 0-100,
            "reason": "explanation if confidence <80%"
        }
    },
    "action_type": "email|whatsapp|invoice|linkedin|etc",
    "priority": "urgent|high|normal|low",
    "requires_human_review": true/false,
    "review_reason": "explanation if requires_review is true"
}

EXAMPLE INPUT:
"Send invoice for $500 to ABC Corp"

EXAMPLE OUTPUT:
{
    "task_summary": "Create and send invoice",
    "fields": {
        "amount": {
            "value": 500,
            "source_text": "$500",
            "confidence": 100
        },
        "customer": {
            "value": "ABC Corp",
            "source_text": "to ABC Corp",
            "confidence": 100
        },
        "invoice_number": {
            "value": null,
            "source_text": null,
            "confidence": 0,
            "reason": "Not mentioned in source"
        }
    },
    "action_type": "invoice",
    "priority": "normal",
    "requires_human_review": true,
    "review_reason": "invoice_number not provided (confidence 0%)"
}
"""

SYSTEM_PROMPT_EMAIL = """
You are an email draft generator for AI Employee Vault.

CRITICAL RULES - ZERO HALLUCINATION:
1. Extract recipient, subject, body ONLY from provided text
2. NEVER invent email addresses, names, or details
3. For each field, cite the EXACT source text
4. If information missing, mark as "UNKNOWN - needs clarification"
5. Rate confidence (0-100%) for each extraction
6. Use [PLACEHOLDER] for missing information in email body

OUTPUT FORMAT (JSON ONLY):
{
    "to": {
        "value": "email@example.com or null",
        "source_text": "exact quote",
        "confidence": 0-100
    },
    "subject": {
        "value": "subject line or null",
        "source_text": "exact quote",
        "confidence": 0-100
    },
    "priority": {
        "value": "urgent|high|normal|low",
        "source_text": "exact quote or null",
        "confidence": 0-100
    },
    "email_body": "Full email text with [PLACEHOLDER] for missing info",
    "requires_human_review": true/false,
    "review_reason": "explanation if review needed"
}
"""

SYSTEM_PROMPT_WHATSAPP = """
You are a WhatsApp reply assistant for AI Employee Vault.

CRITICAL RULES - ZERO HALLUCINATION:
1. Extract sender intent ONLY from provided message
2. NEVER invent names, numbers, or facts
3. For each extraction, cite the EXACT source text
4. Rate confidence (0-100%) for intent detection
5. Keep replies casual, concise, WhatsApp-style
6. If intent unclear (<80% confidence), draft clarification request

OUTPUT FORMAT (JSON ONLY):
{
    "sender": {
        "value": "name/number or null",
        "source_text": "exact quote",
        "confidence": 0-100
    },
    "intent": {
        "value": "what they want or null",
        "source_text": "exact quote",
        "confidence": 0-100
    },
    "urgency": {
        "value": "urgent|normal|low",
        "source_text": "exact quote or null",
        "confidence": 0-100
    },
    "suggested_reply": "Casual WhatsApp-style reply",
    "requires_human_review": true/false,
    "review_reason": "explanation if review needed"
}
"""


# ============================================================================
# OLLAMA (Local, Free)
# ============================================================================

def call_ollama(prompt: str, system_prompt: str = SYSTEM_PROMPT_REASONING, 
                model: str = OLLAMA_MODEL, json_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Call local Ollama API.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        model: Ollama model name
        json_mode: If True, request JSON output
    
    Returns:
        Parsed JSON response or None
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent extraction
            "top_p": 0.9,
        }
    }
    
    if json_mode:
        payload["format"] = "json"
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        output = result.get('response', '')
        
        if json_mode:
            # Parse JSON from output
            try:
                # Ollama might include markdown code blocks
                if output.startswith('```json'):
                    output = output[7:]
                if output.endswith('```'):
                    output = output[:-3]
                output = output.strip()
                return json.loads(output)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw output: {output}")
                return None
        
        return {"text": output}
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Ollama. Is it running?")
        print("Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("Run: ollama pull llama3")
        return None
    except requests.exceptions.Timeout:
        print("ERROR: Ollama request timed out")
        return None
    except Exception as e:
        print(f"ERROR: Ollama call failed: {e}")
        return None


# ============================================================================
# GROQ API (FREE Tier - Fast!)
# ============================================================================

def call_groq(prompt: str, system_prompt: str = SYSTEM_PROMPT_REASONING,
              model: str = GROQ_MODEL, json_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Call Groq API (FREE tier - 30 req/min).
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        model: Groq model name
        json_mode: If True, request JSON output
    
    Returns:
        Parsed JSON response or None
    """
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        output = result['choices'][0]['message']['content']

        if json_mode:
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw output: {output}")
                return None

        return {"text": output}

    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print(f"ERROR: Groq rate limit exceeded. Wait 60 seconds and retry.")
            print(f"Free tier limit: 30 requests/minute")
        else:
            print(f"ERROR: Groq HTTP error: {e}")
        return None
    except requests.exceptions.Timeout:
        print(f"ERROR: Groq API call timed out")
        return None
    except Exception as e:
        print(f"ERROR: Groq API call failed: {e}")
        return None


# ============================================================================
# QWEN API (Alibaba Cloud - OpenAI Compatible)
# ============================================================================

def call_qwen(prompt: str, system_prompt: str = SYSTEM_PROMPT_REASONING,
              model: str = QWEN_MODEL, json_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Call Qwen API (DashScope) - OpenAI compatible.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        model: Qwen model name
        json_mode: If True, request JSON output
    
    Returns:
        Parsed JSON response or None
    """
    if not QWEN_API_KEY:
        print("ERROR: QWEN_API_KEY not set")
        return None
    
    url = QWEN_BASE_URL
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        output = result['choices'][0]['message']['content']
        
        if json_mode:
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw output: {output}")
                return None
        
        return {"text": output}
        
    except Exception as e:
        print(f"ERROR: Qwen API call failed: {e}")
        return None


# ============================================================================
# DEEPSEEK API (OpenAI Compatible)
# ============================================================================

def call_deepseek(prompt: str, system_prompt: str = SYSTEM_PROMPT_REASONING,
                  model: str = DEEPSEEK_MODEL, json_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Call DeepSeek API - OpenAI compatible.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        model: DeepSeek model name
        json_mode: If True, request JSON output
    
    Returns:
        Parsed JSON response or None
    """
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set")
        return None
    
    url = DEEPSEEK_BASE_URL
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        output = result['choices'][0]['message']['content']
        
        if json_mode:
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw output: {output}")
                return None
        
        return {"text": output}
        
    except Exception as e:
        print(f"ERROR: DeepSeek API call failed: {e}")
        return None


# ============================================================================
# OPENAI (Cloud, Paid but Cheap)
# ============================================================================

def call_openai(prompt: str, system_prompt: str = SYSTEM_PROMPT_REASONING,
                model: str = OPENAI_MODEL, json_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Call OpenAI API.
    
    Args:
        prompt: User prompt
        system_prompt: System instructions
        model: OpenAI model name
        json_mode: If True, request JSON output
    
    Returns:
        Parsed JSON response or None
    """
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set")
        return None
    
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,  # Low for consistent extraction
        "max_tokens": 2000
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        output = result['choices'][0]['message']['content']
        
        if json_mode:
            try:
                return json.loads(output)
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Raw output: {output}")
                return None
        
        return {"text": output}
        
    except Exception as e:
        print(f"ERROR: OpenAI call failed: {e}")
        return None


# ============================================================================
# UNIFIED AI AGENT INTERFACE
# ============================================================================

def ai_reasoning(message: str, task_type: str = "general") -> Optional[Dict[str, Any]]:
    """
    Perform AI reasoning with anti-hallucination guards.

    Priority: Groq (FREE) > Qwen > DeepSeek > OpenAI > Ollama (first available)

    Args:
        message: Input message to analyze
        task_type: Type of task (general, email, whatsapp, invoice)

    Returns:
        Structured extraction with confidence scores
    """
    # Select appropriate system prompt
    if task_type == "email":
        system_prompt = SYSTEM_PROMPT_EMAIL
    elif task_type == "whatsapp":
        system_prompt = SYSTEM_PROMPT_WHATSAPP
    elif task_type in ("intent_analysis", "general"):
        system_prompt = "You are a JSON-only assistant. Return only valid JSON with no markdown, no explanation, no code blocks. Just the raw JSON object."
    else:
        system_prompt = SYSTEM_PROMPT_REASONING

    # Try APIs in priority order
    result = None

    # 1. Try Groq first (FREE, fast!)
    if USE_GROQ:
        print(f"Using Groq API ({GROQ_MODEL})...")
        result = call_groq(message, system_prompt, json_mode=True)

    # 2. Try Qwen
    if result is None and USE_QWEN:
        print(f"Using Qwen API ({QWEN_MODEL})...")
        result = call_qwen(message, system_prompt, json_mode=True)

    # 3. Try DeepSeek
    if result is None and USE_DEEPSEEK:
        print(f"Using DeepSeek API ({DEEPSEEK_MODEL})...")
        result = call_deepseek(message, system_prompt, json_mode=True)

    # 4. Try OpenAI
    if result is None and USE_OPENAI:
        print(f"Using OpenAI API ({OPENAI_MODEL})...")
        result = call_openai(message, system_prompt, json_mode=True)

    # 5. Fallback to Ollama
    if result is None:
        print(f"Using Ollama ({OLLAMA_MODEL})...")
        result = call_ollama(message, system_prompt, json_mode=True)

    return result


def ai_generate_email_draft(message: str) -> Optional[Dict[str, Any]]:
    """
    Generate email draft with anti-hallucination guards.
    
    Args:
        message: Input message/request
    
    Returns:
        Email draft with extracted fields and confidence scores
    """
    return ai_reasoning(message, task_type="email")


def ai_generate_whatsapp_reply(message: str) -> Optional[Dict[str, Any]]:
    """
    Generate WhatsApp reply with anti-hallucination guards.
    
    Args:
        message: Input WhatsApp message
    
    Returns:
        WhatsApp reply with intent extraction and confidence scores
    """
    return ai_reasoning(message, task_type="whatsapp")


def ai_extract_invoice_details(message: str) -> Optional[Dict[str, Any]]:
    """
    Extract invoice details with anti-hallucination guards.
    
    Args:
        message: Invoice-related message
    
    Returns:
        Invoice details with confidence scores
    """
    result = ai_reasoning(message, task_type="invoice")
    
    if result:
        # Add invoice-specific validation
        required_fields = ['amount', 'customer', 'invoice_number']
        missing = []
        
        for field in required_fields:
            field_data = result.get('fields', {}).get(field, {})
            if field_data.get('value') is None:
                missing.append(field)
        
        if missing:
            result['requires_human_review'] = True
            result['review_reason'] = f"Missing required fields: {', '.join(missing)}"
    
    return result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_openai_available() -> bool:
    """Check if OpenAI API key is configured."""
    return bool(OPENAI_API_KEY)


def get_model_info() -> Dict[str, Any]:
    """Get current AI model configuration."""
    # Determine primary model
    if USE_GROQ:
        primary = "Groq"
        model = GROQ_MODEL
    elif USE_QWEN:
        primary = "Qwen"
        model = QWEN_MODEL
    elif USE_DEEPSEEK:
        primary = "DeepSeek"
        model = DEEPSEEK_MODEL
    elif USE_OPENAI:
        primary = "OpenAI"
        model = OPENAI_MODEL
    else:
        primary = "Ollama"
        model = OLLAMA_MODEL

    return {
        "primary": primary,
        "model": model,
        "groq_available": USE_GROQ,
        "qwen_available": USE_QWEN,
        "deepseek_available": USE_DEEPSEEK,
        "openai_available": USE_OPENAI,
        "ollama_available": check_ollama_available(),
        "fallback_available": USE_GROQ or USE_QWEN or USE_DEEPSEEK or USE_OPENAI or check_ollama_available()
    }


def list_ollama_models() -> list:
    """List available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
    except:
        pass
    return []


# ============================================================================
# MAIN (Testing)
# ============================================================================

if __name__ == "__main__":
    print("AI Agent Model Test")
    print("=" * 50)
    
    # Check availability
    info = get_model_info()
    print(f"Primary Model: {info['primary']} ({info['model']})")
    print(f"Ollama Available: {info['ollama_available']}")
    print(f"OpenAI Available: {info['openai_available']}")
    print()
    
    # Test reasoning
    test_message = "Send invoice for $500 to ABC Corp for consulting services"
    print(f"Test Input: {test_message}")
    print()
    
    result = ai_reasoning(test_message, task_type="invoice")
    
    if result:
        print("AI Output:")
        print(json.dumps(result, indent=2))
    else:
        print("AI processing failed - check if Ollama/OpenAI is available")
        print()
        print("To use Ollama (free, local):")
        print("  1. Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("  2. Pull model: ollama pull llama3")
        print("  3. Run: ollama serve")
