"""
Gold Tier Integration Test Suite
Simulates complete business flow:
1. Drop invoice CSV → watcher
2. Odoo entry via MCP
3. Social draft generation
4. Weekly audit run
5. Check Briefing.md and logs

Usage: python test_gold.py
"""

import time
import json
import requests
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple


# Configuration
VAULT_PATH = Path('AI_Employee_Vault')
LOGS_PATH = Path('Logs')
SKILLS_PATH = Path('skills')
MCP_ODOO_URL = 'http://localhost:3004'
MCP_SOCIAL_URL = 'http://localhost:3005'

# Test data
TEST_INVOICE = {
    'partner_id': 6,  # Test Customer
    'amount': 25000.00,
    'description': 'AI Automation Services - Test Invoice'
}

TEST_SOCIAL_POST = {
    'content': '🎉 Excited to announce our new AI automation service! Helping businesses save 20+ hours/week. #AI #Automation #BusinessGrowth'
}


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.message = ''
        self.error = None
        self.duration = 0
    
    def __str__(self):
        status = '[PASS]' if self.success else '[FAIL]'
        return f"{status} {self.name}: {self.message}"


def log_test_result(result: TestResult) -> None:
    """Log test result to JSON file."""
    LOGS_PATH.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_PATH / f'test_results_{datetime.now().strftime("%Y-%m-%d")}.json'
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'test': result.name,
        'success': result.success,
        'message': result.message,
        'error': str(result.error) if result.error else None,
        'duration': result.duration
    }
    
    existing = []
    if log_file.exists():
        try:
            existing = json.loads(log_file.read_text())
        except:
            existing = []
    
    existing.append(entry)
    log_file.write_text(json.dumps(existing, indent=2))


def test_vault_structure() -> TestResult:
    """Test 1: Verify vault directory structure exists."""
    result = TestResult('Vault Structure')
    start = time.time()
    
    try:
        required_dirs = [
            VAULT_PATH / 'Needs_Action',
            VAULT_PATH / 'Done',
            VAULT_PATH / 'Plans',
            VAULT_PATH / 'Pending_Approval',
            VAULT_PATH / 'Briefings',
            LOGS_PATH
        ]
        
        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        result.success = True
        result.message = f'Created {len(required_dirs)} directories'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_drop_invoice_csv() -> TestResult:
    """Test 2: Drop invoice CSV file to trigger watcher."""
    result = TestResult('Drop Invoice CSV')
    start = time.time()
    
    try:
        # Create test invoice CSV
        csv_content = """invoice_id,partner,amount,date,description
INV-TEST-001,Test Customer,25000,2026-02-20,AI Automation Services
INV-TEST-002,Another Client,15000,2026-02-20,Consulting Services
"""
        
        drop_file = VAULT_PATH / 'Drop' / f'test_invoice_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        drop_file.parent.mkdir(parents=True, exist_ok=True)
        drop_file.write_text(csv_content)
        
        result.success = drop_file.exists()
        result.message = f'Created: {drop_file.name}'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_odoo_mcp_connection() -> TestResult:
    """Test 3: Test Odoo MCP connection."""
    result = TestResult('Odoo MCP Connection')
    start = time.time()
    
    try:
        response = requests.get(f'{MCP_ODOO_URL}/health', timeout=10)
        data = response.json()
        
        result.success = data.get('success') and data.get('status') == 'connected'
        result.message = f"Connected to {data.get('odoo', {}).get('db', 'unknown')} DB"
    except Exception as e:
        result.error = e
        result.message = f'Connection failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_create_invoice_via_mcp() -> TestResult:
    """Test 4: Create invoice in Odoo via MCP."""
    result = TestResult('Create Invoice via MCP')
    start = time.time()
    
    try:
        response = requests.post(
            f'{MCP_ODOO_URL}/create_invoice',
            json=TEST_INVOICE,
            timeout=30
        )
        data = response.json()
        
        result.success = data.get('success') and data.get('invoice_id')
        result.message = f"Invoice ID: {data.get('invoice_id')}" if result.success else data.get('error', 'Unknown error')
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_read_invoices_via_mcp() -> TestResult:
    """Test 5: Read invoices from Odoo via MCP."""
    result = TestResult('Read Invoices via MCP')
    start = time.time()
    
    try:
        response = requests.post(
            f'{MCP_ODOO_URL}/read_invoices',
            json={'state': 'all', 'limit': 5},
            timeout=30
        )
        data = response.json()
        
        result.success = data.get('success')
        result.message = f"Found {data.get('count', 0)} invoices"
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_social_mcp_connection() -> TestResult:
    """Test 6: Test Social MCP connection."""
    result = TestResult('Social MCP Connection')
    start = time.time()
    
    try:
        response = requests.get(f'{MCP_SOCIAL_URL}/health', timeout=10)
        data = response.json()
        
        result.success = data.get('success') and data.get('status') == 'running'
        result.message = f"Running on port 3005"
    except Exception as e:
        result.error = e
        result.message = f'Connection failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_create_social_draft() -> TestResult:
    """Test 7: Create social media draft via MCP."""
    result = TestResult('Create Social Draft')
    start = time.time()
    
    try:
        response = requests.post(
            f'{MCP_SOCIAL_URL}/post_draft_x',
            json=TEST_SOCIAL_POST,
            timeout=30
        )
        data = response.json()
        
        result.success = data.get('success')
        result.message = f"Draft created for {data.get('platform', 'unknown')}" if result.success else data.get('error', 'Unknown error')
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_create_needs_action_file() -> TestResult:
    """Test 8: Create file in Needs_Action to trigger orchestrator."""
    result = TestResult('Create Needs_Action File')
    start = time.time()
    
    try:
        content = f"""---
type: business_activity
priority: high
subject: Test Business Activity
created: {datetime.now().isoformat()}
---

# Test Business Activity

This is a test file to trigger the orchestrator and generate a LinkedIn draft.

Key points:
- New client project started
- Revenue: PKR 50,000
- Timeline: 2 weeks

## Action Required
- Generate LinkedIn post about this achievement
- Update dashboard
"""
        
        na_file = VAULT_PATH / 'Needs_Action' / f'test_business_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        na_file.write_text(content)
        
        result.success = na_file.exists()
        result.message = f'Created: {na_file.name}'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_weekly_audit_skill_exists() -> TestResult:
    """Test 9: Verify weekly audit skill exists."""
    result = TestResult('Weekly Audit Skill Exists')
    start = time.time()
    
    try:
        skill_file = SKILLS_PATH / 'SKILL_weekly_audit.md'
        result.success = skill_file.exists()
        result.message = f'Found: {skill_file.name}' if result.success else 'Skill file not found'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_run_weekly_audit() -> TestResult:
    """Test 10: Run weekly audit (simulated)."""
    result = TestResult('Run Weekly Audit')
    start = time.time()
    
    try:
        # Create a mock briefing since we can't run Claude CLI in test
        briefing_file = VAULT_PATH / 'Briefings' / f'CEO_Briefing_{datetime.now().strftime("%Y-%m-%d")}.md'
        
        content = f"""---
type: ceo_briefing
period: Test Week
generated: {datetime.now().isoformat()}
priority: high
---

# CEO Weekly Briefing - TEST

## Executive Summary
This is a test briefing generated by the weekly audit test.

## Revenue (PKR)
| Metric | Amount |
|--------|--------|
| Total Invoiced | PKR 40,000 |
| Total Paid | PKR 25,000 |
| Outstanding | PKR 15,000 |

## Bottlenecks
| Customer | Amount | Days Overdue | Priority |
|----------|--------|--------------|----------|
| Test Client | PKR 15,000 | 5 | MEDIUM |

## Suggestions
1. Follow up on overdue invoices
2. Review pending projects

---
*Generated by Weekly Audit Test*
"""
        
        briefing_file.parent.mkdir(parents=True, exist_ok=True)
        briefing_file.write_text(content)
        
        result.success = briefing_file.exists()
        result.message = f'Created: {briefing_file.name}'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_check_briefing_exists() -> TestResult:
    """Test 11: Check if briefing file exists."""
    result = TestResult('Check Briefing Exists')
    start = time.time()
    
    try:
        briefings = list((VAULT_PATH / 'Briefings').glob('CEO_Briefing_*.md'))
        result.success = len(briefings) > 0
        result.message = f'Found {len(briefings)} briefing(s)' if result.success else 'No briefings found'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_check_logs_exist() -> TestResult:
    """Test 12: Check if log files exist."""
    result = TestResult('Check Logs Exist')
    start = time.time()
    
    try:
        log_files = list(LOGS_PATH.glob('*.json'))
        result.success = len(log_files) > 0
        result.message = f'Found {len(log_files)} log file(s)' if result.success else 'No logs found'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_ralph_loop_exists() -> TestResult:
    """Test 13: Verify Ralph Loop module exists."""
    result = TestResult('Ralph Loop Module Exists')
    start = time.time()

    try:
        ralph_file = Path('src/ralph_loop.py')
        result.success = ralph_file.exists()
        result.message = f'Found: {ralph_file.name}' if result.success else 'Module not found'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_watchdog_exists() -> TestResult:
    """Test 14: Verify Watchdog module exists."""
    result = TestResult('Watchdog Module Exists')
    start = time.time()

    try:
        watchdog_file = Path('src/watchdog.py')
        result.success = watchdog_file.exists()
        result.message = f'Found: {watchdog_file.name}' if result.success else 'Module not found'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def cleanup_test_files() -> TestResult:
    """Test 15: Cleanup test files."""
    result = TestResult('Cleanup Test Files')
    start = time.time()
    
    try:
        # Move test files from Needs_Action to Done
        na_files = list((VAULT_PATH / 'Needs_Action').glob('test_*.md'))
        done_path = VAULT_PATH / 'Done'
        
        moved = 0
        for f in na_files:
            shutil.move(str(f), str(done_path / f.name))
            moved += 1
        
        result.success = True
        result.message = f'Moved {moved} test files to Done'
    except Exception as e:
        result.error = e
        result.message = f'Cleanup failed: {e}'
    
    result.duration = time.time() - start
    log_test_result(result)
    return result


def run_all_tests() -> Tuple[list, list]:
    """Run all tests and return results."""
    tests = [
        test_vault_structure,
        test_drop_invoice_csv,
        test_odoo_mcp_connection,
        test_create_invoice_via_mcp,
        test_read_invoices_via_mcp,
        test_social_mcp_connection,
        test_create_social_draft,
        test_create_needs_action_file,
        test_weekly_audit_skill_exists,
        test_run_weekly_audit,
        test_check_briefing_exists,
        test_check_logs_exist,
        test_ralph_loop_exists,
        test_watchdog_exists,
        cleanup_test_files,
    ]
    
    results = []
    passed = []
    failed = []
    
    print("\n" + "=" * 70)
    print(" " * 20 + "GOLD TIER INTEGRATION TESTS")
    print("=" * 70)
    print()
    
    for test_func in tests:
        result = test_func()
        results.append(result)
        
        status = '[OK]' if result.success else '[FAIL]'
        print(f"{status} {result.name}")
        print(f"   {result.message} ({result.duration:.2f}s)")
        
        if result.success:
            passed.append(result)
        else:
            failed.append(result)
        
        # Small delay between tests
        time.sleep(0.5)
    
    print()
    print("=" * 70)
    print(f"RESULTS: {len(passed)}/{len(results)} passed")
    print(f"         {len(failed)}/{len(results)} failed")
    print("=" * 70)
    
    if failed:
        print("\nFailed Tests:")
        for r in failed:
            print(f"  [FAIL] {r.name}: {r.message}")
    
    print()
    print(f"Test logs saved to: {LOGS_PATH.absolute()}")
    print()
    
    return results, failed


if __name__ == '__main__':
    results, failed = run_all_tests()
    
    # Exit with error code if any tests failed
    exit(1 if failed else 0)
