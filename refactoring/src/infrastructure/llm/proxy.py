"""Proxy utilities aligned with the refactored infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...shared.models import ProxySettings
from .config_utils import (
    merge_config_sources,
    read_env_file,
    read_json_file,
    resolve_project_root,
)


def load_proxy_settings(
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> ProxySettings:
    """Load proxy configuration from env/config/.env using shared helpers."""

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
            "proxy_url": "PROXY_URL",
            "proxy_token": "PROXY_TOKEN",
        },
        config_keys={
            "proxy_url": config_data.get("proxy_url") or config_data.get("anthropic_proxy_url"),
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


__all__ = [
    "ProxySettings",
    "load_proxy_settings",
]
