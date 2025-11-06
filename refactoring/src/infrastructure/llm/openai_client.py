"""OpenAI chat client implementing the shared LLMClient interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

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
class OpenAISettings:
    api_key: str | None
    model: str | None
    api_base: str | None
    organization: str | None = None


_DEFAULT_MODEL = "gpt-4.1"
_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_RESPONSES_ENDPOINT = "/responses"
_CHAT_COMPLETIONS_ENDPOINT = "/chat/completions"

EndpointType = Literal["responses", "chat_completions"]


@dataclass(frozen=True, slots=True)
class OpenAIModelConfig:
    name: str
    endpoint: EndpointType
    description: str = ""

    def supports_responses(self) -> bool:
        return self.endpoint == "responses"


_KNOWN_MODEL_CONFIGS: list[OpenAIModelConfig] = [
    OpenAIModelConfig(
        name="gpt-4.1",
        endpoint="responses",
        description="Flagship reasoning model (Responses API)",
    ),
    OpenAIModelConfig(
        name="gpt-4.1-mini",
        endpoint="responses",
        description="Fast lightweight GPT-4.1 variant (Responses API)",
    ),
    OpenAIModelConfig(
        name="gpt-4o",
        endpoint="responses",
        description="GPT-4o multimodal model (Responses API)",
    ),
    OpenAIModelConfig(
        name="gpt-4o-mini",
        endpoint="chat_completions",
        description="Cost-efficient GPT-4o mini (Chat Completions API)",
    ),
    OpenAIModelConfig(
        name="o4-mini",
        endpoint="responses",
        description="Optimized reasoning preview (Responses API)",
    ),
    OpenAIModelConfig(
        name="o3-mini",
        endpoint="responses",
        description="Reasoning model preview (Responses API)",
    ),
    OpenAIModelConfig(
        name="gpt-3.5-turbo",
        endpoint="chat_completions",
        description="Legacy GPT-3.5 model (Chat Completions API)",
    ),
]

_MODEL_REGISTRY: dict[str, OpenAIModelConfig] = {
    cfg.name.lower(): cfg for cfg in _KNOWN_MODEL_CONFIGS
}
_RESPONSES_PREFIXES: tuple[str, ...] = (
    "gpt-4.1",
    "gpt-4o",
    "o4",
    "o3",
)


def resolve_model_config(model_name: str) -> OpenAIModelConfig:
    key = (model_name or "").strip()
    if not key:
        key = _DEFAULT_MODEL
    lookup = _MODEL_REGISTRY.get(key.lower())
    if lookup:
        return lookup
    if key.lower().startswith(_RESPONSES_PREFIXES):
        return OpenAIModelConfig(name=key, endpoint="responses")
    return OpenAIModelConfig(name=key, endpoint="chat_completions")


def list_known_models() -> list[OpenAIModelConfig]:
    return list(_MODEL_REGISTRY.values())


def load_openai_settings(
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> OpenAISettings:
    """Load OpenAI credentials/config from env, config.json, and .env."""

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
            "api_key": "OPENAI_API_KEY",
            "model": "OPENAI_MODEL",
            "api_base": "OPENAI_API_BASE",
            "organization": "OPENAI_ORGANIZATION",
        },
        config_keys={
            "api_key": config_data.get("api_key") or config_data.get("openai_api_key"),
            "model": config_data.get("model") or config_data.get("openai_model"),
            "api_base": config_data.get("api_base") or config_data.get("openai_api_base"),
            "organization": config_data.get("organization") or config_data.get("openai_organization"),
        },
        env_file_keys=env_file_values,
    )

    return OpenAISettings(
        api_key=merged.get("api_key"),
        model=merged.get("model"),
        api_base=merged.get("api_base"),
        organization=merged.get("organization"),
    )


class OpenAIChatClient(LLMClient):
    """HTTP client that talks to OpenAI's Responses and Chat Completions APIs using Transport abstraction."""

    provider_id = "openai_api"

    def __init__(
        self,
        *,
        settings: OpenAISettings | None = None,
        proxy_settings: ProxySettings | None = None,
        transport: Transport | None = None,
        logger: LoggingService | None = None,
        config_override: dict[str, Any] | None = None,
        rp_dir: str | None = None,
        request_timeout: int | None = 120,
    ) -> None:
        start_path = rp_dir if rp_dir else None

        self._settings = settings or load_openai_settings(
            config_override=config_override,
            start_path=start_path,
        )

        if not self._settings.api_key:
            raise LLMAuthError(
                "OpenAI API key missing. Set OPENAI_API_KEY or configure in settings."
            )

        self._proxy_settings = proxy_settings or load_proxy_settings(
            config_override=config_override,
            start_path=start_path,
        )

        # Build transport chain: Base → Proxy → Logging
        base_transport: Transport = transport or RequestsTransport()
        base_transport = ProxyTransport(base_transport, proxy_config=self._proxy_settings)
        if logger is not None:
            base_transport = LoggingTransport(base_transport, logger, name="openai")
        self._transport = base_transport
        self._logger = logger

        self._model = self._settings.model or _DEFAULT_MODEL
        self._model_config = resolve_model_config(self._model)
        self._base_url = (self._settings.api_base or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = request_timeout

        # Build base headers
        self._base_headers: dict[str, str] = {
            "authorization": f"Bearer {self._settings.api_key}",
            "content-type": "application/json",
            "openai-beta": "assistants=v2",
        }

        if self._settings.organization:
            self._base_headers["openai-organization"] = self._settings.organization

        self._capabilities = ProviderCapabilities(
            supports_streaming=False,
            supports_prompt_cache=False,
            supports_thinking_budget=False,
            native_system_role=True,
        )

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        request_timeout: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        model_override = kwargs.pop("model", None)
        active_config = (
            resolve_model_config(model_override) if model_override else self._model_config
        )
        timeout = request_timeout or self._timeout

        messages = self._build_messages(
            cached_context=cached_context,
            conversation_history=conversation_history,
            user_message=user_message,
        )

        if active_config.endpoint == "responses":
            return self._send_via_responses(
                model=active_config.name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                timeout=timeout,
            )

        return self._send_via_chat_completions(
            model=active_config.name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            timeout=timeout,
        )

    # ---------------------------------------------------------------------
    # Endpoint dispatchers
    # ---------------------------------------------------------------------

    def _send_via_responses(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: float | None,
        frequency_penalty: float | None,
        presence_penalty: float | None,
        timeout: int | None,
    ) -> LLMResponse:
        """Send request to OpenAI Responses API."""
        payload: dict[str, Any] = {
            "model": model,
            "input": self._convert_to_responses_input(messages),
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty

        # Make request via transport
        request = TransportRequest(
            endpoint=f"{self._base_url}{_RESPONSES_ENDPOINT}",
            payload=payload,
            headers=self._base_headers,
            timeout_seconds=timeout or self._timeout,
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
            raise LLMError(f"OpenAI API error ({transport_response.status_code}): {error_msg}")

        # Parse successful response
        response_data = transport_response.body
        if not isinstance(response_data, dict):
            raise LLMError(f"Unexpected response format: {type(response_data)}")

        content = self._extract_responses_content_from_dict(response_data)
        usage = self._extract_responses_usage_from_dict(response_data)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response_data,
            thinking=None,
        )

    def _send_via_chat_completions(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: float | None,
        frequency_penalty: float | None,
        presence_penalty: float | None,
        timeout: int | None,
    ) -> LLMResponse:
        """Send request to OpenAI Chat Completions API."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty

        # Make request via transport
        request = TransportRequest(
            endpoint=f"{self._base_url}{_CHAT_COMPLETIONS_ENDPOINT}",
            payload=payload,
            headers=self._base_headers,
            timeout_seconds=timeout or self._timeout,
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
            raise LLMError(f"OpenAI API error ({transport_response.status_code}): {error_msg}")

        # Parse successful response
        response_data = transport_response.body
        if not isinstance(response_data, dict):
            raise LLMError(f"Unexpected response format: {type(response_data)}")

        content = self._extract_chat_content_from_dict(response_data)
        usage = self._extract_chat_usage_from_dict(response_data)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response_data,
            thinking=None,
        )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

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

    def _convert_to_responses_input(self, messages: list[dict[str, str]]) -> list[dict[str, Any]]:
        return [
            {
                "role": message["role"],
                "content": [
                    {
                        "type": "text",
                        "text": message["content"],
                    }
                ],
            }
            for message in messages
        ]

    def _extract_responses_content_from_dict(self, response_data: dict[str, Any]) -> str:
        """Extract content from Responses API response."""
        output = response_data.get("output", [])
        if not output:
            return ""

        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue

            content_blocks = item.get("content", [])
            text_blocks = [
                block.get("text", "")
                for block in content_blocks
                if isinstance(block, dict) and block.get("type") == "output_text"
            ]
            if text_blocks:
                return "".join(text_blocks)

        return ""

    def _extract_responses_usage_from_dict(self, response_data: dict[str, Any]) -> UsageStats:
        """Extract usage from Responses API response."""
        usage = response_data.get("usage", {})
        return UsageStats(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

    def _extract_chat_content_from_dict(self, response_data: dict[str, Any]) -> str:
        """Extract content from Chat Completions API response."""
        choices = response_data.get("choices", [])
        if not choices:
            return ""

        primary = choices[0]
        if not isinstance(primary, dict):
            return ""

        message = primary.get("message", {})
        if not isinstance(message, dict):
            return ""

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))

        return ""

    def _extract_chat_usage_from_dict(self, response_data: dict[str, Any]) -> UsageStats:
        """Extract usage from Chat Completions API response."""
        usage = response_data.get("usage", {})
        if not usage:
            return UsageStats.empty()

        return UsageStats(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

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
    "OpenAIChatClient",
    "OpenAIModelConfig",
    "OpenAISettings",
    "list_known_models",
    "load_openai_settings",
    "resolve_model_config",
]
