#!/usr/bin/env python3
"""
Generate Relationship Preferences for Characters

This utility script automatically generates relationship preference files for
characters with Personality Cores using DeepSeek analysis.

Usage:
    python -m src.generate_preferences "Example RP"                    # Generate for all characters
    python -m src.generate_preferences "Example RP" --character "Sarah"  # Generate for specific character
"""

import sys
from pathlib import Path

from src.entity_manager import EntityManager


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-generate relationship preferences from Personality Cores"
    )
    parser.add_argument(
        "rp_folder",
        help="Name of the RP folder (e.g., 'Example RP')"
    )
    parser.add_argument(
        "--character",
        "-c",
        help="Generate for specific character only (otherwise generates for all)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing preference files"
    )

    args = parser.parse_args()

    # Get RP directory (from project root)
    project_root = Path(__file__).parent.parent
    rp_dir = project_root / "RPs" / args.rp_folder

    if not rp_dir.exists():
        print(f"❌ RP folder not found: {rp_dir}")
        sys.exit(1)

    print(f"📁 RP Directory: {rp_dir}")
    print()

    # Initialize EntityManager
    entity_mgr = EntityManager(rp_dir)
    entity_mgr.scan_and_index()

    print(f"📊 Found {len(entity_mgr.entities)} entities")
    print()

    # Get characters to process
    if args.character:
        # Single character
        characters_to_process = [args.character]
    else:
        # All characters with Personality Cores
        characters_to_process = []
        for name, entity in entity_mgr.entities.items():
            if entity.entity_type.value == "character" and entity.personality_core:
                characters_to_process.append(name)

        print(f"🎭 Found {len(characters_to_process)} characters with Personality Cores:")
        for name in characters_to_process:
            print(f"   - {name}")
        print()

    if not characters_to_process:
        print("⚠️  No characters with Personality Cores found")
        print("   Add Personality Core sections to character cards first")
        sys.exit(0)

    # Check for existing preference files
    relationships_dir = rp_dir / "relationships"
    if not args.overwrite:
        existing = []
        for name in characters_to_process:
            pref_file = relationships_dir / f"{name}_preferences.json"
            if pref_file.exists():
                existing.append(name)

        if existing:
            print(f"⚠️  {len(existing)} character(s) already have preference files:")
            for name in existing:
                print(f"   - {name}")
            print()
            response = input("Overwrite existing files? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                sys.exit(0)

    # Generate preferences
    print("🤖 Generating preferences using DeepSeek...")
    print()

    success_count = 0
    fail_count = 0

    for character_name in characters_to_process:
        print(f"{'='*60}")
        print(f"Processing: {character_name}")
        print(f"{'='*60}")

        success = entity_mgr.auto_generate_preferences(character_name)

        if success:
            success_count += 1
        else:
            fail_count += 1

        print()

    # Summary
    print(f"{'='*60}")
    print("Summary:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"{'='*60}")

    if success_count > 0:
        print()
        print("💡 Next steps:")
        print("   1. Review the generated preference files in relationships/")
        print("   2. Adjust point values and add/remove traits as needed")
        print("   3. Enable relationship tracking in F6 Module Toggles")


if __name__ == "__main__":
    main()
