"""OpenAI chat client implementing the shared LLMClient interface (WIP)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

try:
    import openai  # type: ignore
    from openai import OpenAI  # type: ignore
except ImportError as exc:  # pragma: no cover - import guard for dev envs
    raise RuntimeError(
        "openai package is required for OpenAIChatClient; install openai>=1.0"
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
class OpenAISettings:
    api_key: Optional[str]
    model: Optional[str]
    api_base: Optional[str]
    organization: Optional[str] = None


_DEFAULT_MODEL = "gpt-4.1"
EndpointType = Literal["responses", "chat_completions"]


@dataclass(frozen=True, slots=True)
class OpenAIModelConfig:
    name: str
    endpoint: EndpointType
    description: str = ""

    def supports_responses(self) -> bool:
        return self.endpoint == "responses"


_KNOWN_MODEL_CONFIGS: List[OpenAIModelConfig] = [
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

_MODEL_REGISTRY: Dict[str, OpenAIModelConfig] = {
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


def list_known_models() -> List[OpenAIModelConfig]:
    return list(_MODEL_REGISTRY.values())


def load_openai_settings(
    config_override: Optional[Dict[str, Any]] = None,
    *,
    start_path: Optional[str] = None,
) -> OpenAISettings:
    """Load OpenAI credentials/config from env, config.json, and .env."""

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
            "api_key": "OPENAI_API_KEY",
            "model": "OPENAI_MODEL",
            "api_base": "OPENAI_API_BASE",
            "organization": "OPENAI_ORGANIZATION",
        },
        config_keys={
            "api_key": config_data.get("openai_api_key"),
            "model": config_data.get("openai_model"),
            "api_base": config_data.get("openai_api_base"),
            "organization": config_data.get("openai_organization"),
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
    provider_id = "openai_api"

    def __init__(
        self,
        *,
        settings: Optional[OpenAISettings] = None,
        proxy_settings: Optional[ProxySettings] = None,
        rp_dir: Optional[str] = None,
        request_timeout: Optional[int] = 120,
    ) -> None:
        start_path = rp_dir if rp_dir else None
        self._settings = settings or load_openai_settings(start_path=start_path)
        if not self._settings.api_key:
            raise LLMAuthError(
                "OpenAI API key missing. Set OPENAI_API_KEY or configure in settings."
            )

        self._proxy = proxy_settings or load_proxy_settings(start_path=start_path)
        self._model = self._settings.model or _DEFAULT_MODEL
        self._model_config = resolve_model_config(self._model)
        self._timeout = request_timeout

        client_kwargs: Dict[str, Any] = {
            "api_key": self._settings.api_key,
        }

        if self._settings.organization:
            client_kwargs["organization"] = self._settings.organization

        base_url = pick_first(
            [
                self._proxy.proxy_url if self._proxy.use_proxy else None,
                self._settings.api_base,
            ]
        )
        if base_url:
            client_kwargs["base_url"] = base_url.rstrip("/")

        default_headers: Dict[str, str] = {
            "OpenAI-Beta": "assistants=v2",
        }
        if self._proxy.use_proxy and self._proxy.proxy_token:
            default_headers["X-Proxy-Authorization"] = f"Bearer {self._proxy.proxy_token}"

        client_kwargs["default_headers"] = default_headers

        self._client = OpenAI(**client_kwargs)
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
        cached_context: Optional[str] = None,
        conversation_history: Optional[ConversationHistory] = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        request_timeout: Optional[int] = None,
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
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
        frequency_penalty: Optional[float],
        presence_penalty: Optional[float],
        timeout: Optional[int],
    ) -> LLMResponse:
        params: Dict[str, Any] = {
            "model": model,
            "input": self._convert_to_responses_input(messages),
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty

        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = self._client.responses.create(**params)
        except openai.AuthenticationError as exc:  # type: ignore[attr-defined]
            raise LLMAuthError(str(exc)) from exc
        except openai.RateLimitError as exc:  # type: ignore[attr-defined]
            raise LLMRateLimitError(str(exc)) from exc
        except openai.APIConnectionError as exc:  # type: ignore[attr-defined]
            raise LLMError(f"OpenAI connection error: {exc}") from exc
        except openai.APIStatusError as exc:  # type: ignore[attr-defined]
            message = getattr(exc, "message", str(exc))
            raise LLMError(f"OpenAI API error ({exc.status_code}): {message}") from exc
        except openai.APIError as exc:  # type: ignore[attr-defined]
            raise LLMError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - fallback for unexpected errors
            raise LLMError(f"Unexpected OpenAI error: {exc}") from exc

        content = self._extract_responses_content(response)
        usage = self._extract_responses_usage(response)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response,
            thinking=None,
        )

    def _send_via_chat_completions(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: Optional[float],
        frequency_penalty: Optional[float],
        presence_penalty: Optional[float],
        timeout: Optional[int],
    ) -> LLMResponse:
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if timeout is not None:
            params["timeout"] = timeout

        try:
            response = self._client.chat.completions.create(**params)
        except openai.AuthenticationError as exc:  # type: ignore[attr-defined]
            raise LLMAuthError(str(exc)) from exc
        except openai.RateLimitError as exc:  # type: ignore[attr-defined]
            raise LLMRateLimitError(str(exc)) from exc
        except openai.APIConnectionError as exc:  # type: ignore[attr-defined]
            raise LLMError(f"OpenAI connection error: {exc}") from exc
        except openai.APIStatusError as exc:  # type: ignore[attr-defined]
            message = getattr(exc, "message", str(exc))
            raise LLMError(f"OpenAI API error ({exc.status_code}): {message}") from exc
        except openai.APIError as exc:  # type: ignore[attr-defined]
            raise LLMError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - fallback for unexpected errors
            raise LLMError(f"Unexpected OpenAI error: {exc}") from exc

        content = self._extract_chat_content(response)
        usage = self._extract_chat_usage(response)

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response=response,
            thinking=None,
        )

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

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

    def _convert_to_responses_input(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
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

    def _extract_responses_content(self, response: Any) -> str:
        output = getattr(response, "output", None)
        if not output:
            return ""
        for item in output:
            if item.get("type") != "message":
                continue
            text_blocks = [
                block.get("text", "")
                for block in item.get("content", [])
                if block.get("type") == "output_text"
            ]
            if text_blocks:
                return "".join(text_blocks)
        return ""

    def _extract_responses_usage(self, response: Any) -> UsageStats:
        usage = getattr(response, "usage", None) or {}
        return UsageStats(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

    def _extract_chat_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None)
        if not choices:
            return ""
        primary = choices[0]
        message = getattr(primary, "message", None)
        if not message:
            return ""
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return ""

    def _extract_chat_usage(self, response: Any) -> UsageStats:
        usage = getattr(response, "usage", None)
        if not usage:
            return UsageStats.empty()

        def _read_usage_field(name: str) -> int:
            value = getattr(usage, name, None)
            if value is None and isinstance(usage, dict):
                value = usage.get(name)
            return int(value or 0)

        return UsageStats(
            input_tokens=_read_usage_field("prompt_tokens"),
            output_tokens=_read_usage_field("completion_tokens"),
        )


__all__ = [
    "OpenAIChatClient",
    "load_openai_settings",
    "OpenAISettings",
    "OpenAIModelConfig",
    "list_known_models",
    "resolve_model_config",
]
