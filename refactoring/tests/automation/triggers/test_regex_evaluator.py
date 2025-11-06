"""Unit tests for RegexEvaluator.

Tests regex-based trigger matching with various configurations:
- Basic pattern matching
- Case-sensitive and case-insensitive matching
- Pattern limit enforcement
- Invalid regex handling
- Pattern caching
- Batch evaluation
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.protocols import (
    TriggerContext,
    TriggerPatterns,
)
from refactoring.src.automation.triggers.regex_evaluator import RegexEvaluator


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
        message="I was talking to Alice yesterday about the project",
        loaded_entities=[],
        response_count=1,
        rp_dir=temp_rp_dir,
    )


class TestRegexEvaluatorBasic:
    """Test basic regex pattern matching."""

    def test_simple_pattern_match(self, temp_rp_dir):
        """Test simple regex pattern matching."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "Alice.md",
            entity_name="Alice",
            keywords=[],
            regex_patterns=[r"talk.*alice"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="I was talking to Alice",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)

        assert result is not None
        assert result.entity_name == "Alice"
        assert result.trigger_type == "regex"
        assert result.matched_pattern == r"talk.*alice"
        assert result.confidence == 1.0

    def test_no_match(self, temp_rp_dir):
        """Test when no pattern matches."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "Alice.md",
            entity_name="Alice",
            keywords=[],
            regex_patterns=[r"alice.*home"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Bob went to the store",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is None

    def test_empty_patterns(self, temp_rp_dir, basic_context):
        """Test with no regex patterns."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[],  # Empty
            semantic_descriptions=[],
        )

        result = evaluator.evaluate(patterns, basic_context)
        assert result is None

    def test_complex_pattern(self, temp_rp_dir):
        """Test complex regex with groups and alternatives."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "Alice.md",
            entity_name="Alice",
            keywords=[],
            regex_patterns=[r"talk(ing|ed)?\s+(to|with)\s+alice"],
            semantic_descriptions=[],
        )

        # Test "talking to alice"
        context1 = TriggerContext(
            message="I was talking to Alice",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result1 = evaluator.evaluate(patterns, context1)
        assert result1 is not None

        # Test "talked with alice"
        context2 = TriggerContext(
            message="I talked with Alice",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result2 = evaluator.evaluate(patterns, context2)
        assert result2 is not None


class TestCaseSensitivity:
    """Test case-sensitive vs case-insensitive matching."""

    def test_case_insensitive_default(self, temp_rp_dir):
        """Test case-insensitive matching (default)."""
        evaluator = RegexEvaluator(case_sensitive=False)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"alice"],
            semantic_descriptions=[],
        )

        # Uppercase should match
        context = TriggerContext(
            message="ALICE is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)
        assert result is not None

    def test_case_sensitive_match(self, temp_rp_dir):
        """Test case-sensitive matching."""
        evaluator = RegexEvaluator(case_sensitive=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"Alice"],  # Capitalized
            semantic_descriptions=[],
        )

        # Exact case should match
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)
        assert result is not None

    def test_case_sensitive_no_match(self, temp_rp_dir):
        """Test case-sensitive matching fails with different case."""
        evaluator = RegexEvaluator(case_sensitive=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"Alice"],  # Capitalized
            semantic_descriptions=[],
        )

        # Different case should not match
        context = TriggerContext(
            message="alice is here",  # lowercase
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result = evaluator.evaluate(patterns, context)
        assert result is None


class TestMultiplePatterns:
    """Test handling of multiple regex patterns per file."""

    def test_multiple_patterns_first_match(self, temp_rp_dir):
        """Test returns first matching pattern."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[
                r"alice.*home",  # Won't match
                r"alice.*project",  # Will match
                r"alice.*work",  # Won't be checked (first match wins)
            ],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice worked on the project",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is not None
        assert result.matched_pattern == r"alice.*project"

    def test_pattern_limit_enforcement(self, temp_rp_dir):
        """Test max_patterns_per_file limit is enforced."""
        evaluator = RegexEvaluator(max_patterns_per_file=2)

        # Create 5 patterns, but only first 2 will be checked
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[
                r"pattern1",
                r"pattern2",
                r"alice",  # This won't be checked due to limit
                r"pattern4",
                r"pattern5",
            ],
            semantic_descriptions=[],
        )

        # Message matches pattern 3, but it won't be checked
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        # Should not match because "alice" pattern is beyond the limit
        assert result is None


class TestInvalidRegex:
    """Test graceful handling of invalid regex patterns."""

    def test_invalid_pattern_skipped(self, temp_rp_dir):
        """Test invalid regex patterns are skipped gracefully."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[
                r"[invalid",  # Invalid regex (unmatched bracket)
                r"alice",  # Valid pattern
            ],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        # Should match the valid pattern despite invalid one
        result = evaluator.evaluate(patterns, context)
        assert result is not None
        assert result.matched_pattern == r"alice"

    def test_all_invalid_patterns(self, temp_rp_dir):
        """Test when all patterns are invalid."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[
                r"[invalid",  # Invalid
                r"(?P<",  # Invalid
            ],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result is None

    def test_invalid_pattern_cached(self, temp_rp_dir):
        """Test invalid patterns are cached to avoid recompiling."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"[invalid"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="test",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        # First evaluation should cache the failure
        result1 = evaluator.evaluate(patterns, context)
        assert result1 is None

        # Check that invalid pattern is in cache as None
        assert r"[invalid" in evaluator._pattern_cache
        assert evaluator._pattern_cache[r"[invalid"] is None

        # Second evaluation should use cached failure
        result2 = evaluator.evaluate(patterns, context)
        assert result2 is None


class TestPatternCaching:
    """Test regex pattern compilation caching."""

    def test_patterns_cached(self, temp_rp_dir):
        """Test compiled patterns are cached."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"alice"],
            semantic_descriptions=[],
        )

        # First evaluation should compile and cache
        context1 = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        result1 = evaluator.evaluate(patterns, context1)
        assert result1 is not None

        # Check pattern was cached
        assert r"alice" in evaluator._pattern_cache
        cached_pattern = evaluator._pattern_cache[r"alice"]
        assert cached_pattern is not None

        # Second evaluation should reuse cached pattern
        context2 = TriggerContext(
            message="Alice left",
            loaded_entities=[],
            response_count=2,
            rp_dir=temp_rp_dir,
        )
        result2 = evaluator.evaluate(patterns, context2)
        assert result2 is not None

        # Should be same compiled pattern object
        assert evaluator._pattern_cache[r"alice"] is cached_pattern


class TestBatchEvaluation:
    """Test batch evaluation optimization."""

    def test_batch_multiple_matches(self, temp_rp_dir):
        """Test batch evaluation finds multiple matches."""
        evaluator = RegexEvaluator()

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[r"\balice\b"],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=[],
                regex_patterns=[r"\bbob\b"],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Charlie.md",
                entity_name="Charlie",
                keywords=[],
                regex_patterns=[r"\bcharlie\b"],
                semantic_descriptions=[],
            ),
        ]

        context = TriggerContext(
            message="Alice and Bob met with Charlie",
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
        evaluator = RegexEvaluator()

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[r"alice.*home"],
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

    def test_batch_with_pattern_limit(self, temp_rp_dir):
        """Test batch evaluation respects pattern limits."""
        evaluator = RegexEvaluator(max_patterns_per_file=1)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "test.md",
                entity_name="Test",
                keywords=[],
                regex_patterns=[
                    r"pattern1",
                    r"alice",  # Won't be checked due to limit
                ],
                semantic_descriptions=[],
            ),
        ]

        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        results = evaluator.evaluate_batch(patterns_list, context)
        # Should not match because alice pattern is beyond limit
        assert len(results) == 0


class TestResultMetadata:
    """Test result metadata and properties."""

    def test_metadata_case_sensitive(self, temp_rp_dir):
        """Test metadata includes case sensitivity setting."""
        evaluator = RegexEvaluator(case_sensitive=True)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"Alice"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result.metadata["case_sensitive"] is True

    def test_metadata_case_insensitive(self, temp_rp_dir):
        """Test metadata with case-insensitive setting."""
        evaluator = RegexEvaluator(case_sensitive=False)
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"alice"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result.metadata["case_sensitive"] is False

    def test_confidence_always_one(self, temp_rp_dir):
        """Test regex matches always have confidence 1.0."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"alice"],
            semantic_descriptions=[],
        )
        context = TriggerContext(
            message="Alice is here",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(patterns, context)
        assert result.confidence == 1.0


class TestSpecialPatterns:
    """Test various special regex patterns."""

    def test_word_boundary_pattern(self, temp_rp_dir):
        """Test word boundary patterns."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"\bcat\b"],
            semantic_descriptions=[],
        )

        # Should match standalone word
        context1 = TriggerContext(
            message="The cat sat",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        assert evaluator.evaluate(patterns, context1) is not None

        # Should not match partial word
        context2 = TriggerContext(
            message="The catalog",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        assert evaluator.evaluate(patterns, context2) is None

    def test_lookahead_pattern(self, temp_rp_dir):
        """Test lookahead assertions."""
        evaluator = RegexEvaluator()
        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[r"alice(?=\s+went)"],
            semantic_descriptions=[],
        )

        # Should match when followed by " went"
        context1 = TriggerContext(
            message="Alice went home",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        assert evaluator.evaluate(patterns, context1) is not None

        # Should not match when not followed by " went"
        context2 = TriggerContext(
            message="Alice stayed",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
        )
        assert evaluator.evaluate(patterns, context2) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
