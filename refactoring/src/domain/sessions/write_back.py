"""Session write-back integration for automation agents.

Enables agents to append messages, update existing messages, and add metadata
to sessions during the automation pipeline.
"""

from __future__ import annotations

from typing import Any

from ...shared.interfaces import LoggingService
from .models import SessionMessage
from .repository import SessionRepository


class SessionWriteBack:
    """Handles automation-driven session updates.

    This component provides a safe interface for agents to update session data
    during the automation pipeline. It enforces validation and logging.
    """

    def __init__(self, *, repository: SessionRepository, logger: LoggingService) -> None:
        """Initialize write-back handler.

        Args:
            repository: Session repository for persistence
            logger: Logging service
        """
        self._repository = repository
        self._logger = logger

    def append_message(
        self,
        *,
        user_message: str,
        assistant_response: str,
        chapter: int = 1,
        agent_data_background: dict[str, Any] | None = None,
        agent_data_immediate: dict[str, Any] | None = None,
        model_info: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> int:
        """Append a new message to the active session.

        Args:
            user_message: User's message
            assistant_response: Assistant's response
            chapter: Chapter number
            agent_data_background: Background agent analysis data
            agent_data_immediate: Immediate agent context data
            model_info: Model metadata (name, tokens, etc.)
            status: Optional status indicator

        Returns:
            Response number of the appended message
        """
        from datetime import UTC, datetime

        # Create message
        message = SessionMessage(
            response_num=0,  # Will be set by repository
            timestamp=datetime.now(tz=UTC).isoformat(),
            chapter=chapter,
            user_message=user_message,
            assistant_response=assistant_response,
            agent_data_background=agent_data_background or {},
            agent_data_immediate=agent_data_immediate or {},
            model_info=model_info or {},
            status=status,
        )

        # Append to session
        session = self._repository.append_message(message)

        self._logger.info(
            "session_writeback.message_appended",
            context={
                "response_num": message.response_num,
                "chapter": chapter,
                "has_bg_data": bool(agent_data_background),
                "has_im_data": bool(agent_data_immediate),
            },
        )

        return message.response_num

    def update_message_content(
        self,
        response_num: int,
        *,
        updated_user_message: str | None = None,
        updated_assistant_response: str | None = None,
    ) -> None:
        """Update the content of an existing message.

        Args:
            response_num: Response number to update
            updated_user_message: New user message content (if updating)
            updated_assistant_response: New assistant response content (if updating)

        Raises:
            ValueError: If response_num is invalid or no updates provided
        """
        if updated_user_message is None and updated_assistant_response is None:
            raise ValueError("Must provide at least one field to update")

        # Load active session
        session = self._repository.load_active_session()

        # Find message by response_num
        if response_num < 1 or response_num > len(session.messages):
            raise ValueError(
                f"Invalid response_num {response_num}, valid range is 1-{len(session.messages)}"
            )

        message = session.messages[response_num - 1]

        # Update fields
        if updated_user_message is not None:
            message.user_message = updated_user_message
        if updated_assistant_response is not None:
            message.assistant_response = updated_assistant_response

        # Save session
        self._repository.save_session(session)

        self._logger.info(
            "session_writeback.message_updated",
            context={
                "response_num": response_num,
                "updated_user": updated_user_message is not None,
                "updated_assistant": updated_assistant_response is not None,
            },
        )

    def add_agent_data(
        self,
        response_num: int,
        *,
        background_data: dict[str, Any] | None = None,
        immediate_data: dict[str, Any] | None = None,
        merge: bool = True,
    ) -> None:
        """Add or update agent data for a specific message.

        Args:
            response_num: Response number to update
            background_data: Background agent analysis data
            immediate_data: Immediate agent context data
            merge: If True, merge with existing data; if False, replace

        Raises:
            ValueError: If response_num is invalid or no data provided
        """
        if background_data is None and immediate_data is None:
            raise ValueError("Must provide at least one data field to update")

        # Load active session
        session = self._repository.load_active_session()

        # Find message by response_num
        if response_num < 1 or response_num > len(session.messages):
            raise ValueError(
                f"Invalid response_num {response_num}, valid range is 1-{len(session.messages)}"
            )

        message = session.messages[response_num - 1]

        # Update agent data
        if background_data is not None:
            if merge:
                message.agent_data_background.update(background_data)
            else:
                message.agent_data_background = background_data

        if immediate_data is not None:
            if merge:
                message.agent_data_immediate.update(immediate_data)
            else:
                message.agent_data_immediate = immediate_data

        # Save session
        self._repository.save_session(session)

        self._logger.info(
            "session_writeback.agent_data_updated",
            context={
                "response_num": response_num,
                "updated_bg": background_data is not None,
                "updated_im": immediate_data is not None,
                "merge": merge,
            },
        )

    def update_message_status(self, response_num: int, status: str) -> None:
        """Update the status of a specific message.

        Args:
            response_num: Response number to update
            status: New status value

        Raises:
            ValueError: If response_num is invalid
        """
        # Load active session
        session = self._repository.load_active_session()

        # Find message by response_num
        if response_num < 1 or response_num > len(session.messages):
            raise ValueError(
                f"Invalid response_num {response_num}, valid range is 1-{len(session.messages)}"
            )

        message = session.messages[response_num - 1]
        message.status = status

        # Save session
        self._repository.save_session(session)

        self._logger.info(
            "session_writeback.status_updated",
            context={"response_num": response_num, "status": status},
        )

    def update_model_info(self, response_num: int, model_info: dict[str, Any]) -> None:
        """Update model metadata for a specific message.

        Args:
            response_num: Response number to update
            model_info: Model metadata dict

        Raises:
            ValueError: If response_num is invalid
        """
        # Load active session
        session = self._repository.load_active_session()

        # Find message by response_num
        if response_num < 1 or response_num > len(session.messages):
            raise ValueError(
                f"Invalid response_num {response_num}, valid range is 1-{len(session.messages)}"
            )

        message = session.messages[response_num - 1]
        message.model_info.update(model_info)

        # Save session
        self._repository.save_session(session)

        self._logger.debug(
            "session_writeback.model_info_updated",
            context={"response_num": response_num},
        )
