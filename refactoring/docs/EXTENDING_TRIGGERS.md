# Extending the Trigger System

This guide explains how to add custom trigger evaluators to the trigger system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Creating a Custom Evaluator](#creating-a-custom-evaluator)
- [Protocol Requirements](#protocol-requirements)
- [Example: Proximity Evaluator](#example-proximity-evaluator)
- [Testing Your Evaluator](#testing-your-evaluator)
- [Integration](#integration)
- [Best Practices](#best-practices)

## Overview

The trigger system uses a plugin-based architecture where different evaluators can be added to detect when character/location files should be loaded. The system comes with three built-in evaluators:

- **KeywordEvaluator**: Matches exact keywords (fastest, most reliable)
- **RegexEvaluator**: Matches regex patterns (flexible, reliable)
- **SemanticEvaluator**: AI-powered semantic matching (slowest, most flexible)

You can add custom evaluators for specialized matching logic.

## Architecture

### Core Components

```
TriggerCoordinator
├── Evaluator 1 (e.g., KeywordEvaluator)
├── Evaluator 2 (e.g., RegexEvaluator)
├── Evaluator 3 (e.g., SemanticEvaluator)
└── Your Custom Evaluator
```

**Key Concepts:**

1. **Evaluators are tried in order**: The coordinator tries evaluators sequentially for each pattern file
2. **First match wins**: Once an evaluator matches, others are skipped for that file (performance optimization)
3. **Protocol-based**: Evaluators implement the `TriggerEvaluator` protocol
4. **Batch support**: Evaluators can optimize batch evaluation

### Data Flow

```
User Message
    ↓
TriggerContext (message, loaded_entities, response_count, etc.)
    ↓
TriggerCoordinator.evaluate_triggers(patterns_list, context)
    ↓
For each TriggerPatterns:
    → Try Evaluator 1.evaluate(patterns, context) → TriggerResult or None
    → If None, try Evaluator 2.evaluate(patterns, context)
    → If None, try Evaluator 3.evaluate(patterns, context)
    → ...
    ↓
Filter recent triggers, rank results, limit to max_results
    ↓
List[TriggerResult]
```

## Creating a Custom Evaluator

### Step 1: Understand the Protocol

Your evaluator must implement the `TriggerEvaluator` protocol:

```python
from refactoring.src.automation.triggers.protocols import (
    TriggerEvaluator,
    TriggerPatterns,
    TriggerContext,
    TriggerResult,
)

class TriggerEvaluator(Protocol):
    """Protocol for trigger evaluation strategies."""

    def evaluate(
        self, patterns: TriggerPatterns, context: TriggerContext
    ) -> Optional[TriggerResult]:
        """Evaluate if patterns match the context.

        Returns:
            TriggerResult if match found, None otherwise
        """
        ...

    def evaluate_batch(
        self, patterns_list: List[TriggerPatterns], context: TriggerContext
    ) -> List[TriggerResult]:
        """Evaluate multiple pattern sets (optional optimization).

        Default implementation calls evaluate() for each pattern.
        """
        ...
```

### Step 2: Define Your Data Structures

Decide what data your evaluator needs from pattern files:

**TriggerPatterns fields:**
- `file_path: Path` - Path to the character/location file
- `entity_name: str` - Name of the character/location
- `keywords: list[str]` - Keywords (used by KeywordEvaluator)
- `regex_patterns: list[str]` - Regex patterns (used by RegexEvaluator)
- `semantic_descriptions: list[str]` - Semantic descriptions (used by SemanticEvaluator)

**You can add custom fields** to `TriggerPatterns` in `protocols.py` if needed.

**TriggerContext fields:**
- `message: str` - The user's message to evaluate
- `loaded_entities: list[str]` - Currently loaded entities
- `response_count: int` - Number of responses in this session
- `rp_dir: Path` - Path to RP directory
- `previous_triggers: Optional[list[Path]]` - Recently triggered files

### Step 3: Implement Your Evaluator

Create a new file in `src/automation/triggers/` (e.g., `proximity_evaluator.py`):

```python
"""Proximity-based trigger evaluation.

Triggers entities when they are mentioned near already-loaded entities.
"""

from __future__ import annotations

from typing import List, Optional

from ...shared.logging import get_logger
from .protocols import TriggerContext, TriggerPatterns, TriggerResult


class ProximityEvaluator:
    """Evaluates triggers based on proximity to loaded entities.

    This evaluator triggers entities that are frequently mentioned
    in proximity to already-loaded entities, suggesting relevance.

    Configuration:
        proximity_window: Number of words to consider "near" (default: 50)
        min_occurrences: Minimum co-occurrences to trigger (default: 2)

    Example:
        >>> evaluator = ProximityEvaluator(proximity_window=50, min_occurrences=2)
        >>> patterns = TriggerPatterns(
        ...     file_path=Path("chars/Bob.md"),
        ...     entity_name="Bob",
        ...     keywords=["bob"],
        ...     ...
        ... )
        >>> context = TriggerContext(
        ...     message="Alice and Bob went shopping. Bob paid.",
        ...     loaded_entities=["Alice"],
        ...     ...
        ... )
        >>> result = evaluator.evaluate(patterns, context)
        >>> result.confidence
        0.85
    """

    def __init__(
        self,
        *,
        proximity_window: int = 50,
        min_occurrences: int = 2,
    ) -> None:
        """Initialize proximity evaluator.

        Args:
            proximity_window: Word distance to consider "near"
            min_occurrences: Minimum co-occurrences to trigger
        """
        self.proximity_window = proximity_window
        self.min_occurrences = min_occurrences
        self._logger = get_logger(__name__)

    def evaluate(
        self, patterns: TriggerPatterns, context: TriggerContext
    ) -> Optional[TriggerResult]:
        """Evaluate if entity is mentioned near loaded entities.

        Args:
            patterns: Trigger patterns for entity
            context: Context with message and loaded entities

        Returns:
            TriggerResult if entity mentioned near loaded entities
        """
        # Skip if no loaded entities to compare against
        if not context.loaded_entities:
            return None

        # Skip if no keywords to search for
        if not patterns.keywords:
            return None

        # Tokenize message into words
        words = context.message.lower().split()

        # Find positions of entity keywords
        entity_positions = []
        for i, word in enumerate(words):
            if any(keyword.lower() in word for keyword in patterns.keywords):
                entity_positions.append(i)

        # Find positions of loaded entity names
        loaded_positions = []
        for i, word in enumerate(words):
            if any(entity.lower() in word for entity in context.loaded_entities):
                loaded_positions.append(i)

        # Count co-occurrences within proximity window
        co_occurrences = 0
        for entity_pos in entity_positions:
            for loaded_pos in loaded_positions:
                if abs(entity_pos - loaded_pos) <= self.proximity_window:
                    co_occurrences += 1
                    break  # Count each entity mention once

        # Check if meets threshold
        if co_occurrences < self.min_occurrences:
            return None

        # Calculate confidence based on co-occurrence strength
        confidence = min(1.0, co_occurrences / (self.min_occurrences * 2))

        self._logger.debug(
            "proximity_evaluator.match",
            context={
                "entity": patterns.entity_name,
                "co_occurrences": co_occurrences,
                "confidence": confidence,
            },
        )

        return TriggerResult(
            file_path=patterns.file_path,
            entity_name=patterns.entity_name,
            trigger_type="proximity",
            matched_pattern=f"{co_occurrences} co-occurrences",
            confidence=confidence,
            metadata={
                "proximity_window": self.proximity_window,
                "min_occurrences": self.min_occurrences,
                "co_occurrences": co_occurrences,
            },
        )

    def evaluate_batch(
        self, patterns_list: List[TriggerPatterns], context: TriggerContext
    ) -> List[TriggerResult]:
        """Evaluate multiple patterns (can be optimized).

        Default implementation: evaluate each individually.
        """
        results: List[TriggerResult] = []

        for patterns in patterns_list:
            result = self.evaluate(patterns, context)
            if result is not None:
                results.append(result)

        return results
```

## Protocol Requirements

Your evaluator **must** implement:

1. **`evaluate(patterns, context) -> Optional[TriggerResult]`**
   - Return `TriggerResult` if match found
   - Return `None` if no match
   - Should be deterministic and fast

2. **`evaluate_batch(patterns_list, context) -> List[TriggerResult]`**
   - Can use default implementation (call `evaluate()` for each)
   - Or optimize for batch processing

### TriggerResult Structure

When creating a `TriggerResult`, include:

```python
TriggerResult(
    file_path=patterns.file_path,           # Path to triggered file
    entity_name=patterns.entity_name,       # Entity name
    trigger_type="your_type",               # Your evaluator's type name
    matched_pattern="what matched",         # Description of what matched
    confidence=0.85,                        # Confidence score 0.0-1.0
    metadata={                              # Optional metadata
        "custom_field": value,
        ...
    },
)
```

## Testing Your Evaluator

Create comprehensive tests in `tests/automation/triggers/test_your_evaluator.py`:

```python
"""Unit tests for ProximityEvaluator."""

import tempfile
from pathlib import Path

import pytest

from refactoring.src.automation.triggers.proximity_evaluator import ProximityEvaluator
from refactoring.src.automation.triggers.protocols import (
    TriggerContext,
    TriggerPatterns,
)


@pytest.fixture
def temp_rp_dir():
    """Create temporary RP directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir) / "test_rp"
        rp_dir.mkdir()
        yield rp_dir


@pytest.fixture
def bob_patterns(temp_rp_dir):
    """Create patterns for Bob."""
    return TriggerPatterns(
        file_path=temp_rp_dir / "Bob.md",
        entity_name="Bob",
        keywords=["bob"],
        regex_patterns=[],
        semantic_descriptions=[],
    )


class TestProximityEvaluator:
    """Test proximity-based triggering."""

    def test_triggers_when_near_loaded_entity(self, bob_patterns, temp_rp_dir):
        """Test entity triggers when mentioned near loaded entity."""
        evaluator = ProximityEvaluator(proximity_window=10, min_occurrences=1)

        context = TriggerContext(
            message="Alice and Bob went shopping together",
            loaded_entities=["Alice"],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(bob_patterns, context)

        assert result is not None
        assert result.entity_name == "Bob"
        assert result.trigger_type == "proximity"

    def test_no_trigger_when_far_from_loaded_entity(self, bob_patterns, temp_rp_dir):
        """Test no trigger when entity too far from loaded entities."""
        evaluator = ProximityEvaluator(proximity_window=2, min_occurrences=1)

        # Bob is 5 words away from Alice (outside window of 2)
        context = TriggerContext(
            message="Alice walked home. Later, Bob arrived.",
            loaded_entities=["Alice"],
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(bob_patterns, context)

        assert result is None

    def test_no_trigger_without_loaded_entities(self, bob_patterns, temp_rp_dir):
        """Test no trigger when no entities loaded."""
        evaluator = ProximityEvaluator()

        context = TriggerContext(
            message="Bob went shopping",
            loaded_entities=[],  # No loaded entities
            response_count=1,
            rp_dir=temp_rp_dir,
        )

        result = evaluator.evaluate(bob_patterns, context)

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run your tests:
```bash
pytest tests/automation/triggers/test_proximity_evaluator.py -v
```

## Integration

### Step 1: Register in TriggerRegistry

Modify `src/automation/triggers/registry.py` to include your evaluator:

```python
from .proximity_evaluator import ProximityEvaluator

class TriggerRegistry:
    """Registry for trigger evaluators."""

    def create_evaluators(
        self,
        *,
        ai_client: Optional[AiClient] = None,
    ) -> List[TriggerEvaluator]:
        """Create default evaluators in priority order."""
        evaluators: List[TriggerEvaluator] = [
            KeywordEvaluator(case_sensitive=False, use_word_boundaries=True),
            RegexEvaluator(case_sensitive=False, max_patterns=10),
            ProximityEvaluator(proximity_window=50, min_occurrences=2),  # Add here
            SemanticEvaluator(ai_client=ai_client, confidence_threshold=0.7),
        ]
        return evaluators
```

### Step 2: Position in Priority Order

**Order matters!** Evaluators are tried sequentially:

- **Fast, reliable evaluators first** (keyword, regex)
- **Custom evaluators in the middle** (your evaluator)
- **Slow, expensive evaluators last** (semantic/AI)

### Step 3: Update Pattern Loader (if needed)

If your evaluator uses custom pattern fields, update `pattern_loader.py`:

```python
def _extract_patterns(self, file_path: Path, content: str) -> TriggerPatterns:
    """Extract trigger patterns from file content."""
    # ... existing extraction ...

    # Add custom field extraction
    proximity_keywords = self._extract_proximity_keywords(content)

    return TriggerPatterns(
        file_path=file_path,
        entity_name=entity_name,
        keywords=keywords,
        regex_patterns=regex_patterns,
        semantic_descriptions=semantic_descriptions,
        proximity_keywords=proximity_keywords,  # Your custom field
    )
```

## Best Practices

### Performance

1. **Fail fast**: Return `None` early if evaluation can't succeed
2. **Cache expensive computations**: Store compiled patterns, processed data
3. **Optimize batch operations**: Override `evaluate_batch()` if you can optimize
4. **Consider order**: Place your evaluator appropriately in the priority list

### Reliability

1. **Handle edge cases**: Empty inputs, missing data, malformed patterns
2. **Use try/except**: Catch and log exceptions, don't crash the system
3. **Validate inputs**: Check for None, empty lists, invalid data
4. **Test thoroughly**: Cover happy path, edge cases, error cases

### Logging

Use structured logging for debugging:

```python
from ...shared.logging import get_logger

class YourEvaluator:
    def __init__(self):
        self._logger = get_logger(__name__)

    def evaluate(self, patterns, context):
        self._logger.debug(
            "your_evaluator.evaluation_start",
            context={
                "entity": patterns.entity_name,
                "message_length": len(context.message),
            },
        )

        # ... evaluation logic ...

        if result:
            self._logger.info(
                "your_evaluator.match_found",
                context={
                    "entity": patterns.entity_name,
                    "confidence": result.confidence,
                },
            )
```

### Confidence Scores

- **Use 0.0-1.0 range**: 0.0 = no confidence, 1.0 = absolute certainty
- **Keyword/Regex**: Usually 1.0 (exact matches)
- **Heuristic evaluators**: Variable confidence based on match strength
- **AI evaluators**: Use model's confidence score

### Metadata

Include useful debugging info in `metadata`:

```python
TriggerResult(
    ...,
    metadata={
        "config": {"window": self.window_size},
        "match_details": {"score": 42, "threshold": 30},
        "debug_info": {"processed_tokens": 100},
    },
)
```

### Testing

1. **Unit tests**: Test evaluator in isolation
2. **Integration tests**: Test with TriggerCoordinator
3. **Edge cases**: Empty inputs, special characters, long messages
4. **Performance tests**: Ensure evaluator is fast enough
5. **Batch tests**: Verify `evaluate_batch()` works correctly

## Example Use Cases

### Sentiment Evaluator

Trigger characters when emotional content matches their personality:

```python
class SentimentEvaluator:
    """Triggers based on message sentiment."""

    def evaluate(self, patterns, context):
        # Analyze sentiment of message
        sentiment = analyze_sentiment(context.message)

        # Check if matches character's sentiment tags
        if sentiment in patterns.sentiment_tags:
            return TriggerResult(...)

        return None
```

### Temporal Evaluator

Trigger based on time-related mentions:

```python
class TemporalEvaluator:
    """Triggers when temporal references match character availability."""

    def evaluate(self, patterns, context):
        # Extract time references from message
        time_refs = extract_time_references(context.message)

        # Check if character is available at those times
        if any(ref in patterns.available_times for ref in time_refs):
            return TriggerResult(...)

        return None
```

### Relationship Evaluator

Trigger characters based on relationship graphs:

```python
class RelationshipEvaluator:
    """Triggers characters related to loaded entities."""

    def __init__(self, relationship_graph):
        self.relationships = relationship_graph

    def evaluate(self, patterns, context):
        # Check if entity has relationships with loaded entities
        for loaded_entity in context.loaded_entities:
            if self.relationships.are_related(patterns.entity_name, loaded_entity):
                return TriggerResult(...)

        return None
```

## Summary

1. Implement `TriggerEvaluator` protocol
2. Create comprehensive tests
3. Register in `TriggerRegistry`
4. Position appropriately in priority order
5. Follow best practices for performance and reliability

For questions or issues, refer to existing evaluators in `src/automation/triggers/`.
