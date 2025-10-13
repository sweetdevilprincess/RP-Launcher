"""
Enhanced Multi-Tier Trigger System (WIP)

Provides three types of trigger matching:
1. Keyword matching - Fast, simple word matching with improvements
2. Regex matching - Powerful pattern matching for complex scenarios
3. Semantic matching - AI-powered semantic understanding

Usage:
    from trigger_system import TriggerMatcher

    matcher = TriggerMatcher(config)
    files_to_load = matcher.find_triggered_files(message, rp_dir)
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class TriggerMatch:
    """Information about a successful trigger match"""
    file_path: Path
    entity_name: str
    trigger_type: str  # 'keyword', 'regex', 'semantic'
    matched_pattern: str
    confidence: float = 1.0  # 1.0 for keyword/regex, 0.0-1.0 for semantic


class TriggerMatcher:
    """
    Enhanced trigger matcher with keyword, regex, and semantic matching.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize trigger matcher.

        Args:
            config: Configuration dict with trigger_system settings
        """
        self.config = config or {}
        self.trigger_config = self.config.get('trigger_system', {})

        # Keyword matching config
        self.keyword_enabled = self.trigger_config.get('keyword_matching', {}).get('enabled', True)
        self.keyword_case_sensitive = self.trigger_config.get('keyword_matching', {}).get('case_sensitive', False)
        self.keyword_word_boundaries = self.trigger_config.get('keyword_matching', {}).get('use_word_boundaries', True)

        # Regex matching config
        self.regex_enabled = self.trigger_config.get('regex_matching', {}).get('enabled', True)
        self.regex_max_patterns = self.trigger_config.get('regex_matching', {}).get('max_patterns_per_file', 10)

        # Semantic matching config
        self.semantic_enabled = self.trigger_config.get('semantic_matching', {}).get('enabled', False)
        self.semantic_threshold = self.trigger_config.get('semantic_matching', {}).get('similarity_threshold', 0.7)
        self.semantic_model = None  # Lazy loaded
        self.embedding_cache = {}  # Cache embeddings for performance

        # Compiled regex cache
        self.regex_cache = {}

    def find_triggered_files(self, message: str, rp_dir: Path, log_callback=None) -> List[TriggerMatch]:
        """
        Find all files that should be triggered by the message.

        Args:
            message: User's message text
            rp_dir: RP directory path
            log_callback: Optional callback for logging: func(message: str)

        Returns:
            List of TriggerMatch objects
        """
        matches = []

        # Check characters directory
        chars_dir = rp_dir / "characters"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.md"):
                match = self._check_file_triggers(char_file, message, log_callback)
                if match:
                    matches.append(match)

        # Check entities directory
        entities_dir = rp_dir / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.md"):
                match = self._check_file_triggers(entity_file, message, log_callback)
                if match:
                    matches.append(match)

        return matches

    def _check_file_triggers(self, file_path: Path, message: str, log_callback=None) -> Optional[TriggerMatch]:
        """
        Check if a file should be triggered by the message.

        Returns first match found (keyword -> regex -> semantic order).
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract entity name from filename
            entity_name = file_path.stem
            entity_name = re.sub(r'^\[[A-Z]+\]\s*', '', entity_name)  # Remove [CHAR], [LOC], etc.

            # Parse all trigger types from file
            keyword_triggers, regex_triggers, semantic_triggers = self._parse_triggers(content)

            # Try keyword matching first (fastest)
            if self.keyword_enabled and keyword_triggers:
                match = self._match_keywords(keyword_triggers, message, file_path, entity_name)
                if match:
                    if log_callback:
                        log_callback(f"KEYWORD MATCH: {file_path.name} ('{match.matched_pattern}')")
                    return match

            # Try regex matching second (fast)
            if self.regex_enabled and regex_triggers:
                match = self._match_regex(regex_triggers, message, file_path, entity_name)
                if match:
                    if log_callback:
                        log_callback(f"REGEX MATCH: {file_path.name} (pattern: '{match.matched_pattern}')")
                    return match

            # Try semantic matching last (slowest but most intelligent)
            if self.semantic_enabled and semantic_triggers:
                match = self._match_semantic(semantic_triggers, message, file_path, entity_name)
                if match:
                    if log_callback:
                        log_callback(f"SEMANTIC MATCH: {file_path.name} ('{match.matched_pattern}', confidence: {match.confidence:.2f})")
                    return match

            return None

        except Exception as e:
            if log_callback:
                log_callback(f"WARNING: Could not process {file_path.name}: {e}")
            return None

    def _parse_triggers(self, content: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Parse all three types of triggers from file content.

        Returns:
            (keyword_triggers, regex_triggers, semantic_triggers)
        """
        keyword_triggers = []
        regex_triggers = []
        semantic_triggers = []

        for line in content.split('\n'):
            line_stripped = line.strip()

            # Keyword triggers: [Triggers:word1,word2'] or **Triggers**: word1, word2
            if line_stripped.lower().startswith('**triggers**:'):
                trigger_text = line.split(':', 1)[1].strip()
                keyword_triggers = [t.strip() for t in trigger_text.split(',') if t.strip()]

            elif line_stripped.startswith('[Triggers:'):
                trigger_text = line_stripped[10:].rstrip("']")
                keyword_triggers = [t.strip() for t in trigger_text.split(',') if t.strip()]

            # Regex triggers: [RegexTriggers:pattern1,pattern2']
            elif line_stripped.startswith('[RegexTriggers:'):
                trigger_text = line_stripped[15:].rstrip("']")
                regex_triggers = [t.strip() for t in trigger_text.split(',') if t.strip()]

            # Semantic triggers: [SemanticTriggers:concept1,concept2']
            elif line_stripped.startswith('[SemanticTriggers:'):
                trigger_text = line_stripped[18:].rstrip("']")
                semantic_triggers = [t.strip() for t in trigger_text.split(',') if t.strip()]

        return keyword_triggers, regex_triggers, semantic_triggers

    def _match_keywords(self, triggers: List[str], message: str, file_path: Path, entity_name: str) -> Optional[TriggerMatch]:
        """
        Enhanced keyword matching with word boundaries and case-insensitive option.
        """
        message_to_search = message if self.keyword_case_sensitive else message.lower()

        for trigger in triggers:
            if not trigger:
                continue

            trigger_to_search = trigger if self.keyword_case_sensitive else trigger.lower()

            if self.keyword_word_boundaries:
                # Use word boundaries to avoid false positives
                # e.g., "cat" won't match "category"
                pattern = r'\b' + re.escape(trigger_to_search) + r'\b'
                if re.search(pattern, message_to_search, re.IGNORECASE if not self.keyword_case_sensitive else 0):
                    return TriggerMatch(
                        file_path=file_path,
                        entity_name=entity_name,
                        trigger_type='keyword',
                        matched_pattern=trigger,
                        confidence=1.0
                    )
            else:
                # Simple substring matching (backward compatible)
                if trigger_to_search in message_to_search:
                    return TriggerMatch(
                        file_path=file_path,
                        entity_name=entity_name,
                        trigger_type='keyword',
                        matched_pattern=trigger,
                        confidence=1.0
                    )

        return None

    def _match_regex(self, patterns: List[str], message: str, file_path: Path, entity_name: str) -> Optional[TriggerMatch]:
        """
        Regex pattern matching with safety checks.
        """
        # Limit number of patterns to prevent performance issues
        patterns = patterns[:self.regex_max_patterns]

        for pattern_str in patterns:
            if not pattern_str:
                continue

            try:
                # Get or compile pattern (with caching)
                cache_key = pattern_str
                if cache_key not in self.regex_cache:
                    # Compile pattern
                    compiled_pattern = re.compile(pattern_str)
                    self.regex_cache[cache_key] = compiled_pattern
                else:
                    compiled_pattern = self.regex_cache[cache_key]

                # Try to match
                if compiled_pattern.search(message):
                    return TriggerMatch(
                        file_path=file_path,
                        entity_name=entity_name,
                        trigger_type='regex',
                        matched_pattern=pattern_str,
                        confidence=1.0
                    )

            except re.error as e:
                # Invalid regex pattern - skip it
                # Log warning but continue
                continue

        return None

    def _match_semantic(self, concepts: List[str], message: str, file_path: Path, entity_name: str) -> Optional[TriggerMatch]:
        """
        Semantic matching using sentence embeddings.

        Note: Requires sentence-transformers library. Install with:
        pip install sentence-transformers
        """
        # Lazy load the semantic model
        if self.semantic_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = self.trigger_config.get('semantic_matching', {}).get('model', 'all-MiniLM-L6-v2')
                self.semantic_model = SentenceTransformer(model_name)
            except ImportError:
                # sentence-transformers not installed
                # Disable semantic matching
                self.semantic_enabled = False
                return None
            except Exception:
                # Model loading failed
                self.semantic_enabled = False
                return None

        try:
            from sentence_transformers import util

            # Get or compute message embedding
            message_embedding = self._get_embedding(message)

            # Check each concept
            for concept in concepts:
                if not concept:
                    continue

                # Get or compute concept embedding
                concept_embedding = self._get_embedding(concept)

                # Compute cosine similarity
                similarity = util.pytorch_cos_sim(message_embedding, concept_embedding).item()

                # Check if similarity exceeds threshold
                if similarity >= self.semantic_threshold:
                    return TriggerMatch(
                        file_path=file_path,
                        entity_name=entity_name,
                        trigger_type='semantic',
                        matched_pattern=concept,
                        confidence=similarity
                    )

            return None

        except Exception:
            # Semantic matching failed - continue without it
            return None

    def _get_embedding(self, text: str):
        """
        Get embedding for text, using cache if available.
        """
        cache_key = text.lower().strip()

        if cache_key not in self.embedding_cache:
            # Compute and cache embedding
            embedding = self.semantic_model.encode(text, convert_to_tensor=True)
            self.embedding_cache[cache_key] = embedding

        return self.embedding_cache[cache_key]

    def clear_caches(self):
        """Clear regex and embedding caches (useful for testing)."""
        self.regex_cache.clear()
        self.embedding_cache.clear()


# Convenience function for backward compatibility
def identify_triggers_enhanced(message: str, rp_dir: Path, config: Optional[Dict] = None, log_callback=None) -> Tuple[List[Path], List[str]]:
    """
    Enhanced trigger identification with keyword, regex, and semantic matching.

    Backward compatible with old identify_triggers function.

    Args:
        message: User's message
        rp_dir: RP directory
        config: Configuration dict
        log_callback: Logging callback

    Returns:
        (files_to_load, entity_names)
    """
    matcher = TriggerMatcher(config)
    matches = matcher.find_triggered_files(message, rp_dir, log_callback)

    files_to_load = [match.file_path for match in matches]
    entity_names = [match.entity_name for match in matches]

    return files_to_load, entity_names
