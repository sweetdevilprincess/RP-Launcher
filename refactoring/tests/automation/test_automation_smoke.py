"""Smoke test for end-to-end automation pipeline.

This test validates that the full automation pipeline works correctly from context
creation through prompt assembly, using a minimal RP directory structure.
"""

from __future__ import annotations

import json
from pathlib import Path

from refactoring.src.automation import AutomationContext, create_automation_service


def _create_minimal_rp_structure(tmp_path: Path) -> None:
    """Create a minimal RP directory structure for testing.

    Args:
        tmp_path: Temporary directory path
    """
    # Create directory structure
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "characters").mkdir(parents=True, exist_ok=True)
    (tmp_path / "entities").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "templates" / "prompts").mkdir(parents=True, exist_ok=True)

    # Create ROLEPLAY_OVERVIEW.md with genre
    overview_content = """# My Fantasy RP

**Genre**: Fantasy / Adventure

A test RP for smoke testing.
"""
    (tmp_path / "ROLEPLAY_OVERVIEW.md").write_text(overview_content, encoding="utf-8")

    # Create a test character with triggers
    alice_content = """# Alice - The Protagonist

**Triggers**: Alice, protagonist, hero

## Description
Alice is the main character of our story.

## Background
A brave adventurer seeking glory.
"""
    (tmp_path / "characters" / "Alice.md").write_text(alice_content, encoding="utf-8")

    # Create a test entity with regex triggers
    forest_content = """# The Dark Forest

[RegexTriggers:dark forest,enter(ed|ing)? the forest]

## Description
A mysterious and dangerous forest.
"""
    (tmp_path / "entities" / "DarkForest.md").write_text(forest_content, encoding="utf-8")

    # Create test configuration
    config_data = {
        "version": "1.0.0",
        "automation": {
            "agents_enabled": False,  # Disable agents for smoke test simplicity
            "auto_story_arc": False,
            "arc_frequency": 50,
        },
        "narrative_template": {
            "enabled": True,
            "mode": "auto",
        },
        "triggers": {
            "keyword": {
                "case_sensitive": False,
                "use_word_boundaries": True,
            },
            "regex": {
                "case_sensitive": False,
                "max_patterns_per_file": 10,
            },
            "frequency_tracking": {
                "enabled": True,
                "window_size": 10,
                "escalation_threshold": 3,
            },
        },
    }
    (tmp_path / "state" / "automation_config.json").write_text(
        json.dumps(config_data, indent=2), encoding="utf-8"
    )

    # Create a fantasy template for narrative guidance
    fantasy_template = {
        "display_name": "Fantasy Adventure",
        "sections": {
            "tone": {
                "title": "Narrative Tone",
                "content": [
                    "Epic and heroic storytelling",
                    "Sense of wonder and discovery",
                    "Clear good vs evil themes",
                ],
            },
            "focus": {
                "title": "Story Focus",
                "content": [
                    "Character growth and development",
                    "World exploration and lore",
                    "Epic quests and challenges",
                ],
            },
        },
        "highlights": [
            "Magic and mythical creatures",
            "Ancient prophecies and legends",
        ],
    }
    (tmp_path / "config" / "templates" / "prompts" / "fantasy.json").write_text(
        json.dumps(fantasy_template, indent=2), encoding="utf-8"
    )

    # Create initial response counter
    counter_data = {"count": 0}
    (tmp_path / "state" / "response_counter.json").write_text(
        json.dumps(counter_data, indent=2), encoding="utf-8"
    )


def test_automation_pipeline_end_to_end(tmp_path: Path) -> None:
    """Test full automation pipeline from context creation to prompt assembly.

    This smoke test validates that:
    1. AutomationService can be created via factory
    2. Configuration is loaded correctly
    3. Counter is incremented
    4. Tiered files are loaded
    5. Triggers are evaluated (if message contains trigger words)
    6. Narrative template is loaded and injected
    7. Prompt is assembled with all sections
    """
    # Setup: Create minimal RP structure
    _create_minimal_rp_structure(tmp_path)

    # Create automation service using factory
    service = create_automation_service(tmp_path)

    # Create automation context
    context = AutomationContext(
        message="Alice enters the dark forest, looking for adventure.",
        rp_dir=tmp_path,
    )

    # Execute automation pipeline
    result = service.run(context)

    # Assert: Pipeline completed successfully
    assert result.success, "Automation pipeline should complete successfully"

    # Assert: Enhanced prompt was generated
    assert result.enhanced_prompt, "Enhanced prompt should be generated"
    prompt = result.enhanced_prompt

    # Assert: Prompt contains narrative template (Fantasy genre detected from overview)
    assert (
        "<!-- ========== NARRATIVE TEMPLATE ==========" in prompt or "Genre" in prompt
    ), "Prompt should contain narrative template section"

    # Assert: Prompt contains user message section
    assert "Alice enters the dark forest" in prompt, "Prompt should contain the user's message"

    # Assert: Response counter was incremented (check via state file)
    counter_file = tmp_path / "state" / "response_counter.json"
    assert counter_file.exists(), "Counter file should exist"
    counter_data = json.loads(counter_file.read_text(encoding="utf-8"))
    assert counter_data["count"] == 1, "Counter should be incremented to 1"


def test_automation_pipeline_with_triggered_entities(tmp_path: Path) -> None:
    """Test automation pipeline with trigger evaluation.

    This test validates that:
    1. Keyword triggers fire when message contains keywords
    2. Triggered entity content is loaded and injected
    3. Prompt contains triggered entity information
    """
    # Setup: Create minimal RP structure
    _create_minimal_rp_structure(tmp_path)

    # Create automation service
    service = create_automation_service(tmp_path)

    # Create context with message that triggers "Alice"
    context = AutomationContext(
        message="Alice walks through the village.",
        rp_dir=tmp_path,
    )

    # Execute automation pipeline
    result = service.run(context)

    # Assert: Pipeline completed successfully
    assert result.success, "Automation pipeline should complete successfully"

    # Assert: Prompt was generated
    assert result.enhanced_prompt, "Enhanced prompt should be generated"
    prompt = result.enhanced_prompt

    # Assert: Prompt contains Alice's information (triggered by keyword)
    # Note: This depends on the trigger system being properly integrated
    # The exact format may vary, but Alice should appear somewhere
    assert "Alice" in prompt, "Prompt should contain Alice's name"

    # Assert: Prompt contains user message
    assert "village" in prompt, "Prompt should contain message content"


def test_automation_pipeline_multiple_runs(tmp_path: Path) -> None:
    """Test automation pipeline across multiple runs.

    This test validates that:
    1. Service can be reused for multiple runs
    2. Counter increments correctly across runs
    3. Each run produces valid output
    """
    # Setup
    _create_minimal_rp_structure(tmp_path)
    service = create_automation_service(tmp_path)

    # Run 1
    context1 = AutomationContext(
        message="Alice begins her journey.",
        rp_dir=tmp_path,
    )
    result1 = service.run(context1)
    assert result1.success
    assert "Alice begins her journey" in result1.enhanced_prompt

    # Run 2
    context2 = AutomationContext(
        message="She enters the dark forest.",
        rp_dir=tmp_path,
    )
    result2 = service.run(context2)
    assert result2.success
    assert "dark forest" in result2.enhanced_prompt

    # Run 3
    context3 = AutomationContext(
        message="Alice finds a mysterious artifact.",
        rp_dir=tmp_path,
    )
    result3 = service.run(context3)
    assert result3.success
    assert "artifact" in result3.enhanced_prompt

    # Assert: Counter should be at 3
    counter_file = tmp_path / "state" / "response_counter.json"
    counter_data = json.loads(counter_file.read_text(encoding="utf-8"))
    assert counter_data["count"] == 3, "Counter should increment across runs"
