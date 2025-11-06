"""Trigger coordinator for orchestrating evaluation.

Coordinates evaluation across multiple evaluators and manages:
- Pattern loading and caching
- Evaluator orchestration
- Result deduplication and ranking
- Optional frequency tracking for auto-escalation

Refactored from src/trigger_system/trigger_system.py
"""

from __future__ import annotations

from ...shared.logging import get_logger
from .protocols import TriggerContext, TriggerEvaluator, TriggerPatterns, TriggerResult


class TriggerCoordinator:
    """Coordinates trigger evaluation across multiple evaluators.

    This coordinator:
    1. Manages a list of trigger evaluators (keyword, regex, semantic)
    2. Evaluates triggers for a given context
    3. Tries evaluators in order (keyword -> regex -> semantic) for performance
    4. Deduplicates results (same file can't trigger multiple times)
    5. Ranks results by confidence and trigger type
    6. Filters recently triggered files to avoid repetition

    Example:
        >>> evaluators = registry.create_evaluators()
        >>> coordinator = TriggerCoordinator(evaluators)
        >>> patterns_list = pattern_loader.load_all_patterns(rp_dir)
        >>> context = TriggerContext(message="Alice walked in", ...)
        >>> results = coordinator.evaluate_triggers(patterns_list, context)
    """

    def __init__(
        self,
        evaluators: list[TriggerEvaluator],
        *,
        max_results: int = 10,
    ) -> None:
        """Initialize trigger coordinator.

        Args:
            evaluators: List of trigger evaluators to use (in priority order)
            max_results: Maximum number of results to return
        """
        self._evaluators = evaluators
        self._max_results = max_results
        self._logger = get_logger(__name__)

    def evaluate_triggers(
        self,
        patterns_list: list[TriggerPatterns],
        context: TriggerContext,
    ) -> list[TriggerResult]:
        """Evaluate triggers for the given context.

        This method:
        1. For each pattern file, tries evaluators in order (stops at first match)
        2. Filters out recently triggered files
        3. Ranks results by confidence and type
        4. Limits to max_results

        Args:
            patterns_list: List of trigger patterns to evaluate
            context: The context to evaluate against

        Returns:
            List of TriggerResults, ranked and deduplicated
        """
        # Evaluate each pattern file with the first matching evaluator
        all_results: list[TriggerResult] = []

        for patterns in patterns_list:
            # Try each evaluator in order (keyword -> regex -> semantic)
            # Stop at first match for this file (performance optimization)
            for evaluator in self._evaluators:
                result = evaluator.evaluate(patterns, context)
                if result is not None:
                    all_results.append(result)
                    self._logger.debug(
                        "trigger_coordinator.match_found",
                        context={
                            "evaluator": type(evaluator).__name__,
                            "entity": patterns.entity_name,
                            "trigger_type": result.trigger_type,
                            "pattern": result.matched_pattern,
                        },
                    )
                    break  # Found a match, don't try other evaluators for this file

        # Filter out recently triggered files
        filtered_results = self._filter_recent_triggers(all_results, context)

        # Rank results (keyword > regex > semantic, then by confidence)
        ranked = self._rank_results(filtered_results)

        # Limit to max results
        final_results = ranked[: self._max_results]

        self._logger.info(
            "trigger_coordinator.evaluation_complete",
            context={
                "total_matches": len(all_results),
                "after_filtering": len(filtered_results),
                "final_count": len(final_results),
                "triggered_entities": [r.entity_name for r in final_results],
            },
        )

        return final_results

    def _filter_recent_triggers(
        self, results: list[TriggerResult], context: TriggerContext
    ) -> list[TriggerResult]:
        """Filter out files that were recently triggered.

        Args:
            results: Results to filter
            context: Context containing recently triggered files

        Returns:
            Filtered results
        """
        if not context.previous_triggers:
            return results

        # Create set of recent trigger paths for fast lookup
        recent_paths = set(context.previous_triggers)

        # Filter out recent triggers
        filtered = [r for r in results if r.file_path not in recent_paths]

        if len(filtered) < len(results):
            filtered_count = len(results) - len(filtered)
            self._logger.debug(
                "trigger_coordinator.recent_triggers_filtered",
                context={
                    "filtered_count": filtered_count,
                    "recent_trigger_count": len(recent_paths),
                },
            )

        return filtered

    def _rank_results(self, results: list[TriggerResult]) -> list[TriggerResult]:
        """Rank results by confidence and trigger type priority.

        Ranking priority:
        1. Keyword matches (most reliable, confidence=1.0)
        2. Regex matches (reliable, confidence=1.0)
        3. Semantic matches (variable confidence 0.0-1.0)

        Within same type, higher confidence wins.

        Args:
            results: Results to rank

        Returns:
            Ranked results (highest priority first)
        """
        # Define type priority (lower number = higher priority)
        type_priority = {"keyword": 1, "regex": 2, "semantic": 3}

        # Sort by type priority first, then by confidence (descending)
        ranked = sorted(
            results,
            key=lambda r: (type_priority.get(r.trigger_type, 99), -r.confidence),
        )

        return ranked
