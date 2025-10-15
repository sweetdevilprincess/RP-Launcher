#!/usr/bin/env python3
"""
Prompt Template Manager - Genre-Specific Narrative Guidance

Supports 4 modes:
- auto: Smart detection from ROLEPLAY_OVERVIEW.md
- composite: Pre-made genre combination templates
- modular: Mix sections from different genres
- layered: Primary genre + secondary highlights

Part of Phase 3.1: Prompt Templates & Macros
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from src.automation.core import log_to_file


class PromptTemplateManager:
    """Manages narrative template selection and generation using JSON templates"""

    def __init__(self, rp_dir: Path):
        """Initialize template manager

        Args:
            rp_dir: RP directory path
        """
        self.rp_dir = rp_dir
        self.template_dir = Path(__file__).parent.parent.parent / "config" / "templates" / "prompts"
        self.log_file = rp_dir / "state" / "hook.log"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load narrative template config from automation_config.json"""
        config_file = self.rp_dir / "state" / "automation_config.json"
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                    return full_config.get("narrative_template", {"mode": "auto"})
        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Error loading config: {e}")

        return {"mode": "auto"}

    def generate_narrative_instructions(self) -> str:
        """Main entry point - generates template based on config

        Returns:
            Formatted narrative instructions for prompt injection or empty string
        """
        mode = self.config.get("mode", "auto")

        try:
            if mode == "composite":
                return self._load_composite_template()
            elif mode == "modular":
                return self._build_modular_template()
            elif mode == "layered":
                return self._build_layered_template()
            elif mode == "auto":
                return self._auto_select_template()
            else:
                log_to_file(self.log_file, f"[PromptTemplateManager] Unknown mode: {mode}")
                return ""

        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Error generating template: {e}")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())
            return ""

    def _load_template_json(self, template_name: str) -> Optional[Dict]:
        """Load template JSON file

        Args:
            template_name: Template filename (with or without .json)

        Returns:
            Template dict or None if not found
        """
        if not template_name.endswith('.json'):
            template_name += '.json'

        template_path = self.template_dir / template_name

        try:
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                log_to_file(self.log_file, f"[PromptTemplateManager] Template not found: {template_name}")
        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Error loading {template_name}: {e}")

        return None

    def _format_template_for_prompt(self, template_data: Dict) -> str:
        """Convert JSON template to markdown for prompt injection

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

    def _load_composite_template(self) -> str:
        """Mode 1: Load pre-made composite template"""
        template_name = self.config.get("template")
        if not template_name:
            log_to_file(self.log_file, "[PromptTemplateManager] Composite mode requires 'template' config")
            return ""

        template_data = self._load_template_json(template_name)
        if template_data:
            log_to_file(self.log_file, f"[PromptTemplateManager] Loaded composite template: {template_name}")
            return self._format_template_for_prompt(template_data)

        return ""

    def _build_modular_template(self) -> str:
        """Mode 2: Mix sections from different genres"""
        sections_config = self.config.get("sections", {})
        if not sections_config:
            log_to_file(self.log_file, "[PromptTemplateManager] Modular mode requires 'sections' config")
            return ""

        # Build custom template by mixing sections
        mixed_template = {
            "display_name": "Custom Modular Template",
            "sections": {}
        }

        for section_key, genre in sections_config.items():
            template_data = self._load_template_json(genre)
            if template_data and section_key in template_data.get("sections", {}):
                mixed_template["sections"][section_key] = template_data["sections"][section_key]

        if mixed_template["sections"]:
            log_to_file(self.log_file, f"[PromptTemplateManager] Built modular template with {len(mixed_template['sections'])} sections")
            return self._format_template_for_prompt(mixed_template)

        return ""

    def _build_layered_template(self) -> str:
        """Mode 3: Primary + secondary highlights"""
        primary = self.config.get("primary")
        secondary = self.config.get("secondary")

        if not primary:
            log_to_file(self.log_file, "[PromptTemplateManager] Layered mode requires 'primary' config")
            return ""

        # Load primary template
        primary_data = self._load_template_json(primary)
        if not primary_data:
            return ""

        lines = []
        lines.append(self._format_template_for_prompt(primary_data))

        # Add secondary highlights if specified
        if secondary:
            secondary_data = self._load_template_json(secondary)
            if secondary_data:
                lines.append("")
                lines.append(f"**Secondary Influences: {secondary_data.get('display_name', secondary)}**")
                highlights = secondary_data.get("highlights", [])
                for highlight in highlights:
                    lines.append(f"- {highlight}")
                lines.append("")

        log_to_file(self.log_file, f"[PromptTemplateManager] Built layered template: {primary}" + (f" + {secondary}" if secondary else ""))
        return "\n".join(lines)

    def _auto_select_template(self) -> str:
        """Mode Auto: Smart detection from ROLEPLAY_OVERVIEW.md"""
        primary, secondary = self._parse_genre_from_overview()

        if not primary:
            # No genre found, no template
            log_to_file(self.log_file, "[PromptTemplateManager] Auto mode: No genre found in ROLEPLAY_OVERVIEW.md")
            return ""

        # Try composite template first (if secondary genre exists)
        if secondary:
            # Try both orders: primary_secondary and secondary_primary
            composite_names = [
                f"{primary}_{secondary}",
                f"{secondary}_{primary}"
            ]

            for composite_name in composite_names:
                composite_data = self._load_template_json(composite_name)
                if composite_data:
                    log_to_file(self.log_file, f"[PromptTemplateManager] Auto-selected composite: {composite_name}")
                    return self._format_template_for_prompt(composite_data)

        # Fall back to layered (primary + secondary highlights)
        if secondary:
            temp_config = {"primary": primary, "secondary": secondary}
            old_config = self.config
            self.config = temp_config
            result = self._build_layered_template()
            self.config = old_config
            log_to_file(self.log_file, f"[PromptTemplateManager] Auto mode: Using layered fallback")
            return result

        # Just primary genre
        primary_data = self._load_template_json(primary)
        if primary_data:
            log_to_file(self.log_file, f"[PromptTemplateManager] Auto-selected: {primary}")
            return self._format_template_for_prompt(primary_data)

        log_to_file(self.log_file, f"[PromptTemplateManager] Auto mode: Could not load template for {primary}")
        return ""

    def _parse_genre_from_overview(self) -> Tuple[Optional[str], Optional[str]]:
        """Extract primary/secondary genre from ROLEPLAY_OVERVIEW.md

        Returns:
            Tuple of (primary_genre, secondary_genre) or (None, None)
        """
        overview_file = self.rp_dir / "ROLEPLAY_OVERVIEW.md"

        if not overview_file.exists():
            log_to_file(self.log_file, "[PromptTemplateManager] ROLEPLAY_OVERVIEW.md not found")
            return (None, None)

        try:
            content = overview_file.read_text(encoding='utf-8')

            # Look for **Genre**: line
            match = re.search(r'\*\*Genre\*\*:\s*([^\n]+)', content)
            if match:
                genre_text = match.group(1).strip()

                # Parse "Primary / Secondary" or "Primary/Secondary" or just "Primary"
                if '/' in genre_text:
                    parts = [p.strip() for p in genre_text.split('/')]
                    primary = self._normalize_genre_name(parts[0])
                    secondary = self._normalize_genre_name(parts[1]) if len(parts) > 1 else None
                    log_to_file(self.log_file, f"[PromptTemplateManager] Parsed genres: {primary}, {secondary}")
                    return (primary, secondary)
                else:
                    primary = self._normalize_genre_name(genre_text)
                    log_to_file(self.log_file, f"[PromptTemplateManager] Parsed genre: {primary}")
                    return (primary, None)
            else:
                log_to_file(self.log_file, "[PromptTemplateManager] No **Genre**: field found in ROLEPLAY_OVERVIEW.md")

        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Error parsing ROLEPLAY_OVERVIEW.md: {e}")

        return (None, None)

    def _normalize_genre_name(self, genre: str) -> str:
        """Normalize genre name to template filename format

        Args:
            genre: Genre string from config or ROLEPLAY_OVERVIEW

        Returns:
            Normalized genre name (lowercase, underscores)

        Examples:
            "Dark Romance" -> "dark_romance"
            "Slice of Life" -> "slice_of_life"
            "Thriller" -> "thriller"
        """
        return genre.lower().replace(' ', '_').replace('-', '_')
