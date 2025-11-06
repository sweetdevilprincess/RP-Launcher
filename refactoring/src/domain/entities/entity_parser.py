"""Entity parsing dataclasses and helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CharacterEntity:
    name: str
    basics: Mapping[str, Any]
    appearance: Mapping[str, Any]
    personality: Mapping[str, Any]
    preferences: Mapping[str, Any]
    abilities: Mapping[str, Any]
    background: Mapping[str, Any]
    metadata: Mapping[str, Any]

    @property
    def core_mandate(self) -> str | None:
        return self.personality.get("core_mandate")


@dataclass(frozen=True)
class LocationEntity:
    name: str
    basics: Mapping[str, Any]
    geography: Mapping[str, Any]
    facilities: Mapping[str, Any]
    culture: Mapping[str, Any]
    hooks: Mapping[str, Any]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class OrganizationEntity:
    name: str
    basics: Mapping[str, Any]
    structure: Mapping[str, Any]
    resources: Mapping[str, Any]
    relations: Mapping[str, Any]
    operations: Mapping[str, Any]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class ItemEntity:
    name: str
    basics: Mapping[str, Any]
    attributes: Mapping[str, Any]
    usage: Mapping[str, Any]
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    summary: str
    details: str
    tags: Sequence[str]
    quoted_dialogue: Sequence[str]
    relationships: Mapping[str, Any]
    location: str
    chapter: str
    timestamp: str | None
    message_index: int = 0  # Message index where this memory was created (for temporal filtering)


@dataclass(frozen=True)
class MemoryLog:
    character: str
    entries: Sequence[MemoryEntry]
    session_id: str = "main"  # Session/timeline this memory log belongs to


def _require_keys(data: Mapping[str, Any], keys: Sequence[str], entity: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"{entity} missing keys: {', '.join(missing)}")


def parse_character(data: Mapping[str, Any]) -> CharacterEntity:
    _require_keys(
        data,
        [
            "name",
            "basics",
            "appearance",
            "personality",
            "preferences",
            "abilities",
            "background",
            "metadata",
        ],
        "Character entity",
    )
    return CharacterEntity(
        name=str(data["name"]),
        basics=data["basics"],
        appearance=data["appearance"],
        personality=data["personality"],
        preferences=data["preferences"],
        abilities=data["abilities"],
        background=data["background"],
        metadata=data["metadata"],
    )


def parse_location(data: Mapping[str, Any]) -> LocationEntity:
    _require_keys(
        data,
        ["name", "basics", "geography", "facilities", "culture", "hooks", "metadata"],
        "Location entity",
    )
    return LocationEntity(
        name=str(data["name"]),
        basics=data["basics"],
        geography=data["geography"],
        facilities=data["facilities"],
        culture=data["culture"],
        hooks=data["hooks"],
        metadata=data["metadata"],
    )


def parse_organization(data: Mapping[str, Any]) -> OrganizationEntity:
    _require_keys(
        data,
        ["name", "basics", "structure", "resources", "relations", "operations", "metadata"],
        "Organization entity",
    )
    return OrganizationEntity(
        name=str(data["name"]),
        basics=data["basics"],
        structure=data["structure"],
        resources=data["resources"],
        relations=data["relations"],
        operations=data["operations"],
        metadata=data["metadata"],
    )


def parse_item(data: Mapping[str, Any]) -> ItemEntity:
    _require_keys(
        data,
        ["name", "basics", "attributes", "usage", "metadata"],
        "Item entity",
    )
    return ItemEntity(
        name=str(data["name"]),
        basics=data["basics"],
        attributes=data["attributes"],
        usage=data["usage"],
        metadata=data["metadata"],
    )


def parse_memories(data: Mapping[str, Any]) -> MemoryLog:
    _require_keys(data, ["character", "entries"], "Memory log")
    entries: list[MemoryEntry] = []
    for entry in data["entries"]:
        _require_keys(
            entry,
            [
                "id",
                "summary",
                "details",
                "tags",
                "quoted_dialogue",
                "relationships",
                "location",
                "chapter",
            ],
            "Memory entry",
        )
        entries.append(
            MemoryEntry(
                id=str(entry["id"]),
                summary=str(entry["summary"]),
                details=str(entry["details"]),
                tags=list(entry.get("tags", [])),
                quoted_dialogue=list(entry.get("quoted_dialogue", [])),
                relationships=entry.get("relationships", {}),
                location=str(entry.get("location", "")),
                chapter=str(entry.get("chapter", "")),
                timestamp=entry.get("timestamp"),
            )
        )
    return MemoryLog(character=str(data["character"]), entries=entries)
