"""WIP OpenAI chat client mirroring the Claude API client contract."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from pathlib import Path


def _resolve_env(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return None


class OpenAIChatClient:
    """Prototype OpenAI client following the Claude API interface."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_behavior: str = "system_prompt"
    ) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required for OpenAIChatClient; install openai>=1.0"
            ) from exc

        resolved_key = (api_key or _resolve_env("OPENAI_API_KEY", "OPENAI_TOKEN"))
        if not resolved_key:
            raise ValueError("OpenAI API key required via OPENAI_API_KEY or constructor")

        resolved_model = (
            model
            or _resolve_env("OPENAI_MODEL", "OPENAI_CHAT_MODEL")
            or "gpt-4.1"
        )

        client_kwargs: Dict[str, Any] = {"api_key": resolved_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        else:
            env_base = _resolve_env("OPENAI_API_BASE", "OPENAI_BASE_URL")
            if env_base:
                client_kwargs["base_url"] = env_base

        self._client = OpenAI(**client_kwargs)
        self._model = resolved_model
        self._cache_behavior = cache_behavior

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
    ) -> Dict[str, Any]:
        from openai import APIError  # type: ignore

        messages: List[Dict[str, str]] = []

        if cached_context:
            system_content = cached_context
            messages.append({"role": "system", "content": system_content})

        if conversation_history:
            for item in conversation_history:
                role = item.get("role")
                content = item.get("content")
                if role in {"user", "assistant", "system"} and isinstance(content, str):
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        params: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": temperature,
        }

        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty

        try:
            response = self._client.chat.completions.create(**params)
        except APIError as exc:
            # TODO: map specific error codes (rate_limit, auth) to friendly text
            raise

        # Extract primary assistant message
        message_content = ""
        if response.choices:
            primary_choice = response.choices[0]
            if primary_choice.message and primary_choice.message.content:
                message_content = primary_choice.message.content

        usage_data = response.usage or {}
        mapped_usage = {
            "input_tokens": usage_data.get("prompt_tokens", 0),
            "output_tokens": usage_data.get("completion_tokens", 0),
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }

        return {
            "content": message_content,
            "thinking": None,
            "usage": mapped_usage,
            "raw_response": response,
        }


def load_openai_settings(config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Optional[str]]:
    """WIP settings loader replicating load_api_settings semantics."""

    # TODO: share logic with final config loader; for now follow same precedence.
    base_dir = Path(__file__).parent.parent
    config_data: Dict[str, Any] = {}

    if config_override:
        config_data.update(config_override)
    else:
        config_file = base_dir / "config" / "config.json"
        if config_file.exists():
            try:
                with config_file.open("r", encoding="utf-8") as fp:
                    config_data.update(json.load(fp))
            except Exception as exc:
                print(f"??  Failed to read config/config.json: {exc}")

    env_values: Dict[str, str] = {}
    env_file = base_dir / ".env"
    if env_file.exists():
        try:
            with env_file.open("r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    env_values[key.strip()] = value.strip()
        except Exception as exc:
            print(f"??  Failed to read .env file: {exc}")

    def pick(*options: Optional[str]) -> Optional[str]:
        for opt in options:
            if opt:
                trimmed = opt.strip()
                if trimmed:
                    return trimmed
        return None

    api_key = pick(
        os.environ.get("OPENAI_API_KEY"),
        config_data.get("openai_api_key"),
        env_values.get("OPENAI_API_KEY"),
    )

    model = pick(
        os.environ.get("OPENAI_MODEL"),
        config_data.get("openai_model"),
        env_values.get("OPENAI_MODEL"),
    )

    api_base = pick(
        os.environ.get("OPENAI_API_BASE"),
        config_data.get("openai_api_base"),
        env_values.get("OPENAI_API_BASE"),
    )

    return {
        "api_key": api_key,
        "model": model,
        "api_base": api_base,
    }
