"""
Gold Tier Orchestrator
- Processes files from multiple watchers (Gmail, WhatsApp, Filesystem)
- Creates Plan.md using reasoning loop
- Handles approval workflow for sensitive actions
- Calls MCP for approved external actions with retries
- Generates LinkedIn posts for business activity
- Full JSON logging with retry logic
- Bank CSV processing for Odoo invoice creation
"""

import time
import logging
import shutil
import subprocess
import requests
import re
import json
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pyperclip
import webbrowser

# Load environment variables
load_dotenv()

# Configuration
LOGS_DIR = Path('Logs')
VAULT_PATH = Path('AI_Employee_Vault')
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Odoo MCP configuration
ODOO_MCP_URL = 'http://localhost:3004'

# Client name keywords for bank CSV matching
CLIENT_KEYWORDS = [
    'payment', 'transfer', 'deposit', 'credit',
    'invoice', 'inv', 'payment received', 'received'
]

KNOWN_CLIENTS = [
    'Test Customer', 'ABC Corp', 'XYZ Ltd', 'Client', 'Customer'
]


def get_log_file() -> Path:
    """Get today's log file path."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return LOGS_DIR / f'{date_str}.json'


def get_odoo_log_file() -> Path:
    """Get today's Odoo-specific log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    return LOGS_DIR / f'odoo_{date_str}.json'


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


def log_odoo_action(action: str, result: dict) -> None:
    """Log Odoo MCP action to dedicated Odoo log."""
    log_file = get_odoo_log_file()

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'result': result
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


def retry_request(method: str, url: str, max_retries: int = MAX_RETRIES, **kwargs) -> dict:
    """
    Make HTTP request with retry logic.
    """
    log_action(f'{method.upper()} {url}', 'initiated')

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)

            if response.status_code < 500:
                result = {
                    'success': response.ok,
                    'status_code': response.status_code,
                    'data': response.text,
                    'error': None if response.ok else f'HTTP {response.status_code}'
                }
                log_action(f'{method.upper()} {url}', f'completed: {response.status_code}',
                          error=None if response.ok else result['error'])
                return result

            log_action(f'{method.upper()} {url}', f'retry {attempt}/{max_retries}',
                      error=f'HTTP {response.status_code}')

        except requests.exceptions.Timeout as e:
            log_action(f'{method.upper()} {url}', f'retry {attempt}/{max_retries}', error=f'Timeout: {e}')
        except requests.exceptions.ConnectionError as e:
            log_action(f'{method.upper()} {url}', f'retry {attempt}/{max_retries}', error=f'Connection: {e}')
        except Exception as e:
            log_action(f'{method.upper()} {url}', f'retry {attempt}/{max_retries}', error=str(e))

        if attempt < max_retries:
            time.sleep(RETRY_DELAY * attempt)

    result = {
        'success': False,
        'status_code': None,
        'data': None,
        'error': f'Failed after {max_retries} retries'
    }
    log_action(f'{method.upper()} {url}', 'failed', error=result['error'])
    return result


def retry_odoo_mcp(endpoint: str, json_data: dict, max_retries: int = MAX_RETRIES) -> dict:
    """
    Make Odoo MCP request with retry logic (3 retries).
    Logs response to odoo_{date}.json.
    """
    url = f'{ODOO_MCP_URL}{endpoint}'
    
    for attempt in range(1, max_retries + 1):
        try:
            log_action(f'ODOO_MCP {endpoint}', f'Attempt {attempt}/{max_retries}')
            
            response = requests.post(url, json=json_data, timeout=30)
            result = response.json() if response.ok else {'error': response.text}
            
            # Log to Odoo-specific log
            log_odoo_action(endpoint, {
                'attempt': attempt,
                'request': json_data,
                'response': result,
                'status_code': response.status_code
            })
            
            if response.status_code == 200 and result.get('success'):
                log_action(f'ODOO_MCP {endpoint}', f'Success: {result}')
                return result
            
            log_action(f'ODOO_MCP {endpoint}', f'Retry: {result.get("error", "Unknown error")}')
            
        except requests.exceptions.Timeout as e:
            log_action(f'ODOO_MCP {endpoint}', f'Timeout: {e}')
        except requests.exceptions.ConnectionError as e:
            log_action(f'ODOO_MCP {endpoint}', f'Connection error: {e}')
        except Exception as e:
            log_action(f'ODOO_MCP {endpoint}', f'Error: {e}')
        
        if attempt < max_retries:
            time.sleep(RETRY_DELAY * attempt)
    
    return {'success': False, 'error': f'Failed after {max_retries} retries'}


def extract_client_name(description: str) -> str | None:
    """Extract client name from transaction description."""
    desc_lower = description.lower()
    
    for client in KNOWN_CLIENTS:
        if client.lower() in desc_lower:
            return client
    
    for keyword in CLIENT_KEYWORDS:
        if keyword in desc_lower:
            words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', description)
            if words:
                return ' '.join(words[:2])
    
    return None


def process_bank_csv(vault: Path, dashboard: Path, logger) -> dict:
    """
    Process bank CSV and create invoices via Odoo MCP.
    """
    result = {
        'success': False,
        'processed': 0,
        'invoices_created': 0,
        'unmatched': 0,
        'errors': []
    }
    
    # Find CSV in Drop or Accounting
    search_paths = [vault / 'Drop', vault / 'Accounting']
    csv_files = []
    
    for search_path in search_paths:
        if search_path.exists():
            csv_files.extend(search_path.glob('*.csv'))
    
    if not csv_files:
        return result
    
    # Process latest CSV
    csv_path = max(csv_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Processing bank CSV: {csv_path.name}")
    log_action('bank_csv_processing', f'Started: {csv_path.name}')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            transactions = list(reader)
        
        logger.info(f"Found {len(transactions)} transactions")
        
        for txn in transactions:
            amount = float(txn.get('amount', 0))
            description = txn.get('description', '')
            
            # Skip negative amounts
            if amount <= 0:
                continue
            
            # Check for payment keywords
            desc_lower = description.lower()
            is_payment = any(kw in desc_lower for kw in CLIENT_KEYWORDS)
            
            if not is_payment:
                result['unmatched'] += 1
                continue
            
            # Extract client name
            client_name = extract_client_name(description)
            if not client_name:
                result['unmatched'] += 1
                continue
            
            # Create invoice via Odoo MCP
            logger.info(f"Creating invoice for {client_name}: PKR {amount}")
            
            invoice_result = retry_odoo_mcp('/create_invoice', {
                'partner_name': client_name,
                'amount': amount,
                'description': f'Payment received - {description}'
            })
            
            if invoice_result.get('success'):
                result['invoices_created'] += 1
                result['processed'] += 1
                
                # Update dashboard
                invoice_id = invoice_result.get('invoice_id', 'N/A')
                summary = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Odoo Invoice\n- **Invoice ID:** {invoice_id}\n- **Client:** {client_name}\n- **Amount:** PKR {amount:,.2f}\n- **Source:** {csv_path.name}\n"
                
                append_to_dashboard(dashboard, summary)
                logger.info(f"Invoice created: {invoice_id}")
            else:
                result['errors'].append(f"Failed for {client_name}: {invoice_result.get('error')}")
        
        result['success'] = result['invoices_created'] > 0
        log_action('bank_csv_processing', f'Completed: {result}')
        
    except Exception as e:
        logger.error(f"Bank CSV processing error: {e}")
        result['errors'].append(str(e))
        log_action('bank_csv_error', str(e), error=str(e))
    
    return result


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


def run_orchestrator(vault_path='AI_Employee_Vault', loop=True, interval=60):
    """
    Gold Tier Orchestrator with retry logic and JSON logging.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    vault_path = Path('AI_Employee_Vault')
    vault = Path(vault_path)
    needs_action = vault / 'Needs_Action'
    done = vault / 'Done'
    plans = vault / 'Plans'
    pending_approval = vault / 'Pending_Approval'
    dashboard = vault / 'Dashboard.md'

    # Ensure directories exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    needs_action.mkdir(parents=True, exist_ok=True)
    done.mkdir(parents=True, exist_ok=True)
    plans.mkdir(parents=True, exist_ok=True)
    pending_approval.mkdir(parents=True, exist_ok=True)

    log_action('orchestrator_start', 'Orchestrator initialized', error=None)

    processed_files = set()

    linkedin_keywords = ['sales', 'business', 'project', 'lead', 'service', 'opportunity',
                         'hiring', 'developers', 'news', 'launch', 'milestone', 'achievement',
                         'growth', 'client', 'partner', 'announcement', 'exciting', 'thrilled',
                         'welcome', 'joining', 'team', 'product', 'release', 'update']

    mcp_base_url = 'http://localhost:3000'

    while True:
        try:
            # Check for .md files in Needs_Action
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

                        logger.info(f"Creating plan for {file_path.name}...")
                        plan_file = create_plan(file_path, content, metadata, plans, vault)
                        log_action('create_plan', f'Created: {plan_file.name}')

                        if any(kw in content.lower() for kw in linkedin_keywords):
                            logger.info("Business keyword found, generating LinkedIn draft...")
                            generate_linkedin_draft(needs_action, pending_approval, dashboard, logger)
                            log_action('generate_linkedin', 'Draft created')

                        requires_approval = check_requires_approval(content, metadata, file_type)

                        if requires_approval:
                            logger.info(f"Action requires approval, moving to Pending_Approval...")
                            approval_file = create_approval_request(file_path, plan_file, content,
                                                                   metadata, pending_approval, vault,
                                                                   mcp_base_url)
                            log_action('requires_approval', f'Moved to pending: {file_path.name}')

                            dest = pending_approval / file_path.name
                            shutil.move(str(file_path), str(dest))
                            logger.info(f"Moved {file_path.name} to Pending_Approval")

                            processed_files.add(file_path.name)
                            continue

                        logger.info(f"Executing action for {file_path.name}...")
                        success = execute_action(file_path, content, metadata, mcp_base_url, logger)

                        if success:
                            log_action('execute_action', f'Completed: {file_path.name}')
                        else:
                            log_action('execute_action', f'Failed: {file_path.name}', error='Action execution failed')

                        move_to_done(file_path, done, logger)
                        processed_files.add(file_path.name)

                        logger.info(f"Successfully processed {file_path.name}")
                        log_action('file_processed', f'Completed: {file_path.name}')

                    except Exception as e:
                        logger.error(f"Error processing {file_path.name}: {e}")
                        log_action('process_file', f'Error: {file_path.name}', error=str(e))

                update_dashboard(md_files, dashboard, logger)
                log_action('update_dashboard', f'Updated with {len(md_files)} files')

            else:
                logger.info("No files in Needs_Action to process.")

            # Process bank CSV files
            csv_result = process_bank_csv(vault, dashboard, logger)
            if csv_result['invoices_created'] > 0:
                logger.info(f"Bank CSV: Created {csv_result['invoices_created']} invoice(s)")

            check_linkedin_approvals(pending_approval, done, dashboard, logger)
            check_pending_approvals(pending_approval, done, mcp_base_url, logger)

        except Exception as e:
            logger.error(f"Error in orchestrator: {e}")
            log_action('orchestrator_error', 'Main loop error', error=str(e))

        if not loop:
            break

        time.sleep(interval)


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
- [ ] Step 3: Execute or route for approval
- [ ] Step 4: Verify completion
- [ ] Step 5: Archive to Done

## Notes
Generated by orchestrator reasoning loop.

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

    if not email_data['to']:
        full_pattern = re.search(
            r'[sS]end\s+(?:an?\s+)?email\s+to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+with\s+subject\s+[\'"]([^\'"]+)[\'"]\s+and\s+body\s+[\'"]([^\'"]+)[\'"]',
            content
        )
        if full_pattern:
            email_data['to'] = full_pattern.group(1)
            email_data['subject'] = full_pattern.group(2)
            email_data['body'] = full_pattern.group(3)

    if not email_data['to']:
        colon_pattern = re.search(r'[eE]mail\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*:\s*(.+)', content)
        if colon_pattern:
            email_data['to'] = colon_pattern.group(1)
            rest = colon_pattern.group(2)
            if ' - ' in rest:
                parts = rest.split(' - ', 1)
                email_data['subject'] = parts[0].strip()
                email_data['body'] = parts[1].strip()
            else:
                email_data['subject'] = rest.strip()
                email_data['body'] = rest.strip()

    if email_data['to']:
        return email_data

    return None


def check_requires_approval(content: str, metadata: dict, file_type: str) -> bool:
    """Check if action requires human approval."""
    if file_type in ['email', 'whatsapp']:
        return True

    if file_type == 'file_drop':
        email_data = parse_email_request(content)
        if email_data and email_data.get('to'):
            return True

    if 'linkedin' in content.lower() or 'post' in content.lower():
        return True

    financial_keywords = ['$500', '$750', '$1000', 'payment', 'invoice', 'transfer', 'USD', 'dollar', 'offer']
    if any(kw in content.lower() for kw in financial_keywords):
        return True

    business_keywords = ['sales', 'client', 'project', 'business', 'deal', 'customer', 'order', 'revenue', 'lead', 'service', 'opportunity']
    if any(kw in content.lower() for kw in business_keywords):
        return True

    sensitive_keywords = ['confidential', 'legal', 'contract', 'HR', 'salary']
    if any(kw in content.lower() for kw in sensitive_keywords):
        return True

    if metadata.get('priority') == 'high' and file_type in ['email', 'whatsapp']:
        return True

    return False


def create_approval_request(file_path: Path, plan_file: Path, content: str,
                           metadata: dict, pending_dir: Path, vault: Path,
                           mcp_base_url: str = 'http://localhost:3000') -> Path:
    """Create approval request file."""
    task_id = file_path.stem
    approval_file = pending_dir / f"{task_id}_Approval.md"

    action_type = metadata.get('type', 'unknown')

    email_data = parse_email_request(content)
    if email_data and email_data.get('to'):
        action_type = 'email_request'

    mcp_endpoint = '/send_email' if action_type == 'email_request' else '/social_post'

    to_line = f"**To:** {email_data['to']}" if email_data and email_data.get('to') else ""
    subject_line = f"**Subject:** {email_data['subject']}" if email_data and email_data.get('subject') else ""
    body_line = f"**Body:**\n{email_data['body']}" if email_data and email_data.get('body') else ""

    approval_content = f"""---
type: approval_request
original_file: {plan_file.name}
status: pending_approval
created: {datetime.now().isoformat()}
action_type: {action_type}
requires_mcp: true
mcp_endpoint: {mcp_base_url}{mcp_endpoint}
---

# Approval Request: {metadata.get('subject', task_id)}

## Original Task
{content[:500]}...

## Action Details

**Type:** {action_type}
**Priority:** {metadata.get('priority', 'normal')}
**Source:** {file_path.name}
{to_line}
{subject_line}
{body_line}

## Why Approval Required
- External communication or sensitive action
- Requires human review before execution

---

## Approval Instructions

**To Approve:**
1. Review the action details above
2. Change `status: pending_approval` to `status: approved`
3. Add `approved_at: {datetime.now().isoformat()}`
4. Save the file

**To Reject:**
1. Change `status: pending_approval` to `status: rejected`
2. Add `rejection_reason: {{your reason}}`
3. Save the file

The orchestrator polls this folder every 60 seconds.
"""

    approval_file.write_text(approval_content, encoding='utf-8')
    return approval_file


def execute_action(file_path: Path, content: str, metadata: dict,
                   mcp_base_url: str, logger) -> bool:
    """Execute action directly or via MCP with retry logic."""
    action_type = metadata.get('type', 'unknown')

    try:
        if action_type == 'email':
            result = retry_request(
                'post',
                f"{mcp_base_url}/send_email",
                json={
                    'to': metadata.get('to', 'unknown@example.com'),
                    'subject': metadata.get('subject', 'No subject'),
                    'body': content
                }
            )
            logger.info(f"MCP email response: {result.get('status_code')}")
            return result.get('success', False)

        elif action_type == 'file_drop':
            email_data = parse_email_request(content)
            if email_data and email_data.get('to'):
                logger.info(f"Email request detected in file drop: {email_data['to']}")
                result = retry_request(
                    'post',
                    f"{mcp_base_url}/send_email",
                    json={
                        'to': email_data['to'],
                        'subject': email_data.get('subject', 'No subject'),
                        'body': email_data.get('body', content)
                    }
                )
                logger.info(f"MCP email response: {result.get('status_code')}")
                return result.get('success', False)
            else:
                logger.info(f"File drop processed: {metadata.get('original_name', 'unknown')}")
                return True

        elif action_type == 'whatsapp':
            logger.info(f"WhatsApp message processed: {metadata.get('from', 'unknown')}")
            log_action('whatsapp_processed', metadata.get('from', 'unknown'))
            return True

        return True

    except Exception as e:
        logger.error(f"Error executing action: {e}")
        log_action('execute_action_error', str(e), error=str(e))
        return False


def move_to_done(file_path: Path, done_dir: Path, logger) -> None:
    """Move processed file to Done folder."""
    try:
        base_name = file_path.stem
        related_files = [file_path]

        potential_file = file_path.parent / base_name
        if potential_file.exists() and not potential_file.name.endswith('_Approval.md'):
            related_files.append(potential_file)

        for f in related_files:
            dest = done_dir / f.name
            shutil.move(str(f), str(dest))
            logger.info(f"Moved {f.name} to Done")
            log_action('move_to_done', f'Moved: {f.name}')

    except Exception as e:
        logger.error(f"Error moving file to Done: {e}")
        log_action('move_to_done_error', str(e), error=str(e))


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


def check_pending_approvals(pending_dir: Path, done_dir: Path,
                           mcp_base_url: str, logger) -> None:
    """Check for approved/rejected items in Pending_Approval."""
    if not pending_dir.exists():
        return

    for approval_file in pending_dir.glob('*_Approval.md'):
        content = approval_file.read_text(encoding='utf-8')
        metadata = parse_frontmatter(content)
        status = metadata.get('status', '')

        is_approved = status == 'approved'
        is_rejected = status == 'rejected'

        if is_approved:
            logger.info(f"Processing approved action: {approval_file.name}")
            log_action('approval_received', f'Approved: {approval_file.name}')

            mcp_endpoint = metadata.get('mcp_endpoint', '')
            action_type = metadata.get('action_type', 'unknown')

            if mcp_endpoint:
                try:
                    if action_type == 'email_request':
                        to_match = re.search(r'\*\*To:\*\* (.+)', content)
                        subject_match = re.search(r'\*\*Subject:\*\* (.+)', content)
                        body_match = re.search(r'\*\*Body:\*\*\n(.+?)(?=\n\n|\n##|\n---|$)', content, re.DOTALL)

                        if to_match:
                            email_data = {
                                'to': to_match.group(1).strip(),
                                'subject': subject_match.group(1).strip() if subject_match else 'No subject',
                                'body': body_match.group(1).strip() if body_match else ''
                            }
                            logger.info(f"Sending approved email to {email_data['to']}")

                            result = retry_request('post', mcp_endpoint, json=email_data)
                            logger.info(f"MCP email response: {result.get('status_code')} - {result.get('data', '')}")
                            log_action('send_approved_email', f'Sent to {email_data["to"]}',
                                      error=None if result.get('success') else result.get('error'))
                        else:
                            logger.error("Could not extract email details from approval file")
                            log_action('email_extract_error', 'Failed to extract email details', error='Parse failed')
                    else:
                        result = retry_request('post', mcp_endpoint)
                        logger.info(f"MCP execution response: {result.get('status_code')}")
                        log_action('mcp_execution', f'Endpoint: {mcp_endpoint}',
                                  error=None if result.get('success') else result.get('error'))
                except Exception as e:
                    logger.error(f"MCP call failed: {e}")
                    log_action('mcp_call_error', str(e), error=str(e))

            dest = done_dir / approval_file.name
            shutil.move(str(approval_file), str(dest))
            logger.info(f"Moved approved action to Done: {approval_file.name}")
            log_action('move_approved_to_done', f'Moved: {approval_file.name}')

            original_file_name = metadata.get('original_file', '').replace('_Plan.md', '.md')
            if original_file_name:
                original_file_path = pending_dir / original_file_name
                if original_file_path.exists():
                    original_dest = done_dir / original_file_name
                    shutil.move(str(original_file_path), str(original_dest))
                    logger.info(f"Moved original file to Done: {original_file_name}")

        elif is_rejected:
            logger.info(f"Processing rejected action: {approval_file.name}")
            log_action('approval_rejected', f'Rejected: {approval_file.name}')

            dest = done_dir / approval_file.name
            shutil.move(str(approval_file), str(dest))
            logger.info(f"Moved rejected action to Done: {approval_file.name}")

            original_file_name = metadata.get('original_file', '').replace('_Plan.md', '.md')
            if original_file_name:
                original_file_path = pending_dir / original_file_name
                if original_file_path.exists():
                    original_dest = done_dir / original_file_name
                    shutil.move(str(original_file_path), str(original_dest))
                    logger.info(f"Moved original file to Done: {original_file_name}")


def generate_linkedin_draft(needs_action: Path, pending_approval: Path, dashboard: Path, logger) -> Path:
    """Generate LinkedIn draft file in Pending_Approval folder."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    draft_file = pending_approval / f"LinkedIn_Draft_{timestamp}.md"

    recent_activity = ""
    if dashboard.exists():
        dashboard_content = dashboard.read_text(encoding='utf-8')
        lines = dashboard_content.split('\n')[:10]
        recent_activity = '\n'.join(lines)

    business_content = ""
    for f in needs_action.glob('*.md'):
        content = f.read_text(encoding='utf-8')
        if any(kw in content.lower() for kw in ['sales', 'business', 'project', 'lead', 'service', 'opportunity']):
            business_content = content[:300]
            break

    post_text = f"""Excited to share our latest AI automation project! We're helping businesses streamline workflows and save valuable time.

Our team just completed another successful implementation, delivering real results for our clients.

Want to learn how AI can transform your operations? DM me for more details!

#AI #Automation #BusinessGrowth"""

    draft_content = f"""---
type: linkedin_draft
status: pending
generated_at: {datetime.now().isoformat()}
---

## Post Text

{post_text}

## Approval Actions

- [ ] Approve and Post
- [ ] Reject (add your reason below this line)
- [ ] Edit (add your notes or changes below this line)
"""

    draft_file.write_text(draft_content, encoding='utf-8')
    logger.info(f"LinkedIn draft created: {draft_file.name}")
    log_action('linkedin_draft_created', f'Created: {draft_file.name}')
    return draft_file


def check_linkedin_approvals(pending_approval: Path, done: Path, dashboard: Path, logger) -> None:
    """Check LinkedIn drafts for approval and handle clipboard + browser."""
    if not pending_approval.exists():
        return

    for draft_file in pending_approval.glob('LinkedIn_Draft_*.md'):
        content = draft_file.read_text(encoding='utf-8')

        if '- [x] Approve and Post' in content or '- [X] Approve and Post' in content:
            logger.info("LinkedIn draft approved!")
            log_action('linkedin_approved', f'Approved: {draft_file.name}')

            post_text = ""
            if '## Post Text' in content:
                parts = content.split('## Post Text')
                if len(parts) > 1:
                    post_section = parts[1].split('## Approval Actions')[0].strip()
                    post_text = post_section

            if post_text:
                pyperclip.copy(post_text)
                logger.info("LinkedIn post text copied to clipboard.")
                log_action('linkedin_copy_clipboard', 'Text copied')

                webbrowser.open('https://www.linkedin.com/feed/?shareActive=true', new=2)
                logger.info("Browser opened to LinkedIn post composer.")
                log_action('linkedin_open_browser', 'Composer opened')

                print("\n" + "="*70)
                print(" " * 15 + "LINKEDIN POST READY!")
                print("="*70)
                print("Post text copied to clipboard.")
                print("LinkedIn post composer opened in your browser.")
                print("")
                print(">>> Press Ctrl+V to paste the text <<<")
                print(">>> Then click 'Post' button <<<")
                print("="*70 + "\n")

            if dashboard.exists():
                dash_content = dashboard.read_text(encoding='utf-8')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                update_entry = f"\n## Recent Updates\n{timestamp} - LinkedIn draft approved - ready for manual post. Text copied to clipboard.\n"
                if '## Recent Updates' not in dash_content:
                    dash_content += update_entry
                else:
                    dash_content = dash_content.replace('## Recent Updates', f'## Recent Updates\n{timestamp} - LinkedIn draft approved - ready for manual post. Text copied to clipboard.', 1)
                dashboard.write_text(dash_content, encoding='utf-8')

            with open(draft_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\nApproved - user to paste and click Post manually.\n")

            dest = done / draft_file.name
            shutil.move(str(draft_file), str(dest))
            logger.info(f"Moved approved LinkedIn draft to Done: {draft_file.name}")
            log_action('linkedin_moved_to_done', f'Moved: {draft_file.name}')


if __name__ == "__main__":
    log_action('orchestrator_launch', 'Starting orchestrator')
    run_orchestrator(interval=30)
