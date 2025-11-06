"""Fake transport implementation for testing."""

from __future__ import annotations

from typing import Any

from ...shared.interfaces.transport import (
    TransportRequest,
    TransportResponse,
)


class FakeTransport:
    """
    Test double for Transport protocol.

    Provides predictable responses, error simulation, and request capture
    for comprehensive transport testing.

    Example:
        fake = FakeTransport()
        fake.set_response(status_code=200, body={"result": "ok"})

        response = fake.post(TransportRequest(endpoint="/api/test"))
        assert response.status_code == 200
        assert fake.last_request.endpoint == "/api/test"
    """

    def __init__(self) -> None:
        """Initialize fake transport with default success response."""
        self._response: TransportResponse | None = None
        self._error: Exception | None = None
        self._requests: list[TransportRequest] = []

    def set_response(
        self,
        status_code: int = 200,
        body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> FakeTransport:
        """
        Configure the response to return on next request.

        Args:
            status_code: HTTP status code (default: 200)
            body: Response body (any JSON-serializable object)
            headers: Optional response headers

        Returns:
            Self for method chaining
        """
        self._response = TransportResponse(
            status_code=status_code,
            body=body or {},
            headers=headers,
        )
        self._error = None
        return self

    def set_error(self, error: Exception) -> FakeTransport:
        """
        Configure an error to raise on next request.

        Args:
            error: Exception to raise (typically TransportError)

        Returns:
            Self for method chaining
        """
        self._error = error
        self._response = None
        return self

    def post(self, request: TransportRequest) -> TransportResponse:
        """
        Send a POST request (mocked).

        Args:
            request: The request to send

        Returns:
            The configured response

        Raises:
            Exception: If set_error() was called with an exception
        """
        self._requests.append(request)

        if self._error is not None:
            raise self._error

        if self._response is None:
            # Default success response
            return TransportResponse(status_code=200, body={})

        return self._response

    def get(self, request: TransportRequest) -> TransportResponse:
        """
        Send a GET request (mocked).

        Args:
            request: The request to send

        Returns:
            The configured response

        Raises:
            Exception: If set_error() was called with an exception
        """
        self._requests.append(request)

        if self._error is not None:
            raise self._error

        if self._response is None:
            # Default success response
            return TransportResponse(status_code=200, body={})

        return self._response

    @property
    def last_request(self) -> TransportRequest | None:
        """Get the most recent request sent through this transport."""
        return self._requests[-1] if self._requests else None

    @property
    def requests(self) -> list[TransportRequest]:
        """Get all requests sent through this transport."""
        return self._requests.copy()

    @property
    def request_count(self) -> int:
        """Get the number of requests sent through this transport."""
        return len(self._requests)

    def clear_history(self) -> FakeTransport:
        """
        Clear request history.

        Returns:
            Self for method chaining
        """
        self._requests.clear()
        return self

    def reset(self) -> FakeTransport:
        """
        Reset to initial state (clear history and configured responses).

        Returns:
            Self for method chaining
        """
        self._requests.clear()
        self._response = None
        self._error = None
        return self
