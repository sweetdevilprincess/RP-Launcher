"""Trigger evaluation protocols and data structures.

This module defines the core abstractions for trigger evaluation:
- TriggerContext: Input data for trigger evaluation
- TriggerResult: Output from trigger evaluation
- TriggerEvaluator: Protocol for trigger evaluation strategies
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TriggerContext:
    """Context information provided to trigger evaluators.

    This is the input data that evaluators use to determine if triggers match.

    Attributes:
        message: The user's message text to evaluate
        loaded_entities: List of entity names already loaded (Tier 1/2)
        response_count: Current response number (for context)
        rp_dir: RP directory path (for file discovery)
        previous_triggers: Recently triggered files (for deduplication)
    """

    message: str
    loaded_entities: list[str]
    response_count: int
    rp_dir: Path
    previous_triggers: list[Path] | None = None

    @property
    def message_lower(self) -> str:
        """Lowercase version of message for case-insensitive matching."""
        return self.message.lower()


@dataclass(frozen=True)
class TriggerResult:
    """Result of trigger evaluation.

    This represents a successful trigger match and the file that should be loaded.

    Attributes:
        file_path: Path to the file that was triggered
        entity_name: Name of the entity (extracted from filename)
        trigger_type: Type of trigger that matched (keyword, regex, semantic)
        matched_pattern: The specific pattern/keyword that matched
        confidence: Confidence score (1.0 for keyword/regex, 0.0-1.0 for semantic)
        metadata: Optional additional information about the match
    """

    file_path: Path
    entity_name: str
    trigger_type: str
    matched_pattern: str
    confidence: float = 1.0
    metadata: dict | None = None

    def __post_init__(self):
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass(frozen=True)
class TriggerPatterns:
    """Collection of trigger patterns for a file.

    This represents the patterns that can trigger loading a specific file.

    Attributes:
        file_path: Path to the file these patterns belong to
        entity_name: Name of the entity
        keywords: List of keyword patterns (case-insensitive by default)
        regex_patterns: List of regex pattern strings
        semantic_descriptions: List of semantic descriptions (for AI matching)
        metadata: Optional metadata (priority, category, etc.)
    """

    file_path: Path
    entity_name: str
    keywords: list[str]
    regex_patterns: list[str]
    semantic_descriptions: list[str]
    metadata: dict | None = None


class TriggerEvaluator(Protocol):
    """Protocol for trigger evaluation strategies.

    Implementations provide different matching strategies:
    - KeywordEvaluator: Fast keyword matching
    - RegexEvaluator: Pattern-based matching
    - SemanticEvaluator: AI-powered semantic matching
    """

    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> TriggerResult | None:
        """Evaluate if patterns match the context.

        Args:
            patterns: The trigger patterns to match against
            context: The context to evaluate

        Returns:
            TriggerResult if match found, None otherwise
        """
        ...

    def evaluate_batch(
        self, patterns_list: list[TriggerPatterns], context: TriggerContext
    ) -> list[TriggerResult]:
        """Evaluate multiple pattern sets at once (optional optimization).

        Args:
            patterns_list: List of trigger patterns to evaluate
            context: The context to evaluate

        Returns:
            List of TriggerResults for all matches
        """
        ...
