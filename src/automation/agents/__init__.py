"""
Agent System for RP Claude Code

This package provides a modular agent system based on DeepSeek for
analyzing roleplay responses and gathering context.

Architecture:
- BaseAgent: Abstract base class with common logic
- Background Agents (6): Run after Response N while user types (~30s hidden)
- Immediate Agents (4): Run before Response N+1 (~5s visible)

Usage:
    from src.automation.agents import ResponseAnalyzerAgent
    from src.automation.agent_coordinator import AgentCoordinator

    # Create agent
    agent = ResponseAnalyzerAgent(rp_dir, log_file)

    # Register with coordinator
    coordinator = AgentCoordinator(rp_dir, log_file)
    coordinator.add_agent(
        agent.get_agent_id(),
        agent.execute,
        response_text, response_number,
        description=agent.get_description()
    )

    # Run all agents concurrently
    context = coordinator.run_all_agents(timeout=30)
"""

# Base class
from src.automation.agents.base_agent import BaseAgent

# Background agents (run after Response N)
from src.automation.agents.background.response_analyzer import ResponseAnalyzerAgent
from src.automation.agents.background.memory_creation import MemoryCreationAgent
from src.automation.agents.background.relationship_analysis import RelationshipAnalysisAgent
from src.automation.agents.background.plot_thread_detection import PlotThreadDetectionAgent
from src.automation.agents.background.knowledge_extraction import KnowledgeExtractionAgent
from src.automation.agents.background.contradiction_detection import ContradictionDetectionAgent

# Immediate agents (run before Response N+1)
from src.automation.agents.immediate.quick_entity_analysis import QuickEntityAnalysisAgent
from src.automation.agents.immediate.fact_extraction import FactExtractionAgent
from src.automation.agents.immediate.memory_extraction import MemoryExtractionAgent
from src.automation.agents.immediate.plot_thread_extraction import PlotThreadExtractionAgent

# Convenience functions
from src.automation.agents.background.response_analyzer import analyze_response
from src.automation.agents.background.memory_creation import extract_memories as create_memories
from src.automation.agents.background.relationship_analysis import analyze_relationships
from src.automation.agents.background.plot_thread_detection import detect_plot_threads
from src.automation.agents.background.knowledge_extraction import extract_knowledge
from src.automation.agents.background.contradiction_detection import detect_contradictions
from src.automation.agents.immediate.quick_entity_analysis import analyze_entities
from src.automation.agents.immediate.fact_extraction import extract_facts
from src.automation.agents.immediate.memory_extraction import extract_memories
from src.automation.agents.immediate.plot_thread_extraction import extract_plot_threads

__all__ = [
    # Base class
    "BaseAgent",

    # Background agents
    "ResponseAnalyzerAgent",
    "MemoryCreationAgent",
    "RelationshipAnalysisAgent",
    "PlotThreadDetectionAgent",
    "KnowledgeExtractionAgent",
    "ContradictionDetectionAgent",

    # Immediate agents
    "QuickEntityAnalysisAgent",
    "FactExtractionAgent",
    "MemoryExtractionAgent",
    "PlotThreadExtractionAgent",

    # Convenience functions
    "analyze_response",
    "create_memories",
    "analyze_relationships",
    "detect_plot_threads",
    "extract_knowledge",
    "detect_contradictions",
    "analyze_entities",
    "extract_facts",
    "extract_memories",
    "extract_plot_threads",
]
