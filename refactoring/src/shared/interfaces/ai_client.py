"""AI client protocol for semantic evaluation.

This module defines the protocol for AI clients used in semantic trigger evaluation.
Implementations can use different backends (Claude API, local models, etc.).
"""

from __future__ import annotations

from typing import Protocol


class AiClient(Protocol):
    """Protocol for AI clients used in semantic evaluation.

    This protocol defines the interface for making AI requests for semantic
    matching. Different implementations can use different backends:
    - Claude API via Anthropic SDK
    - Local models (llama, etc.)
    - Mock implementations for testing
    """

    def evaluate_semantic_match(
        self, message: str, descriptions: list[str], entity_name: str
    ) -> tuple[bool, float]:
        """Evaluate if a message semantically matches any descriptions.

        Args:
            message: The user's message to evaluate
            descriptions: List of semantic descriptions to match against
            entity_name: Name of the entity being evaluated

        Returns:
            Tuple of (matched: bool, confidence: float)
            - matched: True if any description matches
            - confidence: Score from 0.0 to 1.0 indicating match strength

        Example:
            >>> client = ClaudeAiClient(api_key="...")
            >>> matched, confidence = client.evaluate_semantic_match(
            ...     message="I was talking to my sister yesterday",
            ...     descriptions=["References to Alice", "Alice's family members"],
            ...     entity_name="Alice"
            ... )
            >>> matched, confidence
            (True, 0.85)
        """
        ...
