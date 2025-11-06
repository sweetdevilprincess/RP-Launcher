"""AI client adapter for semantic trigger evaluation.

Adapts the LLMClient interface to provide the AiClient protocol needed by
SemanticEvaluator. This allows using any LLMClient (Claude, OpenAI, etc.)
for semantic matching.
"""

from __future__ import annotations

from ...shared.interfaces.ai_client import AiClient
from ...shared.logging import get_logger
from .base import LLMClient, LLMError


class SemanticAiClient:
    """Adapts LLMClient to AiClient protocol for semantic evaluation.

    This class wraps any LLMClient and provides the evaluate_semantic_match
    method required by SemanticEvaluator.

    Example:
        >>> from .claude_api_client import ClaudeAPIClient
        >>> llm_client = ClaudeAPIClient()
        >>> ai_client = SemanticAiClient(llm_client)
        >>> matched, confidence = ai_client.evaluate_semantic_match(
        ...     message="I was talking to my sister",
        ...     descriptions=["References to Alice", "Alice's family"],
        ...     entity_name="Alice"
        ... )
    """

    def __init__(
        self,
        llm_client: LLMClient,
        *,
        model: str | None = None,
        max_tokens: int = 100,
    ) -> None:
        """Initialize semantic AI client.

        Args:
            llm_client: The LLM client to use for evaluation
            model: Optional model override (uses client's default if not provided)
            max_tokens: Maximum tokens for response (default: 100)
        """
        self._llm_client = llm_client
        self._model = model
        self._max_tokens = max_tokens
        self._logger = get_logger(__name__)

    def evaluate_semantic_match(
        self, message: str, descriptions: list[str], entity_name: str
    ) -> tuple[bool, float]:
        """Evaluate if a message semantically matches any descriptions.

        Args:
            message: The user's message to evaluate
            descriptions: List of semantic descriptions to match against
            entity_name: Name of the entity being evaluated

        Returns:
            Tuple of (matched: bool, confidence: float)
            - matched: True if any description matches
            - confidence: Score from 0.0 to 1.0 indicating match strength
        """
        # Build the evaluation prompt
        prompt = self._build_evaluation_prompt(message, descriptions, entity_name)

        try:
            # Call the LLM
            response = self._llm_client.generate(
                user_message=prompt,
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=0.0,  # Deterministic for evaluation
            )

            # Parse the response
            matched, confidence = self._parse_response(response.content)

            self._logger.debug(
                "semantic_ai_client.evaluated",
                context={
                    "entity": entity_name,
                    "matched": matched,
                    "confidence": confidence,
                },
            )

            return matched, confidence

        except LLMError as e:
            self._logger.error(
                "semantic_ai_client.error",
                context={"entity": entity_name, "error": str(e)},
            )
            # Return no match on error
            return False, 0.0

    def _build_evaluation_prompt(
        self, message: str, descriptions: list[str], entity_name: str
    ) -> str:
        """Build the prompt for semantic evaluation."""
        descriptions_text = "\n".join(f"- {desc}" for desc in descriptions)

        return f"""Analyze if the following message semantically relates to "{entity_name}" based on these descriptions:

{descriptions_text}

Message: "{message}"

Respond with ONLY a JSON object in this format:
{{"matched": true/false, "confidence": 0.0-1.0}}

Rules:
- matched: true if the message relates to ANY of the descriptions
- confidence: 0.0 (no relation) to 1.0 (strong relation)
- Consider indirect references and context
- Be conservative with confidence scores

Response:"""

    def _parse_response(self, content: str) -> tuple[bool, float]:
        """Parse the LLM response to extract match result.

        Args:
            content: The LLM's response text

        Returns:
            Tuple of (matched, confidence)
        """
        import json
        import re

        # Try to find JSON in the response
        json_match = re.search(r"\{[^}]+\}", content)
        if not json_match:
            self._logger.warning(
                "semantic_ai_client.parse_failed",
                context={"response": content[:100]},
            )
            return False, 0.0

        try:
            result = json.loads(json_match.group())
            matched = bool(result.get("matched", False))
            confidence = float(result.get("confidence", 0.0))

            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))

            return matched, confidence

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            self._logger.warning(
                "semantic_ai_client.parse_error",
                context={"error": str(e), "response": content[:100]},
            )
            return False, 0.0


# Type check to ensure SemanticAiClient implements AiClient protocol
def _type_check() -> None:
    """Verify that SemanticAiClient implements AiClient protocol."""
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        _: AiClient = SemanticAiClient(None)  # type: ignore
