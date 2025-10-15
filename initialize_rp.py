"""
RP Directory Initialization Script
Sets up complete directory structure and state files for a new RP.
"""

import sys
import io
from pathlib import Path
from typing import Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from file_manager import FileManager
from state_templates import StateTemplates


class RPInitializer:
    """
    Initialize a new RP directory with complete structure and state files.
    """

    def __init__(self, rp_dir: Path):
        """
        Initialize RPInitializer.

        Args:
            rp_dir: Path to RP directory (will be created if doesn't exist)
        """
        self.rp_dir = Path(rp_dir)

    def initialize(self, rp_name: Optional[str] = None, skip_existing: bool = True) -> None:
        """
        Initialize complete RP directory structure.

        Args:
            rp_name: Name of the RP (defaults to directory name)
            skip_existing: Skip existing files instead of overwriting
        """
        if rp_name is None:
            rp_name = self.rp_dir.name

        print(f"Initializing RP: {rp_name}")
        print(f"Directory: {self.rp_dir}")
        print()

        # Create base directory
        self.rp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize FileManager
        self.fm = FileManager(self.rp_dir)

        # Create directory structure
        self._create_directory_structure()

        # Create state files
        self._create_state_files(skip_existing)

        # Create initial chapter
        self._create_initial_chapter(skip_existing)

        # Create RP metadata file
        self._create_rp_metadata(rp_name, skip_existing)

        print()
        print("✅ RP initialization complete!")
        print(f"   RP directory: {self.rp_dir}")

    def _create_directory_structure(self) -> None:
        """Create complete directory structure."""
        print("Creating directory structure...")

        directories = [
            "chapters",           # Story chapters
            "entities",           # Character/location/organization cards
            "state",              # State management files
            "memories",           # Character-specific memory files
            "relationships",      # Relationship tracking files
            "sessions",           # Session logs
            "exports",            # Exported content
            "exports/wiki",       # Wiki exports
            "exports/epub",       # EPUB exports
            "exports/pdf",        # PDF exports
            "backups",            # Backup files
            "config",             # Configuration files
        ]

        for dir_path in directories:
            full_path = self.fm.ensure_directory(dir_path)
            print(f"  ✓ {dir_path}/")

    def _create_state_files(self, skip_existing: bool = True) -> None:
        """Create initial state management files."""
        print()
        print("Creating state files...")

        state_files = [
            ("state/plot_threads_master.md", StateTemplates.plot_threads_master()),
            ("state/plot_threads_archive.md", StateTemplates.plot_threads_archive()),
            ("state/knowledge_base.md", StateTemplates.knowledge_base()),
            ("state/current_state.md", StateTemplates.current_state()),
            ("state/entity_tracker.json", StateTemplates.entity_tracker()),
            ("state/relationship_tracker.json", StateTemplates.relationship_tracker()),
            ("state/memory_index.json", StateTemplates.memory_index()),
            ("state/automation_config.json", StateTemplates.automation_config()),
            ("state/file_tracking.json", StateTemplates.file_tracking()),
        ]

        for file_path, content in state_files:
            if skip_existing and self.fm.file_exists(file_path):
                print(f"  ⏭  {file_path} (already exists, skipping)")
                continue

            if isinstance(content, dict):
                self.fm.write_json(file_path, content)
            else:
                self.fm.write_markdown(file_path, content)

            print(f"  ✓ {file_path}")

    def _create_initial_chapter(self, skip_existing: bool = True) -> None:
        """Create initial chapter file."""
        print()
        print("Creating initial chapter...")

        chapter_file = "chapters/chapter_001.md"

        if skip_existing and self.fm.file_exists(chapter_file):
            print(f"  ⏭  {chapter_file} (already exists, skipping)")
            return

        chapter_content = StateTemplates.chapter_template(1)
        self.fm.write_markdown(chapter_file, chapter_content)
        print(f"  ✓ {chapter_file}")

    def _create_rp_metadata(self, rp_name: str, skip_existing: bool = True) -> None:
        """Create RP metadata file."""
        print()
        print("Creating RP metadata...")

        metadata_file = f"{rp_name}.md"

        if skip_existing and self.fm.file_exists(metadata_file):
            print(f"  ⏭  {metadata_file} (already exists, skipping)")
            return

        metadata_content = f"""# {rp_name}

## RP Metadata
- **Name**: {rp_name}
- **Created**: {StateTemplates.automation_config()['last_updated']}
- **Current Chapter**: 1
- **Current Response**: 0
- **Status**: Active

---

## Description

(Describe your RP here)

---

## Genre & Themes

**Genre**: (e.g., fantasy, sci-fi, contemporary, romance)
**Themes**: (e.g., adventure, coming-of-age, mystery)

---

## Setting

**Primary Location**: (e.g., modern day Chicago, fantasy kingdom, space station)
**Time Period**: (e.g., 2024, medieval era, far future)

---

## Main Characters

(List will be populated as characters are added)

---

## Story Notes

(Add notes about your story here)
"""

        self.fm.write_markdown(metadata_file, metadata_content)
        print(f"  ✓ {metadata_file}")

    def create_example_entity(self, entity_name: str, entity_type: str = "character") -> None:
        """
        Create an example entity card.

        Args:
            entity_name: Name of the entity
            entity_type: Type of entity (character, location, organization)
        """
        entity_file = self.fm.get_entity_file(entity_name)

        if entity_file.exists():
            print(f"⚠️  Entity already exists: {entity_name}")
            return

        template = StateTemplates.entity_card_template(entity_name, entity_type)
        self.fm.write_markdown(entity_file, template)
        print(f"✓ Created entity: {entity_name} ({entity_type})")

    def create_character_memory_file(self, character_name: str) -> None:
        """
        Create memory file for a character.

        Args:
            character_name: Name of the character
        """
        memory_file = self.fm.get_memory_file(character_name)

        if memory_file.exists():
            print(f"⚠️  Memory file already exists: {character_name}")
            return

        template = StateTemplates.character_memory_template(character_name)
        self.fm.write_markdown(memory_file, template)
        print(f"✓ Created memory file: {character_name}")


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize a new RP directory with complete structure"
    )
    parser.add_argument(
        "rp_dir",
        type=str,
        help="Path to RP directory (will be created if doesn't exist)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name of the RP (defaults to directory name)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of skipping"
    )

    args = parser.parse_args()

    initializer = RPInitializer(Path(args.rp_dir))
    initializer.initialize(rp_name=args.name, skip_existing=not args.overwrite)


if __name__ == "__main__":
    main()
