"""Unit tests for TriggerCoordinator.

Tests trigger evaluation orchestration with:
- Multiple evaluators in priority order
- Evaluator short-circuiting (stop at first match)
- Result deduplication
- Recent trigger filtering
- Result ranking by type and confidence
- Max results limiting
"""

import tempfile
from pathlib import Path

import pytest
from refactoring.src.automation.triggers.coordinator import TriggerCoordinator
from refactoring.src.automation.triggers.protocols import (
    TriggerContext,
    TriggerPatterns,
    TriggerResult,
)


class MockEvaluator:
    """Mock evaluator for testing coordinator behavior."""

    def __init__(
        self,
        name: str,
        trigger_type: str,
        *,
        matches: set[str] | None = None,
        confidence: float = 1.0,
    ) -> None:
        """Initialize mock evaluator.

        Args:
            name: Name of the evaluator
            trigger_type: Type of trigger ("keyword", "regex", "semantic")
            matches: Set of entity names that should match (None = no matches)
            confidence: Confidence score to return for matches
        """
        self.name = name
        self.trigger_type = trigger_type
        self.matches = matches or set()
        self.confidence = confidence
        self.call_count = 0
        self.evaluated_entities: list[str] = []

    def evaluate(self, patterns: TriggerPatterns, context: TriggerContext) -> TriggerResult | None:
        """Mock evaluate method."""
        self.call_count += 1
        self.evaluated_entities.append(patterns.entity_name)

        if patterns.entity_name in self.matches:
            return TriggerResult(
                file_path=patterns.file_path,
                entity_name=patterns.entity_name,
                trigger_type=self.trigger_type,
                matched_pattern=f"{self.name}_pattern",
                confidence=self.confidence,
                metadata={},
            )

        return None


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
        message="Alice and Bob walked in",
        loaded_entities=[],
        response_count=1,
        rp_dir=temp_rp_dir,
    )


class TestCoordinatorBasic:
    """Test basic coordinator functionality."""

    def test_single_evaluator_single_match(self, temp_rp_dir, basic_context):
        """Test coordinator with single evaluator and single match."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice"})
        coordinator = TriggerCoordinator([keyword_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 1
        assert results[0].entity_name == "Alice"
        assert results[0].trigger_type == "keyword"
        assert keyword_eval.call_count == 1

    def test_single_evaluator_no_matches(self, temp_rp_dir, basic_context):
        """Test coordinator when evaluator finds no matches."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches=set())
        coordinator = TriggerCoordinator([keyword_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 0
        assert keyword_eval.call_count == 1

    def test_multiple_patterns_multiple_matches(self, temp_rp_dir, basic_context):
        """Test coordinator with multiple patterns and multiple matches."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice", "Bob", "Charlie"})
        coordinator = TriggerCoordinator([keyword_eval])

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

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 3
        entity_names = {r.entity_name for r in results}
        assert entity_names == {"Alice", "Bob", "Charlie"}


class TestEvaluatorOrdering:
    """Test evaluator ordering and short-circuiting."""

    def test_evaluators_tried_in_order(self, temp_rp_dir, basic_context):
        """Test evaluators are tried in the order provided."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice"})
        regex_eval = MockEvaluator("regex", "regex", matches=set())
        semantic_eval = MockEvaluator("semantic", "semantic", matches=set())

        coordinator = TriggerCoordinator([keyword_eval, regex_eval, semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 1
        assert results[0].trigger_type == "keyword"
        # Keyword matched, so regex and semantic should not be tried
        assert keyword_eval.call_count == 1
        assert regex_eval.call_count == 0
        assert semantic_eval.call_count == 0

    def test_fallback_to_second_evaluator(self, temp_rp_dir, basic_context):
        """Test fallback when first evaluator doesn't match."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches=set())
        regex_eval = MockEvaluator("regex", "regex", matches={"Alice"})
        semantic_eval = MockEvaluator("semantic", "semantic", matches=set())

        coordinator = TriggerCoordinator([keyword_eval, regex_eval, semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=["alice"],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 1
        assert results[0].trigger_type == "regex"
        # Keyword tried but didn't match, regex matched, semantic not tried
        assert keyword_eval.call_count == 1
        assert regex_eval.call_count == 1
        assert semantic_eval.call_count == 0

    def test_fallback_to_third_evaluator(self, temp_rp_dir, basic_context):
        """Test fallback when first two evaluators don't match."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches=set())
        regex_eval = MockEvaluator("regex", "regex", matches=set())
        semantic_eval = MockEvaluator("semantic", "semantic", matches={"Alice"})

        coordinator = TriggerCoordinator([keyword_eval, regex_eval, semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["References to Alice"],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 1
        assert results[0].trigger_type == "semantic"
        # All evaluators tried
        assert keyword_eval.call_count == 1
        assert regex_eval.call_count == 1
        assert semantic_eval.call_count == 1

    def test_no_match_all_evaluators_tried(self, temp_rp_dir, basic_context):
        """Test all evaluators tried when none match."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches=set())
        regex_eval = MockEvaluator("regex", "regex", matches=set())
        semantic_eval = MockEvaluator("semantic", "semantic", matches=set())

        coordinator = TriggerCoordinator([keyword_eval, regex_eval, semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        assert len(results) == 0
        assert keyword_eval.call_count == 1
        assert regex_eval.call_count == 1
        assert semantic_eval.call_count == 1


class TestRecentTriggerFiltering:
    """Test filtering of recently triggered files."""

    def test_filter_recent_triggers(self, temp_rp_dir):
        """Test that recently triggered files are filtered out."""
        alice_path = temp_rp_dir / "Alice.md"
        bob_path = temp_rp_dir / "Bob.md"

        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice", "Bob"})
        coordinator = TriggerCoordinator([keyword_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=alice_path,
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=bob_path,
                entity_name="Bob",
                keywords=["bob"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        # Alice was recently triggered
        context = TriggerContext(
            message="Alice and Bob walked in",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
            previous_triggers=[alice_path],
        )

        results = coordinator.evaluate_triggers(patterns_list, context)

        # Only Bob should be in results
        assert len(results) == 1
        assert results[0].entity_name == "Bob"

    def test_no_filtering_when_no_previous_triggers(self, temp_rp_dir, basic_context):
        """Test no filtering when previous_triggers is None."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice", "Bob"})
        coordinator = TriggerCoordinator([keyword_eval])

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
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Both should be in results
        assert len(results) == 2
        entity_names = {r.entity_name for r in results}
        assert entity_names == {"Alice", "Bob"}

    def test_filter_all_recent_triggers(self, temp_rp_dir):
        """Test filtering when all matches are recent triggers."""
        alice_path = temp_rp_dir / "Alice.md"
        bob_path = temp_rp_dir / "Bob.md"

        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice", "Bob"})
        coordinator = TriggerCoordinator([keyword_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=alice_path,
                entity_name="Alice",
                keywords=["alice"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=bob_path,
                entity_name="Bob",
                keywords=["bob"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        # Both were recently triggered
        context = TriggerContext(
            message="Alice and Bob walked in",
            loaded_entities=[],
            response_count=1,
            rp_dir=temp_rp_dir,
            previous_triggers=[alice_path, bob_path],
        )

        results = coordinator.evaluate_triggers(patterns_list, context)

        # No results (all filtered)
        assert len(results) == 0


class TestResultRanking:
    """Test result ranking by type and confidence."""

    def test_keyword_ranked_higher_than_regex(self, temp_rp_dir, basic_context):
        """Test keyword matches ranked higher than regex."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Bob"})
        regex_eval = MockEvaluator("regex", "regex", matches={"Alice"})

        coordinator = TriggerCoordinator([keyword_eval, regex_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=["alice"],
                semantic_descriptions=[],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=["bob"],
                regex_patterns=[],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Bob (keyword) should rank before Alice (regex)
        assert len(results) == 2
        assert results[0].entity_name == "Bob"
        assert results[0].trigger_type == "keyword"
        assert results[1].entity_name == "Alice"
        assert results[1].trigger_type == "regex"

    def test_regex_ranked_higher_than_semantic(self, temp_rp_dir, basic_context):
        """Test regex matches ranked higher than semantic."""
        regex_eval = MockEvaluator("regex", "regex", matches={"Bob"})
        semantic_eval = MockEvaluator("semantic", "semantic", matches={"Alice"}, confidence=0.9)

        coordinator = TriggerCoordinator([regex_eval, semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Alice"],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=[],
                regex_patterns=["bob"],
                semantic_descriptions=[],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Bob (regex) should rank before Alice (semantic)
        assert len(results) == 2
        assert results[0].entity_name == "Bob"
        assert results[0].trigger_type == "regex"
        assert results[1].entity_name == "Alice"
        assert results[1].trigger_type == "semantic"

    def test_higher_confidence_semantic_ranked_higher(self, temp_rp_dir, basic_context):
        """Test semantic matches with higher confidence ranked higher."""
        semantic_eval = MockEvaluator("semantic", "semantic", matches={"Alice", "Bob"})

        # Override evaluate to return different confidences
        original_evaluate = semantic_eval.evaluate

        def custom_evaluate(patterns, context):
            result = original_evaluate(patterns, context)
            if result is not None:
                # Alice gets higher confidence
                if patterns.entity_name == "Alice":
                    result = TriggerResult(
                        file_path=result.file_path,
                        entity_name=result.entity_name,
                        trigger_type=result.trigger_type,
                        matched_pattern=result.matched_pattern,
                        confidence=0.95,
                        metadata=result.metadata,
                    )
                else:  # Bob
                    result = TriggerResult(
                        file_path=result.file_path,
                        entity_name=result.entity_name,
                        trigger_type=result.trigger_type,
                        matched_pattern=result.matched_pattern,
                        confidence=0.75,
                        metadata=result.metadata,
                    )
            return result

        semantic_eval.evaluate = custom_evaluate

        coordinator = TriggerCoordinator([semantic_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / "Alice.md",
                entity_name="Alice",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Alice"],
            ),
            TriggerPatterns(
                file_path=temp_rp_dir / "Bob.md",
                entity_name="Bob",
                keywords=[],
                regex_patterns=[],
                semantic_descriptions=["Bob"],
            ),
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Alice (0.95) should rank before Bob (0.75)
        assert len(results) == 2
        assert results[0].entity_name == "Alice"
        assert results[0].confidence == 0.95
        assert results[1].entity_name == "Bob"
        assert results[1].confidence == 0.75


class TestMaxResults:
    """Test max results limiting."""

    def test_max_results_default(self, temp_rp_dir, basic_context):
        """Test default max results is 10."""
        # Create 15 patterns that all match
        keyword_eval = MockEvaluator(
            "keyword",
            "keyword",
            matches={f"Entity{i}" for i in range(15)},
        )
        coordinator = TriggerCoordinator([keyword_eval])

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / f"Entity{i}.md",
                entity_name=f"Entity{i}",
                keywords=[f"entity{i}"],
                regex_patterns=[],
                semantic_descriptions=[],
            )
            for i in range(15)
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Should limit to 10 results (default)
        assert len(results) == 10

    def test_max_results_custom(self, temp_rp_dir, basic_context):
        """Test custom max results limit."""
        keyword_eval = MockEvaluator(
            "keyword",
            "keyword",
            matches={f"Entity{i}" for i in range(15)},
        )
        coordinator = TriggerCoordinator([keyword_eval], max_results=5)

        patterns_list = [
            TriggerPatterns(
                file_path=temp_rp_dir / f"Entity{i}.md",
                entity_name=f"Entity{i}",
                keywords=[f"entity{i}"],
                regex_patterns=[],
                semantic_descriptions=[],
            )
            for i in range(15)
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Should limit to 5 results
        assert len(results) == 5

    def test_max_results_not_reached(self, temp_rp_dir, basic_context):
        """Test when number of matches is below max results."""
        keyword_eval = MockEvaluator("keyword", "keyword", matches={"Alice", "Bob"})
        coordinator = TriggerCoordinator([keyword_eval], max_results=10)

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
        ]

        results = coordinator.evaluate_triggers(patterns_list, basic_context)

        # Should return all 2 results (below max)
        assert len(results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
