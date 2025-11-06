"""Services for rendering state-related templates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ...shared.models import EntityType
from .template_renderer import TemplateRenderer


class StateTemplateService:
    """Wraps TemplateRenderer with domain-specific helpers."""

    def __init__(self, *, renderer: TemplateRenderer | None = None) -> None:
        self._renderer = renderer or TemplateRenderer()

    def render_story_arc_summary(
        self,
        *,
        response_count: int,
        summary: str,
        timestamp: str | None = None,
    ) -> str:
        context = {
            "response_count": response_count,
            "summary": summary,
            "timestamp": timestamp or datetime.utcnow().isoformat() + "Z",
        }
        return self._renderer.render_text("state/story_arc.md.tpl", context)

    def render_character_card(self, name: str) -> str:
        return self._renderer.render_text(
            "state/character_card.md.tpl",
            {"name": name, "type_tag": "CHAR"},
        )

    def render_location_card(self, name: str) -> str:
        return self._renderer.render_text(
            "state/location_card.md.tpl",
            {"name": name, "type_tag": "LOC"},
        )

    def render_organization_card(self, name: str) -> str:
        return self._renderer.render_text(
            "state/organization_card.md.tpl",
            {"name": name, "type_tag": "ORG"},
        )

    def render_entity_card(self, name: str, entity_type: EntityType) -> str:
        if entity_type is EntityType.CHARACTER:
            return self.render_character_card(name)
        if entity_type is EntityType.LOCATION:
            return self.render_location_card(name)
        if entity_type is EntityType.ORGANIZATION:
            return self.render_organization_card(name)
        return self._renderer.render_text(
            "state/generic_entity_card.md.tpl",
            {"name": name, "type_tag": entity_type.value.upper()},
        )

    def render_character_preferences(self, character_name: str) -> dict[str, Any]:
        return self._renderer.render_json(
            "state/character_preferences.json.tpl",
            {
                "character_name": character_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
