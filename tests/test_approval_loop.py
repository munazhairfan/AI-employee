"""
Human-in-the-Loop Approval Test Suite
Tests the complete approval workflow:
1. Drop file with action request
2. Watcher detects → orchestrator creates draft
3. Draft in Pending_Approval (NOT executed yet)
4. Manually approve in file
5. Orchestrator detects approval → executes via MCP
6. Verify execution only after approval

Usage: python test_approval_loop.py
"""

import time
import json
import shutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


# Configuration
VAULT_PATH = Path('AI_Employee_Vault')
LOGS_PATH = Path('Logs')
TEST_TIMEOUT = 120  # seconds
POLL_INTERVAL = 2   # seconds


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
    log_file = LOGS_PATH / f'test_approval_{datetime.now().strftime("%Y-%m-%d")}.json'

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


def cleanup_test_files() -> None:
    """Clean up test files from previous runs."""
    print("\n[CLEANUP] Removing test files from previous runs...")

    # Clean Needs_Action
    for f in VAULT_PATH.glob('Needs_Action/test_*.md'):
        f.unlink()

    # Clean Pending_Approval
    for f in VAULT_PATH.glob('Pending_Approval/WhatsApp_Draft_*.md'):
        f.unlink()

    # Clean Done
    for f in VAULT_PATH.glob('Done/test_*.md'):
        f.unlink()
    for f in VAULT_PATH.glob('Done/WhatsApp_Draft_*.md'):
        f.unlink()

    # Clean Rejected
    for f in VAULT_PATH.glob('Rejected/WhatsApp_Draft_*.md'):
        f.unlink()

    print("[CLEANUP] Done")


def test_vault_structure() -> TestResult:
    """Test 1: Verify vault directory structure exists."""
    result = TestResult('Vault Structure')
    start = time.time()

    try:
        required_dirs = [
            VAULT_PATH / 'Drop',
            VAULT_PATH / 'Needs_Action',
            VAULT_PATH / 'Done',
            VAULT_PATH / 'Pending_Approval',
            VAULT_PATH / 'Rejected',
            LOGS_PATH
        ]

        for dir_path in required_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        result.success = all(d.exists() for d in required_dirs)
        result.message = f'Created/verified {len(required_dirs)} directories'
    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_drop_whatsapp_request() -> TestResult:
    """Test 2: Drop file with WhatsApp payment reminder request."""
    result = TestResult('Drop WhatsApp Request File')
    start = time.time()

    try:
        # Create test file with WhatsApp payment reminder request
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        test_file = VAULT_PATH / 'Drop' / f'test_whatsapp_payment_{timestamp}.md'

        content = f"""---
type: whatsapp_request
priority: high
subject: Payment Reminder
created: {datetime.now().isoformat()}
---

# WhatsApp Payment Reminder Request

**To:** +923001234567
**Subject:** Payment Reminder - Invoice #12345

Please send a WhatsApp message to the client regarding overdue payment.

Message content:
"Assalam-o-Alaikum! This is a friendly reminder that invoice #12345 for PKR 50,000 is now 15 days overdue. Please process the payment at your earliest convenience. JazakAllah!"

---
*Test file for approval loop*
"""

        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(content)

        result.success = test_file.exists()
        result.message = f'Created: {test_file.name}'

        # Also copy to Needs_Action to simulate watcher
        needs_action_file = VAULT_PATH / 'Needs_Action' / test_file.name
        shutil.copy2(str(test_file), str(needs_action_file))

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def wait_for_draft(timeout: int = TEST_TIMEOUT) -> Optional[Path]:
    """Wait for draft to appear in Pending_Approval."""
    print(f"\n[WAITING] Polling Pending_Approval for draft (timeout: {timeout}s)...")

    start = time.time()
    while time.time() - start < timeout:
        drafts = list(VAULT_PATH.glob('Pending_Approval/WhatsApp_Draft_*.md'))
        if drafts:
            print(f"[FOUND] Draft created: {drafts[0].name}")
            return drafts[0]
        time.sleep(POLL_INTERVAL)

    print(f"[TIMEOUT] No draft found after {timeout}s")
    return None


def test_draft_created_in_pending() -> TestResult:
    """Test 3: Verify draft created in Pending_Approval (not executed yet)."""
    result = TestResult('Draft Created in Pending_Approval')
    start = time.time()

    try:
        # Wait for draft
        draft_file = wait_for_draft()

        if draft_file and draft_file.exists():
            content = draft_file.read_text()

            # Verify draft has approval checkboxes
            has_approve = '- [ ] Approve' in content or '- [x] Approve' in content
            has_reject = '- [ ] Reject' in content or '- [x] Reject' in content

            # Verify NOT executed yet (should be in Pending_Approval, not Done)
            in_pending = draft_file.parent.name == 'Pending_Approval'

            result.success = has_approve and has_reject and in_pending
            result.message = f'Draft created with approval checkboxes (not executed yet)'
        else:
            result.success = False
            result.message = 'Draft not created in Pending_Approval'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def approve_draft_manually(draft_file: Path) -> bool:
    """Manually approve draft by marking checkbox in file."""
    try:
        content = draft_file.read_text()

        # Change unchecked approve to checked
        if '- [ ] Approve' in content:
            content = content.replace('- [ ] Approve', '- [x] Approve')
        elif '- [ ] Approve (execute manually)' in content:
            content = content.replace('- [ ] Approve (execute manually)', '- [x] Approve (execute manually)')

        draft_file.write_text(content)
        print(f"[APPROVED] Draft approved manually: {draft_file.name}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to approve draft: {e}")
        return False


def wait_for_execution(timeout: int = TEST_TIMEOUT) -> Tuple[bool, str]:
    """Wait for draft to be executed and moved to Done."""
    print(f"\n[WAITING] Polling for execution (timeout: {timeout}s)...")

    start = time.time()
    while time.time() - start < timeout:
        # Check if file moved to Done
        done_files = list(VAULT_PATH.glob('Done/WhatsApp_Draft_*.md'))
        if done_files:
            print(f"[EXECUTED] Draft moved to Done: {done_files[0].name}")
            return True, done_files[0].name

        # Check logs for execution
        log_file = LOGS_PATH / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
                for entry in reversed(logs[-10:]):
                    if 'whatsapp' in entry.get('action', '').lower() and 'sent' in entry.get('result', '').lower():
                        print(f"[LOG] Execution detected in logs")
                        return True, 'log_entry'
            except:
                pass

        time.sleep(POLL_INTERVAL)

    print(f"[TIMEOUT] Execution not detected after {timeout}s")
    return False, 'timeout'


def test_approval_triggers_execution() -> TestResult:
    """Test 4: Approve draft and verify MCP execution."""
    result = TestResult('Approval Triggers MCP Execution')
    start = time.time()

    try:
        # Find draft in Pending_Approval
        drafts = list(VAULT_PATH.glob('Pending_Approval/WhatsApp_Draft_*.md'))
        if not drafts:
            result.success = False
            result.message = 'No draft found in Pending_Approval'
            return result

        draft_file = drafts[0]

        # Manually approve
        print("\n[ACTION] Manually approving draft...")
        if not approve_draft_manually(draft_file):
            result.success = False
            result.message = 'Failed to approve draft'
            return result

        # Wait for execution
        time.sleep(5)  # Give orchestrator time to poll
        executed, location = wait_for_execution()

        if executed:
            result.success = True
            result.message = f'Draft executed after approval → {location}'
        else:
            result.success = False
            result.message = 'Draft not executed after approval (check MCP config)'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_rejection_workflow() -> TestResult:
    """Test 5: Create draft, reject it, verify moved to Rejected."""
    result = TestResult('Rejection Workflow')
    start = time.time()

    try:
        # Create a new test file for rejection
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        test_file = VAULT_PATH / 'Drop' / f'test_reject_{timestamp}.md'

        content = f"""---
type: whatsapp_request
priority: normal
subject: Test Rejection
---

Send WhatsApp to +923009999999: "Test message"
"""

        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(content)

        # Copy to Needs_Action
        needs_action_file = VAULT_PATH / 'Needs_Action' / test_file.name
        shutil.copy2(str(test_file), str(needs_action_file))

        print("\n[WAITING] Waiting for rejection test draft...")
        time.sleep(10)

        # Find new draft
        drafts = list(VAULT_PATH.glob('Pending_Approval/WhatsApp_Draft_*.md'))
        if len(drafts) < 2:
            result.success = False
            result.message = 'Rejection draft not created'
            return result

        draft_file = drafts[-1]  # Get latest

        # Manually reject
        print("[ACTION] Manually rejecting draft...")
        content = draft_file.read_text()
        if '- [ ] Reject' in content:
            content = content.replace('- [ ] Reject', '- [x] Reject')
            content += "\n\n**Rejection Reason:** Test rejection - do not execute"
            draft_file.write_text(content)

        # Wait for move to Rejected
        time.sleep(5)
        print("[WAITING] Polling for rejection...")

        rejected_files = list(VAULT_PATH.glob('Rejected/WhatsApp_Draft_*.md'))
        if rejected_files:
            result.success = True
            result.message = f'Rejected draft moved to Rejected/'
        else:
            result.success = False
            result.message = 'Rejected draft not moved to Rejected/'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def test_no_execution_without_approval() -> TestResult:
    """Test 6: Verify draft NOT executed without approval mark."""
    result = TestResult('No Execution Without Approval')
    start = time.time()

    try:
        # Create a new test file
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        test_file = VAULT_PATH / 'Drop' / f'test_no_approval_{timestamp}.md'

        content = f"""---
type: whatsapp_request
priority: normal
subject: Test No Approval
---

Send WhatsApp to +923008888888: "Test - should not send"
"""

        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(content)

        # Copy to Needs_Action
        needs_action_file = VAULT_PATH / 'Needs_Action' / test_file.name
        shutil.copy2(str(test_file), str(needs_action_file))

        print("\n[WAITING] Waiting for unapproved draft...")
        time.sleep(10)

        # Find draft
        drafts = list(VAULT_PATH.glob('Pending_Approval/WhatsApp_Draft_*.md'))
        if not drafts:
            result.success = False
            result.message = 'Draft not created'
            return result

        draft_file = drafts[-1]

        # Verify still in Pending_Approval (not executed)
        time.sleep(10)  # Wait to ensure no execution

        still_pending = draft_file.exists() and draft_file.parent.name == 'Pending_Approval'

        # Check logs for any execution
        log_file = LOGS_PATH / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        executed = False
        if log_file.exists():
            logs = json.loads(log_file.read_text())
            for entry in logs:
                if 'test_no_approval' in entry.get('action', '').lower():
                    executed = True
                    break

        result.success = still_pending and not executed
        result.message = 'Draft NOT executed without approval (correct behavior)' if still_pending else 'Draft executed without approval (BUG!)'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def check_done_folder() -> TestResult:
    """Test 7: Verify executed items in Done folder."""
    result = TestResult('Check Done Folder')
    start = time.time()

    try:
        done_files = list(VAULT_PATH.glob('Done/WhatsApp_Draft_*.md'))

        if done_files:
            result.success = True
            result.message = f'Found {len(done_files)} executed draft(s) in Done/'

            # Print details
            for f in done_files:
                content = f.read_text()
                if 'Sent via' in content:
                    print(f"  ✓ {f.name} - Executed via API")
                else:
                    print(f"  ○ {f.name} - Moved to Done")
        else:
            result.success = False
            result.message = 'No executed drafts in Done/'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def check_logs() -> TestResult:
    """Test 8: Verify approval workflow logged."""
    result = TestResult('Check Approval Logs')
    start = time.time()

    try:
        log_file = LOGS_PATH / f'{datetime.now().strftime("%Y-%m-%d")}.json'

        if not log_file.exists():
            result.success = False
            result.message = 'Log file not found'
            return result

        logs = json.loads(log_file.read_text())

        # Look for approval-related actions
        approval_actions = [
            'draft_created',
            'draft_approved',
            'draft_rejected',
            'moved_to_done',
            'moved_to_rejected'
        ]

        found_actions = []
        for entry in logs:
            action = entry.get('action', '')
            if action in approval_actions:
                found_actions.append(action)

        result.success = len(found_actions) > 0
        result.message = f'Found {len(found_actions)} approval workflow actions: {", ".join(set(found_actions))}'

    except Exception as e:
        result.error = e
        result.message = f'Failed: {e}'

    result.duration = time.time() - start
    log_test_result(result)
    return result


def print_summary(results: list) -> None:
    """Print test summary."""
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    print("\n" + "=" * 70)
    print(" " * 20 + "APPROVAL LOOP TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 70)

    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r.success:
                print(f"  [FAIL] {r.name}: {r.message}")

    print("\n" + "=" * 70)
    if passed == len(results):
        print("✓ SUCCESS: All approval loop tests passed!")
        print("✓ Human-in-the-loop workflow verified:")
        print("  - Drafts created in Pending_Approval")
        print("  - NO execution without approval")
        print("  - Execution only after manual approval")
        print("  - Rejection moves to Rejected/")
        print("  - Executed items in Done/")
    else:
        print("✗ Some tests failed. Check MCP configuration and logs.")
    print("=" * 70 + "\n")


def run_all_tests() -> list:
    """Run all approval loop tests."""
    tests = [
        test_vault_structure,
        test_drop_whatsapp_request,
        test_draft_created_in_pending,
        test_approval_triggers_execution,
        test_rejection_workflow,
        test_no_execution_without_approval,
        check_done_folder,
        check_logs,
    ]

    results = []

    print("\n" + "=" * 70)
    print(" " * 15 + "HUMAN-IN-THE-LOOP APPROVAL TEST")
    print("=" * 70)
    print("\nThis test simulates the complete approval workflow:")
    print("1. Drop file with WhatsApp payment reminder")
    print("2. Orchestrator creates draft in Pending_Approval")
    print("3. Draft waits for human approval (NOT executed)")
    print("4. Manually approve by marking checkbox in file")
    print("5. Orchestrator detects approval → executes via MCP")
    print("6. Verify execution only after approval")
    print("=" * 70)

    # Cleanup first
    cleanup_test_files()

    for test_func in tests:
        print(f"\n[TEST] Running: {test_func.__name__}")
        result = test_func()
        results.append(result)

        status = '[OK]' if result.success else '[FAIL]'
        print(f"{status} {result.name}")
        print(f"   {result.message} ({result.duration:.2f}s)")

        # Small delay between tests
        time.sleep(1)

    print_summary(results)

    return results


if __name__ == '__main__':
    results = run_all_tests()

    # Exit with error code if any tests failed
    exit(1 if any(not r.success for r in results) else 0)
