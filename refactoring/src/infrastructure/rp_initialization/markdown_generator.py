"""Markdown file generator for RP wizard.

Generates TIER 1 markdown files (AUTHOR'S_NOTES, STORY_GENOME, etc.) from wizard data
using templates with variable replacement.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class MarkdownGenerator:
    """Generate markdown files from templates with variable replacement."""

    def __init__(self, templates_dir: Path):
        """Initialize markdown generator.

        Args:
            templates_dir: Directory containing markdown templates
        """
        self.templates_dir = templates_dir

    def generate_author_notes(self, wizard_data: dict[str, Any], output_path: Path) -> None:
        """Generate AUTHOR'S_NOTES.md from wizard data.

        Args:
            wizard_data: Data collected from wizard
            output_path: Where to write the file
        """
        template = self._load_template("author_notes_template.md")

        # Build must happen list
        must_happen = wizard_data.get("must_happen", [])
        must_happen_text = "\n".join(f"- {item}" for item in must_happen) if must_happen else "- (Add your story rules here)"

        # Build must not happen list
        must_not_happen = wizard_data.get("must_not_happen", [])
        must_not_happen_text = "\n".join(f"- {item}" for item in must_not_happen) if must_not_happen else "- (Add your boundaries here)"

        # Build themes list
        themes = wizard_data.get("themes", [])
        themes_text = "\n".join(f"- {theme}" for theme in themes) if themes else "- (Add your themes here)"

        replacements = {
            "rp_name": wizard_data.get("rp_name", "Untitled RP"),
            "must_happen": must_happen_text,
            "must_not_happen": must_not_happen_text,
            "death_rules": wizard_data.get("death_rules", "Major characters can die with proper foreshadowing (minimum 2-3 chapters warning)"),
            "romance_pacing": wizard_data.get("romance_pacing", "Slow burn - relationships develop naturally over time"),
            "power_rules": wizard_data.get("power_rules", "Power level increases gradually - no sudden god-mode"),
            "writing_style": wizard_data.get("writing_style", "Descriptive and immersive"),
            "perspective": wizard_data.get("perspective", "Third person limited"),
            "response_length": wizard_data.get("response_length", "3-5 paragraphs"),
            "pacing_preference": wizard_data.get("pacing_preference", "Balanced - mix of action, dialogue, and introspection"),
            "tone": wizard_data.get("tone", "Epic adventure"),
            "themes": themes_text,
            "content_rating": wizard_data.get("content_rating", "PG-13"),
            "user": wizard_data.get("user_name", "{{user}}"),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = self._replace_variables(template, replacements)
        self._write_file(output_path, content)

    def generate_story_genome(self, wizard_data: dict[str, Any], output_path: Path) -> None:
        """Generate STORY_GENOME.md from wizard data.

        Args:
            wizard_data: Data collected from wizard
            output_path: Where to write the file
        """
        template = self._load_template("story_genome_template.md")

        # Build arc details based on structure type
        arc_structure = wizard_data.get("arc_structure", "3-act")
        if arc_structure == "3-act":
            arc_details = """
### Act 1: Setup
Introduction, inciting incident, rising action

### Act 2: Confrontation
Complications, midpoint twist, crisis

### Act 3: Resolution
Climax, falling action, resolution
"""
        elif arc_structure == "5-act":
            arc_details = """
### Act 1: Exposition
World and character introduction

### Act 2: Rising Action
Complications begin

### Act 3: Climax
Major turning point

### Act 4: Falling Action
Consequences unfold

### Act 5: Resolution
Story conclusion
"""
        elif arc_structure == "episodic":
            arc_details = "Each session tells a complete mini-story while building larger narrative threads."
        else:  # sandbox
            arc_details = "Player-driven exploration with emergent narrative. No predetermined story structure."

        # Build themes list
        themes = wizard_data.get("themes", [])
        themes_text = "\n".join(f"- {theme}" for theme in themes) if themes else "- (Add your themes here)"

        replacements = {
            "rp_name": wizard_data.get("rp_name", "Untitled RP"),
            "genre": wizard_data.get("genre", "Fantasy"),
            "setting": wizard_data.get("setting", "A fantastical world"),
            "premise": wizard_data.get("premise", "An epic adventure awaits"),
            "story_mode": wizard_data.get("story_mode", "Guided narrative with player agency"),
            "arc_structure": arc_structure,
            "arc_details": arc_details,
            "act1_goal": wizard_data.get("act1_goal", "(Define your Act 1 goal)"),
            "midpoint_twist": wizard_data.get("midpoint_twist", "(Define your midpoint twist)"),
            "climax": wizard_data.get("climax", "(Define your climax)"),
            "themes": themes_text,
            "world_notes": wizard_data.get("world_notes", "(Add world-building notes)"),
            "user": wizard_data.get("user_name", "{{user}}"),
            "char": wizard_data.get("char_name", "{{char}}"),
            "user_arc": wizard_data.get("user_arc", "(Define character arc)"),
            "char_arc": wizard_data.get("char_arc", "(Define character arc)"),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = self._replace_variables(template, replacements)
        self._write_file(output_path, content)

    def generate_naming_conventions(self, wizard_data: dict[str, Any], output_path: Path) -> None:
        """Generate NAMING_CONVENTIONS.md from wizard data.

        Args:
            wizard_data: Data collected from wizard
            output_path: Where to write the file
        """
        template = self._load_template("naming_conventions_template.md")

        replacements = {
            "rp_name": wizard_data.get("rp_name", "Untitled RP"),
            "primary_culture": wizard_data.get("primary_culture", "Main Culture"),
            "culture_description": wizard_data.get("culture_description", "Describe your primary culture's characteristics and influences."),
            "male_names_example": wizard_data.get("male_names_example", "Examples: (Add male name examples)"),
            "female_names_example": wizard_data.get("female_names_example", "Examples: (Add female name examples)"),
            "neutral_names_example": wizard_data.get("neutral_names_example", "Examples: (Add neutral name examples)"),
            "surname_pattern": wizard_data.get("surname_pattern", "Pattern: (Describe surname pattern)"),
            "city_naming": wizard_data.get("city_naming", "(Describe city naming patterns)"),
            "natural_naming": wizard_data.get("natural_naming", "(Describe natural feature naming)"),
            "landmark_naming": wizard_data.get("landmark_naming", "(Describe landmark naming)"),
            "org_naming_format": wizard_data.get("org_naming_format", "(Describe organization naming format)"),
            "org_examples": wizard_data.get("org_examples", "(Add organization examples)"),
            "titles_ranks": wizard_data.get("titles_ranks", "(Add titles and ranks)"),
            "additional_cultures": wizard_data.get("additional_cultures", "(Add additional cultures if needed)"),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = self._replace_variables(template, replacements)
        self._write_file(output_path, content)

    def generate_scene_notes(self, wizard_data: dict[str, Any], output_path: Path) -> None:
        """Generate SCENE_NOTES.md from wizard data.

        Args:
            wizard_data: Data collected from wizard
            output_path: Where to write the file
        """
        template = self._load_template("scene_notes_template.md")

        # Build active NPCs list
        char_name = wizard_data.get("char_name", "Main NPC")
        active_npcs = f"- **{char_name}** - {wizard_data.get('char_brief', 'Main supporting character')}"

        # Build session goals
        session_goals_list = wizard_data.get("session_goals", [])
        if session_goals_list:
            session_goals = "\n".join(f"- {goal}" for goal in session_goals_list)
        else:
            session_goals = "- Begin the adventure\n- Introduce main characters\n- Establish the setting"

        replacements = {
            "rp_name": wizard_data.get("rp_name", "Untitled RP"),
            "starting_location": wizard_data.get("starting_location", "Unknown Location"),
            "starting_time": wizard_data.get("starting_time", "Present day"),
            "atmosphere": wizard_data.get("atmosphere", "Neutral"),
            "active_npcs": active_npcs,
            "opening_scenario": wizard_data.get("opening_scenario", "The story begins..."),
            "session_goals": session_goals,
            "dm_notes": wizard_data.get("dm_notes", "Focus on introducing the world and characters. Let the player take the lead."),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = self._replace_variables(template, replacements)
        self._write_file(output_path, content)

    def generate_rp_overview(self, wizard_data: dict[str, Any], output_path: Path) -> None:
        """Generate {RP_NAME}.md overview file from wizard data.

        Args:
            wizard_data: Data collected from wizard
            output_path: Where to write the file
        """
        template = self._load_template("rp_overview_template.md")

        # Build character descriptions
        user_name = wizard_data.get("user_name", "{{user}}")
        char_name = wizard_data.get("char_name", "{{char}}")

        user_description = wizard_data.get("user_brief", "Player character")
        char_description = wizard_data.get("char_brief", "Main NPC")

        # Additional characters (if any)
        additional_chars = wizard_data.get("additional_characters", [])
        additional_text = ""
        if additional_chars:
            additional_text = "\n\n### Additional Characters\n"
            for char in additional_chars:
                additional_text += f"- **{char['name']}** - {char.get('brief', 'Supporting character')}\n"

        # Story goals
        story_goals_list = wizard_data.get("story_goals", [])
        if story_goals_list:
            story_goals = "\n".join(f"- {goal}" for goal in story_goals_list)
        else:
            story_goals = "- (Define your story goals)"

        replacements = {
            "rp_name": wizard_data.get("rp_name", "Untitled RP"),
            "genre": wizard_data.get("genre", "Fantasy"),
            "setting": wizard_data.get("setting", "A fantastical world"),
            "tone": wizard_data.get("tone", "Epic adventure"),
            "content_rating": wizard_data.get("content_rating", "PG-13"),
            "premise": wizard_data.get("premise", "An epic adventure awaits"),
            "user": user_name,
            "char": char_name,
            "user_description": user_description,
            "char_description": char_description,
            "additional_characters": additional_text,
            "story_goals": story_goals,
            "notes": wizard_data.get("notes", "Created with RP Start Wizard"),
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
        }

        content = self._replace_variables(template, replacements)
        self._write_file(output_path, content)

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _load_template(self, template_name: str) -> str:
        """Load a template file.

        Args:
            template_name: Name of template file

        Returns:
            Template content as string
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def _replace_variables(self, template: str, replacements: dict[str, str]) -> str:
        """Replace {{variable}} placeholders in template.

        Args:
            template: Template string with {{variable}} placeholders
            replacements: Dict mapping variable names to values

        Returns:
            Template with variables replaced
        """
        content = template
        for key, value in replacements.items():
            placeholder = f"{{{{{key}}}}}"  # {{key}}
            content = content.replace(placeholder, str(value))
        return content

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file.

        Args:
            path: File path to write
            content: Content to write
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


__all__ = ["MarkdownGenerator"]
