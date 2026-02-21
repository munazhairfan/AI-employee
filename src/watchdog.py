"""
Gold Tier Watchdog - Process Monitor
Monitors watcher and orchestrator processes, restarts if dead.
Uses psutil for process management.

Run in background: python watchdog.py
Or: start /B python watchdog.py (Windows)
"""

import time
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    subprocess.run(['pip', 'install', 'psutil'], check=True)
    import psutil

# Configuration
LOGS_DIR = Path('Logs')
WATCHDOG_LOG = LOGS_DIR / 'watchdog.log'
PROCESSES_TO_MONITOR = [
    {'name': 'gmail_watcher.py', 'cmd': ['python', 'src/gmail_watcher.py']},
    {'name': 'whatsapp_watcher.py', 'cmd': ['python', 'src/whatsapp_watcher.py']},
    {'name': 'file_watcher.py', 'cmd': ['python', 'src/file_watcher.py']},
    {'name': 'orchestrator.py', 'cmd': ['python', 'src/orchestrator.py']},
    {'name': 'facebook_watcher.py', 'cmd': ['python', 'src/facebook_watcher.py']},
    {'name': 'instagram_watcher.py', 'cmd': ['python', 'src/instagram_watcher.py']},
    {'name': 'x_watcher.py', 'cmd': ['python', 'src/x_watcher.py']},
]
CHECK_INTERVAL = 30  # seconds
RESTART_DELAY = 5  # seconds before restart

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(WATCHDOG_LOG, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Watchdog')


def log_watchdog_event(event: str, process_name: str, details: str = None) -> None:
    """Log watchdog event to JSON log."""
    log_file = LOGS_DIR / f'{datetime.now().strftime("%Y-%m-%d")}.json'
    
    event_entry = {
        'timestamp': datetime.now().isoformat(),
        'source': 'watchdog',
        'event': event,
        'process': process_name,
        'details': details
    }
    
    # Read existing logs
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
    
    existing_logs.append(event_entry)
    log_file.write_text(json.dumps(existing_logs, indent=2), encoding='utf-8')


def find_process_by_name(name: str) -> list:
    """Find running processes by script name."""
    matching = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline:
                cmd_str = ' '.join(cmdline)
                if name in cmd_str:
                    matching.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return matching


def start_process(cmd: list) -> subprocess.Popen:
    """Start a process in background."""
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        return None


def restart_process(proc_config: dict) -> bool:
    """Restart a monitored process."""
    name = proc_config['name']
    cmd = proc_config['cmd']
    
    logger.info(f"Restarting {name}...")
    log_watchdog_event('restart_attempt', name, f'Command: {" ".join(cmd)}')
    
    # Kill any existing instances
    existing = find_process_by_name(name)
    for proc in existing:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            logger.info(f"Terminated existing {name} (PID: {proc.pid})")
        except Exception as e:
            logger.warning(f"Failed to terminate {name}: {e}")
            try:
                proc.kill()
                logger.info(f"Killed existing {name} (PID: {proc.pid})")
            except Exception:
                pass
    
    # Wait before restart
    time.sleep(RESTART_DELAY)
    
    # Start new instance
    new_proc = start_process(cmd)
    
    if new_proc:
        logger.info(f"Started new {name} (PID: {new_proc.pid})")
        log_watchdog_event('restart_success', name, f'New PID: {new_proc.pid}')
        return True
    else:
        logger.error(f"Failed to start {name}")
        log_watchdog_event('restart_failed', name, 'Could not start process')
        return False


def check_all_processes() -> dict:
    """Check status of all monitored processes."""
    status = {}
    
    for proc_config in PROCESSES_TO_MONITOR:
        name = proc_config['name']
        running = find_process_by_name(name)
        status[name] = {
            'running': len(running) > 0,
            'count': len(running),
            'pids': [p.pid for p in running] if running else []
        }
    
    return status


def run_watchdog():
    """Main watchdog loop."""
    logger.info("=" * 60)
    logger.info("Gold Tier Watchdog Starting")
    logger.info("=" * 60)
    logger.info(f"Monitoring {len(PROCESSES_TO_MONITOR)} processes")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Log file: {WATCHDOG_LOG}")
    logger.info("=" * 60)
    
    log_watchdog_event('watchdog_start', 'watchdog', 
                      f'Monitoring {len(PROCESSES_TO_MONITOR)} processes')
    
    # Track restart counts to prevent restart loops
    restart_counts = {name: 0 for name in [p['name'] for p in PROCESSES_TO_MONITOR]}
    max_restarts_per_hour = 3  # Prevent infinite restart loops
    
    while True:
        try:
            status = check_all_processes()
            
            for proc_config in PROCESSES_TO_MONITOR:
                name = proc_config['name']
                proc_status = status[name]
                
                if not proc_status['running']:
                    logger.warning(f"DEAD: {name}")
                    log_watchdog_event('process_dead', name, 'Not running')
                    
                    # Check restart limit
                    if restart_counts[name] >= max_restarts_per_hour:
                        logger.error(f"Skipping restart for {name} - max restarts reached")
                        log_watchdog_event('restart_skipped', name, 
                                         f'Max restarts ({max_restarts_per_hour}) reached')
                        continue
                    
                    # Attempt restart
                    if restart_process(proc_config):
                        restart_counts[name] += 1
                        logger.info(f"Restart count for {name}: {restart_counts[name]}/{max_restarts_per_hour}")
                else:
                    # Process is running - log status
                    logger.debug(f"OK: {name} (PID: {proc_status['pids']})")
                    
                    # Reset restart count if process has been stable
                    if restart_counts[name] > 0:
                        restart_counts[name] = 0
            
            # Reset restart counts every hour (simple approach)
            # In production, use a sliding window
            
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
            log_watchdog_event('watchdog_error', 'watchdog', str(e))
        
        time.sleep(CHECK_INTERVAL)


def get_process_summary() -> str:
    """Get summary of monitored processes."""
    status = check_all_processes()
    
    summary = []
    for name, proc_status in status.items():
        status_str = "RUNNING" if proc_status['running'] else "DEAD"
        pids = proc_status['pids'] if proc_status['pids'] else "none"
        summary.append(f"  {name}: {status_str} (PIDs: {pids})")
    
    return "\n".join(summary)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        # Show status and exit
        print("Gold Tier Watchdog - Process Status")
        print("=" * 60)
        print(get_process_summary())
        print("=" * 60)
    else:
        # Run watchdog
        run_watchdog()
