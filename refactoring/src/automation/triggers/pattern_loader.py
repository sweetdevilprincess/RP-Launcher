"""Pattern loader for discovering trigger patterns from entity files.

Discovers entity files and parses trigger patterns from their metadata.
Supports multiple trigger formats and caching for performance.

Refactored from src/trigger_system/trigger_system.py
"""

from __future__ import annotations

import re
from pathlib import Path

from ...shared.logging import get_logger
from .protocols import TriggerPatterns


class PatternLoader:
    """Loads and parses trigger patterns from entity files.

    This loader:
    1. Discovers entity files (characters/*.md, entities/*.md)
    2. Parses trigger metadata from each file
    3. Supports multiple trigger formats:
       - Keyword: [Triggers:word1,word2] or **Triggers**: word1, word2
       - Regex: [RegexTriggers:pattern1,pattern2]
       - Semantic: [SemanticTriggers:concept1,concept2]
    4. Caches patterns for performance

    Example:
        >>> loader = PatternLoader()
        >>> patterns_list = loader.load_all_patterns(rp_dir)
        >>> len(patterns_list)
        15  # Number of entity files with triggers
    """

    def __init__(self) -> None:
        """Initialize pattern loader."""
        self._logger = get_logger(__name__)
        self._pattern_cache: dict[Path, TriggerPatterns] = {}

    def load_all_patterns(self, rp_dir: Path) -> list[TriggerPatterns]:
        """Load trigger patterns from all entity files.

        Args:
            rp_dir: RP directory path

        Returns:
            List of TriggerPatterns for all discovered entities
        """
        patterns_list: list[TriggerPatterns] = []

        # Check characters directory
        chars_dir = rp_dir / "characters"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.md"):
                patterns = self.load_patterns_from_file(char_file)
                if patterns and self._has_any_patterns(patterns):
                    patterns_list.append(patterns)

        # Check entities directory
        entities_dir = rp_dir / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.md"):
                patterns = self.load_patterns_from_file(entity_file)
                if patterns and self._has_any_patterns(patterns):
                    patterns_list.append(patterns)

        self._logger.info(
            "pattern_loader.patterns_loaded",
            context={
                "total_files": len(patterns_list),
                "chars_dir": str(chars_dir),
                "entities_dir": str(entities_dir),
            },
        )

        return patterns_list

    def load_patterns_from_file(self, file_path: Path) -> TriggerPatterns | None:
        """Load trigger patterns from a single file.

        Args:
            file_path: Path to entity file

        Returns:
            TriggerPatterns if file is readable, None otherwise
        """
        # Check cache first
        if file_path in self._pattern_cache:
            return self._pattern_cache[file_path]

        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract entity name from filename
            entity_name = self._extract_entity_name(file_path)

            # Parse triggers from content
            keywords, regex_patterns, semantic_descriptions = self._parse_triggers(content)

            patterns = TriggerPatterns(
                file_path=file_path,
                entity_name=entity_name,
                keywords=keywords,
                regex_patterns=regex_patterns,
                semantic_descriptions=semantic_descriptions,
            )

            # Cache for future use
            self._pattern_cache[file_path] = patterns

            return patterns

        except Exception as e:
            self._logger.warning(
                "pattern_loader.file_read_error",
                context={"file_path": str(file_path), "error": str(e)},
            )
            return None

    def _extract_entity_name(self, file_path: Path) -> str:
        """Extract entity name from file path.

        Removes file extension and optional prefixes like [CHAR], [LOC], etc.

        Args:
            file_path: Path to entity file

        Returns:
            Cleaned entity name

        Example:
            >>> loader._extract_entity_name(Path("characters/[CHAR] Alice.md"))
            "Alice"
        """
        entity_name = file_path.stem

        # Remove [CHAR], [LOC], [ITEM], etc. prefixes
        entity_name = re.sub(r"^\[[A-Z]+\]\s*", "", entity_name)

        return entity_name

    def _parse_triggers(self, content: str) -> tuple[list[str], list[str], list[str]]:
        """Parse all three types of triggers from file content.

        Supported formats:
        - Keyword: **Triggers**: word1, word2, word3
        - Keyword: [Triggers:word1,word2,word3]
        - Regex: [RegexTriggers:pattern1,pattern2]
        - Semantic: [SemanticTriggers:concept1,concept2]

        Args:
            content: File content to parse

        Returns:
            Tuple of (keywords, regex_patterns, semantic_descriptions)
        """
        keywords: list[str] = []
        regex_patterns: list[str] = []
        semantic_descriptions: list[str] = []

        for line in content.split("\n"):
            line_stripped = line.strip()

            # Keyword triggers: **Triggers**: word1, word2
            if line_stripped.lower().startswith("**triggers**:"):
                trigger_text = line.split(":", 1)[1].strip()
                keywords = [t.strip() for t in trigger_text.split(",") if t.strip()]

            # Keyword triggers: [Triggers:word1,word2]
            elif line_stripped.startswith("[Triggers:"):
                trigger_text = line_stripped[10:].rstrip("']")
                keywords = [t.strip() for t in trigger_text.split(",") if t.strip()]

            # Regex triggers: [RegexTriggers:pattern1,pattern2]
            elif line_stripped.startswith("[RegexTriggers:"):
                trigger_text = line_stripped[15:].rstrip("']")
                regex_patterns = [t.strip() for t in trigger_text.split(",") if t.strip()]

            # Semantic triggers: [SemanticTriggers:concept1,concept2]
            elif line_stripped.startswith("[SemanticTriggers:"):
                trigger_text = line_stripped[18:].rstrip("']")
                semantic_descriptions = [t.strip() for t in trigger_text.split(",") if t.strip()]

        return keywords, regex_patterns, semantic_descriptions

    def _has_any_patterns(self, patterns: TriggerPatterns) -> bool:
        """Check if patterns has at least one trigger defined.

        Args:
            patterns: TriggerPatterns to check

        Returns:
            True if any triggers are defined
        """
        return bool(patterns.keywords or patterns.regex_patterns or patterns.semantic_descriptions)

    def clear_cache(self) -> None:
        """Clear the pattern cache (useful for testing or reloading)."""
        self._pattern_cache.clear()
        self._logger.debug("pattern_loader.cache_cleared", context={})
