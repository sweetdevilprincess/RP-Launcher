"""Keyword-based trigger evaluation.

Provides fast, simple keyword matching with configurable options:
- Case-sensitive or case-insensitive matching
- Word boundary enforcement
- Multiple keyword support per file
"""

from __future__ import annotations

import re

from .protocols import TriggerContext, TriggerPatterns, TriggerResult


class KeywordEvaluator:
    """Fast keyword-based trigger evaluation.

    This evaluator uses simple string matching to determine if keywords
    appear in the user's message. It's the fastest trigger type and should
    be tried first before more expensive evaluators.

    Configuration:
        case_sensitive: Whether to match case exactly (default: False)
        use_word_boundaries: Require word boundaries around keywords (default: True)

    Example:
        >>> evaluator = KeywordEvaluator(case_sensitive=False, use_word_boundaries=True)
        >>> patterns = TriggerPatterns(
        ...     file_path=Path("chars/Alice.md"),
        ...     entity_name="Alice",
        ...     keywords=["alice", "allie"],
        ...     regex_patterns=[],
        ...     semantic_descriptions=[]
        ... )
        >>> context = TriggerContext(message="Alice walked into the room", ...)
        >>> result = evaluator.evaluate(patterns, context)
        >>> result.matched_pattern
        'alice'
    """

    def __init__(self, *, case_sensitive: bool = False, use_word_boundaries: bool = True) -> None:
        """Initialize keyword evaluator.

        Args:
            case_sensitive: Whether keyword matching is case-sensitive
            use_word_boundaries: Whether to enforce word boundaries
        """
        self.case_sensitive = case_sensitive
        self.use_word_boundaries = use_word_boundaries
        self._boundary_cache: dict[str, re.Pattern] = {}

    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> TriggerResult | None:
        """Evaluate if any keywords match the message.

        Args:
            patterns: Trigger patterns including keywords
            context: Trigger context with message to check

        Returns:
            TriggerResult if match found, None otherwise
        """
        if not patterns.keywords:
            return None

        # Get the message to search
        search_text = context.message if self.case_sensitive else context.message_lower

        # Try each keyword
        for keyword in patterns.keywords:
            # Normalize keyword for comparison
            search_keyword = keyword if self.case_sensitive else keyword.lower()

            # Check if keyword matches
            if self.use_word_boundaries:
                if self._match_with_boundaries(search_keyword, search_text):
                    return self._create_result(patterns, keyword)
            elif search_keyword in search_text:
                return self._create_result(patterns, keyword)

        return None

    def evaluate_batch(
        self, patterns_list: list[TriggerPatterns], context: TriggerContext
    ) -> list[TriggerResult]:
        """Evaluate multiple pattern sets at once.

        This is an optimization opportunity - we can scan the message once
        for all keywords rather than repeatedly.

        Args:
            patterns_list: List of trigger patterns to evaluate
            context: The context to evaluate

        Returns:
            List of TriggerResults for all matches
        """
        results: list[TriggerResult] = []

        # Build a map of keywords to their patterns
        keyword_map: dict[str, TriggerPatterns] = {}
        for patterns in patterns_list:
            for keyword in patterns.keywords:
                search_keyword = keyword if self.case_sensitive else keyword.lower()
                if search_keyword not in keyword_map:
                    keyword_map[search_keyword] = patterns

        # Get the message to search
        search_text = context.message if self.case_sensitive else context.message_lower

        # Check each keyword once
        for keyword, patterns in keyword_map.items():
            if self.use_word_boundaries:
                if self._match_with_boundaries(keyword, search_text):
                    results.append(self._create_result(patterns, keyword))
            elif keyword in search_text:
                results.append(self._create_result(patterns, keyword))

        return results

    def _match_with_boundaries(self, keyword: str, text: str) -> bool:
        """Check if keyword matches with word boundaries.

        Args:
            keyword: The keyword to search for
            text: The text to search in

        Returns:
            True if keyword found with word boundaries
        """
        # Get or compile the regex pattern
        if keyword not in self._boundary_cache:
            # Escape special regex characters
            escaped = re.escape(keyword)
            # Add word boundaries
            pattern = rf"\b{escaped}\b"
            # Compile with appropriate flags
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._boundary_cache[keyword] = re.compile(pattern, flags)

        # Search using compiled pattern
        return bool(self._boundary_cache[keyword].search(text))

    def _create_result(self, patterns: TriggerPatterns, matched_keyword: str) -> TriggerResult:
        """Create a TriggerResult for a successful match.

        Args:
            patterns: The trigger patterns that matched
            matched_keyword: The specific keyword that matched

        Returns:
            TriggerResult with match information
        """
        return TriggerResult(
            file_path=patterns.file_path,
            entity_name=patterns.entity_name,
            trigger_type="keyword",
            matched_pattern=matched_keyword,
            confidence=1.0,  # Keyword matches are absolute
            metadata={
                "case_sensitive": self.case_sensitive,
                "word_boundaries": self.use_word_boundaries,
            },
        )
