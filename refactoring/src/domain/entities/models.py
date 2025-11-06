"""Domain models for entity cards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...shared.models import EntityType


@dataclass
class EntityCard:
    """Parsed representation of an entity card."""

    name: str
    entity_type: EntityType
    file_path: Path
    triggers: list[str]
    full_content: str
    personality_core: str | None
    metadata: dict[str, Any]
    sections: dict[str, str]
