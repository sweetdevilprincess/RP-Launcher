"""Service for managing centralized session state file (state/session.json)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ...shared.interfaces import LoggingService


class SessionStateService:
    """Manages the centralized session state file with backup support.

    This service owns state/session.json, which tracks:
    - Current timeline (session_id, branch info)
    - Timeline-specific file paths (arcs, relationships, plot threads)
    - RP metadata (response count, total messages, etc.)

    Provides atomic writes and automatic backup for corruption recovery.
    """

    def __init__(self, *, logger: LoggingService) -> None:
        self._logger = logger

    def initialize_session_state(
        self,
        rp_dir: Path,
        *,
        rp_title: str | None = None,
        session_id: str = "main",
    ) -> dict[str, Any]:
        """Initialize a new session state file with proper structure.

        Creates state/session.json with all required fields for a new RP.
        If the file already exists, this will merge with existing data to ensure
        all required fields are present (migration/repair).

        Args:
            rp_dir: Root directory of the RP
            rp_title: Optional title for the RP (defaults to directory name)
            session_id: Initial session ID (defaults to "main")

        Returns:
            The initialized session state dictionary
        """
        import datetime

        session_file = rp_dir / "state" / "session.json"

        # Check if file exists and try to load existing data
        existing_data = {}
        if session_file.exists():
            try:
                existing_data = json.loads(session_file.read_text(encoding="utf-8"))
                self._logger.info(
                    "session_state.initialize.merging_existing",
                    context={"path": str(session_file)},
                )
            except (json.JSONDecodeError, ValueError) as exc:
                self._logger.warning(
                    "session_state.initialize.corrupted_file",
                    context={"path": str(session_file), "error": str(exc)},
                )
                # Will create new file with defaults

        # Build complete session state with all required fields
        state = {
            "version": "2.0.0",
            "session_id": existing_data.get("session_id", session_id),
            "rp_title": existing_data.get("rp_title", rp_title or rp_dir.name),
            "response_count": existing_data.get("response_count", 0),
            "total_messages": existing_data.get("total_messages", 0),
            "start_time": existing_data.get(
                "start_time", datetime.datetime.now(datetime.UTC).isoformat()
            ),
            # Timeline metadata
            "timeline": existing_data.get("timeline", {
                "current_session_id": session_id,
                "session_type": "active",
                "is_branch": False,
                "parent_session": None,
                "branch_point": None,
            }),
            # Arc tracking configuration
            "arc_tracking": existing_data.get("arc_tracking", {
                "arc_file": f"state/arc_{session_id}.md",
                "arc_session_id": session_id,
            }),
            # Relationship tracking configuration
            "relationship_tracking": existing_data.get("relationship_tracking", {
                "relationship_file": f"state/relationships_{session_id}.json",
            }),
            # Plot threads configuration
            "plot_threads": existing_data.get("plot_threads", {
                "thread_file": f"state/plot_threads_{session_id}.json",
            }),
            # Scene context configuration
            "scene_context": existing_data.get("scene_context", {
                "scene_file": f"state/scene_context_{session_id}.json",
            }),
            # Knowledge base configuration
            "knowledge": existing_data.get("knowledge", {
                "knowledge_file": f"state/knowledge_{session_id}.json",
            }),
            # RP metadata (additional counters and stats)
            "rp_metadata": existing_data.get("rp_metadata", {
                "response_count": existing_data.get("response_count", 0),
                "total_messages": existing_data.get("total_messages", 0),
                "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
            }),
        }

        # Save the initialized state
        self.save_session_state(rp_dir, state)

        self._logger.info(
            "session_state.initialize.success",
            context={
                "path": str(session_file),
                "session_id": session_id,
                "rp_title": state["rp_title"],
            },
        )

        return state

    def load_session_state(
        self, rp_dir: Path, *, auto_initialize: bool = True
    ) -> dict[str, Any]:
        """Load session state from state/session.json.

        Falls back to .backup if primary file is corrupted.
        Can auto-initialize if file is missing (enabled by default).

        Args:
            rp_dir: Root directory of the RP
            auto_initialize: If True, automatically initialize session state if missing

        Returns:
            Session state dictionary

        Raises:
            FileNotFoundError: If both primary and backup files are missing/corrupted
                               and auto_initialize is False
        """
        session_file = rp_dir / "state" / "session.json"

        # Try primary file
        if session_file.exists():
            try:
                state = json.loads(session_file.read_text(encoding="utf-8"))
                self._logger.debug(
                    "session_state.load.success",
                    context={"path": str(session_file)},
                )
                return state
            except (json.JSONDecodeError, ValueError) as exc:
                self._logger.error(
                    "session_state.load.corrupted",
                    context={"path": str(session_file), "error": str(exc)},
                )

        # Fall back to backup
        backup_file = rp_dir / "state" / "session.json.backup"
        if backup_file.exists():
            try:
                state = json.loads(backup_file.read_text(encoding="utf-8"))
                self._logger.warning(
                    "session_state.load.from_backup",
                    context={"backup_path": str(backup_file)},
                )
                # Restore backup to primary
                shutil.copy2(backup_file, session_file)
                return state
            except (json.JSONDecodeError, ValueError) as exc:
                self._logger.error(
                    "session_state.load.backup_corrupted",
                    context={"path": str(backup_file), "error": str(exc)},
                )

        # No valid session file found
        if auto_initialize:
            self._logger.warning(
                "session_state.load.missing_auto_initializing",
                context={"rp_dir": str(rp_dir)},
            )
            return self.initialize_session_state(rp_dir)

        raise FileNotFoundError(
            f"Session state not found or corrupted in {rp_dir / 'state'}"
        )

    def save_session_state(self, rp_dir: Path, state: dict[str, Any]) -> None:
        """Save session state to state/session.json with backup.

        Creates backup before writing to prevent data loss.

        Args:
            rp_dir: Root directory of the RP
            state: Session state dictionary to save
        """
        session_file = rp_dir / "state" / "session.json"
        backup_file = rp_dir / "state" / "session.json.backup"

        # Ensure state directory exists
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if primary file exists
        if session_file.exists():
            try:
                shutil.copy2(session_file, backup_file)
                self._logger.debug(
                    "session_state.backup.created",
                    context={"backup_path": str(backup_file)},
                )
            except Exception as exc:
                self._logger.warning(
                    "session_state.backup.failed",
                    context={"error": str(exc)},
                )

        # Write new state atomically (temp file + rename)
        temp_file = session_file.with_suffix(".json.tmp")
        serialized = json.dumps(state, indent=2, ensure_ascii=False)
        temp_file.write_text(serialized, encoding="utf-8")
        temp_file.replace(session_file)  # Atomic on both POSIX and Windows

        self._logger.debug(
            "session_state.save.success",
            context={"path": str(session_file), "bytes": len(serialized.encode())},
        )

    def get_current_timeline(self, rp_dir: Path) -> dict[str, Any]:
        """Get current timeline info from session state.

        Returns:
            Timeline metadata (session_id, is_branch, parent_session, branch_point)
        """
        state = self.load_session_state(rp_dir)
        return state.get("timeline", {})

    def switch_timeline(
        self,
        rp_dir: Path,
        session_id: str,
        *,
        parent_session: str | None = None,
        branch_point: int | None = None,
    ) -> None:
        """Switch to a different timeline/branch.

        Updates state/session.json to point to the new timeline.

        Args:
            rp_dir: Root directory of the RP
            session_id: Target session ID
            parent_session: Parent session ID if this is a branch
            branch_point: Message index where branch diverged
        """
        state = self.load_session_state(rp_dir)

        is_branch = parent_session is not None
        session_type = "branch" if is_branch else "active"

        state["timeline"] = {
            "current_session_id": session_id,
            "session_type": session_type,
            "is_branch": is_branch,
            "parent_session": parent_session,
            "branch_point": branch_point,
        }

        # Update file paths for timeline-specific resources
        # Create missing fields for backwards compatibility with old session.json files
        if "arc_tracking" not in state:
            state["arc_tracking"] = {}
        state["arc_tracking"]["arc_file"] = f"state/arc_{session_id}.md"
        state["arc_tracking"]["arc_session_id"] = session_id

        if "relationship_tracking" not in state:
            state["relationship_tracking"] = {}
        state["relationship_tracking"][
            "relationship_file"
        ] = f"state/relationships_{session_id}.json"

        if "plot_threads" not in state:
            state["plot_threads"] = {}
        state["plot_threads"]["thread_file"] = f"state/plot_threads_{session_id}.json"

        # Update scene_context pointer for timeline-specific scene metadata
        if "scene_context" not in state:
            state["scene_context"] = {}
        state["scene_context"]["scene_file"] = f"state/scene_context_{session_id}.json"

        # Update knowledge pointer for timeline-specific knowledge base
        if "knowledge" not in state:
            state["knowledge"] = {}
        state["knowledge"]["knowledge_file"] = f"state/knowledge_{session_id}.json"

        self.save_session_state(rp_dir, state)
        self._logger.info(
            "session_state.timeline.switched",
            context={
                "session_id": session_id,
                "is_branch": is_branch,
                "parent_session": parent_session,
            },
        )

    def get_timeline_files(self, rp_dir: Path) -> dict[str, Path]:
        """Get paths to timeline-specific files.

        Returns:
            Dictionary mapping resource type to file path
        """
        state = self.load_session_state(rp_dir)

        return {
            "arc": rp_dir / state["arc_tracking"]["arc_file"],
            "relationships": rp_dir
            / state["relationship_tracking"]["relationship_file"],
            "plot_threads": rp_dir / state["plot_threads"]["thread_file"],
            "knowledge": rp_dir / state["knowledge"]["knowledge_file"],
        }

    def increment_response_count(self, rp_dir: Path) -> int:
        """Increment the response counter and return new value.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            Updated response count
        """
        state = self.load_session_state(rp_dir)

        if "rp_metadata" not in state:
            state["rp_metadata"] = {}

        current = state["rp_metadata"].get("response_count", 0)
        new_count = current + 1
        state["rp_metadata"]["response_count"] = new_count

        self.save_session_state(rp_dir, state)

        self._logger.debug(
            "session_state.response_count.incremented",
            context={"count": new_count},
        )

        return new_count

    def get_response_count(self, rp_dir: Path) -> int:
        """Get current response count from session state.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            Current response count
        """
        state = self.load_session_state(rp_dir)
        return state.get("rp_metadata", {}).get("response_count", 0)

    def get_current_chapter(self, rp_dir: Path) -> str:
        """Get current chapter from scene context.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            Current chapter name or empty string if not set
        """
        context = self.get_scene_context(rp_dir)
        return context.get("chapter", "")

    def set_current_chapter(self, rp_dir: Path, chapter: str) -> None:
        """Set current chapter in scene context.

        Args:
            rp_dir: Root directory of the RP
            chapter: Chapter name to set
        """
        # Get current scene context
        scene_data = self.get_scene_context(rp_dir)

        # Update chapter
        scene_data["chapter"] = chapter

        # Save back to file
        self.update_scene_context(rp_dir, scene_data)

        self._logger.debug(
            "session_state.chapter.updated",
            context={"chapter": chapter},
        )

    def get_current_location(self, rp_dir: Path) -> str:
        """Get current location from scene context.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            Current location or "Unknown" if not set
        """
        context = self.get_scene_context(rp_dir)
        return context.get("location", "Unknown")

    def set_current_location(self, rp_dir: Path, location: str) -> None:
        """Set current location in scene context.

        Args:
            rp_dir: Root directory of the RP
            location: Location to set
        """
        # Get current scene context
        scene_data = self.get_scene_context(rp_dir)

        # Update location
        scene_data["location"] = location

        # Save back to file
        self.update_scene_context(rp_dir, scene_data)

        self._logger.debug(
            "session_state.location.updated",
            context={"location": location},
        )

    def get_scene_context(self, rp_dir: Path) -> dict[str, Any]:
        """Get scene context for current timeline.

        Reads from timeline-specific scene_context_{session_id}.json file.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            Dict with chapter, location, characters_in_scene, scene_analysis, etc.
            Returns default empty context if file doesn't exist.
        """
        import json

        state = self.load_session_state(rp_dir)
        scene_file = state.get("scene_context", {}).get(
            "scene_file",
            "state/scene_context_main.json"
        )
        scene_path = rp_dir / scene_file

        if not scene_path.exists():
            # Return default context
            return {
                "chapter": "",
                "location": "Unknown",
                "characters_in_scene": [],
                "last_updated_message": 0,
                "scene_analysis": {},
                "time_context": {}
            }

        try:
            with open(scene_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self._logger.error(
                "scene_context.load_failed",
                context={"path": str(scene_path), "error": str(e)}
            )
            return {
                "chapter": "",
                "location": "Unknown",
                "characters_in_scene": [],
                "last_updated_message": 0,
                "scene_analysis": {},
                "time_context": {}
            }

    def update_scene_context(self, rp_dir: Path, scene_data: dict[str, Any]) -> None:
        """Update scene context for current timeline.

        Writes to timeline-specific scene_context_{session_id}.json file.

        Args:
            rp_dir: Root directory of the RP
            scene_data: Dict with chapter, location, characters_in_scene, etc.

        Side Effects:
            Writes to state/scene_context_{session_id}.json atomically
        """
        import json

        state = self.load_session_state(rp_dir)
        scene_file = state.get("scene_context", {}).get(
            "scene_file",
            "state/scene_context_main.json"
        )
        scene_path = rp_dir / scene_file

        # Ensure parent directory exists
        scene_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically (temp file + rename)
        temp_path = scene_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(scene_path)  # Atomic on both POSIX and Windows

            self._logger.debug(
                "scene_context.updated",
                context={
                    "path": str(scene_path),
                    "chapter": scene_data.get("chapter", ""),
                    "location": scene_data.get("location", "")
                }
            )
        except Exception as e:
            self._logger.error(
                "scene_context.update_failed",
                context={"path": str(scene_path), "error": str(e)}
            )
            if temp_path.exists():
                temp_path.unlink()
            raise

    def get_characters_in_scene(self, rp_dir: Path) -> list[str]:
        """Get characters currently in scene.

        Args:
            rp_dir: Root directory of the RP

        Returns:
            List of character names in current scene
        """
        context = self.get_scene_context(rp_dir)
        return context.get("characters_in_scene", [])


__all__ = ["SessionStateService"]
