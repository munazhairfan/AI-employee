"""
Weekly Audit Scheduler - Gold Tier
Runs SKILL_weekly_audit.md every Sunday at 8:00 AM

Usage: python scheduler_audit.py
Install: pip install schedule
"""

import schedule
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Hardcoded vault path
VAULT_PATH = Path('AI_Employee_Vault')
BRIEFINGS_PATH = VAULT_PATH / 'Briefings'
SKILLS_PATH = Path('skills')


def run_weekly_audit():
    """Execute the weekly audit skill via Claude."""
    print(f"[{datetime.now().isoformat()}] Starting Weekly Audit...")
    
    skill_file = SKILLS_PATH / 'SKILL_weekly_audit.md'
    
    if not skill_file.exists():
        print(f"ERROR: Skill file not found: {skill_file}")
        return
    
    try:
        # Execute skill via Claude CLI
        result = subprocess.run(
            ['claude', 'Execute', str(skill_file)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"[{datetime.now().isoformat()}] Weekly Audit completed successfully")
            print(f"Output: {result.stdout[:500]}...")
        else:
            print(f"[{datetime.now().isoformat()}] Weekly Audit failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().isoformat()}] ERROR: Audit timed out after 5 minutes")
    except FileNotFoundError:
        print(f"[{datetime.now().isoformat()}] ERROR: 'claude' command not found. Install Claude CLI.")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")


def main():
    """Main scheduler loop."""
    print("=" * 60)
    print("Weekly Audit Scheduler - Gold Tier")
    print("=" * 60)
    print(f"Vault: {VAULT_PATH.absolute()}")
    print(f"Skill: {SKILLS_PATH / 'SKILL_weekly_audit.md'}")
    print(f"Schedule: Every Sunday at 8:00 AM")
    print("=" * 60)
    
    # Ensure briefings directory exists
    BRIEFINGS_PATH.mkdir(parents=True, exist_ok=True)
    
    # Schedule weekly audit for Sunday 8:00 AM
    schedule.every().sunday.at("08:00").do(run_weekly_audit)
    
    print(f"[{datetime.now().isoformat()}] Scheduler started. Waiting for jobs...")
    print("Press Ctrl+C to stop.\n")
    
    # Run pending jobs immediately (for testing)
    # schedule.run_pending()
    
    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    main()
