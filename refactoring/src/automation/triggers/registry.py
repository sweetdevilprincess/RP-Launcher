"""Trigger evaluator registry for extensibility.

Provides centralized registration and creation of trigger evaluators.
Supports configuration-based setup and custom evaluator plugins.
"""

from __future__ import annotations

from ...shared.interfaces.ai_client import AiClient
from ...shared.interfaces.config_service import ConfigService
from ...shared.logging import get_logger
from .keyword_evaluator import KeywordEvaluator
from .protocols import TriggerEvaluator
from .regex_evaluator import RegexEvaluator
from .semantic_evaluator import SemanticEvaluator


class TriggerRegistry:
    """Registry for creating and configuring trigger evaluators.

    This registry loads evaluator configurations and creates instances
    in the correct order for optimal performance:
    1. KeywordEvaluator (fastest, try first)
    2. RegexEvaluator (medium speed)
    3. SemanticEvaluator (slowest, try last, optional)

    The registry supports:
    - Configuration-based setup
    - Optional AI client for semantic evaluation
    - Extensibility for custom evaluators (future)

    Example:
        >>> config_service = JsonConfigService(config_file)
        >>> ai_client = ClaudeAiClient(api_key="...")
        >>> registry = TriggerRegistry(config_service, ai_client=ai_client)
        >>> evaluators = registry.create_evaluators()
        >>> # Returns [KeywordEvaluator, RegexEvaluator, SemanticEvaluator]
    """

    def __init__(
        self,
        config_service: ConfigService,
        *,
        ai_client: AiClient | None = None,
    ) -> None:
        """Initialize trigger registry.

        Args:
            config_service: Configuration service for loading settings
            ai_client: Optional AI client for semantic evaluation
        """
        self._config_service = config_service
        self._ai_client = ai_client
        self._logger = get_logger(__name__)

    def create_evaluators(self) -> list[TriggerEvaluator]:
        """Create configured trigger evaluators in optimal order.

        Returns:
            List of evaluators ordered by performance (fastest first)
        """
        evaluators: list[TriggerEvaluator] = []

        # Always create keyword evaluator (fastest, most reliable)
        keyword_eval = self._create_keyword_evaluator()
        evaluators.append(keyword_eval)

        # Always create regex evaluator
        regex_eval = self._create_regex_evaluator()
        evaluators.append(regex_eval)

        # Optionally create semantic evaluator if AI client available
        if self._should_use_semantic_evaluation():
            semantic_eval = self._create_semantic_evaluator()
            evaluators.append(semantic_eval)

        self._logger.info(
            "trigger_registry.evaluators_created",
            context={
                "evaluator_count": len(evaluators),
                "evaluator_types": [type(e).__name__ for e in evaluators],
            },
        )

        return evaluators

    def _create_keyword_evaluator(self) -> KeywordEvaluator:
        """Create keyword evaluator from configuration.

        Returns:
            Configured KeywordEvaluator
        """
        # Load configuration with defaults
        case_sensitive = self._config_service.get_bool(
            "triggers.keyword.case_sensitive", default=False
        )
        use_word_boundaries = self._config_service.get_bool(
            "triggers.keyword.use_word_boundaries", default=True
        )

        return KeywordEvaluator(
            case_sensitive=case_sensitive,
            use_word_boundaries=use_word_boundaries,
        )

    def _create_regex_evaluator(self) -> RegexEvaluator:
        """Create regex evaluator from configuration.

        Returns:
            Configured RegexEvaluator
        """
        # Load configuration with defaults
        case_sensitive = self._config_service.get_bool(
            "triggers.regex.case_sensitive", default=False
        )
        max_patterns_per_file = self._config_service.get_int(
            "triggers.regex.max_patterns_per_file", default=10
        )

        return RegexEvaluator(
            case_sensitive=case_sensitive,
            max_patterns_per_file=max_patterns_per_file,
        )

    def _create_semantic_evaluator(self) -> SemanticEvaluator:
        """Create semantic evaluator from configuration.

        Returns:
            Configured SemanticEvaluator
        """
        # Load configuration with defaults
        confidence_threshold = self._config_service.get_float(
            "triggers.semantic.confidence_threshold", default=0.7
        )

        return SemanticEvaluator(
            ai_client=self._ai_client,
            confidence_threshold=confidence_threshold,
        )

    def _should_use_semantic_evaluation(self) -> bool:
        """Check if semantic evaluation should be enabled.

        Returns:
            True if semantic evaluation is available and enabled
        """
        # Check if AI client is available
        if self._ai_client is None:
            return False

        # Check if semantic evaluation is enabled in config
        enabled = self._config_service.get_bool("triggers.semantic.enabled", default=True)

        return enabled
