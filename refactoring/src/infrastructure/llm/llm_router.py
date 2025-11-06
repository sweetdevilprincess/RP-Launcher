"""LLM Router - Provider-agnostic routing for primary and secondary LLM calls.

This module provides abstraction functions for routing LLM calls to the appropriate
provider (primary or secondary) based on the configuration.

The router is completely provider-agnostic - it works with ANY LLM provider that
implements the LLMClient interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import ConversationHistory, LLMResponse

if TYPE_CHECKING:
    from ...presentation.bridge.bridge_service import BridgeService


def call_primary_llm(
    bridge: "BridgeService",
    user_message: str,
    *,
    cached_context: str | None = None,
    conversation_history: ConversationHistory | None = None,
    **kwargs
) -> LLMResponse:
    """Call the primary LLM for main conversation.

    Provider-agnostic: works with ANY provider configured as primary
    (Claude SDK, OpenRouter, OpenAI, etc.).

    Args:
        bridge: Bridge service instance with primary_client
        user_message: The user's message
        cached_context: Optional context to cache (TIER_1 files)
        conversation_history: Optional conversation history
        **kwargs: Additional provider-specific arguments

    Returns:
        LLM response from primary provider

    Raises:
        RuntimeError: If no primary LLM is configured
    """
    if not bridge.primary_client:
        raise RuntimeError("No primary LLM configured")

    return bridge.primary_client.send_message(
        user_message=user_message,
        cached_context=cached_context,
        conversation_history=conversation_history,
        **kwargs
    )


def call_secondary_llm(
    bridge: "BridgeService",
    user_message: str,
    *,
    cached_context: str | None = None,
    **kwargs
) -> LLMResponse:
    """Call the secondary LLM for automation agents.

    Provider-agnostic: works with ANY provider configured as secondary.

    Routing logic:
    - If use_secondary_for_automation is False, routes to primary
    - If secondary_provider is empty, routes to primary
    - Otherwise, uses secondary client

    This allows single-key mode (everything uses primary) OR dual-provider
    mode (automation uses different provider/model).

    Args:
        bridge: Bridge service instance with primary_client and secondary_client
        user_message: The user's message (automation prompt)
        cached_context: Optional context to cache
        **kwargs: Additional provider-specific arguments

    Returns:
        LLM response from secondary provider (or primary if routing to primary)

    Raises:
        RuntimeError: If no LLM is configured
    """
    # Check routing configuration
    use_secondary = bridge.llm_routing.get("use_secondary_for_automation", False)

    if not use_secondary or not bridge.secondary_client:
        # Route to primary (single-provider mode)
        return call_primary_llm(bridge, user_message, cached_context=cached_context, **kwargs)

    # Use secondary client (dual-provider mode)
    return bridge.secondary_client.send_message(
        user_message=user_message,
        cached_context=cached_context,
        **kwargs
    )


__all__ = [
    "call_primary_llm",
    "call_secondary_llm",
]
