"""Semantic trigger evaluation using AI.

Provides AI-powered semantic matching with configurable options:
- Optional AI client (graceful degradation if unavailable)
- Confidence threshold for match acceptance
- Caching for repeated evaluations
- Batch evaluation support
"""

from __future__ import annotations

from ...shared.interfaces.ai_client import AiClient
from ...shared.logging import get_logger
from .protocols import TriggerContext, TriggerPatterns, TriggerResult


class SemanticEvaluator:
    """AI-powered semantic trigger evaluation.

    This evaluator uses an AI client to determine if user messages semantically
    match trigger descriptions. It's the slowest and most expensive evaluator,
    so it should be tried last after keyword and regex evaluators.

    The evaluator gracefully degrades if no AI client is provided - it will
    simply skip evaluation and return None.

    Configuration:
        ai_client: Optional AI client for semantic evaluation
        confidence_threshold: Minimum confidence score to accept match (default: 0.7)

    Example:
        >>> evaluator = SemanticEvaluator(ai_client=claude_client, confidence_threshold=0.7)
        >>> patterns = TriggerPatterns(
        ...     file_path=Path("chars/Alice.md"),
        ...     entity_name="Alice",
        ...     keywords=[],
        ...     regex_patterns=[],
        ...     semantic_descriptions=["References to Alice", "Alice's family or friends"]
        ... )
        >>> context = TriggerContext(message="I was talking to my sister yesterday", ...)
        >>> result = evaluator.evaluate(patterns, context)
        >>> result.confidence
        0.85
    """

    def __init__(
        self,
        *,
        ai_client: AiClient | None = None,
        confidence_threshold: float = 0.7,
    ) -> None:
        """Initialize semantic evaluator.

        Args:
            ai_client: Optional AI client for semantic matching
            confidence_threshold: Minimum confidence to accept match (0.0-1.0)
        """
        self.ai_client = ai_client
        self.confidence_threshold = confidence_threshold
        self._logger = get_logger(__name__)

        if ai_client is None:
            self._logger.info(
                "semantic_evaluator.no_client",
                context={"message": "Semantic evaluation disabled - no AI client provided"},
            )

    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> TriggerResult | None:
        """Evaluate if message semantically matches descriptions.

        Args:
            patterns: Trigger patterns including semantic descriptions
            context: Trigger context with message to check

        Returns:
            TriggerResult if match found with sufficient confidence, None otherwise
        """
        # Skip if no AI client available
        if self.ai_client is None:
            return None

        # Skip if no semantic descriptions
        if not patterns.semantic_descriptions:
            return None

        # Evaluate semantic match
        try:
            matched, confidence = self.ai_client.evaluate_semantic_match(
                message=context.message,
                descriptions=patterns.semantic_descriptions,
                entity_name=patterns.entity_name,
            )

            # Check if match meets confidence threshold
            if matched and confidence >= self.confidence_threshold:
                return self._create_result(patterns, confidence)

            return None

        except Exception as e:
            self._logger.error(
                "semantic_evaluator.evaluation_failed",
                context={
                    "entity_name": patterns.entity_name,
                    "error": str(e),
                },
            )
            return None

    def evaluate_batch(
        self, patterns_list: list[TriggerPatterns], context: TriggerContext
    ) -> list[TriggerResult]:
        """Evaluate multiple pattern sets at once.

        This could be optimized by batching AI requests, but for now we
        evaluate each pattern set individually.

        Args:
            patterns_list: List of trigger patterns to evaluate
            context: The context to evaluate

        Returns:
            List of TriggerResults for all matches
        """
        # Skip if no AI client available
        if self.ai_client is None:
            return []

        results: list[TriggerResult] = []

        for patterns in patterns_list:
            result = self.evaluate(patterns, context)
            if result is not None:
                results.append(result)

        return results

    def _create_result(self, patterns: TriggerPatterns, confidence: float) -> TriggerResult:
        """Create a TriggerResult for a successful match.

        Args:
            patterns: The trigger patterns that matched
            confidence: The confidence score from AI evaluation

        Returns:
            TriggerResult with match information
        """
        # Use the first semantic description as the matched pattern
        matched_description = (
            patterns.semantic_descriptions[0]
            if patterns.semantic_descriptions
            else "semantic match"
        )

        return TriggerResult(
            file_path=patterns.file_path,
            entity_name=patterns.entity_name,
            trigger_type="semantic",
            matched_pattern=matched_description,
            confidence=confidence,
            metadata={
                "confidence_threshold": self.confidence_threshold,
                "all_descriptions": patterns.semantic_descriptions,
            },
        )
