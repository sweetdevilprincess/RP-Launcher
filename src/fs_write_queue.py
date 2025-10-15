#!/usr/bin/env python3
"""
Filesystem Write Queue with Debouncing

Queues filesystem write operations and debounces them to reduce disk I/O.
Each file has its own debounce timer - writes are delayed until no new writes
for that file occur within the debounce period.

Features:
- Per-file debouncing (independent timers for each file)
- Automatic batching of rapid writes
- Thread-safe operation
- Graceful shutdown with pending write flush
- Support for both text and JSON writes
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class WriteType(Enum):
    """Type of write operation"""
    TEXT = "text"
    JSON = "json"


@dataclass
class WriteOperation:
    """Represents a pending write operation"""
    file_path: Path
    content: Any
    write_type: WriteType
    encoding: str
    json_indent: int
    timestamp: float  # Time when this write was queued


class FSWriteQueue:
    """Filesystem write queue with per-file debouncing

    Usage:
        # Create queue with 500ms debounce
        queue = FSWriteQueue(debounce_ms=500)

        # Queue writes (returns immediately)
        queue.write_text(Path("file.txt"), "content")
        queue.write_json(Path("data.json"), {"key": "value"})

        # Writes happen automatically after debounce period

        # Manual flush if needed
        queue.flush()

        # Clean shutdown
        queue.shutdown()
    """

    def __init__(self, debounce_ms: int = 500, verbose: bool = False):
        """Initialize write queue

        Args:
            debounce_ms: Milliseconds to wait after last write before flushing
            verbose: Print debug information
        """
        self.debounce_ms = debounce_ms
        self.verbose = verbose

        # Per-file pending writes
        self._pending: Dict[str, WriteOperation] = {}

        # Per-file debounce timers
        self._timers: Dict[str, threading.Timer] = {}

        # Lock for thread safety
        self._lock = threading.Lock()

        # Shutdown flag
        self._shutdown = False

        if self.verbose:
            print(f"[FSWriteQueue] Initialized with {debounce_ms}ms debounce")

    def write_text(self, file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """Queue a text write operation

        Args:
            file_path: Path to write to
            content: Text content to write
            encoding: Text encoding (default: utf-8)
        """
        self._queue_write(WriteOperation(
            file_path=file_path,
            content=content,
            write_type=WriteType.TEXT,
            encoding=encoding,
            json_indent=0,
            timestamp=time.time()
        ))

    def write_json(self, file_path: Path, data: dict, encoding: str = 'utf-8',
                   indent: int = 2) -> None:
        """Queue a JSON write operation

        Args:
            file_path: Path to write to
            data: Dictionary to serialize as JSON
            encoding: Text encoding (default: utf-8)
            indent: JSON indentation (default: 2)
        """
        self._queue_write(WriteOperation(
            file_path=file_path,
            content=data,
            write_type=WriteType.JSON,
            encoding=encoding,
            json_indent=indent,
            timestamp=time.time()
        ))

    def _queue_write(self, operation: WriteOperation) -> None:
        """Queue a write operation and start/reset debounce timer

        Args:
            operation: Write operation to queue
        """
        if self._shutdown:
            # If shutting down, write immediately
            self._execute_write(operation)
            return

        file_key = str(operation.file_path.resolve())

        with self._lock:
            # Cancel existing timer for this file
            if file_key in self._timers:
                self._timers[file_key].cancel()

            # Store/update pending operation
            self._pending[file_key] = operation

            if self.verbose:
                print(f"[FSWriteQueue] Queued write: {operation.file_path.name} "
                      f"({operation.write_type.value})")

            # Start new debounce timer
            timer = threading.Timer(
                self.debounce_ms / 1000.0,
                self._flush_file,
                args=(file_key,)
            )
            timer.daemon = True
            timer.start()
            self._timers[file_key] = timer

    def _flush_file(self, file_key: str) -> None:
        """Flush a specific file's pending write

        Args:
            file_key: Resolved file path string
        """
        with self._lock:
            if file_key not in self._pending:
                return

            operation = self._pending.pop(file_key)
            self._timers.pop(file_key, None)

        # Execute write outside lock
        self._execute_write(operation)

    def _execute_write(self, operation: WriteOperation) -> None:
        """Execute a write operation

        Args:
            operation: Write operation to execute
        """
        try:
            # Ensure parent directory exists
            operation.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Execute write based on type
            if operation.write_type == WriteType.TEXT:
                operation.file_path.write_text(
                    operation.content,
                    encoding=operation.encoding
                )
            elif operation.write_type == WriteType.JSON:
                operation.file_path.write_text(
                    json.dumps(operation.content, indent=operation.json_indent),
                    encoding=operation.encoding
                )

            if self.verbose:
                elapsed_ms = (time.time() - operation.timestamp) * 1000
                print(f"[FSWriteQueue] Wrote: {operation.file_path.name} "
                      f"(after {elapsed_ms:.0f}ms)")

        except Exception as e:
            print(f"[FSWriteQueue] ERROR writing {operation.file_path}: {e}")

    def flush(self) -> None:
        """Immediately flush all pending writes"""
        if self.verbose:
            print(f"[FSWriteQueue] Flushing {len(self._pending)} pending writes")

        with self._lock:
            # Cancel all timers
            for timer in self._timers.values():
                timer.cancel()

            # Get all pending operations
            operations = list(self._pending.values())

            # Clear pending and timers
            self._pending.clear()
            self._timers.clear()

        # Execute all writes outside lock
        for operation in operations:
            self._execute_write(operation)

    def shutdown(self) -> None:
        """Shutdown queue and flush all pending writes"""
        if self.verbose:
            print("[FSWriteQueue] Shutting down...")

        self._shutdown = True
        self.flush()

        if self.verbose:
            print("[FSWriteQueue] Shutdown complete")

    def get_pending_count(self) -> int:
        """Get number of pending writes

        Returns:
            Number of files with pending writes
        """
        with self._lock:
            return len(self._pending)

    def is_pending(self, file_path: Path) -> bool:
        """Check if a file has a pending write

        Args:
            file_path: Path to check

        Returns:
            True if file has pending write
        """
        file_key = str(file_path.resolve())
        with self._lock:
            return file_key in self._pending


# Global singleton instance
_global_queue: Optional[FSWriteQueue] = None
_global_queue_lock = threading.Lock()


def get_write_queue(debounce_ms: int = 500, verbose: bool = False) -> FSWriteQueue:
    """Get or create global write queue singleton

    Args:
        debounce_ms: Debounce period (only used on first call)
        verbose: Verbose logging (only used on first call)

    Returns:
        Global FSWriteQueue instance
    """
    global _global_queue

    if _global_queue is None:
        with _global_queue_lock:
            if _global_queue is None:
                _global_queue = FSWriteQueue(debounce_ms=debounce_ms, verbose=verbose)

    return _global_queue


def flush_all_writes() -> None:
    """Flush all pending writes in global queue"""
    if _global_queue is not None:
        _global_queue.flush()


def shutdown_write_queue() -> None:
    """Shutdown global write queue"""
    global _global_queue

    if _global_queue is not None:
        _global_queue.shutdown()
        _global_queue = None


# Context manager for automatic flush on exit
class WriteQueueContext:
    """Context manager for write queue with automatic flush

    Usage:
        with WriteQueueContext(debounce_ms=500) as queue:
            queue.write_text(Path("file.txt"), "content")
            # Automatic flush on exit
    """

    def __init__(self, debounce_ms: int = 500, verbose: bool = False):
        self.queue = FSWriteQueue(debounce_ms=debounce_ms, verbose=verbose)

    def __enter__(self) -> FSWriteQueue:
        return self.queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queue.shutdown()
        return False


if __name__ == "__main__":
    # Example usage and testing
    import tempfile

    print("Testing FSWriteQueue...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create queue with verbose output
        queue = FSWriteQueue(debounce_ms=200, verbose=True)

        # Test rapid text writes (should be batched)
        print("\n1. Testing text write batching:")
        test_file = tmppath / "test.txt"
        queue.write_text(test_file, "version 1")
        time.sleep(0.05)
        queue.write_text(test_file, "version 2")
        time.sleep(0.05)
        queue.write_text(test_file, "version 3")
        time.sleep(0.05)
        queue.write_text(test_file, "version 4 (final)")

        # Wait for debounce
        time.sleep(0.3)
        assert test_file.read_text() == "version 4 (final)"
        print(f"[OK] Final content: {test_file.read_text()}")

        # Test JSON writes
        print("\n2. Testing JSON write:")
        json_file = tmppath / "data.json"
        queue.write_json(json_file, {"test": "value", "count": 42})
        time.sleep(0.3)

        loaded_data = json.loads(json_file.read_text())
        assert loaded_data["test"] == "value"
        assert loaded_data["count"] == 42
        print(f"[OK] JSON content: {loaded_data}")

        # Test multiple files
        print("\n3. Testing multiple files:")
        file1 = tmppath / "file1.txt"
        file2 = tmppath / "file2.txt"
        queue.write_text(file1, "content 1")
        queue.write_text(file2, "content 2")
        time.sleep(0.3)

        assert file1.read_text() == "content 1"
        assert file2.read_text() == "content 2"
        print("[OK] Multiple files written correctly")

        # Test manual flush
        print("\n4. Testing manual flush:")
        file3 = tmppath / "file3.txt"
        queue.write_text(file3, "immediate")
        queue.flush()
        assert file3.read_text() == "immediate"
        print("[OK] Manual flush works")

        # Test shutdown
        print("\n5. Testing shutdown:")
        file4 = tmppath / "file4.txt"
        queue.write_text(file4, "shutdown test")
        queue.shutdown()
        assert file4.read_text() == "shutdown test"
        print("[OK] Shutdown flushes pending writes")

    print("\n[SUCCESS] All tests passed!")
