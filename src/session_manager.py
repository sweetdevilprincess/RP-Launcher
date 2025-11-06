"""
Session Manager - Core Session Log System

Manages session logs for retry, branching, checkpointing, and switching.
Based on Phase 1 architecture documented in docs/planned_features/checkpoint_retry/.
"""

from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class SessionManager:
    """Manages session logs for retry, branching, and checkpointing."""

    def __init__(self, rp_dir: Path):
        """Initialize SessionManager."""
        self.rp_dir = Path(rp_dir)
        if not self.rp_dir.exists():
            raise ValueError(f"RP directory does not exist: {rp_dir}")

        self.sessions_dir = self.rp_dir / "sessions"
        self.branches_dir = self.sessions_dir / "branches"
        self.archived_dir = self.sessions_dir / "archived"

        self.sessions_dir.mkdir(exist_ok=True)
        self.branches_dir.mkdir(exist_ok=True)
        self.archived_dir.mkdir(exist_ok=True)

        self.active_session_path = self.sessions_dir / "session_main.json"

    # --------------------------------------------------------------------- #
    # Session loading and saving
    # --------------------------------------------------------------------- #

    def load_session(self, session_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load session from JSON file."""
        session_path = Path(session_path) if session_path else self.active_session_path

        if not session_path.exists():
            raise FileNotFoundError(f"Session not found: {session_path}")

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid session JSON: {exc}") from exc

        self._validate_session(session)
        return session

    def save_session(self, session: Dict[str, Any], session_path: Optional[Path] = None) -> None:
        """Save session to JSON file."""
        session_path = Path(session_path) if session_path else self.active_session_path

        session["last_modified"] = datetime.now().isoformat()
        self._validate_session(session)

        session_path.parent.mkdir(parents=True, exist_ok=True)

        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------------------- #
    # Core helpers
    # --------------------------------------------------------------------- #

    def _validate_session(self, session: Dict[str, Any]) -> None:
        """Validate session structure and raise ValueError if invalid."""
        if not isinstance(session, dict):
            raise ValueError("Session must be a dictionary")

        required_fields = [
            "session_id",
            "session_type",
            "created",
            "last_modified",
            "current_response",
            "tags",
            "messages",
            "rp_metadata",
        ]

        for field in required_fields:
            if field not in session:
                raise ValueError(f"Session missing required field: {field}")

        if not isinstance(session["tags"], list):
            raise ValueError("Session tags must be a list")

        messages = session["messages"]
        if not isinstance(messages, list):
            raise ValueError("Session messages must be a list")

        current_response = session.get("current_response")
        if not isinstance(current_response, int) or current_response < 0:
            raise ValueError("current_response must be a non-negative integer")

        if current_response != len(messages):
            raise ValueError("Session current_response does not match number of messages")

        if not isinstance(session["rp_metadata"], dict):
            raise ValueError("Session rp_metadata must be a dictionary")

        message_required_fields = [
            "response_num",
            "timestamp",
            "chapter",
            "user_message",
            "assistant_response",
            "agent_data_background",
            "agent_data_immediate",
            "model_info",
        ]

        for index, message in enumerate(messages, start=1):
            if not isinstance(message, dict):
                raise ValueError("Session message must be a dictionary")

            for field in message_required_fields:
                if field not in message:
                    raise ValueError(f"Message missing required field: {field}")

            if message["response_num"] != index:
                raise ValueError("Message response_num must be sequential starting at 1")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize session name for filesystem usage."""
        safe = "".join(c for c in name if c.isalnum() or c in " _-")
        safe = safe.strip()
        safe = safe.replace(" ", "_")

        while "__" in safe:
            safe = safe.replace("__", "_")

        return safe.lower()[:50]

    def _add_auto_tags(
        self,
        user_tags: Optional[List[str]],
        session_type: str,
        response_num: int,
        chapter: int,
    ) -> List[str]:
        """Combine user tags with automatic system tags."""
        tags: List[str] = list(user_tags or [])

        if session_type == "archived":
            tags.append("retry")
        elif session_type == "checkpoint":
            tags.append("checkpoint")
        elif session_type == "branch":
            tags.append("branch")

        tags.append(f"chapter-{chapter}")
        tags.append(f"response-{response_num}")
        tags.append(datetime.now().strftime("date-%Y%m%d"))

        deduped: List[str] = []
        seen = set()

        for tag in tags:
            if not tag:
                continue
            if tag not in seen:
                deduped.append(tag)
                seen.add(tag)

        return deduped

    # --------------------------------------------------------------------- #
    # Core copy operation and command wrappers
    # --------------------------------------------------------------------- #

    def copy_session(
        self,
        up_to_response: int,
        new_session_name: str,
        session_type: str = "branch",
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> Path:
        """Copy session up to specific response number."""
        active = self.load_session()

        if up_to_response < 0 or up_to_response > active["current_response"]:
            raise ValueError(
                f"Invalid response number: {up_to_response} "
                f"(session has {active['current_response']} messages)"
            )

        safe_name = self._sanitize_name(new_session_name)
        if not safe_name:
            raise ValueError("Session name cannot be empty")

        if session_type == "branch":
            save_path = self.branches_dir / f"session_{safe_name}.json"
        elif session_type == "archived":
            save_path = self.archived_dir / f"{safe_name}.json"
        elif session_type == "checkpoint":
            save_path = self.archived_dir / f"checkpoint_{safe_name}.json"
        else:
            raise ValueError(f"Invalid session_type: {session_type}")

        if save_path.exists():
            raise ValueError(f"Session already exists: {safe_name}")

        rp_metadata = deepcopy(active.get("rp_metadata", {}))
        chapter = rp_metadata.get("chapter", 1)

        new_session = {
            "session_id": safe_name,
            "session_type": session_type,
            "parent_session": active.get("session_id"),
            "branch_point": up_to_response,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "current_response": up_to_response,
            "tags": self._add_auto_tags(tags, session_type, up_to_response, chapter),
            "description": description,
            "rp_metadata": rp_metadata,
            "messages": deepcopy(active["messages"][:up_to_response]),
        }

        self.save_session(new_session, save_path)
        return save_path

    def retry(self, tags: Optional[List[str]] = None) -> Path:
        """Retry last response by archiving current state and removing last message."""
        active = self.load_session()

        if active["current_response"] == 0:
            raise ValueError("Cannot retry: Session is empty")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"retry_{timestamp}"

        archive_path = self.copy_session(
            up_to_response=active["current_response"],
            new_session_name=archive_name,
            session_type="archived",
            tags=tags or [],
            description="Retried response",
        )

        active["messages"] = active["messages"][:-1]
        active["current_response"] -= 1
        active["last_modified"] = datetime.now().isoformat()

        self.save_session(active)
        return archive_path

    def branch(
        self,
        branch_name: str,
        response_num: Optional[int] = None,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> Path:
        """Create named branch from specific point."""
        if not branch_name or not branch_name.strip():
            raise ValueError("Branch name cannot be empty")

        safe_name = self._sanitize_name(branch_name)
        if not safe_name:
            raise ValueError("Branch name cannot be empty")

        active = self.load_session()
        branch_point = response_num if response_num is not None else active["current_response"]

        return self.copy_session(
            up_to_response=branch_point,
            new_session_name=branch_name,
            session_type="branch",
            tags=tags or [],
            description=description,
        )

    def checkpoint(
        self,
        checkpoint_name: str,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> Path:
        """Save checkpoint at current point."""
        if not checkpoint_name or not checkpoint_name.strip():
            raise ValueError("Checkpoint name cannot be empty")

        safe_name = self._sanitize_name(checkpoint_name)
        if not safe_name:
            raise ValueError("Checkpoint name cannot be empty")

        active = self.load_session()

        return self.copy_session(
            up_to_response=active["current_response"],
            new_session_name=checkpoint_name,
            session_type="checkpoint",
            tags=tags or [],
            description=description,
        )

    def switch(self, session_name: str) -> Path:
        """Switch to different session."""
        if not session_name or not session_name.strip():
            raise ValueError("Session name cannot be empty")

        safe_name = self._sanitize_name(session_name)
        if not safe_name:
            raise ValueError("Session name cannot be empty")

        candidates = [
            self.branches_dir / f"session_{safe_name}.json",
            self.archived_dir / f"{safe_name}.json",
            self.archived_dir / f"checkpoint_{safe_name}.json",
        ]

        session_path: Optional[Path] = None
        for candidate in candidates:
            if candidate.exists():
                session_path = candidate
                break

        if session_path is None:
            backup_candidates = sorted(
                self.archived_dir.glob("switch_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for backup in backup_candidates:
                try:
                    candidate_session = self.load_session(backup)
                except (FileNotFoundError, ValueError):
                    continue
                if self._sanitize_name(candidate_session.get("session_id", "")) == safe_name:
                    session_path = backup
                    break

        if session_path is None:
            raise FileNotFoundError(f"Session not found: {session_name}")

        active = self.load_session()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.archived_dir / f"switch_backup_{timestamp}.json"
        self.save_session(active, backup_path)

        target = self.load_session(session_path)
        target["session_type"] = "active"
        self.save_session(target, self.active_session_path)

        return self.active_session_path

    # --------------------------------------------------------------------- #
    # Session discovery
    # --------------------------------------------------------------------- #

    def list_sessions(self, tag_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available sessions with optional tag filtering."""
        sessions: List[Dict[str, Any]] = []

        if self.active_session_path.exists():
            try:
                active = self.load_session()
                sessions.append({
                    "name": active.get("session_id", "main"),
                    "type": "active",
                    "path": self.active_session_path,
                    "response_count": active.get("current_response", 0),
                    "tags": active.get("tags", []),
                    "description": active.get("description", ""),
                    "last_modified": active.get("last_modified", ""),
                })
            except (FileNotFoundError, ValueError):
                pass

        for session_file in self.branches_dir.glob("session_*.json"):
            try:
                session = self.load_session(session_file)
            except (FileNotFoundError, ValueError):
                continue

            sessions.append({
                "name": session.get("session_id"),
                "type": session.get("session_type", "branch"),
                "path": session_file,
                "response_count": session.get("current_response", 0),
                "tags": session.get("tags", []),
                "description": session.get("description", ""),
                "last_modified": session.get("last_modified", ""),
            })

        for session_file in self.archived_dir.glob("*.json"):
            if "switch_backup" in session_file.name:
                continue

            try:
                session = self.load_session(session_file)
            except (FileNotFoundError, ValueError):
                continue

            sessions.append({
                "name": session.get("session_id"),
                "type": session.get("session_type", "archived"),
                "path": session_file,
                "response_count": session.get("current_response", 0),
                "tags": session.get("tags", []),
                "description": session.get("description", ""),
                "last_modified": session.get("last_modified", ""),
            })

        if tag_filter:
            sessions = [s for s in sessions if tag_filter in s.get("tags", [])]

        sessions.sort(key=lambda s: s.get("last_modified", ""), reverse=True)
        return sessions

    # --------------------------------------------------------------------- #
    # Message management
    # --------------------------------------------------------------------- #

    def append_message(
        self,
        user_message: str,
        assistant_response: str,
        agent_data_background: Optional[Dict] = None,
        agent_data_immediate: Optional[Dict] = None,
        model_info: Optional[Dict] = None,
    ) -> int:
        """Append new message to active session."""
        session = self.load_session()
        new_response_num = session["current_response"] + 1

        message = {
            "response_num": new_response_num,
            "timestamp": datetime.now().isoformat(),
            "chapter": session.get("rp_metadata", {}).get("chapter", 1),
            "user_message": user_message,
            "assistant_response": assistant_response,
            "agent_data_background": agent_data_background or {},
            "agent_data_immediate": agent_data_immediate or {},
            "model_info": model_info or {},
        }

        session["messages"].append(message)
        session["current_response"] = new_response_num

        self.save_session(session)
        return new_response_num

    def append_message_entry(self, message: Dict[str, Any], status: Optional[str] = None) -> Dict[str, Any]:
        """Append a complete message entry to the active session log."""
        session = self.load_session()
        new_response_num = session["current_response"] + 1

        entry = deepcopy(message)
        entry["response_num"] = new_response_num
        entry.setdefault("timestamp", datetime.now().isoformat())
        entry.setdefault("chapter", session.get("rp_metadata", {}).get("chapter", 1))
        entry.setdefault("agent_data_background", {})
        entry.setdefault("agent_data_immediate", {})
        entry.setdefault("model_info", {})

        if status is not None:
            entry["status"] = status

        session["messages"].append(entry)
        session["current_response"] = new_response_num

        self.save_session(session)
        return entry

    def update_message_agent_data(
        self,
        response_num: int,
        field: str,
        data: Dict[str, Any],
    ) -> None:
        """Update agent data for a specific message."""
        if field not in {"agent_data_background", "agent_data_immediate"}:
            raise ValueError("Invalid field for agent data update")

        session = self.load_session()

        if response_num < 1 or response_num > session["current_response"]:
            raise ValueError("Invalid response number")

        message = session["messages"][response_num - 1]
        message[field] = data

        self.save_session(session)

    def update_message_entry(
        self,
        response_num: int,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        merge: bool = True,
    ) -> Dict[str, Any]:
        """Update message metadata/status for a specific response."""
        session = self.load_session()

        if response_num < 1 or response_num > session["current_response"]:
            raise ValueError("Invalid response number")

        message = session["messages"][response_num - 1]

        if metadata:
            for key, value in metadata.items():
                if merge and isinstance(message.get(key), dict) and isinstance(value, dict):
                    updated = dict(message.get(key, {}))
                    updated.update(value)
                    message[key] = updated
                else:
                    message[key] = value

        if status is not None:
            message["status"] = status

        self.save_session(session)
        return message

    # --------------------------------------------------------------------- #
    # Misc utilities
    # --------------------------------------------------------------------- #

    def get_current_response_count(self) -> int:
        """Get current response count from active session."""
        try:
            session = self.load_session()
            return session.get("current_response", 0)
        except (FileNotFoundError, ValueError):
            return 0

    def session_exists(self, session_name: str) -> bool:
        """Check if a session exists."""
        if not session_name:
            return False

        safe_name = self._sanitize_name(session_name)
        if not safe_name:
            return False

        if self.active_session_path.exists():
            try:
                active = self.load_session()
                if self._sanitize_name(active.get("session_id", "")) == safe_name:
                    return True
            except (FileNotFoundError, ValueError):
                pass

        candidates = [
            self.branches_dir / f"session_{safe_name}.json",
            self.archived_dir / f"{safe_name}.json",
            self.archived_dir / f"checkpoint_{safe_name}.json",
        ]

        if any(path.exists() for path in candidates):
            return True

        for backup in self.archived_dir.glob("switch_backup_*.json"):
            try:
                data = self.load_session(backup)
            except (FileNotFoundError, ValueError):
                continue
            if self._sanitize_name(data.get("session_id", "")) == safe_name:
                return True

        return False

    def create_initial_session(self, rp_name: str, chapter: int = 1) -> None:
        """Create initial empty session."""
        if self.active_session_path.exists():
            raise FileExistsError("Active session already exists")

        initial_session = self._create_empty_session()
        initial_session["rp_metadata"]["rp_name"] = rp_name
        initial_session["rp_metadata"]["chapter"] = chapter
        initial_session["tags"] = ["main-timeline", f"chapter-{chapter}"]
        initial_session["created"] = datetime.now().isoformat()
        initial_session["last_modified"] = datetime.now().isoformat()

        self.save_session(initial_session)

    def _create_empty_session(self) -> Dict[str, Any]:
        """Create an empty session structure."""
        return {
            "session_id": "main",
            "session_type": "active",
            "parent_session": None,
            "branch_point": None,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "current_response": 0,
            "tags": ["main-timeline"],
            "description": "",
            "rp_metadata": {
                "rp_name": "Untitled RP",
                "chapter": 1,
                "scene": "",
            },
            "messages": [],
        }
