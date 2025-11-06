"""Tests for RequestsTransport implementation."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest
import requests
from refactoring.src.infrastructure.transports.requests_transport import RequestsTransport
from refactoring.src.shared.interfaces.transport import (
    TransportError,
    TransportRequest,
)


class TestRequestsTransport:
    """Tests for RequestsTransport."""

    def test_post_success_json_response(self):
        """POST request with JSON response returns parsed body."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(
            endpoint="https://api.example.com/test",
            payload={"key": "value"},
            headers={"Authorization": "Bearer token"},
            timeout_seconds=30.0,
        )

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 200
        assert response.body == {"result": "success"}
        assert response.headers == {"Content-Type": "application/json"}

        mock_session.request.assert_called_once_with(
            "post",
            "https://api.example.com/test",
            json={"key": "value"},
            headers={"Authorization": "Bearer token"},
            timeout=30.0,
        )

    def test_get_success_json_response(self):
        """GET request with JSON response returns parsed body."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [1, 2, 3]}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/items")

        # Act
        response = transport.get(request)

        # Assert
        assert response.status_code == 200
        assert response.body == {"items": [1, 2, 3]}

        mock_session.request.assert_called_once_with(
            "get",
            "https://api.example.com/items",
            json=None,
            headers=None,
            timeout=None,
        )

    def test_post_text_response_fallback(self):
        """POST request with non-JSON response returns text."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text response"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/text")

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 200
        assert response.body == "Plain text response"
        assert response.headers == {"Content-Type": "text/plain"}

    def test_get_text_response_fallback(self):
        """GET request with non-JSON response returns text."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "HTML content"
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/html")

        # Act
        response = transport.get(request)

        # Assert
        assert response.status_code == 200
        assert response.body == "HTML content"

    def test_post_error_status_code(self):
        """POST request with error status code still returns response."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/missing")

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 404
        assert response.body == {"error": "Not found"}

    def test_get_error_status_code(self):
        """GET request with error status code still returns response."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/error")

        # Act
        response = transport.get(request)

        # Assert
        assert response.status_code == 500
        assert response.body == {"error": "Internal server error"}

    def test_post_network_error_raises_transport_error(self):
        """POST request network error raises TransportError."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_session.request.side_effect = requests.ConnectionError("Connection refused")

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act & Assert
        with pytest.raises(TransportError) as exc_info:
            transport.post(request)

        assert "Connection refused" in str(exc_info.value)

    def test_get_network_error_raises_transport_error(self):
        """GET request network error raises TransportError."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_session.request.side_effect = requests.Timeout("Request timed out")

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/slow")

        # Act & Assert
        with pytest.raises(TransportError) as exc_info:
            transport.get(request)

        assert "Request timed out" in str(exc_info.value)

    def test_post_timeout_error_raises_transport_error(self):
        """POST request timeout raises TransportError."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_session.request.side_effect = requests.Timeout("Timeout exceeded")

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/slow", timeout_seconds=1.0)

        # Act & Assert
        with pytest.raises(TransportError):
            transport.post(request)

    def test_default_session_creation(self):
        """Transport creates default session if none provided."""
        # Act
        transport = RequestsTransport()

        # Assert
        assert transport._session is not None
        assert isinstance(transport._session, requests.Session)

    def test_custom_session_used(self):
        """Transport uses provided custom session."""
        # Arrange
        custom_session = requests.Session()
        custom_session.headers.update({"X-Custom": "Header"})

        # Act
        transport = RequestsTransport(session=custom_session)

        # Assert
        assert transport._session is custom_session
        assert transport._session.headers.get("X-Custom") == "Header"

    def test_post_minimal_request(self):
        """POST with minimal request (endpoint only) works."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/create")

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 201
        mock_session.request.assert_called_once_with(
            "post",
            "https://api.example.com/create",
            json=None,
            headers=None,
            timeout=None,
        )

    def test_get_minimal_request(self):
        """GET with minimal request (endpoint only) works."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/list")

        # Act
        response = transport.get(request)

        # Assert
        assert response.status_code == 200
        assert response.body == []

    def test_post_complex_json_payload(self):
        """POST with complex nested JSON payload."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)

        complex_payload = {
            "user": {"name": "Alice", "roles": ["admin", "user"]},
            "metadata": {"tags": ["tag1", "tag2"], "count": 42},
        }

        request = TransportRequest(
            endpoint="https://api.example.com/users", payload=complex_payload
        )

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 200
        mock_session.request.assert_called_once_with(
            "post",
            "https://api.example.com/users",
            json=complex_payload,
            headers=None,
            timeout=None,
        )

    def test_get_custom_headers_passed_through(self):
        """GET request custom headers are passed to requests."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)

        custom_headers = {
            "Authorization": "Bearer secret-token",
            "X-API-Key": "key123",
            "User-Agent": "CustomClient/1.0",
        }

        request = TransportRequest(
            endpoint="https://api.example.com/secure", headers=custom_headers
        )

        # Act
        transport.get(request)

        # Assert
        mock_session.request.assert_called_once_with(
            "get",
            "https://api.example.com/secure",
            json=None,
            headers=custom_headers,
            timeout=None,
        )

    def test_post_timeout_passed_through(self):
        """POST request timeout is passed to requests."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/test", timeout_seconds=45.5)

        # Act
        transport.post(request)

        # Assert
        mock_session.request.assert_called_once_with(
            "post",
            "https://api.example.com/test",
            json=None,
            headers=None,
            timeout=45.5,
        )

    def test_response_headers_preserved(self):
        """Response headers are preserved in TransportResponse."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.headers = {
            "Content-Type": "application/json",
            "X-RateLimit-Remaining": "999",
            "X-Request-ID": "abc123",
        }
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        response = transport.post(request)

        # Assert
        assert response.headers == {
            "Content-Type": "application/json",
            "X-RateLimit-Remaining": "999",
            "X-Request-ID": "abc123",
        }

    def test_empty_json_response(self):
        """Empty JSON response is handled correctly."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.return_value = None
        mock_response.headers = {}
        mock_session.request.return_value = mock_response

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/delete")

        # Act
        response = transport.post(request)

        # Assert
        assert response.status_code == 204
        assert response.body is None

    def test_http_error_raises_transport_error(self):
        """HTTP error (like SSLError) raises TransportError."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        mock_session.request.side_effect = requests.exceptions.SSLError("SSL verification failed")

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/secure")

        # Act & Assert
        with pytest.raises(TransportError) as exc_info:
            transport.get(request)

        assert "SSL verification failed" in str(exc_info.value)

    def test_request_exception_chain_preserved(self):
        """RequestException is chained as cause of TransportError."""
        # Arrange
        mock_session = MagicMock(spec=requests.Session)
        original_error = requests.ConnectionError("Network unreachable")
        mock_session.request.side_effect = original_error

        transport = RequestsTransport(session=mock_session)
        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act & Assert
        with pytest.raises(TransportError) as exc_info:
            transport.post(request)

        assert exc_info.value.__cause__ is original_error
