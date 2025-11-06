"""Facade around the filesystem write queue."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...shared.interfaces import LoggingService


class WriteQueueProtocol:
    """Subset of behaviours we rely on from the concrete write queue."""

    def write_text(self, file_path: Path, content: str, encoding: str = "utf-8") -> None: ...

    def write_json(
        self,
        file_path: Path,
        data: Any,
        encoding: str = "utf-8",
        indent: int = 2,
    ) -> None: ...

    def flush(self) -> None: ...

    def shutdown(self) -> None: ...


@dataclass(frozen=True)
class FileWriteQueue:
    """Thin wrapper that exposes higher-level operations used by services."""

    queue: WriteQueueProtocol
    logger: LoggingService

    def write_text(self, path: Path, content: str) -> None:
        self.logger.debug("file_write_queue.write_text", context={"path": str(path)})
        self.queue.write_text(path, content)

    def write_json(self, path: Path, data: Any) -> None:
        self.logger.debug("file_write_queue.write_json", context={"path": str(path)})
        self.queue.write_json(path, data)

    def flush(self) -> None:
        self.logger.debug("file_write_queue.flush")
        self.queue.flush()

    def shutdown(self) -> None:
        self.logger.debug("file_write_queue.shutdown")
        self.queue.shutdown()


def build_default_write_queue(logger: LoggingService, *, debounce_ms: int = 500) -> FileWriteQueue:
    """Factory that mirrors the legacy global write queue behaviour."""

    from src.fs_write_queue import get_write_queue  # type: ignore[import-not-found]

    queue = get_write_queue(debounce_ms=debounce_ms)
    return FileWriteQueue(queue=queue, logger=logger)
