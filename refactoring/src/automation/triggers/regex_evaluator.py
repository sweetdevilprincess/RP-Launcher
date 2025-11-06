"""Regex-based trigger evaluation.

Provides pattern-based matching with configurable options:
- Compiled pattern caching for performance
- Graceful handling of invalid regex patterns
- Configurable max patterns per file
- Multiple pattern support per file
"""

from __future__ import annotations

import re

from ...shared.logging import get_logger
from .protocols import TriggerContext, TriggerPatterns, TriggerResult


class RegexEvaluator:
    r"""Pattern-based trigger evaluation using regular expressions.

    This evaluator uses regex patterns to match against user messages.
    It's more flexible than keyword matching but slower, so it should
    be tried after KeywordEvaluator.

    Configuration:
        case_sensitive: Whether patterns match case exactly (default: False)
        max_patterns_per_file: Maximum regex patterns allowed per file (default: 10)

    Example:
        >>> evaluator = RegexEvaluator(case_sensitive=False)
        >>> patterns = TriggerPatterns(
        ...     file_path=Path("chars/Alice.md"),
        ...     entity_name="Alice",
        ...     keywords=[],
        ...     regex_patterns=[r"alice['']s? \w+", r"talk(ing|ed)? (?:to|with) alice"],
        ...     semantic_descriptions=[]
        ... )
        >>> context = TriggerContext(message="I was talking to Alice yesterday", ...)
        >>> result = evaluator.evaluate(patterns, context)
        >>> result.matched_pattern
        "talk(ing|ed)? (?:to|with) alice"
    """

    def __init__(self, *, case_sensitive: bool = False, max_patterns_per_file: int = 10) -> None:
        """Initialize regex evaluator.

        Args:
            case_sensitive: Whether regex matching is case-sensitive
            max_patterns_per_file: Maximum patterns allowed per file
        """
        self.case_sensitive = case_sensitive
        self.max_patterns_per_file = max_patterns_per_file
        self._pattern_cache: dict[str, re.Pattern | None] = {}
        self._logger = get_logger(__name__)

    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> TriggerResult | None:
        """Evaluate if any regex patterns match the message.

        Args:
            patterns: Trigger patterns including regex patterns
            context: Trigger context with message to check

        Returns:
            TriggerResult if match found, None otherwise
        """
        if not patterns.regex_patterns:
            return None

        # Limit patterns per file
        patterns_to_check = patterns.regex_patterns[: self.max_patterns_per_file]
        if len(patterns.regex_patterns) > self.max_patterns_per_file:
            self._logger.warning(
                "regex_evaluator.pattern_limit_exceeded",
                context={
                    "file_path": str(patterns.file_path),
                    "pattern_count": len(patterns.regex_patterns),
                    "max_allowed": self.max_patterns_per_file,
                },
            )

        # Try each pattern
        for pattern_str in patterns_to_check:
            compiled = self._get_compiled_pattern(pattern_str)
            if compiled is None:
                # Invalid pattern, skip it
                continue

            # Check if pattern matches
            if compiled.search(context.message):
                return self._create_result(patterns, pattern_str)

        return None

    def evaluate_batch(
        self, patterns_list: list[TriggerPatterns], context: TriggerContext
    ) -> list[TriggerResult]:
        """Evaluate multiple pattern sets at once.

        This is an optimization opportunity - we can compile all patterns
        once and scan the message with all of them.

        Args:
            patterns_list: List of trigger patterns to evaluate
            context: The context to evaluate

        Returns:
            List of TriggerResults for all matches
        """
        results: list[TriggerResult] = []

        # Build a map of compiled patterns to their original patterns
        pattern_map: dict[re.Pattern, tuple[TriggerPatterns, str]] = {}
        for patterns in patterns_list:
            patterns_to_check = patterns.regex_patterns[: self.max_patterns_per_file]

            for pattern_str in patterns_to_check:
                compiled = self._get_compiled_pattern(pattern_str)
                if compiled is not None:
                    pattern_map[compiled] = (patterns, pattern_str)

        # Check each pattern once
        for compiled, (patterns, pattern_str) in pattern_map.items():
            if compiled.search(context.message):
                results.append(self._create_result(patterns, pattern_str))

        return results

    def _get_compiled_pattern(self, pattern_str: str) -> re.Pattern | None:
        """Get or compile a regex pattern.

        Args:
            pattern_str: The regex pattern string

        Returns:
            Compiled pattern, or None if invalid
        """
        # Check cache first
        if pattern_str in self._pattern_cache:
            return self._pattern_cache[pattern_str]

        # Try to compile
        try:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            compiled = re.compile(pattern_str, flags)
            self._pattern_cache[pattern_str] = compiled
            return compiled
        except re.error as e:
            # Invalid regex pattern
            self._logger.warning(
                "regex_evaluator.invalid_pattern",
                context={"pattern": pattern_str, "error": str(e)},
            )
            # Cache the failure so we don't try again
            self._pattern_cache[pattern_str] = None
            return None

    def _create_result(self, patterns: TriggerPatterns, matched_pattern: str) -> TriggerResult:
        """Create a TriggerResult for a successful match.

        Args:
            patterns: The trigger patterns that matched
            matched_pattern: The specific regex pattern that matched

        Returns:
            TriggerResult with match information
        """
        return TriggerResult(
            file_path=patterns.file_path,
            entity_name=patterns.entity_name,
            trigger_type="regex",
            matched_pattern=matched_pattern,
            confidence=1.0,  # Regex matches are absolute
            metadata={
                "case_sensitive": self.case_sensitive,
            },
        )
