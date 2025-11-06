"""Shared fixtures for agent system tests."""

import pytest
from pathlib import Path
from typing import Any

from refactoring.src.automation.contracts import AgentContext, AutomationContext
from refactoring.src.automation.contracts.agent_contracts import AgentMetadata, AgentType
from refactoring.src.shared.interfaces import LoggingService, ConfigService


class StubLogger(LoggingService):
    """Stub logger for testing that captures log messages."""

    def __init__(self):
        self.messages = []

    def debug(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.messages.append(("debug", message, context))

    def info(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.messages.append(("info", message, context))

    def warning(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.messages.append(("warning", message, context))

    def error(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.messages.append(("error", message, context))

    def exception(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None:
        self.messages.append(("exception", message, context, exc))


@pytest.fixture
def stub_logger():
    """Provide a stub logger for testing."""
    return StubLogger()


@pytest.fixture
def sample_immediate_metadata():
    """Provide sample immediate agent metadata."""
    return AgentMetadata(
        agent_id="test_immediate",
        description="Test immediate agent",
        agent_type=AgentType.IMMEDIATE,
        priority=5,
        timeout_seconds=3.0,
        enabled=True,
    )


@pytest.fixture
def sample_background_metadata():
    """Provide sample background agent metadata."""
    return AgentMetadata(
        agent_id="test_background",
        description="Test background agent",
        agent_type=AgentType.BACKGROUND,
        priority=7,
        timeout_seconds=10.0,
        enabled=True,
    )


@pytest.fixture
def sample_automation_context(tmp_path: Path):
    """Provide sample automation context for testing."""
    return AutomationContext(
        message="Test message with Alice and Bob",
        rp_dir=tmp_path,
        response_count=1,
        loaded_entities=["Alice", "Bob"],
    )


@pytest.fixture
def sample_agent_context():
    """Provide sample agent context for testing."""
    return AgentContext(
        message="Test message",
        response_number=1,
        characters_in_scene=["Alice"],
        loaded_entities=["Alice", "Bob"],
    )


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, result: dict[str, Any] | None = None, fail: bool = False):
        self.agent_id = agent_id
        self.result = result or {"status": "success", "data": "test"}
        self.fail = fail
        self.called = False
        self.context_received = None

    def run(self, context: AgentContext) -> dict[str, Any]:
        """Mock run method."""
        self.called = True
        self.context_received = context
        if self.fail:
            raise RuntimeError(f"Mock agent {self.agent_id} failed")
        return self.result


@pytest.fixture
def mock_agent_factory():
    """Provide a factory for creating mock agents."""
    def _create(agent_id: str = "test_agent", result: dict = None, fail: bool = False):
        return MockAgent(agent_id, result, fail)
    return _create


class MockConfigService(ConfigService):
    """Mock config service for testing."""

    def __init__(self, config_data: dict[str, Any] | None = None):
        self._config = config_data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        parts = key.split(".")
        value = self._config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """Get config value as int."""
        value = self.get(key, default)
        return int(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get config value as bool."""
        value = self.get(key, default)
        return bool(value) if value is not None else default

    def section(self, key: str) -> dict[str, Any]:
        """Get config section."""
        return self.get(key, {})


@pytest.fixture
def mock_config_service():
    """Provide a mock config service."""
    return MockConfigService({
        "triggers": {
            "frequency_tracking": {
                "enabled": True,
                "window_size": 10,
                "escalation_threshold": 3,
            }
        }
    })
