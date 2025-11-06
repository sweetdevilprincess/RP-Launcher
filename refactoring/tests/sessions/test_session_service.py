"""Tests for session repository and service integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from refactoring.src.automation.contracts import AutomationContext
from refactoring.src.domain.sessions.models import SessionData, SessionMessage
from refactoring.src.domain.sessions.repository import SessionRepository
from refactoring.src.domain.sessions.service import SessionService
from refactoring.src.infrastructure.filesystem.state_paths import StatePaths
from refactoring.src.shared.interfaces import LoggingService


class StubLogger(LoggingService):
    def debug(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def info(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def warning(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def error(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def exception(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None: ...


@pytest.fixture
def session_repository(tmp_path: Path) -> SessionRepository:
    paths = StatePaths(rp_dir=tmp_path)
    return SessionRepository(paths=paths, logger=StubLogger())


def test_ensure_active_session_creates_default_document(
    session_repository: SessionRepository,
) -> None:
    session = session_repository.ensure_active_session(rp_name="Celestial Saga", chapter=2)

    assert session.session_id == "main"
    assert session_repository.active_path.exists()

    stored = session_repository.load_active_session()
    assert stored.rp_metadata["rp_name"] == "Celestial Saga"
    assert stored.rp_metadata["chapter"] == 2


def test_session_service_populates_agent_context(tmp_path: Path) -> None:
    logger = StubLogger()
    repo = SessionRepository(paths=StatePaths(rp_dir=tmp_path), logger=logger)

    session = SessionData.create_default(rp_name="Celestial Saga")
    session.messages.append(
        SessionMessage(
            response_num=1,
            timestamp="2025-10-19T12:00:00",
            chapter=1,
            user_message="Hello",
            assistant_response="Greetings",
            agent_data_background={"summary": "Background insight"},
            agent_data_immediate={
                "prompt": "Immediate prompt",
                "entities": ["Aurora", "Lyra"],
            },
            model_info={},
        )
    )
    session.sync_response_count()
    repo.save_session(session)

    service = SessionService(repository=repo, logger=logger)
    context = AutomationContext(message="Next", rp_dir=tmp_path)

    enriched = service.enrich_session(context)

    assert enriched.cached_background_context == "Background insight"
    assert enriched.immediate_agent_context == "Immediate prompt"
    assert {"Aurora", "Lyra"}.issubset(set(enriched.loaded_entities))
