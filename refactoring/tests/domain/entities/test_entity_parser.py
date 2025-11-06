"""Tests for entity parsing functions."""

import pytest
from refactoring.src.domain.entities.entity_parser import (
    CharacterEntity,
    ItemEntity,
    LocationEntity,
    MemoryEntry,
    MemoryLog,
    OrganizationEntity,
    parse_character,
    parse_item,
    parse_location,
    parse_memories,
    parse_organization,
)

# Fixtures


@pytest.fixture
def valid_character_data():
    """Valid character data for parsing."""
    return {
        "name": "Alice",
        "basics": {"age": "25", "gender": "female", "species": "human"},
        "appearance": {"height": "5'8\"", "build": "athletic", "hair": "blonde"},
        "personality": {
            "core_mandate": "Brave knight who values honor above all",
            "traits": ["brave", "honorable", "loyal"],
        },
        "preferences": {"likes": [], "dislikes": [], "hates": []},
        "abilities": {"combat": "expert swordsman", "magic": "none"},
        "background": {"origin": "Kingdom of Valor", "history": "Noble family"},
        "metadata": {"tags": ["alice", "warrior"], "created": "2025-01-01"},
    }


@pytest.fixture
def valid_location_data():
    """Valid location data for parsing."""
    return {
        "name": "Tavern of the Lost",
        "basics": {"type": "tavern", "size": "medium"},
        "geography": {"region": "North District", "terrain": "urban"},
        "facilities": {"rooms": 12, "common_area": "large"},
        "culture": {"atmosphere": "rowdy", "clientele": "adventurers"},
        "hooks": {"rumors": ["dragon sighting", "treasure map"]},
        "metadata": {"tags": ["tavern", "north"], "created": "2025-01-01"},
    }


@pytest.fixture
def valid_organization_data():
    """Valid organization data for parsing."""
    return {
        "name": "The Silver Order",
        "basics": {"type": "guild", "size": "large", "alignment": "good"},
        "structure": {"hierarchy": "council", "leader": "Grand Master"},
        "resources": {"wealth": "high", "territory": ["castle", "mines"]},
        "relations": {"allies": ["Kingdom"], "enemies": ["Dark Cult"]},
        "operations": {"primary": "monster hunting", "secondary": "trade"},
        "metadata": {"tags": ["guild", "knights"], "created": "2025-01-01"},
    }


@pytest.fixture
def valid_item_data():
    """Valid item data for parsing."""
    return {
        "name": "Sword of Light",
        "basics": {"type": "weapon", "rarity": "legendary"},
        "attributes": {"damage": "+10", "enchantment": "holy"},
        "usage": {"wielder": "Alice", "condition": "pristine"},
        "metadata": {"tags": ["sword", "legendary"], "created": "2025-01-01"},
    }


@pytest.fixture
def valid_memory_data():
    """Valid memory log data for parsing."""
    return {
        "character": "Alice",
        "entries": [
            {
                "id": "mem_001",
                "summary": "First meeting with Bob",
                "details": "Met Bob at the tavern. He offered a quest.",
                "tags": ["bob", "quest"],
                "quoted_dialogue": ["Hello, I'm Bob", "Can you help me?"],
                "relationships": {"bob": "friendly"},
                "location": "Tavern of the Lost",
                "chapter": "Chapter 1",
                "timestamp": "2025-01-01T12:00:00",
            },
            {
                "id": "mem_002",
                "summary": "Battle with dragon",
                "details": "Fought a dragon in the mountains.",
                "tags": ["dragon", "combat"],
                "quoted_dialogue": ["You shall not pass!"],
                "relationships": {},
                "location": "Dragon's Peak",
                "chapter": "Chapter 2",
                "timestamp": "2025-01-02T15:30:00",
            },
        ],
    }


# Tests for parse_character


def test_parse_character_success(valid_character_data):
    """Test successful character parsing."""
    result = parse_character(valid_character_data)

    assert isinstance(result, CharacterEntity)
    assert result.name == "Alice"
    assert result.basics["age"] == "25"
    assert result.appearance["height"] == "5'8\""
    assert result.personality["core_mandate"] == "Brave knight who values honor above all"
    assert result.metadata["tags"] == ["alice", "warrior"]


def test_parse_character_core_mandate_property(valid_character_data):
    """Test that core_mandate property works correctly."""
    result = parse_character(valid_character_data)

    assert result.core_mandate == "Brave knight who values honor above all"


def test_parse_character_missing_core_mandate():
    """Test character parsing when core_mandate is missing."""
    data = {
        "name": "Bob",
        "basics": {},
        "appearance": {},
        "personality": {"traits": ["friendly"]},  # No core_mandate
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    result = parse_character(data)
    assert result.core_mandate is None


def test_parse_character_missing_required_key():
    """Test error when required key is missing."""
    data = {
        "name": "Alice",
        "basics": {},
        "appearance": {},
        # Missing "personality"
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    with pytest.raises(ValueError, match="Character entity missing keys: personality"):
        parse_character(data)


def test_parse_character_multiple_missing_keys():
    """Test error message when multiple keys are missing."""
    data = {
        "name": "Alice",
        # Missing several keys
    }

    with pytest.raises(ValueError, match="Character entity missing keys"):
        parse_character(data)


def test_parse_character_empty_sections():
    """Test parsing character with empty sections."""
    data = {
        "name": "MinimalChar",
        "basics": {},
        "appearance": {},
        "personality": {},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    result = parse_character(data)
    assert result.name == "MinimalChar"
    assert result.basics == {}
    assert result.metadata == {}


# Tests for parse_location


def test_parse_location_success(valid_location_data):
    """Test successful location parsing."""
    result = parse_location(valid_location_data)

    assert isinstance(result, LocationEntity)
    assert result.name == "Tavern of the Lost"
    assert result.basics["type"] == "tavern"
    assert result.geography["region"] == "North District"
    assert result.facilities["rooms"] == 12
    assert result.culture["atmosphere"] == "rowdy"
    assert result.hooks["rumors"] == ["dragon sighting", "treasure map"]


def test_parse_location_missing_key():
    """Test error when location is missing a required key."""
    data = {
        "name": "Incomplete Location",
        "basics": {},
        "geography": {},
        # Missing "facilities"
        "culture": {},
        "hooks": {},
        "metadata": {},
    }

    with pytest.raises(ValueError, match="Location entity missing keys: facilities"):
        parse_location(data)


# Tests for parse_organization


def test_parse_organization_success(valid_organization_data):
    """Test successful organization parsing."""
    result = parse_organization(valid_organization_data)

    assert isinstance(result, OrganizationEntity)
    assert result.name == "The Silver Order"
    assert result.basics["type"] == "guild"
    assert result.structure["hierarchy"] == "council"
    assert result.resources["wealth"] == "high"
    assert result.relations["allies"] == ["Kingdom"]
    assert result.operations["primary"] == "monster hunting"


def test_parse_organization_missing_key():
    """Test error when organization is missing a required key."""
    data = {
        "name": "Incomplete Org",
        "basics": {},
        "structure": {},
        "resources": {},
        # Missing "relations"
        "operations": {},
        "metadata": {},
    }

    with pytest.raises(ValueError, match="Organization entity missing keys: relations"):
        parse_organization(data)


# Tests for parse_item


def test_parse_item_success(valid_item_data):
    """Test successful item parsing."""
    result = parse_item(valid_item_data)

    assert isinstance(result, ItemEntity)
    assert result.name == "Sword of Light"
    assert result.basics["type"] == "weapon"
    assert result.attributes["damage"] == "+10"
    assert result.usage["wielder"] == "Alice"


def test_parse_item_missing_key():
    """Test error when item is missing a required key."""
    data = {
        "name": "Incomplete Item",
        "basics": {},
        # Missing "attributes"
        "usage": {},
        "metadata": {},
    }

    with pytest.raises(ValueError, match="Item entity missing keys: attributes"):
        parse_item(data)


# Tests for parse_memories


def test_parse_memories_success(valid_memory_data):
    """Test successful memory log parsing."""
    result = parse_memories(valid_memory_data)

    assert isinstance(result, MemoryLog)
    assert result.character == "Alice"
    assert len(result.entries) == 2

    # Check first entry
    entry1 = result.entries[0]
    assert isinstance(entry1, MemoryEntry)
    assert entry1.id == "mem_001"
    assert entry1.summary == "First meeting with Bob"
    assert entry1.details == "Met Bob at the tavern. He offered a quest."
    assert entry1.tags == ["bob", "quest"]
    assert entry1.quoted_dialogue == ["Hello, I'm Bob", "Can you help me?"]
    assert entry1.relationships == {"bob": "friendly"}
    assert entry1.location == "Tavern of the Lost"
    assert entry1.chapter == "Chapter 1"
    assert entry1.timestamp == "2025-01-01T12:00:00"

    # Check second entry
    entry2 = result.entries[1]
    assert entry2.id == "mem_002"
    assert entry2.summary == "Battle with dragon"


def test_parse_memories_empty_entries():
    """Test parsing memory log with no entries."""
    data = {"character": "Bob", "entries": []}

    result = parse_memories(data)
    assert result.character == "Bob"
    assert result.entries == []


def test_parse_memories_missing_character():
    """Test error when character field is missing."""
    data = {
        # Missing "character"
        "entries": []
    }

    with pytest.raises(ValueError, match="Memory log missing keys: character"):
        parse_memories(data)


def test_parse_memories_entry_missing_required_field():
    """Test error when memory entry is missing a required field."""
    data = {
        "character": "Alice",
        "entries": [
            {
                "id": "mem_001",
                "summary": "Test",
                # Missing "details", "tags", etc.
            }
        ],
    }

    with pytest.raises(ValueError, match="Memory entry missing keys"):
        parse_memories(data)


def test_parse_memories_optional_fields():
    """Test memory entry with minimal required fields."""
    data = {
        "character": "Alice",
        "entries": [
            {
                "id": "mem_001",
                "summary": "Test memory",
                "details": "Some details",
                "tags": [],
                "quoted_dialogue": [],
                "relationships": {},
                "location": "",
                "chapter": "",
                # "timestamp" is optional
            }
        ],
    }

    result = parse_memories(data)
    entry = result.entries[0]
    assert entry.timestamp is None
    assert entry.tags == []
    assert entry.quoted_dialogue == []


def test_parse_memories_entry_type_conversion():
    """Test that entry fields are properly type-converted."""
    data = {
        "character": "Bob",
        "entries": [
            {
                "id": 123,  # Will be converted to str
                "summary": "Test Summary",
                "details": "Test Details",
                "tags": ["tag1", "tag2"],
                "quoted_dialogue": ["Quote 1", "Quote 2"],
                "relationships": {"alice": "friend"},
                "location": "Test Location",
                "chapter": "Test Chapter",
                "timestamp": "2025-01-01T12:00:00",
            }
        ],
    }

    result = parse_memories(data)
    entry = result.entries[0]
    assert entry.id == "123"  # Converted to string
    assert entry.tags == ["tag1", "tag2"]
    assert entry.quoted_dialogue == ["Quote 1", "Quote 2"]
    assert entry.relationships == {"alice": "friend"}
    assert entry.location == "Test Location"
    assert entry.chapter == "Test Chapter"


# Tests for _require_keys edge cases


def test_parse_character_extra_keys_allowed(valid_character_data):
    """Test that extra keys are allowed and don't cause errors."""
    valid_character_data["extra_field"] = "extra_value"
    valid_character_data["another_extra"] = {"nested": "data"}

    result = parse_character(valid_character_data)
    assert result.name == "Alice"


def test_parse_location_extra_keys_allowed(valid_location_data):
    """Test that extra keys are allowed for locations."""
    valid_location_data["custom_data"] = "some value"

    result = parse_location(valid_location_data)
    assert result.name == "Tavern of the Lost"


# Integration tests


def test_parse_multiple_entities():
    """Test parsing multiple different entity types."""
    char_data = {
        "name": "Alice",
        "basics": {},
        "appearance": {},
        "personality": {},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    loc_data = {
        "name": "Castle",
        "basics": {},
        "geography": {},
        "facilities": {},
        "culture": {},
        "hooks": {},
        "metadata": {},
    }

    char = parse_character(char_data)
    loc = parse_location(loc_data)

    assert char.name == "Alice"
    assert loc.name == "Castle"
    assert isinstance(char, CharacterEntity)
    assert isinstance(loc, LocationEntity)


def test_frozen_dataclasses():
    """Test that parsed entities are frozen (immutable)."""
    data = {
        "name": "Alice",
        "basics": {},
        "appearance": {},
        "personality": {},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    result = parse_character(data)

    # Should not be able to modify frozen dataclass
    with pytest.raises(AttributeError):
        result.name = "Bob"  # type: ignore
