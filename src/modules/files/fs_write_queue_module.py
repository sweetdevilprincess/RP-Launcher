"""
Filesystem Write Queue Module

Wraps FSWriteQueue for the module management system.
Handles debounced filesystem writes to reduce disk I/O.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from fs_write_queue import FSWriteQueue


class FSWriteQueueModule(RPModule):
    """Module wrapper for FSWriteQueue.

    Provides debounced filesystem writes with:
    - Per-file debounce timers
    - Automatic batching of rapid writes
    - Thread-safe operation
    - Graceful shutdown with flush

    Dependencies: file_manager (logical, for coordination)
    """

    # Module metadata
    name = "fs_write_queue"
    version = "1.0.0"
    description = "Debounced filesystem write queue to reduce disk I/O"
    dependencies: List[str] = ["file_manager"]  # Logical dependency for coordination
    optional = False  # Core module for write operations

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize FS write queue module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # Write queue instance (created during initialize)
        self.write_queue: Optional[FSWriteQueue] = None

        # Configuration
        self.debounce_ms = config.get('debounce_ms', 500)
        self.verbose = config.get('verbose', False)

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize FS write queue.

        Creates FSWriteQueue with debounce timers.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create write queue
            self.write_queue = FSWriteQueue(
                debounce_ms=self.debounce_ms,
                verbose=self.verbose
            )

            self.log_info(f"FS write queue initialized ({self.debounce_ms}ms debounce)")
            return True

        except Exception as e:
            self.log_error("Failed to initialize FS write queue", e)
            return False

    def start(self) -> bool:
        """Start FS write queue.

        Queue is already active (timers start on demand).

        Returns:
            True (always succeeds)
        """
        self.log_info("FS write queue started (passive module)")
        return True

    def stop(self) -> bool:
        """Stop FS write queue.

        Sets shutdown flag but doesn't flush yet.

        Returns:
            True if successful
        """
        if not self.write_queue:
            return True

        try:
            self.write_queue._shutdown = True
            self.log_info("FS write queue stopped (shutdown flag set)")
            return True

        except Exception as e:
            self.log_error("Failed to stop FS write queue", e)
            return False

    def cleanup(self) -> None:
        """Cleanup FS write queue.

        Flushes all pending writes.
        """
        if not self.write_queue:
            return

        try:
            pending_count = self.write_queue.get_pending_count()
            if pending_count > 0:
                self.log_info(f"Flushing {pending_count} pending writes...")

            self.write_queue.shutdown()
            self.log_info("FS write queue shutdown complete")

        except Exception as e:
            self.log_error("Error during FS write queue cleanup", e)

        finally:
            self.write_queue = None

    # ==================== Write Operations ====================

    def write_text(self, file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """Queue a text write operation.

        Args:
            file_path: Path to write to
            content: Text content to write
            encoding: Text encoding

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")

        self.write_queue.write_text(file_path, content, encoding)

    def write_json(self, file_path: Path, data: dict, encoding: str = 'utf-8', indent: int = 2) -> None:
        """Queue a JSON write operation.

        Args:
            file_path: Path to write to
            data: Dictionary to serialize as JSON
            encoding: Text encoding
            indent: JSON indentation

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")

        self.write_queue.write_json(file_path, data, encoding, indent)

    def flush(self) -> None:
        """Immediately flush all pending writes.

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")

        self.write_queue.flush()

    def get_pending_count(self) -> int:
        """Get number of pending writes.

        Returns:
            Number of files with pending writes

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")

        return self.write_queue.get_pending_count()

    def is_pending(self, file_path: Path) -> bool:
        """Check if a file has a pending write.

        Args:
            file_path: Path to check

        Returns:
            True if file has pending write

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")

        return self.write_queue.is_pending(file_path)

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle FS write queue commands.

        Commands:
            status - Show write queue status
            flush - Flush all pending writes
            pending - Show pending writes count

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"FS Write Queue v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")
            lines.append(f"Debounce: {self.debounce_ms}ms")

            # Add pending count if initialized
            if self.write_queue:
                pending = self.get_pending_count()
                lines.append(f"Pending writes: {pending}")

            return "\n".join(lines)

        elif command == "flush":
            try:
                if not self.write_queue:
                    return "FS write queue not initialized"

                pending_before = self.get_pending_count()
                self.flush()

                return f"✓ Flushed {pending_before} pending writes"

            except Exception as e:
                return f"Error flushing writes: {e}"

        elif command == "pending":
            try:
                if not self.write_queue:
                    return "FS write queue not initialized"

                pending = self.get_pending_count()
                return f"Pending writes: {pending}"

            except Exception as e:
                return f"Error getting pending count: {e}"

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
        status["debounce_ms"] = self.debounce_ms

        if self.write_queue:
            try:
                status["pending_writes"] = self.get_pending_count()
            except Exception:
                pass  # Ignore errors in status

        return status

    # ==================== Direct Access ====================

    def get_write_queue(self) -> FSWriteQueue:
        """Get the underlying FSWriteQueue instance.

        For legacy code that needs direct access.

        Returns:
            FSWriteQueue instance

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.write_queue:
            raise RuntimeError("FS write queue not initialized")
        return self.write_queue
