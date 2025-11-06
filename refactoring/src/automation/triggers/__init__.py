"""Trigger evaluation system for conditional file loading.

This module provides a flexible, extensible trigger system for determining
which files should be loaded based on user messages.

Core Components:
- TriggerEvaluator: Protocol for different matching strategies
- TriggerContext: Input data for evaluation
- TriggerResult: Match results
- TriggerRegistry: Extensible registry of evaluators
- TriggerCoordinator: Orchestrates evaluation and frequency tracking

Evaluators:
- KeywordEvaluator: Fast keyword matching
- RegexEvaluator: Pattern-based matching
- SemanticEvaluator: AI-powered semantic understanding (optional)
"""

from .coordinator import TriggerCoordinator
from .frequency_tracker import FrequencyTracker
from .keyword_evaluator import KeywordEvaluator
from .pattern_loader import PatternLoader
from .protocols import (
    TriggerContext,
    TriggerEvaluator,
    TriggerPatterns,
    TriggerResult,
)
from .regex_evaluator import RegexEvaluator
from .registry import TriggerRegistry
from .semantic_evaluator import SemanticEvaluator

__all__ = [
    "FrequencyTracker",
    "KeywordEvaluator",
    "PatternLoader",
    "RegexEvaluator",
    "SemanticEvaluator",
    "TriggerContext",
    "TriggerCoordinator",
    "TriggerEvaluator",
    "TriggerPatterns",
    "TriggerRegistry",
    "TriggerResult",
]
