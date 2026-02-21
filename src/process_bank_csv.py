"""
Bank CSV Processor - Gold Tier
Processes bank statement CSV files and creates invoices for received payments.
"""

import csv
import json
import requests
import re
from pathlib import Path
from datetime import datetime

# Configuration
VAULT_PATH = Path('AI_Employee_Vault')
LOGS_PATH = Path('Logs')
MCP_URL = 'http://localhost:3004'

# Client name keywords for matching
CLIENT_KEYWORDS = [
    'payment', 'transfer', 'deposit', 'credit',
    'invoice', 'inv', 'payment received', 'received'
]

# Known client names (extend as needed)
KNOWN_CLIENTS = [
    'Test Customer', 'ABC Corp', 'XYZ Ltd', 'Client', 'Customer'
]


def get_latest_csv() -> Path | None:
    """Find latest CSV in Drop or Accounting folder."""
    search_paths = [
        VAULT_PATH / 'Drop',
        VAULT_PATH / 'Accounting'
    ]
    
    csv_files = []
    for search_path in search_paths:
        if search_path.exists():
            csv_files.extend(search_path.glob('*.csv'))
    
    if not csv_files:
        return None
    
    return max(csv_files, key=lambda f: f.stat().st_mtime)


def parse_bank_csv(csv_path: Path) -> list[dict]:
    """Parse bank CSV file."""
    transactions = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append({
                'date': row.get('date', ''),
                'description': row.get('description', ''),
                'amount': float(row.get('amount', 0)),
                'type': row.get('type', '')
            })
    
    return transactions


def extract_client_name(description: str) -> str | None:
    """Extract client name from transaction description."""
    desc_lower = description.lower()
    
    # Check for known clients
    for client in KNOWN_CLIENTS:
        if client.lower() in desc_lower:
            return client
    
    # Check for payment keywords
    for keyword in CLIENT_KEYWORDS:
        if keyword in desc_lower:
            # Try to extract a name (capitalize words)
            words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', description)
            if words:
                return ' '.join(words[:2])  # Return first 1-2 words as name
    
    return None


def create_invoice(partner_name: str, amount: float, description: str) -> dict | None:
    """Create invoice via Odoo MCP."""
    try:
        response = requests.post(
            f'{MCP_URL}/create_invoice',
            json={
                'partner_name': partner_name,
                'amount': amount,
                'description': description
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': response.text}
    
    except Exception as e:
        return {'error': str(e)}


def update_dashboard(summary: str) -> None:
    """Append summary to Dashboard.md."""
    dashboard = VAULT_PATH / 'Dashboard.md'
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n## {timestamp} - Bank CSV Processing\n{summary}\n"
    
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


def log_unmatched(transaction: dict, csv_path: Path) -> None:
    """Log unmatched transaction."""
    LOGS_PATH.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_PATH / 'csv_unmatched.log'
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'source_file': csv_path.name,
        'transaction': transaction
    }
    
    existing = []
    if log_file.exists():
        try:
            existing = json.loads(log_file.read_text())
        except:
            existing = []
    
    existing.append(entry)
    log_file.write_text(json.dumps(existing, indent=2))


def process_bank_csv() -> dict:
    """Main processing function."""
    result = {
        'success': False,
        'processed': 0,
        'invoices_created': 0,
        'unmatched': 0,
        'errors': []
    }
    
    # Find latest CSV
    csv_path = get_latest_csv()
    if not csv_path:
        result['errors'].append('No CSV files found in Drop or Accounting')
        return result
    
    print(f"Processing: {csv_path.name}")
    
    # Parse CSV
    transactions = parse_bank_csv(csv_path)
    print(f"Found {len(transactions)} transactions")
    
    # Process each transaction
    for txn in transactions:
        amount = txn.get('amount', 0)
        description = txn.get('description', '')
        
        # Check for positive amount (payment received)
        if amount <= 0:
            continue
        
        # Check for payment keywords
        desc_lower = description.lower()
        is_payment = any(kw in desc_lower for kw in CLIENT_KEYWORDS)
        
        if not is_payment:
            result['unmatched'] += 1
            log_unmatched(txn, csv_path)
            continue
        
        # Extract client name
        client_name = extract_client_name(description)
        
        if not client_name:
            result['unmatched'] += 1
            log_unmatched(txn, csv_path)
            continue
        
        # Create invoice
        print(f"Creating invoice for {client_name}: PKR {amount}")
        invoice_result = create_invoice(
            client_name,
            amount,
            f'Payment received - {description}'
        )
        
        if invoice_result and invoice_result.get('success'):
            result['invoices_created'] += 1
            
            # Update dashboard
            summary = f"""- **Invoice Created:** {invoice_result.get('invoice_id')}
- **Client:** {client_name}
- **Amount:** PKR {amount:,.2f}
- **Source:** {csv_path.name}"""
            
            update_dashboard(summary)
            result['processed'] += 1
        else:
            result['errors'].append(f"Failed for {client_name}: {invoice_result}")
    
    result['success'] = result['invoices_created'] > 0
    return result


if __name__ == '__main__':
    result = process_bank_csv()
    print(f"\nResult: {json.dumps(result, indent=2)}")
