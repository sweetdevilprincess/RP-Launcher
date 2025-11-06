"""Generate character preference data from entity information."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from ...infrastructure.llm.base import LLMAuthError, LLMClient, LLMError
from ...shared.interfaces import LoggingService
from .models import EntityCard


@dataclass
class PreferenceResult:
    """Structured representation of generated preferences."""

    character_name: str
    preferences: dict[str, object]
    source: str


class PreferenceGenerator(Protocol):
    """Contract for generating relationship preferences."""

    def generate(self, entity: EntityCard) -> PreferenceResult: ...


class LLMPreferenceGenerator:
    """LLM-backed implementation of ``PreferenceGenerator``.

    Uses the generic LLMClient interface from Workstream I to generate
    character preferences. Works with any LLM provider (Claude, OpenAI, OpenRouter, etc.).
    """

    PROMPT_TEMPLATE = """Analyze this character's Personality Core and generate relationship preferences.

**Character Name**: {character_name}

**Personality Core**:
{personality_core}

**Task**: Based on this personality, generate a list of traits this character would like, dislike, and hate in relationships with others.

**Guidelines**:
- Be specific to THIS character's personality (not generic traits)
- Consider their core values, flaws, speaking style, and behaviors
- Likes should have +5 to +15 points (most important values get higher points)
- Dislikes should have -5 to -10 points
- Hates should have -20 to -30 points (dealbreakers only)
- Include 3-5 items in each category
- Each item should have a "trait" and a "reason" explaining why based on personality

Return ONLY valid JSON in this exact format:
{{
  "likes": [
    {{"trait": "trait_name", "points": 10, "reason": "why this character values this"}},
    ...
  ],
  "dislikes": [
    {{"trait": "trait_name", "points": -5, "reason": "why this bothers this character"}},
    ...
  ],
  "hates": [
    {{"trait": "trait_name", "points": -25, "reason": "why this is a dealbreaker"}},
    ...
  ]
}}"""

    def __init__(
        self,
        *,
        client: LLMClient,
        logger: LoggingService | None = None,
    ) -> None:
        """Initialize the preference generator.

        Args:
            client: LLMClient instance (required). Use registry to get a client.
            logger: Optional logging service for error tracking.
        """
        self._client = client
        self._logger = logger

    def generate(self, entity: EntityCard) -> PreferenceResult:
        """Generate relationship preferences for a character entity.

        Args:
            entity: EntityCard with personality_core populated

        Returns:
            PreferenceResult with likes, dislikes, and hates

        Raises:
            ValueError: If personality_core is missing
            LLMAuthError: If LLM authentication fails
            LLMError: If LLM request fails
        """
        if not entity.personality_core:
            raise ValueError("Personality Core required for preference generation")

        prompt = self.PROMPT_TEMPLATE.format(
            character_name=entity.name,
            personality_core=entity.personality_core,
        )

        try:
            response = self._client.send_message(
                user_message=prompt,
                max_tokens=2048,
                temperature=0.7,
            )
        except LLMAuthError as exc:
            self._log_error("llm.auth_error", exc)
            raise
        except LLMError as exc:
            self._log_error("llm.error", exc)
            raise

        payload = _extract_json(response.content)
        preferences = _validate_preferences(payload)

        return PreferenceResult(
            character_name=entity.name,
            preferences=preferences,
            source=self._client.provider_id,
        )

    def _log_error(self, event: str, error: Exception) -> None:
        if self._logger is None:
            return
        self._logger.error(event, context={"error": str(error)})


_JSON_PATTERN = re.compile(r"\{[\s\S]*\}")


def _extract_json(response: str) -> dict[str, object]:
    """Extract JSON from LLM response text.

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON as dict

    Raises:
        ValueError: If no JSON found or parsing fails
    """
    match = _JSON_PATTERN.search(response)
    if not match:
        raise ValueError("LLM response did not contain JSON payload")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM response: {exc}") from exc


def _validate_preferences(data: dict[str, object]) -> dict[str, object]:
    required_keys = {"likes", "dislikes", "hates"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        raise ValueError(f"Generated preferences missing keys: {sorted(missing)}")
    return data
