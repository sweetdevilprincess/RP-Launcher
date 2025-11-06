"""Proxy client for routing LLM API requests through a proxy server.

This module provides a unified proxy interface that all LLM clients can use.
It handles proxy configuration loading and automatic request routing.
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any


def load_proxy_config(rp_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load proxy configuration from environment variables and config files.

    Checks in order:
    1. PROXY_URL and PROXY_TOKEN environment variables
    2. Global config.json (created by TUI settings)
    3. Legacy ANTHROPIC_PROXY_URL/TOKEN env vars (backward compatibility)

    Args:
        rp_dir: RP directory (for future use with per-RP configs)

    Returns:
        Dict with keys:
            - proxy_url: Proxy server URL (or None)
            - proxy_token: Proxy authentication token (or None)
            - use_proxy: Whether proxy is enabled (bool)
    """
    # Check environment variables (new)
    proxy_url = os.environ.get("PROXY_URL")
    proxy_token = os.environ.get("PROXY_TOKEN")
    use_proxy = False

    # Check legacy environment variables
    proxy_url = proxy_url or os.environ.get("ANTHROPIC_PROXY_URL")
    proxy_token = proxy_token or os.environ.get("ANTHROPIC_PROXY_TOKEN")

    # Check global config.json (TUI settings)
    base_dir = Path(__file__).parent.parent.parent
    config_file = base_dir / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding='utf-8'))
            # New config field names
            proxy_url = proxy_url or config.get("proxy_url")
            proxy_token = proxy_token or config.get("proxy_token")
            use_proxy = config.get("use_proxy", False)

            # Legacy config field names (backward compatibility)
            if not proxy_url:
                proxy_url = config.get("anthropic_proxy_url")
            if not proxy_token:
                proxy_token = config.get("anthropic_proxy_token")
        except Exception:
            pass

    return {
        "proxy_url": proxy_url,
        "proxy_token": proxy_token,
        "use_proxy": use_proxy
    }


class ProxyClient:
    """HTTP client that automatically routes requests through a proxy when enabled.

    This client wraps the requests library and handles proxy routing transparently.
    When proxy is enabled, it:
    1. Replaces the target endpoint with the proxy URL
    2. Adds X-Proxy-Authorization header with the proxy token
    3. Sends the request to the proxy, which forwards it to the actual LLM service

    This is a SillyTavern-style proxy where the proxy acts as an API endpoint
    replacement, not as an HTTP traffic router.

    Example usage:
        proxy = ProxyClient()
        response = proxy.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer sk-..."},
            json={"model": "gpt-4", "messages": [...]},
            timeout=60
        )
    """

    def __init__(self, rp_dir: Optional[Path] = None):
        """Initialize proxy client.

        Args:
            rp_dir: RP directory (for future per-RP config support)
        """
        config = load_proxy_config(rp_dir)
        self.proxy_url = config["proxy_url"]
        self.proxy_token = config["proxy_token"]
        self.use_proxy = config["use_proxy"]

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """Make a POST request, automatically routing through proxy if enabled.

        This method mimics requests.post() but adds automatic proxy support.

        Args:
            url: Target API endpoint URL (will be replaced with proxy_url if proxy enabled)
            headers: Request headers (proxy auth header added automatically if needed)
            json: JSON payload
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to requests.post()

        Returns:
            requests.Response object
        """
        # Use proxy URL if proxy is enabled
        actual_url = self.proxy_url if self.use_proxy and self.proxy_url else url

        # Copy headers to avoid mutating the original
        request_headers = headers.copy() if headers else {}

        # Add proxy authentication header if proxy is enabled
        if self.use_proxy and self.proxy_token:
            request_headers["X-Proxy-Authorization"] = f"Bearer {self.proxy_token}"

        # Make the request
        return requests.post(
            actual_url,
            headers=request_headers,
            json=json,
            timeout=timeout,
            **kwargs
        )

    def is_enabled(self) -> bool:
        """Check if proxy is currently enabled.

        Returns:
            True if proxy routing is active, False otherwise
        """
        return self.use_proxy and bool(self.proxy_url)
