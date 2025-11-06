"""Tests for FixtureEntityRepository."""

import json

import pytest
from refactoring.src.domain.entities.entity_parser import (
    CharacterEntity,
    ItemEntity,
    LocationEntity,
    MemoryLog,
    OrganizationEntity,
)
from refactoring.src.domain.entities.entity_repository import FixtureEntityRepository

# Fixtures


@pytest.fixture
def temp_repo_dir(tmp_path):
    """Temporary directory for repository tests."""
    repo_dir = tmp_path / "test_fixtures"
    repo_dir.mkdir()
    return repo_dir


@pytest.fixture
def empty_repository(temp_repo_dir):
    """Empty repository for testing."""
    return FixtureEntityRepository(base_dir=temp_repo_dir)


@pytest.fixture
def populated_repository(temp_repo_dir):
    """Repository with sample fixtures."""
    # Create sample character
    char_data = {
        "name": "Alice",
        "basics": {"age": "25"},
        "appearance": {},
        "personality": {"core_mandate": "Brave knight"},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {"tags": ["alice"]},
    }
    (temp_repo_dir / "character_alice.json").write_text(json.dumps(char_data), encoding="utf-8")

    # Create sample location
    loc_data = {
        "name": "Tavern",
        "basics": {},
        "geography": {},
        "facilities": {},
        "culture": {},
        "hooks": {},
        "metadata": {},
    }
    (temp_repo_dir / "location_tavern.json").write_text(json.dumps(loc_data), encoding="utf-8")

    # Create sample organization
    org_data = {
        "name": "The Guild",
        "basics": {},
        "structure": {},
        "resources": {},
        "relations": {},
        "operations": {},
        "metadata": {},
    }
    (temp_repo_dir / "organization_the_guild.json").write_text(
        json.dumps(org_data), encoding="utf-8"
    )

    # Create sample item
    item_data = {
        "name": "Magic Sword",
        "basics": {},
        "attributes": {},
        "usage": {},
        "metadata": {},
    }
    (temp_repo_dir / "item_magic_sword.json").write_text(json.dumps(item_data), encoding="utf-8")

    # Create sample memory log
    memory_data = {
        "character": "Alice",
        "entries": [
            {
                "id": "mem_001",
                "summary": "Test memory",
                "details": "Details",
                "tags": [],
                "quoted_dialogue": [],
                "relationships": {},
                "location": "",
                "chapter": "",
            }
        ],
    }
    (temp_repo_dir / "alice_memories.json").write_text(json.dumps(memory_data), encoding="utf-8")

    return FixtureEntityRepository(base_dir=temp_repo_dir)


# Tests for initialization


def test_repository_creates_base_dir(tmp_path):
    """Test that repository creates base directory if it doesn't exist."""
    repo_dir = tmp_path / "new_fixtures"
    assert not repo_dir.exists()

    repo = FixtureEntityRepository(base_dir=repo_dir)

    assert repo_dir.exists()
    assert repo.base_dir == repo_dir


def test_repository_indexes_existing_fixtures(populated_repository):
    """Test that repository indexes existing fixtures on init."""
    assert len(populated_repository._character_index) == 1
    assert len(populated_repository._location_index) == 1
    assert len(populated_repository._organization_index) == 1
    assert len(populated_repository._item_index) == 1
    assert len(populated_repository._memory_index) == 1

    assert "Alice" in populated_repository._character_index
    assert "Tavern" in populated_repository._location_index
    assert "The Guild" in populated_repository._organization_index
    assert "Magic Sword" in populated_repository._item_index
    assert "Alice" in populated_repository._memory_index


# Tests for Character operations


def test_list_characters_empty(empty_repository):
    """Test listing characters from empty repository."""
    characters = empty_repository.list_characters()
    assert characters == []


def test_list_characters_populated(populated_repository):
    """Test listing characters from populated repository."""
    characters = populated_repository.list_characters()

    assert len(characters) == 1
    assert characters[0].name == "Alice"
    assert isinstance(characters[0], CharacterEntity)


def test_get_character_success(populated_repository):
    """Test getting a character by name."""
    character = populated_repository.get_character("Alice")

    assert character.name == "Alice"
    assert character.basics["age"] == "25"
    assert character.core_mandate == "Brave knight"


def test_get_character_not_found(empty_repository):
    """Test error when character not found."""
    with pytest.raises(KeyError, match="Unknown character fixture: Unknown"):
        empty_repository.get_character("Unknown")


def test_save_character_new(empty_repository):
    """Test saving a new character."""
    char_data = {
        "name": "Bob",
        "basics": {},
        "appearance": {},
        "personality": {},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    result = empty_repository.save_character(char_data)

    assert result.name == "Bob"
    assert "Bob" in empty_repository._character_index

    # Verify file was created
    file_path = empty_repository.base_dir / "character_bob.json"
    assert file_path.exists()

    # Verify file content
    with file_path.open() as f:
        saved_data = json.load(f)
    assert saved_data["name"] == "Bob"


def test_save_character_update_existing(populated_repository):
    """Test updating an existing character."""
    # Get existing character
    original = populated_repository.get_character("Alice")
    assert original.basics["age"] == "25"

    # Update character
    updated_data = {
        "name": "Alice",
        "basics": {"age": "26"},  # Changed age
        "appearance": {},
        "personality": {"core_mandate": "Brave knight"},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {"tags": ["alice", "updated"]},
    }

    result = populated_repository.save_character(updated_data)

    assert result.name == "Alice"
    assert result.basics["age"] == "26"
    assert result.metadata["tags"] == ["alice", "updated"]

    # Verify updated in repository
    reloaded = populated_repository.get_character("Alice")
    assert reloaded.basics["age"] == "26"


def test_save_character_from_dataclass(empty_repository):
    """Test saving a CharacterEntity dataclass."""
    character = CharacterEntity(
        name="Charlie",
        basics={"age": "30"},
        appearance={},
        personality={},
        preferences={},
        abilities={},
        background={},
        metadata={},
    )

    result = empty_repository.save_character(character)

    assert result.name == "Charlie"
    assert "Charlie" in empty_repository._character_index


def test_save_character_missing_name(empty_repository):
    """Test error when saving character without name."""
    char_data = {
        # Missing "name"
        "basics": {},
        "appearance": {},
        "personality": {},
        "preferences": {},
        "abilities": {},
        "background": {},
        "metadata": {},
    }

    # Parser will catch missing "name" before repository validation
    with pytest.raises(ValueError, match="Character entity missing keys: name"):
        empty_repository.save_character(char_data)


# Tests for Location operations


def test_list_locations(populated_repository):
    """Test listing locations."""
    locations = populated_repository.list_locations()

    assert len(locations) == 1
    assert locations[0].name == "Tavern"
    assert isinstance(locations[0], LocationEntity)


def test_get_location(populated_repository):
    """Test getting a location by name."""
    location = populated_repository.get_location("Tavern")
    assert location.name == "Tavern"


def test_get_location_not_found(empty_repository):
    """Test error when location not found."""
    with pytest.raises(KeyError, match="Unknown location fixture"):
        empty_repository.get_location("Unknown")


def test_save_location(empty_repository):
    """Test saving a location."""
    loc_data = {
        "name": "Castle",
        "basics": {"type": "fortress"},
        "geography": {},
        "facilities": {},
        "culture": {},
        "hooks": {},
        "metadata": {},
    }

    result = empty_repository.save_location(loc_data)

    assert result.name == "Castle"
    assert result.basics["type"] == "fortress"
    assert "Castle" in empty_repository._location_index


# Tests for Organization operations


def test_list_organizations(populated_repository):
    """Test listing organizations."""
    organizations = populated_repository.list_organizations()

    assert len(organizations) == 1
    assert organizations[0].name == "The Guild"
    assert isinstance(organizations[0], OrganizationEntity)


def test_get_organization(populated_repository):
    """Test getting an organization by name."""
    org = populated_repository.get_organization("The Guild")
    assert org.name == "The Guild"


def test_save_organization(empty_repository):
    """Test saving an organization."""
    org_data = {
        "name": "Merchants Alliance",
        "basics": {},
        "structure": {},
        "resources": {},
        "relations": {},
        "operations": {},
        "metadata": {},
    }

    result = empty_repository.save_organization(org_data)

    assert result.name == "Merchants Alliance"
    assert "Merchants Alliance" in empty_repository._organization_index


# Tests for Item operations


def test_list_items(populated_repository):
    """Test listing items."""
    items = populated_repository.list_items()

    assert len(items) == 1
    assert items[0].name == "Magic Sword"
    assert isinstance(items[0], ItemEntity)


def test_get_item(populated_repository):
    """Test getting an item by name."""
    item = populated_repository.get_item("Magic Sword")
    assert item.name == "Magic Sword"


def test_save_item(empty_repository):
    """Test saving an item."""
    item_data = {
        "name": "Healing Potion",
        "basics": {"type": "consumable"},
        "attributes": {},
        "usage": {},
        "metadata": {},
    }

    result = empty_repository.save_item(item_data)

    assert result.name == "Healing Potion"
    assert result.basics["type"] == "consumable"
    assert "Healing Potion" in empty_repository._item_index


# Tests for Memory operations


def test_list_memory_logs(populated_repository):
    """Test listing memory logs."""
    logs = populated_repository.list_memory_logs()

    assert len(logs) == 1
    assert logs[0].character == "Alice"
    assert isinstance(logs[0], MemoryLog)


def test_get_memory_log(populated_repository):
    """Test getting a memory log."""
    log = populated_repository.get_memory_log("Alice")

    assert log.character == "Alice"
    assert len(log.entries) == 1
    assert log.entries[0].id == "mem_001"


def test_save_memory_log(empty_repository):
    """Test saving a memory log."""
    memory_data = {
        "character": "Bob",
        "entries": [
            {
                "id": "mem_001",
                "summary": "Test",
                "details": "Details",
                "tags": [],
                "quoted_dialogue": [],
                "relationships": {},
                "location": "",
                "chapter": "",
            }
        ],
    }

    result = empty_repository.save_memory_log(memory_data)

    assert result.character == "Bob"
    assert len(result.entries) == 1
    assert "Bob" in empty_repository._memory_index


def test_append_memory_entry(populated_repository):
    """Test appending a new entry to existing memory log."""
    # Get original log
    original_log = populated_repository.get_memory_log("Alice")
    assert len(original_log.entries) == 1

    # Append new entry
    new_entry = {
        "id": "mem_002",
        "summary": "New memory",
        "details": "New details",
        "tags": ["new"],
        "quoted_dialogue": [],
        "relationships": {},
        "location": "Tavern",
        "chapter": "Chapter 2",
    }

    result = populated_repository.append_memory_entry("Alice", new_entry)

    assert result.character == "Alice"
    assert len(result.entries) == 2
    assert result.entries[0].id == "mem_001"
    assert result.entries[1].id == "mem_002"
    assert result.entries[1].summary == "New memory"

    # Verify persisted
    reloaded = populated_repository.get_memory_log("Alice")
    assert len(reloaded.entries) == 2


# Tests for helper methods


def test_slug_generation(empty_repository):
    """Test slug generation from entity names."""
    assert empty_repository._slug("Alice") == "alice"
    assert empty_repository._slug("The Great Wizard") == "the_great_wizard"
    assert empty_repository._slug("Bob's Tavern") == "bob_s_tavern"
    assert empty_repository._slug("123 Main St.") == "123_main_st"
    assert empty_repository._slug("!!!") == "entity"  # Fallback for all special chars


def test_to_mapping_from_dict(empty_repository):
    """Test converting dict to mapping."""
    data = {"name": "Test", "value": 123}
    result = empty_repository._to_mapping(data)

    assert result == data


def test_to_mapping_from_dataclass(empty_repository):
    """Test converting dataclass to mapping."""
    character = CharacterEntity(
        name="Test",
        basics={},
        appearance={},
        personality={},
        preferences={},
        abilities={},
        background={},
        metadata={},
    )

    result = empty_repository._to_mapping(character)

    assert isinstance(result, dict)
    assert result["name"] == "Test"


def test_to_mapping_invalid_type(empty_repository):
    """Test error for invalid data type."""
    with pytest.raises(TypeError, match="Entity data must be a mapping or dataclass"):
        empty_repository._to_mapping("invalid")


# Integration tests


def test_save_and_load_roundtrip(empty_repository):
    """Test saving and loading entities maintains data integrity."""
    # Save character
    char_data = {
        "name": "Alice",
        "basics": {"age": "25", "gender": "female"},
        "appearance": {"height": "5'8\""},
        "personality": {"core_mandate": "Brave knight", "traits": ["brave"]},
        "preferences": {"likes": ["honor"]},
        "abilities": {"combat": "expert"},
        "background": {"origin": "Valor"},
        "metadata": {"tags": ["alice", "warrior"]},
    }

    saved = empty_repository.save_character(char_data)
    loaded = empty_repository.get_character("Alice")

    assert saved.name == loaded.name
    assert saved.basics == loaded.basics
    assert saved.appearance == loaded.appearance
    assert saved.personality == loaded.personality
    assert saved.metadata == loaded.metadata


def test_multiple_entities_same_type(empty_repository):
    """Test handling multiple entities of the same type."""
    # Create multiple characters
    for name in ["Alice", "Bob", "Charlie"]:
        char_data = {
            "name": name,
            "basics": {},
            "appearance": {},
            "personality": {},
            "preferences": {},
            "abilities": {},
            "background": {},
            "metadata": {},
        }
        empty_repository.save_character(char_data)

    characters = empty_repository.list_characters()

    assert len(characters) == 3
    assert sorted([c.name for c in characters]) == ["Alice", "Bob", "Charlie"]


def test_repository_isolation(temp_repo_dir):
    """Test that separate repositories don't interfere."""
    repo1_dir = temp_repo_dir / "repo1"
    repo2_dir = temp_repo_dir / "repo2"

    repo1 = FixtureEntityRepository(base_dir=repo1_dir)
    repo2 = FixtureEntityRepository(base_dir=repo2_dir)

    # Save to repo1
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
    repo1.save_character(char_data)

    # Verify repo1 has it, repo2 doesn't
    assert len(repo1.list_characters()) == 1
    assert len(repo2.list_characters()) == 0

    with pytest.raises(KeyError):
        repo2.get_character("Alice")
