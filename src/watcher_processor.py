"""
Watcher Processor - AI Auto-Creates Tasks from Watcher Output
Runs every 5 minutes, processes 1 file at a time (LOW PRIORITY)
Conservative rate limiting to avoid Groq API limits (30 req/min free tier)
"""

import time
import json
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, 'src')

from intent_analyzer import analyze_intent
from ai_agent import get_model_info

# Folders
WATCHER_OUTPUT = Path('data/watcher_output')
NEEDS_ACTION = Path('data/AI_Employee_Vault/Needs_Action')
PROCESSED_LOG = Path('data/watcher_processed_log.json')

# Rate limiting - VERY CONSERVATIVE (background priority)
# Background files: 1 file per 5 minutes = 0.2 calls/minute
# This leaves 99% of AI budget for user actions!
MAX_FILES_PER_BATCH = 1       # Only 1 file at a time
BATCH_DELAY = 300             # Wait 5 minutes (300 seconds)
MAIN_LOOP_INTERVAL = 300      # Check every 5 minutes
INITIAL_DELAY = 120           # Wait 2 minutes at startup (let user actions go first)

# Create folders
WATCHER_OUTPUT.mkdir(parents=True, exist_ok=True)
NEEDS_ACTION.mkdir(parents=True, exist_ok=True)


def load_processed_log():
    """Load list of already processed files"""
    if PROCESSED_LOG.exists():
        try:
            return json.loads(PROCESSED_LOG.read_text(encoding='utf-8'))
        except:
            return []
    return []


def save_processed_log(processed_files):
    """Save list of processed files"""
    PROCESSED_LOG.write_text(json.dumps(processed_files, indent=2), encoding='utf-8')


def get_new_files():
    """Get unprocessed markdown files from watcher output"""
    processed = load_processed_log()
    new_files = []
    
    for md_file in WATCHER_OUTPUT.glob('*.md'):
        if md_file.name not in processed:
            new_files.append(md_file)
    
    return new_files


def create_task_from_file(watcher_file):
    """Read watcher output, AI analyzes, creates task in correct folder"""
    
    # Check if file still exists
    if not watcher_file.exists():
        print(f"\n[AI] File no longer exists (already processed or deleted): {watcher_file.name}")
        return False
    
    print(f"\n[AI] Processing: {watcher_file.name}")

    # Read watcher output
    try:
        content = watcher_file.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"\n[AI] File disappeared: {watcher_file.name} (race condition)")
        return False
    except Exception as e:
        print(f"\n[AI] Error reading file: {e}")
        return False
    
    # Extract metadata from frontmatter
    metadata = {}
    lines = content.split('\n')
    in_frontmatter = False
    
    for line in lines:
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        
        if in_frontmatter and ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()
    
    # Get the message content (everything after frontmatter)
    message_start = content.find('---', content.find('---') + 3) + 3
    message_content = content[message_start:].strip()

    # Extract original message for context (if available)
    original_message = ""
    if "## Original Message" in content:
        # Extract everything under "## Original Message" section
        orig_start = content.find("## Original Message")
        orig_end = content.find("---", orig_start)
        if orig_end == -1:
            orig_end = len(content)
        original_message = content[orig_start:orig_end].strip()

    # AI analyzes the message
    print(f"[AI] Analyzing message...")

    # Add source-specific context for better AI analysis
    ai_input_text = message_content
    source = metadata.get('source', '')
    from_chat = metadata.get('from', '')

    if source == 'whatsapp_watcher' and from_chat:
        # Add WhatsApp-specific context to help AI extract phone number and format correctly
        ai_input_text = f"""This is a WhatsApp message that needs to be processed.

**Source:** WhatsApp
**From:** {from_chat}
**Phone:** {metadata.get('phone', 'Not available')}

**Original Message:**
{original_message if original_message else message_content}

**INSTRUCTIONS FOR AI:**
1. Analyze the message content to determine the correct intent (odoo_invoice, whatsapp_reply, email_send, etc.)
2. Extract the phone number from the metadata if available (phone: {metadata.get('phone', 'NOT_EXTRACTED')})
3. If phone is 'NOT_EXTRACTED' or 'Not available', mark it as missing info for human to fill
4. The message_content entity should contain the suggested reply message
5. Format the suggested_action with an arrow: → Send '[message]' to [phone] on WhatsApp
6. Include confidence score and all extracted entities (phone, message content)"""

    # Try AI analysis with retries for rate limit
    max_retries = 3
    ai_result = None

    for attempt in range(max_retries):
        try:
            ai_result = analyze_intent(ai_input_text)
            if ai_result and ai_result.get('primary_intent'):
                # Check if AI returned an error
                if 'error' in ai_result:
                    print(f"[AI] AI returned error: {ai_result.get('error')}")
                    if attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)
                        print(f"[AI] Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                else:
                    break
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'rate limit' in error_msg.lower():
                print(f"[AI] Groq rate limit hit. Waiting 60 seconds...")
                if attempt < max_retries - 1:
                    time.sleep(60)
                    continue
            elif attempt < max_retries - 1:
                wait_time = 30 * (attempt + 1)
                print(f"[AI] AI error. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[AI] Analysis failed: {e}")
                break

    if not ai_result or not ai_result.get('primary_intent'):
        print(f"[AI] Analysis failed after {max_retries} retries!")
        # Create informational task instead of failing
        ai_result = {
            'primary_intent': 'general_task',
            'category': 'informational',
            'can_auto_execute': False,
            'confidence': 0,
            'one_line_summary': 'AI analysis failed - manual review needed',
            'expires_in_days': 7
        }
    
    print(f"[AI] Intent: {ai_result.get('primary_intent')}")
    print(f"[AI] Category: {ai_result.get('category', 'unknown')}")
    print(f"[AI] Can Auto-Execute: {ai_result.get('can_auto_execute', False)}")
    print(f"[AI] Confidence: {ai_result.get('confidence')}%")
    
    # Decide which folder based on AI's category decision
    category = ai_result.get('category', 'informational')
    can_auto = ai_result.get('can_auto_execute', False)
    
    if category == 'actionable' and can_auto:
        # Actionable task - goes to Pending_Approval
        task_folder = Path('data/AI_Employee_Vault/Pending_Approval')
        task_folder.mkdir(parents=True, exist_ok=True)
        print(f"[AI] ✓ ACTIONABLE - Can auto-execute → Pending_Approval/")
    else:
        # Informational task - goes to To_Review
        task_folder = Path('data/AI_Employee_Vault/To_Review')
        task_folder.mkdir(parents=True, exist_ok=True)
        print(f"[AI] ℹ INFORMATIONAL → To_Review/")
    
    # Create task file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    task_type = ai_result.get('primary_intent') or 'general_task'
    
    if category == 'actionable':
        task_file = task_folder / f"{task_type}_watcher_{timestamp}.md"
    else:
        task_file = task_folder / f"review_{task_type}_{timestamp}.md"
    
    # Build task markdown
    if category == 'actionable':
        # Actionable task format
        task_content = f"""---
type: {task_type}
auto_generated: true
source_file: {watcher_file.name}
source: {metadata.get('source', 'watcher')}
created: {datetime.now().isoformat()}
ai_confidence: {ai_result.get('confidence', 0)}
category: actionable
can_auto_execute: true
requires_human_review: true
---

# Action Required

**Intent:** {ai_result.get('suggested_action', 'Review and decide action')}

**Priority:** {ai_result.get('priority', 'normal').upper()}

**Confidence:** {ai_result.get('confidence', 0)}%

---

## Extracted Information

"""
        
        # Add entities table
        entities = ai_result.get('entities', {})
        if entities:
            task_content += "| Field | Value | Confidence |\n"
            task_content += "|-------|-------|------------|\n"
            for field, value in entities.items():
                if value:
                    task_content += f"| {field} | {value} | 85% |\n"
        
        # Add missing info (simplified, no checkboxes)
        missing = ai_result.get('missing_info', [])
        if missing:
            task_content += "\n## ⚠️ Missing Information\n\n"
            for item in missing:
                task_content += f"- {item}\n"
            task_content += "\n"

        # Add original message
        task_content += f"""
## Original Message

**From:** {metadata.get('from', 'Unknown')}
**Phone:** {metadata.get('phone', 'Not available')}
**Received:** {metadata.get('received', 'Unknown')}

```
{message_content}
```

---

*Auto-generated by AI from watcher output*
*Review in dashboard before approval*
"""
    
    else:
        # Informational task format
        one_line_summary = ai_result.get('one_line_summary', 'Review this item')
        from datetime import timedelta
        expires_in = ai_result.get('expires_in_days') or 7  # Default to 7 days
        expiry_date = (datetime.now() + timedelta(days=expires_in)).strftime('%Y-%m-%d')
        
        task_content = f"""---
type: {task_type}
auto_generated: true
source_file: {watcher_file.name}
source: {metadata.get('source', 'watcher')}
created: {datetime.now().isoformat()}
category: informational
can_auto_execute: false
ai_summary: {one_line_summary}
expires: {expiry_date}
---

# To Review

**What:** {metadata.get('subject', (task_type or 'item').replace('_', ' ').title())}

**AI Summary:** {one_line_summary}

**From:** {metadata.get('from', 'Unknown')}

**Received:** {metadata.get('received', 'Unknown')}

---

## Content

```
{message_content[:2000]}{'...' if len(message_content) > 2000 else ''}
```

---

**⚠️ This item will auto-archive on {expiry_date} if not reviewed**

---

*Auto-generated by AI from watcher output*
*Mark as done in dashboard after reviewing*
"""
    
    # Save task
    task_file.write_text(task_content, encoding='utf-8')
    print(f"[AI] ✓ Task created: {task_file.name}")
    
    # Mark watcher file as processed
    processed = load_processed_log()
    processed.append(watcher_file.name)
    save_processed_log(processed)
    
    return True


def run_processor():
    """Main processor loop - VERY SLOW (background priority)"""
    print("=" * 60)
    print("  Watcher AI Processor (BACKGROUND PRIORITY)")
    print("=" * 60)
    print()
    print(f"Checking for new watcher output every {MAIN_LOOP_INTERVAL//60} minutes...")
    print(f"Processing: {MAX_FILES_PER_BATCH} file(s) per batch")
    print(f"Delay between batches: {BATCH_DELAY//60} minutes")
    print("Press Ctrl+C to stop")
    print()

    # Check AI availability
    ai_info = get_model_info()
    if ai_info['fallback_available']:
        print(f"AI Agent: {ai_info['primary']} ({ai_info['model']}) - Ready")
        print(f"NOTE: Background processing is SLOW (1 file/5min) to prioritize user actions")
    else:
        print("WARNING: No AI agent available!")
        print()

    print()
    
    # Wait before first processing (let user actions go first)
    print(f"[INFO] Waiting {INITIAL_DELAY//60} minutes before first processing...")
    print(f"[INFO] User actions have priority - background files wait")
    time.sleep(INITIAL_DELAY)
    print(f"[INFO] Starting background processing loop...\n")

    iteration = 0

    while True:
        iteration += 1
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Check for new files
        new_files = get_new_files()

        if new_files:
            print(f"\n[{timestamp}] Found {len(new_files)} file(s) in queue")

            # Process ONE file at a time (very slow)
            batch_count = 0

            for file in new_files:
                # Only 1 file per batch
                if batch_count >= MAX_FILES_PER_BATCH:
                    wait_minutes = BATCH_DELAY // 60
                    print(f"\n[{timestamp}] Batch limit reached. Waiting {wait_minutes} minutes...")
                    time.sleep(BATCH_DELAY)
                    batch_count = 0

                print(f"[{timestamp}] Processing: {file.name}")
                success = create_task_from_file(file)
                if success:
                    print(f"[{timestamp}] ✓ Processed: {file.name}")
                    batch_count += 1
                else:
                    print(f"[{timestamp}] ✗ Failed: {file.name}")
        else:
            wait_minutes = MAIN_LOOP_INTERVAL // 60
            print(f"[{timestamp}] No new files (check #{iteration}, next check in {wait_minutes} min)")

        # Wait 5 minutes between checks
        time.sleep(MAIN_LOOP_INTERVAL)


if __name__ == "__main__":
    try:
        run_processor()
    except KeyboardInterrupt:
        print("\n\nProcessor stopped by user")
