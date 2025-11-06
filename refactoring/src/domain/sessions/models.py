"""Domain models for session management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _generate_checkpoint_id() -> str:
    """Generate unique checkpoint ID."""
    return f"cp_{uuid.uuid4().hex[:12]}"


@dataclass
class SessionCheckpoint:
    """Represents a save-point in the session for branching/restoration."""

    checkpoint_id: str
    message_index: int
    timestamp: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        message_index: int,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> SessionCheckpoint:
        """Create a new checkpoint with auto-generated ID.

        Args:
            message_index: Index of the message this checkpoint references
            description: Human-readable description
            metadata: Optional additional metadata

        Returns:
            New SessionCheckpoint
        """
        return cls(
            checkpoint_id=_generate_checkpoint_id(),
            message_index=message_index,
            timestamp=_now_iso(),
            description=description,
            metadata=metadata or {},
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionCheckpoint:
        """Load checkpoint from dict."""
        return cls(
            checkpoint_id=str(data.get("checkpoint_id", "")),
            message_index=int(data.get("message_index", 0)),
            timestamp=str(data.get("timestamp", _now_iso())),
            description=str(data.get("description", "")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize checkpoint to dict."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "message_index": self.message_index,
            "timestamp": self.timestamp,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass
class SessionMessage:
    """Represents a single entry in the session log."""

    response_num: int
    timestamp: str
    chapter: int
    user_message: str
    assistant_response: str
    agent_data_background: dict[str, Any] = field(default_factory=dict)
    agent_data_immediate: dict[str, Any] = field(default_factory=dict)
    model_info: dict[str, Any] = field(default_factory=dict)
    status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMessage:
        return cls(
            response_num=int(data.get("response_num", 0)),
            timestamp=str(data.get("timestamp", _now_iso())),
            chapter=int(data.get("chapter", 1)),
            user_message=str(data.get("user_message", "")),
            assistant_response=str(data.get("assistant_response", "")),
            agent_data_background=dict(data.get("agent_data_background", {})),
            agent_data_immediate=dict(data.get("agent_data_immediate", {})),
            model_info=dict(data.get("model_info", {})),
            status=data.get("status"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "response_num": self.response_num,
            "timestamp": self.timestamp,
            "chapter": self.chapter,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "agent_data_background": self.agent_data_background,
            "agent_data_immediate": self.agent_data_immediate,
            "model_info": self.model_info,
        }
        if self.status is not None:
            payload["status"] = self.status
        return payload


@dataclass
class SessionData:
    """Aggregate session document."""

    session_id: str
    session_type: str
    parent_session: str | None
    branch_point: int | None
    created: str
    last_modified: str
    current_response: int
    tags: list[str] = field(default_factory=list)
    description: str = ""
    rp_metadata: dict[str, Any] = field(default_factory=dict)
    messages: list[SessionMessage] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    checkpoints: list[SessionCheckpoint] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionData:
        messages = [SessionMessage.from_dict(item) for item in data.get("messages", [])]
        checkpoints = [SessionCheckpoint.from_dict(cp) for cp in data.get("checkpoints", [])]
        return cls(
            session_id=str(data.get("session_id", "main")),
            session_type=str(data.get("session_type", "active")),
            parent_session=data.get("parent_session"),
            branch_point=data.get("branch_point"),
            created=str(data.get("created", _now_iso())),
            last_modified=str(data.get("last_modified", _now_iso())),
            current_response=int(data.get("current_response", len(messages))),
            tags=list(data.get("tags", [])),
            description=str(data.get("description", "")),
            rp_metadata=dict(data.get("rp_metadata", {})),
            messages=messages,
            total_duration_seconds=float(data.get("total_duration_seconds", 0.0)),
            checkpoints=checkpoints,
        )

    @classmethod
    def create_default(cls, *, rp_name: str = "Untitled RP", chapter: int = 1) -> SessionData:
        now = _now_iso()
        return cls(
            session_id="main",
            session_type="active",
            parent_session=None,
            branch_point=None,
            created=now,
            last_modified=now,
            current_response=0,
            tags=["main-timeline", f"chapter-{chapter}"],
            description="",
            rp_metadata={
                "rp_name": rp_name,
                "chapter": chapter,
                "scene": "",
            },
            messages=[],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_type": self.session_type,
            "parent_session": self.parent_session,
            "branch_point": self.branch_point,
            "created": self.created,
            "last_modified": self.last_modified,
            "current_response": self.current_response,
            "tags": self.tags,
            "description": self.description,
            "rp_metadata": self.rp_metadata,
            "messages": [message.to_dict() for message in self.messages],
            "total_duration_seconds": self.total_duration_seconds,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
        }

    def touch(self) -> None:
        """Update the modification timestamp."""

        self.last_modified = _now_iso()

    def sync_response_count(self) -> None:
        """Ensure response count equals the number of messages."""

        self.current_response = len(self.messages)

    def latest_message(self) -> SessionMessage | None:
        return self.messages[-1] if self.messages else None

    def validate(self) -> None:
        if self.current_response != len(self.messages):
            raise ValueError("Session current_response must match message count")
        if not isinstance(self.tags, list):
            raise ValueError("Session tags must be a list")
        if not isinstance(self.rp_metadata, dict):
            raise ValueError("Session rp_metadata must be a mapping")
        for index, message in enumerate(self.messages, start=1):
            if message.response_num != index:
                raise ValueError("Session messages must be sequential starting at 1")
