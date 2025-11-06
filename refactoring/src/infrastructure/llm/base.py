"""Base interfaces and data structures for provider-agnostic LLM clients."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

MessageRole = Literal["system", "user", "assistant", "tool"]


@dataclass(slots=True)
class ConversationMessage:
    """Single turn in a chat-style conversation."""

    role: MessageRole
    content: str
    metadata: dict[str, Any] | None = None


ConversationHistory = list[ConversationMessage]


@dataclass(slots=True)
class UsageStats:
    """Token accounting normalized across providers."""

    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @classmethod
    def empty(cls) -> UsageStats:
        return cls(input_tokens=0, output_tokens=0)

    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(slots=True)
class ProviderCapabilities:
    """Capability flags describing an LLM client."""

    supports_streaming: bool = False
    supports_prompt_cache: bool = False
    supports_thinking_budget: bool = False
    native_system_role: bool = True


@dataclass(slots=True)
class LLMResponse:
    """Standard response payload returned by every provider."""

    content: str
    usage: UsageStats
    raw_response: Any
    thinking: str | None = None


class LLMError(Exception):
    """Base error for provider-specific exceptions."""


class LLMRateLimitError(LLMError):
    """Raised when a provider rejects due to rate limiting."""


class LLMAuthError(LLMError):
    """Raised when credentials are invalid or missing."""


class LLMClient(Protocol):
    """Common client interface expected by the bridge and automation layers."""

    provider_id: str

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse: ...

    def capabilities(self) -> ProviderCapabilities: ...


class StreamingLLMClient(LLMClient, Protocol):
    """Optional interface for streaming providers (Claude SDK, future OpenAI streaming)."""

    def stream_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> Iterable[str]: ...


__all__ = [
    "ConversationHistory",
    "ConversationMessage",
    "LLMAuthError",
    "LLMClient",
    "LLMError",
    "LLMRateLimitError",
    "LLMResponse",
    "MessageRole",
    "ProviderCapabilities",
    "StreamingLLMClient",
    "UsageStats",
]
