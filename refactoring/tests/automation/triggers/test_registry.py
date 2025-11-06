"""Unit tests for TriggerRegistry.

Tests trigger evaluator registration and creation:
- Evaluator creation and configuration
- Configuration-based setup
- AI client integration
- Evaluator ordering
"""

from typing import Any

import pytest
from refactoring.src.automation.triggers.keyword_evaluator import KeywordEvaluator
from refactoring.src.automation.triggers.regex_evaluator import RegexEvaluator
from refactoring.src.automation.triggers.registry import TriggerRegistry
from refactoring.src.automation.triggers.semantic_evaluator import SemanticEvaluator


class MockConfigService:
    """Mock configuration service for testing."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize mock config service.

        Args:
            config: Configuration dict
        """
        self.config = config or {}

    def get_bool(self, key: str, *, default: bool = False) -> bool:
        """Get boolean config value."""
        return self.config.get(key, default)

    def get_int(self, key: str, *, default: int = 0) -> int:
        """Get integer config value."""
        return self.config.get(key, default)

    def get_float(self, key: str, *, default: float = 0.0) -> float:
        """Get float config value."""
        return self.config.get(key, default)

    def get_str(self, key: str, *, default: str = "") -> str:
        """Get string config value."""
        return self.config.get(key, default)

    def get_dict(self, key: str, *, default: dict | None = None) -> dict:
        """Get dict config value."""
        return self.config.get(key, default or {})


class MockAiClient:
    """Mock AI client for testing."""

    def evaluate_semantic_match(
        self, message: str, descriptions: list[str], entity_name: str
    ) -> tuple[bool, float]:
        """Mock semantic match evaluation."""
        return (True, 0.85)


class TestEvaluatorCreation:
    """Test evaluator creation."""

    def test_creates_keyword_evaluator(self):
        """Test keyword evaluator is always created."""
        config = MockConfigService()
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()

        # Should have at least keyword and regex
        assert len(evaluators) >= 2
        assert isinstance(evaluators[0], KeywordEvaluator)

    def test_creates_regex_evaluator(self):
        """Test regex evaluator is always created."""
        config = MockConfigService()
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()

        assert len(evaluators) >= 2
        assert isinstance(evaluators[1], RegexEvaluator)

    def test_creates_semantic_evaluator_with_ai_client(self):
        """Test semantic evaluator is created when AI client provided."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert len(evaluators) == 3
        assert isinstance(evaluators[2], SemanticEvaluator)

    def test_no_semantic_evaluator_without_ai_client(self):
        """Test semantic evaluator is not created without AI client."""
        config = MockConfigService()
        registry = TriggerRegistry(config, ai_client=None)

        evaluators = registry.create_evaluators()

        assert len(evaluators) == 2
        # Only keyword and regex
        assert isinstance(evaluators[0], KeywordEvaluator)
        assert isinstance(evaluators[1], RegexEvaluator)


class TestEvaluatorOrdering:
    """Test evaluator ordering for performance."""

    def test_keyword_first(self):
        """Test keyword evaluator is first (fastest)."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert isinstance(evaluators[0], KeywordEvaluator)

    def test_regex_second(self):
        """Test regex evaluator is second."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert isinstance(evaluators[1], RegexEvaluator)

    def test_semantic_last(self):
        """Test semantic evaluator is last (slowest)."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert isinstance(evaluators[2], SemanticEvaluator)


class TestKeywordEvaluatorConfig:
    """Test keyword evaluator configuration."""

    def test_default_keyword_config(self):
        """Test keyword evaluator uses default configuration."""
        config = MockConfigService()
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        keyword_eval = evaluators[0]

        # Defaults: case_sensitive=False, use_word_boundaries=True
        assert keyword_eval.case_sensitive is False
        assert keyword_eval.use_word_boundaries is True

    def test_custom_keyword_case_sensitive(self):
        """Test custom case_sensitive configuration."""
        config = MockConfigService({"triggers.keyword.case_sensitive": True})
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        keyword_eval = evaluators[0]

        assert keyword_eval.case_sensitive is True

    def test_custom_keyword_word_boundaries(self):
        """Test custom use_word_boundaries configuration."""
        config = MockConfigService({"triggers.keyword.use_word_boundaries": False})
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        keyword_eval = evaluators[0]

        assert keyword_eval.use_word_boundaries is False

    def test_custom_keyword_both_settings(self):
        """Test both keyword settings customized."""
        config = MockConfigService(
            {
                "triggers.keyword.case_sensitive": True,
                "triggers.keyword.use_word_boundaries": False,
            }
        )
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        keyword_eval = evaluators[0]

        assert keyword_eval.case_sensitive is True
        assert keyword_eval.use_word_boundaries is False


class TestRegexEvaluatorConfig:
    """Test regex evaluator configuration."""

    def test_default_regex_config(self):
        """Test regex evaluator uses default configuration."""
        config = MockConfigService()
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        regex_eval = evaluators[1]

        # Defaults: case_sensitive=False, max_patterns=10
        assert regex_eval.case_sensitive is False
        assert regex_eval.max_patterns_per_file == 10

    def test_custom_regex_case_sensitive(self):
        """Test custom case_sensitive configuration."""
        config = MockConfigService({"triggers.regex.case_sensitive": True})
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        regex_eval = evaluators[1]

        assert regex_eval.case_sensitive is True

    def test_custom_regex_max_patterns(self):
        """Test custom max_patterns_per_file configuration."""
        config = MockConfigService({"triggers.regex.max_patterns_per_file": 5})
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        regex_eval = evaluators[1]

        assert regex_eval.max_patterns_per_file == 5

    def test_custom_regex_both_settings(self):
        """Test both regex settings customized."""
        config = MockConfigService(
            {
                "triggers.regex.case_sensitive": True,
                "triggers.regex.max_patterns_per_file": 20,
            }
        )
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()
        regex_eval = evaluators[1]

        assert regex_eval.case_sensitive is True
        assert regex_eval.max_patterns_per_file == 20


class TestSemanticEvaluatorConfig:
    """Test semantic evaluator configuration."""

    def test_default_semantic_config(self):
        """Test semantic evaluator uses default configuration."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()
        semantic_eval = evaluators[2]

        # Default: confidence_threshold=0.7
        assert semantic_eval.confidence_threshold == 0.7
        assert semantic_eval.ai_client is ai_client

    def test_custom_semantic_confidence_threshold(self):
        """Test custom confidence_threshold configuration."""
        config = MockConfigService({"triggers.semantic.confidence_threshold": 0.85})
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()
        semantic_eval = evaluators[2]

        assert semantic_eval.confidence_threshold == 0.85

    def test_semantic_disabled_in_config(self):
        """Test semantic evaluator can be disabled in config."""
        config = MockConfigService({"triggers.semantic.enabled": False})
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        # Should only have keyword and regex (semantic disabled)
        assert len(evaluators) == 2
        assert isinstance(evaluators[0], KeywordEvaluator)
        assert isinstance(evaluators[1], RegexEvaluator)

    def test_semantic_enabled_by_default(self):
        """Test semantic evaluator is enabled by default if AI client available."""
        config = MockConfigService()  # No explicit enabled setting
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        # Should have all three (enabled by default)
        assert len(evaluators) == 3


class TestAiClientIntegration:
    """Test AI client integration."""

    def test_ai_client_passed_to_semantic_evaluator(self):
        """Test AI client is passed to semantic evaluator."""
        config = MockConfigService()
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()
        semantic_eval = evaluators[2]

        assert semantic_eval.ai_client is ai_client

    def test_none_ai_client_skips_semantic(self):
        """Test None AI client skips semantic evaluator creation."""
        config = MockConfigService()
        registry = TriggerRegistry(config, ai_client=None)

        evaluators = registry.create_evaluators()

        # Should not have semantic evaluator
        assert all(not isinstance(e, SemanticEvaluator) for e in evaluators)


class TestEvaluatorCount:
    """Test evaluator count under different configurations."""

    def test_count_without_ai_client(self):
        """Test evaluator count without AI client."""
        config = MockConfigService()
        registry = TriggerRegistry(config)

        evaluators = registry.create_evaluators()

        assert len(evaluators) == 2

    def test_count_with_ai_client_enabled(self):
        """Test evaluator count with AI client and enabled."""
        config = MockConfigService({"triggers.semantic.enabled": True})
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert len(evaluators) == 3

    def test_count_with_ai_client_disabled(self):
        """Test evaluator count with AI client but disabled."""
        config = MockConfigService({"triggers.semantic.enabled": False})
        ai_client = MockAiClient()
        registry = TriggerRegistry(config, ai_client=ai_client)

        evaluators = registry.create_evaluators()

        assert len(evaluators) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
