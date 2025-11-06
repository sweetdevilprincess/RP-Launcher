"""Unit tests for SemanticEvaluator.

Tests AI-powered semantic trigger matching with various configurations:
- AI client availability (graceful degradation when unavailable)
- Confidence threshold enforcement
- Error handling from AI client
- Batch evaluation
- Result metadata
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.protocols import (
    TriggerContext,
    TriggerPatterns,
)
from refactoring.src.automation.triggers.semantic_evaluator import SemanticEvaluator


class MockAiClient:
    """Mock AI client for testing semantic evaluation."""

    def __init__(
        self,
        *,
        matched: bool = True,
        confidence: float = 0.85,
        raise_error: bool = False,
    ) -> None:
        """Initialize mock AI client.

        Args:
            matched: Whether to return a match
            confidence: Confidence score to return
            raise_error: If True, raise exception on evaluate_semantic_match
        """
        self.matched = matched
        self.confidence = confidence
        self.raise_error = raise_error
        self.call_count = 0
        self.last_call: dict | None = None

    def evaluate_semantic_match(
        self, message: str, descriptions: list[str], entity_name: str
    ) -> tuple[bool, float]:
        """Mock semantic match evaluation.

        Args:
            message: User message to evaluate
            descriptions: Semantic descriptions to match against
            entity_name: Name of entity being evaluated

        Returns:
            Tuple of (matched, confidence)
        """
        self.call_count += 1
        self.last_call = {
            "message": message,
            "descriptions": descriptions,
            "entity_name": entity_name,
        }

        if self.raise_error:
            raise RuntimeError("Mock AI client error")

        return (self.matched, self.confidence)


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
        message="I was talking to my sister yesterday",
        loaded_entities=[],
        response_count=1,
        rp_dir=temp_rp_dir,
    )


@pytest.fixture
def alice_patterns(temp_rp_dir):
    """Create trigger patterns for Alice with semantic descriptions."""
    return TriggerPatterns(
        file_path=temp_rp_dir / "characters" / "Alice.md",
        entity_name="Alice",
        keywords=[],
        regex_patterns=[],
        semantic_descriptions=[
            "References to Alice",
            "Alice's family members",
            "Alice's friends",
        ],
    )


class TestSemanticEvaluatorBasic:
    """Test basic semantic evaluation functionality."""

    def test_no_ai_client_returns_none(self, alice_patterns, basic_context):
        """Test evaluator returns None when no AI client provided."""
        evaluator = SemanticEvaluator(ai_client=None)
        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is None

    def test_no_semantic_descriptions_returns_none(self, temp_rp_dir, basic_context):
        """Test evaluator returns None when patterns have no semantic descriptions."""
        ai_client = MockAiClient(matched=True, confidence=0.9)
        evaluator = SemanticEvaluator(ai_client=ai_client)

        patterns = TriggerPatterns(
            file_path=temp_rp_dir / "test.md",
            entity_name="Test",
            keywords=[],
            regex_patterns=[],
            semantic_descriptions=[],  # Empty
        )

        result = evaluator.evaluate(patterns, basic_context)
        assert result is None
        assert ai_client.call_count == 0  # AI client should not be called

    def test_successful_match_above_threshold(self, alice_patterns, basic_context):
        """Test successful semantic match above confidence threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.entity_name == "Alice"
        assert result.trigger_type == "semantic"
        assert result.matched_pattern == "References to Alice"  # First description
        assert result.confidence == 0.85
        assert result.file_path == alice_patterns.file_path

    def test_no_match_when_confidence_below_threshold(self, alice_patterns, basic_context):
        """Test no match when confidence is below threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.5)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is None

    def test_no_match_when_ai_returns_false(self, alice_patterns, basic_context):
        """Test no match when AI client returns matched=False."""
        ai_client = MockAiClient(matched=False, confidence=0.9)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is None


class TestConfidenceThreshold:
    """Test confidence threshold enforcement."""

    def test_match_at_exact_threshold(self, alice_patterns, basic_context):
        """Test match is accepted when confidence exactly equals threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.7)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is not None
        assert result.confidence == 0.7

    def test_match_just_below_threshold(self, alice_patterns, basic_context):
        """Test match is rejected when confidence is just below threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.69)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is None

    def test_high_threshold_configuration(self, alice_patterns, basic_context):
        """Test with high confidence threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.9)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is None  # Below 0.9 threshold

    def test_low_threshold_configuration(self, alice_patterns, basic_context):
        """Test with low confidence threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.5)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.3)

        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is not None  # Above 0.3 threshold


class TestErrorHandling:
    """Test error handling during semantic evaluation."""

    def test_ai_client_error_returns_none(self, alice_patterns, basic_context):
        """Test graceful handling when AI client raises exception."""
        ai_client = MockAiClient(raise_error=True)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        # Should not raise exception, should return None
        result = evaluator.evaluate(alice_patterns, basic_context)
        assert result is None

    def test_ai_client_called_with_correct_params(self, alice_patterns, basic_context):
        """Test AI client is called with correct parameters."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        evaluator.evaluate(alice_patterns, basic_context)

        assert ai_client.call_count == 1
        assert ai_client.last_call["message"] == basic_context.message
        assert ai_client.last_call["descriptions"] == alice_patterns.semantic_descriptions
        assert ai_client.last_call["entity_name"] == alice_patterns.entity_name


class TestBatchEvaluation:
    """Test batch evaluation functionality."""

    def test_batch_no_ai_client_returns_empty(self, temp_rp_dir, basic_context):
        """Test batch evaluation returns empty list when no AI client."""
        evaluator = SemanticEvaluator(ai_client=None)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["References to Alice"],
            ),
        ]

        results = evaluator.evaluate_batch(patterns_list, basic_context)
        assert len(results) == 0

    def test_batch_multiple_matches(self, temp_rp_dir, basic_context):
        """Test batch evaluation finds multiple matches."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Alice's family"],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["References to Bob"],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Charlie.md",
                entity_name="Charlie",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Charlie mentioned"],
            ),
        ]

        results = evaluator.evaluate_batch(patterns_list, basic_context)

        assert len(results) == 3
        assert ai_client.call_count == 3
        entity_names = {r.entity_name for r in results}
        assert entity_names == {"Alice", "Bob", "Charlie"}

    def test_batch_no_matches(self, temp_rp_dir, basic_context):
        """Test batch evaluation with no matches."""
        ai_client = MockAiClient(matched=False, confidence=0.5)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["References to Alice"],
            ),
        ]

        results = evaluator.evaluate_batch(patterns_list, basic_context)
        assert len(results) == 0

    def test_batch_partial_matches(self, temp_rp_dir, basic_context):
        """Test batch evaluation with some matches."""

        # Create AI client that alternates between match and no-match
        class AlternatingMockClient:
            def __init__(self):
                self.call_count = 0

            def evaluate_semantic_match(self, message, descriptions, entity_name):
                self.call_count += 1
                # Return match for Alice, no match for Bob
                if entity_name == "Alice":
                    return (True, 0.85)
                return (False, 0.3)

        ai_client = AlternatingMockClient()
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Alice's family"],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["References to Bob"],
            ),
        ]

        results = evaluator.evaluate_batch(patterns_list, basic_context)
        assert len(results) == 1
        assert results[0].entity_name == "Alice"


class TestResultMetadata:
    """Test result metadata and properties."""

    def test_result_metadata_includes_threshold(self, alice_patterns, basic_context):
        """Test result metadata includes confidence threshold."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.75)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.metadata["confidence_threshold"] == 0.75

    def test_result_metadata_includes_all_descriptions(self, alice_patterns, basic_context):
        """Test result metadata includes all semantic descriptions."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.metadata["all_descriptions"] == alice_patterns.semantic_descriptions

    def test_matched_pattern_is_first_description(self, alice_patterns, basic_context):
        """Test matched_pattern is the first semantic description."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.matched_pattern == "References to Alice"
        assert result.matched_pattern == alice_patterns.semantic_descriptions[0]

    def test_confidence_from_ai_client(self, alice_patterns, basic_context):
        """Test confidence score comes from AI client."""
        ai_client = MockAiClient(matched=True, confidence=0.92)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.confidence == 0.92

    def test_trigger_type_is_semantic(self, alice_patterns, basic_context):
        """Test trigger_type is always 'semantic'."""
        ai_client = MockAiClient(matched=True, confidence=0.85)
        evaluator = SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7)

        result = evaluator.evaluate(alice_patterns, basic_context)

        assert result is not None
        assert result.trigger_type == "semantic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
