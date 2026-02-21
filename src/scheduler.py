import schedule
import time
import logging
import subprocess
import threading
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler')

# Vault path
VAULT_PATH = 'AI_Employee_Vault'


def run_watchers():
    """
    Run all watcher scripts to check for new items.
    Each watcher runs once and checks for new content.
    Note: WhatsApp watcher is NOT included here - run it separately
    as it requires a continuous browser session.
    """
    logger.info("Running watchers...")

    watchers = [
        ('Gmail', 'watchers/gmail_watcher.py'),
        ('Filesystem', 'watchers/filesystem_watcher.py')
    ]

    for name, script in watchers:
        try:
            # Check if script exists
            if Path(script).exists():
                logger.info(f"Running {name} watcher...")
                # Run watcher once (not in loop mode)
                subprocess.run(
                    ['python', script],
                    timeout=30,
                    capture_output=True,
                    text=True
                )
            else:
                logger.debug(f"{name} watcher not found, skipping")
        except subprocess.TimeoutExpired:
            logger.warning(f"{name} watcher timed out")
        except Exception as e:
            logger.error(f"Error running {name} watcher: {e}")

    logger.info("All watchers completed")
    logger.info("Note: Run WhatsApp watcher separately for continuous monitoring")


def run_orchestrator_loop():
    """
    Run the orchestrator to process items in Needs_Action.
    Imports and calls the orchestrator function directly.
    """
    logger.info("Running orchestrator...")
    
    try:
        from orchestrator import run_orchestrator
        # Run one iteration (not in loop mode)
        run_orchestrator(vault_path=VAULT_PATH, loop=False, interval=0)
        logger.info("Orchestrator completed")
    except Exception as e:
        logger.error(f"Error running orchestrator: {e}")


def run_approval_checker():
    """
    Check Pending_Approval folder for approved/rejected items.
    """
    logger.info("Checking pending approvals...")
    
    try:
        pending_dir = Path(VAULT_PATH) / 'Pending_Approval'
        if not pending_dir.exists():
            return
        
        for approval_file in pending_dir.glob('*_Approval.md'):
            content = approval_file.read_text()
            
            if 'status: approved' in content:
                logger.info(f"Found approved action: {approval_file.name}")
                # TODO: Execute via MCP endpoint
                # requests.post('http://localhost:3000/approve_email', ...)
                
            elif 'status: rejected' in content:
                logger.info(f"Found rejected action: {approval_file.name}")
                # Move to Done with rejection note
        
    except Exception as e:
        logger.error(f"Error checking approvals: {e}")


def start_background_watchers():
    """
    Start watchers that run continuously in background threads.
    """
    from watchers.filesystem_watcher import FileSystemWatcher
    from watchers.whatsapp_watcher import WhatsAppWatcher

    # Filesystem watcher runs continuously
    try:
        watcher = FileSystemWatcher(VAULT_PATH)
        thread = threading.Thread(target=watcher.run, daemon=True)
        thread.start()
        logger.info("Filesystem watcher started (background)")
    except Exception as e:
        logger.error(f"Failed to start filesystem watcher: {e}")
    
    # WhatsApp watcher runs continuously with persistent browser
    try:
        watcher = WhatsAppWatcher(VAULT_PATH, check_interval=30)
        thread = threading.Thread(target=watcher.run, daemon=True)
        thread.start()
        logger.info("WhatsApp watcher started (background, persistent browser)")
        logger.info("Browser window will stay open - you can minimize it")
    except Exception as e:
        logger.error(f"Failed to start WhatsApp watcher: {e}")
        logger.info("Run 'python watchers/whatsapp_watcher.py' separately if needed")


def print_schedule():
    """Print current schedule status."""
    logger.info("=" * 60)
    logger.info("SCHEDULED TASKS")
    logger.info("=" * 60)
    for job in schedule.get_jobs():
        logger.info(f"  {job}")
    logger.info("=" * 60)


def main():
    logger.info("=" * 60)
    logger.info("AI EMPLOYEE VAULT - SCHEDULER")
    logger.info("=" * 60)
    logger.info(f"Vault: {VAULT_PATH}")
    
    # Start background watchers (run continuously)
    start_background_watchers()
    time.sleep(2)  # Give watcher time to initialize
    
    # Schedule periodic tasks
    schedule.every(2).minutes.do(run_watchers)
    schedule.every(1).minute.do(run_orchestrator_loop)
    schedule.every(30).seconds.do(run_approval_checker)
    
    # Print schedule
    print_schedule()
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    logger.info("Drop files in AI_Employee_Vault/Drop/ to test")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopping...")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
