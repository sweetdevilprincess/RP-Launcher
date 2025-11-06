"""Session service exposing higher-level operations for automation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from ...infrastructure.sessions import SessionStateService
from ...shared.interfaces import LoggingService
from .models import SessionMessage
from .repository import SessionRepository

if TYPE_CHECKING:
    from ...automation.contracts import AutomationContext


class SessionService:
    """Provides session-derived context for the automation pipeline."""

    def __init__(
        self,
        *,
        repository: SessionRepository,
        logger: LoggingService,
        session_state_service: SessionStateService | None = None,
    ) -> None:
        self._repository = repository
        self._logger = logger
        self._session_state_service = session_state_service

    def enrich_session(self, context: AutomationContext) -> AutomationContext:
        """Populate the automation context with session-derived data and timeline information."""

        try:
            session = self._repository.ensure_active_session()
        except Exception as exc:
            self._logger.exception(
                "session_service.load_failed",
                context={"rp_dir": str(context.rp_dir)},
                exc=exc,
            )
            return context

        latest_message = session.latest_message()
        if latest_message is None:
            return context

        updates: dict[str, object] = {}

        background = self._extract_agent_text(latest_message.agent_data_background)
        immediate = self._extract_agent_text(latest_message.agent_data_immediate)

        if background:
            updates["cached_background_context"] = background
        if immediate:
            updates["immediate_agent_context"] = immediate

        entities = self._extract_entities(latest_message)
        if entities:
            merged = sorted({*context.loaded_entities, *entities})
            updates["loaded_entities"] = merged

        # Enrich with timeline information from session state
        timeline_updates = self._load_timeline_info(context)
        if timeline_updates:
            updates.update(timeline_updates)

        if updates:
            return context.with_update(**updates)
        return context

    def _load_timeline_info(self, context: AutomationContext) -> dict[str, Any]:
        """Load timeline information from session state file.

        Returns:
            Dictionary with session_id, parent_session, and branch_point if available
        """
        if self._session_state_service is None:
            return {}

        try:
            state = self._session_state_service.load_session_state(context.rp_dir)
            timeline = state.get("timeline", {})

            session_id = timeline.get("current_session_id", "main")
            is_branch = timeline.get("is_branch", False)

            result = {"session_id": session_id}
            if is_branch:
                result["parent_session"] = timeline.get("parent_session")
                result["branch_point"] = timeline.get("branch_point")

            self._logger.debug(
                "session_service.timeline_enriched",
                context={
                    "session_id": session_id,
                    "is_branch": is_branch,
                },
            )

            return result

        except FileNotFoundError:
            # Session state doesn't exist yet (e.g., new RP)
            self._logger.debug(
                "session_service.no_state_file",
                context={
                    "message": "No session state file found, using default main timeline",
                    "rp_dir": str(context.rp_dir),
                },
            )
            return {}
        except Exception as exc:
            # Log error but don't break the pipeline
            self._logger.error(
                "session_service.timeline_enrichment_failed",
                context={"error": str(exc), "rp_dir": str(context.rp_dir)},
            )
            return {}

    # ------------------------------------------------------------------
    # Extraction helpers

    def _extract_agent_text(self, data: object) -> str:
        if isinstance(data, str):
            return data.strip()
        if not isinstance(data, dict):
            return ""
        for key in ("context", "prompt", "text", "body", "summary"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if not data:
            return ""
        try:
            serialized = json.dumps(data, indent=2, ensure_ascii=False)
        except TypeError:
            return ""
        return serialized

    def _extract_entities(self, message: SessionMessage) -> list[str]:
        entities: list[str] = []
        for container in (
            message.agent_data_immediate.get("entities"),
            message.agent_data_background.get("entities"),
            message.agent_data_immediate.get("characters_in_scene"),
        ):
            if isinstance(container, Iterable) and not isinstance(container, (str, bytes)):
                for item in container:
                    if isinstance(item, str) and item.strip():
                        entities.append(item.strip())
        return entities
