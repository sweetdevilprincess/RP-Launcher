"""Template loader for JSON template files.

Loads narrative template files from disk with caching support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...shared.logging import get_logger
from .template_cache import TemplateCache


class TemplateLoader:
    """Loads narrative templates from JSON files with caching.

    This loader:
    1. Loads template JSON files from a base directory
    2. Validates template structure
    3. Caches templates in memory for performance
    4. Supports lazy loading (only loads when requested)

    Template Structure:
        {
            "display_name": "Fantasy Adventure",
            "sections": {
                "tone": {
                    "title": "Narrative Tone",
                    "content": ["Item 1", "Item 2"]
                },
                ...
            },
            "highlights": ["Optional highlight 1", ...]
        }

    Example:
        >>> loader = TemplateLoader(template_dir, cache)
        >>> template = loader.load_template("fantasy")
        >>> template["display_name"]
        "Fantasy Adventure"
    """

    def __init__(
        self,
        template_dir: Path,
        cache: TemplateCache | None = None,
    ) -> None:
        """Initialize template loader.

        Args:
            template_dir: Base directory containing template JSON files
            cache: Optional template cache (creates new if not provided)
        """
        self._template_dir = template_dir
        self._cache = cache or TemplateCache()
        self._logger = get_logger(__name__)

    def load_template(self, template_name: str) -> dict[str, Any] | None:
        """Load a template by name.

        Args:
            template_name: Template name (with or without .json extension)

        Returns:
            Template dict if found and valid, None otherwise
        """
        # Normalize template name
        if not template_name.endswith(".json"):
            template_name += ".json"

        template_path = self._template_dir / template_name

        # Check cache first
        cached = self._cache.get(template_path)
        if cached is not None:
            return cached

        # Load from disk
        template_data = self._load_from_disk(template_path)

        if template_data is not None:
            # Validate structure
            if self._validate_template(template_data):
                # Cache for future use
                self._cache.put(template_path, template_data)
                return template_data
            self._logger.warning(
                "template_loader.invalid_structure",
                context={"template_path": str(template_path)},
            )

        return None

    def load_template_sections(self, template_name: str, section_keys: list[str]) -> dict[str, Any]:
        """Load specific sections from a template.

        Args:
            template_name: Template name
            section_keys: List of section keys to extract

        Returns:
            Dict with only the requested sections
        """
        template = self.load_template(template_name)
        if not template:
            return {}

        sections = template.get("sections", {})
        filtered_sections = {key: sections[key] for key in section_keys if key in sections}

        return filtered_sections

    def invalidate_cache(self, template_name: str) -> bool:
        """Invalidate cached template (forces reload).

        Args:
            template_name: Template name to invalidate

        Returns:
            True if template was in cache, False otherwise
        """
        if not template_name.endswith(".json"):
            template_name += ".json"

        template_path = self._template_dir / template_name
        return self._cache.invalidate(template_path)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache stats dict
        """
        return self._cache.get_stats()

    def _load_from_disk(self, template_path: Path) -> dict[str, Any] | None:
        """Load template from disk.

        Args:
            template_path: Full path to template file

        Returns:
            Template dict if successful, None otherwise
        """
        if not template_path.exists():
            self._logger.debug(
                "template_loader.file_not_found",
                context={"template_path": str(template_path)},
            )
            return None

        try:
            with open(template_path, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                self._logger.debug(
                    "template_loader.loaded",
                    context={
                        "template_path": str(template_path),
                        "display_name": data.get("display_name", "unknown"),
                    },
                )
                return data
            self._logger.warning(
                "template_loader.invalid_format",
                context={
                    "template_path": str(template_path),
                    "type": type(data).__name__,
                },
            )

        except Exception as e:
            self._logger.error(
                "template_loader.load_error",
                context={"template_path": str(template_path), "error": str(e)},
            )

        return None

    def _validate_template(self, template_data: dict[str, Any]) -> bool:
        """Validate template structure.

        Args:
            template_data: Template dict to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if "display_name" not in template_data:
            return False

        if "sections" not in template_data:
            return False

        sections = template_data["sections"]
        if not isinstance(sections, dict):
            return False

        # Validate each section
        for section_key, section_data in sections.items():
            if not isinstance(section_data, dict):
                return False

            # Each section should have title and content
            if "title" not in section_data or "content" not in section_data:
                return False

            # Content should be a list
            if not isinstance(section_data["content"], list):
                return False

        return True
