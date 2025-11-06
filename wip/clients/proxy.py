"""Proxy utilities aligned with the new LLM client abstractions (WIP)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .config_utils import (
    merge_config_sources,
    read_env_file,
    read_json_file,
    resolve_project_root,
)


@dataclass(slots=True)
class ProxySettings:
    proxy_url: Optional[str]
    proxy_token: Optional[str]
    use_proxy: bool


def load_proxy_settings(
    config_override: Optional[Dict[str, Any]] = None,
    *,
    start_path: Optional[str] = None,
) -> ProxySettings:
    """Load proxy configuration from env/config/.env using shared helpers."""

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
            "proxy_url": "PROXY_URL",
            "proxy_token": "PROXY_TOKEN",
        },
        config_keys={
            "proxy_url": config_data.get("proxy_url")
            or config_data.get("anthropic_proxy_url"),
            "proxy_token": config_data.get("proxy_token")
            or config_data.get("anthropic_proxy_token"),
        },
        env_file_keys=env_file_values,
    )

    # Fallback to legacy Anthropics env vars when PROXY_URL/TOKEN not set
    proxy_url = merged.get("proxy_url") or env_file_values.get("ANTHROPIC_PROXY_URL")
    proxy_token = merged.get("proxy_token") or env_file_values.get("ANTHROPIC_PROXY_TOKEN")

    use_proxy = False
    if config_override and "use_proxy" in config_override:
        use_proxy = bool(config_override["use_proxy"])
    else:
        use_proxy = bool(config_data.get("use_proxy"))

    return ProxySettings(
        proxy_url=proxy_url,
        proxy_token=proxy_token,
        use_proxy=use_proxy and bool(proxy_url),
    )


class ProxyHttpClient:
    """Requests wrapper that injects proxy headers and URL overrides."""

    def __init__(self, settings: ProxySettings) -> None:
        self.settings = settings

    def post(
        self,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> requests.Response:
        target_url = self.settings.proxy_url if self.settings.use_proxy else url
        out_headers = dict(headers or {})

        if self.settings.use_proxy and self.settings.proxy_token:
            out_headers.setdefault(
                "X-Proxy-Authorization",
                f"Bearer {self.settings.proxy_token}"
            )

        return requests.post(
            target_url,
            headers=out_headers,
            json=json,
            timeout=timeout,
            **kwargs,
        )

    def is_enabled(self) -> bool:
        return self.settings.use_proxy


__all__ = [
    "ProxySettings",
    "load_proxy_settings",
    "ProxyHttpClient",
]
