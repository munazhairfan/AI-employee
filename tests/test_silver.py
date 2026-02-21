"""
Silver Tier End-to-End Integration Test

Tests the complete pipeline:
1. Drop file with business keyword
2. Watcher copies to Needs_Action
3. Orchestrator creates Plan.md
4. Approval workflow simulation
5. MCP mock email send
6. Verify all outputs
"""

import sys
import time
import shutil
import threading
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Hardcoded vault path
VAULT_PATH = Path('AI_Employee_Vault')


def setup():
    """Clean and prepare vault directories."""
    print("=" * 60)
    print("SILVER TIER - END TO END TEST")
    print("=" * 60)
    
    # Create directories
    drop_path = VAULT_PATH / 'Drop'
    needs_action_path = VAULT_PATH / 'Needs_Action'
    done_path = VAULT_PATH / 'Done'
    plans_path = VAULT_PATH / 'Plans'
    pending_path = VAULT_PATH / 'Pending_Approval'
    
    for p in [drop_path, needs_action_path, done_path, plans_path, pending_path]:
        p.mkdir(parents=True, exist_ok=True)
    
    # Clean existing files
    for folder in [drop_path, needs_action_path, done_path, plans_path, pending_path]:
        for f in folder.glob('*'):
            f.unlink()
    
    # Clean dashboard
    dashboard = VAULT_PATH / 'Dashboard.md'
    if dashboard.exists():
        dashboard.unlink()
    
    # Clean processed cache files
    for cache in VAULT_PATH.glob('.processed_*'):
        cache.unlink()
    
    print("[SETUP] Directories cleaned")
    return drop_path, needs_action_path, done_path, plans_path, pending_path, dashboard


def create_test_file(drop_path: Path) -> Path:
    """Create a test file with business/sales keyword."""
    test_file = drop_path / 'client_invoice.txt'
    
    content = """---
type: file_drop
original_name: client_invoice.txt
size: 256
---

New file dropped for processing.

Subject: Urgent - Client Invoice #12345 for $750

Hi Team,

We just closed a new sales deal with ABC Corp! 
This is a $750 invoice for our AI automation services.

Please process this payment urgently.

Best regards,
Sales Team
"""
    
    test_file.write_text(content, encoding='utf-8')
    print(f"[TEST] Created test file: {test_file}")
    return test_file


def start_watcher(drop_path: Path, needs_action_path: Path):
    """Start filesystem watcher in background."""
    from watchers.filesystem_watcher import FileSystemWatcher
    
    watcher = FileSystemWatcher(str(VAULT_PATH))
    thread = threading.Thread(target=watcher.run, daemon=True)
    thread.start()
    print("[WATCHER] Filesystem watcher started")
    return thread


def start_orchestrator():
    """Start orchestrator in background."""
    from src.orchestrator import run_orchestrator
    
    thread = threading.Thread(
        target=lambda: run_orchestrator(str(VAULT_PATH), loop=True, interval=5),
        daemon=True
    )
    thread.start()
    print("[ORCHESTRATOR] Started (5s interval)")
    return thread


def simulate_approval(pending_path: Path) -> bool:
    """Simulate user approving an action."""
    print("[APPROVAL] Waiting for approval file...")
    
    max_wait = 30
    elapsed = 0
    
    while elapsed < max_wait:
        approval_files = list(pending_path.glob('*_Approval.md'))
        if approval_files:
            approval_file = approval_files[0]
            print(f"[APPROVAL] Found: {approval_file.name}")
            
            # Read and modify to approve
            content = approval_file.read_text(encoding='utf-8')
            content = content.replace(
                'status: pending_approval',
                'status: approved'
            )
            content = content.replace(
                'The orchestrator polls this folder every 60 seconds.',
                f'approved_at: {datetime.now().isoformat()}'
            )
            
            approval_file.write_text(content, encoding='utf-8')
            print(f"[APPROVAL] Approved: {approval_file.name}")
            return True
        
        time.sleep(1)
        elapsed += 1
    
    print("[APPROVAL] Timeout - no approval file found")
    return False


def verify_results(done_path: Path, plans_path: Path, dashboard: Path) -> dict:
    """Verify test results."""
    results = {
        'done_files': False,
        'plan_created': False,
        'dashboard_updated': False,
        'approval_processed': False
    }
    
    # Check Done folder
    done_files = list(done_path.glob('*'))
    if done_files:
        results['done_files'] = True
        print(f"[VERIFY] Done folder has {len(done_files)} file(s)")
        for f in done_files:
            print(f"  - {f.name}")
    
    # Check Plans folder
    plan_files = list(plans_path.glob('*_Plan.md'))
    if plan_files:
        results['plan_created'] = True
        print(f"[VERIFY] Plans folder has {len(plan_files)} file(s)")
        for f in plan_files:
            print(f"  - {f.name}")
    
    # Check Dashboard
    if dashboard.exists():
        results['dashboard_updated'] = True
        content = dashboard.read_text(encoding='utf-8')
        print(f"[VERIFY] Dashboard exists ({len(content)} bytes)")
        print(f"  Content preview: {content[:200]}...")
    
    # Check if approval was processed
    approval_done = list(done_path.glob('*_Approval.md'))
    if approval_done:
        results['approval_processed'] = True
        print(f"[VERIFY] Approval file moved to Done")
    
    return results


def run_test():
    """Run the complete end-to-end test."""
    
    # Setup
    drop_path, needs_action_path, done_path, plans_path, pending_path, dashboard = setup()
    
    # Start services
    watcher_thread = start_watcher(drop_path, needs_action_path)
    time.sleep(1)
    
    orchestrator_thread = start_orchestrator()
    time.sleep(1)
    
    # Create test file
    test_file = create_test_file(drop_path)
    print("\n[TEST] Waiting for watcher to process file...")
    
    # Wait for watcher to copy file
    time.sleep(5)
    
    # Check if file reached Needs_Action
    na_files = list(needs_action_path.glob('*.md'))
    if na_files:
        print(f"[TEST] File reached Needs_Action: {[f.name for f in na_files]}")
    else:
        print("[FAIL] File did not reach Needs_Action")
        print("\n" + "=" * 60)
        print("TEST FAILED - Watcher not working")
        print("=" * 60)
        return
    
    # Wait for orchestrator to create plan and approval
    print("\n[TEST] Waiting for orchestrator to create Plan and Approval...")
    time.sleep(10)
    
    # Check if Plan was created
    plan_files = list(plans_path.glob('*_Plan.md'))
    if plan_files:
        print(f"[TEST] Plan created: {plan_files[0].name}")
    else:
        print("[WARN] No Plan file created yet")
    
    # Check if Approval was requested
    approval_files = list(pending_path.glob('*_Approval.md'))
    if approval_files:
        print(f"[TEST] Approval requested: {approval_files[0].name}")
        
        # Simulate user approval
        print("\n[TEST] Simulating user approval...")
        approve_success = simulate_approval(pending_path)
        
        if approve_success:
            print("[TEST] Waiting for orchestrator to process approval...")
            time.sleep(10)
    
    # Wait for final processing
    print("\n[TEST] Waiting for final processing...")
    time.sleep(5)
    
    # Verify results
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    results = verify_results(done_path, plans_path, dashboard)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {check}")
        if success:
            passed += 1
    
    print("=" * 60)
    print(f"SCORE: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n*** SUCCESS: All silver tier features working! ***")
    elif passed >= total - 1:
        print("\n*** PARTIAL SUCCESS: Most features working ***")
    else:
        print("\n*** FAIL: Multiple issues detected ***")
    
    print("=" * 60)
    
    # Cleanup
    print("\n[CLEANUP] Removing test files...")
    for folder in [drop_path, needs_action_path, done_path, plans_path, pending_path]:
        for f in folder.glob('*'):
            f.unlink()
    if dashboard.exists():
        dashboard.unlink()
    print("[CLEANUP] Done")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_test()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
