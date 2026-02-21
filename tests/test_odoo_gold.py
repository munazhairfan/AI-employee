"""
Gold Tier Odoo Flow Test
Verifies bank CSV -> Orchestrator -> Odoo Invoice flow.

Steps:
1. Create dummy CSV in AI_Employee_Vault/Accounting/
2. Wait for orchestrator to process
3. Verify invoice created via Odoo MCP
4. Check Dashboard.md updated

Run: python test_odoo_gold.py
"""

import time
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Configuration
VAULT_PATH = Path('AI_Employee_Vault')
ACCOUNTING_PATH = VAULT_PATH / 'Accounting'
DASHBOARD_PATH = VAULT_PATH / 'Dashboard.md'
ODOO_MCP_URL = os.getenv('ODOO_MCP_URL', 'http://localhost:3004')

# Test data
TEST_CSV_CONTENT = """date,description,amount,type
2026-02-20,Client Payment from Test Customer,50000,incoming
2026-02-19,Office Supplies,-2500,outgoing
2026-02-18,Payment received ABC Corp,35000,incoming
"""

TEST_CSV_FILENAME = f"test_payment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


def create_test_csv() -> Path:
    """Create test CSV file in Accounting folder."""
    print("[1/4] Creating test CSV file...")
    
    ACCOUNTING_PATH.mkdir(parents=True, exist_ok=True)
    csv_path = ACCOUNTING_PATH / TEST_CSV_FILENAME
    csv_path.write_text(TEST_CSV_CONTENT, encoding='utf-8')
    
    print(f"      Created: {csv_path}")
    print(f"      Content:\n{TEST_CSV_CONTENT}")
    
    return csv_path


def wait_for_orchestrator(wait_seconds: int = 60) -> None:
    """Wait for orchestrator to process the CSV."""
    print(f"\n[2/4] Waiting {wait_seconds}s for orchestrator to process...")
    print("      (Orchestrator polls every 30-60 seconds)")
    
    for i in range(wait_seconds, 0, -1):
        print(f"      {i}s remaining...", end='\r')
        time.sleep(1)
    
    print(f"\n      Wait complete.")


def check_odoo_invoices() -> dict:
    """Check Odoo for newly created invoices via MCP."""
    print("\n[3/4] Checking Odoo for invoices...")
    
    try:
        response = requests.post(
            f'{ODOO_MCP_URL}/read_invoices',
            json={'state': 'all', 'limit': 10},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                invoices = data.get('invoices', [])
                print(f"      Found {len(invoices)} invoice(s) in Odoo")
                
                # Look for our test invoices (by amount or partner)
                test_invoices = [
                    inv for inv in invoices 
                    if inv.get('amount_total') in [50000.0, 35000.0]
                ]
                
                if test_invoices:
                    print(f"      ✓ Found {len(test_invoices)} test invoice(s):")
                    for inv in test_invoices:
                        print(f"        - ID: {inv.get('id')}, "
                              f"Partner: {inv.get('partner_name')}, "
                              f"Amount: PKR {inv.get('amount_total'):,.2f}, "
                              f"State: {inv.get('state')}")
                    return {
                        'success': True,
                        'invoices': test_invoices,
                        'all_invoices': invoices
                    }
                else:
                    print("      ✗ No test invoices found (expected 50000 or 35000)")
                    print("      All invoices:")
                    for inv in invoices[:5]:
                        print(f"        - {inv.get('name')}: {inv.get('partner_name')} - PKR {inv.get('amount_total')}")
                    return {
                        'success': False,
                        'invoices': [],
                        'all_invoices': invoices
                    }
            else:
                print(f"      ✗ MCP error: {data.get('error')}")
                return {'success': False, 'error': data.get('error')}
        else:
            print(f"      ✗ HTTP error: {response.status_code}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    
    except requests.exceptions.ConnectionError as e:
        print(f"      ✗ Connection error: {e}")
        print("      Make sure Odoo MCP server is running: node odoo_mcp.js")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f"      ✗ Error: {e}")
        return {'success': False, 'error': str(e)}


def check_dashboard_updated() -> bool:
    """Check if Dashboard.md was updated with Odoo invoice info."""
    print("\n[4/4] Checking Dashboard.md for updates...")
    
    if not DASHBOARD_PATH.exists():
        print("      ✗ Dashboard.md not found")
        return False
    
    content = DASHBOARD_PATH.read_text(encoding='utf-8')
    
    # Check for Odoo-related entries
    odoo_keywords = ['Odoo', 'Invoice', 'invoice_id', 'PKR', 'Client']
    found_keywords = [kw for kw in odoo_keywords if kw in content]
    
    if found_keywords:
        print(f"      ✓ Dashboard contains Odoo-related content: {found_keywords}")
        
        # Show recent entries
        lines = content.split('\n')
        recent_lines = []
        for i, line in enumerate(lines[-20:], 1):  # Last 20 lines
            if any(kw in line for kw in ['Invoice', 'PKR', 'Client', 'Odoo']):
                recent_lines.append(line)
        
        if recent_lines:
            print("      Recent Odoo entries:")
            for line in recent_lines[-5:]:
                print(f"        {line}")
        
        return True
    else:
        print("      ✗ No Odoo-related content found in Dashboard")
        return False


def check_pending_approval() -> bool:
    """Check if any files in Pending_Approval folder."""
    print("\n[Extra] Checking Pending_Approval folder...")
    
    pending_path = VAULT_PATH / 'Pending_Approval'
    if not pending_path.exists():
        print("      - Pending_Approval folder not found")
        return False
    
    md_files = list(pending_path.glob('*.md'))
    if md_files:
        print(f"      ✓ Found {len(md_files)} file(s) in Pending_Approval:")
        for f in md_files:
            print(f"        - {f.name}")
        return True
    else:
        print("      - No files in Pending_Approval")
        return False


def cleanup_test_csv(csv_path: Path) -> None:
    """Move test CSV to Done folder."""
    done_path = VAULT_PATH / 'Done'
    done_path.mkdir(parents=True, exist_ok=True)
    
    if csv_path.exists():
        dest = done_path / csv_path.name
        csv_path.rename(dest)
        print(f"\n      Cleaned up: Moved {csv_path.name} to Done/")


def run_test() -> bool:
    """Run complete test flow."""
    print("=" * 70)
    print(" " * 20 + "GOLD TIER ODOO FLOW TEST")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Vault: {VAULT_PATH.absolute()}")
    print(f"  Odoo MCP: {ODOO_MCP_URL}")
    print(f"  Test CSV: {TEST_CSV_FILENAME}")
    print("=" * 70)
    
    # Step 1: Create test CSV
    csv_path = create_test_csv()
    
    # Step 2: Wait for orchestrator
    wait_for_orchestrator(wait_seconds=60)
    
    # Step 3: Check Odoo invoices
    odoo_result = check_odoo_invoices()
    
    # Step 4: Check Dashboard
    dashboard_updated = check_dashboard_updated()
    
    # Extra: Check Pending_Approval
    check_pending_approval()
    
    # Summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)
    
    success = odoo_result.get('success', False) and dashboard_updated
    
    if success:
        print("\n✓ TEST PASSED")
        print("  - Invoice(s) created in Odoo")
        print("  - Dashboard.md updated")
    else:
        print("\n✗ TEST FAILED")
        if not odoo_result.get('success'):
            print(f"  - Invoice creation failed: {odoo_result.get('error', 'Unknown')}")
        if not dashboard_updated:
            print("  - Dashboard not updated")
    
    print("\n" + "=" * 70)
    
    # Cleanup
    cleanup_test_csv(csv_path)
    
    return success


if __name__ == '__main__':
    success = run_test()
    exit(0 if success else 1)
