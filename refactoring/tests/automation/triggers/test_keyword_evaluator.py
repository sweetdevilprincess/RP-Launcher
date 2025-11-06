"""Unit tests for KeywordEvaluator.

Tests keyword-based trigger matching with various configurations:
- Case-sensitive and case-insensitive matching
- Word boundary enforcement
- Batch evaluation optimization
- Pattern caching
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.keyword_evaluator import KeywordEvaluator
from refactoring.src.automation.triggers.protocols import (
    TriggerContext,
    TriggerPatterns,
)


@pytest.fixture
def temp_rp_dir():
    """Create temporary RP directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir) / "test_rp"
        rp_dir.mkdir()
        yield rp_dir


@pytest.fixture
def basic_context(temp_rp_dir):
    """Create basic trigger context."""
    return TriggerContext(
        message="Alice walked into the room with Bob",
        loaded_entities=["Alice"],
        response_count=42,
        rp_dir=temp_rp_dir,
        previous_triggers=None,
    )


@pytest.fixture
def alice_patterns(temp_rp_dir):
    """Create trigger patterns for Alice."""
    return TriggerPatterns(
        file_path=temp_rp_dir / "characters" / "Alice.md",
        entity_name="Alice",
        keywords=["alice", "allie"],
        regex_patterns=[],
        semantic_descriptions=[],
    )


class TestKeywordEvaluatorBasic:
    """Test basic keyword matching functionality."""

    def test_simple_match_case_insensitive(self, alice_patterns, basic_context):
        """Test simple keyword match with case-insensitive matching."""
        evaluator = KeywordEvaluator(case_sensitive=False, use_word_boundaries=True)
        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.entity_name == "Alice"
        assert result.trigger_type == "keyword"
        assert result.matched_pattern == "alice"
        assert result.confidence == 1.0
        assert result.file_path == alice_patterns.file_path

    def test_no_match(self, alice_patterns, temp_rp_dir):
        """Test when no keyword matches."""
        evaluator = KeywordEvaluator()
        context = TriggerContext(
            message="Charlie and David went shopping",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(alice_patterns, context)
        assert result is None

    def test_empty_keywords(self, temp_rp_dir, basic_context):
        """Test patterns with no keywords."""
        evaluator = KeywordEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],  # Empty keywords list
            regex_patterns=[],
            semantic_descriptions=[],
        )

        result = evaluator.evaluate(patterns, basic_context)
        assert result is None

    def test_alternative_keyword_match(self, alice_patterns, temp_rp_dir):
        """Test matching with alternative keyword spelling."""
        evaluator = KeywordEvaluator()
        context = TriggerContext(
            message="Allie came home early",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(alice_patterns, context)
        assert result is not None
        assert result.matched_pattern == "allie"


class TestCaseSensitivity:
    """Test case-sensitive vs case-insensitive matching."""

    def test_case_insensitive_uppercase(self, alice_patterns, temp_rp_dir):
        """Test case-insensitive match with uppercase in message."""
        evaluator = KeywordEvaluator(case_sensitive=False)
        context = TriggerContext(
            message="ALICE IS HERE",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(alice_patterns, context)
        assert result is not None
        assert result.matched_pattern == "alice"

    def test_case_insensitive_mixed(self, alice_patterns, temp_rp_dir):
        """Test case-insensitive match with mixed case."""
        evaluator = KeywordEvaluator(case_sensitive=False)
        context = TriggerContext(
            message="AlIcE walked in",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(alice_patterns, context)
        assert result is not None

    def test_case_sensitive_exact_match(self, temp_rp_dir):
        """Test case-sensitive match requires exact case."""
        evaluator = KeywordEvaluator(case_sensitive=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["Alice"],  # Capitalized
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # Exact match should work
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)
        assert result is not None

    def test_case_sensitive_no_match(self, temp_rp_dir):
        """Test case-sensitive match fails with different case."""
        evaluator = KeywordEvaluator(case_sensitive=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["Alice"],  # Capitalized
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # Wrong case should fail
        context = TriggerContext(
            message="alice is here",  # lowercase
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)
        assert result is None


class TestWordBoundaries:
    """Test word boundary enforcement."""

    def test_word_boundaries_full_word(self, temp_rp_dir):
        """Test word boundaries match full words."""
        evaluator = KeywordEvaluator(use_word_boundaries=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["cat"],
            regex_patterns=[],
            semantic_descriptions=[],
        )

        context = TriggerContext(
            message="The cat sat on the mat",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is not None

    def test_word_boundaries_reject_partial(self, temp_rp_dir):
        """Test word boundaries reject partial word matches."""
        evaluator = KeywordEvaluator(use_word_boundaries=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["cat"],
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # "cat" is part of "catalog" but shouldn't match with word boundaries
        context = TriggerContext(
            message="I need to check the catalog",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is None

    def test_no_word_boundaries_partial_match(self, temp_rp_dir):
        """Test without word boundaries allows partial matches."""
        evaluator = KeywordEvaluator(use_word_boundaries=False)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["cat"],
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # Should match "cat" inside "catalog"
        context = TriggerContext(
            message="I need to check the catalog",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is not None
        assert result.matched_pattern == "cat"

    def test_word_boundaries_with_punctuation(self, temp_rp_dir):
        """Test word boundaries work with punctuation."""
        evaluator = KeywordEvaluator(use_word_boundaries=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["cat"],
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # Should match even with punctuation
        context = TriggerContext(
            message="Look, a cat!",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is not None


class TestBatchEvaluation:
    """Test batch evaluation optimization."""

    def test_batch_multiple_matches(self, temp_rp_dir):
        """Test batch evaluation finds multiple matches."""
        evaluator = KeywordEvaluator()

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=["bob"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Charlie.md",
                entity_name="Charlie",
                keywords=["charlie"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        context = TriggerContext(
            message="Alice and Bob went to see Charlie",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        results = evaluator.evaluate_batch(patterns_list, context)

        assert len(results) == 3
        entity_names = {r.entity_name for r in results}
        assert entity_names == {"Alice", "Bob", "Charlie"}

    def test_batch_no_matches(self, temp_rp_dir):
        """Test batch evaluation with no matches."""
        evaluator = KeywordEvaluator()

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        context = TriggerContext(
            message="No one is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        results = evaluator.evaluate_batch(patterns_list, context)
        assert len(results) == 0

    def test_batch_partial_matches(self, temp_rp_dir):
        """Test batch evaluation with some matches."""
        evaluator = KeywordEvaluator()

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=["bob"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Charlie.md",
                entity_name="Charlie",
                keywords=["charlie"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        # Only Alice mentioned
        context = TriggerContext(
            message="Alice arrived",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        results = evaluator.evaluate_batch(patterns_list, context)
        assert len(results) == 1
        assert results[0].entity_name == "Alice"


class TestResultMetadata:
    """Test result metadata and properties."""

    def test_result_metadata_case_sensitive(self, temp_rp_dir):
        """Test metadata includes configuration."""
        evaluator = KeywordEvaluator(case_sensitive=False, use_word_boundaries=False)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["alice"],
            regex_patterns=[],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)

        assert result is not None
        assert result.metadata["case_sensitive"] is False
        assert result.metadata["word_boundaries"] is False

    def test_result_metadata_case_insensitive(self, alice_patterns, basic_context):
        """Test metadata with different configuration."""
        evaluator = KeywordEvaluator(case_sensitive=False, use_word_boundaries=True)
        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result.metadata["case_sensitive"] is False
        assert result.metadata["word_boundaries"] is True

    def test_confidence_always_one(self, alice_patterns, basic_context):
        """Test keyword matches always have confidence 1.0."""
        evaluator = KeywordEvaluator()
        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result.confidence == 1.0


class TestBoundaryCache:
    """Test regex boundary caching optimization."""

    def test_cache_reuses_patterns(self, temp_rp_dir):
        """Test that boundary patterns are cached and reused."""
        evaluator = KeywordEvaluator(use_word_boundaries=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=["alice"],
            regex_patterns=[],
            semantic_descriptions=[],
        )

        # First evaluation should compile and cache the pattern
        context1 = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result1 = evaluator.evaluate(patterns, context1)
        assert result1 is not None

        # Check cache was populated
        assert "alice" in evaluator._boundary_cache

        # Second evaluation should reuse cached pattern
        context2 = TriggerContext(
            message="Alice left",
            loaded_entities=[],
            response_count=2,
            rp_dir=temp_rp_dir,
        )
        result2 = evaluator.evaluate(patterns, context2)
        assert result2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
