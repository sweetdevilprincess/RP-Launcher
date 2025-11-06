"""Tests for preference generation using LLM."""

from pathlib import Path

import pytest
from refactoring.src.domain.entities.models import EntityCard
from refactoring.src.domain.entities.preference_generator import (
    LLMPreferenceGenerator,
    PreferenceResult,
    _extract_json,
    _validate_preferences,
)
from refactoring.src.infrastructure.llm.base import (
    LLMAuthError,
    LLMError,
    LLMResponse,
    UsageStats,
)
from refactoring.src.shared.models import EntityType


# Mock LLM Client for testing
class MockLLMClient:
    """Mock LLM client that returns predefined responses."""

    def __init__(self, response_content: str, provider_id: str = "mock"):
        self.provider_id = provider_id
        self._response_content = response_content
        self.last_message = None
        self.call_count = 0

    def send_message(self, user_message: str, **kwargs) -> LLMResponse:
        self.last_message = user_message
        self.call_count += 1
        return LLMResponse(
            content=self._response_content,
            usage=UsageStats(input_tokens=100, output_tokens=200),
            raw_response={"mock": True},
        )

    def capabilities(self):
        from refactoring.src.infrastructure.llm.base import ProviderCapabilities

        return ProviderCapabilities()


class FailingLLMClient:
    """Mock LLM client that raises errors."""

    provider_id = "failing_mock"

    def __init__(self, error: Exception):
        self._error = error

    def send_message(self, user_message: str, **kwargs) -> LLMResponse:
        raise self._error

    def capabilities(self):
        from refactoring.src.infrastructure.llm.base import ProviderCapabilities

        return ProviderCapabilities()


# Test fixtures


@pytest.fixture
def sample_entity_card():
    """Sample entity card with personality core."""
    return EntityCard(
        name="Alice",
        entity_type=EntityType.CHARACTER,
        file_path=Path("/fake/alice.md"),
        triggers=["alice", "Ali"],
        full_content="# Alice\n\nA brave warrior.",
        personality_core="Brave, loyal, values honor above all. Dislikes cowardice.",
        metadata={"tags": ["alice"]},
        sections={"personality_core": "Brave, loyal, values honor above all."},
    )


@pytest.fixture
def valid_preferences_json():
    """Valid JSON response for preferences."""
    return """{
  "likes": [
    {"trait": "honesty", "points": 10, "reason": "values truth"},
    {"trait": "courage", "points": 12, "reason": "respects bravery"}
  ],
  "dislikes": [
    {"trait": "lying", "points": -8, "reason": "opposes dishonesty"}
  ],
  "hates": [
    {"trait": "cowardice", "points": -25, "reason": "dealbreaker for honor"}
  ]
}"""


# Tests for _extract_json


def test_extract_json_from_plain_response():
    """Test extracting JSON from response without surrounding text."""
    response = '{"key": "value"}'
    result = _extract_json(response)
    assert result == {"key": "value"}


def test_extract_json_from_response_with_text():
    """Test extracting JSON from response with surrounding text."""
    response = 'Here is the result:\n{"key": "value"}\nDone!'
    result = _extract_json(response)
    assert result == {"key": "value"}


def test_extract_json_from_response_with_markdown():
    """Test extracting JSON from markdown code block."""
    response = """Here are the preferences:

```json
{"likes": [], "dislikes": [], "hates": []}
```

Hope this helps!"""
    result = _extract_json(response)
    assert result == {"likes": [], "dislikes": [], "hates": []}


def test_extract_json_no_json_in_response():
    """Test error when no JSON in response."""
    response = "This is just plain text without any JSON."
    with pytest.raises(ValueError, match="did not contain JSON payload"):
        _extract_json(response)


def test_extract_json_invalid_json():
    """Test error when JSON is malformed."""
    response = '{"incomplete": invalid}'  # Invalid JSON - not quoted
    with pytest.raises(ValueError, match="Failed to parse LLM response"):
        _extract_json(response)


# Tests for _validate_preferences


def test_validate_preferences_valid():
    """Test validating correct preference structure."""
    data = {
        "likes": [{"trait": "honesty", "points": 10}],
        "dislikes": [{"trait": "lying", "points": -5}],
        "hates": [{"trait": "betrayal", "points": -25}],
    }
    result = _validate_preferences(data)
    assert result == data


def test_validate_preferences_missing_key():
    """Test error when required key is missing."""
    data = {"likes": [], "dislikes": []}  # missing "hates"
    with pytest.raises(ValueError, match="missing keys"):
        _validate_preferences(data)


def test_validate_preferences_extra_keys_allowed():
    """Test that extra keys are allowed."""
    data = {
        "likes": [],
        "dislikes": [],
        "hates": [],
        "extra_field": "allowed",
    }
    result = _validate_preferences(data)
    assert result == data


# Tests for LLMPreferenceGenerator


def test_generator_success(sample_entity_card, valid_preferences_json):
    """Test successful preference generation."""
    mock_client = MockLLMClient(valid_preferences_json, provider_id="test_provider")
    generator = LLMPreferenceGenerator(client=mock_client)

    result = generator.generate(sample_entity_card)

    assert isinstance(result, PreferenceResult)
    assert result.character_name == "Alice"
    assert result.source == "test_provider"
    assert "likes" in result.preferences
    assert "dislikes" in result.preferences
    assert "hates" in result.preferences
    assert len(result.preferences["likes"]) == 2
    assert result.preferences["likes"][0]["trait"] == "honesty"


def test_generator_sends_correct_prompt(sample_entity_card, valid_preferences_json):
    """Test that generator sends properly formatted prompt."""
    mock_client = MockLLMClient(valid_preferences_json)
    generator = LLMPreferenceGenerator(client=mock_client)

    generator.generate(sample_entity_card)

    assert mock_client.call_count == 1
    assert "Alice" in mock_client.last_message
    assert "Brave, loyal, values honor above all" in mock_client.last_message
    assert "relationship preferences" in mock_client.last_message


def test_generator_missing_personality_core(sample_entity_card):
    """Test error when personality core is missing."""
    sample_entity_card.personality_core = None
    mock_client = MockLLMClient("{}")
    generator = LLMPreferenceGenerator(client=mock_client)

    with pytest.raises(ValueError, match="Personality Core required"):
        generator.generate(sample_entity_card)


def test_generator_llm_auth_error(sample_entity_card):
    """Test handling of LLM authentication errors."""
    failing_client = FailingLLMClient(LLMAuthError("Invalid API key"))
    generator = LLMPreferenceGenerator(client=failing_client)

    with pytest.raises(LLMAuthError, match="Invalid API key"):
        generator.generate(sample_entity_card)


def test_generator_llm_error(sample_entity_card):
    """Test handling of general LLM errors."""
    failing_client = FailingLLMClient(LLMError("API timeout"))
    generator = LLMPreferenceGenerator(client=failing_client)

    with pytest.raises(LLMError, match="API timeout"):
        generator.generate(sample_entity_card)


def test_generator_invalid_json_response(sample_entity_card):
    """Test error when LLM returns invalid JSON."""
    mock_client = MockLLMClient("This is not JSON at all")
    generator = LLMPreferenceGenerator(client=mock_client)

    with pytest.raises(ValueError, match="did not contain JSON payload"):
        generator.generate(sample_entity_card)


def test_generator_incomplete_json_response(sample_entity_card):
    """Test error when LLM returns JSON missing required keys."""
    incomplete_json = '{"likes": [], "dislikes": []}'  # missing "hates"
    mock_client = MockLLMClient(incomplete_json)
    generator = LLMPreferenceGenerator(client=mock_client)

    with pytest.raises(ValueError, match="missing keys"):
        generator.generate(sample_entity_card)


def test_generator_with_logger(sample_entity_card, valid_preferences_json):
    """Test that generator logs errors when logger provided."""

    class MockLogger:
        def __init__(self):
            self.errors = []

        def error(self, event, context):
            self.errors.append((event, context))

    logger = MockLogger()
    failing_client = FailingLLMClient(LLMAuthError("Test error"))
    generator = LLMPreferenceGenerator(client=failing_client, logger=logger)

    try:
        generator.generate(sample_entity_card)
    except LLMAuthError:
        pass

    assert len(logger.errors) == 1
    assert logger.errors[0][0] == "llm.auth_error"
    assert "Test error" in str(logger.errors[0][1])


def test_generator_temperature_and_max_tokens(sample_entity_card, valid_preferences_json):
    """Test that generator uses correct LLM parameters."""

    class ParameterCapturingClient:
        provider_id = "test"

        def __init__(self):
            self.params = {}

        def send_message(self, user_message: str, **kwargs):
            self.params = kwargs
            return LLMResponse(
                content=valid_preferences_json,
                usage=UsageStats(input_tokens=10, output_tokens=20),
                raw_response={},
            )

        def capabilities(self):
            from refactoring.src.infrastructure.llm.base import ProviderCapabilities

            return ProviderCapabilities()

    client = ParameterCapturingClient()
    generator = LLMPreferenceGenerator(client=client)

    generator.generate(sample_entity_card)

    assert client.params["max_tokens"] == 2048
    assert client.params["temperature"] == 0.7
