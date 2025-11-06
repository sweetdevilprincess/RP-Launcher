"""Claude SDK streaming client implementing shared interfaces (WIP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .base import (
    ConversationHistory,
    LLMResponse,
    ProviderCapabilities,
    StreamingLLMClient,
    UsageStats,
)

try:
    # Reuse existing high-performance SDK bridge implementation
    from src.clients.claude_sdk import ClaudeSDKClient as LegacyClaudeSDKClient
except ImportError as exc:  # pragma: no cover - dev env guard
    raise RuntimeError(
        "Legacy ClaudeSDKClient not found. Ensure src/clients/claude_sdk.py is available."
    ) from exc


class ClaudeSDKStreamingClient(StreamingLLMClient):
    """Adapter around the legacy Claude SDK bridge exposing the new interface."""

    provider_id = "anthropic_sdk"

    def __init__(
        self,
        *,
        rp_dir: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        working_dir = rp_dir or project_root or Path.cwd()
        self._client = LegacyClaudeSDKClient(cwd=working_dir)
        self._capabilities = ProviderCapabilities(
            supports_streaming=True,
            supports_prompt_cache=True,
            supports_thinking_budget=True,
            native_system_role=False,  # SDK handles system via cache/session
        )

    # ------------------------------------------------------------------
    # Interface implementation
    # ------------------------------------------------------------------

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def stream_message(
        self,
        user_message: str,
        *,
        cached_context: Optional[str] = None,
        conversation_history: Optional[ConversationHistory] = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> Iterable[str]:
        # SDK maintains session state internally; conversation_history not needed
        del conversation_history
        del max_tokens  # SDK currently controls via Node bridge config
        del temperature  # Temperature handled by bridge defaults

        stream = self._client.query(
            message=user_message,
            cached_context=cached_context,
            thinking_mode=thinking_mode,
            thinking_budget=thinking_budget,
            stream=True,
            **kwargs,
        )
        for chunk in stream:
            yield chunk

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: Optional[str] = None,
        conversation_history: Optional[ConversationHistory] = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        del conversation_history
        del max_tokens
        del temperature

        chunks = self._client.query(
            message=user_message,
            cached_context=cached_context,
            thinking_mode=thinking_mode,
            thinking_budget=thinking_budget,
            stream=False,
            **kwargs,
        )
        # query returns an iterator even when stream=False
        content = "".join(chunks)
        usage = self._build_usage_stats()

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response={
                "cache_stats": self._client.get_cache_stats(),
                "metadata": self._client.get_metadata(),
            },
            thinking=None,
        )

    # ------------------------------------------------------------------
    # Additional helpers
    # ------------------------------------------------------------------

    def clear_session(self) -> None:
        self._client.clear_session()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ClaudeSDKStreamingClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_usage_stats(self) -> UsageStats:
        usage_data: Dict[str, Any] = getattr(self._client, "_last_usage", {}) or {}
        cache_stats = self._client.get_cache_stats()

        input_tokens = (
            usage_data.get("input_tokens")
            or usage_data.get("prompt_tokens")
            or (cache_stats.input_tokens if cache_stats else 0)
        )
        output_tokens = (
            usage_data.get("output_tokens")
            or usage_data.get("completion_tokens")
            or (cache_stats.output_tokens if cache_stats else 0)
        )

        cache_creation = cache_read = 0
        if cache_stats:
            cache_creation = cache_stats.cache_creation_input_tokens
            cache_read = cache_stats.cache_read_input_tokens

        return UsageStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
        )


__all__ = ["ClaudeSDKStreamingClient"]
