"""Tests for LoggingTransport implementation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from refactoring.src.infrastructure.transports.fake_transport import FakeTransport
from refactoring.src.infrastructure.transports.logging_transport import LoggingTransport
from refactoring.src.shared.interfaces.transport import (
    TransportError,
    TransportRequest,
    TransportResponse,
)


class TestLoggingTransport:
    """Tests for LoggingTransport."""

    def test_post_logs_request_and_response(self):
        """POST request logs both request and response."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={"result": "ok"})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(
            transport=fake_transport, logger=mock_logger, name="test_client"
        )

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            payload={"key": "value"},
            timeout_seconds=30.0,
        )

        # Act
        response = logging_transport.post(request)

        # Assert
        assert response.status_code == 200
        assert response.body == {"result": "ok"}

        # Check request logging
        assert mock_logger.debug.call_count == 2
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[0][0] == "test_client.post"
        assert request_log_call[1]["context"]["endpoint"] == "https://api.example.com/test"
        assert request_log_call[1]["context"]["timeout"] == 30.0

        # Check response logging
        response_log_call = mock_logger.debug.call_args_list[1]
        assert response_log_call[0][0] == "test_client.post.response"
        assert response_log_call[1]["context"]["endpoint"] == "https://api.example.com/test"
        assert response_log_call[1]["context"]["status_code"] == 200

    def test_get_logs_request_and_response(self):
        """GET request logs both request and response."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={"items": [1, 2, 3]})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(
            transport=fake_transport, logger=mock_logger, name="api_client"
        )

        request = TransportRequest(endpoint="https://api.example.com/items")

        # Act
        response = logging_transport.get(request)

        # Assert
        assert response.status_code == 200
        assert response.body == {"items": [1, 2, 3]}

        # Check request logging
        assert mock_logger.debug.call_count == 2
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[0][0] == "api_client.get"

        # Check response logging
        response_log_call = mock_logger.debug.call_args_list[1]
        assert response_log_call[0][0] == "api_client.get.response"

    def test_default_name_is_transport(self):
        """Default name is 'transport' when not specified."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[0][0] == "transport.post"

        response_log_call = mock_logger.debug.call_args_list[1]
        assert response_log_call[0][0] == "transport.post.response"

    def test_authorization_header_masked(self):
        """Authorization header is masked in request logs."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(
            endpoint="https://api.example.com/secure",
            headers={"Authorization": "Bearer secret-token-12345"},
        )

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[1]["context"]["headers"]["Authorization"] == "***"

    def test_proxy_authorization_header_masked(self):
        """X-Proxy-Authorization header is masked in request logs."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            headers={"X-Proxy-Authorization": "proxy-secret-abc"},
        )

        # Act
        logging_transport.get(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[1]["context"]["headers"]["X-Proxy-Authorization"] == "***"

    def test_case_insensitive_header_masking(self):
        """Header masking is case-insensitive."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            headers={
                "AUTHORIZATION": "Bearer token1",
                "authorization": "Bearer token2",
                "X-PROXY-AUTHORIZATION": "proxy1",
                "x-proxy-authorization": "proxy2",
            },
        )

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        logged_headers = request_log_call[1]["context"]["headers"]
        assert logged_headers["AUTHORIZATION"] == "***"
        assert logged_headers["authorization"] == "***"
        assert logged_headers["X-PROXY-AUTHORIZATION"] == "***"
        assert logged_headers["x-proxy-authorization"] == "***"

    def test_non_sensitive_headers_not_masked(self):
        """Non-sensitive headers are logged as-is."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "TestClient/1.0",
                "X-Request-ID": "abc123",
            },
        )

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        logged_headers = request_log_call[1]["context"]["headers"]
        assert logged_headers["Content-Type"] == "application/json"
        assert logged_headers["User-Agent"] == "TestClient/1.0"
        assert logged_headers["X-Request-ID"] == "abc123"

    def test_no_headers_logged_as_empty_dict(self):
        """Request with no headers logs empty dict."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[1]["context"]["headers"] == {}

    def test_response_returned_unchanged(self):
        """Response is returned unchanged from wrapped transport."""
        # Arrange
        fake_transport = FakeTransport()
        expected_response = TransportResponse(
            status_code=201,
            body={"id": 123, "name": "Alice"},
            headers={"X-Custom": "value"},
        )
        fake_transport.set_response(
            status_code=201,
            body={"id": 123, "name": "Alice"},
            headers={"X-Custom": "value"},
        )

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/users")

        # Act
        response = logging_transport.post(request)

        # Assert
        assert response.status_code == expected_response.status_code
        assert response.body == expected_response.body
        assert response.headers == expected_response.headers

    def test_exception_propagates(self):
        """Exceptions from wrapped transport propagate correctly."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_error(TransportError("Network error"))

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act & Assert
        with pytest.raises(TransportError) as exc_info:
            logging_transport.post(request)

        assert "Network error" in str(exc_info.value)

        # Verify request was logged before exception
        assert mock_logger.debug.call_count == 1
        request_log_call = mock_logger.debug.call_args_list[0]
        assert "post" in request_log_call[0][0]

    def test_timeout_logged_in_context(self):
        """Request timeout is logged in context."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/test", timeout_seconds=45.5)

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[1]["context"]["timeout"] == 45.5

    def test_null_timeout_logged(self):
        """Null timeout (None) is logged correctly."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/test", timeout_seconds=None)

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        assert request_log_call[1]["context"]["timeout"] is None

    def test_error_status_code_logged(self):
        """Error status codes (4xx, 5xx) are logged."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=404, body={"error": "Not found"})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(endpoint="https://api.example.com/missing")

        # Act
        response = logging_transport.get(request)

        # Assert
        assert response.status_code == 404

        response_log_call = mock_logger.debug.call_args_list[1]
        assert response_log_call[1]["context"]["status_code"] == 404

    def test_multiple_requests_logged_separately(self):
        """Multiple requests are logged separately."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request1 = TransportRequest(endpoint="https://api.example.com/endpoint1")
        request2 = TransportRequest(endpoint="https://api.example.com/endpoint2")

        # Act
        logging_transport.post(request1)
        logging_transport.get(request2)

        # Assert
        assert mock_logger.debug.call_count == 4

        # First request
        assert "endpoint1" in str(mock_logger.debug.call_args_list[0])
        assert "post" in mock_logger.debug.call_args_list[0][0][0]

        # Second request
        assert "endpoint2" in str(mock_logger.debug.call_args_list[2])
        assert "get" in mock_logger.debug.call_args_list[2][0][0]

    def test_mixed_sensitive_and_non_sensitive_headers(self):
        """Request with mixed sensitive and non-sensitive headers."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        mock_logger = MagicMock()
        logging_transport = LoggingTransport(transport=fake_transport, logger=mock_logger)

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/json",
                "X-Proxy-Authorization": "proxy-secret",
                "User-Agent": "Client/1.0",
            },
        )

        # Act
        logging_transport.post(request)

        # Assert
        request_log_call = mock_logger.debug.call_args_list[0]
        logged_headers = request_log_call[1]["context"]["headers"]

        # Sensitive headers masked
        assert logged_headers["Authorization"] == "***"
        assert logged_headers["X-Proxy-Authorization"] == "***"

        # Non-sensitive headers unchanged
        assert logged_headers["Content-Type"] == "application/json"
        assert logged_headers["User-Agent"] == "Client/1.0"
