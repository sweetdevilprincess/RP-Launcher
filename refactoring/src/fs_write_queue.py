"""Simple synchronous write queue implementation for testing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SimpleWriteQueue:
    """Simple synchronous write queue implementation.

    This is a minimal implementation for testing. In production,
    this would be replaced with a more sophisticated async/debounced queue.
    """

    def __init__(self, debounce_ms: int = 500):
        """Initialize write queue.

        Args:
            debounce_ms: Debounce delay in milliseconds (not used in sync implementation)
        """
        self.debounce_ms = debounce_ms

    def write_text(self, file_path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text to file synchronously.

        Args:
            file_path: Path to file
            content: Text content to write
            encoding: Text encoding
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)

    def write_json(
        self,
        file_path: Path,
        data: Any,
        encoding: str = "utf-8",
        indent: int = 2,
    ) -> None:
        """Write JSON to file synchronously.

        Args:
            file_path: Path to file
            data: Data to serialize to JSON
            encoding: Text encoding
            indent: JSON indentation
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        file_path.write_text(content, encoding=encoding)

    def flush(self) -> None:
        """Flush pending writes (no-op for synchronous implementation)."""
        pass

    def shutdown(self) -> None:
        """Shutdown the write queue (no-op for synchronous implementation)."""
        pass


# Global instance
_write_queue: SimpleWriteQueue | None = None


def get_write_queue(debounce_ms: int = 500) -> SimpleWriteQueue:
    """Get or create the global write queue instance.

    Args:
        debounce_ms: Debounce delay in milliseconds

    Returns:
        Global write queue instance
    """
    global _write_queue
    if _write_queue is None:
        _write_queue = SimpleWriteQueue(debounce_ms=debounce_ms)
    return _write_queue
