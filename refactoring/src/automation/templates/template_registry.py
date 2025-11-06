"""Template registry for discovering available templates.

Discovers and catalogs available narrative templates from the template directory.
"""

from __future__ import annotations

from pathlib import Path

from ...shared.logging import get_logger


class TemplateRegistry:
    """Registry for discovering and managing narrative templates.

    This registry:
    1. Discovers available templates in the template directory
    2. Provides methods to query template availability
    3. Supports genre normalization for consistent naming

    Example:
        >>> registry = TemplateRegistry(template_dir)
        >>> available = registry.list_available_templates()
        >>> "fantasy" in available
        True
        >>> registry.has_template("dark_romance")
        True
    """

    def __init__(self, template_dir: Path) -> None:
        """Initialize template registry.

        Args:
            template_dir: Directory containing template JSON files
        """
        self._template_dir = template_dir
        self._logger = get_logger(__name__)
        self._available_templates: list[str] = []
        self._refresh_available_templates()

    def list_available_templates(self) -> list[str]:
        """List all available template names.

        Returns:
            List of template names (without .json extension)
        """
        return self._available_templates.copy()

    def has_template(self, template_name: str) -> bool:
        """Check if a template exists.

        Args:
            template_name: Template name to check (with or without .json)

        Returns:
            True if template exists, False otherwise
        """
        # Normalize name (remove .json if present)
        normalized_name = template_name.replace(".json", "")
        return normalized_name in self._available_templates

    def find_composite_template(self, primary: str, secondary: str) -> str | None:
        """Find a composite template combining two genres.

        Tries both "{primary}_{secondary}" and "{secondary}_{primary}".

        Args:
            primary: Primary genre name
            secondary: Secondary genre name

        Returns:
            Template name if found, None otherwise
        """
        # Normalize genre names
        primary_normalized = self.normalize_genre_name(primary)
        secondary_normalized = self.normalize_genre_name(secondary)

        # Try both orders
        candidates = [
            f"{primary_normalized}_{secondary_normalized}",
            f"{secondary_normalized}_{primary_normalized}",
        ]

        for candidate in candidates:
            if self.has_template(candidate):
                self._logger.debug(
                    "template_registry.composite_found",
                    context={
                        "primary": primary,
                        "secondary": secondary,
                        "template": candidate,
                    },
                )
                return candidate

        return None

    def normalize_genre_name(self, genre: str) -> str:
        """Normalize genre name to template filename format.

        Args:
            genre: Genre string from config or overview

        Returns:
            Normalized genre name (lowercase, underscores)

        Examples:
            >>> registry.normalize_genre_name("Dark Romance")
            "dark_romance"
            >>> registry.normalize_genre_name("Slice of Life")
            "slice_of_life"
        """
        return genre.lower().replace(" ", "_").replace("-", "_")

    def refresh(self) -> None:
        """Refresh the list of available templates.

        Useful if templates are added/removed at runtime.
        """
        self._refresh_available_templates()
        self._logger.info(
            "template_registry.refreshed",
            context={"template_count": len(self._available_templates)},
        )

    def _refresh_available_templates(self) -> None:
        """Scan template directory and update available templates list."""
        self._available_templates = []

        if not self._template_dir.exists():
            self._logger.warning(
                "template_registry.directory_not_found",
                context={"template_dir": str(self._template_dir)},
            )
            return

        try:
            for template_file in self._template_dir.glob("*.json"):
                # Remove .json extension
                template_name = template_file.stem
                self._available_templates.append(template_name)

            self._logger.debug(
                "template_registry.templates_discovered",
                context={
                    "template_dir": str(self._template_dir),
                    "template_count": len(self._available_templates),
                    "templates": self._available_templates,
                },
            )

        except Exception as e:
            self._logger.error(
                "template_registry.scan_error",
                context={"template_dir": str(self._template_dir), "error": str(e)},
            )
