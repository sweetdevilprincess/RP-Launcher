from refactoring.src.domain.entities.entity_parser import (
    parse_character,
    parse_item,
    parse_location,
    parse_memories,
    parse_organization,
)
from refactoring.src.domain.entities.fixtures import (
    load_character_fixture,
    load_item_fixture,
    load_location_fixture,
    load_memories_fixture,
    load_organization_fixture,
)


def test_parse_character_core_mandate():
    entity = parse_character(load_character_fixture())
    assert entity.core_mandate
    assert "Inspire hope" in entity.core_mandate


def test_parse_location_sections():
    entity = parse_location(load_location_fixture())
    assert entity.geography["notable_features"]


def test_parse_organization_relations():
    entity = parse_organization(load_organization_fixture())
    assert "allies" in entity.relations


def test_parse_item_attributes():
    entity = parse_item(load_item_fixture())
    assert "function" in entity.attributes


def test_parse_memories_entries():
    log = parse_memories(load_memories_fixture())
    assert log.entries
    assert log.entries[0].tags
