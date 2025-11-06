"""Integration-style snapshots for FileManager behaviours."""

from __future__ import annotations

import json
from pathlib import Path

from refactoring.src.infrastructure.filesystem.file_manager import FileManager
from refactoring.src.infrastructure.filesystem.json_store import JsonStore
from refactoring.src.infrastructure.filesystem.markdown_store import MarkdownStore
from refactoring.src.infrastructure.filesystem.state_paths import StatePaths
from refactoring.src.infrastructure.filesystem.write_queue import build_default_write_queue
from refactoring.src.shared.interfaces.logging_service import (
    LoggingService,  # type: ignore[attr-defined]
)


class StubLogger(LoggingService):
    def debug(self, message: str, *, context: dict[str, object] | None = None) -> None: ...

    def info(self, message: str, *, context: dict[str, object] | None = None) -> None: ...

    def warning(self, message: str, *, context: dict[str, object] | None = None) -> None: ...

    def error(self, message: str, *, context: dict[str, object] | None = None) -> None: ...

    def exception(
        self,
        message: str,
        *,
        context: dict[str, object] | None = None,
        exc: BaseException | None = None,
    ) -> None: ...


def _make_manager(tmp_path: Path) -> FileManager:
    paths = StatePaths(rp_dir=tmp_path)
    json_store = JsonStore(root=paths.state_dir, logger=StubLogger())
    markdown_store = MarkdownStore(root=paths.rp_dir, logger=StubLogger())
    write_queue = build_default_write_queue(logger=StubLogger(), debounce_ms=0)
    return FileManager(
        paths=paths,
        json_store=json_store,
        markdown_store=markdown_store,
        write_queue=write_queue,
        logger=StubLogger(),
    )


def test_response_counter_increment(tmp_path: Path) -> None:
    manager = _make_manager(tmp_path)
    count = manager.increment_response_counter()
    assert count == 1
    count = manager.increment_response_counter()
    assert count == 2
    stored = json.loads((tmp_path / "state" / "response_counter.json").read_text(encoding="utf-8"))
    assert stored["count"] == 2


def test_ipc_migration(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    legacy = state_dir / "rp_client_input.txt"
    legacy.write_text("Legacy message\n", encoding="utf-8")

    manager = _make_manager(tmp_path)
    manager.ensure_ipc_migration()

    payload = json.loads((state_dir / "rp_client_input.json").read_text(encoding="utf-8"))
    assert payload["message"] == "Legacy message"
    assert not legacy.exists()


def test_backup_file_suffix(tmp_path: Path) -> None:
    rp_file = tmp_path / "state" / "current_state.md"
    rp_file.parent.mkdir(parents=True, exist_ok=True)
    rp_file.write_text("content", encoding="utf-8")

    manager = _make_manager(tmp_path)
    backup_path = manager.backup_file(Path("state/current_state.md"))

    assert backup_path.exists()
    assert backup_path.name.startswith("current_state.")
    assert backup_path.read_text(encoding="utf-8") == "content"
