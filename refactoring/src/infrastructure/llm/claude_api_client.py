"""Claude API client using shared LLM abstractions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...shared.interfaces import (
    LoggingService,
    Transport,
    TransportError,
    TransportRequest,
)
from ..transports import LoggingTransport, ProxyTransport, RequestsTransport
from .base import (
    ConversationHistory,
    ConversationMessage,
    LLMAuthError,
    LLMClient,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
    ProviderCapabilities,
    StreamingLLMClient,
    UsageStats,
)
from .config_utils import (
    merge_config_sources,
    read_env_file,
    read_json_file,
    resolve_project_root,
)
from .proxy import ProxySettings, load_proxy_settings


@dataclass(slots=True)
class ClaudeAPISettings:
    api_key: str | None
    auth_token: str | None
    base_url: str | None


_DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
_DEFAULT_BASE_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


_THINKING_MODES: dict[str, int] = {
    "disabled": 0,
    "think": 5_000,
    "think hard": 10_000,
    "megathink": 10_000,
    "think harder": 25_000,
    "ultrathink": 31_999,
}


def load_claude_settings(
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> ClaudeAPISettings:
    start = Path(start_path) if start_path else None
    project_root = resolve_project_root(start)

    config_data: dict[str, Any] = {}
    if config_override:
        config_data.update(config_override)
    else:
        config_data.update(read_json_file(project_root / "config" / "config.json"))

    env_file_values = read_env_file(project_root / ".env")

    merged = merge_config_sources(
        env_keys={
            "api_key": "ANTHROPIC_API_KEY",
            "auth_token": "ANTHROPIC_AUTH_TOKEN",
            "base_url": "ANTHROPIC_BASE_URL",
        },
        config_keys={
            "api_key": config_data.get("api_key") or config_data.get("anthropic_api_key"),
            "auth_token": config_data.get("auth_token") or config_data.get("anthropic_auth_token"),
            "base_url": config_data.get("base_url") or config_data.get("anthropic_base_url"),
        },
        env_file_keys=env_file_values,
    )

    # Legacy support: some configs stored proxy URL in api_key slot
    api_key = merged.get("api_key")
    base_url = merged.get("base_url")
    if api_key and api_key.lower().startswith(("http://", "https://")):
        base_url = api_key
        api_key = None

    return ClaudeAPISettings(
        api_key=api_key,
        auth_token=merged.get("auth_token"),
        base_url=base_url,
    )


class ClaudeAPIClient(StreamingLLMClient):
    """HTTP client that talks to Anthropic's Messages API using Transport abstraction.

    Supports both streaming and non-streaming responses from the Anthropic API.
    """

    provider_id = "anthropic_api"

    def __init__(
        self,
        *,
        settings: ClaudeAPISettings | None = None,
        proxy_settings: ProxySettings | None = None,
        transport: Transport | None = None,
        logger: LoggingService | None = None,
        config_override: dict[str, Any] | None = None,
        rp_dir: str | None = None,
        request_timeout: int | None = 60,
    ) -> None:
        start_path = rp_dir if rp_dir else None

        self._settings = settings or load_claude_settings(
            config_override=config_override,
            start_path=start_path,
        )

        if not (self._settings.api_key or self._settings.auth_token):
            raise LLMAuthError(
                "Anthropic credentials missing. Provide ANTHROPIC_API_KEY or auth token."
            )

        self._proxy_settings = proxy_settings or load_proxy_settings(
            config_override=config_override,
            start_path=start_path,
        )

        # Build transport chain: Base → Proxy → Logging
        base_transport: Transport = transport or RequestsTransport()
        base_transport = ProxyTransport(base_transport, proxy_config=self._proxy_settings)
        if logger is not None:
            base_transport = LoggingTransport(base_transport, logger, name="anthropic")
        self._transport = base_transport
        self._logger = logger

        self._model = _DEFAULT_MODEL
        self._base_url = (self._settings.base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = request_timeout

        # Build base headers
        self._base_headers: dict[str, str] = {
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        # Add authentication
        if self._settings.api_key:
            self._base_headers["x-api-key"] = self._settings.api_key
        elif self._settings.auth_token:
            self._base_headers["authorization"] = f"Bearer {self._settings.auth_token}"

        self._capabilities = ProviderCapabilities(
            supports_streaming=True,
            supports_prompt_cache=True,
            supports_thinking_budget=True,
            native_system_role=False,
        )

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8_192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a message to the Anthropic API and return the response."""
        # Build system blocks
        system: list[dict[str, Any]] = []
        if cached_context:
            system.append(
                {
                    "type": "text",
                    "text": cached_context,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Build message history
        messages: list[dict[str, Any]] = []
        if conversation_history:
            for entry in conversation_history:
                if isinstance(entry, ConversationMessage):
                    role, content = entry.role, entry.content
                else:
                    role = entry.get("role")
                    content = entry.get("content")
                if role not in {"user", "assistant"}:
                    continue
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        # Build request payload
        budget = self._resolve_thinking_budget(thinking_mode, thinking_budget)

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system:
            payload["system"] = system

        if budget > 0:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }

        # Make request via transport
        request = TransportRequest(
            endpoint=self._base_url,
            payload=payload,
            headers=self._base_headers,
            timeout_seconds=self._timeout,
        )

        try:
            transport_response = self._transport.post(request)
        except TransportError as exc:
            raise LLMError(f"Transport error: {exc}") from exc

        # Handle HTTP errors
        if transport_response.status_code == 401:
            error_msg = self._extract_error_message(transport_response.body)
            raise LLMAuthError(f"Authentication failed: {error_msg}")
        if transport_response.status_code == 429:
            error_msg = self._extract_error_message(transport_response.body)
            raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
        if transport_response.status_code >= 400:
            error_msg = self._extract_error_message(transport_response.body)
            raise LLMError(f"Anthropic API error ({transport_response.status_code}): {error_msg}")

        # Parse successful response
        response_data = transport_response.body
        if not isinstance(response_data, dict):
            raise LLMError(f"Unexpected response format: {type(response_data)}")

        content, thinking = self._extract_blocks_from_dict(response_data)

        # Extract usage stats
        usage_data = response_data.get("usage", {})
        usage = UsageStats(
            input_tokens=usage_data.get("input_tokens", 0),
            output_tokens=usage_data.get("output_tokens", 0),
            cache_creation_input_tokens=usage_data.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=usage_data.get("cache_read_input_tokens", 0),
        )

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response_data,
            thinking=thinking or None,
        )

    def stream_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8_192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> Iterable[str]:
        """Stream a message to the Anthropic API and yield chunks as they arrive.

        Args:
            user_message: The user's message
            cached_context: Optional context to cache
            conversation_history: Optional conversation history
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            thinking_mode: Thinking mode string
            thinking_budget: Override thinking budget
            **kwargs: Additional arguments

        Yields:
            Text chunks from the streaming response
        """
        # Build system blocks (same as send_message)
        system: list[dict[str, Any]] = []
        if cached_context:
            system.append(
                {
                    "type": "text",
                    "text": cached_context,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Build message history (same as send_message)
        messages: list[dict[str, Any]] = []
        if conversation_history:
            for entry in conversation_history:
                if isinstance(entry, ConversationMessage):
                    role, content = entry.role, entry.content
                else:
                    role = entry.get("role")
                    content = entry.get("content")
                if role not in {"user", "assistant"}:
                    continue
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        # Build request payload (same as send_message, but with stream=true)
        budget = self._resolve_thinking_budget(thinking_mode, thinking_budget)

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,  # Enable streaming
        }

        if system:
            payload["system"] = system

        if budget > 0:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }

        # Make streaming request via transport
        request = TransportRequest(
            endpoint=self._base_url,
            payload=payload,
            headers=self._base_headers,
            timeout_seconds=self._timeout,
        )

        try:
            # Yield chunks from transport's streaming response
            for chunk in self._transport.post_stream(request):
                yield chunk
        except TransportError as exc:
            raise LLMError(f"Transport error during streaming: {exc}") from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_thinking_budget(self, mode: str, override: int | None) -> int:
        """Resolve thinking budget from mode string or explicit override."""
        if override is not None:
            return max(0, int(override))
        return _THINKING_MODES.get(mode.lower(), _THINKING_MODES["megathink"])

    @staticmethod
    def _extract_blocks_from_dict(response_data: dict[str, Any]) -> tuple[str, str]:
        """Extract text and thinking blocks from API response."""
        text = ""
        thinking = ""

        content_blocks = response_data.get("content", [])
        for block in content_blocks:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type", "")
            if block_type == "thinking":
                thinking = block.get("thinking", "")
            elif block_type == "text":
                text = block.get("text", "")

        return text, thinking

    @staticmethod
    def _extract_error_message(body: Any) -> str:
        """Extract error message from API error response."""
        if isinstance(body, dict):
            error = body.get("error", {})
            if isinstance(error, dict):
                return error.get("message", str(body))
            return str(error) if error else str(body)
        return str(body)


__all__ = [
    "ClaudeAPIClient",
    "ClaudeAPISettings",
    "load_claude_settings",
]
