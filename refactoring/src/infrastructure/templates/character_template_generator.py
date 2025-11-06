"""Character template generation from JSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CharacterTemplateGenerator:
    """Generates character markdown templates from JSON schemas."""

    def __init__(self, schema_path: Path):
        """Initialize generator with a schema file.

        Args:
            schema_path: Path to character schema JSON file
        """
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Load and parse the JSON schema."""
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate(self, character_name: str, wizard_data: dict[str, Any] | None = None) -> str:
        """Generate markdown character sheet from schema.

        Args:
            character_name: Name of the character (for title)
            wizard_data: Optional wizard data to fill in fields

        Returns:
            Markdown formatted character sheet
        """
        wizard_data = wizard_data or {}
        lines = []

        # Header
        lines.append(f"# {character_name} - Your Character Sheet")
        lines.append("")
        lines.append("Edit this template with your character's information. This helps Claude understand who you are in the story.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Generate each section
        for section in self.schema.get("sections", []):
            section_md = self._generate_section(section, wizard_data)
            if section_md:
                lines.append(section_md)
                lines.append("")

        return "\n".join(lines)

    def _generate_section(self, section: dict[str, Any], wizard_data: dict[str, Any]) -> str:
        """Generate markdown for a single section.

        Args:
            section: Section definition from schema
            wizard_data: Wizard data for filling fields

        Returns:
            Markdown for the section
        """
        lines = []

        # Section title
        title = section.get("title", "")
        lines.append(f"## {title}")
        lines.append("")

        # Generate fields
        for field in section.get("fields", []):
            field_md = self._generate_field(field, wizard_data)
            if field_md:
                lines.append(field_md)

        return "\n".join(lines)

    def _generate_field(self, field: dict[str, Any], wizard_data: dict[str, Any]) -> str:
        """Generate markdown for a single field.

        Args:
            field: Field definition from schema
            wizard_data: Wizard data for filling values

        Returns:
            Markdown for the field
        """
        field_id = field.get("id", "")
        field_type = field.get("type", "text")
        label = field.get("label", "")
        help_text = field.get("help_text", "")
        markdown_format = field.get("markdown_format", "**{label}:** {value}")
        default = field.get("default", "")

        # Check if wizard data has a value for this field
        value = wizard_data.get(field_id, "")

        # If no value, use default or help text as placeholder
        if not value:
            if default:
                value = default
            elif help_text:
                value = f"({help_text})"
            else:
                value = ""

        # Handle different field types
        if field_type == "list":
            return self._generate_list_field(field, value)
        elif field_type == "subsection":
            return self._generate_subsection_field(field)
        else:
            # Text or textarea
            if value:
                # Format using the template
                formatted = markdown_format.format(label=label, value=value)
                return formatted
            else:
                # Empty field, just show label with help text
                return markdown_format.format(label=label, value=f"({help_text})" if help_text else "")

    def _generate_list_field(self, field: dict[str, Any], value: str) -> str:
        """Generate markdown for a list-type field.

        Args:
            field: Field definition
            value: Value or empty

        Returns:
            Markdown for the list field
        """
        label = field.get("label", "")
        subitems = field.get("subitems", [])
        markdown_format = field.get("markdown_format", "**{label}:**\n{list_items}")

        if subitems:
            # Use predefined subitems
            list_items = "\n".join(f"- {item}" for item in subitems)
        elif value:
            # Value is provided (could be multiline)
            list_items = "\n".join(f"- {line}" for line in value.split("\n") if line.strip())
        else:
            # Empty, just show help text
            help_text = field.get("help_text", "")
            list_items = f"- ({help_text})" if help_text else "- To be determined"

        return markdown_format.format(label=label, list_items=list_items)

    def _generate_subsection_field(self, field: dict[str, Any]) -> str:
        """Generate markdown for a subsection-type field.

        Args:
            field: Field definition

        Returns:
            Markdown for the subsection
        """
        label = field.get("label", "")
        subitems = field.get("subitems", [])
        markdown_format = field.get("markdown_format", "**{label}:**\n{list_items}")

        list_items = "\n".join(f"- {item}" for item in subitems)
        return markdown_format.format(label=label, list_items=list_items)

    def get_wizard_fields(self) -> list[dict[str, Any]]:
        """Get list of fields that should appear in the wizard.

        Returns:
            List of field definitions where wizard_field=True
        """
        wizard_fields = []

        for section in self.schema.get("sections", []):
            for field in section.get("fields", []):
                if field.get("wizard_field", False):
                    wizard_fields.append({
                        "section_id": section.get("id"),
                        "section_title": section.get("title"),
                        "field_id": field.get("id"),
                        "label": field.get("label"),
                        "type": field.get("type"),
                        "required": field.get("required", False),
                        "help_text": field.get("help_text", "")
                    })

        return wizard_fields
