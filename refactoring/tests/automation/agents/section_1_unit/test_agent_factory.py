"""Unit tests for AgentFactory - Agent instantiation from catalog metadata.

Tests the AgentFactory component in isolation with mock agent classes.
"""

import pytest
from pathlib import Path
from refactoring.src.automation.contracts import AgentMetadata, AgentType
from refactoring.src.automation.services.agent_catalog import AgentCatalog
from refactoring.src.automation.services.agent_factory import (
    AgentFactory,
    AgentCreationError,
)


class MockAgentClass:
    """Mock agent class for testing instantiation."""

    def __init__(self, rp_dir: Path, log_file: Path):
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.agent_id = "test_agent"


class FailingMockAgentClass:
    """Mock agent that raises exception during construction."""

    def __init__(self, rp_dir: Path, log_file: Path):
        raise ValueError("Agent construction failed")


@pytest.mark.unit
def test_create_agent_success(tmp_path, stub_logger, sample_immediate_metadata):
    """Test successful agent creation with valid ID."""
    catalog = AgentCatalog()
    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    agent = factory.create_agent(sample_immediate_metadata.agent_id)

    assert agent is not None
    assert isinstance(agent, MockAgentClass)
    assert agent.rp_dir == tmp_path
    assert agent.log_file == tmp_path / "test.log"


@pytest.mark.unit
def test_create_agent_not_found_raises_error(tmp_path, stub_logger):
    """Test that creating non-existent agent raises error."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    with pytest.raises(AgentCreationError, match="not found in registry"):
        factory.create_agent("nonexistent_agent")


@pytest.mark.unit
def test_create_agent_disabled_raises_error(tmp_path, stub_logger):
    """Test that creating disabled agent raises error."""
    catalog = AgentCatalog()

    # Create disabled agent metadata
    disabled_metadata = AgentMetadata(
        agent_id="disabled_agent",
        description="Disabled agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=False,
    )

    catalog.register_agent(disabled_metadata, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    with pytest.raises(AgentCreationError, match="is disabled"):
        factory.create_agent("disabled_agent")


@pytest.mark.unit
def test_create_agent_construction_failure_raises_error(tmp_path, stub_logger):
    """Test that agent construction failure is caught and wrapped."""
    catalog = AgentCatalog()

    metadata = AgentMetadata(
        agent_id="failing_agent",
        description="Failing agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    catalog.register_agent(metadata, agent_class=FailingMockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    with pytest.raises(AgentCreationError, match="Failed to create agent"):
        factory.create_agent("failing_agent")


@pytest.mark.unit
def test_create_agents_multiple_success(tmp_path, stub_logger):
    """Test creating multiple agents in batch."""
    catalog = AgentCatalog()

    # Register multiple agents
    agent1 = AgentMetadata(
        agent_id="agent1",
        description="First agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    agent2 = AgentMetadata(
        agent_id="agent2",
        description="Second agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    catalog.register_agent(agent1, agent_class=MockAgentClass)
    catalog.register_agent(agent2, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    agents = factory.create_agents(["agent1", "agent2"])

    assert len(agents) == 2
    assert all(isinstance(a, MockAgentClass) for a in agents)


@pytest.mark.unit
def test_create_agents_skips_disabled(tmp_path, stub_logger):
    """Test that create_agents silently skips disabled agents."""
    catalog = AgentCatalog()

    enabled_agent = AgentMetadata(
        agent_id="enabled",
        description="Enabled agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    disabled_agent = AgentMetadata(
        agent_id="disabled",
        description="Disabled agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=False,
    )

    catalog.register_agent(enabled_agent, agent_class=MockAgentClass)
    catalog.register_agent(disabled_agent, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Should only create enabled agent
    agents = factory.create_agents(["enabled", "disabled"])

    assert len(agents) == 1
    assert agents[0].agent_id == "test_agent"


@pytest.mark.unit
def test_create_agents_continues_on_error(tmp_path, stub_logger):
    """Test that create_agents continues creating other agents after error."""
    catalog = AgentCatalog()

    good_agent = AgentMetadata(
        agent_id="good",
        description="Good agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    failing_agent = AgentMetadata(
        agent_id="failing",
        description="Failing agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    catalog.register_agent(good_agent, agent_class=MockAgentClass)
    catalog.register_agent(failing_agent, agent_class=FailingMockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Should create good agent and skip failing agent
    agents = factory.create_agents(["failing", "good"])

    assert len(agents) == 1
    assert isinstance(agents[0], MockAgentClass)


@pytest.mark.unit
def test_create_agents_with_conditional_context(tmp_path, stub_logger):
    """Test conditional agent creation based on context."""
    catalog = AgentCatalog()

    # fact_extraction requires tier2_entities
    fact_agent = AgentMetadata(
        agent_id="fact_extraction",
        description="Fact extraction agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    catalog.register_agent(fact_agent, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    # Should skip fact_extraction when tier2_entities is empty
    agents = factory.create_agents(
        ["fact_extraction"],
        context={"tier2_entities": []},
    )

    assert len(agents) == 0

    # Should create fact_extraction when tier2_entities is non-empty
    agents = factory.create_agents(
        ["fact_extraction"],
        context={"tier2_entities": ["Alice", "Bob"]},
    )

    assert len(agents) == 1


@pytest.mark.unit
def test_create_immediate_agents(tmp_path, stub_logger):
    """Test creating all immediate agents from catalog."""
    catalog = AgentCatalog()

    # Register immediate agents
    immediate1 = AgentMetadata(
        agent_id="immediate1",
        description="Immediate agent 1",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    immediate2 = AgentMetadata(
        agent_id="immediate2",
        description="Immediate agent 2",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    # Register background agent (should not be created)
    background = AgentMetadata(
        agent_id="background1",
        description="Background agent",
        agent_type=AgentType.BACKGROUND,
        enabled=True,
    )

    catalog.register_agent(immediate1, agent_class=MockAgentClass)
    catalog.register_agent(immediate2, agent_class=MockAgentClass)
    catalog.register_agent(background, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    agents = factory.create_immediate_agents()

    # Should only create immediate agents
    assert len(agents) == 2


@pytest.mark.unit
def test_create_background_agents(tmp_path, stub_logger):
    """Test creating all background agents from catalog."""
    catalog = AgentCatalog()

    # Register immediate agent (should not be created)
    immediate = AgentMetadata(
        agent_id="immediate1",
        description="Immediate agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True,
    )

    # Register background agents
    background1 = AgentMetadata(
        agent_id="background1",
        description="Background agent 1",
        agent_type=AgentType.BACKGROUND,
        enabled=True,
    )

    background2 = AgentMetadata(
        agent_id="background2",
        description="Background agent 2",
        agent_type=AgentType.BACKGROUND,
        enabled=True,
    )

    catalog.register_agent(immediate, agent_class=MockAgentClass)
    catalog.register_agent(background1, agent_class=MockAgentClass)
    catalog.register_agent(background2, agent_class=MockAgentClass)

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=stub_logger,
    )

    agents = factory.create_background_agents()

    # Should only create background agents
    assert len(agents) == 2


@pytest.mark.unit
def test_should_create_agent_no_conditional_requirement(tmp_path):
    """Test that agents without conditional requirements are always created."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
    )

    # Agent without conditional requirement
    result = factory._should_create_agent("some_agent", {})

    assert result is True


@pytest.mark.unit
def test_should_create_agent_list_requirements(tmp_path):
    """Test conditional creation with list requirements."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
    )

    # fact_extraction requires non-empty tier2_entities
    assert factory._should_create_agent(
        "fact_extraction",
        {"tier2_entities": ["Alice", "Bob"]},
    ) is True

    assert factory._should_create_agent(
        "fact_extraction",
        {"tier2_entities": []},
    ) is False

    # memory_extraction requires non-empty scene_participants
    assert factory._should_create_agent(
        "memory_extraction",
        {"scene_participants": ["Alice"]},
    ) is True

    assert factory._should_create_agent(
        "memory_extraction",
        {"scene_participants": []},
    ) is False


@pytest.mark.unit
def test_should_create_agent_boolean_requirements(tmp_path):
    """Test conditional creation with boolean requirements."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
    )

    # contradiction_detection requires boolean flag
    assert factory._should_create_agent(
        "contradiction_detection",
        {"enable_contradiction_detection": True},
    ) is True

    assert factory._should_create_agent(
        "contradiction_detection",
        {"enable_contradiction_detection": False},
    ) is False


@pytest.mark.unit
def test_should_create_agent_missing_context(tmp_path):
    """Test conditional creation when required context is missing."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
    )

    # Should return False when required field is missing
    assert factory._should_create_agent(
        "fact_extraction",
        {},  # Missing tier2_entities
    ) is False

    assert factory._should_create_agent(
        "memory_extraction",
        {},  # Missing scene_participants
    ) is False


@pytest.mark.unit
def test_factory_repr(tmp_path):
    """Test factory string representation."""
    catalog = AgentCatalog()

    factory = AgentFactory(
        catalog=catalog,
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
    )

    repr_str = repr(factory)

    assert "AgentFactory" in repr_str
    assert tmp_path.name in repr_str
