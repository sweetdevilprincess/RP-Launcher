"""Filesystem-backed session repository."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...infrastructure.filesystem import JsonStore, StatePaths
from ...shared.interfaces import LoggingService
from .models import SessionCheckpoint, SessionData, SessionMessage


@dataclass
class SessionMetadata:
    """Lightweight session metadata (without loading full messages)."""

    session_id: str
    session_type: str
    created: str
    last_modified: str
    message_count: int
    parent_session: str | None
    branch_point: int | None
    description: str
    tags: list[str]
    file_path: Path


class SessionRepository:
    """Persist and retrieve session documents from the filesystem."""

    def __init__(
        self,
        *,
        paths: StatePaths,
        logger: LoggingService,
        session_state_service: Any | None = None,
    ) -> None:
        self._paths = paths
        self._logger = logger
        self._store = JsonStore(root=self._paths.sessions_dir, logger=logger)
        self._session_state_service = session_state_service
        self._ensure_directories()

    # ------------------------------------------------------------------
    # Core operations

    def ensure_active_session(
        self, *, rp_name: str = "Untitled RP", chapter: int = 1
    ) -> SessionData:
        """Return the active session, creating a default one if missing."""

        if not self.active_path.exists():
            session = SessionData.create_default(rp_name=rp_name, chapter=chapter)
            self.save_session(session)
            return session
        return self.load_active_session()

    def load_active_session(self) -> SessionData:
        """Load the active session document (main or current branch)."""

        active_path = self.active_path

        if active_path.parent == self._paths.session_branches_dir:
            # Branch session - use branches store
            branches_store = JsonStore(root=self._paths.session_branches_dir, logger=self._logger)
            data = branches_store.read(Path(active_path.name))
        else:
            # Main session - use default store
            data = self._store.read(self._active_relative_path())

        session = SessionData.from_dict(data)
        session.validate()
        return session

    def save_session(self, session: SessionData) -> None:
        """Persist the provided session, enforcing invariants."""

        session.sync_response_count()
        session.touch()
        session.validate()

        # Determine which store to use based on session type
        active_path = self.active_path

        if active_path.parent == self._paths.session_branches_dir:
            # Branch session - use branches store
            branches_store = JsonStore(root=self._paths.session_branches_dir, logger=self._logger)
            branches_store.write(Path(active_path.name), session.to_dict())
        else:
            # Main session - use default store
            self._store.write(self._active_relative_path(), session.to_dict())

    def append_message(self, message: SessionMessage) -> SessionData:
        """Append a message to the active session and return the updated document."""

        session = self.ensure_active_session()
        sequence = len(session.messages) + 1
        message.response_num = sequence
        session.messages.append(message)
        self.save_session(session)
        return session

    # ------------------------------------------------------------------
    # Session discovery and metadata

    def list_sessions(
        self, *, archived: bool = False, include_branches: bool = False
    ) -> list[SessionMetadata]:
        """List all sessions with metadata (lightweight, doesn't load messages).

        Args:
            archived: If True, return archived sessions; if False, return active sessions
            include_branches: If True, also include branch sessions

        Returns:
            List of SessionMetadata objects sorted by last_modified (newest first)
        """
        sessions = []

        # Collect active or archived sessions
        target_dir = self._paths.session_archived_dir if archived else self._paths.sessions_dir

        if target_dir.exists():
            for session_file in target_dir.glob("session_*.json"):
                try:
                    metadata = self._load_session_metadata(session_file)
                    sessions.append(metadata)
                except Exception as exc:
                    self._logger.warning(
                        "session_repository.metadata_load_failed",
                        context={"file": str(session_file), "error": str(exc)},
                    )

        # Optionally include branches
        if include_branches:
            branches_dir = self._paths.session_branches_dir
            if branches_dir.exists():
                for branch_file in branches_dir.glob("session_*.json"):
                    try:
                        metadata = self._load_session_metadata(branch_file)
                        sessions.append(metadata)
                    except Exception as exc:
                        self._logger.warning(
                            "session_repository.branch_metadata_load_failed",
                            context={"file": str(branch_file), "error": str(exc)},
                        )

        # Sort by last_modified (newest first)
        sessions.sort(key=lambda s: s.last_modified, reverse=True)
        return sessions

    def get_session_metadata(self, session_id: str) -> SessionMetadata | None:
        """Get metadata for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            SessionMetadata or None if not found
        """
        # Check active sessions
        session_file = self._paths.sessions_dir / f"session_{session_id}.json"
        if session_file.exists():
            return self._load_session_metadata(session_file)

        # Check archived sessions
        archived_file = self._paths.session_archived_dir / f"session_{session_id}.json"
        if archived_file.exists():
            return self._load_session_metadata(archived_file)

        # Check branches
        branches_dir = self._paths.session_branches_dir
        if branches_dir.exists():
            for branch_file in branches_dir.glob(f"session_{session_id}*.json"):
                if branch_file.exists():
                    return self._load_session_metadata(branch_file)

        return None

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists (active, archived, or branch).

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        return self.get_session_metadata(session_id) is not None

    def _load_session_metadata(self, file_path: Path) -> SessionMetadata:
        """Load lightweight metadata without loading all messages.

        Args:
            file_path: Path to session JSON file

        Returns:
            SessionMetadata object
        """
        # For now, we need to load the full session to extract metadata
        # Future optimization: store metadata separately
        data = self._store.read(
            Path(file_path.name) if file_path.parent == self._paths.sessions_dir else file_path
        )
        session = SessionData.from_dict(data)

        return SessionMetadata(
            session_id=session.session_id,
            session_type=session.session_type,
            created=session.created,
            last_modified=session.last_modified,
            message_count=len(session.messages),
            parent_session=session.parent_session,
            branch_point=session.branch_point,
            description=session.description,
            tags=session.tags,
            file_path=file_path,
        )

    # ------------------------------------------------------------------
    # Branching operations

    def create_branch(
        self,
        *,
        source_session_id: str = "main",
        branch_name: str,
        branch_point: int | None = None,
        description: str = "",
    ) -> SessionData:
        """Create a new branch from an existing session.

        Args:
            source_session_id: Session to branch from (defaults to main)
            branch_name: Name for the new branch
            branch_point: Message index to branch from (None = latest)
            description: Optional description for the branch

        Returns:
            New branched SessionData

        Raises:
            FileNotFoundError: If source session doesn't exist
            ValueError: If branch_point is invalid
        """
        # Load source session
        source_file = self._paths.sessions_dir / f"session_{source_session_id}.json"
        if not source_file.exists():
            # Check archived sessions
            source_file = self._paths.session_archived_dir / f"session_{source_session_id}.json"
            if not source_file.exists():
                raise FileNotFoundError(f"Source session '{source_session_id}' not found")

        source_data = self._store.read(
            Path(source_file.name)
            if source_file.parent == self._paths.sessions_dir
            else source_file
        )
        source_session = SessionData.from_dict(source_data)

        # Validate branch point
        if branch_point is None:
            branch_point = len(source_session.messages)
        elif branch_point < 0 or branch_point > len(source_session.messages):
            raise ValueError(
                f"Invalid branch_point {branch_point}, must be 0-{len(source_session.messages)}"
            )

        # Create branch session
        from datetime import UTC, datetime
        import uuid

        now_iso = datetime.now(tz=UTC).isoformat()

        # Generate unique branch ID (not using user's name in ID)
        branch_id = f"br_{uuid.uuid4().hex[:12]}"

        # Copy rp_metadata and add branch title
        branch_metadata = source_session.rp_metadata.copy()
        branch_metadata["branch_title"] = branch_name  # Store user's name as title

        branch_session = SessionData(
            session_id=branch_id,
            session_type="branch",
            parent_session=source_session_id,
            branch_point=branch_point,
            created=now_iso,
            last_modified=now_iso,
            current_response=branch_point,
            tags=[f"branch-{branch_name}", *source_session.tags],
            description=description or f"Branch from {source_session_id} at message {branch_point}",
            rp_metadata=branch_metadata,
            messages=source_session.messages[:branch_point],
        )

        # Save to branches directory
        branch_file = self._paths.session_branches_dir / f"session_{branch_id}.json"
        self._store.write(branch_file, branch_session.to_dict())

        # Update centralized state file to switch to new branch
        if self._session_state_service:
            self._session_state_service.switch_timeline(
                self._paths.rp_dir,
                branch_id,
                parent_session=source_session_id,
                branch_point=branch_point,
            )

        self._logger.info(
            "session_repository.branch_created",
            context={
                "branch_id": branch_id,
                "source": source_session_id,
                "branch_point": branch_point,
            },
        )

        return branch_session

    def list_branches(self, base_session_id: str | None = None) -> list[SessionMetadata]:
        """List all branch sessions, optionally filtered by parent.

        Args:
            base_session_id: If specified, only return branches of this session

        Returns:
            List of SessionMetadata for branch sessions
        """
        branches = []
        branches_dir = self._paths.session_branches_dir

        if not branches_dir.exists():
            return []

        for branch_file in branches_dir.glob("session_*.json"):
            try:
                metadata = self._load_session_metadata(branch_file)
                if base_session_id is None or metadata.parent_session == base_session_id:
                    branches.append(metadata)
            except Exception as exc:
                self._logger.warning(
                    "session_repository.branch_list_failed",
                    context={"file": str(branch_file), "error": str(exc)},
                )

        return sorted(branches, key=lambda b: b.created, reverse=True)

    # ------------------------------------------------------------------
    # Archival operations

    def archive_session(self, session_id: str) -> None:
        """Move a session to the archived directory.

        Args:
            session_id: Session to archive

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If trying to archive the main session
        """
        if session_id == "main":
            raise ValueError("Cannot archive the main session")

        # Check active sessions first
        source_file = self._paths.sessions_dir / f"session_{session_id}.json"
        if not source_file.exists():
            # Check branches directory
            source_file = self._paths.session_branches_dir / f"session_{session_id}.json"
            if not source_file.exists():
                raise FileNotFoundError(
                    f"Session '{session_id}' not found in active sessions or branches"
                )

        # Move to archived directory
        target_file = self._paths.session_archived_dir / source_file.name
        shutil.move(str(source_file), str(target_file))

        self._logger.info(
            "session_repository.archived",
            context={"session_id": session_id, "target": str(target_file)},
        )

    def unarchive_session(self, session_id: str) -> None:
        """Move an archived session back to active sessions.

        Args:
            session_id: Session to unarchive

        Raises:
            FileNotFoundError: If archived session doesn't exist
        """
        source_file = self._paths.session_archived_dir / f"session_{session_id}.json"
        if not source_file.exists():
            raise FileNotFoundError(f"Archived session '{session_id}' not found")

        # Move back to active sessions
        target_file = self._paths.sessions_dir / source_file.name
        shutil.move(str(source_file), str(target_file))

        self._logger.info(
            "session_repository.unarchived",
            context={"session_id": session_id, "target": str(target_file)},
        )

    def delete_session(self, session_id: str, *, permanent: bool = False) -> None:
        """Delete a session (archives by default, permanently deletes if specified).

        Args:
            session_id: Session to delete
            permanent: If True, permanently delete; if False, archive instead

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If trying to delete the main session
        """
        if session_id == "main":
            raise ValueError("Cannot delete the main session")

        if permanent:
            # Permanently delete from any location
            locations = [
                self._paths.sessions_dir / f"session_{session_id}.json",
                self._paths.session_archived_dir / f"session_{session_id}.json",
                self._paths.session_branches_dir / f"session_{session_id}.json",
            ]

            deleted = False
            for file_path in locations:
                if file_path.exists():
                    file_path.unlink()
                    deleted = True
                    self._logger.warning(
                        "session_repository.deleted_permanent",
                        context={"session_id": session_id, "path": str(file_path)},
                    )

            if not deleted:
                raise FileNotFoundError(f"Session '{session_id}' not found")
        else:
            # Archive instead of delete
            self.archive_session(session_id)

    # ------------------------------------------------------------------
    # Checkpoint management

    def create_checkpoint(
        self,
        session_id: str,
        message_index: int,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> SessionCheckpoint:
        """Create a checkpoint at a specific message index.

        Args:
            session_id: Session to checkpoint
            message_index: Message index to checkpoint at
            description: Human-readable description
            metadata: Optional additional metadata

        Returns:
            Created SessionCheckpoint

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If message_index is invalid
        """
        # Load session (check active first, then archived)
        session_file = self._paths.sessions_dir / f"session_{session_id}.json"
        if not session_file.exists():
            session_file = self._paths.session_archived_dir / f"session_{session_id}.json"
            if not session_file.exists():
                raise FileNotFoundError(f"Session '{session_id}' not found")

        session_data = self._store.read(
            Path(session_file.name)
            if session_file.parent == self._paths.sessions_dir
            else session_file
        )
        session = SessionData.from_dict(session_data)

        # Validate message index
        if message_index < 0 or message_index > len(session.messages):
            raise ValueError(
                f"Invalid message_index {message_index}, must be 0-{len(session.messages)}"
            )

        # Create checkpoint
        checkpoint = SessionCheckpoint.create(
            message_index=message_index,
            description=description,
            metadata=metadata,
        )

        # Add to session
        session.checkpoints.append(checkpoint)
        session.touch()

        # Save session
        self._store.write(
            (
                Path(session_file.name)
                if session_file.parent == self._paths.sessions_dir
                else session_file
            ),
            session.to_dict(),
        )

        self._logger.info(
            "session_repository.checkpoint_created",
            context={
                "session_id": session_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "message_index": message_index,
            },
        )

        return checkpoint

    def restore_checkpoint(self, session_id: str, checkpoint_id: str) -> SessionData:
        """Restore a session to a specific checkpoint (creates a branch).

        This doesn't modify the original session, but creates a branch from the checkpoint.

        Args:
            session_id: Session containing the checkpoint
            checkpoint_id: Checkpoint to restore to

        Returns:
            New branched SessionData at the checkpoint

        Raises:
            FileNotFoundError: If session doesn't exist
            ValueError: If checkpoint doesn't exist
        """
        # Load session
        session_file = self._paths.sessions_dir / f"session_{session_id}.json"
        if not session_file.exists():
            session_file = self._paths.session_archived_dir / f"session_{session_id}.json"
            if not session_file.exists():
                raise FileNotFoundError(f"Session '{session_id}' not found")

        session_data = self._store.read(
            Path(session_file.name)
            if session_file.parent == self._paths.sessions_dir
            else session_file
        )
        session = SessionData.from_dict(session_data)

        # Find checkpoint
        checkpoint = next(
            (cp for cp in session.checkpoints if cp.checkpoint_id == checkpoint_id), None
        )
        if checkpoint is None:
            raise ValueError(f"Checkpoint '{checkpoint_id}' not found in session '{session_id}'")

        # Create branch from checkpoint with unique name (add timestamp for uniqueness)
        from datetime import UTC, datetime

        timestamp_suffix = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S_%f")[
            :20
        ]  # Truncate microseconds
        branch_name = f"restore_{checkpoint_id}_{timestamp_suffix}"
        branch = self.create_branch(
            source_session_id=session_id,
            branch_name=branch_name,
            branch_point=checkpoint.message_index,
            description=f"Restored from checkpoint: {checkpoint.description}",
        )

        self._logger.info(
            "session_repository.checkpoint_restored",
            context={
                "session_id": session_id,
                "checkpoint_id": checkpoint_id,
                "branch_id": branch.session_id,
            },
        )

        return branch

    def list_checkpoints(self, session_id: str) -> list[SessionCheckpoint]:
        """List all checkpoints in a session.

        Args:
            session_id: Session to list checkpoints for

        Returns:
            List of SessionCheckpoint objects (sorted by message_index)

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        # Load session
        session_file = self._paths.sessions_dir / f"session_{session_id}.json"
        if not session_file.exists():
            session_file = self._paths.session_archived_dir / f"session_{session_id}.json"
            if not session_file.exists():
                raise FileNotFoundError(f"Session '{session_id}' not found")

        session_data = self._store.read(
            Path(session_file.name)
            if session_file.parent == self._paths.sessions_dir
            else session_file
        )
        session = SessionData.from_dict(session_data)

        # Return checkpoints sorted by message_index
        return sorted(session.checkpoints, key=lambda cp: cp.message_index)

    # ------------------------------------------------------------------
    # Discovery helpers

    def list_archived_sessions(self) -> list[Path]:
        archived = self._paths.session_archived_dir
        if not archived.exists():
            return []
        return sorted(path for path in archived.glob("*.json"))

    def iter_branch_sessions(self) -> Iterable[Path]:
        branches = self._paths.session_branches_dir
        if not branches.exists():
            return []
        return sorted(path for path in branches.glob("session_*.json"))

    # ------------------------------------------------------------------

    @property
    def active_path(self) -> Path:
        """Get path to currently active session (may be main or branch).

        Checks SessionStateService to determine which timeline is active.
        """
        # Check if we're on a branch
        if self._session_state_service:
            try:
                state = self._session_state_service.load_session_state(self._paths.rp_dir)
                timeline = state.get("timeline", {})
                current_session_id = timeline.get("current_session_id", "main")

                # If on a branch, return branch file path
                if current_session_id != "main":
                    branch_file = self._paths.session_branches_dir / f"session_{current_session_id}.json"
                    if branch_file.exists():
                        return branch_file
            except Exception:
                # If we can't determine the current session, fall back to main
                pass

        # Default to main session
        return self._paths.active_session_file()

    def _active_relative_path(self) -> Path:
        """Get relative path for active session."""
        active = self.active_path

        # If it's in branches directory, return relative to branches
        if active.parent == self._paths.session_branches_dir:
            return Path(active.name)

        # Otherwise relative to sessions directory
        return Path(active.name)

    def _ensure_directories(self) -> None:
        self._paths.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._paths.session_branches_dir.mkdir(parents=True, exist_ok=True)
        self._paths.session_archived_dir.mkdir(parents=True, exist_ok=True)
