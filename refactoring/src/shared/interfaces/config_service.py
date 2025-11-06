"""Protocol for configuration access across the application."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class ConfigService(Protocol):
    """Expose validated configuration data with type-safe accessors."""

    def get(self, key: str, default: T | None = None) -> T:
        """Return a configuration value or the provided default."""

    def require(self, key: str) -> Any:
        """Return a configuration value, raising if the key is missing."""

    def section(self, prefix: str) -> Mapping[str, Any]:
        """Return a read-only view of a namespaced configuration section."""

    def keys(self) -> Iterable[str]:
        """Expose known configuration keys for diagnostics and tooling."""

    def reload(self) -> None:
        """Refresh configuration values from their source."""
