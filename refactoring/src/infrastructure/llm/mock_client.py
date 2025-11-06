"""Mock LLM Client for Testing Mode.

This module provides a mock LLM client that returns pre-defined responses
without making any actual API calls. Useful for testing the bridge and TUI
without incurring API costs or requiring network connectivity.
"""

from __future__ import annotations

import time
from typing import Any

from .base import (
    ConversationHistory,
    LLMResponse,
    ProviderCapabilities,
    UsageStats,
)


class MockLLMClient:
    """Mock LLM client that returns pre-defined responses.

    This client simulates an LLM by returning pre-configured responses
    with a configurable delay to mimic real API latency. It implements
    the LLMClient protocol without making any actual API calls.
    """

    provider_id = "mock"

    def __init__(
        self,
        delay: float = 0.5,
        response_templates: list[str] | None = None,
    ):
        """Initialize mock client.

        Args:
            delay: Simulated response delay in seconds (default: 0.5)
            response_templates: List of response templates to cycle through.
                If None, uses default templates.
        """
        self.delay = delay
        self.response_index = 0

        # Default response templates
        if response_templates is None:
            self.response_templates = [
                "This is a test response from the mock LLM client. "
                "Testing mode is active, so no actual API calls are being made.",

                "Mock response #{index}: Your message '{preview}' was received. "
                "In production mode, this would be processed by a real LLM provider.",

                "Testing mode active. The mock client is simulating an LLM response "
                "with realistic token counts and metadata.",

                "Hello! I'm the mock LLM client. I'm here to help you test your "
                "application without making real API calls or incurring costs.",

                "Mock LLM response: Everything is working correctly in testing mode. "
                "You can switch to a real provider when you're ready to deploy.",
            ]
        else:
            self.response_templates = response_templates

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send message and return mock response.

        Args:
            user_message: The user's message
            cached_context: Context to cache (ignored in mock)
            conversation_history: Previous conversation turns (ignored in mock)
            max_tokens: Maximum tokens to generate (used for mock stats)
            temperature: Sampling temperature (ignored in mock)
            **kwargs: Additional provider-specific parameters (ignored in mock)

        Returns:
            Mock LLMResponse with realistic-looking data
        """
        # Simulate API latency
        time.sleep(self.delay)

        # Get next response template
        template = self.response_templates[self.response_index]
        self.response_index = (self.response_index + 1) % len(self.response_templates)

        # Format response with context
        user_preview = user_message[:50] + "..." if len(user_message) > 50 else user_message
        response_content = template.format(
            index=self.response_index,
            preview=user_preview,
        )

        # Calculate mock token counts (rough estimate)
        input_token_count = len(user_message.split()) * 2  # Rough approximation
        if cached_context:
            input_token_count += len(cached_context.split()) * 2
        if conversation_history:
            for msg in conversation_history:
                input_token_count += len(msg.content.split()) * 2

        output_token_count = len(response_content.split()) * 2

        # Create mock usage stats
        usage = UsageStats(
            input_tokens=input_token_count,
            output_tokens=output_token_count,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        )

        # Create mock response
        return LLMResponse(
            content=response_content,
            usage=usage,
            raw_response={
                "mock": True,
                "provider": "mock_client",
                "user_message_length": len(user_message),
                "delay": self.delay,
            },
            thinking=None,  # Mock client doesn't include thinking
        )

    def capabilities(self) -> ProviderCapabilities:
        """Return mock provider capabilities.

        Returns:
            ProviderCapabilities indicating what the mock client supports
        """
        return ProviderCapabilities(
            supports_streaming=False,
            supports_prompt_cache=False,
            supports_thinking_budget=False,
            native_system_role=True,
        )

    def set_delay(self, delay: float) -> None:
        """Update the simulated response delay.

        Args:
            delay: New delay in seconds
        """
        self.delay = delay

    def add_response_template(self, template: str) -> None:
        """Add a new response template to the rotation.

        Args:
            template: Response template string (can include {index} and {preview} placeholders)
        """
        self.response_templates.append(template)

    def reset_response_index(self) -> None:
        """Reset the response template index to 0."""
        self.response_index = 0


__all__ = ["MockLLMClient"]
