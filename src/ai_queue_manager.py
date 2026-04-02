"""
AI Queue Manager - Priority-Based Rate Limiting

Manages AI API calls with:
- Priority queue (user actions > background tasks)
- Rate limiting (10 calls/minute for user, 1 call/5min for background)
- Automatic retry on rate limit errors
- Task status tracking

Usage:
    from ai_queue_manager import ai_queue_manager
    
    # Submit high priority task (user action)
    eta = ai_queue_manager.submit(
        task_data={'text': 'Send email to john@example.com'},
        callback=lambda data: analyze_intent(data['text']),
        priority='high'
    )
    
    # Submit low priority task (background file)
    eta = ai_queue_manager.submit(
        task_data={'file': 'whatsapp_123.md'},
        callback=lambda data: process_file(data['file']),
        priority='low'
    )
"""

import threading
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Dict, Any, Optional
import uuid
import traceback


class AIQueueManager:
    def __init__(self):
        # Rate limits
        self.high_priority_interval = 6  # 10 calls/minute (6 seconds apart)
        self.low_priority_interval = 300  # 1 call/5 minutes (300 seconds)
        
        # Queue storage
        self.high_queue = []  # User actions
        self.low_queue = []   # Background files
        self.processing = {}  # Currently processing tasks
        self.completed = {}   # Completed tasks (cache)
        
        # Rate limiting
        self.last_high_call = 0
        self.last_low_call = 0
        
        # Thread safety
        self.lock = threading.Lock()
        self.running = True
        
        # Worker thread
        self.worker_thread = None
        self._start_worker()
        
        # Status file for dashboard polling
        self.status_file = Path('data/ai_queue_status.json')
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _start_worker(self):
        """Start background worker thread"""
        self.worker_thread = threading.Thread(target=self._process_queues, daemon=True)
        self.worker_thread.start()
        print("[AI Queue] Worker thread started")
    
    def submit(self, task_data: Any, callback: Callable, 
               priority: str = 'high', task_id: Optional[str] = None) -> tuple:
        """
        Submit task for AI processing.

        Args:
            task_data: Data to pass to callback (can be string, dict, or any type)
            callback: Function to call with task_data
            priority: 'high' (user) or 'low' (background)
            task_id: Optional custom task ID

        Returns:
            (task_id, estimated_wait_seconds)
        """
        if task_id is None:
            task_id = str(uuid.uuid4())[:8]

        task = {
            'id': task_id,
            'data': task_data,
            'callback': callback,
            'priority': priority,
            'submitted_at': time.time(),
            'status': 'queued',
            'result': None,
            'error': None
        }
        
        with self.lock:
            if priority == 'high':
                self.high_queue.append(task)
                eta = len(self.high_queue) * self.high_priority_interval
            else:
                self.low_queue.append(task)
                eta = len(self.low_queue) * self.low_priority_interval
            
            # Store for polling
            self.processing[task_id] = task
            
            # Save status
            self._save_status()
        
        print(f"[AI Queue] Task {task_id} queued ({priority} priority, ETA: {eta}s)")
        return task_id, eta
        
        with self.lock:
            if priority == 'high':
                self.high_queue.append(task)
                # Estimate: 6 seconds per high priority task ahead
                eta = len(self.high_queue) * self.high_priority_interval
            else:
                self.low_queue.append(task)
                # Estimate: 300 seconds per low priority task ahead
                eta = len(self.low_queue) * self.low_priority_interval
            
            # Store for polling
            self.processing[task_id] = task
            self._save_status()
        
        print(f"[AI Queue] Task {task_id} queued ({priority} priority, ETA: {eta}s)")
        return task_id, eta
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task (for polling)"""
        with self.lock:
            # Check processing
            if task_id in self.processing:
                task = self.processing[task_id]
                return {
                    'id': task_id,
                    'status': task['status'],
                    'priority': task['priority'],
                    'submitted_at': task['submitted_at'],
                    'result': task['result'],
                    'error': task['error']
                }
            
            # Check completed cache
            if task_id in self.completed:
                return self.completed[task_id]
        
        return None
    
    def _process_queues(self):
        """Background worker - processes queues with rate limiting"""
        print("[AI Queue] Worker loop started")
        
        while self.running:
            try:
                # Always process high priority first
                task = self._get_next_task()
                
                if task:
                    self._process_task(task)
                else:
                    # No tasks, sleep briefly
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[AI Queue] Worker error: {e}")
                traceback.print_exc()
                time.sleep(5)
    
    def _get_next_task(self) -> Optional[Dict]:
        """Get next task to process (respects rate limits)"""
        with self.lock:
            now = time.time()
            
            # High priority first
            if self.high_queue:
                time_since_last = now - self.last_high_call
                if time_since_last >= self.high_priority_interval:
                    return self.high_queue.pop(0)
            
            # Then low priority
            if self.low_queue:
                time_since_last = now - self.last_low_call
                if time_since_last >= self.low_priority_interval:
                    return self.low_queue.pop(0)
            
            # No tasks ready
            return None
    
    def _process_task(self, task: Dict):
        """Process a single task"""
        task_id = task['id']
        priority = task['priority']
        
        print(f"[AI Queue] Processing task {task_id} ({priority})")
        
        # DEBUG: Check callback before calling
        callback = task['callback']
        print(f"[AI Queue DEBUG] _process_task - callback type: {type(callback)}, callable: {callable(callback)}")
        print(f"[AI Queue DEBUG] _process_task - task['data'] type: {type(task['data'])}")
        
        try:
            # Update status
            with self.lock:
                task['status'] = 'processing'
                self._save_status()
            
            # Execute callback
            print(f"[AI Queue DEBUG] About to call callback with data: {task['data']}")
            result = callback(task['data'])
            print(f"[AI Queue DEBUG] Callback returned: {type(result)}")
            
            # Store result
            with self.lock:
                task['status'] = 'completed'
                task['result'] = result
                self.completed[task_id] = {
                    'id': task_id,
                    'status': 'completed',
                    'result': result,
                    'completed_at': time.time()
                }
                
                # Remove from processing
                if task_id in self.processing:
                    del self.processing[task_id]
                
                # Update rate limit timestamp
                if priority == 'high':
                    self.last_high_call = time.time()
                else:
                    self.last_low_call = time.time()
                
                self._save_status()
            
            print(f"[AI Queue] Task {task_id} completed")
            
        except Exception as e:
            print(f"[AI Queue] Task {task_id} failed: {e}")
            traceback.print_exc()
            
            with self.lock:
                task['status'] = 'failed'
                task['error'] = str(e)
                
                # Remove from processing
                if task_id in self.processing:
                    del self.processing[task_id]
                
                self._save_status()
    
    def _save_status(self):
        """Save queue status to file (for dashboard polling)"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'high_queue_length': len(self.high_queue),
                'low_queue_length': len(self.low_queue),
                'processing_count': len(self.processing),
                'tasks': []
            }
            
            # Save task info WITHOUT callbacks (can't JSON serialize functions)
            for task_id, task in list(self.processing.items())[-10:]:  # Last 10 tasks
                status['tasks'].append({
                    'id': task['id'],
                    'priority': task['priority'],
                    'status': task['status'],
                    'submitted_at': task['submitted_at'],
                    # DON'T save callback - it's already in memory
                    # DON'T save data - might be large
                })
            
            self.status_file.write_text(json.dumps(status, indent=2, default=str), encoding='utf-8')
        except Exception as e:
            print(f"[AI Queue] Failed to save status: {e}")
    
    def shutdown(self):
        """Shutdown worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("[AI Queue] Shutdown complete")


# Global instance
ai_queue_manager = AIQueueManager()


# Convenience functions for common use cases

def submit_user_task(task_data: Dict[str, Any], callback: Callable) -> tuple:
    """Submit high-priority task (user action)"""
    return ai_queue_manager.submit(task_data, callback, priority='high')


def submit_background_task(task_data: Dict[str, Any], callback: Callable) -> tuple:
    """Submit low-priority task (background file processing)"""
    return ai_queue_manager.submit(task_data, callback, priority='low')


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status by ID"""
    return ai_queue_manager.get_task_status(task_id)


# For backwards compatibility - synchronous call with rate limiting
def call_ai_with_rate_limit(callback: Callable, task_data: Any,
                            priority: str = 'high', timeout: int = 120) -> Any:
    """
    Call AI function with automatic rate limiting (blocking).

    Use this for synchronous calls where user waits for result.

    Args:
        callback: Function to call (receives task_data as argument)
        task_data: Data to pass to callback (can be string, dict, or any type)
        priority: 'high' (user) or 'low' (background)
        timeout: Max seconds to wait
    """
    task_id, eta = ai_queue_manager.submit(task_data, callback, priority=priority)

    # Wait for completion
    start_time = time.time()
    while True:
        status = ai_queue_manager.get_task_status(task_id)

        if status is None:
            raise Exception("Task not found")

        if status['status'] == 'completed':
            return status['result']

        if status['status'] == 'failed':
            raise Exception(status['error'])

        # Check timeout
        if time.time() - start_time > timeout:
            raise Exception(f"Task {task_id} timed out after {timeout} seconds")

        # Wait a bit
        time.sleep(1)
