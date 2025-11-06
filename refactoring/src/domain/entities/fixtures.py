"""Utilities for loading entity test fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "entities" / "fixtures"


@dataclass(frozen=True)
class FixtureLoader:
    """Loads JSON fixtures from the refactoring test directory."""

    base_dir: Path = FIXTURE_DIR

    def load_json(self, name: str) -> dict[str, Any]:
        path = self.base_dir / name
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


def load_character_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("character_aurora.json")


def load_location_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("location_celestia.json")


def load_organization_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("organization_elysian_alliance.json")


def load_item_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("item_harmonic_resonator.json")


def load_memories_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("Aurora_Lys_memories.json")


def load_deepseek_response_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("deepseek_preference_response.json")


def load_scene_excerpt_fixture() -> dict[str, Any]:
    return FixtureLoader().load_json("scene_excerpt.json")
