#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test wizard RP creation without running the TUI."""

import sys
from pathlib import Path
from src.infrastructure.rp_initialization import RPCreator

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Test data matching what the wizard would collect
test_data = {
    "template": "fantasy_adventure",  # TEST WITH TEMPLATE
    "rp_name": "Test Adventure",
    "genre": "fantasy",
    "setting": "Medieval fantasy kingdom",
    "premise": "A young hero embarks on a quest to save their village from an ancient evil.",
    "content_rating": "PG-13",
    "tone": "Heroic and adventurous",
    "writing_style": "Descriptive with action",
    "time_period": "Medieval",
    "world_notes": "Magic exists through ancient artifacts",
    "primary_culture": "Celtic-inspired",
    "starting_location": "Village of Willowbrook",
    "starting_time": "Dawn",
    "starting_atmosphere": "Peaceful but tense",
    "user_char_name": "Aria",
    "user_age": "20",
    "user_gender": "Female",
    "user_appearance": "Tall with auburn hair and green eyes",
    "user_personality": "Brave, curious, and compassionate",
    "main_npc_name": "Elder Moren",
    "npc_age": "65",
    "npc_gender": "Male",
    "npc_appearance": "Wise-looking with a long white beard",
    "npc_personality": "Patient, knowledgeable, mysterious",
    "primary_provider": "openai",
    "primary_api_key": "test-key",
    "temperature": "0.7",
    "max_tokens": "2048",
    "system_prompt": "",
    "secondary_provider": "same",
    "secondary_api_key": "",
}

def test_rp_creation():
    """Test creating an RP with the wizard data."""
    print("Testing RP creation...")

    # Use a test directory
    test_dir = Path("test_rps_output")
    test_dir.mkdir(exist_ok=True)

    try:
        # Create RP
        creator = RPCreator(test_dir)
        rp_dir = creator.create_rp(test_data)

        print(f"✓ RP created at: {rp_dir}")

        # Verify structure
        required_files = [
            "Test Adventure.md",
            "AUTHOR'S_NOTES.md",
            "STORY_GENOME.md",
            "NAMING_CONVENTIONS.md",
            "SCENE_NOTES.md",
            "rp_config.json",
        ]

        required_dirs = [
            "chapters",
            "characters",
            "entities",
            "state",
            "memories",
        ]

        print("\nVerifying files:")
        for file in required_files:
            file_path = rp_dir / file
            if file_path.exists():
                print(f"  ✓ {file}")
            else:
                print(f"  ✗ {file} MISSING!")

        print("\nVerifying directories:")
        for dir_name in required_dirs:
            dir_path = rp_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"  ✓ {dir_name}/")
            else:
                print(f"  ✗ {dir_name}/ MISSING!")

        # Check state files
        state_files = [
            "automation_config.json",
            "current_state.md",
            "entity_tracker.json",
            "relationship_tracker.json",
            "memory_index.json",
            "file_tracking.json",
            "response_counter.json",
            "plot_threads_master.md",
            "plot_threads_archive.md",
            "knowledge_base.md",
        ]

        print("\nVerifying state files:")
        for state_file in state_files:
            file_path = rp_dir / "state" / state_file
            if file_path.exists():
                print(f"  ✓ state/{state_file}")
            else:
                print(f"  ✗ state/{state_file} MISSING!")

        # Check character files
        char_files = ["{{user}}.md", "{{char}}.md"]
        print("\nVerifying character files:")
        for char_file in char_files:
            file_path = rp_dir / "characters" / char_file
            if file_path.exists():
                print(f"  ✓ characters/{char_file}")
            else:
                print(f"  ✗ characters/{char_file} MISSING!")

        # Check chapter file
        chapter_file = rp_dir / "chapters" / "chapter_001.md"
        print(f"\nChapter file: {'✓' if chapter_file.exists() else '✗'} chapters/chapter_001.md")

        print(f"\n{'='*60}")
        print("SUCCESS! All files created correctly.")
        print(f"{'='*60}")

        # Show sample content
        print("\nSample content from AUTHOR'S_NOTES.md:")
        print("-" * 60)
        with open(rp_dir / "AUTHOR'S_NOTES.md", "r", encoding="utf-8") as f:
            lines = f.readlines()[:15]
            print("".join(lines))
        print("-" * 60)

        return True

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_rp_creation()
