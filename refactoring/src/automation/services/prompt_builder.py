"""Prompt building utilities for automation pipelines."""

from __future__ import annotations

from pathlib import Path

from ...shared.interfaces import ConfigService, LoggingService
from ..contracts import AutomationContext
from ..templates import (
    NarrativeTemplateManager,
    TemplateCache,
    TemplateLoader,
    TemplateRegistry,
)
from .prompt_sections import build_all_sections


class PromptBuilder:
    """Compose prompts for agents using the active configuration."""

    def __init__(
        self,
        *,
        config: ConfigService,
        logger: LoggingService,
        rp_dir: Path | None = None,
    ) -> None:
        self._config = config
        self._logger = logger
        self._rp_dir = rp_dir

        # Template system components (initialized on first use with rp_dir)
        self._template_cache: TemplateCache | None = None
        self._template_loader: TemplateLoader | None = None
        self._template_registry: TemplateRegistry | None = None
        self._template_manager: NarrativeTemplateManager | None = None

    def _should_use_templates(self) -> bool:
        """Check if narrative templates are enabled.

        Returns:
            True if templates should be used
        """
        return self._config.get_bool("narrative_template.enabled", default=True)

    def build_prompt(self, context: AutomationContext) -> str:
        """Construct the agent prompt from context data.

        Args:
            context: Automation context with all loaded data

        Returns:
            Fully assembled prompt string
        """
        self._logger.debug("prompt_builder.start", context={"rp_dir": str(context.rp_dir)})

        # Build narrative template section (if enabled)
        narrative_instructions = ""
        if self._template_manager is None and self._should_use_templates():
            # Lazy initialization of template system using rp_dir from context
            template_dir_str = self._config.get_str(
                "narrative_template.template_dir",
                default="config/templates/prompts",
            )
            template_dir = context.rp_dir / template_dir_str

            # Create template components
            cache_size = self._config.get_int("narrative_template.cache_size", default=50)
            self._template_cache = TemplateCache(max_size=cache_size)
            self._template_loader = TemplateLoader(template_dir, self._template_cache)
            self._template_registry = TemplateRegistry(template_dir)

            # Create template manager
            self._template_manager = NarrativeTemplateManager(
                context.rp_dir,
                self._config,
                self._template_loader,
                self._template_registry,
            )

            self._logger.info(
                "prompt_builder.templates_initialized",
                context={"template_dir": str(template_dir), "cache_size": cache_size},
            )

        if self._template_manager:
            narrative_instructions = self._template_manager.generate_narrative_instructions()

        # Build all applicable sections
        sections = build_all_sections(context)

        # Combine: narrative template + sections
        parts = []
        if narrative_instructions:
            parts.append(narrative_instructions)

        prompt_sections = "\n\n".join(section.render() for section in sections if section.body)
        parts.append(prompt_sections)

        prompt = "\n\n".join(parts)

        self._logger.debug(
            "prompt_builder.complete",
            context={
                "length": len(prompt),
                "section_count": len(sections),
                "has_narrative_template": bool(narrative_instructions),
            },
        )

        return prompt
