"""Fallback trigger system strategy for legacy compatibility.

The trigger system is the original context-gathering mechanism that detects
keywords and patterns in messages to determine what context should be loaded.
It serves as a fallback when agents are disabled or unavailable.
"""

from __future__ import annotations

from pathlib import Path

from ...shared.interfaces import ConfigService, LoggingService
from ..contracts import AgentContext, AutomationContext, AutomationResult
from ..triggers import (
    FrequencyTracker,
    PatternLoader,
    TriggerContext,
    TriggerCoordinator,
    TriggerRegistry,
    TriggerResult,
)


class FallbackTriggerStrategy:
    """Execute trigger system as fallback for agent strategies.

    The trigger system evaluates patterns in the user message to determine
    what additional context should be loaded. It's simpler and faster than
    agents but less intelligent.

    Trigger types:
    - Keyword: Fast exact word matching
    - Regex: Pattern-based matching
    - Semantic: AI-powered semantic understanding (optional)

    Features:
    - Pattern loading from entity files
    - Frequency tracking for auto-escalation
    - Result deduplication and ranking
    """

    def __init__(
        self,
        *,
        logger: LoggingService,
        config_service: ConfigService,
        use_trigger_system: bool = True,
    ) -> None:
        """Initialize fallback trigger strategy.

        Args:
            logger: Logging service for diagnostics
            config_service: Configuration service
            use_trigger_system: Whether trigger system is enabled
        """
        self._logger = logger
        self._config = config_service
        self._use_trigger_system = use_trigger_system

        # Initialize trigger components
        if use_trigger_system:
            self._pattern_loader = PatternLoader()
            self._trigger_registry = TriggerRegistry(config_service)
            evaluators = self._trigger_registry.create_evaluators()
            self._trigger_coordinator = TriggerCoordinator(evaluators)
        else:
            self._pattern_loader = None
            self._trigger_coordinator = None

    def create_context(self, context: AutomationContext) -> AgentContext:
        """Create agent context from automation context.

        Args:
            context: The automation context

        Returns:
            Agent context suitable for trigger evaluation
        """
        return AgentContext(
            message=context.message,
            response_number=context.response_count,
            loaded_entities=context.loaded_entities,
            characters_in_scene=[],  # Triggers don't need this
            chapter=None,
            previous_scenes=[],
        )

    def execute(
        self,
        agent_context: AgentContext,
        prompt: str,
        automation_context: AutomationContext,
    ) -> AutomationResult:
        """Execute trigger evaluation and enhance prompt if needed.

        Args:
            agent_context: Context for trigger evaluation
            prompt: The current prompt
            automation_context: Full automation context with rp_dir

        Returns:
            AutomationResult with potentially enhanced prompt and triggered files
        """
        if not self._use_trigger_system:
            self._logger.debug(
                "trigger_system.disabled",
                context={"response_number": agent_context.response_number},
            )
            return AutomationResult(success=True, enhanced_prompt=prompt)

        self._logger.info(
            "trigger_system.start",
            context={"response_number": agent_context.response_number},
        )

        # Evaluate triggers using the trigger system
        triggered_results, triggered_context = self._evaluate_triggers(
            agent_context, automation_context
        )

        if triggered_results:
            # Track frequency for auto-escalation (if enabled)
            escalated_files = self._track_frequency(triggered_results, automation_context.rp_dir)

            # Inject triggered context into prompt
            enhanced_prompt = self._inject_triggered_context(prompt, triggered_context)

            self._logger.info(
                "trigger_system.triggered",
                context={
                    "response_number": agent_context.response_number,
                    "triggered_count": len(triggered_results),
                    "triggered_entities": [r.entity_name for r in triggered_results],
                    "escalated_count": len(escalated_files),
                    "context_length": len(triggered_context),
                },
            )

            # Return with triggered file paths for tier3_files tracking
            triggered_paths = [r.file_path for r in triggered_results]

            return AutomationResult(
                success=True,
                enhanced_prompt=enhanced_prompt,
                cached_context=triggered_context,
            )

        self._logger.debug(
            "trigger_system.no_triggers",
            context={"response_number": agent_context.response_number},
        )
        return AutomationResult(success=True, enhanced_prompt=prompt)

    def _evaluate_triggers(
        self, agent_context: AgentContext, automation_context: AutomationContext
    ) -> tuple[list[TriggerResult], str]:
        """Evaluate triggers in the message and gather context.

        Args:
            agent_context: Context for trigger evaluation
            automation_context: Full automation context

        Returns:
            Tuple of (triggered_results, formatted_context_string)
        """
        # Load all trigger patterns from entity files
        patterns_list = self._pattern_loader.load_all_patterns(automation_context.rp_dir)

        if not patterns_list:
            self._logger.debug(
                "trigger_system.no_patterns",
                context={"rp_dir": str(automation_context.rp_dir)},
            )
            return ([], "")

        # Build trigger context
        trigger_context = TriggerContext(
            message=agent_context.message,
            loaded_entities=agent_context.loaded_entities,
            response_count=agent_context.response_number,
            rp_dir=automation_context.rp_dir,
            previous_triggers=automation_context.tier3_files,  # Filter recently triggered
        )

        # Evaluate triggers
        triggered_results = self._trigger_coordinator.evaluate_triggers(
            patterns_list, trigger_context
        )

        if not triggered_results:
            return ([], "")

        # Format triggered context for injection
        formatted_context = self._format_triggered_results(triggered_results)

        return (triggered_results, formatted_context)

    def _format_triggered_results(self, results: list[TriggerResult]) -> str:
        """Format trigger results into context string.

        Args:
            results: List of trigger results

        Returns:
            Formatted context string
        """
        if not results:
            return ""

        sections: list[str] = []
        sections.append("<!-- ========== TRIGGERED CONTEXT ========== -->")

        for result in results:
            sections.append(f"<!-- Trigger: {result.entity_name} -->")
            sections.append(f"<!-- Type: {result.trigger_type} -->")
            sections.append(f"<!-- Pattern: {result.matched_pattern} -->")

            # Load the entity file content
            try:
                content = result.file_path.read_text(encoding="utf-8")
                sections.append(f"\n{content}\n")
            except Exception as e:
                self._logger.warning(
                    "trigger_system.file_read_error",
                    context={
                        "file_path": str(result.file_path),
                        "error": str(e),
                    },
                )
                sections.append(f"<!-- Error loading {result.entity_name} -->")

        sections.append("<!-- ========================================= -->")

        return "\n".join(sections)

    def _track_frequency(self, triggered_results: list[TriggerResult], rp_dir: Path) -> list[Path]:
        """Track trigger frequency and identify files for escalation.

        Args:
            triggered_results: Triggered files from this response
            rp_dir: RP directory path

        Returns:
            List of files to escalate to TIER_2
        """
        # Check if frequency tracking is enabled
        if not self._config.get_bool("triggers.frequency_tracking.enabled", default=True):
            return []

        # Initialize frequency tracker
        history_file = rp_dir / "state" / "trigger_history.json"
        window_size = self._config.get_int("triggers.frequency_tracking.window_size", default=10)
        threshold = self._config.get_int(
            "triggers.frequency_tracking.escalation_threshold", default=3
        )

        tracker = FrequencyTracker(
            history_file, window_size=window_size, escalation_threshold=threshold
        )

        # Track triggered files
        triggered_paths = [r.file_path for r in triggered_results]
        escalated_files = tracker.track_and_escalate(triggered_paths)

        return escalated_files

    def _inject_triggered_context(self, prompt: str, triggered_context: str) -> str:
        """Inject triggered context into the prompt.

        Args:
            prompt: Original prompt
            triggered_context: Context from trigger evaluation

        Returns:
            Enhanced prompt with triggered context
        """
        # Inject before the user message section
        user_message_marker = "========== USER MESSAGE =========="
        if user_message_marker in prompt:
            parts = prompt.split(user_message_marker, 1)
            return (
                f"{parts[0]}\n\n"
                f"<!-- TRIGGERED CONTEXT -->\n{triggered_context}\n\n"
                f"{user_message_marker}{parts[1]}"
            )

        # If no marker found, append at end
        return f"{prompt}\n\n<!-- TRIGGERED CONTEXT -->\n{triggered_context}"
