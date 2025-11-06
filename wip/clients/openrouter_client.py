"""OpenRouter client implementing the shared LLMClient interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

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
    read_env_file,
    read_json_file,
    resolve_project_root,
)
from .proxy import ProxyHttpClient, ProxySettings, load_proxy_settings

_DEFAULT_MODEL = "deepseek/deepseek-chat-v3.1"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(slots=True)
class OpenRouterSettings:
    api_key: Optional[str]
    model: Optional[str]
    base_url: Optional[str]
    site_url: Optional[str]
    app_name: Optional[str]


def load_openrouter_settings(
    config_override: Optional[Dict[str, Any]] = None,
    *,
    start_path: Optional[str] = None,
) -> OpenRouterSettings:
    """Load OpenRouter credentials and configuration.

    Lookup order (highest to lowest priority):
        1. Explicit override dict provided by the caller
        2. Environment variables
        3. `config/config.json`
        4. `.env`
    """

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
            "api_key": "OPENROUTER_API_KEY",
            "model": "OPENROUTER_MODEL",
            "base_url": "OPENROUTER_BASE_URL",
            "site_url": "OPENROUTER_SITE_URL",
            "app_name": "OPENROUTER_APP_NAME",
        },
        config_keys={
            "api_key": config_data.get("openrouter_api_key")
            or config_data.get("deepseek_api_key"),
            "model": config_data.get("openrouter_model")
            or config_data.get("deepseek_model"),
            "base_url": config_data.get("openrouter_base_url"),
            "site_url": config_data.get("openrouter_site_url"),
            "app_name": config_data.get("openrouter_app_name"),
        },
        env_file_keys=env_file_values,
    )

    return OpenRouterSettings(
        api_key=merged.get("api_key"),
        model=merged.get("model"),
        base_url=merged.get("base_url"),
        site_url=merged.get("site_url"),
        app_name=merged.get("app_name"),
    )


class OpenRouterClient(LLMClient):
    """HTTP client that talks to OpenRouter's Chat Completions API."""

    provider_id = "openrouter_api"

    def __init__(
        self,
        *,
        settings: Optional[OpenRouterSettings] = None,
        proxy_settings: Optional[ProxySettings] = None,
        config_override: Optional[Dict[str, Any]] = None,
        rp_dir: Optional[str] = None,
        request_timeout: Optional[int] = 60,
    ) -> None:
        start_path = rp_dir if rp_dir else None

        self._settings = settings or load_openrouter_settings(
            config_override=config_override,
            start_path=start_path,
        )

        if not self._settings.api_key:
            raise LLMAuthError(
                "OpenRouter API key missing. Set OPENROUTER_API_KEY or configure it in settings."
            )

        self._proxy_settings = proxy_settings or load_proxy_settings(
            config_override=config_override,
            start_path=start_path,
        )
        self._http = ProxyHttpClient(self._proxy_settings)

        self._model = self._settings.model or _DEFAULT_MODEL
        self._base_url = (self._settings.base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = request_timeout

        self._base_headers: Dict[str, str] = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

        if self._settings.site_url:
            self._base_headers["HTTP-Referer"] = self._settings.site_url

        if self._settings.app_name:
            self._base_headers["X-Title"] = self._settings.app_name

        # Capability flags: OpenRouter supports streaming, but we only implement
        # standard responses in this prototype.
        self._capabilities = ProviderCapabilities(
            supports_streaming=False,
            supports_prompt_cache=False,
            supports_thinking_budget=False,
            native_system_role=True,
        )

    # ------------------------------------------------------------------ #
    # LLMClient interface
    # ------------------------------------------------------------------ #

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: Optional[str] = None,
        conversation_history: Optional[ConversationHistory] = None,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        top_p: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        stop: Optional[List[str]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        request_timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        messages = self._build_messages(
            cached_context=cached_context,
            conversation_history=conversation_history,
            user_message=user_message,
        )

        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if top_p is not None:
            payload["top_p"] = top_p
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if stop:
            payload["stop"] = stop
        if response_format:
            payload["response_format"] = response_format

        # Allow callers to pass OpenRouter-specific extras via kwargs.
        extra_params = kwargs.get("openrouter_params")
        if isinstance(extra_params, dict):
            payload.update(extra_params)

        timeout = request_timeout or self._timeout

        try:
            response = self._http.post(
                self._base_url,
                headers=self._base_headers,
                json=payload,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise LLMError(
                f"OpenRouter request timed out after {timeout or 'unknown'} seconds"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise LLMError(f"OpenRouter request failed: {exc}") from exc

        if response.status_code == 401:
            raise LLMAuthError("OpenRouter rejected the API key (401 Unauthorized).")
        if response.status_code == 402:
            raise LLMError(
                "OpenRouter returned 402 Payment Required. "
                "Check account balance at https://openrouter.ai/credits."
            )
        if response.status_code == 429:
            raise LLMRateLimitError("OpenRouter rate limit exceeded (429).")
        if response.status_code >= 500:
            raise LLMError(f"OpenRouter service error ({response.status_code}).")

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            detail = self._extract_error_detail(response)
            raise LLMError(f"OpenRouter error: {detail}") from exc

        data = response.json()
        content = self._extract_content(data)
        usage = self._extract_usage(data)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=data,
            thinking=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _build_messages(
        self,
        *,
        cached_context: Optional[str],
        conversation_history: Optional[ConversationHistory],
        user_message: str,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []

        if cached_context:
            messages.append({"role": "system", "content": cached_context})

        if conversation_history:
            for entry in conversation_history:
                if isinstance(entry, ConversationMessage):
                    role, content = entry.role, entry.content
                else:
                    role = entry.get("role")  # type: ignore[assignment]
                    content = entry.get("content")  # type: ignore[assignment]
                if not role or not content:
                    continue
                if role not in {"system", "user", "assistant"}:
                    continue
                messages.append({"role": role, "content": str(content)})

        messages.append({"role": "user", "content": user_message})
        return messages

    def _extract_content(self, data: Dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""

        first = choices[0]
        message = first.get("message")

        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                aggregated = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            aggregated.append(text)
                    elif isinstance(block, str):
                        aggregated.append(block)
                return "".join(aggregated)

        # Some providers return `text` fields instead of message dicts.
        text_value = first.get("text")
        if isinstance(text_value, str):
            return text_value

        return ""

    def _extract_usage(self, data: Dict[str, Any]) -> UsageStats:
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}

        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0

        return UsageStats(
            input_tokens=int(prompt_tokens) if isinstance(prompt_tokens, int) else 0,
            output_tokens=int(completion_tokens) if isinstance(completion_tokens, int) else 0,
        )

    def _extract_error_detail(self, response: requests.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text

        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
        elif isinstance(error, str):
            return error
        return response.text


__all__ = [
    "OpenRouterClient",
    "OpenRouterSettings",
    "load_openrouter_settings",
]
