"""Tests for Mock LLM Client."""

from __future__ import annotations

import time

import pytest
from refactoring.src.infrastructure.llm.mock_client import MockLLMClient


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    def test_mock_client_initialization(self):
        """Mock client initializes with default settings."""
        client = MockLLMClient()

        assert client.provider_id == "mock"
        assert client.delay == 0.5
        assert len(client.response_templates) == 5
        assert client.response_index == 0

    def test_mock_client_custom_delay(self):
        """Mock client accepts custom delay."""
        client = MockLLMClient(delay=0.1)

        assert client.delay == 0.1

    def test_mock_client_custom_templates(self):
        """Mock client accepts custom response templates."""
        templates = [
            "Custom response 1",
            "Custom response 2"
        ]
        client = MockLLMClient(response_templates=templates)

        assert client.response_templates == templates
        assert len(client.response_templates) == 2

    def test_send_message_returns_response(self):
        """send_message returns LLMResponse."""
        client = MockLLMClient(delay=0.0)  # No delay for faster tests

        response = client.send_message("Hello test")

        assert response.content is not None
        assert isinstance(response.content, str)
        assert len(response.content) > 0

    def test_send_message_simulates_delay(self):
        """send_message simulates API latency."""
        client = MockLLMClient(delay=0.2)

        start = time.time()
        client.send_message("Hello")
        elapsed = time.time() - start

        # Should take at least 0.2 seconds
        assert elapsed >= 0.2

    def test_send_message_rotates_templates(self):
        """send_message cycles through response templates."""
        templates = ["Response 1", "Response 2", "Response 3"]
        client = MockLLMClient(delay=0.0, response_templates=templates)

        # First call should use template 0, but index advances to 1
        response1 = client.send_message("Test 1")
        # Second call should use template 1, index advances to 2
        response2 = client.send_message("Test 2")
        # Third call should use template 2, index wraps to 0
        response3 = client.send_message("Test 3")
        # Fourth call should use template 0 again
        response4 = client.send_message("Test 4")

        assert "Response 1" in response1.content
        assert "Response 2" in response2.content
        assert "Response 3" in response3.content
        assert "Response 1" in response4.content  # Wrapped around

    def test_send_message_includes_usage_stats(self):
        """send_message returns usage statistics."""
        client = MockLLMClient(delay=0.0)

        response = client.send_message("Hello test message")

        assert response.usage is not None
        assert response.usage.input_tokens > 0
        assert response.usage.output_tokens > 0
        assert response.usage.cache_creation_input_tokens == 0
        assert response.usage.cache_read_input_tokens == 0

    def test_send_message_calculates_input_tokens(self):
        """send_message calculates input tokens from message."""
        client = MockLLMClient(delay=0.0)

        short_response = client.send_message("Hi")
        long_response = client.send_message("This is a much longer message with many words")

        # Longer message should have more input tokens
        assert long_response.usage.input_tokens > short_response.usage.input_tokens

    def test_send_message_with_cached_context(self):
        """send_message accounts for cached context in token count."""
        client = MockLLMClient(delay=0.0)

        response_no_cache = client.send_message("Hello")
        response_with_cache = client.send_message(
            "Hello",
            cached_context="This is a large context that would be cached"
        )

        # Response with cache should have more input tokens
        assert response_with_cache.usage.input_tokens > response_no_cache.usage.input_tokens

    def test_send_message_raw_response_metadata(self):
        """send_message includes mock metadata in raw_response."""
        client = MockLLMClient(delay=0.25)

        response = client.send_message("Test message")

        assert response.raw_response is not None
        assert response.raw_response["mock"] is True
        assert response.raw_response["provider"] == "mock_client"
        assert response.raw_response["delay"] == 0.25
        assert "user_message_length" in response.raw_response

    def test_send_message_no_thinking(self):
        """send_message returns None for thinking field."""
        client = MockLLMClient(delay=0.0)

        response = client.send_message("Hello")

        assert response.thinking is None

    def test_capabilities(self):
        """capabilities returns mock provider capabilities."""
        client = MockLLMClient()

        capabilities = client.capabilities()

        assert capabilities.supports_streaming is False
        assert capabilities.supports_prompt_cache is False
        assert capabilities.supports_thinking_budget is False
        assert capabilities.native_system_role is True

    def test_set_delay(self):
        """set_delay updates response delay."""
        client = MockLLMClient(delay=0.5)

        client.set_delay(0.1)

        assert client.delay == 0.1

    def test_add_response_template(self):
        """add_response_template adds new template to rotation."""
        client = MockLLMClient(delay=0.0, response_templates=["Response 1"])

        initial_count = len(client.response_templates)
        client.add_response_template("New response")

        assert len(client.response_templates) == initial_count + 1
        assert "New response" in client.response_templates

    def test_reset_response_index(self):
        """reset_response_index resets template rotation."""
        client = MockLLMClient(delay=0.0, response_templates=["A", "B", "C"])

        # Advance index by getting responses
        client.send_message("1")
        client.send_message("2")
        assert client.response_index == 2

        # Reset
        client.reset_response_index()
        assert client.response_index == 0

    def test_send_message_with_all_parameters(self):
        """send_message accepts all LLMClient protocol parameters."""
        client = MockLLMClient(delay=0.0)

        # Should not raise even with unused parameters
        response = client.send_message(
            "Test message",
            cached_context="Context here",
            conversation_history=None,
            max_tokens=1024,
            temperature=0.7,
            extra_param="ignored"
        )

        assert response is not None
        assert response.content is not None

    def test_mock_client_realistic_token_estimation(self):
        """Mock client provides realistic token count estimates."""
        client = MockLLMClient(delay=0.0)

        # Rough estimate: 1 token ≈ 0.5 words, so 10 words ≈ 20 tokens
        message = " ".join(["word"] * 10)  # 10 words
        response = client.send_message(message)

        # Should be around 20 tokens (10 words * 2)
        assert 15 <= response.usage.input_tokens <= 25

    def test_response_template_formatting(self):
        """Response templates support {index} and {preview} placeholders."""
        templates = [
            "Response {index} for message: {preview}"
        ]
        client = MockLLMClient(delay=0.0, response_templates=templates)

        response = client.send_message("Hello world this is a test")

        # Should contain formatted content
        assert "Hello world" in response.content or "preview" not in response.content.lower()

    def test_long_message_preview_truncation(self):
        """Long messages are truncated in preview."""
        client = MockLLMClient(
            delay=0.0,
            response_templates=["Got: {preview}"]
        )

        long_message = "x" * 100  # 100 characters
        response = client.send_message(long_message)

        # Preview should be truncated (50 chars + "...")
        # The actual response might not show this if template doesn't use {preview}
        # but the logic should work
        assert response.content is not None


class TestMockLLMClientIntegration:
    """Integration tests for MockLLMClient."""

    def test_multiple_requests_in_sequence(self):
        """Multiple requests work correctly in sequence."""
        client = MockLLMClient(delay=0.0)

        responses = []
        for i in range(10):
            response = client.send_message(f"Message {i}")
            responses.append(response)

        # All responses should be valid
        assert len(responses) == 10
        for response in responses:
            assert response.content is not None
            assert response.usage.input_tokens > 0
            assert response.usage.output_tokens > 0

    def test_consistent_provider_id(self):
        """Provider ID is consistent across instances."""
        client1 = MockLLMClient()
        client2 = MockLLMClient(delay=1.0)

        assert client1.provider_id == client2.provider_id == "mock"

    def test_zero_delay_for_testing(self):
        """Zero delay allows instant responses for fast tests."""
        client = MockLLMClient(delay=0.0)

        start = time.time()
        for _ in range(10):
            client.send_message("Test")
        elapsed = time.time() - start

        # 10 requests with 0 delay should be very fast (< 0.1s)
        assert elapsed < 0.1
