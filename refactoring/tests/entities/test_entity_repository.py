from dataclasses import asdict
from pathlib import Path

from refactoring.src.domain.entities.entity_repository import FixtureEntityRepository

FIXTURE_SOURCE = Path(__file__).resolve().parent / "fixtures"


def _copy_fixtures(tmp_path):
    for path in FIXTURE_SOURCE.glob("*.json"):
        target = tmp_path / path.name
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def test_repository_get_character():
    repo = FixtureEntityRepository()
    character = repo.get_character("Aurora Lys")
    assert character.name == "Aurora Lys"
    assert character.metadata["related_locations"]


def test_repository_list_locations():
    repo = FixtureEntityRepository()
    locations = repo.list_locations()
    assert locations
    assert any(loc.name == "Celestia Observatory" for loc in locations)


def test_repository_memory_log():
    repo = FixtureEntityRepository()
    log = repo.get_memory_log("Aurora Lys")
    assert log.entries
    assert log.entries[0].summary


def test_save_character_updates(tmp_path):
    base = _copy_fixtures(tmp_path)
    repo = FixtureEntityRepository(base_dir=base)
    character = repo.get_character("Aurora Lys")
    data = asdict(character)
    data["personality"]["core_mandate"] = "Protect the Dawnrise at all costs"
    repo.save_character(data)
    reloaded = repo.get_character("Aurora Lys")
    assert reloaded.personality["core_mandate"] == "Protect the Dawnrise at all costs"


def test_save_new_item_creates_file(tmp_path):
    base = _copy_fixtures(tmp_path)
    repo = FixtureEntityRepository(base_dir=base)
    new_item = {
        "name": "Harmonic Compass",
        "type": "item",
        "basics": {
            "category": "Tool",
            "origin": "Celestia Observatory",
            "rarity": "Uncommon",
            "owner": "Aurora Lys",
        },
        "attributes": {
            "function": "Points toward stable harmonic currents",
            "components": ["Resonance gyroscope"],
            "limitations": ["Fails near strong magnetic storms"],
        },
        "usage": {"activation": "Requires calibration song", "side_effects": ["Temporary vertigo"]},
        "metadata": {
            "related_characters": ["Aurora Lys"],
            "related_locations": ["Celestia Observatory"],
            "related_organizations": ["Elysian Alliance"],
            "tags": ["navigation", "tool"],
        },
    }
    repo.save_item(new_item)
    reloaded = repo.get_item("Harmonic Compass")
    assert reloaded.attributes["function"] == "Points toward stable harmonic currents"


def test_append_memory_entry(tmp_path):
    base = _copy_fixtures(tmp_path)
    repo = FixtureEntityRepository(base_dir=base)
    repo.append_memory_entry(
        "Aurora Lys",
        {
            "id": "aurora_mem_test",
            "summary": "Aurora recorded a new lullaby for the crew.",
            "details": "Late at night in the observation lounge, Aurora improvised a calming melody.",
            "tags": ["Aurora_Lys", "music", "crew", "Ch_03"],
            "quoted_dialogue": ['"Sleep easy—I\'ll keep the storms at bay."'],
            "relationships": {"Crew": "comforted"},
            "location": "Observation lounge",
            "chapter": "Chapter 3",
            "timestamp": "2199-06-12T02:03:00Z",
        },
    )
    log = repo.get_memory_log("Aurora Lys")
    assert any(entry.summary.startswith("Aurora recorded") for entry in log.entries)
