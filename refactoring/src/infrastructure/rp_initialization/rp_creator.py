"""RP initialization and folder structure creation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..filesystem.state_paths import StatePaths
from ..templates import CharacterTemplateGenerator, SchemaLoader


class RPCreationError(Exception):
    """Raised when RP creation fails."""
    pass


class RPCreator:
    """Creates new RP folders with required structure and files."""

    def __init__(self, base_rps_dir: Path):
        """Initialize RP creator.

        Args:
            base_rps_dir: Base directory where RPs are stored (e.g., "RPs/")
        """
        self.base_rps_dir = base_rps_dir

    def _determine_character_schema(self, wizard_data: dict[str, Any]) -> str:
        """Determine which character schema to use based on wizard data.

        Args:
            wizard_data: Data from wizard

        Returns:
            Schema name (e.g., 'fantasy', 'minimal')
        """
        # Check template first
        template = wizard_data.get("template", "custom")
        if template == "fantasy_adventure":
            return "fantasy"

        # Check genre
        genre = wizard_data.get("genre", "").lower()
        if "fantasy" in genre or "medieval" in genre:
            return "fantasy"
        elif "sci" in genre or "space" in genre or "cyberpunk" in genre:
            return "minimal"  # Could be "scifi" when that schema exists

        # Default to minimal
        return "minimal"

    def create_rp(self, wizard_data: dict[str, Any]) -> Path:
        """Create a new RP folder structure from wizard data.

        Args:
            wizard_data: Data collected from the setup wizard

        Returns:
            Path to the created RP directory

        Raises:
            RPCreationError: If creation fails
        """
        rp_name = wizard_data.get("rp_name", "").strip()
        if not rp_name:
            raise RPCreationError("RP name is required")

        # Create RP directory
        rp_dir = self.base_rps_dir / rp_name
        if rp_dir.exists():
            raise RPCreationError(f"RP '{rp_name}' already exists")

        try:
            # Create directory structure
            self._create_directory_structure(rp_dir)

            # Copy template files if specified
            template = wizard_data.get("template", "custom")
            if template != "custom":
                self._copy_template_files(rp_dir, template, rp_name)

            # Create/override core story files with wizard data
            self._create_rp_overview(rp_dir, wizard_data)
            self._create_authors_notes(rp_dir, wizard_data)
            self._create_story_genome(rp_dir, wizard_data)
            self._create_naming_conventions(rp_dir, wizard_data)
            self._create_scene_notes(rp_dir, wizard_data)

            # Create character files (will merge with template if exists)
            self._create_character_files(rp_dir, wizard_data)

            # Create initial chapter if not from template
            if not (rp_dir / "chapters" / "chapter_001.md").exists():
                self._create_initial_chapter(rp_dir)

            # Create state files
            self._create_state_files(rp_dir, wizard_data)

            # Create config file
            self._create_rp_config(rp_dir, wizard_data)

            return rp_dir

        except Exception as e:
            # Clean up on failure
            if rp_dir.exists():
                import shutil
                shutil.rmtree(rp_dir)
            raise RPCreationError(f"Failed to create RP: {e}") from e

    def _create_directory_structure(self, rp_dir: Path) -> None:
        """Create all required directories."""
        paths = StatePaths(rp_dir)

        directories = [
            rp_dir,
            paths.chapters_dir,
            paths.characters_dir,
            paths.entities_dir,
            paths.state_dir,
            paths.memories_dir,
            rp_dir / "relationships",
            rp_dir / "locations",
            paths.sessions_dir,
            paths.session_branches_dir,
            paths.session_archived_dir,
            rp_dir / "exports",
            rp_dir / "exports" / "wiki",
            rp_dir / "exports" / "epub",
            rp_dir / "exports" / "pdf",
            rp_dir / "backups",
            rp_dir / "config",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _copy_template_files(self, rp_dir: Path, template_name: str, rp_name: str) -> None:
        """Copy template files from setup/templates/starter_packs/.

        Args:
            rp_dir: Destination RP directory
            template_name: Template name (minimal, fantasy_adventure, etc.)
            rp_name: Name of the RP (for renaming RP_NAME.md)
        """
        import shutil

        # Find template directory - it should be in setup/templates/starter_packs/
        # Go up from src/infrastructure/rp_initialization/ to project root
        project_root = Path(__file__).parent.parent.parent.parent
        template_dir = project_root / "setup" / "templates" / "starter_packs" / template_name

        if not template_dir.exists():
            # Template not found, skip silently (will use wizard data only)
            return

        # Copy all template files
        for item in template_dir.iterdir():
            # Skip README.md (template documentation)
            if item.name == "README.md":
                continue

            # Skip characters directory - character sheets are always generated from JSON schemas
            if item.name == "characters":
                continue

            dest_item = rp_dir / item.name

            # Handle RP_NAME.md renaming
            if item.name == "RP_NAME.md":
                dest_item = rp_dir / f"{rp_name}.md"

            try:
                if item.is_file():
                    shutil.copy2(item, dest_item)
                elif item.is_dir():
                    # Copy directory contents, merging with existing
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
            except Exception:
                # If copy fails, continue (wizard data will fill in)
                pass

    def _create_rp_overview(self, rp_dir: Path, data: dict) -> None:
        """Create the [RP Name].md overview file (or skip if template exists)."""
        rp_name = data.get("rp_name", "Untitled RP")
        overview_file = rp_dir / f"{rp_name}.md"

        # If template already created this file, skip
        if overview_file.exists():
            return

        genre = data.get("genre", "Custom")
        setting = data.get("setting", "")
        tone = data.get("tone", "")
        content_rating = data.get("content_rating", "PG-13")
        premise = data.get("premise", "")

        content = f"""# {rp_name}

## Quick Overview
**Genre:** {genre}
**Setting:** {setting or "To be determined"}
**Tone:** {tone or "To be determined"}
**Content Rating:** {content_rating}

## Premise
{premise or "To be written..."}

## Characters
**{{{{user}}}}** - {data.get("user_char_name", "Player Character")}
**{{{{char}}}}** - {data.get("main_npc_name", "Main NPC")}

## Story Goals
{self._format_list(data.get("story_goals", []))}

## Current Status
- **Chapter:** 1
- **Messages:** 0
- **Last Updated:** {datetime.now().strftime("%Y-%m-%d")}
"""

        overview_file.write_text(content, encoding="utf-8")

    def _create_authors_notes(self, rp_dir: Path, data: dict) -> None:
        """Create AUTHOR'S_NOTES.md file (or skip if template exists)."""
        file_path = rp_dir / "AUTHOR'S_NOTES.md"
        if file_path.exists():
            return  # Template already provided this

        content = f"""# Author's Notes

## Story Rules - What MUST Happen
{self._format_list(data.get("must_happen", []))}

## Story Rules - What MUST NOT Happen
{self._format_list(data.get("must_not_happen", []))}

## Writing Preferences
**Style:** {data.get("writing_style", "Balanced mix of description and action")}
**Perspective:** {data.get("perspective", "Third person")}
**Response Length:** {data.get("response_length", "Medium (2-4 paragraphs)")}

## Tone & Themes
**Tone:** {data.get("tone", "Balanced")}
**Themes:** {self._format_list(data.get("themes", []))}
**Content Boundaries:** {data.get("content_boundaries", "No extreme violence or explicit content")}

## Character Notes
**Your Character ({{{{user}}}}):**
- Play {{{{user}}}} as written in their character sheet
- Respect their established personality and background
- Allow for character growth and development

**NPCs:**
- Keep NPCs consistent with their established personalities
- Give them agency and realistic motivations
- Allow relationships to develop naturally
"""

        file_path.write_text(content, encoding="utf-8")

    def _create_story_genome(self, rp_dir: Path, data: dict) -> None:
        """Create STORY_GENOME.md file (or skip if template exists)."""
        file_path = rp_dir / "STORY_GENOME.md"
        if file_path.exists():
            return  # Template already provided this

        content = f"""# Story Genome

## Genre & Setting
**Genre:** {data.get("genre", "Custom")}
**Setting:** {data.get("setting", "To be determined")}
**Time Period:** {data.get("time_period", "To be determined")}

## Story Arc
**Act 1 - Opening:**
{data.get("act1", "The story begins...")}

**Midpoint:**
{data.get("midpoint", "A turning point occurs...")}

**Climax:**
{data.get("climax", "The story reaches its peak...")}

## Major Plot Points
{self._format_list(data.get("plot_points", []))}

## Themes
{self._format_list(data.get("themes", []))}

## Character Arcs
**{{{{user}}}}:**
- Beginning: {data.get("user_arc_begin", "Starting point")}
- Growth: {data.get("user_arc_growth", "How they change")}
- End: {data.get("user_arc_end", "Where they end up")}

## World Notes
{data.get("world_notes", "Details about magic systems, culture, locations, history...")}
"""

        file_path.write_text(content, encoding="utf-8")

    def _create_naming_conventions(self, rp_dir: Path, data: dict) -> None:
        """Create NAMING_CONVENTIONS.md file (or skip if template exists)."""
        file_path = rp_dir / "NAMING_CONVENTIONS.md"
        if file_path.exists():
            return  # Template already provided this

        content = f"""# Naming Conventions

## Quick Reference
**Genre:** {data.get("genre", "Custom")}
**Setting:** {data.get("setting", "To be determined")}
**Tone:** {data.get("tone", "To be determined")}

## Character Names
### Primary Culture/Region: {data.get("primary_culture", "Main Culture")}
**Description:** {data.get("culture_desc", "Brief description of the culture")}
**Naming Patterns:**
- **Given names:** {data.get("given_name_pattern", "Follow established patterns")}
- **Family names:** {data.get("family_name_pattern", "Follow established patterns")}
**Examples:**
- Male: {data.get("male_name_examples", "John, Michael, David")}
- Female: {data.get("female_name_examples", "Sarah, Emma, Lisa")}

## Location Names
### Cities and Towns
**Naming Pattern:** {data.get("location_pattern", "Descriptive or cultural")}
**Examples:** {data.get("location_examples", "Rivertown, Highgate, Summerhaven")}

## Organizations & Factions
### Government/Military
**Structure:** {data.get("org_structure", "Hierarchical")}
**Examples:** {data.get("org_examples", "The Royal Guard, Merchant's Guild")}

## Titles & Ranks
### Nobility
**Structure:** {data.get("title_structure", "Traditional hierarchy")}
**Examples:** {data.get("title_examples", "Lord, Lady, Sir, Dame")}
"""

        file_path.write_text(content, encoding="utf-8")

    def _create_scene_notes(self, rp_dir: Path, data: dict) -> None:
        """Create SCENE_NOTES.md file (or skip if template exists)."""
        file_path = rp_dir / "SCENE_NOTES.md"
        if file_path.exists():
            return  # Template already provided this

        content = f"""# Scene Notes

## Current Scene
**Location:** {data.get("starting_location", "To be determined")}
**Time:** {data.get("starting_time", "To be determined")}
**Characters Present:**
- {{{{user}}}}
- {data.get("starting_characters", "{{char}}")}
**Atmosphere:** {data.get("starting_atmosphere", "To be determined")}

## Session Goals
{self._format_list(data.get("session_goals", ["Establish setting", "Introduce characters", "Set up initial conflict"]))}

## Active NPCs
**{data.get("main_npc_name", "Main NPC")}:**
- Mood: {data.get("npc_mood", "Neutral")}
- Goals: {data.get("npc_goals", "To be determined")}
- Key info: {data.get("npc_key_info", "Important details about this NPC")}

## Guidance for Claude
{self._format_list(data.get("claude_guidance", ["Focus on character introduction", "Establish tone and atmosphere"]))}

## Reminders
- This is the beginning of the RP
- Take time to establish the world and characters
- Let the story unfold naturally
"""

        file_path = rp_dir / "SCENE_NOTES.md"
        file_path.write_text(content, encoding="utf-8")

    def _create_character_files(self, rp_dir: Path, data: dict) -> None:
        """Create character sheet files from JSON schemas."""
        paths = StatePaths(rp_dir)

        # Always generate {{user}}.md from schema
        user_file = paths.characters_dir / "{{user}}.md"
        user_content = self._generate_character_sheet(
            data,  # Pass full wizard data for schema determination
            name=data.get("user_char_name", "{{user}}"),
            age=data.get("user_age", ""),
            gender=data.get("user_gender", ""),
            species=data.get("user_species", "Human"),
            occupation=data.get("user_occupation", ""),
            appearance=data.get("user_appearance", ""),
            personality=data.get("user_personality", ""),
            background=data.get("user_background", ""),
            skills=data.get("user_skills", ""),
            goals=data.get("user_goals", ""),
            is_user=True
        )
        user_file.write_text(user_content, encoding="utf-8")

        # Generate {{char}}.md from schema if NPC info provided
        npc_file = paths.characters_dir / "{{char}}.md"
        if data.get("main_npc_name"):
            npc_content = self._generate_character_sheet(
                data,  # Pass full wizard data for schema determination
                name=data.get("main_npc_name", "{{char}}"),
                age=data.get("npc_age", ""),
                gender=data.get("npc_gender", ""),
                species=data.get("npc_species", "Human"),
                occupation=data.get("npc_occupation", ""),
                appearance=data.get("npc_appearance", ""),
                personality=data.get("npc_personality", ""),
                background=data.get("npc_background", ""),
                skills=data.get("npc_skills", ""),
                goals=data.get("npc_goals", ""),
                is_user=False
            )
            npc_file.write_text(npc_content, encoding="utf-8")

    def _generate_character_sheet(self, wizard_data: dict[str, Any], **kwargs) -> str:
        """Generate character sheet content from schema.

        Args:
            wizard_data: Full wizard data (for schema determination)
            **kwargs: Character-specific data fields

        Returns:
            Generated markdown content
        """
        name = kwargs.get("name", "Character")
        is_user = kwargs.get("is_user", False)

        # Determine which schema to use
        schema_name = self._determine_character_schema(wizard_data)

        # Load and resolve schema
        try:
            schema = SchemaLoader.load_and_resolve(schema_name)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to minimal if schema not found
            schema = SchemaLoader.load_and_resolve("minimal")

        # Build character-specific wizard data
        char_wizard_data = {
            "name": kwargs.get("name", ""),
            "age": kwargs.get("age", ""),
            "gender": kwargs.get("gender", ""),
            "species": kwargs.get("species", ""),
            "race": kwargs.get("species", ""),  # Fantasy uses "race"
            "occupation": kwargs.get("occupation", ""),
            "physical_description": kwargs.get("appearance", ""),
            "hair_eyes": kwargs.get("appearance", ""),  # Fantasy field
            "core_traits": kwargs.get("personality", ""),
            "personality_type": kwargs.get("personality", ""),  # Fantasy field
            "history": kwargs.get("background", ""),
            "past": kwargs.get("background", ""),  # Fantasy field
            "abilities": kwargs.get("skills", ""),
            "motivations": kwargs.get("goals", ""),
        }

        # Generate using template generator
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        schema_path = project_root / "setup" / "templates" / "character_schemas" / f"{schema_name}_character_schema.json"
        generator = CharacterTemplateGenerator(schema_path)

        # Generate with character name and wizard data
        content = generator.generate(name, char_wizard_data)

        # Add note about character type
        note = "Player character - controlled by the user" if is_user else "NPC - controlled by the AI"
        content += f"\n\n---\n\n**Note:** {note}\n"

        return content

    def _create_initial_chapter(self, rp_dir: Path) -> None:
        """Create the initial chapter file."""
        paths = StatePaths(rp_dir)
        chapter_file = paths.chapter_file(1)

        content = f"""# Chapter 1

*Story begins here...*

---

**Turn 1** - {datetime.now().strftime("%Y-%m-%d %H:%M")}

"""

        chapter_file.write_text(content, encoding="utf-8")

    def _create_state_files(self, rp_dir: Path, data: dict) -> None:
        """Create all state JSON and markdown files."""
        paths = StatePaths(rp_dir)
        timestamp = datetime.now().isoformat()

        # automation_config.json
        automation_config = {
            "last_updated": timestamp,
            "deepseek_integration": {
                "enabled": True,
                "api_endpoint": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "background_analysis": True,
                "analysis_delay": 0
            },
            "context_intelligence": {
                "enabled": True,
                "three_tier_loading": True,
                "token_budget": {
                    "max_entities": 50000,
                    "max_memories": 10000,
                    "max_plot_threads": 5000
                }
            },
            "plot_tracking": {
                "enabled": True,
                "auto_extract_threads": True,
                "enable_consequences": True,
                "consequence_countdowns": {
                    "high_priority": 5,
                    "medium_priority": 10,
                    "low_priority": 20
                }
            },
            "memory_system": {
                "enabled": True,
                "auto_extract": True,
                "max_memories_per_character": 500,
                "relevance_threshold": 0.7
            },
            "relationship_system": {
                "enabled": True,
                "auto_analyze": True,
                "tier_threshold": 15,
                "auto_create_preferences": False
            },
            "character_consistency": {
                "enabled": True,
                "always_load_cores": True,
                "include_checklist": True
            },
            "enable_narrative_templates": True,
            "narrative_template": {
                "mode": "auto"
            },
            "knowledge_base": {
                "enabled": True,
                "auto_extract": True,
                "load_full_document": True
            },
            "pacing_analysis": {
                "enabled": True,
                "scene_variety_check": True,
                "tension_tracking": True
            }
        }

        (paths.state_dir / "automation_config.json").write_text(
            json.dumps(automation_config, indent=2), encoding="utf-8"
        )

        # entity_tracker.json
        entity_tracker = {
            "last_updated": timestamp,
            "current_chapter": 1,
            "current_response": 0,
            "characters": {},
            "locations": {},
            "organizations": {},
            "items": {}
        }

        (paths.state_dir / "entity_tracker.json").write_text(
            json.dumps(entity_tracker, indent=2), encoding="utf-8"
        )

        # relationship_tracker.json
        relationship_tracker = {
            "last_updated": timestamp,
            "current_chapter": 1,
            "current_response": 0,
            "relationships": {},
            "recent_tier_changes": []
        }

        (paths.state_dir / "relationship_tracker.json").write_text(
            json.dumps(relationship_tracker, indent=2), encoding="utf-8"
        )

        # memory_index.json
        memory_index = {
            "last_updated": timestamp,
            "total_memories": 0,
            "memories_by_character": {},
            "memories_by_chapter": {},
            "recent_memories": []
        }

        (paths.state_dir / "memory_index.json").write_text(
            json.dumps(memory_index, indent=2), encoding="utf-8"
        )

        # file_tracking.json
        file_tracking = {
            "last_updated": timestamp,
            "tracked_files": {}
        }

        (paths.state_dir / "file_tracking.json").write_text(
            json.dumps(file_tracking, indent=2), encoding="utf-8"
        )

        # response_counter.json
        response_counter = {
            "count": 0,
            "last_updated": timestamp
        }

        (paths.state_dir / "response_counter.json").write_text(
            json.dumps(response_counter, indent=2), encoding="utf-8"
        )

        # current_state.md
        current_state = f"""# CURRENT STATE

## Story Progress
- **Current Chapter**: 1
- **Current Response**: 0
- **Last Updated**: {timestamp}
- **Session**: 1

## Active Scene
**Location**: {data.get("starting_location", "To be determined")}
**Characters Present**: {{{{user}}}}, {data.get("main_npc_name", "{{char}}")}
**Time of Day**: {data.get("starting_time", "To be determined")}
**Weather**: To be determined
**Mood**: {data.get("starting_atmosphere", "To be determined")}

## Recent Events Summary
- RP just created - story has not yet begun

## Active Characters
### In Current Scene
- {{{{user}}}}
- {data.get("main_npc_name", "{{char}}")}

## Current Plot Focus
**Primary Thread**: Initial setup
**Secondary Threads**: None yet

## Pacing & Tension
**Current Tension Level**: 1/10 (Just beginning)
**Recent Scene Types**: None yet
**Pacing**: Not started

## User Notes
- First session - take time to establish setting and characters
"""

        (paths.state_dir / "current_state.md").write_text(current_state, encoding="utf-8")

        # plot_threads_master.md
        plot_threads = f"""# PLOT THREADS MASTER FILE

## Metadata
- **Total Active Threads**: 0
- **Last Updated**: {timestamp}
- **Current Chapter**: 1
- **Current Response**: 0

## Instructions
This file tracks all active plot threads, character arcs, and story developments.
Auto-updated by DeepSeek analysis after each response.

## Active Threads
*No active threads yet - story has not begun*

## Recently Resolved Threads
*None*

## Thread Statistics
**By Priority:**
- High: 0
- Medium: 0
- Low: 0

**By Status:**
- Active: 0
- Critical: 0
- Resolved: 0

**Time-Sensitive Threads:**
- Immediate (0-5 responses): 0
- Near-term (6-15 responses): 0
- Long-term (16+ responses): 0
"""

        (paths.state_dir / "plot_threads_master.md").write_text(plot_threads, encoding="utf-8")

        # plot_threads_archive.md
        (paths.state_dir / "plot_threads_archive.md").write_text(
            "# PLOT THREADS ARCHIVE\n\n*No archived threads yet*\n", encoding="utf-8"
        )

        # knowledge_base.md
        knowledge_base = f"""# WORLD KNOWLEDGE BASE

## Metadata
- **Last Updated**: {timestamp}
- **Current Chapter**: 1
- **Total Entries**: 0

## Setting
**Genre**: {data.get("genre", "Custom")}
**Time Period**: {data.get("time_period", "To be determined")}
**Primary Location**: {data.get("starting_location", "To be determined")}
**Technology Level**: {data.get("tech_level", "To be determined")}

## Geography
### Locations
*To be populated during play*

## Organizations
*To be populated during play*

## Cultural Details
*To be populated during play*

## Important Items
*To be populated during play*

## Story Themes
{self._format_list(data.get("themes", []))}

## World Rules
{data.get("world_notes", "*To be established during play*")}

## Historical Events
*To be populated during play*
"""

        (paths.state_dir / "knowledge_base.md").write_text(knowledge_base, encoding="utf-8")

    def _create_rp_config(self, rp_dir: Path, data: dict) -> None:
        """Create rp_config.json metadata file."""
        config = {
            "title": data.get("rp_name", "Untitled RP"),
            "genre": data.get("genre", "Custom"),
            "characters": [
                data.get("user_char_name", "{{user}}"),
                data.get("main_npc_name", "{{char}}")
            ],
            "last_played": datetime.now().isoformat(),
            "created": datetime.now().isoformat(),
            "turns": 0,
            "status": "Active",
            "description": data.get("premise", ""),
            "llm_config": {
                "primary_provider": data.get("primary_provider", "openai"),
                "primary_api_key": data.get("primary_api_key", ""),
                "secondary_provider": data.get("secondary_provider", "same"),
                "secondary_api_key": data.get("secondary_api_key", ""),
                "temperature": float(data.get("temperature", "0.7")),
                "max_tokens": int(data.get("max_tokens", "2048")),
                "system_prompt": data.get("system_prompt", "")
            }
        }

        config_file = rp_dir / "rp_config.json"
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def _add_user_data_to_template_file(self, file_path: Path, data: dict, is_user: bool = True) -> None:
        """Add user's wizard data to an existing template file.

        Args:
            file_path: Path to the template character file
            data: Wizard data
            is_user: True if this is the user character, False if NPC
        """
        # Read existing template
        template_content = file_path.read_text(encoding="utf-8")

        # Prepare user data section
        prefix = "user" if is_user else "npc"
        user_data_lines = []

        # Add a comment at the top with wizard data
        user_data_lines.append("<!-- Wizard Data -->")
        user_data_lines.append("<!--")

        if data.get(f"{prefix}_char_name"):
            user_data_lines.append(f"Character Name: {data.get(f'{prefix}_char_name' if is_user else 'main_npc_name')}")
        if data.get(f"{prefix}_age"):
            user_data_lines.append(f"Age: {data.get(f'{prefix}_age')}")
        if data.get(f"{prefix}_gender"):
            user_data_lines.append(f"Gender: {data.get(f'{prefix}_gender')}")
        if data.get(f"{prefix}_appearance"):
            user_data_lines.append(f"Appearance: {data.get(f'{prefix}_appearance')}")
        if data.get(f"{prefix}_personality"):
            user_data_lines.append(f"Personality: {data.get(f'{prefix}_personality')}")

        user_data_lines.append("-->")
        user_data_lines.append("")

        # Combine with template
        combined_content = "\n".join(user_data_lines) + template_content
        file_path.write_text(combined_content, encoding="utf-8")

    def _format_list(self, items: list[str]) -> str:
        """Format a list of items as markdown bullet points."""
        if not items:
            return "- *To be determined*"
        return "\n".join(f"- {item}" for item in items)
