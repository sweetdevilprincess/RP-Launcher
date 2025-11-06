from refactoring.src.domain.entities.fixtures import (
    load_character_fixture,
    load_deepseek_response_fixture,
    load_item_fixture,
    load_location_fixture,
    load_memories_fixture,
    load_organization_fixture,
    load_scene_excerpt_fixture,
)


def test_character_fixture_shape():
    data = load_character_fixture()
    assert data["type"] == "character"
    assert "personality" in data and "core_mandate" in data["personality"]
    assert data["metadata"]["related_locations"]


def test_location_fixture_shape():
    data = load_location_fixture()
    assert data["type"] == "location"
    assert "geography" in data


def test_organization_fixture_shape():
    data = load_organization_fixture()
    assert data["type"] == "organization"
    assert "structure" in data


def test_item_fixture_shape():
    data = load_item_fixture()
    assert data["type"] == "item"
    assert "attributes" in data


def test_memories_fixture_entries():
    data = load_memories_fixture()
    assert isinstance(data["entries"], list)
    entry = data["entries"][0]
    assert entry["tags"]
    assert entry["quoted_dialogue"]


def test_deepseek_fixture():
    data = load_deepseek_response_fixture()
    assert "recommended_prompts" in data


def test_scene_excerpt_fixture():
    data = load_scene_excerpt_fixture()
    assert "mentioned_entities" in data
