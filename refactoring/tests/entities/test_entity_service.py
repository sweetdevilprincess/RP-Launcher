from dataclasses import replace
from pathlib import Path

from refactoring.src.domain.entities.entity_repository import FixtureEntityRepository
from refactoring.src.domain.entities.entity_service import EntityService
from refactoring.src.domain.entities.models import EntityType


def copy_fixtures(target: Path) -> Path:
    source = FixtureEntityRepository().base_dir
    for path in source.glob("*.json"):
        destination = target / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def make_service(tmp_path=None):
    if tmp_path is not None:
        base = copy_fixtures(tmp_path)
        repo = FixtureEntityRepository(base_dir=base)
    else:
        repo = FixtureEntityRepository()
    return EntityService(repository=repo)


def test_stats_counts_entities():
    service = make_service()
    stats = service.stats()
    assert stats.total_characters >= 1
    assert stats.total_locations >= 1
    assert stats.total_organizations >= 1


def test_detect_mentions_uses_tags():
    service = make_service()
    text = "The pilot hummed a tune while the crew prepped the Celestia Observatory dock."
    mentions = service.detect_mentions(text)
    assert "Aurora Lys" in mentions
    assert "Celestia Observatory" in mentions


def test_save_character_updates(tmp_path):
    service = make_service(tmp_path)
    character = service.get_character("Aurora Lys")
    assert character is not None
    modified = replace(
        character, personality={**character.personality, "core_mandate": "Protect the crew"}
    )
    service.save_character(modified)
    reloaded = service.get_character("Aurora Lys")
    assert reloaded is not None
    assert reloaded.personality["core_mandate"] == "Protect the crew"


def test_append_memory_entry(tmp_path):
    service = make_service(tmp_path)
    service.append_memory_entry(
        "Aurora Lys",
        {
            "id": "test_entry",
            "summary": "Aurora recorded a new lullaby",
            "details": "Late-night rehearsal in the observation lounge",
            "tags": ["Aurora_Lys", "music", "Ch_04"],
            "quoted_dialogue": [],
            "relationships": {},
            "location": "Observatory Lounge",
            "chapter": "Chapter 4",
            "timestamp": "2199-07-01T00:00:00Z",
        },
    )
    log = service.list_memory_logs()[0]
    assert any(entry.id == "test_entry" for entry in log.entries)


def test_generate_entity_card_template():
    service = make_service()
    markup = service.generate_entity_card_template("Aurora Lys", EntityType.CHARACTER)
    assert "Aurora Lys" in markup


def test_generate_preferences_template():
    service = make_service()
    data = service.generate_character_preferences_template("Aurora Lys")
    assert data["character_name"] == "Aurora Lys"
    assert "likes" in data["preferences"]
