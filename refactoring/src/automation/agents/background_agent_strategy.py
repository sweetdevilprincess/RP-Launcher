"""Background agent execution strategy for post-response analysis.

Background agents run AFTER Claude generates a response and perform analysis tasks
like creating memories, analyzing relationships, detecting plot threads, etc.
Results are saved to files for future reference.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any

from ...shared.interfaces import LoggingService
from ..contracts import AgentContext, AutomationContext, AutomationResult

# Import refactored agents from implementations
try:
    from .implementations import (
        ContradictionSynthesisAgent,
        KnowledgeExtractionAgent,
        MemoryCreationAgent,
        PlotThreadDetectionAgent,
        RelationshipAnalysisAgent,
        ResponseAnalyzerAgent,
        TimeTrackingAgent,
    )
    RESPONSE_ANALYZER_AVAILABLE = True
    TIME_TRACKING_AVAILABLE = True
    MEMORY_CREATION_AVAILABLE = True
    PLOT_THREAD_DETECTION_AVAILABLE = True
    RELATIONSHIP_ANALYSIS_AVAILABLE = True
    KNOWLEDGE_EXTRACTION_AVAILABLE = True
    CONTRADICTION_SYNTHESIS_AVAILABLE = True
except ImportError:
    RESPONSE_ANALYZER_AVAILABLE = False
    TIME_TRACKING_AVAILABLE = False
    MEMORY_CREATION_AVAILABLE = False
    PLOT_THREAD_DETECTION_AVAILABLE = False
    RELATIONSHIP_ANALYSIS_AVAILABLE = False
    KNOWLEDGE_EXTRACTION_AVAILABLE = False
    CONTRADICTION_SYNTHESIS_AVAILABLE = False
    class ResponseAnalyzerAgent: pass
    class TimeTrackingAgent: pass
    class MemoryCreationAgent: pass
    class PlotThreadDetectionAgent: pass
    class RelationshipAnalysisAgent: pass
    class KnowledgeExtractionAgent: pass
    class ContradictionSynthesisAgent: pass

# Determine if any agents are available
AGENTS_AVAILABLE = (
    RESPONSE_ANALYZER_AVAILABLE or
    TIME_TRACKING_AVAILABLE or
    MEMORY_CREATION_AVAILABLE or
    PLOT_THREAD_DETECTION_AVAILABLE or
    RELATIONSHIP_ANALYSIS_AVAILABLE or
    KNOWLEDGE_EXTRACTION_AVAILABLE or
    CONTRADICTION_SYNTHESIS_AVAILABLE
)


class BackgroundAgentStrategy:
    """Execute background agents for post-response analysis.

    Background agents analyze the Claude response and extract information
    like memories, relationships, plot threads, and knowledge for future use.

    Refactored agent types:
    - response_analyzer: Scene classification and pacing analysis (✓ Refactored)
    - time_tracking: Track narrative time progression (✓ Refactored)
    - memory_creation: Extract memorable moments (✓ Refactored)
    - relationship_analysis: Analyze character dynamics (✓ Refactored)
    - plot_thread_detection: Detect plot changes (✓ Refactored)
    - knowledge_extraction: Extract world-building facts (✓ Refactored)
    - contradiction_synthesis: Detect inconsistencies & synthesize explanations (✓ Refactored)
    """

    def __init__(
        self,
        *,
        logger: LoggingService,
        max_workers: int = 4,
        enabled_agents: dict[str, bool] | None = None,
        rp_dir: Any = None,
        bridge: Any = None,
    ) -> None:
        """Initialize background agent strategy.

        Args:
            logger: Logging service for diagnostics
            max_workers: Maximum concurrent agents
            enabled_agents: Dict mapping agent IDs to enabled status
            rp_dir: RP directory path for agent instantiation
            bridge: Bridge service for agent LLM access
        """
        self._logger = logger
        self._max_workers = max_workers
        self._enabled_agents = enabled_agents or {}
        self._rp_dir = rp_dir
        self._bridge = bridge

    def create_context(self, context: AutomationContext) -> AgentContext:
        """Create agent context from automation context.

        Background agents need:
        - response_number: For tracking/naming output files
        - loaded_entities: Characters mentioned in the response
        - chapter: Current chapter for context
        - previous_scenes: Recent scene history

        Args:
            context: The automation context

        Returns:
            Agent context suitable for background processing
        """
        return AgentContext(
            message=context.message,
            response_number=context.response_count,
            loaded_entities=context.loaded_entities,
            characters_in_scene=[],  # Extracted from response, not message
            chapter=None,  # TODO: Extract from session state when available
            previous_scenes=[],  # TODO: Load from session history
        )

    def execute(
        self,
        agent_context: AgentContext,
        prompt: str,
        automation_context: Any = None,
    ) -> AutomationResult:
        """Execute background agents concurrently (pre-response placeholder).

        Args:
            agent_context: Context for agent execution
            prompt: The full prompt sent to Claude (including enhanced context)
            automation_context: Full automation context (unused by this strategy)

        Returns:
            AutomationResult with success status

        Note:
            This method is called during pre-response automation phase but does nothing.
            Background agents should be executed via execute_post_response() AFTER
            Claude responds, as they need the response content to analyze.
        """
        # Background agents need Claude's response, so we skip execution here
        # They will be executed via execute_post_response() after Claude responds
        return AutomationResult(success=True, enhanced_prompt=prompt)

    def execute_post_response(
        self,
        user_message: str,
        claude_response: str,
        message_number: int,
        rp_dir: Any = None,
    ) -> dict[str, dict]:
        """Execute background agents after Claude responds.

        Args:
            user_message: The user's original message
            claude_response: Claude's generated response
            message_number: Current message/response number
            rp_dir: RP directory path (uses self._rp_dir if not provided)

        Returns:
            Dict mapping agent_id to result dict with success, content, duration, etc.

        Note:
            This is the primary execution path for background agents.
        """
        if not AGENTS_AVAILABLE:
            self._logger.warning(
                "background_agents.unavailable",
                context={"reason": "Agents not imported"},
            )
            return {}

        self._logger.info(
            "background_agents.post_response.start",
            context={
                "message_number": message_number,
                "enabled_count": sum(1 for v in self._enabled_agents.values() if v),
            },
        )

        # Create minimal agent context for filtering
        agent_context = AgentContext(
            message=user_message,
            response_number=message_number,
        )

        # Prepare agent tasks based on configuration
        agent_tasks = self._prepare_agent_tasks_simple()

        if not agent_tasks:
            self._logger.debug(
                "background_agents.none_enabled",
                context={"message_number": message_number},
            )
            return {}

        # Use rp_dir from initialization or parameter
        final_rp_dir = rp_dir or self._rp_dir
        if not final_rp_dir:
            self._logger.error("background_agents.missing_rp_dir")
            return {}

        # Execute agents concurrently with response
        results = self._execute_agents_with_response(
            agent_tasks, user_message, claude_response, message_number, final_rp_dir
        )

        success_count = sum(1 for r in results.values() if r.get("success", False))
        self._logger.info(
            "background_agents.post_response.complete",
            context={
                "total": len(agent_tasks),
                "successful": success_count,
                "failed": len(agent_tasks) - success_count,
            },
        )

        return results

    def _prepare_agent_tasks_simple(self) -> list[tuple[str, type]]:
        """Prepare list of enabled agents (simplified for post-response).

        Returns:
            List of (agent_id, agent_class) tuples
        """
        available_agents = {}

        # Add refactored agents
        if RESPONSE_ANALYZER_AVAILABLE:
            available_agents["response_analyzer"] = ResponseAnalyzerAgent
        if TIME_TRACKING_AVAILABLE:
            available_agents["time_tracking"] = TimeTrackingAgent
        if MEMORY_CREATION_AVAILABLE:
            available_agents["memory_creation"] = MemoryCreationAgent
        if PLOT_THREAD_DETECTION_AVAILABLE:
            available_agents["plot_thread_detection"] = PlotThreadDetectionAgent
        if RELATIONSHIP_ANALYSIS_AVAILABLE:
            available_agents["relationship_analysis"] = RelationshipAnalysisAgent
        if KNOWLEDGE_EXTRACTION_AVAILABLE:
            available_agents["knowledge_extraction"] = KnowledgeExtractionAgent
        if CONTRADICTION_SYNTHESIS_AVAILABLE:
            available_agents["contradiction_synthesis"] = ContradictionSynthesisAgent

        if not available_agents:
            return []

        tasks = []
        for agent_id, agent_class in available_agents.items():
            if self._enabled_agents.get(agent_id, False):
                tasks.append((agent_id, agent_class))

        return tasks

    def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type]]:
        """Prepare list of agents to execute based on configuration (legacy).

        Args:
            agent_context: Context for filtering agents

        Returns:
            List of (agent_id, agent_class) tuples
        """
        # For backwards compatibility - just return empty list
        # Background agents use execute_post_response() now
        return []

    def _execute_agents_concurrent(
        self, agent_tasks: list[tuple[str, type]], agent_context: AgentContext, rp_dir
    ) -> dict[str, dict[str, any]]:
        """Execute agents concurrently using thread pool.

        Args:
            agent_tasks: List of (agent_id, agent_class) tuples
            agent_context: Context for agent execution
            rp_dir: RP directory path for agent instantiation

        Returns:
            Dict mapping agent_id to result dict
        """
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all agent tasks
            future_to_agent = {}
            for agent_id, agent_class in agent_tasks:
                future = executor.submit(
                    self._execute_single_agent, agent_id, agent_class, agent_context, rp_dir
                )
                future_to_agent[future] = agent_id

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_id] = result
                except Exception as exc:
                    self._logger.exception(
                        "background_agent.execution_error",
                        context={"agent_id": agent_id},
                        exc=exc,
                    )
                    results[agent_id] = {"success": False, "error": str(exc)}

        return results

    def _execute_agents_with_response(
        self,
        agent_tasks: list[tuple[str, type]],
        user_message: str,
        claude_response: str,
        message_number: int,
        rp_dir: Any
    ) -> dict[str, dict]:
        """Execute agents concurrently with Claude's response.

        Args:
            agent_tasks: List of (agent_id, agent_class) tuples
            user_message: User's original message
            claude_response: Claude's generated response
            message_number: Current message number
            rp_dir: RP directory path

        Returns:
            Dict mapping agent_id to result dict
        """
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all agent tasks
            future_to_agent = {}
            for agent_id, agent_class in agent_tasks:
                future = executor.submit(
                    self._execute_single_agent_with_response,
                    agent_id,
                    agent_class,
                    user_message,
                    claude_response,
                    message_number,
                    rp_dir
                )
                future_to_agent[future] = agent_id

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_id] = result
                except Exception as exc:
                    self._logger.exception(
                        "background_agent.execution_error",
                        context={"agent_id": agent_id},
                        exc=exc,
                    )
                    results[agent_id] = {"success": False, "error": str(exc)}

        return results

    def _execute_single_agent_with_response(
        self,
        agent_id: str,
        agent_class: type,
        user_message: str,
        claude_response: str,
        message_number: int,
        rp_dir: Any
    ) -> dict:
        """Execute a single background agent with Claude's response.

        Args:
            agent_id: Agent identifier
            agent_class: Agent class to instantiate
            user_message: User's original message
            claude_response: Claude's generated response
            message_number: Current message number
            rp_dir: RP directory path

        Returns:
            Result dict with success, content, duration, etc.
        """
        start_time = time.perf_counter()

        try:
            self._logger.debug("background_agent.start", context={"agent_id": agent_id})

            # Instantiate agent with rp_dir and bridge for LLM access
            agent = agent_class(rp_dir=rp_dir, log_file=None, bridge=self._bridge)

            # Call agent.execute() with user message, message number, and Claude's response
            result_text = agent.execute(
                user_message=user_message,
                message_number=message_number,
                claude_response=claude_response  # ← KEY: Pass Claude's response!
            )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            self._logger.debug(
                "background_agent.complete",
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
                "background_agent.error",
                context={"agent_id": agent_id, "duration_ms": duration_ms},
                exc=exc,
            )
            return {
                "success": False,
                "agent_id": agent_id,
                "duration_ms": duration_ms,
                "error": str(exc),
            }

    def _execute_single_agent(
        self, agent_id: str, agent_class: type, agent_context: AgentContext, rp_dir
    ) -> dict[str, any]:
        """Execute a single background agent.

        Args:
            agent_id: Agent identifier
            agent_class: Agent class to instantiate
            agent_context: Context for execution
            rp_dir: RP directory path

        Returns:
            Result dict with success, content, duration, etc.
        """
        start_time = time.perf_counter()

        try:
            self._logger.debug("background_agent.start", context={"agent_id": agent_id})

            # Instantiate agent with rp_dir and bridge for LLM access
            agent = agent_class(rp_dir=rp_dir, log_file=None, bridge=self._bridge)

            # Call agent.execute() with user message and response number
            # BaseAgent.execute() accepts *args/**kwargs that are passed to gather_data()
            result_text = agent.execute(
                user_message=agent_context.message,
                message_number=agent_context.response_number
            )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            self._logger.debug(
                "background_agent.complete",
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
                "background_agent.error",
                context={"agent_id": agent_id, "duration_ms": duration_ms},
                exc=exc,
            )
            return {
                "success": False,
                "agent_id": agent_id,
                "duration_ms": duration_ms,
                "error": str(exc),
            }
