"""Provider registry skeleton for multi-LLM support."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .base import LLMClient
from .claude_api_client import ClaudeAPIClient, ClaudeAPISettings, load_claude_settings
from .claude_sdk_client import ClaudeSDKStreamingClient
from .openai_client import OpenAIChatClient, OpenAISettings, load_openai_settings
from .openrouter_client import (
    OpenRouterClient,
    OpenRouterSettings,
    load_openrouter_settings,
)
from .proxy import ProxySettings, load_proxy_settings

ProviderFactory = Callable[[dict[str, Any]], LLMClient]


@dataclass(slots=True)
class ProviderSpec:
    provider_id: str
    label: str
    supports_streaming: bool
    factory: ProviderFactory
    description: str = ""


_registry: dict[str, ProviderSpec] = {}


def register_provider(spec: ProviderSpec) -> None:
    _registry[spec.provider_id] = spec


def get_provider(provider_id: str) -> ProviderSpec | None:
    return _registry.get(provider_id)


def list_providers() -> dict[str, ProviderSpec]:
    return dict(_registry)


# ---------------------------------------------------------------------------
# Provider factories
# ---------------------------------------------------------------------------


def _sdk_factory(config: dict[str, Any]) -> LLMClient:
    rp_dir = config.get("rp_dir")
    project_root = config.get("project_root")
    return ClaudeSDKStreamingClient(rp_dir=rp_dir, project_root=project_root)


def _api_factory(config: dict[str, Any]) -> LLMClient:
    settings: ClaudeAPISettings = load_claude_settings(config_override=config)
    proxy_settings: ProxySettings = load_proxy_settings(config_override=config)
    return ClaudeAPIClient(
        settings=settings,
        proxy_settings=proxy_settings,
        config_override=config,
        rp_dir=config.get("rp_dir"),
    )


def _openai_factory(config: dict[str, Any]) -> LLMClient:
    settings: OpenAISettings = load_openai_settings(config_override=config)
    proxy_settings: ProxySettings = load_proxy_settings(config_override=config)
    return OpenAIChatClient(
        settings=settings,
        proxy_settings=proxy_settings,
        config_override=config,
        rp_dir=config.get("rp_dir"),
    )


def _openrouter_factory(config: dict[str, Any]) -> LLMClient:
    settings: OpenRouterSettings = load_openrouter_settings(config_override=config)
    proxy_settings: ProxySettings = load_proxy_settings(config_override=config)
    return OpenRouterClient(
        settings=settings,
        proxy_settings=proxy_settings,
        config_override=config,
        rp_dir=config.get("rp_dir"),
    )


register_provider(
    ProviderSpec(
        provider_id="claude_sdk_client",
        label="Claude SDK",
        supports_streaming=True,
        factory=_sdk_factory,
        description="High-performance Claude SDK bridge (Node)",
    )
)

register_provider(
    ProviderSpec(
        provider_id="claude_api_client",
        label="Claude API",
        supports_streaming=False,
        factory=_api_factory,
        description="Anthropic API with prompt caching",
    )
)

register_provider(
    ProviderSpec(
        provider_id="openai_client",
        label="OpenAI API",
        supports_streaming=False,
        factory=_openai_factory,
        description="OpenAI Responses API (GPT-4.1 / GPT-4o)",
    )
)

register_provider(
    ProviderSpec(
        provider_id="openrouter_client",
        label="OpenRouter API",
        supports_streaming=False,
        factory=_openrouter_factory,
        description="OpenRouter multi-model gateway (DeepSeek, Mistral, etc.)",
    )
)


__all__ = [
    "ProviderSpec",
    "get_provider",
    "list_providers",
    "register_provider",
]
