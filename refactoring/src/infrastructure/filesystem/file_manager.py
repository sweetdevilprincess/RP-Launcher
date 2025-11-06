"""Refactored FileManager leveraging JsonStore and MarkdownStore."""

from __future__ import annotations

import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ...shared.interfaces import LoggingService
from ..ipc import IpcChannel
from ..sessions import SessionStateService
from .json_store import JsonStore
from .markdown_store import MarkdownStore
from .state_paths import StatePaths
from .write_queue import FileWriteQueue


@dataclass
class FileManager:
    """Facade around filesystem helpers for RP automation."""

    paths: StatePaths
    json_store: JsonStore
    markdown_store: MarkdownStore
    write_queue: FileWriteQueue
    logger: LoggingService
    session_state_service: SessionStateService | None = None  # Optional: for response counter delegation

    # ------------------------------------------------------------------
    # JSON helpers

    def read_json(self, relative_path: Path, *, default: Any | None = None) -> Any:
        """Read JSON data relative to the JsonStore root."""

        return self.json_store.read(relative_path, default=default)

    def write_json(
        self,
        relative_path: Path,
        data: Any,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """Write JSON data through the JsonStore."""

        self.json_store.write(relative_path, data, indent=indent, ensure_ascii=ensure_ascii)

    def merge_json(
        self,
        relative_path: Path,
        updates: Mapping[str, Any],
        *,
        create_if_missing: bool = True,
    ) -> None:
        """Deep-merge updates into a stored JSON document."""

        self.json_store.merge(relative_path, updates, create_if_missing=create_if_missing)

    # ------------------------------------------------------------------
    # Markdown helpers

    def read_markdown(self, relative_path: Path) -> str | None:
        """Read markdown content relative to the MarkdownStore root."""

        return self.markdown_store.read(relative_path)

    def write_markdown(self, relative_path: Path, content: str) -> None:
        """Write markdown content."""

        self.markdown_store.write(relative_path, content)

    def append_markdown(self, relative_path: Path, content: str) -> None:
        """Append markdown content with newline handling."""

        self.markdown_store.append(relative_path, content)

    # ------------------------------------------------------------------
    # Counter operations

    def increment_response_counter(self) -> int:
        """Increment the response counter.

        Delegates to SessionStateService if available (new behavior),
        otherwise falls back to legacy response_counter.json (deprecated).
        """
        if self.session_state_service:
            return self.session_state_service.increment_response_count(self.paths.rp_dir)

        # Legacy fallback (deprecated - will be removed after migration)
        counter_path = Path("response_counter.json")
        data = self.json_store.read(counter_path, default={"count": 0})
        count = int(data.get("count", 0)) + 1
        self.json_store.write(counter_path, {"count": count})
        return count

    def read_response_counter(self) -> int:
        """Read current response counter.

        Delegates to SessionStateService if available (new behavior),
        otherwise falls back to legacy response_counter.json (deprecated).
        """
        if self.session_state_service:
            return self.session_state_service.get_response_count(self.paths.rp_dir)

        # Legacy fallback (deprecated - will be removed after migration)
        counter_path = Path("response_counter.json")
        data = self.json_store.read(counter_path, default={"count": 0})
        return int(data.get("count", 0))

    def write_response_counter(self, count: int) -> None:
        """Persist the response counter.

        Delegates to SessionStateService if available (new behavior),
        otherwise falls back to legacy response_counter.json (deprecated).
        """
        if self.session_state_service:
            # Load, update, and save via SessionStateService
            state = self.session_state_service.load_session_state(self.paths.rp_dir)
            if "rp_metadata" not in state:
                state["rp_metadata"] = {}
            state["rp_metadata"]["response_count"] = int(count)
            self.session_state_service.save_session_state(self.paths.rp_dir, state)
            return

        # Legacy fallback (deprecated - will be removed after migration)
        counter_path = Path("response_counter.json")
        self.json_store.write(counter_path, {"count": int(count)})

    # ------------------------------------------------------------------
    # IPC helpers

    def write_ipc_input(self, message: str) -> None:
        """Write IPC input payload in JSON format."""

        self._ipc_channel().write_input(message)

    def read_ipc_input(self) -> str | None:
        """Return the cached IPC input message if present."""

        payload = self._ipc_channel().read_input()
        return payload.message if payload else None

    def ensure_ipc_migration(self) -> None:
        """Migrate legacy text IPC input to JSON format if necessary."""

        _ = self._ipc_channel().read_input()

    def write_ipc_response(
        self,
        response: str,
        *,
        model: str | None = None,
        cache_stats: Mapping[str, Any] | None = None,
    ) -> None:
        """Persist the IPC response payload in JSON format."""

        self._ipc_channel().write_response(
            response,
            model=model,
            cache_stats=cache_stats,
        )

    def read_ipc_response(self) -> str | None:
        """Return the cached IPC response text, migrating legacy format if needed."""

        payload = self._ipc_channel().read_response()
        return payload.response if payload else None

    def read_session_triggers(self) -> list[str]:
        """Load active session triggers (character list) with legacy fallback."""

        return self._ipc_channel().read_session_triggers()

    def write_session_triggers(self, characters: Sequence[str]) -> None:
        """Persist active session triggers to JSON."""

        self._ipc_channel().write_session_triggers(characters)

    # ------------------------------------------------------------------
    # Write queue helpers

    def queue_json(self, relative_path: Path, data: Any) -> None:
        """Queue a JSON write via the write queue facade."""

        destination = self._resolve_relative(relative_path)
        self.write_queue.write_json(destination, data)

    def queue_text(self, relative_path: Path, content: str) -> None:
        """Queue a text write via the write queue facade."""

        destination = self._resolve_relative(relative_path)
        self.write_queue.write_text(destination, content)

    # ------------------------------------------------------------------
    # File metadata helpers

    def get_file_metadata(self, relative_path: Path) -> dict[str, Any]:
        """Return file metadata information."""

        target = self._resolve_relative(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")

        stat = target.stat()
        return {
            "path": str(target.relative_to(self.paths.rp_dir)),
            "absolute_path": str(target),
            "size_bytes": stat.st_size,
            "modified_timestamp": stat.st_mtime,
            "modified_datetime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": target.is_file(),
            "is_directory": target.is_dir(),
        }

    def has_file_changed(self, relative_path: Path, last_modified: float) -> bool:
        """Check whether a file has been modified since the given timestamp."""

        target = self._resolve_relative(relative_path)
        if not target.exists():
            return False
        return target.stat().st_mtime > last_modified

    def file_exists(self, relative_path: Path) -> bool:
        """Return True if the resolved path exists on disk."""

        return self._resolve_relative(relative_path).exists()

    def directory_exists(self, relative_dir: Path) -> bool:
        """Return True if the resolved directory exists."""

        return self._resolve_relative(relative_dir).is_dir()

    def list_files(
        self,
        relative_dir: Path,
        *,
        pattern: str = "*",
        recursive: bool = False,
    ) -> list[Path]:
        """List files under a relative directory using the provided pattern."""

        base_dir = self._resolve_relative(relative_dir)
        if not base_dir.exists():
            return []
        iterator = base_dir.rglob(pattern) if recursive else base_dir.glob(pattern)
        return sorted(path for path in iterator if path.is_file())

    # ------------------------------------------------------------------
    # Backup operations

    def backup_file(self, relative_path: Path) -> Path:
        """Create a timestamped backup of the given file under the backups directory."""

        source = self._resolve_relative(relative_path)
        if not source.exists():
            raise FileNotFoundError(f"Cannot backup missing file: {source}")

        backup_dir = self.paths.backups_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = self._current_timestamp(compact=True)
        backup_name = f"{source.stem}.{timestamp}{source.suffix}"
        destination = backup_dir / backup_name
        shutil.copy2(source, destination)
        self.logger.debug(
            "file_manager.backup",
            context={"source": str(source), "destination": str(destination)},
        )
        return destination

    # ------------------------------------------------------------------
    # Convenience path helpers

    def state_file(self, filename: str) -> Path:
        """Return a path within the state directory."""

        return self.paths.state_file(filename)

    def entity_file(self, entity_name: str) -> Path:
        """Return a path within the entities directory."""

        return self.paths.entities_dir / f"{entity_name}.md"

    def character_file(self, character_name: str) -> Path:
        return self.paths.character_file(character_name)

    def chapter_file(self, chapter_num: int) -> Path:
        return self.paths.chapter_file(chapter_num)

    def memory_file(self, character_name: str) -> Path:
        return self.paths.memory_file(character_name)

    def ensure_directory(self, relative_dir: Path) -> Path:
        """Ensure a directory exists relative to the RP root and return it."""

        directory = self._resolve_relative(relative_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    # ------------------------------------------------------------------

    def _ipc_channel(self) -> IpcChannel:
        """Return a lazily constructed IPC channel using this file manager."""

        return IpcChannel(file_manager=self, logger=self.logger)

    def _resolve_relative(self, relative_path: Path) -> Path:
        """Resolve a relative path against the RP directory with safeguards."""

        candidate = (self.paths.rp_dir / relative_path).resolve()
        root = self.paths.rp_dir.resolve()
        if not str(candidate).startswith(str(root)):
            raise ValueError("FileManager paths must stay within the RP directory")
        return candidate

    def _current_timestamp(self, *, compact: bool = False) -> str:
        fmt = "%Y%m%d%H%M%S" if compact else "%Y-%m-%dT%H:%M:%S"
        return datetime.now().strftime(fmt)

    # TODO: port remaining FileManager behaviours (tiered loading, directory snapshots, etc.)
