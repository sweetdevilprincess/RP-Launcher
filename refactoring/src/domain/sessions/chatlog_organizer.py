"""Chatlog Organizer - Organizes messages into chapter-based chatlog files.

This module creates chapter-grouped chatlog files from SessionData messages.
Chapter files provide easy navigation and export capabilities while the primary
storage remains in sessions/session_*.json files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...infrastructure.filesystem import StatePaths
from ...shared.interfaces import LoggingService
from .models import SessionData, SessionMessage
from .repository import SessionRepository


class ChatlogOrganizer:
    """Organizes session messages into chapter-based chatlog files.

    File Structure:
        sessions/chatlogs/{session_id}/
            chapter_1.json
            chapter_2.json
            chapter_3.json

    Each chapter file contains:
    - Chapter metadata (number, title, message range)
    - All messages from that chapter
    - Scene context snapshots for each message
    """

    def __init__(
        self,
        *,
        paths: StatePaths,
        logger: LoggingService,
        repository: SessionRepository,
    ) -> None:
        """Initialize chatlog organizer.

        Args:
            paths: File system paths
            logger: Logging service
            repository: Session repository for loading messages
        """
        self._paths = paths
        self._logger = logger
        self._repository = repository

    def update_chapter_file(
        self,
        session_id: str,
        chapter_number: int,
        chapter_title: str = ""
    ) -> None:
        """Update chapter file with latest messages from session.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number
            chapter_title: Optional chapter title

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        # Load session data
        session = self._load_session_by_id(session_id)

        # Filter messages for this chapter
        chapter_messages = [
            msg for msg in session.messages
            if msg.chapter == chapter_number
        ]

        if not chapter_messages:
            self._logger.debug(
                "chatlog_organizer.no_messages",
                context={"session_id": session_id, "chapter": chapter_number}
            )
            return

        # Build chapter file data
        chapter_data = {
            "session_id": session_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "start_message": chapter_messages[0].response_num,
            "end_message": chapter_messages[-1].response_num,
            "messages": [self._format_message(msg) for msg in chapter_messages]
        }

        # Write to file
        self._write_chapter_file(session_id, chapter_number, chapter_data)

        self._logger.info(
            "chatlog_organizer.chapter_updated",
            context={
                "session_id": session_id,
                "chapter": chapter_number,
                "message_count": len(chapter_messages)
            }
        )

    def append_message_to_chapter(
        self,
        session_id: str,
        message: SessionMessage
    ) -> None:
        """Append a single message to the appropriate chapter file.

        This is more efficient than rewriting the entire chapter file
        when adding individual messages.

        Args:
            session_id: Session identifier
            message: Message to append

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        chapter_number = message.chapter
        chapter_file = self._get_chapter_file_path(session_id, chapter_number)

        # Load existing chapter file or create new one
        if chapter_file.exists():
            chapter_data = self._read_chapter_file(session_id, chapter_number)
            chapter_data["end_message"] = message.response_num
            chapter_data["messages"].append(self._format_message(message))
        else:
            # New chapter file
            chapter_data = {
                "session_id": session_id,
                "chapter_number": chapter_number,
                "chapter_title": "",  # Will be set on chapter transition
                "start_message": message.response_num,
                "end_message": message.response_num,
                "messages": [self._format_message(message)]
            }

        # Write updated file
        self._write_chapter_file(session_id, chapter_number, chapter_data)

        self._logger.debug(
            "chatlog_organizer.message_appended",
            context={
                "session_id": session_id,
                "chapter": chapter_number,
                "message_num": message.response_num
            }
        )

    def finalize_chapter(
        self,
        session_id: str,
        chapter_number: int,
        chapter_title: str
    ) -> None:
        """Finalize a chapter by setting its title.

        Called when transitioning to a new chapter to name the completed chapter.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number to finalize
            chapter_title: Title for the chapter

        Raises:
            FileNotFoundError: If chapter file doesn't exist
        """
        chapter_file = self._get_chapter_file_path(session_id, chapter_number)

        if not chapter_file.exists():
            self._logger.warning(
                "chatlog_organizer.chapter_not_found",
                context={"session_id": session_id, "chapter": chapter_number}
            )
            return

        # Load and update chapter data
        chapter_data = self._read_chapter_file(session_id, chapter_number)
        chapter_data["chapter_title"] = chapter_title

        # Write updated file
        self._write_chapter_file(session_id, chapter_number, chapter_data)

        self._logger.info(
            "chatlog_organizer.chapter_finalized",
            context={
                "session_id": session_id,
                "chapter": chapter_number,
                "title": chapter_title
            }
        )

    def get_chapter_info(
        self,
        session_id: str,
        chapter_number: int
    ) -> dict[str, Any] | None:
        """Get chapter metadata without loading all messages.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number

        Returns:
            Dict with chapter metadata or None if not found
        """
        chapter_file = self._get_chapter_file_path(session_id, chapter_number)

        if not chapter_file.exists():
            return None

        chapter_data = self._read_chapter_file(session_id, chapter_number)

        return {
            "chapter_number": chapter_data["chapter_number"],
            "chapter_title": chapter_data["chapter_title"],
            "start_message": chapter_data["start_message"],
            "end_message": chapter_data["end_message"],
            "message_count": len(chapter_data["messages"])
        }

    def list_chapters(self, session_id: str) -> list[dict[str, Any]]:
        """List all chapters for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of chapter metadata dicts
        """
        chatlogs_dir = self._get_chatlogs_dir(session_id)

        if not chatlogs_dir.exists():
            return []

        chapters = []
        for chapter_file in sorted(chatlogs_dir.glob("chapter_*.json")):
            try:
                chapter_num = int(chapter_file.stem.replace("chapter_", ""))
                info = self.get_chapter_info(session_id, chapter_num)
                if info:
                    chapters.append(info)
            except (ValueError, KeyError) as e:
                self._logger.warning(
                    "chatlog_organizer.invalid_chapter_file",
                    context={"file": str(chapter_file), "error": str(e)}
                )

        return chapters

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _format_message(self, message: SessionMessage) -> dict[str, Any]:
        """Format SessionMessage for chapter file storage.

        Args:
            message: Session message

        Returns:
            Dict with message data including scene_context snapshot
        """
        # Extract scene_context snapshot from agent_data_background
        scene_context_snapshot = message.agent_data_background.get("scene_context_snapshot", {})

        return {
            "message_number": message.response_num,
            "timestamp": message.timestamp,
            "user_message": message.user_message,
            "claude_response": message.assistant_response,
            "scene_context_snapshot": scene_context_snapshot
        }

    def _load_session_by_id(self, session_id: str) -> SessionData:
        """Load session data by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData

        Raises:
            FileNotFoundError: If session not found
        """
        if session_id == "main":
            return self._repository.load_active_session()

        # Check branches
        session_file = self._paths.session_branches_dir / f"session_{session_id}.json"
        if session_file.exists():
            from ...infrastructure.filesystem import JsonStore
            store = JsonStore(root=self._paths.session_branches_dir, logger=self._logger)
            data = store.read(Path(session_file.name))
            return SessionData.from_dict(data)

        # Check archived
        session_file = self._paths.session_archived_dir / f"session_{session_id}.json"
        if session_file.exists():
            from ...infrastructure.filesystem import JsonStore
            store = JsonStore(root=self._paths.session_archived_dir, logger=self._logger)
            data = store.read(Path(session_file.name))
            return SessionData.from_dict(data)

        raise FileNotFoundError(f"Session '{session_id}' not found")

    def _get_chatlogs_dir(self, session_id: str) -> Path:
        """Get chatlogs directory for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to chatlogs directory
        """
        return self._paths.sessions_dir / "chatlogs" / session_id

    def _get_chapter_file_path(self, session_id: str, chapter_number: int) -> Path:
        """Get path to chapter file.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number

        Returns:
            Path to chapter file
        """
        return self._get_chatlogs_dir(session_id) / f"chapter_{chapter_number}.json"

    def _read_chapter_file(self, session_id: str, chapter_number: int) -> dict[str, Any]:
        """Read chapter file.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number

        Returns:
            Chapter data dict

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        chapter_file = self._get_chapter_file_path(session_id, chapter_number)

        if not chapter_file.exists():
            raise FileNotFoundError(f"Chapter file not found: {chapter_file}")

        with open(chapter_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_chapter_file(
        self,
        session_id: str,
        chapter_number: int,
        chapter_data: dict[str, Any]
    ) -> None:
        """Write chapter file atomically.

        Args:
            session_id: Session identifier
            chapter_number: Chapter number
            chapter_data: Chapter data dict
        """
        chapter_file = self._get_chapter_file_path(session_id, chapter_number)

        # Ensure directory exists
        chapter_file.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically (temp file + rename)
        temp_file = chapter_file.with_suffix(".json.tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)
            temp_file.replace(chapter_file)  # Atomic on both POSIX and Windows
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e


__all__ = ["ChatlogOrganizer"]
