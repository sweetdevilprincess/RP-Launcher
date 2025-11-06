"""OpenRouter client implementing the shared LLMClient interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...shared.interfaces import (
    LoggingService,
    Transport,
    TransportError,
    TransportRequest,
    TransportResponse,
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
    UsageStats,
)
from .config_utils import (
    merge_config_sources,
    read_env_file,
    read_json_file,
    resolve_project_root,
)
from .proxy import ProxySettings, load_proxy_settings

_DEFAULT_MODEL = "deepseek/deepseek-chat-v3.1"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(slots=True)
class OpenRouterSettings:
    api_key: str | None
    model: str | None
    base_url: str | None
    site_url: str | None
    app_name: str | None


def load_openrouter_settings(
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> OpenRouterSettings:
    """Load OpenRouter credentials and configuration."""

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
            "api_key": "OPENROUTER_API_KEY",
            "model": "OPENROUTER_MODEL",
            "base_url": "OPENROUTER_BASE_URL",
            "site_url": "OPENROUTER_SITE_URL",
            "app_name": "OPENROUTER_APP_NAME",
        },
        config_keys={
            "api_key": config_data.get("api_key") or config_data.get("openrouter_api_key"),
            "model": config_data.get("model") or config_data.get("openrouter_model"),
            "base_url": config_data.get("base_url") or config_data.get("openrouter_base_url"),
            "site_url": config_data.get("site_url") or config_data.get("openrouter_site_url"),
            "app_name": config_data.get("app_name") or config_data.get("openrouter_app_name"),
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
        settings: OpenRouterSettings | None = None,
        proxy_settings: ProxySettings | None = None,
        transport: Transport | None = None,
        logger: LoggingService | None = None,
        config_override: dict[str, Any] | None = None,
        rp_dir: str | None = None,
        request_timeout: int | None = 60,
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

        base_transport: Transport = transport or RequestsTransport()
        base_transport = ProxyTransport(base_transport, proxy_config=self._proxy_settings)
        if logger is not None:
            base_transport = LoggingTransport(base_transport, logger, name="openrouter")
        self._transport = base_transport
        self._logger = logger

        self._model = self._settings.model or _DEFAULT_MODEL
        self._base_url = (self._settings.base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = request_timeout

        self._base_headers: dict[str, str] = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }

        if self._settings.site_url:
            self._base_headers["HTTP-Referer"] = self._settings.site_url

        if self._settings.app_name:
            self._base_headers["X-Title"] = self._settings.app_name

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
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.8,
        top_p: float | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        stop: list[str] | None = None,
        response_format: dict[str, Any] | None = None,
        request_timeout: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        messages = self._build_messages(
            cached_context=cached_context,
            conversation_history=conversation_history,
            user_message=user_message,
        )

        payload: dict[str, Any] = {
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

        extra_params = kwargs.get("openrouter_params")
        if isinstance(extra_params, dict):
            payload.update(extra_params)

        timeout = request_timeout or self._timeout

        try:
            response = self._transport.post(
                TransportRequest(
                    endpoint=self._base_url,
                    payload=payload,
                    headers=self._base_headers,
                    timeout_seconds=timeout,
                )
            )
        except TransportError as exc:
            raise LLMError(f"OpenRouter request failed: {exc}") from exc

        self._handle_http_errors(response)

        body = response.body
        if not isinstance(body, dict):
            raise LLMError("OpenRouter returned unexpected response format")

        content = self._extract_content(body)
        usage = self._extract_usage(body)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=body,
            thinking=None,
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _handle_http_errors(self, response: TransportResponse) -> None:
        status = response.status_code
        if status == 401:
            raise LLMAuthError("OpenRouter rejected the API key (401 Unauthorized).")
        if status == 402:
            raise LLMError(
                "OpenRouter returned 402 Payment Required. "
                "Check account balance at https://openrouter.ai/credits."
            )
        if status == 429:
            raise LLMRateLimitError("OpenRouter rate limit exceeded (429).")
        if status >= 500:
            raise LLMError(f"OpenRouter service error ({status}).")
        if status >= 400:
            detail = self._extract_error_detail(response)
            raise LLMError(f"OpenRouter error ({status}): {detail}")

    def _build_messages(
        self,
        *,
        cached_context: str | None,
        conversation_history: ConversationHistory | None,
        user_message: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []

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

    def _extract_content(self, data: dict[str, Any]) -> str:
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
                aggregated: list[str] = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            aggregated.append(text)
                    elif isinstance(block, str):
                        aggregated.append(block)
                return "".join(aggregated)

        text_value = first.get("text")
        if isinstance(text_value, str):
            return text_value

        return ""

    def _extract_usage(self, data: dict[str, Any]) -> UsageStats:
        usage = data.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}

        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0

        return UsageStats(
            input_tokens=int(prompt_tokens) if isinstance(prompt_tokens, int) else 0,
            output_tokens=int(completion_tokens) if isinstance(completion_tokens, int) else 0,
        )

    def _extract_error_detail(self, response: TransportResponse) -> str:
        body = response.body
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict):
                message = error.get("message")
                if isinstance(message, str):
                    return message
            elif isinstance(error, str):
                return error
            return str(body)
        if isinstance(body, str):
            return body
        return str(body)


__all__ = [
    "OpenRouterClient",
    "OpenRouterSettings",
    "load_openrouter_settings",
]
