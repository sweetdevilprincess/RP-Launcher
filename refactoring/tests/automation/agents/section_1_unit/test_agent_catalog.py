"""Unit tests for AgentCatalog - Agent registration and discovery.

Tests the AgentCatalog component in isolation with no external dependencies.
"""

import pytest
from refactoring.src.automation.contracts import AgentMetadata, AgentType
from refactoring.src.automation.services.agent_catalog import (
    AgentCatalog,
    AgentRegistrationError,
)


class MockAgentClass:
    """Mock agent class for testing registration."""
    pass


class AnotherMockAgentClass:
    """Another mock agent class for testing multiple registrations."""
    pass


@pytest.mark.unit
def test_register_agent_success(sample_immediate_metadata):
    """Test successful agent registration."""
    catalog = AgentCatalog()

    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    # Verify registration
    assert catalog.is_registered(sample_immediate_metadata.agent_id)
    metadata = catalog.get_agent_metadata(sample_immediate_metadata.agent_id)
    assert metadata == sample_immediate_metadata


@pytest.mark.unit
def test_register_duplicate_agent_raises_error(sample_immediate_metadata):
    """Test that registering duplicate agent_id raises error."""
    catalog = AgentCatalog()

    # Register once - should succeed
    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    # Register again with same agent_id - should fail
    with pytest.raises(AgentRegistrationError, match="already registered"):
        catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)


@pytest.mark.unit
def test_get_agent_metadata_returns_correct_metadata(sample_immediate_metadata):
    """Test retrieving agent metadata."""
    catalog = AgentCatalog()
    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    retrieved = catalog.get_agent_metadata(sample_immediate_metadata.agent_id)

    assert retrieved is not None
    assert retrieved.agent_id == sample_immediate_metadata.agent_id
    assert retrieved.description == sample_immediate_metadata.description
    assert retrieved.agent_type == AgentType.IMMEDIATE


@pytest.mark.unit
def test_get_nonexistent_agent_returns_none():
    """Test that getting non-existent agent returns None."""
    catalog = AgentCatalog()

    result = catalog.get_agent_metadata("nonexistent_agent")

    assert result is None


@pytest.mark.unit
def test_get_agent_class(sample_immediate_metadata):
    """Test retrieving agent class."""
    catalog = AgentCatalog()
    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    retrieved_class = catalog.get_agent_class(sample_immediate_metadata.agent_id)

    assert retrieved_class is MockAgentClass


@pytest.mark.unit
def test_list_agents_by_type(sample_immediate_metadata, sample_background_metadata):
    """Test filtering agents by type."""
    catalog = AgentCatalog()

    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)
    catalog.register_agent(sample_background_metadata, agent_class=AnotherMockAgentClass)

    # List immediate agents
    immediate_agents = catalog.list_agents(agent_type=AgentType.IMMEDIATE)
    assert len(immediate_agents) == 1
    assert immediate_agents[0].agent_id == sample_immediate_metadata.agent_id

    # List background agents
    background_agents = catalog.list_agents(agent_type=AgentType.BACKGROUND)
    assert len(background_agents) == 1
    assert background_agents[0].agent_id == sample_background_metadata.agent_id


@pytest.mark.unit
def test_list_agents_sorted_by_priority():
    """Test that agents are sorted by priority (lower = higher priority)."""
    catalog = AgentCatalog()

    # Register agents with different priorities
    high_priority = AgentMetadata(
        agent_id="high_priority",
        description="High priority agent",
        agent_type=AgentType.IMMEDIATE,
        priority=1,
        enabled=True
    )

    low_priority = AgentMetadata(
        agent_id="low_priority",
        description="Low priority agent",
        agent_type=AgentType.IMMEDIATE,
        priority=10,
        enabled=True
    )

    mid_priority = AgentMetadata(
        agent_id="mid_priority",
        description="Mid priority agent",
        agent_type=AgentType.IMMEDIATE,
        priority=5,
        enabled=True
    )

    # Register in random order
    catalog.register_agent(low_priority, agent_class=MockAgentClass)
    catalog.register_agent(high_priority, agent_class=MockAgentClass)
    catalog.register_agent(mid_priority, agent_class=MockAgentClass)

    # List agents - should be sorted by priority
    agents = catalog.list_agents(agent_type=AgentType.IMMEDIATE)

    assert len(agents) == 3
    assert agents[0].agent_id == "high_priority"  # priority 1
    assert agents[1].agent_id == "mid_priority"   # priority 5
    assert agents[2].agent_id == "low_priority"   # priority 10


@pytest.mark.unit
def test_list_enabled_agents_only():
    """Test filtering to only enabled agents."""
    catalog = AgentCatalog()

    enabled_agent = AgentMetadata(
        agent_id="enabled",
        description="Enabled agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True
    )

    disabled_agent = AgentMetadata(
        agent_id="disabled",
        description="Disabled agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=False
    )

    catalog.register_agent(enabled_agent, agent_class=MockAgentClass)
    catalog.register_agent(disabled_agent, agent_class=MockAgentClass)

    # List only enabled agents
    enabled_agents = catalog.list_agents(
        agent_type=AgentType.IMMEDIATE,
        enabled_only=True
    )

    assert len(enabled_agents) == 1
    assert enabled_agents[0].agent_id == "enabled"


@pytest.mark.unit
def test_unregister_agent(sample_immediate_metadata):
    """Test removing an agent from catalog."""
    catalog = AgentCatalog()
    catalog.register_agent(sample_immediate_metadata, agent_class=MockAgentClass)

    # Verify registered
    assert catalog.is_registered(sample_immediate_metadata.agent_id)

    # Unregister
    result = catalog.unregister_agent(sample_immediate_metadata.agent_id)
    assert result is True

    # Verify no longer registered
    assert not catalog.is_registered(sample_immediate_metadata.agent_id)
    assert catalog.get_agent_metadata(sample_immediate_metadata.agent_id) is None


@pytest.mark.unit
def test_unregister_nonexistent_agent_returns_false():
    """Test that unregistering non-existent agent returns False."""
    catalog = AgentCatalog()

    result = catalog.unregister_agent("nonexistent")

    assert result is False


@pytest.mark.unit
def test_catalog_isolation():
    """Test that multiple catalogs don't interfere with each other."""
    catalog1 = AgentCatalog()
    catalog2 = AgentCatalog()

    metadata1 = AgentMetadata(
        agent_id="agent1",
        description="First agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True
    )

    metadata2 = AgentMetadata(
        agent_id="agent2",
        description="Second agent",
        agent_type=AgentType.IMMEDIATE,
        enabled=True
    )

    # Register different agents in each catalog
    catalog1.register_agent(metadata1, agent_class=MockAgentClass)
    catalog2.register_agent(metadata2, agent_class=AnotherMockAgentClass)

    # Verify isolation
    assert catalog1.is_registered("agent1")
    assert not catalog1.is_registered("agent2")

    assert catalog2.is_registered("agent2")
    assert not catalog2.is_registered("agent1")


@pytest.mark.unit
def test_register_agent_validates_class_type(sample_immediate_metadata):
    """Test that registering non-class raises error."""
    catalog = AgentCatalog()

    # Try to register an instance instead of class
    with pytest.raises(AgentRegistrationError, match="must be a class"):
        catalog.register_agent(sample_immediate_metadata, agent_class="not_a_class")
