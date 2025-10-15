#!/usr/bin/env python3
"""
Agent Factory

Factory pattern for creating and configuring agents.
Eliminates repetitive agent initialization code.
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Type
from dataclasses import dataclass

from src.automation.agent_coordinator import AgentCoordinator
from src.automation.core import log_to_file
from src.automation.agents import (
    QuickEntityAnalysisAgent,
    FactExtractionAgent,
    MemoryExtractionAgent,
    PlotThreadExtractionAgent,
    ResponseAnalyzerAgent,
    MemoryCreationAgent,
    RelationshipAnalysisAgent,
    PlotThreadDetectionAgent,
    KnowledgeExtractionAgent,
    ContradictionDetectionAgent
)


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_class: Type
    param_mapping: List[str]
    condition_field: Optional[str] = None
    description: Optional[str] = None


class AgentFactory:
    """
    Factory for creating and configuring agents.

    This eliminates the repetitive pattern of:
    1. Creating agent instance
    2. Getting agent ID
    3. Getting description
    4. Adding to coordinator
    """

    # Registry of all available agents with their configurations
    AGENT_REGISTRY = {
        # Immediate agents
        'quick_entity': AgentConfig(
            QuickEntityAnalysisAgent,
            ['message', 'message_number'],
            description="Quick entity analysis"
        ),
        'fact_extraction': AgentConfig(
            FactExtractionAgent,
            ['message', 'tier2_entities'],
            condition_field='tier2_entities',
            description="Extract facts for Tier 2 entities"
        ),
        'memory_extraction': AgentConfig(
            MemoryExtractionAgent,
            ['message', 'scene_participants'],
            condition_field='scene_participants',
            description="Extract relevant memories"
        ),
        'plot_thread_extraction': AgentConfig(
            PlotThreadExtractionAgent,
            ['message', 'message_number'],
            description="Extract plot threads"
        ),

        # Background agents
        'response_analyzer': AgentConfig(
            ResponseAnalyzerAgent,
            ['response_text', 'response_number', 'previous_scenes'],
            description="Analyze response for scene and pacing"
        ),
        'memory_creation': AgentConfig(
            MemoryCreationAgent,
            ['response_text', 'response_number', 'chapter'],
            description="Create memorable moments"
        ),
        'relationship_analysis': AgentConfig(
            RelationshipAnalysisAgent,
            ['response_text', 'response_number', 'characters_in_scene'],
            condition_field='characters_in_scene',
            description="Analyze character relationships"
        ),
        'plot_thread_detection': AgentConfig(
            PlotThreadDetectionAgent,
            ['response_text', 'response_number', 'chapter'],
            description="Detect plot thread changes"
        ),
        'knowledge_extraction': AgentConfig(
            KnowledgeExtractionAgent,
            ['response_text', 'response_number', 'chapter'],
            description="Extract world-building facts"
        ),
        'contradiction_detection': AgentConfig(
            ContradictionDetectionAgent,
            ['response_text', 'response_number'],
            condition_field='enable_contradiction_detection',
            description="Detect contradictions"
        )
    }

    def __init__(self, rp_dir: Path, log_file: Path):
        """
        Initialize agent factory.

        Args:
            rp_dir: RP directory path
            log_file: Log file path
        """
        self.rp_dir = rp_dir
        self.log_file = log_file

    def create_agent(self, agent_name: str, context: Dict[str, Any]) -> Optional[Tuple]:
        """
        Create a single agent with context.

        Args:
            agent_name: Name of agent to create
            context: Context dictionary with parameters

        Returns:
            Tuple of (agent_instance, execute_method, args) or None if conditions not met
        """
        if agent_name not in self.AGENT_REGISTRY:
            log_to_file(self.log_file, f"[AgentFactory] Unknown agent: {agent_name}")
            return None

        config = self.AGENT_REGISTRY[agent_name]

        # Check condition if specified
        if config.condition_field:
            condition_value = context.get(config.condition_field)
            if not condition_value:
                return None

        # Create agent instance
        agent = config.agent_class(self.rp_dir, self.log_file)

        # Extract parameters from context
        args = []
        for param_name in config.param_mapping:
            if param_name not in context:
                log_to_file(self.log_file,
                           f"[AgentFactory] Missing parameter '{param_name}' for {agent_name}")
                return None
            args.append(context[param_name])

        return (agent, agent.execute, args)

    def create_agent_batch(self, agent_names: List[str],
                          context: Dict[str, Any]) -> List[Tuple]:
        """
        Create multiple agents with context.

        Args:
            agent_names: List of agent names to create
            context: Context dictionary with parameters

        Returns:
            List of (agent, execute_method, args) tuples
        """
        agents = []
        for name in agent_names:
            agent_data = self.create_agent(name, context)
            if agent_data:
                agents.append(agent_data)
        return agents

    def add_agents_to_coordinator(self, coordinator: AgentCoordinator,
                                 agent_names: List[str],
                                 context: Dict[str, Any]) -> int:
        """
        Add multiple agents to a coordinator.

        Args:
            coordinator: Agent coordinator instance
            agent_names: List of agent names to add
            context: Context dictionary with parameters

        Returns:
            Number of agents added
        """
        added = 0
        for name in agent_names:
            agent_data = self.create_agent(name, context)
            if agent_data:
                agent, execute_method, args = agent_data
                config = self.AGENT_REGISTRY[name]

                coordinator.add_agent(
                    agent.get_agent_id(),
                    execute_method,
                    *args,
                    description=config.description or agent.get_description()
                )
                added += 1

        return added


class AgentOrchestrator:
    """
    Simplified agent orchestration using factory pattern.

    This replaces the repetitive agent initialization code in the main orchestrator.
    """

    def __init__(self, rp_dir: Path, log_file: Path, max_workers: int = 4):
        """
        Initialize agent orchestrator.

        Args:
            rp_dir: RP directory path
            log_file: Log file path
            max_workers: Maximum concurrent workers
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.max_workers = max_workers
        self.factory = AgentFactory(rp_dir, log_file)

    def run_immediate_agents(self, message: str, response_number: int,
                           loaded_entities: List[str]) -> str:
        """
        Run immediate agents (before prompt building).

        Args:
            message: User message
            response_number: Current response number
            loaded_entities: List of loaded entity names

        Returns:
            Agent context string
        """
        log_to_file(self.log_file, "--- Running Immediate Agents (Context Gathering) ---")

        coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=4)

        # Build context
        context = {
            'message': message,
            'message_number': response_number,
            'tier2_entities': [],  # TODO: Get from entity analysis
            'scene_participants': loaded_entities if loaded_entities else []
        }

        # Define which agents to run
        agent_names = [
            'quick_entity',
            'fact_extraction',
            'memory_extraction',
            'plot_thread_extraction'
        ]

        # Add agents using factory
        added = self.factory.add_agents_to_coordinator(coordinator, agent_names, context)
        log_to_file(self.log_file, f"[Immediate Agents] Added {added} agents")

        # Run all agents
        try:
            agent_context = coordinator.run_all_agents(timeout=10, allow_partial=True)

            stats = coordinator.get_stats()
            log_to_file(self.log_file,
                       f"[Immediate Agents] Completed: {stats['successful']}/{stats['agents_executed']} "
                       f"in {stats['max_duration_ms']}ms")

            return agent_context if agent_context else ""

        except Exception as e:
            log_to_file(self.log_file, f"[Immediate Agents] Error: {e}")
            return ""

    def run_background_agents(self, response_text: str, response_number: int,
                            characters_in_scene: Optional[List[str]] = None,
                            chapter: Optional[str] = None,
                            config: Optional[Dict] = None) -> None:
        """
        Run background agents (after response).

        Args:
            response_text: Claude's response text
            response_number: Current response number
            characters_in_scene: Optional list of characters
            chapter: Optional chapter identifier
            config: Optional configuration dict
        """
        log_to_file(self.log_file, "--- Running Background Agents (Post-Response Analysis) ---")

        coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=6)

        # Build context
        context = {
            'response_text': response_text,
            'response_number': response_number,
            'characters_in_scene': characters_in_scene,
            'chapter': chapter,
            'previous_scenes': [],  # TODO: Load from state
            'enable_contradiction_detection': config.get('enable_contradiction_detection', False) if config else False
        }

        # Define which agents to run
        agent_names = [
            'response_analyzer',
            'memory_creation',
            'relationship_analysis',
            'plot_thread_detection',
            'knowledge_extraction',
            'contradiction_detection'
        ]

        # Add agents using factory
        added = self.factory.add_agents_to_coordinator(coordinator, agent_names, context)
        log_to_file(self.log_file, f"[Background Agents] Added {added} agents")

        # Run all agents
        try:
            agent_context = coordinator.run_all_agents(timeout=60, allow_partial=True)

            stats = coordinator.get_stats()
            log_to_file(self.log_file,
                       f"[Background Agents] Completed: {stats['successful']}/{stats['agents_executed']} "
                       f"in {stats['max_duration_ms']}ms")

            # Save to cache
            cache_file = self.rp_dir / "state" / "agent_analysis.json"
            coordinator.save_to_cache(cache_file, response_number)
            log_to_file(self.log_file, "[Background Agents] Results saved to cache")

        except Exception as e:
            log_to_file(self.log_file, f"[Background Agents] Error: {e}")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())