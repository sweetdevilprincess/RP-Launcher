"""Narrative template manager for genre-specific guidance.

Manages template selection, loading, and rendering with support for
multiple composition modes.

Refactored from src/automation/prompt_templates.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ...shared.interfaces.config_service import ConfigService
from ...shared.logging import get_logger
from .template_loader import TemplateLoader
from .template_registry import TemplateRegistry


class NarrativeTemplateManager:
    """High-level manager for narrative template selection and rendering.

    Supports 4 template modes:
    - auto: Smart detection from ROLEPLAY_OVERVIEW.md
    - composite: Pre-made genre combination templates
    - modular: Mix sections from different genres
    - layered: Primary genre + secondary highlights

    Example:
        >>> manager = NarrativeTemplateManager(rp_dir, config_service, template_loader, registry)
        >>> instructions = manager.generate_narrative_instructions()
    """

    def __init__(
        self,
        rp_dir: Path,
        config_service: ConfigService,
        template_loader: TemplateLoader,
        template_registry: TemplateRegistry,
    ) -> None:
        """Initialize narrative template manager.

        Args:
            rp_dir: RP directory path
            config_service: Configuration service
            template_loader: Template loader instance
            template_registry: Template registry instance
        """
        self._rp_dir = rp_dir
        self._config = config_service
        self._loader = template_loader
        self._registry = template_registry
        self._logger = get_logger(__name__)

    def generate_narrative_instructions(self) -> str:
        """Generate narrative instructions based on configuration.

        Returns:
            Formatted narrative instructions or empty string
        """
        mode = self._config.get_str("narrative_template.mode", default="auto")

        try:
            if mode == "composite":
                return self._load_composite_template()
            if mode == "modular":
                return self._build_modular_template()
            if mode == "layered":
                return self._build_layered_template()
            if mode == "auto":
                return self._auto_select_template()
            self._logger.warning("narrative_template.unknown_mode", context={"mode": mode})
            return ""

        except Exception as e:
            self._logger.error(
                "narrative_template.generation_error",
                context={"mode": mode, "error": str(e)},
            )
            return ""

    def _load_composite_template(self) -> str:
        """Mode 1: Load pre-made composite template."""
        template_name = self._config.get_str("narrative_template.template")

        if not template_name:
            self._logger.warning(
                "narrative_template.missing_config",
                context={"mode": "composite", "required": "template"},
            )
            return ""

        template_data = self._loader.load_template(template_name)
        if template_data:
            self._logger.info(
                "narrative_template.composite_loaded",
                context={"template": template_name},
            )
            return self._format_template_for_prompt(template_data)

        return ""

    def _build_modular_template(self) -> str:
        """Mode 2: Mix sections from different genres."""
        # Get sections config as dict
        sections_config = self._config.get_dict("narrative_template.sections", default={})

        if not sections_config:
            self._logger.warning(
                "narrative_template.missing_config",
                context={"mode": "modular", "required": "sections"},
            )
            return ""

        # Build custom template by mixing sections
        mixed_template: dict[str, Any] = {
            "display_name": "Custom Modular Template",
            "sections": {},
        }

        for section_key, genre in sections_config.items():
            template_data = self._loader.load_template(str(genre))
            if template_data:
                sections = template_data.get("sections", {})
                if section_key in sections:
                    mixed_template["sections"][section_key] = sections[section_key]

        if mixed_template["sections"]:
            self._logger.info(
                "narrative_template.modular_built",
                context={"section_count": len(mixed_template["sections"])},
            )
            return self._format_template_for_prompt(mixed_template)

        return ""

    def _build_layered_template(self) -> str:
        """Mode 3: Primary genre + secondary highlights."""
        primary = self._config.get_str("narrative_template.primary")
        secondary = self._config.get_str("narrative_template.secondary")

        if not primary:
            self._logger.warning(
                "narrative_template.missing_config",
                context={"mode": "layered", "required": "primary"},
            )
            return ""

        # Load primary template
        primary_data = self._loader.load_template(primary)
        if not primary_data:
            return ""

        lines = []
        lines.append(self._format_template_for_prompt(primary_data))

        # Add secondary highlights if specified
        if secondary:
            secondary_data = self._loader.load_template(secondary)
            if secondary_data:
                lines.append("")
                lines.append(
                    f"**Secondary Influences: {secondary_data.get('display_name', secondary)}**"
                )

                highlights = secondary_data.get("highlights", [])
                for highlight in highlights:
                    lines.append(f"- {highlight}")
                lines.append("")

        self._logger.info(
            "narrative_template.layered_built",
            context={"primary": primary, "secondary": secondary or "none"},
        )

        return "\n".join(lines)

    def _auto_select_template(self) -> str:
        """Mode Auto: Smart detection from ROLEPLAY_OVERVIEW.md."""
        primary, secondary = self._parse_genre_from_overview()

        if not primary:
            self._logger.debug(
                "narrative_template.auto_no_genre",
                context={"message": "No genre found in ROLEPLAY_OVERVIEW.md"},
            )
            return ""

        # Try composite template first (if secondary genre exists)
        if secondary:
            composite_name = self._registry.find_composite_template(primary, secondary)
            if composite_name:
                composite_data = self._loader.load_template(composite_name)
                if composite_data:
                    self._logger.info(
                        "narrative_template.auto_composite",
                        context={"template": composite_name},
                    )
                    return self._format_template_for_prompt(composite_data)

        # Fall back to layered (primary + secondary highlights)
        if secondary:
            primary_data = self._loader.load_template(primary)
            secondary_data = self._loader.load_template(secondary)

            if primary_data:
                lines = []
                lines.append(self._format_template_for_prompt(primary_data))

                if secondary_data:
                    lines.append("")
                    lines.append(
                        f"**Secondary Influences: {secondary_data.get('display_name', secondary)}**"
                    )
                    highlights = secondary_data.get("highlights", [])
                    for highlight in highlights:
                        lines.append(f"- {highlight}")
                    lines.append("")

                self._logger.info(
                    "narrative_template.auto_layered",
                    context={"primary": primary, "secondary": secondary},
                )

                return "\n".join(lines)

        # Just primary genre
        primary_data = self._loader.load_template(primary)
        if primary_data:
            self._logger.info("narrative_template.auto_primary", context={"template": primary})
            return self._format_template_for_prompt(primary_data)

        self._logger.warning("narrative_template.auto_not_found", context={"primary": primary})
        return ""

    def _parse_genre_from_overview(self) -> tuple[str | None, str | None]:
        """Extract primary/secondary genre from ROLEPLAY_OVERVIEW.md.

        Returns:
            Tuple of (primary_genre, secondary_genre) or (None, None)
        """
        overview_file = self._rp_dir / "ROLEPLAY_OVERVIEW.md"

        if not overview_file.exists():
            return (None, None)

        try:
            content = overview_file.read_text(encoding="utf-8")

            # Look for **Genre**: line
            match = re.search(r"\*\*Genre\*\*:\s*([^\n]+)", content)
            if match:
                genre_text = match.group(1).strip()

                # Parse "Primary / Secondary" or "Primary/Secondary" or just "Primary"
                if "/" in genre_text:
                    parts = [p.strip() for p in genre_text.split("/")]
                    primary = self._registry.normalize_genre_name(parts[0])
                    secondary = (
                        self._registry.normalize_genre_name(parts[1]) if len(parts) > 1 else None
                    )
                    return (primary, secondary)
                primary = self._registry.normalize_genre_name(genre_text)
                return (primary, None)

        except Exception as e:
            self._logger.error(
                "narrative_template.overview_parse_error",
                context={"overview_file": str(overview_file), "error": str(e)},
            )

        return (None, None)

    def _format_template_for_prompt(self, template_data: dict[str, Any]) -> str:
        """Convert JSON template to markdown for prompt injection.

        Args:
            template_data: Template dict from JSON

        Returns:
            Formatted markdown string
        """
        lines = []
        lines.append("<!-- ========== NARRATIVE TEMPLATE ========== -->")
        lines.append(f"**Genre**: {template_data.get('display_name', 'Unknown')}")
        lines.append("")

        sections = template_data.get("sections", {})
        for section_key, section_data in sections.items():
            title = section_data.get("title", section_key)
            content = section_data.get("content", [])

            lines.append(f"**{title}**:")
            for item in content:
                lines.append(f"- {item}")
            lines.append("")

        lines.append("---")
        return "\n".join(lines)
