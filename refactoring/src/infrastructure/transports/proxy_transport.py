"""Proxy-aware transport that decorates another transport implementation."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path

from ...shared.interfaces import Transport, TransportRequest, TransportResponse
from ...shared.models import ProxySettings


def load_proxy_config(rp_dir: str | Path | None = None) -> ProxySettings:
    """Load proxy configuration from env vars and optional config file.

    Args:
        rp_dir: Optional directory to search for config.json

    Returns:
        ProxySettings with merged configuration from env vars and file
    """

    proxy_url = os.environ.get("PROXY_URL") or os.environ.get("ANTHROPIC_PROXY_URL")
    proxy_token = os.environ.get("PROXY_TOKEN") or os.environ.get("ANTHROPIC_PROXY_TOKEN")
    use_proxy = False

    config_path = _find_config_json(rp_dir)
    if config_path and config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config = {}
        proxy_url = proxy_url or config.get("proxy_url") or config.get("anthropic_proxy_url")
        proxy_token = (
            proxy_token or config.get("proxy_token") or config.get("anthropic_proxy_token")
        )
        use_proxy = config.get("use_proxy", False)

    return ProxySettings(
        proxy_url=proxy_url,
        proxy_token=proxy_token,
        use_proxy=use_proxy,
    )


def _find_config_json(rp_dir: str | Path | None) -> Path | None:
    if rp_dir:
        candidate = Path(rp_dir) / "config.json"
        if candidate.exists():
            return candidate

    cwd_candidate = Path.cwd() / "config.json"
    if cwd_candidate.exists():
        return cwd_candidate

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config.json"
        if candidate.exists():
            return candidate
    return None


class ProxyTransport(Transport):
    """Routes requests through a proxy when configured.

    Decorator that wraps another transport to route requests through a proxy
    when proxy settings are enabled.

    Args:
        transport: The underlying transport to wrap
        rp_dir: Optional directory to search for config.json
        proxy_config: Optional explicit proxy settings (overrides file/env)
    """

    def __init__(
        self,
        transport: Transport,
        *,
        rp_dir: str | Path | None = None,
        proxy_config: ProxySettings | None = None,
    ) -> None:
        self._transport = transport
        self._config = proxy_config or load_proxy_config(rp_dir)

    def post(self, request: TransportRequest) -> TransportResponse:
        return self._transport.post(self._apply_proxy(request))

    def get(self, request: TransportRequest) -> TransportResponse:
        return self._transport.get(self._apply_proxy(request))

    def post_stream(self, request: TransportRequest) -> Iterable[str]:
        return self._transport.post_stream(self._apply_proxy(request))

    # ------------------------------------------------------------------

    def _apply_proxy(self, request: TransportRequest) -> TransportRequest:
        """Apply proxy configuration to the request if enabled.

        Args:
            request: The original request

        Returns:
            Modified request with proxy endpoint and auth, or original if proxy disabled
        """
        if not self._config.use_proxy or not self._config.proxy_url:
            return request

        headers = dict(request.headers or {})
        if self._config.proxy_token:
            headers["X-Proxy-Authorization"] = f"Bearer {self._config.proxy_token}"

        return TransportRequest(
            endpoint=self._config.proxy_url,
            payload=request.payload,
            headers=headers,
            timeout_seconds=request.timeout_seconds,
        )
