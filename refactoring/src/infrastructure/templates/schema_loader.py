"""Schema loading utilities for character templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Get project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
SCHEMA_DIR = project_root / "setup" / "templates" / "character_schemas"


class SchemaLoader:
    """Loads and manages character template schemas."""

    @staticmethod
    def get_available_schemas() -> list[str]:
        """Get list of available schema names.

        Returns:
            List of schema names (without .json extension)
        """
        if not SCHEMA_DIR.exists():
            return []

        schemas = []
        for schema_file in SCHEMA_DIR.glob("*.json"):
            # Skip base schema (it's for extending only)
            if schema_file.stem == "base_character_schema":
                continue
            schemas.append(schema_file.stem.replace("_character_schema", ""))

        return sorted(schemas)

    @staticmethod
    def load_schema(schema_name: str) -> dict[str, Any]:
        """Load a character schema by name.

        Args:
            schema_name: Name of schema (e.g., 'fantasy', 'minimal')
                        Will automatically add '_character_schema.json'

        Returns:
            Parsed schema dictionary

        Raises:
            FileNotFoundError: If schema doesn't exist
            json.JSONDecodeError: If schema is invalid JSON
        """
        # Normalize schema name
        if not schema_name.endswith("_character_schema"):
            schema_name = f"{schema_name}_character_schema"
        if not schema_name.endswith(".json"):
            schema_name = f"{schema_name}.json"

        schema_path = SCHEMA_DIR / schema_name

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def resolve_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """Resolve schema inheritance (extends field).

        Args:
            schema: Schema dictionary (may have 'extends' field)

        Returns:
            Fully resolved schema with parent sections merged in
        """
        # Check if schema extends another
        extends = schema.get("extends")
        if not extends:
            return schema

        # Load parent schema
        parent_name = extends.replace(".json", "").replace("_character_schema", "")
        parent_schema = SchemaLoader.load_schema(parent_name)

        # Recursively resolve parent
        parent_schema = SchemaLoader.resolve_schema(parent_schema)

        # Merge schemas (child overrides parent)
        resolved = {
            "template_name": schema.get("template_name", parent_schema.get("template_name", "")),
            "description": schema.get("description", parent_schema.get("description", "")),
            "sections": SchemaLoader._merge_sections(
                parent_schema.get("sections", []),
                schema.get("sections", [])
            )
        }

        return resolved

    @staticmethod
    def _merge_sections(
        parent_sections: list[dict[str, Any]],
        child_sections: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge parent and child sections.

        Args:
            parent_sections: Sections from parent schema
            child_sections: Sections from child schema

        Returns:
            Merged sections (child sections override parent by ID)
        """
        # Build lookup by section ID
        merged = {section["id"]: section.copy() for section in parent_sections}

        # Override with child sections
        for section in child_sections:
            section_id = section["id"]
            if section_id in merged:
                # Merge fields within section
                parent_fields = merged[section_id].get("fields", [])
                child_fields = section.get("fields", [])
                merged_fields = SchemaLoader._merge_fields(parent_fields, child_fields)

                merged[section_id] = section.copy()
                merged[section_id]["fields"] = merged_fields
            else:
                # New section from child
                merged[section_id] = section.copy()

        # Return sections in original order (parent first, then new child sections)
        result = []
        parent_ids = [s["id"] for s in parent_sections]
        child_only_ids = [s["id"] for s in child_sections if s["id"] not in parent_ids]

        for section_id in parent_ids:
            if section_id in merged:
                result.append(merged[section_id])

        for section_id in child_only_ids:
            result.append(merged[section_id])

        return result

    @staticmethod
    def _merge_fields(
        parent_fields: list[dict[str, Any]],
        child_fields: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge parent and child fields.

        Args:
            parent_fields: Fields from parent schema
            child_fields: Fields from child schema

        Returns:
            Merged fields (child fields override parent by ID)
        """
        # Build lookup by field ID
        merged = {field["id"]: field.copy() for field in parent_fields}

        # Override with child fields
        for field in child_fields:
            merged[field["id"]] = field.copy()

        # Return fields in order (parent first, then new child fields)
        result = []
        parent_ids = [f["id"] for f in parent_fields]
        child_only_ids = [f["id"] for f in child_fields if f["id"] not in parent_ids]

        for field_id in parent_ids:
            if field_id in merged:
                result.append(merged[field_id])

        for field_id in child_only_ids:
            result.append(merged[field_id])

        return result

    @staticmethod
    def load_and_resolve(schema_name: str) -> dict[str, Any]:
        """Load and fully resolve a schema (including inheritance).

        Args:
            schema_name: Name of schema (e.g., 'fantasy', 'minimal')

        Returns:
            Fully resolved schema dictionary
        """
        schema = SchemaLoader.load_schema(schema_name)
        return SchemaLoader.resolve_schema(schema)
