"""Integration tests for AgentCoordinator - Full pipeline orchestration.

Tests the coordinator's integration of Catalog → Factory → Executor → Formatter pipeline.
"""

import pytest
import json
from pathlib import Path
from refactoring.src.automation.services.agent_coordinator import AgentCoordinator
from refactoring.src.automation.contracts import AgentMetadata, AgentType


class MockLegacyAgent:
    """Mock legacy agent for testing coordination."""

    def __init__(self, rp_dir: Path, log_file: Path):
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.executed = False

    def get_agent_id(self) -> str:
        return "mock_agent"

    def execute(self, *args, **kwargs) -> str:
        self.executed = True
        # Return JSON-formatted result
        return json.dumps({"status": "success", "data": "mock_result"})


@pytest.mark.integration
def test_coordinator_initializes_all_components(stub_logger, tmp_path):
    """Test that coordinator initializes all pipeline components."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Verify all components are initialized
    assert coordinator.catalog is not None
    assert coordinator.factory is not None
    assert coordinator.immediate_executor is not None
    assert coordinator.background_executor is not None
    assert coordinator.formatter is not None


@pytest.mark.integration
def test_coordinator_registers_agents_in_catalog(stub_logger, tmp_path):
    """Test that coordinator can register agents."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    metadata = AgentMetadata(
        agent_id="test_agent",
        description="Test agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    coordinator.register_agent(metadata, MockLegacyAgent)

    # Verify agent is in catalog
    assert coordinator.catalog.is_registered("test_agent")


@pytest.mark.integration
def test_coordinator_runs_immediate_agents_returns_empty_when_none(stub_logger, tmp_path):
    """Test that coordinator returns empty string when no immediate agents."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    result = coordinator.run_immediate_agents(
        message="Test message",
        response_number=1,
    )

    # No agents registered, should return empty
    assert result == ""


@pytest.mark.integration
def test_coordinator_runs_background_agents_returns_empty_cache_when_none(stub_logger, tmp_path):
    """Test that coordinator returns empty cache when no background agents."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    result = coordinator.run_background_agents(
        response_text="Test response",
        response_number=1,
    )

    # Should return empty cache structure
    assert result["version"] == "1.0"
    assert result["meta"]["resp_num"] == 1
    assert result["meta"]["agents_run"] == 0
    assert result["background"] == {}


@pytest.mark.integration
def test_coordinator_saves_cache_to_file(stub_logger, tmp_path):
    """Test that coordinator can save cache to file."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    cache_data = {
        "version": "1.0",
        "meta": {"resp_num": 5},
        "background": {},
    }

    cache_file = tmp_path / "state" / "agent_analysis.json"
    coordinator.save_to_cache(cache_data, cache_file)

    # Verify file was created
    assert cache_file.exists()

    # Verify content
    with open(cache_file) as f:
        loaded = json.load(f)
    assert loaded["meta"]["resp_num"] == 5


@pytest.mark.integration
def test_coordinator_loads_cache_from_file(stub_logger, tmp_path):
    """Test that coordinator can load cache from file."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Create cache file
    cache_file = tmp_path / "state" / "agent_analysis.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "version": "1.0",
        "meta": {"resp_num": 42},
        "background": {"test": "data"},
    }

    with open(cache_file, "w") as f:
        json.dump(cache_data, f)

    # Load it
    loaded = coordinator.load_from_cache(cache_file)

    assert loaded is not None
    assert loaded["meta"]["resp_num"] == 42
    assert loaded["background"]["test"] == "data"


@pytest.mark.integration
def test_coordinator_loads_cache_returns_none_when_missing(stub_logger, tmp_path):
    """Test that coordinator returns None when cache file doesn't exist."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    cache_file = tmp_path / "state" / "nonexistent.json"
    loaded = coordinator.load_from_cache(cache_file)

    assert loaded is None


@pytest.mark.integration
def test_coordinator_get_catalog_stats(stub_logger, tmp_path):
    """Test that coordinator provides catalog statistics."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Register some agents
    metadata1 = AgentMetadata(
        agent_id="immediate1",
        description="Immediate agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    metadata2 = AgentMetadata(
        agent_id="background1",
        description="Background agent",
        agent_type=AgentType.BACKGROUND,
        enabled=True,
    )

    coordinator.register_agent(metadata1, MockLegacyAgent)
    coordinator.register_agent(metadata2, MockLegacyAgent)

    stats = coordinator.get_catalog_stats()

    assert stats["total"] == 2
    assert stats["immediate"] == 1
    assert stats["background"] == 1
    assert stats["enabled"] == 2


@pytest.mark.integration
def test_coordinator_string_representation(stub_logger, tmp_path):
    """Test coordinator string representation."""
    coordinator = AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Register an agent
    metadata = AgentMetadata(
        agent_id="test",
        description="Test",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )
    coordinator.register_agent(metadata, MockLegacyAgent)

    repr_str = repr(coordinator)

    assert "AgentCoordinator" in repr_str
    assert "1 agents" in repr_str or "catalog=1" in repr_str
