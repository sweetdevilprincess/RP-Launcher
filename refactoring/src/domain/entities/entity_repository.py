"""Fixture-backed entity repository for refactor testing."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Union

from .entity_parser import (
    CharacterEntity,
    ItemEntity,
    LocationEntity,
    MemoryLog,
    OrganizationEntity,
    parse_character,
    parse_item,
    parse_location,
    parse_memories,
    parse_organization,
)

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "entities" / "fixtures"
MappingLike = Union[
    Mapping[str, object], CharacterEntity, LocationEntity, OrganizationEntity, ItemEntity, MemoryLog
]


class FixtureEntityRepository:
    """Repository that surfaces JSON fixtures as parsed entity objects."""

    def __init__(
        self,
        rp_dir: Path | None = None,
        base_dir: Path | None = None,
        session_state_service: Any | None = None,
    ) -> None:
        # Determine base directory for entity files
        if base_dir:
            self.base_dir = base_dir
        elif rp_dir:
            # Check entities/ first, fall back to characters/ for legacy support
            entities_dir = rp_dir / "entities"
            characters_dir = rp_dir / "characters"
            self.base_dir = entities_dir if entities_dir.exists() else characters_dir
        else:
            # Default to test fixtures
            self.base_dir = FIXTURE_DIR

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.rp_dir = rp_dir
        self.session_state_service = session_state_service
        self._character_index = self._index("character_*.json")
        self._location_index = self._index("location_*.json")
        self._organization_index = self._index("organization_*.json")
        self._item_index = self._index("item_*.json")
        self._memory_index = self._index("*_memories.json")

    # ------------------------------------------------------------------
    # Index helpers

    def _index(self, pattern: str) -> dict[str, Path]:
        index: dict[str, Path] = {}
        for path in self.base_dir.glob(pattern):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                name = str(data.get("name") or data.get("character"))
                if name:
                    index[name] = path
        return index

    def _slug(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
        return slug.strip("_") or "entity"

    def _to_mapping(self, data: MappingLike) -> Mapping[str, object]:
        if is_dataclass(data):
            return asdict(data)
        if isinstance(data, Mapping):
            return data
        raise TypeError("Entity data must be a mapping or dataclass instance")

    def _write_json(self, path: Path, data: Mapping[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)

    def _load(self, path: Path) -> Mapping[str, object]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    # ------------------------------------------------------------------
    # Characters

    def list_characters(self) -> list[CharacterEntity]:
        return [self.get_character(name) for name in sorted(self._character_index)]

    def get_character(self, name: str) -> CharacterEntity:
        path = self._character_index.get(name)
        if path is None:
            raise KeyError(f"Unknown character fixture: {name}")
        return parse_character(self._load(path))

    def save_character(self, data: MappingLike) -> CharacterEntity:
        mapping = self._to_mapping(data)
        name = str(mapping.get("name"))
        if not name:
            raise ValueError("Character data must include a 'name'")
        path = self._character_index.get(name)
        if path is None:
            slug = self._slug(name)
            path = self.base_dir / f"character_{slug}.json"
        self._write_json(path, mapping)
        self._character_index[name] = path
        return parse_character(mapping)

    # ------------------------------------------------------------------
    # Locations

    def list_locations(self) -> list[LocationEntity]:
        return [self.get_location(name) for name in sorted(self._location_index)]

    def get_location(self, name: str) -> LocationEntity:
        path = self._location_index.get(name)
        if path is None:
            raise KeyError(f"Unknown location fixture: {name}")
        return parse_location(self._load(path))

    def save_location(self, data: MappingLike) -> LocationEntity:
        mapping = self._to_mapping(data)
        name = str(mapping.get("name"))
        if not name:
            raise ValueError("Location data must include a 'name'")
        path = self._location_index.get(name)
        if path is None:
            slug = self._slug(name)
            path = self.base_dir / f"location_{slug}.json"
        self._write_json(path, mapping)
        self._location_index[name] = path
        return parse_location(mapping)

    # ------------------------------------------------------------------
    # Organizations

    def list_organizations(self) -> list[OrganizationEntity]:
        return [self.get_organization(name) for name in sorted(self._organization_index)]

    def get_organization(self, name: str) -> OrganizationEntity:
        path = self._organization_index.get(name)
        if path is None:
            raise KeyError(f"Unknown organization fixture: {name}")
        return parse_organization(self._load(path))

    def save_organization(self, data: MappingLike) -> OrganizationEntity:
        mapping = self._to_mapping(data)
        name = str(mapping.get("name"))
        if not name:
            raise ValueError("Organization data must include a 'name'")
        path = self._organization_index.get(name)
        if path is None:
            slug = self._slug(name)
            path = self.base_dir / f"organization_{slug}.json"
        self._write_json(path, mapping)
        self._organization_index[name] = path
        return parse_organization(mapping)

    # ------------------------------------------------------------------
    # Items

    def list_items(self) -> list[ItemEntity]:
        return [self.get_item(name) for name in sorted(self._item_index)]

    def get_item(self, name: str) -> ItemEntity:
        path = self._item_index.get(name)
        if path is None:
            raise KeyError(f"Unknown item fixture: {name}")
        return parse_item(self._load(path))

    def save_item(self, data: MappingLike) -> ItemEntity:
        mapping = self._to_mapping(data)
        name = str(mapping.get("name"))
        if not name:
            raise ValueError("Item data must include a 'name'")
        path = self._item_index.get(name)
        if path is None:
            slug = self._slug(name)
            path = self.base_dir / f"item_{slug}.json"
        self._write_json(path, mapping)
        self._item_index[name] = path
        return parse_item(mapping)

    # ------------------------------------------------------------------
    # Memories

    def list_memory_logs(self) -> list[MemoryLog]:
        return [self.get_memory_log(name) for name in sorted(self._memory_index)]

    def get_memory_log(self, character_name: str, session_id: str | None = None) -> MemoryLog:
        """Load memory log with Copy-on-Write support for branched timelines.

        Args:
            character_name: Character to load memories for
            session_id: Optional session/timeline ID (defaults to current timeline from session state)

        Returns:
            MemoryLog with entries filtered by timeline branch point
        """
        # Determine target session_id
        if session_id is None and self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            session_id = timeline.get("current_session_id", "main")
        elif session_id is None:
            session_id = "main"

        # Try to load timeline-specific memory file first
        slug = self._slug(character_name)
        timeline_file = self.base_dir / f"{slug}_memories_{session_id}.json"

        # If this is main timeline or timeline file exists, load directly
        if session_id == "main" or timeline_file.exists():
            if timeline_file.exists():
                return parse_memories(self._load(timeline_file))
            # Fall back to legacy filename for main timeline
            legacy_path = self._memory_index.get(character_name)
            if legacy_path:
                return parse_memories(self._load(legacy_path))
            raise KeyError(f"Unknown memory fixture: {character_name}")

        # Copy-on-Write: load parent + branch memories
        if self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            parent_session = timeline.get("parent_session")
            branch_point = timeline.get("branch_point")

            if parent_session and branch_point is not None:
                # Load parent memories
                parent_file = self.base_dir / f"{slug}_memories_{parent_session}.json"
                if not parent_file.exists():
                    # Fall back to legacy main file
                    parent_file = self.base_dir / f"{slug}_memories.json"

                if parent_file.exists():
                    parent_data = self._load(parent_file)
                    parent_log = parse_memories(parent_data)

                    # Filter parent memories by branch point
                    filtered_entries = [
                        e for e in parent_log.entries if e.message_index <= branch_point
                    ]

                    # Try to load branch-specific memories
                    branch_entries = []
                    if timeline_file.exists():
                        branch_data = self._load(timeline_file)
                        branch_log = parse_memories(branch_data)
                        branch_entries = list(branch_log.entries)

                    # Combine filtered parent + branch entries
                    return MemoryLog(
                        character=character_name,
                        entries=filtered_entries + branch_entries,
                        session_id=session_id,
                    )

        # Fall back to main timeline
        legacy_path = self._memory_index.get(character_name)
        if legacy_path:
            return parse_memories(self._load(legacy_path))
        raise KeyError(f"Unknown memory fixture: {character_name}")

    def save_memory_log(self, data: MappingLike, session_id: str | None = None) -> MemoryLog:
        """Save memory log to timeline-specific file.

        Args:
            data: Memory log data to save
            session_id: Optional session/timeline ID (defaults to current timeline from session state)

        Returns:
            Parsed MemoryLog
        """
        mapping = self._to_mapping(data)
        character = str(mapping.get("character"))
        if not character:
            raise ValueError("Memory log must include a 'character'")

        # Determine target session_id
        if session_id is None and self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            session_id = timeline.get("current_session_id", "main")
        elif session_id is None:
            session_id = "main"

        # Add session_id to mapping if not present
        if "session_id" not in mapping:
            mapping["session_id"] = session_id

        # Determine file path
        slug = self._slug(character)
        if session_id == "main":
            # For main timeline, use legacy filename for backward compatibility
            path = self._memory_index.get(character)
            if path is None:
                path = self.base_dir / f"{slug}_memories.json"
        else:
            # For branches, use timeline-specific filename
            path = self.base_dir / f"{slug}_memories_{session_id}.json"

        self._write_json(path, mapping)
        self._memory_index[character] = path
        return parse_memories(mapping)

    def append_memory_entry(self, character_name: str, entry: Mapping[str, object]) -> MemoryLog:
        log = self.get_memory_log(character_name)
        entries = [asdict(e) for e in log.entries]
        entries.append(dict(entry))
        data = {
            "character": character_name,
            "entries": entries,
        }
        return self.save_memory_log(data)

    # ------------------------------------------------------------------
    # Relationships

    def get_relationships(self, character_name: str, session_id: str | None = None) -> Mapping[str, object]:
        """Load relationship data with Copy-on-Write support for branched timelines.

        Args:
            character_name: Character to load relationships for
            session_id: Optional session/timeline ID (defaults to current timeline from session state)

        Returns:
            Dict with structure: {"character": str, "session_id": str, "relationships": {...}}
        """
        # Determine target session_id
        if session_id is None and self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            session_id = timeline.get("current_session_id", "main")
        elif session_id is None:
            session_id = "main"

        # Try to load timeline-specific relationship file first
        slug = self._slug(character_name)
        timeline_file = self.base_dir / f"{slug}_relationships_{session_id}.json"

        # If this is main timeline or timeline file exists, load directly
        if session_id == "main":
            main_file = self.base_dir / f"{slug}_relationships.json"
            if main_file.exists():
                return self._load(main_file)
            # Return empty structure if no file exists
            return {
                "character": character_name,
                "session_id": session_id,
                "relationships": {}
            }

        if timeline_file.exists():
            return self._load(timeline_file)

        # Copy-on-Write: load parent + branch relationships
        if self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            parent_session = timeline.get("parent_session")
            branch_point = timeline.get("branch_point")

            if parent_session and branch_point is not None:
                # Load parent relationships
                parent_file = self.base_dir / f"{slug}_relationships_{parent_session}.json"
                if not parent_file.exists():
                    # Fall back to main file
                    parent_file = self.base_dir / f"{slug}_relationships.json"

                if parent_file.exists():
                    parent_data = self._load(parent_file)

                    # Filter parent relationships by branch point
                    filtered_relationships = {}
                    for target, rel_data in parent_data.get("relationships", {}).items():
                        last_message = rel_data.get("last_message_index", 0)
                        if last_message <= branch_point:
                            # Filter change history to only include changes up to branch point
                            filtered_history = [
                                h for h in rel_data.get("change_history", [])
                                if h.get("message_index", 0) <= branch_point
                            ]
                            rel_data_copy = dict(rel_data)
                            rel_data_copy["change_history"] = filtered_history
                            filtered_relationships[target] = rel_data_copy

                    # Try to load branch-specific relationships
                    branch_relationships = {}
                    if timeline_file.exists():
                        branch_data = self._load(timeline_file)
                        branch_relationships = branch_data.get("relationships", {})

                    # Merge: branch relationships override parent
                    merged_relationships = {**filtered_relationships, **branch_relationships}

                    return {
                        "character": character_name,
                        "session_id": session_id,
                        "relationships": merged_relationships
                    }

        # Fall back to main timeline or empty
        main_file = self.base_dir / f"{slug}_relationships.json"
        if main_file.exists():
            return self._load(main_file)

        return {
            "character": character_name,
            "session_id": session_id,
            "relationships": {}
        }

    def save_relationships(self, data: MappingLike, session_id: str | None = None) -> Mapping[str, object]:
        """Save relationship data to timeline-specific file.

        Args:
            data: Relationship data to save
            session_id: Optional session/timeline ID (defaults to current timeline from session state)

        Returns:
            Saved relationship data as mapping
        """
        mapping = self._to_mapping(data)
        character = str(mapping.get("character"))
        if not character:
            raise ValueError("Relationship data must include a 'character'")

        # Determine target session_id
        if session_id is None and self.session_state_service and self.rp_dir:
            timeline = self.session_state_service.get_current_timeline(self.rp_dir)
            session_id = timeline.get("current_session_id", "main")
        elif session_id is None:
            session_id = "main"

        # Add session_id to mapping if not present
        if "session_id" not in mapping:
            mapping["session_id"] = session_id

        # Determine file path
        slug = self._slug(character)
        if session_id == "main":
            path = self.base_dir / f"{slug}_relationships.json"
        else:
            path = self.base_dir / f"{slug}_relationships_{session_id}.json"

        self._write_json(path, mapping)
        return mapping

    def update_relationship_entry(
        self,
        character_name: str,
        target_character: str,
        relationship_data: Mapping[str, object]
    ) -> Mapping[str, object]:
        """Update or create a single relationship entry.

        Args:
            character_name: Character whose relationships to update
            target_character: Target character name
            relationship_data: Relationship data to set/update

        Returns:
            Updated relationship data mapping
        """
        rel_data = self.get_relationships(character_name)
        relationships = dict(rel_data.get("relationships", {}))
        relationships[target_character] = dict(relationship_data)

        data = {
            "character": character_name,
            "session_id": rel_data.get("session_id", "main"),
            "relationships": relationships
        }

        return self.save_relationships(data)
