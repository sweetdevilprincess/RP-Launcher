"""
Background Task Queue Module

Wraps BackgroundTaskQueue for the module management system.
Handles async execution of long-running tasks with retry logic.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from automation.background_tasks import BackgroundTaskQueue


class BackgroundTaskQueueModule(RPModule):
    """Module wrapper for BackgroundTaskQueue.

    Provides background task execution with:
    - Concurrent worker pool
    - Automatic retry with exponential backoff
    - Task persistence
    - Graceful shutdown

    Dependencies: None
    """

    # Module metadata
    name = "background_task_queue"
    version = "1.0.0"
    description = "Background task queue with concurrent workers and retry logic"
    dependencies: List[str] = []  # No dependencies
    optional = False  # Core module for async operations

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize background task queue module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # Task queue instance (created during initialize)
        self.task_queue: Optional[BackgroundTaskQueue] = None

        # Configuration
        self.max_workers = config.get('max_workers', 4)
        self.max_queue_size = config.get('max_queue_size', 50)
        self.shutdown_timeout = config.get('shutdown_timeout', 60)

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize background task queue.

        Creates BackgroundTaskQueue with worker pool.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Set up persistence file
            persistence_file = self.rp_dir / "state" / "background_tasks.json"
            persistence_file.parent.mkdir(parents=True, exist_ok=True)

            # Create task queue
            self.task_queue = BackgroundTaskQueue(
                max_queue_size=self.max_queue_size,
                max_workers=self.max_workers,
                persistence_file=persistence_file
            )

            self.log_info(f"Background task queue initialized ({self.max_workers} workers)")
            return True

        except Exception as e:
            self.log_error("Failed to initialize background task queue", e)
            return False

    def start(self) -> bool:
        """Start background task queue.

        Queue is already running (dispatcher starts in __init__).

        Returns:
            True (always succeeds)
        """
        self.log_info("Background task queue started (workers active)")
        return True

    def stop(self) -> bool:
        """Stop background task queue.

        Stops accepting new tasks but doesn't wait for completion.

        Returns:
            True if successful
        """
        if not self.task_queue:
            return True

        try:
            self.task_queue.active = False
            self.log_info("Background task queue stopped (no new tasks accepted)")
            return True

        except Exception as e:
            self.log_error("Failed to stop background task queue", e)
            return False

    def cleanup(self) -> None:
        """Cleanup background task queue.

        Shuts down worker pool and waits for running tasks.
        """
        if not self.task_queue:
            return

        try:
            self.log_info(f"Shutting down background task queue (timeout: {self.shutdown_timeout}s)")
            self.task_queue.shutdown(timeout=self.shutdown_timeout)
            self.log_info("Background task queue shutdown complete")

        except Exception as e:
            self.log_error("Error during background task queue cleanup", e)

        finally:
            self.task_queue = None

    # ==================== Task Queue Operations ====================

    def queue_task(self, func: Callable, *args,
                   task_id: Optional[str] = None,
                   callback: Optional[Callable] = None,
                   max_retries: int = 3,
                   **kwargs) -> str:
        """Queue a task for background execution.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier
            callback: Optional callback(result, error)
            max_retries: Maximum retry attempts
            **kwargs: Keyword arguments for function

        Returns:
            Task ID string

        Raises:
            RuntimeError: If module not initialized
            queue.Full: If queue is full
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.queue_task(
            func, *args,
            task_id=task_id,
            callback=callback,
            max_retries=max_retries,
            **kwargs
        )

    def try_queue_task(self, func: Callable, *args,
                       task_id: Optional[str] = None,
                       callback: Optional[Callable] = None,
                       max_retries: int = 3,
                       **kwargs) -> Optional[str]:
        """Try to queue a task (non-blocking).

        Args:
            func: Function to execute
            *args: Positional arguments
            task_id: Optional task identifier
            callback: Optional callback function
            max_retries: Maximum retry attempts
            **kwargs: Keyword arguments

        Returns:
            Task ID if queued, None if queue is full

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.try_queue_task(
            func, *args,
            task_id=task_id,
            callback=callback,
            max_retries=max_retries,
            **kwargs
        )

    def get_result(self, timeout: Optional[float] = None) -> Optional[Tuple[str, Any, Optional[Exception]]]:
        """Get result from completed task.

        Args:
            timeout: Max seconds to wait (None = non-blocking)

        Returns:
            Tuple of (task_id, result, error) or None

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.get_result(timeout)

    def get_queue_size(self) -> int:
        """Get number of pending tasks.

        Returns:
            Number of tasks in queue

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.get_queue_size()

    def get_stats(self) -> Dict:
        """Get queue statistics.

        Returns:
            Dict with queue stats

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.get_stats()

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all queued tasks to complete.

        Args:
            timeout: Max seconds to wait

        Returns:
            True if all tasks completed, False if timeout

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        return self.task_queue.wait_for_completion(timeout)

    # ==================== Entity Card Generation (Convenience) ====================

    def queue_entity_card_generation(
        self,
        entity_name: str,
        generate_func: Callable,
        *args,
        log_file: Optional[Path] = None,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """Queue entity card generation as background task.

        Args:
            entity_name: Name of entity
            generate_func: Function that generates the card
            *args: Arguments for generation function
            log_file: Optional log file for completion notification
            max_retries: Maximum retry attempts
            **kwargs: Keyword arguments for generation function

        Returns:
            Task ID

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")

        import time

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

        return self.task_queue.queue_task(
            generate_func,
            *args,
            task_id=task_id,
            callback=completion_callback,
            max_retries=max_retries,
            **kwargs
        )

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle background task queue commands.

        Commands:
            status - Show queue status
            stats - Show detailed statistics

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"Background Task Queue v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")
            lines.append(f"Workers: {self.max_workers}")

            # Add queue stats if initialized
            if self.task_queue:
                stats = self.get_stats()
                lines.append(f"Pending: {stats['pending']}")
                lines.append(f"Running: {stats['running']}")

            return "\n".join(lines)

        elif command == "stats":
            try:
                if not self.task_queue:
                    return "Background task queue not initialized"

                stats = self.get_stats()
                lines = ["📊 Background Task Queue Statistics:"]
                lines.append(f"  Pending: {stats['pending']}")
                lines.append(f"  Running: {stats['running']}")
                lines.append(f"  Completed: {stats['completed']}")
                lines.append(f"  Failed: {stats['failed']}")
                lines.append(f"  Retried: {stats['retried']}")
                lines.append(f"  Total: {stats['total']}")
                lines.append(f"  Workers: {stats['workers']}")

                return "\n".join(lines)

            except Exception as e:
                return f"Error getting queue stats: {e}"

        # Default to parent handler
        return super().handle_command(command, args)

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status with queue-specific info.

        Returns:
            Status dictionary
        """
        status = super().get_status()

        # Add queue-specific info
        status["max_workers"] = self.max_workers
        status["max_queue_size"] = self.max_queue_size

        if self.task_queue:
            try:
                queue_stats = self.get_stats()
                status["queue_stats"] = queue_stats
            except Exception:
                pass  # Ignore errors in status

        return status

    # ==================== Direct Access ====================

    def get_task_queue(self) -> BackgroundTaskQueue:
        """Get the underlying BackgroundTaskQueue instance.

        For legacy code that needs direct access.

        Returns:
            BackgroundTaskQueue instance

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.task_queue:
            raise RuntimeError("Background task queue not initialized")
        return self.task_queue
