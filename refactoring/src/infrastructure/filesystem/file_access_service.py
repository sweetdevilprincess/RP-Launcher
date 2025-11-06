"""High-level filesystem facade composing manager and tiered loader."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ...shared.interfaces import LoggingService
from ..ipc import IpcChannel, IpcResponsePayload
from .author_notes_loader import AuthorNotesData, AuthorNotesLoader
from .file_manager import FileManager
from .loaders.tiered_loader import TieredFileLoader, TieredLoadResult


@dataclass
class TieredContext:
    """Aggregated tier bundle results."""

    tier1: dict[str, TieredLoadResult]
    tier2: dict[str, TieredLoadResult]
    tier3: dict[str, TieredLoadResult]
    tier3_referenced: dict[str, TieredLoadResult]  # Referenced entities (basics only)
    author_notes: AuthorNotesData | None = None  # Author's Notes (highest priority)


class FileAccessService:
    """Coordinates complex filesystem workflows using lower-level helpers."""

    def __init__(
        self,
        *,
        file_manager: FileManager,
        tier_loader: TieredFileLoader,
        logger: LoggingService,
        ipc_channel: IpcChannel | None = None,
        rp_dir: Path | None = None,
    ) -> None:
        self._file_manager = file_manager
        self._tier_loader = tier_loader
        self._logger = logger
        self._rp_dir = rp_dir
        self._ipc_channel = ipc_channel or IpcChannel(
            file_manager=file_manager,
            logger=logger,
        )
        # Initialize author notes loader (lazy - only if rp_dir is provided)
        self._author_notes_loader: AuthorNotesLoader | None = None
        if rp_dir:
            self._author_notes_loader = AuthorNotesLoader(rp_dir, logger)

    # ------------------------------------------------------------------
    # Tiered loading

    def load_tiered_context(
        self,
        *,
        response_count: int | None,
        triggered_files: Sequence[Path] | None = None,
        tier3_referenced_files: Sequence[Path] | None = None,
    ) -> TieredContext:
        """Return tiered bundle results split by tier.

        Args:
            response_count: Current response number (for tier2 periodic loading)
            triggered_files: In-scene entity files (full cards)
            tier3_referenced_files: Referenced entity files (basics only)

        Returns:
            TieredContext with all tier bundles loaded
        """
        triggered_files = list(triggered_files or [])
        tier3_referenced_files = list(tier3_referenced_files or [])

        self._logger.debug(
            "file_access.tiers.start",
            context={
                "response_count": response_count,
                "triggered_count": len(triggered_files),
                "referenced_count": len(tier3_referenced_files),
            },
        )

        # Load author notes (highest priority)
        author_notes = None
        if self._author_notes_loader:
            author_notes = self._author_notes_loader.load()

        tier1 = self._tier_loader.load_tier1()
        tier2 = (
            self._tier_loader.load_tier2(response_count=response_count or 0)
            if response_count is not None
            else {}
        )
        tier3 = self._tier_loader.load_tier3(triggered_files=triggered_files)
        tier3_referenced = self._tier_loader.load_tier3_referenced(
            triggered_files=tier3_referenced_files
        )

        self._logger.debug(
            "file_access.tiers.complete",
            context={
                "author_notes": bool(author_notes and author_notes.content),
                "active_genome": author_notes.active_genome_file if author_notes else None,
                "tier1": len(tier1),
                "tier2": len(tier2),
                "tier3": len(tier3),
                "tier3_referenced": len(tier3_referenced),
            },
        )

        return TieredContext(
            tier1=tier1,
            tier2=tier2,
            tier3=tier3,
            tier3_referenced=tier3_referenced,
            author_notes=author_notes,
        )

    def load_all_bundles(
        self,
        *,
        response_count: int | None,
        triggered_files: Sequence[Path] | None = None,
    ) -> dict[str, TieredLoadResult]:
        """Return all applicable bundles keyed by bundle id."""

        bundles = self._tier_loader.load_all(
            response_count=response_count,
            triggered_files=triggered_files,
        )
        self._logger.debug(
            "file_access.tiers.all",
            context={"bundle_count": len(bundles)},
        )
        return bundles

    # ------------------------------------------------------------------
    # Delegated utilities (thin pass-throughs for now)

    def increment_response_counter(self) -> int:
        return self._file_manager.increment_response_counter()

    def read_response_counter(self) -> int:
        return self._file_manager.read_response_counter()

    def ensure_ipc_migration(self) -> None:
        self._ipc_channel.read_input()

    # IPC wrappers -----------------------------------------------------

    def write_ipc_input(self, message: str) -> None:
        self._ipc_channel.write_input(message)

    def read_ipc_input(self) -> str | None:
        payload = self._ipc_channel.read_input()
        return payload.message if payload else None

    def write_ipc_response(
        self,
        response: str,
        *,
        model: str | None = None,
        cache_stats: dict | None = None,
    ) -> None:
        self._ipc_channel.write_response(
            response,
            model=model,
            cache_stats=cache_stats,
        )

    def read_ipc_response(self) -> IpcResponsePayload | None:
        return self._ipc_channel.read_response()

    def read_session_triggers(self) -> list[str]:
        return self._ipc_channel.read_session_triggers()

    def write_session_triggers(self, characters: Sequence[str]) -> None:
        self._ipc_channel.write_session_triggers(characters)

    def backup_file(self, relative_path: Path) -> Path:
        return self._file_manager.backup_file(relative_path)

    def queue_json(self, relative_path: Path, data: dict) -> None:
        self._file_manager.queue_json(relative_path, data)

    def queue_text(self, relative_path: Path, content: str) -> None:
        self._file_manager.queue_text(relative_path, content)
