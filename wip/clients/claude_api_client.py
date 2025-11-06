"""Claude API client using shared LLM abstractions (WIP)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import anthropic  # type: ignore
except ImportError as exc:  # pragma: no cover - dev env guard
    raise RuntimeError(
        "anthropic package is required for ClaudeAPIClient; install anthropic>=0.37"
    ) from exc

from .base import (
    ConversationHistory,
    ConversationMessage,
    LLMAuthError,
    LLMClient,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
    ProviderCapabilities,
    UsageStats,
)
from .config_utils import (
    merge_config_sources,
    pick_first,
    read_env_file,
    read_json_file,
    resolve_project_root,
)
from .proxy import ProxySettings, load_proxy_settings


@dataclass(slots=True)
class ClaudeAPISettings:
    api_key: Optional[str]
    auth_token: Optional[str]
    base_url: Optional[str]


_DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


_THINKING_MODES: Dict[str, int] = {
    "disabled": 0,
    "think": 5_000,
    "think hard": 10_000,
    "megathink": 10_000,
    "think harder": 25_000,
    "ultrathink": 31_999,
}


def load_claude_settings(
    config_override: Optional[Dict[str, Any]] = None,
    *,
    start_path: Optional[str] = None,
) -> ClaudeAPISettings:
    start = Path(start_path) if start_path else None
    project_root = resolve_project_root(start)

    config_data: Dict[str, Any] = {}
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
            "api_key": config_data.get("anthropic_api_key"),
            "auth_token": config_data.get("anthropic_auth_token"),
            "base_url": config_data.get("anthropic_base_url"),
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


class ClaudeAPIClient(LLMClient):
    provider_id = "anthropic_api"

    def __init__(
        self,
        *,
        settings: Optional[ClaudeAPISettings] = None,
        proxy_settings: Optional[ProxySettings] = None,
    ) -> None:
        self._settings = settings or load_claude_settings()
        if not (self._settings.api_key or self._settings.auth_token):
            raise LLMAuthError(
                "Anthropic credentials missing. Provide ANTHROPIC_API_KEY or auth token."
            )

        self._proxy = proxy_settings or load_proxy_settings()
        self._model = _DEFAULT_MODEL

        client_kwargs: Dict[str, Any] = {}
        if self._settings.api_key:
            client_kwargs["api_key"] = self._settings.api_key
        if self._settings.auth_token:
            client_kwargs["auth_token"] = self._settings.auth_token

        base_url = pick_first(
            [
                self._proxy.proxy_url if self._proxy.use_proxy else None,
                self._settings.base_url,
            ]
        )
        if base_url:
            client_kwargs["base_url"] = self._normalize_base_url(base_url)

        # When using proxy, pass auth token via auth flow if provided
        if self._proxy.use_proxy and self._proxy.proxy_token:
            client_kwargs.setdefault("auth_token", self._proxy.proxy_token)

        self._client = anthropic.Anthropic(**client_kwargs)
        self._capabilities = ProviderCapabilities(
            supports_streaming=False,
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
        cached_context: Optional[str] = None,
        conversation_history: Optional[ConversationHistory] = None,
        max_tokens: int = 8_192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        system: List[Dict[str, Any]] = []
        if cached_context:
            system.append(
                {
                    "type": "text",
                    "text": cached_context,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        messages: List[Dict[str, Any]] = []
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

        budget = self._resolve_thinking_budget(thinking_mode, thinking_budget)

        params: Dict[str, Any] = {
            "model": self._model,
            "system": system or None,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if budget > 0:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }

        try:
            response = self._client.messages.create(**params)
        except anthropic.AuthenticationError as exc:  # type: ignore[attr-defined]
            raise LLMAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:  # type: ignore[attr-defined]
            raise LLMRateLimitError(str(exc)) from exc
        except anthropic.APIStatusError as exc:  # type: ignore[attr-defined]
            message = getattr(exc, "message", str(exc))
            raise LLMError(f"Anthropic API error ({exc.status_code}): {message}") from exc
        except anthropic.APIError as exc:  # type: ignore[attr-defined]
            raise LLMError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise LLMError(f"Unexpected Anthropic error: {exc}") from exc

        content, thinking = self._extract_blocks(response)
        usage = UsageStats(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_creation_input_tokens=getattr(response.usage, "cache_creation_input_tokens", 0),
            cache_read_input_tokens=getattr(response.usage, "cache_read_input_tokens", 0),
        )

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response,
            thinking=thinking or None,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_base_url(url: str) -> str:
        clean = url.strip()
        if not clean:
            return clean
        return clean.rstrip("/")

    def _resolve_thinking_budget(self, mode: str, override: Optional[int]) -> int:
        if override is not None:
            return max(0, int(override))
        return _THINKING_MODES.get(mode.lower(), _THINKING_MODES["megathink"])

    @staticmethod
    def _extract_blocks(response: Any) -> tuple[str, str]:
        text = ""
        thinking = ""
        for block in response.content:
            if block.type == "thinking":
                thinking = block.thinking
            elif block.type == "text":
                text = block.text
        return text, thinking


__all__ = [
    "ClaudeAPIClient",
    "load_claude_settings",
    "ClaudeAPISettings",
]
