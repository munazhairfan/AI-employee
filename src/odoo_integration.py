"""
Odoo Integration - Actually Create Invoices
Connects dashboard approvals to real Odoo invoice creation
"""

import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Odoo Configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost')
ODOO_PORT = os.getenv('ODOO_PORT', '8069')
ODOO_DB = os.getenv('ODOO_DB', 'ai_employee_db')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASS = os.getenv('ODOO_PASS', 'admin')

# Fix URL construction (remove port from URL if present)
ODOO_URL_CLEAN = ODOO_URL.replace(':8069', '').replace(':3004', '')
ODOO_BASE_URL = f"{ODOO_URL_CLEAN}:{ODOO_PORT}"


def create_odoo_invoice(customer_name, amount, description='', invoice_number=None):
    """
    Create invoice in Odoo via JSON-RPC API
    
    Args:
        customer_name: Customer name (will find or create partner)
        amount: Invoice amount (number)
        description: Invoice description
        invoice_number: Optional (Odoo will auto-generate if not provided)
    
    Returns:
        dict with success status and invoice details
    """
    try:
        # Step 1: Authenticate
        session = requests.Session()
        
        # Get session ID
        auth_url = f"{ODOO_BASE_URL}/web/session/authenticate"
        auth_data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": ODOO_DB,
                "login": ODOO_USER,
                "password": ODOO_PASS
            },
            "id": 1
        }
        
        response = session.post(auth_url, json=auth_data)
        result = response.json()
        
        if result.get('error'):
            return {
                'success': False,
                'error': f"Authentication failed: {result['error']['message']}",
                'invoice_id': None
            }
        
        uid = result['result']['uid']
        
        if uid == 0:
            return {
                'success': False,
                'error': 'Odoo authentication failed - check credentials',
                'invoice_id': None
            }
        
        # Step 2: Find or create customer (partner)
        partner_id = find_or_create_partner(session, customer_name)
        
        if not partner_id:
            return {
                'success': False,
                'error': f'Could not find or create customer: {customer_name}',
                'invoice_id': None
            }
        
        # Step 3: Create invoice using web API
        invoice_url = f"{ODOO_BASE_URL}/web/dataset/call_kw"
        
        # For Odoo 19, use proper format
        invoice_values = {
            "move_type": "out_invoice",
            "partner_id": int(partner_id),  # Ensure it's an integer, not array
            "invoice_line_ids": [
                [0, 0, {
                    "name": description or "Invoice item",
                    "quantity": 1,
                    "price_unit": float(amount)
                }]
            ]
        }
        
        create_data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "account.move",
                "method": "create",
                "args": [invoice_values],
                "kwargs": {}
            },
            "id": 2
        }
        
        response = session.post(invoice_url, json=create_data)
        result = response.json()
        
        if result.get('error'):
            error_msg = result['error'].get('message', 'Unknown Odoo error')
            error_data = result['error'].get('data', {})
            print(f"[DEBUG] Odoo Error: {error_msg}")
            print(f"[DEBUG] Odoo Error Data: {error_data}")
            return {
                'success': False,
                'error': f"Invoice creation failed: {error_msg}",
                'invoice_id': None,
                'debug_data': error_data
            }
        
        invoice_id = result['result']
        
        # Step 4: Get invoice number (Odoo auto-generates)
        invoice_data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "account.move",
                "method": "search_read",
                "domain": [["id", "=", invoice_id]]
            },
            "id": 3
        }
        
        response = session.post(invoice_url, json=invoice_data)
        result = response.json()
        
        invoice_number = result['result'][0]['name'] if result.get('result') else 'N/A'
        
        return {
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'partner_id': partner_id,
            'partner_name': customer_name,
            'amount': amount,
            'message': f'Invoice {invoice_number} created successfully'
        }
        
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': f'Cannot connect to Odoo at {ODOO_BASE_URL}. Is Odoo running?',
            'invoice_id': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error creating invoice: {str(e)}',
            'invoice_id': None
        }


def find_or_create_partner(session, customer_name):
    """Find existing customer or create new one"""
    
    invoice_url = f"{ODOO_BASE_URL}/web/dataset/call_kw"
    
    # Try to find existing partner
    search_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "res.partner",
            "method": "search_read",
            "domain": [["name", "=ilike", customer_name]],
            "fields": ["id", "name"]
        },
        "id": 4
    }
    
    response = session.post(invoice_url, json=search_data)
    result = response.json()
    
    if result.get('result') and len(result['result']) > 0:
        # Found existing partner - extract ID from first result
        partner = result['result'][0]
        return partner.get('id')
    
    # Create new partner
    create_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "model": "res.partner",
            "method": "create",
            "args": [[{
                "name": customer_name,
                "company_type": "company"
            }]],
            "kwargs": {}
        },
        "id": 5
    }
    
    response = session.post(invoice_url, json=create_data)
    result = response.json()
    
    # Return just the ID (not a list)
    partner_id = result.get('result')
    if isinstance(partner_id, list):
        return partner_id[0] if partner_id else None
    return partner_id


def execute_approved_task(task_type, content, task_file):
    """
    Execute action based on approved task type
    
    Args:
        task_type: Type of task (odoo_invoice, email_send, etc.)
        content: Full task content
        task_file: Task filename
    
    Returns:
        dict with execution result
    """
    
    if task_type == 'odoo_invoice' or task_type == 'email_invoice':
        # Extract details from task content
        customer_name = extract_field(content, 'customer_name')
        amount = extract_field(content, 'amount')
        description = extract_field(content, 'product_service') or 'Invoice item'
        invoice_number = extract_field(content, 'invoice_number')
        
        if not customer_name or not amount:
            return {
                'success': False,
                'error': 'Missing required fields: customer_name or amount'
            }
        
        # Create invoice in Odoo
        result = create_odoo_invoice(customer_name, amount, description, invoice_number)
        
        if result['success']:
            return {
                'success': True,
                'message': f"Invoice {result['invoice_number']} created in Odoo for {customer_name}",
                'details': result
            }
        else:
            return result
    
    elif task_type == 'email_send':
        # TODO: Implement Gmail API integration
        return {
            'success': True,
            'message': 'Email sending requires Gmail API setup (see docs/EMAIL_INTEGRATION.md)',
            'details': {'status': 'pending_integration'}
        }
    
    elif task_type == 'whatsapp_reply':
        # TODO: Implement WhatsApp API integration
        return {
            'success': True,
            'message': 'WhatsApp sending requires WhatsApp API setup (see docs/WHATSAPP_INTEGRATION.md)',
            'details': {'status': 'pending_integration'}
        }
    
    else:
        return {
            'success': True,
            'message': f'Task marked as completed (type: {task_type})',
            'details': {'status': 'completed'}
        }


def extract_field(content, field_name):
    """Extract field value from task markdown content"""
    import re
    
    # Look for field in markdown table
    pattern = rf'\|\s*{field_name}\s*\|\s*([^\|]+)\s*\|'
    match = re.search(pattern, content)
    
    if match:
        value = match.group(1).strip()
        # Clean up common values
        if value.lower() in ['unknown', 'not mentioned', 'null', 'none']:
            return None
        return value
    
    return None


# Test function
if __name__ == "__main__":
    print("Testing Odoo Integration...")
    print("=" * 60)
    
    result = create_odoo_invoice(
        customer_name="Test Customer",
        amount=1000,
        description="Test invoice from dashboard"
    )
    
    if result['success']:
        print(f"[OK] SUCCESS: Invoice {result['invoice_number']} created!")
        print(f"   Invoice ID: {result['invoice_id']}")
        print(f"   Customer: {result['partner_name']}")
        print(f"   Amount: {result['amount']}")
    else:
        print(f"[ERROR] FAILED: {result['error']}")
        print("\nTroubleshooting:")
        print("1. Check if Odoo is running: docker ps")
        print("2. Check Odoo URL: http://localhost:8069")
        print("3. Check credentials in .env file")
