"""
Watcher Processor - AI Auto-Creates Tasks from Watcher Output
Runs every 30 seconds, checks for new watcher output, creates tasks
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

# Rate limiting - process max emails per batch to avoid Groq rate limits
MAX_EMAILS_PER_BATCH = 10  # Process 10 emails, then wait 30 seconds

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
    print(f"\n[AI] Processing: {watcher_file.name}")
    
    # Read watcher output
    content = watcher_file.read_text(encoding='utf-8')
    
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
    
    # AI analyzes the message
    print(f"[AI] Analyzing message...")
    
    # Try AI analysis with retries for rate limit
    max_retries = 3
    ai_result = None
    
    for attempt in range(max_retries):
        try:
            ai_result = analyze_intent(message_content)
            if ai_result and ai_result.get('primary_intent'):
                break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 30 * (attempt + 1)
                print(f"[AI] Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
    
    if not ai_result or not ai_result.get('primary_intent'):
        print(f"[AI] Analysis failed after {max_retries} retries!")
        return False
    
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
        
        # Add missing info
        missing = ai_result.get('missing_info', [])
        if missing:
            task_content += "\n## ⚠️ Missing Information\n\n"
            for item in missing:
                task_content += f"- [ ] {item}\n"
            task_content += "\n**Human review required to fill in missing details**\n"
        
        # Add original message
        task_content += f"""
## Original Message

```
{message_content}
```

---

## Approval Actions

- [ ] Approve (execute suggested action)
- [ ] Edit & Approve (modify details first)
- [ ] Reject (add reason below)
- [ ] Need More Info (specify what's needed)

---

*Auto-generated by AI from watcher output*
*Review before approval - system will execute automatically*
"""
    
    else:
        # Informational task format
        one_line_summary = ai_result.get('one_line_summary', 'Review this item')
        expires_in = ai_result.get('expires_in_days') or 7  # Default to 7 days
        expiry_date = datetime.now().replace(day=datetime.now().day + expires_in).strftime('%Y-%m-%d')
        
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

## Actions

- [ ] I've reviewed this
- [ ] Not interested (archive)
- [ ] Convert to actionable task (requires manual action)

---

**⚠️ This item will auto-archive on {expiry_date} if not reviewed**

---

*Auto-generated by AI from watcher output*
*Mark as done after reviewing - no automated action available*
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
    """Main processor loop - runs every 30 seconds"""
    print("=" * 60)
    print("  Watcher AI Processor")
    print("=" * 60)
    print()
    print("Checking for new watcher output every 30 seconds...")
    print("Press Ctrl+C to stop")
    print()
    
    # Check AI availability
    ai_info = get_model_info()
    if ai_info['fallback_available']:
        print(f"AI Agent: {ai_info['primary']} ({ai_info['model']}) - Ready")
    else:
        print("WARNING: No AI agent available!")
        print()
    
    print()
    
    iteration = 0
    
    while True:
        iteration += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Check for new files
        new_files = get_new_files()
        
        if new_files:
            print(f"\n[{timestamp}] Found {len(new_files)} new file(s)!")
            
            # Process in batches to avoid rate limits
            batch_count = 0
            
            for file in new_files:
                # Check if we hit batch limit
                if batch_count >= MAX_EMAILS_PER_BATCH:
                    print(f"\n[{timestamp}] Reached batch limit ({MAX_EMAILS_PER_BATCH} emails). Waiting 30 seconds...")
                    time.sleep(30)  # Wait for Groq rate limit to reset
                    batch_count = 0  # Reset counter
                
                success = create_task_from_file(file)
                if success:
                    print(f"[{timestamp}] ✓ Processed: {file.name}")
                    batch_count += 1
                else:
                    print(f"[{timestamp}] ✗ Failed: {file.name}")
        else:
            print(f"[{timestamp}] No new files (check #{iteration})")
        
        # Wait 30 seconds between checks
        time.sleep(30)


if __name__ == "__main__":
    try:
        run_processor()
    except KeyboardInterrupt:
        print("\n\nProcessor stopped by user")
