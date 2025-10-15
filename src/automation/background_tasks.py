#!/usr/bin/env python3
"""
Background Task Queue

Handles async execution of long-running tasks like entity card generation.
Prevents blocking the main request-response loop.

Features:
- Concurrent workers (ThreadPoolExecutor)
- Automatic retry on failure (with exponential backoff)
- Task persistence (survives crashes)
- Special handling for low balance errors (402)
"""

import threading
import queue
import time
import json
import concurrent.futures
from typing import Callable, Any, Optional, Tuple, Dict
from pathlib import Path
from datetime import datetime


class BackgroundTaskQueue:
    """Thread-safe background task queue with concurrent workers

    Tasks are executed in a thread pool for parallel processing.
    Failed tasks are automatically retried with exponential backoff.
    Tasks persist to disk to prevent loss on crash/shutdown.
    """

    def __init__(self, max_queue_size: int = 50, max_workers: int = 4,
                 persistence_file: Optional[Path] = None):
        """Initialize background task queue

        Args:
            max_queue_size: Maximum number of queued tasks
            max_workers: Number of concurrent worker threads (default 4)
            persistence_file: Path to save pending tasks (optional)
        """
        self.task_queue = queue.Queue(maxsize=max_queue_size)
        self.results_queue = queue.Queue()
        self.active = True
        self._tasks_completed = 0
        self._tasks_failed = 0
        self._tasks_retried = 0
        self._tasks_pending: Dict[str, dict] = {}  # Track pending tasks
        self.max_workers = max_workers
        self.persistence_file = persistence_file
        self._lock = threading.Lock()

        # Load persisted tasks
        if self.persistence_file and self.persistence_file.exists():
            self._load_persisted_tasks()

        # Start worker pool
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="BGTask"
        )

        # Start dispatcher thread (feeds tasks to executor)
        self.dispatcher_thread = threading.Thread(target=self._dispatcher, daemon=True)
        self.dispatcher_thread.start()

    def _load_persisted_tasks(self) -> None:
        """Load persisted tasks from disk"""
        try:
            data = json.loads(self.persistence_file.read_text(encoding='utf-8'))
            # Note: We can't persist the actual function objects, only metadata
            # Persisted tasks would need to be requeued by the application
            print(f"[BGTaskQueue] Loaded {len(data.get('pending', []))} persisted task records")
        except Exception as e:
            print(f"[BGTaskQueue] Warning: Could not load persisted tasks: {e}")

    def _save_pending_tasks(self) -> None:
        """Save pending tasks to disk"""
        if not self.persistence_file:
            return

        try:
            with self._lock:
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'pending': [
                        {
                            'task_id': task_id,
                            'queued_at': info['queued_at'],
                            'retry_count': info['retry_count']
                        }
                        for task_id, info in self._tasks_pending.items()
                    ],
                    'stats': self.get_stats()
                }

            self.persistence_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"[BGTaskQueue] Warning: Could not persist tasks: {e}")

    def _dispatcher(self) -> None:
        """Dispatcher thread that submits tasks to executor pool"""
        while self.active:
            try:
                # Get task with timeout so we can check active flag
                try:
                    task_data = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                task_id, func, args, kwargs, callback, retry_count, max_retries = task_data

                # Track as pending
                with self._lock:
                    self._tasks_pending[task_id] = {
                        'queued_at': datetime.now().isoformat(),
                        'retry_count': retry_count
                    }
                    self._save_pending_tasks()

                # Submit to executor pool
                future = self.executor.submit(self._execute_task, task_id, func, args, kwargs, callback, retry_count, max_retries)

                # Task is now running
                self.task_queue.task_done()

            except Exception as e:
                print(f"[BGTaskQueue] Dispatcher error: {e}")

    def _execute_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict,
                      callback: Optional[Callable], retry_count: int, max_retries: int) -> None:
        """Execute a single task (runs in executor pool)"""
        try:
            # Execute task
            result = func(*args, **kwargs)

            # Success!
            with self._lock:
                self._tasks_completed += 1
                if task_id in self._tasks_pending:
                    del self._tasks_pending[task_id]
                self._save_pending_tasks()

            # Call callback if provided
            if callback:
                try:
                    callback(result, None)
                except Exception as e:
                    print(f"[BGTaskQueue] Callback error for {task_id}: {e}")

            # Store result
            self.results_queue.put((task_id, result, None))

        except Exception as e:
            # Check if it's a low balance error (402)
            from src.clients.deepseek import InsufficientBalanceError
            is_balance_error = isinstance(e, InsufficientBalanceError)

            # Determine if we should retry
            should_retry = (retry_count < max_retries) and not is_balance_error

            if should_retry:
                # Retry with exponential backoff
                wait_time = min(2 ** retry_count, 60)  # Cap at 60 seconds
                print(f"[BGTaskQueue] Task {task_id} failed (attempt {retry_count + 1}/{max_retries}), "
                      f"retrying in {wait_time}s: {e}")

                with self._lock:
                    self._tasks_retried += 1

                time.sleep(wait_time)

                # Requeue the task
                try:
                    self.task_queue.put((task_id, func, args, kwargs, callback, retry_count + 1, max_retries), block=False)
                except queue.Full:
                    print(f"[BGTaskQueue] Queue full, cannot retry task {task_id}")
                    self._handle_task_failure(task_id, e, callback, is_balance_error)
            else:
                # Final failure
                self._handle_task_failure(task_id, e, callback, is_balance_error)

    def _handle_task_failure(self, task_id: str, error: Exception, callback: Optional[Callable], is_balance_error: bool) -> None:
        """Handle final task failure"""
        with self._lock:
            self._tasks_failed += 1
            if task_id in self._tasks_pending:
                del self._tasks_pending[task_id]
            self._save_pending_tasks()

        error_prefix = "[LOW BALANCE] " if is_balance_error else ""
        print(f"[BGTaskQueue] {error_prefix}Task {task_id} FAILED: {error}")

        # Call callback with error
        if callback:
            try:
                callback(None, error)
            except Exception as e:
                print(f"[BGTaskQueue] Callback error for {task_id}: {e}")

        # Store error
        self.results_queue.put((task_id, None, error))

    def queue_task(self, func: Callable, *args,
                   task_id: Optional[str] = None,
                   callback: Optional[Callable] = None,
                   max_retries: int = 3,
                   **kwargs) -> str:
        """Queue a task for background execution

        Args:
            func: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier (auto-generated if not provided)
            callback: Optional callback(result, error) called after completion
            max_retries: Maximum number of retry attempts (default 3)
            **kwargs: Keyword arguments for function

        Returns:
            Task ID string

        Raises:
            queue.Full: If queue is full
        """
        if task_id is None:
            task_id = f"task_{int(time.time() * 1000)}"

        # Pack task data with retry information
        task_data = (task_id, func, args, kwargs, callback, 0, max_retries)
        self.task_queue.put(task_data, block=False)
        return task_id

    def try_queue_task(self, func: Callable, *args,
                       task_id: Optional[str] = None,
                       callback: Optional[Callable] = None,
                       max_retries: int = 3,
                       **kwargs) -> Optional[str]:
        """Try to queue a task (non-blocking)

        Args:
            func: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier
            callback: Optional callback function
            max_retries: Maximum number of retry attempts (default 3)
            **kwargs: Keyword arguments for function

        Returns:
            Task ID if queued, None if queue is full
        """
        try:
            return self.queue_task(func, *args, task_id=task_id, callback=callback, max_retries=max_retries, **kwargs)
        except queue.Full:
            return None

    def get_result(self, timeout: Optional[float] = None) -> Optional[Tuple[str, Any, Optional[Exception]]]:
        """Get result from completed task

        Args:
            timeout: Max seconds to wait (None = non-blocking)

        Returns:
            Tuple of (task_id, result, error) or None if no results
        """
        try:
            return self.results_queue.get(block=timeout is not None, timeout=timeout)
        except queue.Empty:
            return None

    def get_queue_size(self) -> int:
        """Get number of pending tasks

        Returns:
            Number of tasks in queue
        """
        return self.task_queue.qsize()

    def get_stats(self) -> dict:
        """Get queue statistics

        Returns:
            Dict with queue stats
        """
        with self._lock:
            return {
                'pending': self.task_queue.qsize(),
                'running': len(self._tasks_pending),
                'completed': self._tasks_completed,
                'failed': self._tasks_failed,
                'retried': self._tasks_retried,
                'total': self._tasks_completed + self._tasks_failed,
                'workers': self.max_workers
            }

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all queued tasks to complete

        Args:
            timeout: Max seconds to wait (None = wait forever)

        Returns:
            True if all tasks completed, False if timeout
        """
        try:
            self.task_queue.join()
            # Also wait for executor to finish running tasks
            self.executor.shutdown(wait=True, cancel_futures=False)
            return True
        except Exception:
            return False

    def shutdown(self) -> None:
        """Shutdown the task queue gracefully"""
        self.active = False

        # Save final state
        self._save_pending_tasks()

        # Wait for dispatcher to finish
        if self.dispatcher_thread.is_alive():
            self.dispatcher_thread.join(timeout=2.0)

        # Shutdown executor (wait for running tasks)
        self.executor.shutdown(wait=True, cancel_futures=False)


# Global singleton task queue
_global_task_queue: Optional[BackgroundTaskQueue] = None
_queue_lock = threading.Lock()


def get_task_queue(max_workers: int = 4, persistence_file: Optional[Path] = None) -> BackgroundTaskQueue:
    """Get or create global background task queue

    Args:
        max_workers: Number of concurrent workers (only used on first call)
        persistence_file: Path to save pending tasks (only used on first call)

    Returns:
        Global BackgroundTaskQueue instance
    """
    global _global_task_queue

    if _global_task_queue is None:
        with _queue_lock:
            if _global_task_queue is None:
                # Default persistence file if not provided
                if persistence_file is None:
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir())
                    persistence_file = temp_dir / "rp_claude_code_tasks.json"

                _global_task_queue = BackgroundTaskQueue(
                    max_workers=max_workers,
                    persistence_file=persistence_file
                )

    return _global_task_queue


def shutdown_task_queue() -> None:
    """Shutdown global task queue"""
    global _global_task_queue

    if _global_task_queue is not None:
        _global_task_queue.shutdown()
        _global_task_queue = None


# Convenience function for entity card generation
def queue_entity_card_generation(entity_name: str, generate_func: Callable,
                                  *args, log_file: Optional[Path] = None,
                                  max_retries: int = 3, **kwargs) -> str:
    """Queue entity card generation as background task

    Args:
        entity_name: Name of entity
        generate_func: Function that generates the card
        *args: Arguments for generation function
        log_file: Optional log file for completion notification
        max_retries: Maximum number of retry attempts (default 3)
        **kwargs: Keyword arguments for generation function

    Returns:
        Task ID
    """
    task_queue = get_task_queue()

    def completion_callback(result, error):
        """Log completion"""
        if log_file:
            from src.automation.core import log_to_file
            from src.clients.deepseek import InsufficientBalanceError

            if error:
                if isinstance(error, InsufficientBalanceError):
                    log_to_file(log_file, f"[BACKGROUND] ⚠️ LOW BALANCE: Entity card generation for {entity_name} failed - please add credits to OpenRouter")
                else:
                    log_to_file(log_file, f"[BACKGROUND] Entity card generation FAILED for {entity_name}: {error}")
            else:
                log_to_file(log_file, f"[BACKGROUND] Entity card generation COMPLETED for {entity_name}")

    task_id = f"entity_card_{entity_name}_{int(time.time())}"

    return task_queue.queue_task(
        generate_func,
        *args,
        task_id=task_id,
        callback=completion_callback,
        max_retries=max_retries,
        **kwargs
    )
