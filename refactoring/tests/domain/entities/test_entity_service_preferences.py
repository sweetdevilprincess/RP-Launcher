"""Tests for EntityService preference generation integration."""

import pytest
from refactoring.src.domain.entities.entity_parser import CharacterEntity
from refactoring.src.domain.entities.entity_service import EntityService
from refactoring.src.domain.entities.models import EntityCard
from refactoring.src.domain.entities.preference_generator import PreferenceResult
from refactoring.src.infrastructure.llm.base import (
    LLMAuthError,
    LLMError,
)
from refactoring.src.shared.models import EntityType

# Mock components


class MockPreferenceGenerator:
    """Mock preference generator for testing."""

    def __init__(self, result: PreferenceResult = None, error: Exception = None):
        self._result = result
        self._error = error
        self.generate_calls = []

    def generate(self, entity: EntityCard) -> PreferenceResult:
        self.generate_calls.append(entity)
        if self._error:
            raise self._error
        return self._result


class MockRepository:
    """Mock repository that returns test characters."""

    def __init__(self, characters=None):
        self._characters = characters or {}

    def list_characters(self):
        return list(self._characters.values())

    def get_character(self, name: str):
        return self._characters.get(name)

    def list_locations(self):
        return []

    def list_organizations(self):
        return []

    def list_items(self):
        return []

    def list_memory_logs(self):
        return []


# Fixtures


@pytest.fixture
def sample_character():
    """Sample character entity."""
    return CharacterEntity(
        name="Alice",
        basics={"age": "25", "gender": "female"},
        appearance={"height": "5'8\"", "build": "athletic"},
        personality={
            "core_mandate": "Brave and honorable knight. Values truth and justice.",
            "traits": ["brave", "honorable", "loyal"],
        },
        preferences={},
        abilities={"combat": "expert swordsman"},
        background={"origin": "Kingdom of Valor"},
        metadata={"tags": ["alice", "warrior"]},
    )


@pytest.fixture
def sample_preferences_result():
    """Sample preference result."""
    return PreferenceResult(
        character_name="Alice",
        preferences={
            "likes": [
                {"trait": "honesty", "points": 10, "reason": "values truth"},
                {"trait": "courage", "points": 12, "reason": "respects bravery"},
            ],
            "dislikes": [{"trait": "lying", "points": -8, "reason": "opposes dishonesty"}],
            "hates": [{"trait": "cowardice", "points": -25, "reason": "dealbreaker for honor"}],
        },
        source="test_provider",
    )


# Tests


def test_generate_character_preferences_success(sample_character, sample_preferences_result):
    """Test successful preference generation through EntityService."""
    mock_repo = MockRepository(characters={"Alice": sample_character})
    mock_generator = MockPreferenceGenerator(result=sample_preferences_result)

    service = EntityService(repository=mock_repo, preference_generator=mock_generator)

    result = service.generate_character_preferences("Alice")

    assert result == sample_preferences_result
    assert result.character_name == "Alice"
    assert len(result.preferences["likes"]) == 2
    assert len(mock_generator.generate_calls) == 1

    # Verify the entity card passed to generator
    entity_card = mock_generator.generate_calls[0]
    assert entity_card.name == "Alice"
    assert entity_card.entity_type == EntityType.CHARACTER
    assert entity_card.personality_core == "Brave and honorable knight. Values truth and justice."


def test_generate_character_preferences_no_generator():
    """Test error when preference generator not configured."""
    mock_repo = MockRepository()
    service = EntityService(repository=mock_repo, preference_generator=None)

    with pytest.raises(ValueError, match="Preference generator not configured"):
        service.generate_character_preferences("Alice")


def test_generate_character_preferences_character_not_found(sample_preferences_result):
    """Test error when character doesn't exist."""
    mock_repo = MockRepository(characters={})  # Empty repository
    mock_generator = MockPreferenceGenerator(result=sample_preferences_result)

    service = EntityService(repository=mock_repo, preference_generator=mock_generator)

    with pytest.raises(ValueError, match="Character 'Unknown' not found"):
        service.generate_character_preferences("Unknown")


def test_generate_character_preferences_llm_auth_error(sample_character):
    """Test handling of LLM authentication errors."""
    mock_repo = MockRepository(characters={"Alice": sample_character})
    mock_generator = MockPreferenceGenerator(error=LLMAuthError("Invalid API key"))

    service = EntityService(repository=mock_repo, preference_generator=mock_generator)

    with pytest.raises(LLMAuthError, match="Invalid API key"):
        service.generate_character_preferences("Alice")


def test_generate_character_preferences_llm_error(sample_character):
    """Test handling of general LLM errors."""
    mock_repo = MockRepository(characters={"Alice": sample_character})
    mock_generator = MockPreferenceGenerator(error=LLMError("API timeout"))

    service = EntityService(repository=mock_repo, preference_generator=mock_generator)

    with pytest.raises(LLMError, match="API timeout"):
        service.generate_character_preferences("Alice")


def test_generate_character_preferences_missing_personality_core(sample_character):
    """Test handling when character has no personality core."""
    # Character without personality_core (no core_mandate and empty personality)
    character_no_core = CharacterEntity(
        name="Bob",
        basics={},
        appearance={},
        personality={},  # No core_mandate
        preferences={},
        abilities={},
        background={},
        metadata={"tags": ["bob"]},
    )

    mock_repo = MockRepository(characters={"Bob": character_no_core})
    mock_generator = MockPreferenceGenerator(
        error=ValueError("Personality Core required for preference generation")
    )

    service = EntityService(repository=mock_repo, preference_generator=mock_generator)

    with pytest.raises(ValueError, match="Personality Core required"):
        service.generate_character_preferences("Bob")


def test_generate_character_preferences_with_logger(sample_character, sample_preferences_result):
    """Test that service logs when generating preferences."""

    class MockLogger:
        def __init__(self):
            self.debug_calls = []

        def debug(self, message, context):
            self.debug_calls.append((message, context))

    logger = MockLogger()
    mock_repo = MockRepository(characters={"Alice": sample_character})
    mock_generator = MockPreferenceGenerator(result=sample_preferences_result)

    service = EntityService(
        repository=mock_repo, preference_generator=mock_generator, logger=logger
    )

    service.generate_character_preferences("Alice")

    # Should have logged the preference generation
    assert any("generate_preferences" in call[0] for call in logger.debug_calls)
    logged_context = next(
        call[1] for call in logger.debug_calls if "generate_preferences" in call[0]
    )
    assert logged_context["character"] == "Alice"
    assert logged_context["source"] == "test_provider"


def test_entity_card_construction_from_character(sample_character):
    """Test that EntityCard is correctly constructed from CharacterEntity."""
    mock_repo = MockRepository(characters={"Alice": sample_character})

    # Create a generator that captures what it receives
    captured_entity = None

    class CapturingGenerator:
        def generate(self, entity: EntityCard) -> PreferenceResult:
            nonlocal captured_entity
            captured_entity = entity
            return PreferenceResult(character_name="Alice", preferences={}, source="test")

    service = EntityService(repository=mock_repo, preference_generator=CapturingGenerator())

    service.generate_character_preferences("Alice")

    assert captured_entity is not None
    assert captured_entity.name == "Alice"
    assert captured_entity.entity_type == EntityType.CHARACTER
    assert captured_entity.triggers == ["alice", "warrior"]
    assert (
        captured_entity.personality_core == "Brave and honorable knight. Values truth and justice."
    )
    assert "personality" in captured_entity.sections
    assert "basics" in captured_entity.sections
