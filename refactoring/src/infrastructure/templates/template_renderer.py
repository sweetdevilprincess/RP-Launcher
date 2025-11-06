"""Template rendering utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from string import Template
from typing import Any

from ...shared.interfaces import LoggingService  # type: ignore[attr-defined]


class TemplateRenderer:
    """Loads text or JSON templates and renders them with context."""

    def __init__(
        self, *, base_dir: Path | None = None, logger: LoggingService | None = None
    ) -> None:
        self.base_dir = (base_dir or Path(__file__).resolve().parents[3] / "templates").resolve()
        self.logger = logger

    def render_text(self, template_name: str, context: Mapping[str, Any]) -> str:
        path = self._resolve(template_name)
        text = path.read_text(encoding="utf-8")
        rendered = Template(text).safe_substitute(context)
        if self.logger:
            self.logger.debug(
                "template.render_text",
                context={"template": str(path), "keys": sorted(context.keys())},
            )
        return rendered

    def render_json(self, template_name: str, context: Mapping[str, Any]) -> dict[str, Any]:
        path = self._resolve(template_name)
        data = json.loads(path.read_text(encoding="utf-8"))
        rendered = self._apply_context(data, context)
        if self.logger:
            self.logger.debug(
                "template.render_json",
                context={"template": str(path), "keys": sorted(context.keys())},
            )
        return rendered

    def _resolve(self, template_name: str) -> Path:
        path = (self.base_dir / template_name).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Template not found: {template_name}")
        if self.base_dir not in path.parents and path != self.base_dir:
            raise ValueError("Template path escapes base directory")
        return path

    def _apply_context(self, data: Any, context: Mapping[str, Any]) -> Any:
        if isinstance(data, str):
            return Template(data).safe_substitute(context)
        if isinstance(data, list):
            return [self._apply_context(item, context) for item in data]
        if isinstance(data, dict):
            return {key: self._apply_context(value, context) for key, value in data.items()}
        return data
