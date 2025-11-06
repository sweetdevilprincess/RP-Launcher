"""Immediate agent execution strategy for pre-response context gathering.

Immediate agents run BEFORE sending the prompt to Claude to quickly gather
additional context that should be included in the prompt. They have short timeouts
(3-5 seconds) and their results are injected into the enhanced prompt.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any

from ...shared.interfaces import LoggingService
from ..contracts import AgentContext, AutomationContext, AutomationResult

# Import refactored immediate agents
try:
    from .immediate import (
        FactExtractionAgent,
        MemoryExtractionAgent,
        PlotThreadExtractionAgent,
    )
    FACT_EXTRACTION_AVAILABLE = True
    MEMORY_EXTRACTION_AVAILABLE = True
    PLOT_THREAD_EXTRACTION_AVAILABLE = True
except ImportError:
    FACT_EXTRACTION_AVAILABLE = False
    MEMORY_EXTRACTION_AVAILABLE = False
    PLOT_THREAD_EXTRACTION_AVAILABLE = False
    class FactExtractionAgent: pass
    class MemoryExtractionAgent: pass
    class PlotThreadExtractionAgent: pass

# Import legacy agents temporarily until they're refactored
# TODO (Workstream E): Move these agents into refactoring/ structure
try:
    from src.automation.agents import (
        FactExtractionAgent,
        PlotThreadExtractionAgent,
        QuickEntityAnalysisAgent,
    )
    LEGACY_AGENTS_AVAILABLE = True
except ImportError:
    LEGACY_AGENTS_AVAILABLE = False
    class FactExtractionAgent: pass
    class PlotThreadExtractionAgent: pass
    class QuickEntityAnalysisAgent: pass

# Determine if any agents are available
AGENTS_AVAILABLE = (
    FACT_EXTRACTION_AVAILABLE or
    MEMORY_EXTRACTION_AVAILABLE or
    PLOT_THREAD_EXTRACTION_AVAILABLE or
    LEGACY_AGENTS_AVAILABLE
)


class ImmediateAgentStrategy:
    """Execute immediate agents for pre-response context gathering.

    Immediate agents run quickly (with timeouts) to gather context that should
    be included in the Claude prompt. This provides dynamic, relevant information
    based on the user's message.

    Refactored agent types:
    - memory_extraction: Find relevant memories for characters (✓ Refactored)

    Legacy agent types (TODO: Refactor):
    - quick_entity_analysis: Fast analysis of mentioned entities
    - fact_extraction: Extract relevant facts about entities
    - plot_thread_extraction: Identify active plot threads
    """

    def __init__(
        self,
        *,
        logger: LoggingService,
        max_workers: int = 4,
        enabled_agents: dict[str, dict[str, any]] | None = None,
        default_timeout: int = 5,
        rp_dir: Any = None,
        bridge: Any = None,
    ) -> None:
        """Initialize immediate agent strategy.

        Args:
            logger: Logging service for diagnostics
            max_workers: Maximum concurrent agents
            enabled_agents: Dict mapping agent IDs to config (enabled, timeout_seconds)
            default_timeout: Default timeout in seconds if not specified
            rp_dir: RP directory path for agent instantiation
            bridge: Bridge service for agent LLM access
        """
        self._logger = logger
        self._max_workers = max_workers
        self._enabled_agents = enabled_agents or {}
        self._default_timeout = default_timeout
        self._rp_dir = rp_dir
        self._bridge = bridge

    def create_context(self, context: AutomationContext) -> AgentContext:
        """Create agent context from automation context.

        Immediate agents need:
        - message: User's message to analyze
        - response_number: For context and naming
        - loaded_entities: Entities detected in tier loading
        - characters_in_scene: Characters mentioned in message
        - in_scene_entities: Entities actively in scene (full cards loaded)
        - referenced_entities: Entities mentioned but not in scene (basics only)

        Args:
            context: The automation context

        Returns:
            Agent context suitable for immediate processing
        """
        # Extract characters_in_scene from in_scene_entities
        # Filter to only characters (not locations/items)
        characters_in_scene = context.in_scene_entities if context.in_scene_entities else context.loaded_entities

        return AgentContext(
            message=context.message,
            response_number=context.response_count,
            loaded_entities=context.loaded_entities,
            characters_in_scene=characters_in_scene,
            chapter=None,  # TODO: Extract from session state when available
            previous_scenes=[],  # Not typically needed for immediate agents
            in_scene_entities=context.in_scene_entities,
            referenced_entities=context.referenced_entities,
        )

    def execute(
        self,
        agent_context: AgentContext,
        prompt: str,
        automation_context: Any = None,
    ) -> AutomationResult:
        """Execute immediate agents concurrently and inject results into prompt.

        Args:
            agent_context: Context for agent execution
            prompt: The current prompt (will be enhanced with agent results)
            automation_context: Full automation context (unused by this strategy)

        Returns:
            AutomationResult with enhanced prompt including agent context
        """
        if not AGENTS_AVAILABLE:
            self._logger.warning(
                "immediate_agents.unavailable",
                context={"reason": "Legacy agents not imported"},
            )
            return AutomationResult(
                success=True,
                enhanced_prompt=prompt,
                cached_context="",
                error="Immediate agents not available (import error)",
            )

        enabled_count = sum(
            1 for config in self._enabled_agents.values() if config.get("enabled", False)
        )

        self._logger.info(
            "immediate_agents.start",
            context={
                "response_number": agent_context.response_number,
                "enabled_count": enabled_count,
            },
        )

        agent_tasks = self._prepare_agent_tasks(agent_context)

        if not agent_tasks:
            self._logger.debug(
                "immediate_agents.none_enabled",
                context={"response_number": agent_context.response_number},
            )
            return AutomationResult(
                success=True, enhanced_prompt=prompt, cached_context=""
            )

        # Use rp_dir from initialization (fallback to automation_context if not set)
        rp_dir = self._rp_dir
        if not rp_dir and automation_context:
            rp_dir = automation_context.rp_dir
        if not rp_dir:
            self._logger.error("immediate_agents.missing_rp_dir")
            return AutomationResult(
                success=False,
                enhanced_prompt=prompt,
                error="Missing rp_dir in strategy initialization"
            )

        # Execute agents concurrently with timeout
        results = self._execute_agents_concurrent(agent_tasks, agent_context, rp_dir)

        # Format agent results for injection
        agent_context_text = self._format_agent_results(results)

        # Inject into prompt
        if agent_context_text:
            enhanced_prompt = self._inject_agent_context(prompt, agent_context_text)
        else:
            enhanced_prompt = prompt

        success_count = sum(1 for r in results.values() if r.get("success", False))
        self._logger.info(
            "immediate_agents.complete",
            context={
                "total": len(agent_tasks),
                "successful": success_count,
                "failed": len(agent_tasks) - success_count,
                "context_length": len(agent_context_text),
            },
        )

        return AutomationResult(
            success=True,
            enhanced_prompt=enhanced_prompt,
            cached_context=agent_context_text,
        )

    def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type, int]]:
        """Prepare list of agents to execute based on configuration.

        Args:
            agent_context: Context for filtering agents

        Returns:
            List of (agent_id, agent_class, timeout) tuples
        """
        # Early return if no agents available
        if not AGENTS_AVAILABLE:
            return []

        available_agents = {}

        # Add refactored agents
        if FACT_EXTRACTION_AVAILABLE:
            available_agents["fact_extraction"] = FactExtractionAgent

        if MEMORY_EXTRACTION_AVAILABLE:
            available_agents["memory_extraction"] = MemoryExtractionAgent

        if PLOT_THREAD_EXTRACTION_AVAILABLE:
            available_agents["plot_thread_extraction"] = PlotThreadExtractionAgent

        # Add legacy agents
        if LEGACY_AGENTS_AVAILABLE:
            available_agents.update({
                "quick_entity_analysis": QuickEntityAnalysisAgent,
            })

        tasks = []
        for agent_id, agent_class in available_agents.items():
            agent_config = self._enabled_agents.get(agent_id, {})
            if not agent_config.get("enabled", False):
                continue

            # Check if agent has required context
            if agent_id == "fact_extraction" and not agent_context.loaded_entities:
                continue  # Skip if no entities loaded
            if agent_id == "memory_extraction" and not agent_context.has_characters:
                continue  # Skip if no characters in scene

            timeout = agent_config.get("timeout_seconds", self._default_timeout)
            tasks.append((agent_id, agent_class, timeout))

        return tasks

    def _execute_agents_concurrent(
        self, agent_tasks: list[tuple[str, type, int]], agent_context: AgentContext, rp_dir
    ) -> dict[str, dict[str, any]]:
        """Execute agents concurrently using thread pool with timeouts.

        Args:
            agent_tasks: List of (agent_id, agent_class, timeout) tuples
            agent_context: Context for agent execution
            rp_dir: RP directory path for agent instantiation

        Returns:
            Dict mapping agent_id to result dict
        """
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all agent tasks
            future_to_agent = {}
            for agent_id, agent_class, timeout in agent_tasks:
                future = executor.submit(
                    self._execute_single_agent,
                    agent_id,
                    agent_class,
                    agent_context,
                    timeout,
                    rp_dir,
                )
                future_to_agent[future] = (agent_id, timeout)

            # Collect results as they complete
            for future in concurrent.futures.as_completed(
                future_to_agent, timeout=max(t for _, _, t in agent_tasks) + 1
            ):
                agent_id, timeout = future_to_agent[future]
                try:
                    result = future.result(timeout=timeout)
                    results[agent_id] = result
                except concurrent.futures.TimeoutError:
                    self._logger.warning(
                        "immediate_agent.timeout",
                        context={"agent_id": agent_id, "timeout": timeout},
                    )
                    results[agent_id] = {
                        "success": False,
                        "error": f"Timeout after {timeout}s",
                    }
                except Exception as exc:
                    self._logger.exception(
                        "immediate_agent.execution_error",
                        context={"agent_id": agent_id},
                        exc=exc,
                    )
                    results[agent_id] = {"success": False, "error": str(exc)}

        return results

    def _execute_single_agent(
        self, agent_id: str, agent_class: type, agent_context: AgentContext, timeout: int, rp_dir
    ) -> dict[str, any]:
        """Execute a single immediate agent.

        Args:
            agent_id: Agent identifier
            agent_class: Agent class to instantiate
            agent_context: Context for execution
            timeout: Maximum execution time in seconds
            rp_dir: RP directory path

        Returns:
            Result dict with success, content, duration, etc.
        """
        start_time = time.perf_counter()

        try:
            self._logger.debug(
                "immediate_agent.start",
                context={"agent_id": agent_id, "timeout": timeout},
            )

            # Instantiate agent with rp_dir and bridge for LLM access
            agent = agent_class(rp_dir=rp_dir, log_file=None, bridge=self._bridge)

            # Call agent.execute() with user message, response number, and entity context
            # BaseAgent.execute() accepts *args/**kwargs that are passed to gather_data()
            result_text = agent.execute(
                user_message=agent_context.message,
                message_number=agent_context.response_number,
                loaded_entities=agent_context.loaded_entities,
                in_scene_entities=agent_context.in_scene_entities,
                referenced_entities=agent_context.referenced_entities,
            )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            self._logger.debug(
                "immediate_agent.complete",
                context={"agent_id": agent_id, "duration_ms": duration_ms},
            )

            return {
                "success": True,
                "agent_id": agent_id,
                "duration_ms": duration_ms,
                "content": result_text,
            }

        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._logger.exception(
                "immediate_agent.error",
                context={"agent_id": agent_id, "duration_ms": duration_ms},
                exc=exc,
            )
            return {
                "success": False,
                "agent_id": agent_id,
                "duration_ms": duration_ms,
                "error": str(exc),
            }

    def _format_agent_results(self, results: dict[str, dict[str, any]]) -> str:
        """Format agent results for injection into prompt.

        Args:
            results: Dict mapping agent_id to result dict

        Returns:
            Formatted text ready for prompt injection
        """
        if not results:
            return ""

        sections = []
        for agent_id, result in results.items():
            if result.get("success") and result.get("content"):
                sections.append(f"<!-- {agent_id} -->\n{result['content']}")

        if not sections:
            return ""

        return "\n\n".join(sections)

    def _inject_agent_context(self, prompt: str, agent_context: str) -> str:
        """Inject agent context into the prompt.

        Args:
            prompt: Original prompt
            agent_context: Formatted agent results

        Returns:
            Enhanced prompt with agent context
        """
        # Inject before the user message section
        user_message_marker = "========== USER MESSAGE =========="
        if user_message_marker in prompt:
            parts = prompt.split(user_message_marker, 1)
            return (
                f"{parts[0]}\n\n"
                f"<!-- IMMEDIATE AGENT CONTEXT -->\n{agent_context}\n\n"
                f"{user_message_marker}{parts[1]}"
            )

        # If no marker found, append at end
        return f"{prompt}\n\n<!-- IMMEDIATE AGENT CONTEXT -->\n{agent_context}"
