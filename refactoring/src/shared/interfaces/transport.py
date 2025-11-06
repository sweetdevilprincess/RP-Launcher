"""Protocol definitions for network transports and diagnostics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class TransportRequest:
    """Represents an outbound request payload."""

    endpoint: str
    payload: Mapping[str, Any] | None = None
    headers: Mapping[str, str] | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class TransportResponse:
    """Standard response returned by transports."""

    status_code: int
    body: Any
    headers: Mapping[str, str] | None = None


class TransportError(Exception):
    """Base transport exception for connectivity or protocol issues."""


class Transport(Protocol):
    """Contract for HTTP-like transports used by model clients."""

    def post(self, request: TransportRequest) -> TransportResponse:
        """Send a POST request and return the structured response."""

    def get(self, request: TransportRequest) -> TransportResponse:
        """Send a GET request and return the structured response."""

    def post_stream(self, request: TransportRequest) -> Iterable[str]:
        """Send a POST request and return an iterable of streaming chunks."""
