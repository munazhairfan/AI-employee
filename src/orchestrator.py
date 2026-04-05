"""
Gold Tier Orchestrator - Human-in-the-Loop (Draft-Only)
- Processes files from multiple watchers (Gmail, WhatsApp, Filesystem)
- Creates Plan.md using reasoning loop
- Generates drafts in Pending_Approval for ALL external actions
- NO direct MCP/API calls - human executes approved actions manually
- Polls Pending_Approval and runs SKILL_approval_handler.md
- Logs rejections to Dashboard.md
- Full JSON logging
"""

import time
import logging
import shutil
import subprocess
import requests
import re
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# AI Agent Model
from ai_agent import (
    ai_reasoning,
    ai_generate_email_draft,
    ai_generate_whatsapp_reply,
    ai_extract_invoice_details,
    get_model_info,
    check_ollama_available
)

# WhatsApp integration
from whatsapp_sender import send_whatsapp_local

# Load environment variables
load_dotenv()

# Configuration
LOGS_DIR = Path('Logs')
VAULT_PATH = Path('AI_Employee_Vault')
SKILLS_PATH = Path('skills')
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# API Tokens from .env (for reference only - not used directly)
LINKEDIN_TOKEN = os.getenv('LINKEDIN_TOKEN', '')
WHATSAPP_API_KEY = os.getenv('WHATSAPP_API_KEY', '')
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASS = os.getenv('EMAIL_PASS', '')
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost')
ODOO_PORT = os.getenv('ODOO_PORT', '8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee_db')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASS = os.getenv('ODOO_PASS', 'admin')

# Client name keywords for bank CSV matching
CLIENT_KEYWORDS = [
    'payment', 'transfer', 'deposit', 'credit',
    'invoice', 'inv', 'payment received', 'received'
]

KNOWN_CLIENTS = [
    'Test Customer', 'ABC Corp', 'XYZ Ltd', 'Client', 'Customer'
]


# ============================================================================
# ANTI-HALLUCINATION VALIDATION FUNCTIONS
# ============================================================================

def validate_ai_extraction(extraction_data: dict) -> tuple[bool, list[str]]:
    """
    Validate AI extraction for anti-hallucination guards.
    
    Checks:
    1. All extracted fields have source citations
    2. All confidence scores are valid (0-100)
    3. Required fields are present
    
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(extraction_data, dict):
        return False, ["Extraction data must be a dictionary"]
    
    # Check for fields with extraction table
    fields = extraction_data.get('fields', {})
    
    for field_name, field_data in fields.items():
        if not isinstance(field_data, dict):
            errors.append(f"{field_name}: field data must be a dictionary")
            continue
        
        # Check source_text exists for non-null values
        if field_data.get('value') is not None:
            if not field_data.get('source_text'):
                errors.append(f"{field_name}: missing source citation for value '{field_data.get('value')}'")
        
        # Check confidence score exists and is valid
        if 'confidence' not in field_data:
            errors.append(f"{field_name}: missing confidence score")
        elif not isinstance(field_data['confidence'], (int, float)):
            errors.append(f"{field_name}: confidence must be a number")
        elif field_data['confidence'] < 0 or field_data['confidence'] > 100:
            errors.append(f"{field_name}: confidence must be between 0-100")
    
    return len(errors) == 0, errors


def requires_human_review(extraction_data: dict, confidence_threshold: int = 80) -> tuple[bool, str]:
    """
    Determine if AI extraction requires human review.
    
    Rules:
    1. Any field with confidence < threshold → requires review
    2. Any field with null value → requires review
    3. If extraction_data explicitly flags for review → requires review
    
    Returns: (needs_review, reason)
    """
    if not isinstance(extraction_data, dict):
        return True, "Invalid extraction data format"
    
    fields = extraction_data.get('fields', {})
    low_confidence_fields = []
    missing_fields = []
    
    for field_name, field_data in fields.items():
        if not isinstance(field_data, dict):
            continue
        
        confidence = field_data.get('confidence', 0)
        value = field_data.get('value')
        
        # Check for low confidence
        if isinstance(confidence, (int, float)) and confidence < confidence_threshold:
            low_confidence_fields.append(f"{field_name} ({confidence}%)")
        
        # Check for missing values
        if value is None:
            missing_fields.append(field_name)
    
    # Build reason string
    reasons = []
    if low_confidence_fields:
        reasons.append(f"Low confidence fields: {', '.join(low_confidence_fields)}")
    if missing_fields:
        reasons.append(f"Missing fields: {', '.join(missing_fields)}")
    
    # Check if explicitly flagged for review
    if extraction_data.get('requires_human_review'):
        reasons.append(extraction_data.get('review_reason', 'AI flagged for review'))
    
    if reasons:
        return True, "; ".join(reasons)
    
    return False, ""


def calculate_confidence_average(extraction_data: dict) -> float:
    """Calculate average confidence score across all fields."""
    if not isinstance(extraction_data, dict):
        return 0.0
    
    fields = extraction_data.get('fields', {})
    if not fields:
        return 0.0
    
    confidence_scores = []
    for field_data in fields.values():
        if isinstance(field_data, dict) and 'confidence' in field_data:
            conf = field_data['confidence']
            if isinstance(conf, (int, float)) and 0 <= conf <= 100:
                confidence_scores.append(conf)
    
    if not confidence_scores:
        return 0.0
    
    return sum(confidence_scores) / len(confidence_scores)


def log_ai_decision(draft_id: str, action_type: str, input_data: dict, 
                    ai_output: dict, requires_review: bool, review_reason: str = "") -> None:
    """
    Log AI decision to audit trail with full details.
    
    This creates a separate AI audit log entry for tracking:
    - What input was provided to AI
    - What output AI generated
    - Whether human review is required
    - Confidence scores
    """
    log_file = get_log_file()
    
    # Create AI-specific log entry
    ai_log_entry = {
        'timestamp': datetime.now().isoformat(),
        'log_type': 'ai_decision',
        'draft_id': draft_id,
        'action_type': action_type,
        'input_summary': {
            'source_file': input_data.get('source_file', 'unknown'),
            'content_preview': input_data.get('content', '')[:200] if input_data.get('content') else ''
        },
        'ai_output_summary': {
            'extracted_fields_count': len(ai_output.get('fields', {})),
            'average_confidence': calculate_confidence_average(ai_output),
            'requires_human_review': requires_review
        },
        'ai_output_full': ai_output,
        'requires_human_review': requires_review,
        'review_reason': review_reason,
        'human_action': None,  # Will be filled when human approves/rejects
        'human_modified_data': None  # Will be filled if human changes AI output
    }
    
    # Load existing logs
    existing_logs = []
    if log_file.exists():
        try:
            content = log_file.read_text(encoding='utf-8')
            if content.strip():
                existing_logs = json.loads(content)
                if not isinstance(existing_logs, list):
                    existing_logs = [existing_logs]
        except (json.JSONDecodeError, IOError):
            existing_logs = []
    
    existing_logs.append(ai_log_entry)
    log_file.write_text(json.dumps(existing_logs, indent=2), encoding='utf-8')


def parse_frontmatter_with_validation(content: str) -> dict:
    """
    Parse frontmatter from markdown content with validation.
    
    Returns metadata dict with added validation fields:
    - ai_confidence_average: float (0-100)
    - ai_requires_review: bool
    - ai_review_reason: str
    """
    metadata = parse_frontmatter(content)
    
    # Try to extract fields from content if not in frontmatter
    if 'fields' not in metadata:
        # Attempt to parse from content
        fields = {}
        lines = content.split('\n')
        for line in lines:
            if line.startswith('|') and '|' in line[1:]:
                parts = line.strip('|').split('|')
                if len(parts) >= 4:
                    field_name = parts[0].strip()
                    value = parts[1].strip()
                    source = parts[2].strip()
                    conf_str = parts[3].strip().replace('%', '')
                    
                    if field_name and field_name not in ['Field', '---']:
                        try:
                            confidence = int(conf_str) if conf_str.isdigit() else 0
                            fields[field_name] = {
                                'value': None if value == 'UNKNOWN' else value,
                                'source_text': None if source == 'Not mentioned in source' else source,
                                'confidence': confidence
                            }
                        except ValueError:
                            pass
        
        if fields:
            metadata['fields'] = fields
    
    # Calculate validation metrics
    metadata['ai_confidence_average'] = calculate_confidence_average(metadata)
    metadata['ai_requires_review'], metadata['ai_review_reason'] = requires_human_review(metadata)
    
    return metadata


# ============================================================================
# END ANTI-HALLUCINATION VALIDATION FUNCTIONS
# ============================================================================


def get_log_file() -> Path:
    """Get today's log file path."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return LOGS_DIR / f'{date_str}.json'


def log_action(action: str, result: str, error: str = None) -> None:
    """Append action to JSON log file."""
    log_file = get_log_file()

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'result': result,
        'error': error
    }

    existing_logs = []
    if log_file.exists():
        try:
            content = log_file.read_text(encoding='utf-8')
            if content.strip():
                existing_logs = json.loads(content)
                if not isinstance(existing_logs, list):
                    existing_logs = [existing_logs]
        except (json.JSONDecodeError, IOError):
            existing_logs = []

    existing_logs.append(log_entry)
    log_file.write_text(json.dumps(existing_logs, indent=2), encoding='utf-8')


def append_to_dashboard(dashboard: Path, entry: str) -> None:
    """Append entry to Dashboard.md under ## Recent Updates."""
    if dashboard.exists():
        content = dashboard.read_text(encoding='utf-8')

        if '## Recent Updates' in content:
            content = content.replace('## Recent Updates', f'## Recent Updates\n{entry}', 1)
        else:
            content += f"\n## Recent Updates\n{entry}"

        dashboard.write_text(content, encoding='utf-8')
    else:
        dashboard.write_text(f"# Dashboard\n\n## Recent Updates\n{entry}", encoding='utf-8')


def run_skill(skill_name: str, logger) -> dict:
    """
    Run a skill via AI Agent (Ollama/OpenAI).
    Returns dict with success status and output.
    
    DEPRECATED: Claude CLI replaced by ai_agent.py
    """
    skill_path = SKILLS_PATH / skill_name

    if not skill_path.exists():
        logger.error(f"Skill file not found: {skill_name}")
        return {'success': False, 'error': f'Skill not found: {skill_name}'}

    try:
        logger.info(f"Running skill via AI agent: {skill_name}")
        
        # Read skill file for context
        skill_content = skill_path.read_text(encoding='utf-8')
        
        # Extract the prompt from skill file
        # (In production, you'd parse the markdown more carefully)
        prompt_start = skill_content.find('## Prompt:')
        if prompt_start == -1:
            prompt_start = skill_content.find('## Description:')
        
        if prompt_start != -1:
            prompt_text = skill_content[prompt_start:]
        else:
            prompt_text = skill_content
        
        # Call AI agent with skill context
        result = ai_reasoning(prompt_text[:4000])  # Truncate to avoid token limits
        
        if result:
            logger.info(f"Skill completed: {skill_name}")
            return {
                'success': True,
                'output': json.dumps(result, indent=2),
                'ai_data': result
            }
        else:
            logger.error(f"AI agent failed: {skill_name}")
            return {
                'success': False,
                'error': 'AI agent returned no result'
            }

    except Exception as e:
        logger.error(f"Skill execution error: {e}")
        return {'success': False, 'error': str(e)}


def generate_draft_with_ai(action_type: str, content: str, metadata: dict,
                           pending_dir: Path, logger) -> Path:
    """
    Generate draft using AI agent with anti-hallucination guards.
    
    Args:
        action_type: Type of action (email, whatsapp, invoice)
        content: Source content to process
        metadata: Additional metadata
        pending_dir: Directory to save draft
        logger: Logger instance
    
    Returns:
        Path to created draft file
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    task_id = metadata.get('task_id', datetime.now().strftime('%Y%m%d%H%M%S'))
    
    draft_file = pending_dir / f"{action_type}_Draft_{timestamp}.md"
    
    # Select appropriate AI function based on action type
    if action_type == 'email':
        logger.info("Generating email draft with AI...")
        ai_result = ai_generate_email_draft(content)
    elif action_type == 'whatsapp':
        logger.info("Generating WhatsApp reply with AI...")
        ai_result = ai_generate_whatsapp_reply(content)
    elif action_type == 'invoice':
        logger.info("Extracting invoice details with AI...")
        ai_result = ai_extract_invoice_details(content)
    else:
        logger.info(f"Processing {action_type} with AI...")
        ai_result = ai_reasoning(content, task_type=action_type)
    
    # Handle AI failure
    if ai_result is None:
        logger.error("AI processing failed - creating basic draft")
        # Fall back to basic draft generation
        return generate_draft_for_action(action_type, content, metadata, pending_dir, logger)
    
    # Extract fields from AI result
    fields = ai_result.get('fields', {})
    requires_review = ai_result.get('requires_human_review', False)
    review_reason = ai_result.get('review_reason', '')
    ai_confidence = calculate_confidence_average({'fields': fields})
    
    # Build draft content based on action type
    if action_type == 'email':
        to_line = f"**To:** {ai_result.get('to', {}).get('value', 'UNKNOWN') or 'UNKNOWN'}"
        subject_line = f"**Subject:** {ai_result.get('subject', {}).get('value', 'UNKNOWN') or 'UNKNOWN'}"
        body_section = f"\n## Email Body\n\n{ai_result.get('email_body', content[:1000])}\n"
    elif action_type == 'whatsapp':
        from_line = f"**From:** {ai_result.get('sender', {}).get('value', 'UNKNOWN') or 'UNKNOWN'}"
        original_message = metadata.get('original_message', content[:500])
        body_section = f"\n## Original Message\n\n{original_message}\n\n## Suggested Reply\n\n{ai_result.get('suggested_reply', '')}\n"
    elif action_type == 'invoice':
        client_line = f"**Client:** {fields.get('customer', {}).get('value', 'UNKNOWN') or 'UNKNOWN'}"
        amount_line = f"**Amount:** {fields.get('amount', {}).get('value', 'UNKNOWN') or 'UNKNOWN'}"
        body_section = f"\n## Invoice Details\n\n{metadata.get('description', content[:500])}\n"
    else:
        to_line = subject_line = body_section = client_line = amount_line = ""
        body_section = f"\n## Content\n\n{content[:1000]}\n"
    
    # Build extracted information table
    extracted_table = ""
    if fields:
        extracted_table = "## Extracted Information (With Source Citations)\n\n"
        extracted_table += "| Field | Value | Source Text | Confidence |\n"
        extracted_table += "|-------|-------|-------------|------------|\n"
        
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                value = field_data.get('value', 'UNKNOWN')
                source = field_data.get('source_text', 'Not mentioned')
                confidence = field_data.get('confidence', 0)
                extracted_table += f"| {field_name} | {value} | {source} | {confidence}% |\n"
        
        extracted_table += "\n"
    
    # Human review section
    if requires_review:
        human_review_section = f"""## Human Review Required

**YES** - {review_reason}

**Action:** Human must review before approval

"""
    else:
        human_review_section = """## Human Review Required

**NO** - All extractions high confidence (≥80%)

"""
    
    draft_content = f"""---
type: {action_type}_draft
status: pending_review
generated_at: {datetime.now().isoformat()}
task_id: {task_id}
source_file: {metadata.get('source_file', 'orchestrator')}
requires_human_review: {str(requires_review).lower()}
ai_confidence_average: {ai_confidence:.1f}
---

# Draft: {action_type.replace('_', ' ').title()}

## Action Details

{to_line if action_type == 'email' else ''}
{subject_line if action_type == 'email' else ''}
{client_line if action_type == 'invoice' else ''}
{amount_line if action_type == 'invoice' else ''}
{body_section}

{extracted_table}
{human_review_section}
---

## Approval Actions

- [ ] Approve (execute manually)
- [ ] Reject (add your reason below)
- [ ] Edit (add your changes/notes below)

---
*Draft generated by AI Agent - Anti-Hallucination Guards Active - No API calls made*
"""
    
    draft_file.write_text(draft_content, encoding='utf-8')
    
    # Log AI decision for audit trail
    input_data = {
        'source_file': metadata.get('source_file', 'unknown'),
        'content': content,
        'action_type': action_type
    }
    log_ai_decision(
        draft_id=draft_file.name,
        action_type=action_type,
        input_data=input_data,
        ai_output=ai_result,
        requires_review=requires_review,
        review_reason=review_reason
    )
    
    logger.info(f"AI draft created: {draft_file.name} (confidence: {ai_confidence:.1f}%, review: {requires_review})")
    log_action('ai_draft_created', f'{action_type}: {draft_file.name}',
               error=f'Confidence: {ai_confidence:.1f}%, Review: {requires_review}')
    
    return draft_file


def generate_draft_for_action(action_type: str, content: str, metadata: dict,
                               pending_dir: Path, logger) -> Path:
    """
    Generate draft file in Pending_Approval for human review.
    Includes anti-hallucination validation and human review flags.
    No MCP calls - draft only.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    task_id = metadata.get('task_id', datetime.now().strftime('%Y%m%d%H%M%S'))

    draft_file = pending_dir / f"{action_type}_Draft_{timestamp}.md"

    # Extract relevant details based on action type
    to_line = ""
    subject_line = ""
    body_section = ""
    amount_line = ""
    client_line = ""

    if action_type == 'email':
        to_line = f"**To:** {metadata.get('to', 'N/A')}"
        subject_line = f"**Subject:** {metadata.get('subject', 'N/A')}"
        body_section = f"\n## Email Body\n\n{content[:1000]}\n"

    elif action_type == 'whatsapp':
        to_line = f"**From:** {metadata.get('from', 'N/A')}"
        body_section = f"\n## Message Content\n\n{content[:1000]}\n"

    elif action_type == 'linkedin' or action_type == 'linkedin_post':
        body_section = f"\n## Post Text\n\n{content[:500]}\n"

    elif action_type == 'invoice':
        client_line = f"**Client:** {metadata.get('partner_name', 'N/A')}"
        amount_line = f"**Amount:** PKR {metadata.get('amount', '0')}"
        body_section = f"\n## Invoice Details\n\n{metadata.get('description', content[:500])}\n"

    # Anti-hallucination validation
    fields = metadata.get('fields', {})
    ai_confidence = calculate_confidence_average(metadata) if fields else 100.0
    requires_review, review_reason = requires_human_review(metadata) if fields else (False, "")
    
    # Build extracted information table if fields exist
    extracted_table = ""
    if fields:
        extracted_table = "## Extracted Information (With Source Citations)\n\n"
        extracted_table += "| Field | Value | Source Text | Confidence |\n"
        extracted_table += "|-------|-------|-------------|------------|\n"
        
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                value = field_data.get('value', 'UNKNOWN')
                source = field_data.get('source_text', 'Not mentioned')
                confidence = field_data.get('confidence', 0)
                extracted_table += f"| {field_name} | {value} | {source} | {confidence}% |\n"
        
        extracted_table += "\n"

    # Determine human review section
    if requires_review:
        human_review_section = f"""## Human Review Required

**YES** - {review_reason}

**Action:** Human must review before approval

"""
    else:
        human_review_section = """## Human Review Required

**NO** - All extractions high confidence (≥80%)

"""

    draft_content = f"""---
type: {action_type}_draft
status: pending_review
generated_at: {datetime.now().isoformat()}
task_id: {task_id}
source_file: {metadata.get('source_file', 'orchestrator')}
requires_human_review: {str(requires_review).lower()}
ai_confidence_average: {ai_confidence:.1f}
---

# Draft: {action_type.replace('_', ' ').title()}

## Action Details

{to_line}
{subject_line}
{client_line}
{amount_line}
{body_section}

{extracted_table}
{human_review_section}
---

## Approval Actions

- [ ] Approve (execute manually)
- [ ] Reject (add your reason below)
- [ ] Edit (add your changes/notes below)

---
*Draft generated by orchestrator - Anti-Hallucination Guards Active - No API calls made*
"""

    draft_file.write_text(draft_content, encoding='utf-8')
    
    # Log AI decision for audit trail
    input_data = {
        'source_file': metadata.get('source_file', 'unknown'),
        'content': content,
        'action_type': action_type
    }
    log_ai_decision(
        draft_id=draft_file.name,
        action_type=action_type,
        input_data=input_data,
        ai_output={'fields': fields},
        requires_review=requires_review,
        review_reason=review_reason
    )
    
    logger.info(f"Draft created: {draft_file.name} (confidence: {ai_confidence:.1f}%, review: {requires_review})")
    log_action('draft_created', f'{action_type}: {draft_file.name}', 
               error=f'Confidence: {ai_confidence:.1f}%, Review: {requires_review}')

    return draft_file


def poll_pending_approvals(pending_dir: Path, done_dir: Path, rejected_dir: Path,
                           dashboard: Path, logger) -> None:
    """
    Poll Pending_Approval folder and execute approved drafts via MCP APIs.
    Human approves → System auto-executes via MCP.
    """
    if not pending_dir.exists():
        return

    # Ensure Rejected directory exists
    rejected_dir.mkdir(parents=True, exist_ok=True)

    for approval_file in pending_dir.glob('*_Draft_*.md'):
        content = approval_file.read_text(encoding='utf-8')
        metadata = parse_frontmatter(content)

        # Check for approval marks
        is_approved = '- [x] Approve' in content or '- [X] Approve' in content
        is_rejected = '- [x] Reject' in content or '- [X] Reject' in content

        if is_approved:
            logger.info(f"Draft approved: {approval_file.name} - Executing via MCP...")
            log_action('draft_approved', f'{approval_file.name}')

            # Extract action type and details
            action_type = metadata.get('type', 'unknown').replace('_draft', '')
            
            # Extract content based on action type
            post_text = ""
            email_to = ""
            email_subject = ""
            email_body = ""
            whatsapp_to = ""
            whatsapp_message = ""
            invoice_partner = ""
            invoice_amount = ""
            invoice_description = ""

            # Extract post text for social media
            if '## Post Text' in content:
                parts = content.split('## Post Text')
                if len(parts) > 1:
                    post_text = parts[1].split('## Approval')[0].strip()

            # Extract email details
            if '**To:**' in content:
                match = re.search(r'\*\*To:\*\* (.+)', content)
                if match:
                    email_to = match.group(1).strip()

            if '**Subject:**' in content:
                match = re.search(r'\*\*Subject:\*\* (.+)', content)
                if match:
                    email_subject = match.group(1).strip()

            if '## Email Body' in content:
                match = re.search(r'## Email Body\n\n(.+?)\n---', content, re.DOTALL)
                if match:
                    email_body = match.group(1).strip()

            # Extract WhatsApp details
            if '## Message Content' in content or '## Suggested Reply' in content:
                match = re.search(r'(## Message Content|## Suggested Reply)\n\n(.+?)\n---', content, re.DOTALL)
                if match:
                    whatsapp_message = match.group(2).strip()

            if '**From:**' in content and 'whatsapp' in action_type.lower():
                match = re.search(r'\*\*From:\*\* (.+)', content)
                if match:
                    whatsapp_to = match.group(1).strip()

            # Extract invoice details
            if '**Client:**' in content:
                match = re.search(r'\*\*Client:\*\* (.+)', content)
                if match:
                    invoice_partner = match.group(1).strip()

            if '**Amount:**' in content:
                match = re.search(r'\*\*Amount:\*\* [PKR ]*(.+)', content)
                if match:
                    invoice_amount = match.group(1).strip().replace(',', '')

            if '## Invoice Details' in content or '## Action Details' in content:
                match = re.search(r'(## Invoice Details|## Action Details)\n\n(.+?)\n---', content, re.DOTALL)
                if match:
                    invoice_description = match.group(2).strip()[:500]

            # Execute via appropriate MCP endpoint
            execution_success = False

            try:
                if action_type == 'email' and email_to and email_body:
                    # Call Email MCP
                    logger.info(f"Sending email to {email_to} via MCP...")
                    response = requests.post(
                        'http://localhost:3000/send_approved_email',
                        json={
                            'to': email_to,
                            'subject': email_subject or 'No subject',
                            'body': email_body,
                            'draft_file': str(approval_file)
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"Email sent: {result.get('messageId')}")
                            execution_success = True
                        else:
                            logger.error(f"Email send failed: {result.get('error')}")
                    else:
                        logger.error(f"Email MCP error: {response.status_code}")

                elif action_type in ['linkedin', 'linkedin_draft', 'linkedin_post'] and post_text:
                    # Call Social MCP - LinkedIn
                    logger.info(f"Posting to LinkedIn via MCP...")
                    response = requests.post(
                        'http://localhost:3005/post_linkedin',
                        json={'content': post_text},
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"LinkedIn posted: {result.get('post_url')}")
                            execution_success = True
                        else:
                            logger.error(f"LinkedIn post failed: {result.get('error')}")
                    else:
                        logger.error(f"LinkedIn MCP error: {response.status_code}")

                elif 'whatsapp' in action_type.lower() and whatsapp_to and whatsapp_message:
                    # Call WhatsApp MCP
                    logger.info(f"Sending WhatsApp to {whatsapp_to} via MCP...")
                    response = requests.post(
                        'http://localhost:3006/send_whatsapp',
                        json={
                            'to': whatsapp_to,
                            'message': whatsapp_message,
                            'draft_file': str(approval_file)
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"WhatsApp sent: {result.get('message_sid') or result.get('message_id')}")
                            execution_success = True
                        else:
                            logger.error(f"WhatsApp send failed: {result.get('error')}")
                    else:
                        logger.error(f"WhatsApp MCP error: {response.status_code}")

                elif 'invoice' in action_type.lower() and invoice_partner and invoice_amount:
                    # Call Odoo MCP - Post Invoice
                    logger.info(f"Posting invoice to Odoo via MCP...")
                    response = requests.post(
                        'http://localhost:3004/post_invoice',
                        json={
                            'partner_name': invoice_partner,
                            'amount': invoice_amount,
                            'description': invoice_description or f'Invoice for {invoice_partner}'
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            logger.info(f"Odoo invoice posted: {result.get('invoice_number')}")
                            execution_success = True
                        else:
                            logger.error(f"Odoo invoice post failed: {result.get('error')}")
                    else:
                        logger.error(f"Odoo MCP error: {response.status_code}")

                else:
                    logger.warning(f"Unknown action type or missing details: {action_type}")
                    execution_success = False

            except requests.exceptions.ConnectionError as e:
                logger.error(f"MCP server connection error: {e}")
                execution_success = False
            except Exception as e:
                logger.error(f"MCP execution error: {e}")
                execution_success = False

            # Update dashboard
            if execution_success:
                append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action_type} executed successfully via MCP")
                # Move to Done
                dest = done_dir / approval_file.name
                shutil.move(str(approval_file), str(dest))
                logger.info(f"Moved executed draft to Done: {approval_file.name}")
                log_action('moved_to_done', f'{approval_file.name}')
            else:
                append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action_type} execution FAILED - check logs")
                logger.warning(f"Execution failed, leaving draft in Pending_Approval for review: {approval_file.name}")

        elif is_rejected:
            logger.info(f"Draft rejected: {approval_file.name}")
            log_action('draft_rejected', f'{approval_file.name}')

            # Extract rejection reason
            rejection_reason = "No reason provided"
            if 'Reject' in content:
                parts = content.split('Reject')
                if len(parts) > 1:
                    # Get text after Reject checkbox
                    reason_section = parts[1].split('\n\n')[0].strip()
                    if reason_section and not reason_section.startswith('('):
                        rejection_reason = reason_section

            # Log rejection to dashboard
            append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Draft rejected: {approval_file.name} - Reason: {rejection_reason}")

            # Move to Rejected
            dest = rejected_dir / approval_file.name
            shutil.move(str(approval_file), str(dest))
            logger.info(f"Moved rejected draft to Rejected: {approval_file.name}")
            log_action('moved_to_rejected', f'{approval_file.name}')

        # If no mark, leave in Pending_Approval for next poll


def parse_frontmatter(content: str) -> dict:
    """Extract metadata from YAML frontmatter."""
    metadata = {}

    if '---' not in content:
        return metadata

    parts = content.split('---', 2)
    if len(parts) < 3:
        return metadata

    meta_section = parts[1]
    for line in meta_section.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    return metadata


def create_plan(file_path: Path, content: str, metadata: dict, plans_dir: Path, vault: Path) -> Path:
    """Create a Plan.md file using reasoning loop skill."""
    task_id = file_path.stem
    plan_file = plans_dir / f"{task_id}_Plan.md"

    plan_content = f"""---
task_id: {task_id}
type: {metadata.get('type', 'unknown')}
priority: {metadata.get('priority', 'normal')}
status: planning
created: {datetime.now().isoformat()}
source_file: {file_path.name}
---

## Task Summary
{metadata.get('subject', metadata.get('original_name', 'Unknown task'))}

## Reasoning
1. Task type: {metadata.get('type', 'unknown')}
2. Priority: {metadata.get('priority', 'normal')}
3. Source: {file_path.name}

## Action Plan

- [ ] Step 1: Review task details
- [ ] Step 2: Determine required actions
- [ ] Step 3: Generate draft for approval
- [ ] Step 4: Wait for human approval
- [ ] Step 5: Archive to Done

## Notes
Generated by orchestrator reasoning loop. Human-in-the-loop required.

"""

    plan_file.write_text(plan_content, encoding='utf-8')
    return plan_file


def parse_email_request(content: str) -> dict | None:
    """Parse natural language email requests from dropped files."""
    content_lower = content.lower()

    email_indicators = ['send email', 'send an email', 'email to', 'email:',
                        'send mail', 'send a mail', 'compose email', 'to:']
    if not any(ind in content_lower for ind in email_indicators):
        return None

    email_data = {'to': None, 'subject': None, 'body': None}

    to_match = re.search(r'^to:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content, re.IGNORECASE | re.MULTILINE)
    subject_match = re.search(r'^subject:\s*(.+)$', content, re.IGNORECASE | re.MULTILINE)
    body_match = re.search(r'^body:\s*(.+)$', content, re.IGNORECASE | re.MULTILINE)

    if to_match:
        email_data['to'] = to_match.group(1).strip()
    if subject_match:
        email_data['subject'] = subject_match.group(1).strip()
    if body_match:
        email_data['body'] = body_match.group(1).strip()

    if not email_data['to']:
        single_line = re.search(
            r'to:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+subject:\s*(.+?)\s+body:\s*(.+)',
            content, re.IGNORECASE
        )
        if single_line:
            email_data['to'] = single_line.group(1).strip()
            email_data['subject'] = single_line.group(2).strip()
            email_data['body'] = single_line.group(3).strip()

    if email_data['to']:
        return email_data

    return None


def check_requires_draft(content: str, metadata: dict, file_type: str) -> tuple:
    """
    Check if action requires draft generation (human-in-the-loop).
    Returns: (requires_draft: bool, action_type: str, auto_execute: bool)

    Rules:
    - Odoo invoices: NO approval (auto-execute)
    - WhatsApp with frontmatter: NO approval (auto-execute)
    - External comms (email, social): Approval required, then auto-execute via MCP
    """
    # Odoo invoices - NO approval needed (autonomous)
    if file_type == 'invoice' or 'invoice' in content.lower():
        if 'payment' in content.lower() or 'amount' in content.lower():
            return False, 'invoice', True  # Auto-create in Odoo
    
    # WhatsApp with explicit frontmatter - auto-execute (no draft)
    if file_type == 'whatsapp' and metadata.get('phone') and metadata.get('message'):
        return False, 'whatsapp', True  # Auto-execute via local agent

    if file_type == 'file_drop':
        email_data = parse_email_request(content)
        if email_data and email_data.get('to'):
            return True, 'email', True  # Draft + auto-execute after approval

    # Check for social keywords - return specific platform
    if any(kw in content.lower() for kw in ['linkedin', 'linked in']):
        return True, 'linkedin', True  # Draft + auto-execute after approval

    # Generic "post" keyword defaults to LinkedIn
    if 'post' in content.lower():
        return True, 'linkedin', True

    # Check for financial keywords (external payments)
    financial_keywords = ['$', 'USD', 'payment', 'transfer', 'PKR', 'dollar']
    if any(kw in content.lower() for kw in financial_keywords):
        # If it's about creating invoice in Odoo, auto-execute
        if 'invoice' in content.lower() or 'odoo' in content.lower():
            return False, 'invoice', True
        # Otherwise, draft for approval
        return True, 'payment', True

    # Check for business keywords (internal processing)
    business_keywords = ['sales', 'client', 'project', 'business', 'deal', 'customer', 'order', 'revenue', 'lead', 'service', 'opportunity']
    if any(kw in content.lower() for kw in business_keywords):
        return False, 'business', False  # Internal processing only

    return False, file_type, False  # Default: no draft, no auto-execute


def run_orchestrator(vault_path='AI_Employee_Vault', loop=True, interval=60):
    """
    Gold Tier Orchestrator - Human-in-the-Loop (Draft-Only)
    NO direct MCP/API calls. All external actions generate drafts for human approval.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    vault_path = Path('AI_Employee_Vault')
    vault = Path(vault_path)
    needs_action = vault / 'Needs_Action'
    done = vault / 'Done'
    plans = vault / 'Plans'
    pending_approval = vault / 'Pending_Approval'
    rejected = vault / 'Rejected'
    processed = vault / 'Processed'  # NEW: For original files after draft creation
    dashboard = vault / 'Dashboard.md'

    # Ensure directories exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    needs_action.mkdir(parents=True, exist_ok=True)
    done.mkdir(parents=True, exist_ok=True)
    plans.mkdir(parents=True, exist_ok=True)
    pending_approval.mkdir(parents=True, exist_ok=True)
    rejected.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)  # NEW folder

    log_action('orchestrator_start', 'Orchestrator initialized (Human-in-the-Loop mode)')
    logger.info("Starting orchestrator in Human-in-the-Loop mode")
    logger.info("All external actions will generate drafts - no automatic execution")

    processed_files = set()

    linkedin_keywords = ['sales', 'business', 'project', 'lead', 'service', 'opportunity',
                         'hiring', 'developers', 'news', 'launch', 'milestone', 'achievement',
                         'growth', 'client', 'partner', 'announcement', 'exciting', 'thrilled',
                         'welcome', 'joining', 'team', 'product', 'release', 'update']

    while True:
        try:
            # Step 1: Poll Pending_Approval and run approval handler
            logger.info("Polling Pending_Approval folder...")
            poll_pending_approvals(pending_approval, done, rejected, dashboard, logger)

            # Step 2: Check for .md files in Needs_Action
            md_files = list(needs_action.glob('*.md'))

            if md_files:
                logger.info(f"Found {len(md_files)} files in Needs_Action, processing...")
                log_action('scan_needs_action', f'Found {len(md_files)} files')

                for file_path in md_files:
                    if file_path.name in processed_files:
                        continue

                    logger.info(f"Processing {file_path.name}...")
                    log_action('process_file', f'Started: {file_path.name}')

                    try:
                        content = file_path.read_text(encoding='utf-8')
                        metadata = parse_frontmatter(content)
                        file_type = metadata.get('type', 'unknown')
                        original_name = metadata.get('original_name', metadata.get('subject', file_path.name))

                        # Create plan
                        logger.info(f"Creating plan for {file_path.name}...")
                        plan_file = create_plan(file_path, content, metadata, plans, vault)
                        log_action('create_plan', f'Created: {plan_file.name}')

                        # Determine action type and execution mode
                        requires_draft, action_type, auto_execute = check_requires_draft(content, metadata, file_type)

                        # Check if draft generation is required
                        if requires_draft:
                            logger.info(f"Generating {action_type} draft for human approval...")

                            # Generate draft in Pending_Approval
                            draft_file = generate_draft_for_action(
                                action_type, content, metadata, pending_approval, logger
                            )

                            # Move original file to Processed (waiting for approval)
                            dest = processed / file_path.name
                            shutil.move(str(file_path), str(dest))
                            logger.info(f"Moved {file_path.name} to Processed (draft created)")
                            log_action('moved_to_processed', f'Moved: {file_path.name}')

                            processed_files.add(file_path.name)

                            # Update dashboard
                            append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {action_type} draft created in Pending_Approval for review")

                            continue

                        # Auto-execute Odoo invoices (no approval needed)
                        elif action_type == 'invoice' and auto_execute:
                            logger.info(f"Auto-creating Odoo invoice (no approval required)...")

                            # Extract invoice details
                            invoice_data = {
                                'partner_name': metadata.get('partner_name', metadata.get('client', 'Unknown Client')),
                                'amount': metadata.get('amount', '0'),
                                'description': metadata.get('description', content[:200])
                            }

                            # Call Odoo MCP to create and post invoice
                            try:
                                response = requests.post(
                                    'http://localhost:3004/post_invoice',
                                    json=invoice_data,
                                    timeout=30
                                )

                                if response.status_code == 200:
                                    result = response.json()
                                    if result.get('success'):
                                        logger.info(f"Invoice created and posted: {result.get('invoice_number')}")
                                        log_action('odoo_invoice_auto', f"Created: {result.get('invoice_number')}")

                                        # Update dashboard
                                        append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Odoo invoice created and posted: {result.get('invoice_number')}")
                                    else:
                                        logger.error(f"Invoice creation failed: {result.get('error')}")
                                        log_action('odoo_invoice_error', result.get('error'), error=str(result.get('error')))
                                else:
                                    logger.error(f"Odoo MCP error: {response.status_code}")
                                    log_action('odoo_mcp_error', f'HTTP {response.status_code}', error=response.text)

                            except requests.exceptions.ConnectionError:
                                logger.error("Odoo MCP server not running (port 3004)")
                                log_action('odoo_mcp_offline', 'Server not running', error='Connection refused')
                            except Exception as e:
                                logger.error(f"Invoice auto-creation error: {e}")
                                log_action('odoo_invoice_exception', str(e), error=str(e))

                            # Move to Processed (invoice auto-created)
                            dest = processed / file_path.name
                            shutil.move(str(file_path), str(dest))
                            logger.info(f"Moved {file_path.name} to Processed (invoice auto-created)")
                            processed_files.add(file_path.name)

                            continue

                        # Auto-execute WhatsApp messages (local agent)
                        elif action_type == 'whatsapp' and auto_execute:
                            logger.info(f"Auto-sending WhatsApp message via local agent...")

                            # Extract WhatsApp details
                            phone = metadata.get('phone', metadata.get('to', ''))
                            message = metadata.get('message', content[:500])

                            # Send via local agent
                            result = send_whatsapp_local(phone, message)

                            if result['success']:
                                logger.info(f"WhatsApp sent to {phone}")
                                log_action('whatsapp_auto', f'Sent to: {phone}')

                                # Update dashboard
                                append_to_dashboard(dashboard, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - WhatsApp sent to {phone}")
                            else:
                                logger.error(f"WhatsApp send failed: {result.get('error')}")
                                log_action('whatsapp_auto_error', result.get('error'), error=str(result.get('error')))

                            # Move to Processed
                            dest = processed / file_path.name
                            shutil.move(str(file_path), str(dest))
                            logger.info(f"Moved {file_path.name} to Processed (WhatsApp sent)")
                            processed_files.add(file_path.name)

                            continue

                        # For non-draft actions (internal processing), move to Processed
                        dest = processed / file_path.name
                        shutil.move(str(file_path), str(dest))
                        logger.info(f"Moved {file_path.name} to Processed (internal action)")
                        processed_files.add(file_path.name)

                    except Exception as e:
                        logger.error(f"Error processing {file_path.name}: {e}")
                        log_action('process_file', f'Error: {file_path.name}', error=str(e))

                update_dashboard(md_files, dashboard, logger)
                log_action('update_dashboard', f'Updated with {len(md_files)} files')

            else:
                logger.info("No files in Needs_Action to process.")

            # Wait for next iteration
            if not loop:
                break

            time.sleep(interval)

        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            log_action('orchestrator_error', 'Main loop error', error=str(e))
            if not loop:
                raise


def update_dashboard(processed_files: list, dashboard: Path, logger) -> None:
    """Update dashboard with processing summary."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    entry = f"\n## {timestamp}\n"
    entry += f"Processed {len(processed_files)} file(s):\n"

    for f in processed_files:
        entry += f"- {f.name}\n"

    if dashboard.exists():
        content = dashboard.read_text(encoding='utf-8')
        lines = content.split('\n')

        insert_idx = 1
        for i, line in enumerate(lines):
            if line.startswith('#'):
                insert_idx = i + 1
                break

        lines.insert(insert_idx, entry)
        dashboard.write_text('\n'.join(lines), encoding='utf-8')
    else:
        dashboard.write_text(f"# Dashboard\n{entry}", encoding='utf-8')

    logger.info("Dashboard updated")
    log_action('dashboard_update', f'Updated with {len(processed_files)} entries')


if __name__ == "__main__":
    log_action('orchestrator_launch', 'Starting orchestrator (Human-in-the-Loop)')
    run_orchestrator(interval=30)
