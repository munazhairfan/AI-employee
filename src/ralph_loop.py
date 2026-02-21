"""
Ralph Loop - Gold Tier Autonomous Multi-Step Executor
Named after Ralph Wiggum: "I'm stuck in a loop!"

Retries tasks until completion or max iterations.
Usage: from ralph_loop import run_ralph
       run_ralph('weekly_audit', 'skills/SKILL_weekly_audit.md')
"""

import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


class RalphLoop:
    """Autonomous multi-step task executor with retry logic."""
    
    def __init__(self, vault_path: str = 'AI_Employee_Vault', max_iterations: int = 10):
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.done_path = self.vault_path / 'Done'
        self.logs_path = Path('Logs')
        
        # Ensure directories exist
        self.done_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger('RalphLoop')
        self.logger.setLevel(logging.INFO)
        
    def _setup_logger(self, task_name: str) -> logging.Logger:
        """Setup file logger for specific task."""
        log_file = self.logs_path / f'ralph_{task_name}.log'
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        return self.logger
    
    def _check_done_folder(self, task_name: str, since: datetime) -> bool:
        """Check if any file was created in /Done since timestamp."""
        if not self.done_path.exists():
            return False
        
        for file in self.done_path.iterdir():
            if file.is_file():
                # Check if file was modified after our start time
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime > since:
                    self.logger.info(f"Found new file in /Done: {file.name}")
                    return True
        
        return False
    
    def _check_task_complete(self, output: str) -> bool:
        """Check if output contains TASK_COMPLETE marker."""
        return 'TASK_COMPLETE' in output
    
    def _execute_skill(self, skill_path: Path, task_context: str = '') -> Tuple[str, int]:
        """Execute skill via Claude CLI."""
        try:
            # Build the command
            cmd = ['claude', 'Execute', str(skill_path)]
            
            # Add task context if provided
            if task_context:
                cmd.extend(['--context', task_context])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per iteration
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]: {result.stderr}"
            
            return output, result.returncode
            
        except subprocess.TimeoutExpired:
            return "ERROR: Task timed out after 10 minutes", -1
        except FileNotFoundError:
            return "ERROR: 'claude' command not found. Install Claude CLI.", -2
        except Exception as e:
            return f"ERROR: {str(e)}", -3
    
    def run_ralph(self, task_name: str, skill_md: str, context: str = '') -> dict:
        """
        Run Ralph Loop for autonomous multi-step task execution.
        
        Args:
            task_name: Name of the task (for logging)
            skill_md: Path to the skill markdown file
            context: Optional context/instructions for the task
        
        Returns:
            dict with keys: success, iterations, output, log_file
        """
        start_time = datetime.now()
        skill_path = Path(skill_md)
        
        # Validate skill file exists
        if not skill_path.exists():
            return {
                'success': False,
                'error': f'Skill file not found: {skill_path}',
                'iterations': 0
            }
        
        # Setup logger
        logger = self._setup_logger(task_name)
        log_file = self.logs_path / f'ralph_{task_name}.log'
        
        logger.info("=" * 60)
        logger.info(f"Ralph Loop Starting: {task_name}")
        logger.info(f"Skill: {skill_path}")
        logger.info(f"Max Iterations: {self.max_iterations}")
        logger.info("=" * 60)
        
        # Track state
        iteration = 0
        last_output = ""
        
        while iteration < self.max_iterations:
            iteration += 1
            
            logger.info(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            logger.info(f"Executing skill: {skill_path}")
            
            # Execute skill
            output, returncode = self._execute_skill(skill_path, context)
            last_output = output
            
            # Log output (truncated if too long)
            output_preview = output[:500] + "..." if len(output) > 500 else output
            logger.info(f"Output:\n{output_preview}")
            
            # Check for errors
            if returncode != 0 or output.startswith("ERROR:"):
                logger.warning(f"Iteration {iteration} failed: {output[:200]}")
                logger.info("Retrying...")
                time.sleep(2)  # Brief pause before retry
                continue
            
            # Check completion condition 1: TASK_COMPLETE marker
            if self._check_task_complete(output):
                logger.info("✓ Found TASK_COMPLETE marker in output")
                break
            
            # Check completion condition 2: New file in /Done
            if self._check_done_folder(task_name, start_time):
                logger.info("✓ Found new file in /Done folder")
                break
            
            # Check completion condition 3: Output indicates completion
            completion_keywords = [
                'task completed',
                'finished successfully',
                'all steps done',
                'audit complete',
                'briefing generated'
            ]
            if any(keyword in output.lower() for keyword in completion_keywords):
                logger.info("✓ Completion detected in output")
                break
            
            logger.info("Task not complete, continuing loop...")
            time.sleep(1)  # Brief pause between iterations
        
        # Determine final status
        success = iteration < self.max_iterations or self._check_task_complete(last_output)
        
        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("Ralph Loop Summary")
        logger.info("=" * 60)
        logger.info(f"Task: {task_name}")
        logger.info(f"Status: {'✓ COMPLETED' if success else '✗ MAX ITERATIONS REACHED'}")
        logger.info(f"Iterations: {iteration}")
        logger.info(f"Duration: {datetime.now() - start_time}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 60)
        
        return {
            'success': success,
            'iterations': iteration,
            'output': last_output,
            'log_file': str(log_file),
            'duration': (datetime.now() - start_time).total_seconds()
        }


# Convenience function
def run_ralph(task_name: str, skill_md: str, context: str = '', 
              vault_path: str = 'AI_Employee_Vault', max_iterations: int = 10) -> dict:
    """
    Run Ralph Loop for autonomous multi-step task execution.
    
    Args:
        task_name: Name of the task (for logging)
        skill_md: Path to the skill markdown file
        context: Optional context/instructions for the task
        vault_path: Path to the vault directory
        max_iterations: Maximum loop iterations (default: 10)
    
    Returns:
        dict with keys: success, iterations, output, log_file
    
    Example:
        >>> result = run_ralph('weekly_audit', 'skills/SKILL_weekly_audit.md')
        >>> if result['success']:
        ...     print(f"Completed in {result['iterations']} iterations")
    """
    ralph = RalphLoop(vault_path=vault_path, max_iterations=max_iterations)
    return ralph.run_ralph(task_name, skill_md, context)


if __name__ == '__main__':
    import sys
    
    # Example usage
    if len(sys.argv) >= 3:
        task = sys.argv[1]
        skill = sys.argv[2]
        
        print(f"Running Ralph Loop: {task}")
        print(f"Skill: {skill}")
        
        result = run_ralph(task, skill)
        
        print(f"\nResult: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"Iterations: {result['iterations']}")
        print(f"Log: {result['log_file']}")
    else:
        print("Usage: python ralph_loop.py <task_name> <skill_md>")
        print("Example: python ralph_loop.py weekly_audit skills/SKILL_weekly_audit.md")
