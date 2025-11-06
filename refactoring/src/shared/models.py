"""Shared domain models and enums used across layers.

This module contains types and enums that are used by multiple layers
(domain, infrastructure, automation) to prevent circular import issues.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntityType(Enum):
    """Supported entity categories."""

    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProxySettings:
    """Proxy configuration settings.

    Standardized proxy configuration used across transport layers.
    Replaces dict-based proxy configuration for type safety.

    Attributes:
        proxy_url: The proxy server URL (e.g., "https://proxy.example.com")
        proxy_token: Optional authentication token for the proxy
        use_proxy: Whether to enable proxy routing (default: False)
    """

    proxy_url: str | None = None
    proxy_token: str | None = None
    use_proxy: bool = False
