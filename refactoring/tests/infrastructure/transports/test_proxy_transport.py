"""Tests for ProxyTransport implementation."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

from refactoring.src.infrastructure.transports.fake_transport import FakeTransport
from refactoring.src.infrastructure.transports.proxy_transport import (
    ProxyTransport,
    load_proxy_config,
)
from refactoring.src.shared.interfaces.transport import (
    TransportRequest,
)
from refactoring.src.shared.models import ProxySettings


class TestProxyTransport:
    """Tests for ProxyTransport."""

    def test_post_no_proxy_request_unchanged(self):
        """POST request unchanged when proxy not enabled."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={"result": "ok"})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(use_proxy=False, proxy_url=None, proxy_token=None),
        )

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            payload={"key": "value"},
        )

        # Act
        response = proxy_transport.post(request)

        # Assert
        assert response.status_code == 200
        assert fake_transport.last_request.endpoint == "https://api.example.com/test"
        assert fake_transport.last_request.payload == {"key": "value"}

    def test_get_no_proxy_request_unchanged(self):
        """GET request unchanged when proxy not enabled."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(use_proxy=False, proxy_url="https://proxy.example.com"),
        )

        request = TransportRequest(endpoint="https://api.example.com/items")

        # Act
        response = proxy_transport.get(request)

        # Assert
        assert response.status_code == 200
        assert fake_transport.last_request.endpoint == "https://api.example.com/items"

    def test_post_proxy_enabled_changes_endpoint(self):
        """POST request endpoint changed to proxy_url when enabled."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com/forward",
                proxy_token=None,
            ),
        )

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            payload={"data": "value"},
        )

        # Act
        proxy_transport.post(request)

        # Assert
        assert fake_transport.last_request.endpoint == "https://proxy.example.com/forward"
        assert fake_transport.last_request.payload == {"data": "value"}

    def test_get_proxy_enabled_changes_endpoint(self):
        """GET request endpoint changed to proxy_url when enabled."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token=None,
            ),
        )

        request = TransportRequest(endpoint="https://api.example.com/data")

        # Act
        proxy_transport.get(request)

        # Assert
        assert fake_transport.last_request.endpoint == "https://proxy.example.com"

    def test_proxy_token_added_as_header(self):
        """Proxy token added as X-Proxy-Authorization header."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token="secret-proxy-token",
            ),
        )

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        proxy_transport.post(request)

        # Assert
        assert (
            fake_transport.last_request.headers["X-Proxy-Authorization"]
            == "Bearer secret-proxy-token"
        )

    def test_proxy_without_token_no_header_added(self):
        """Proxy without token does not add X-Proxy-Authorization header."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token=None,
            ),
        )

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        proxy_transport.post(request)

        # Assert
        headers = fake_transport.last_request.headers or {}
        assert "X-Proxy-Authorization" not in headers

    def test_existing_headers_preserved(self):
        """Existing request headers are preserved when proxy applied."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token="token",
            ),
        )

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer api-key",
            },
        )

        # Act
        proxy_transport.post(request)

        # Assert
        assert fake_transport.last_request.headers["Content-Type"] == "application/json"
        assert fake_transport.last_request.headers["Authorization"] == "Bearer api-key"
        assert fake_transport.last_request.headers["X-Proxy-Authorization"] == "Bearer token"

    def test_timeout_preserved(self):
        """Request timeout preserved when proxy applied."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token=None,
            ),
        )

        request = TransportRequest(
            endpoint="https://api.example.com/test",
            timeout_seconds=45.5,
        )

        # Act
        proxy_transport.post(request)

        # Assert
        assert fake_transport.last_request.timeout_seconds == 45.5

    def test_payload_preserved(self):
        """Request payload preserved when proxy applied."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url="https://proxy.example.com",
                proxy_token=None,
            ),
        )

        complex_payload = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "claude-3",
            "max_tokens": 1024,
        }

        request = TransportRequest(
            endpoint="https://api.example.com/chat",
            payload=complex_payload,
        )

        # Act
        proxy_transport.post(request)

        # Assert
        assert fake_transport.last_request.payload == complex_payload

    def test_proxy_enabled_true_but_no_url_unchanged(self):
        """Request unchanged when use_proxy=True but proxy_url is None."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(status_code=200, body={})

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(
                use_proxy=True,
                proxy_url=None,
                proxy_token="token",
            ),
        )

        request = TransportRequest(endpoint="https://api.example.com/test")

        # Act
        proxy_transport.post(request)

        # Assert
        assert fake_transport.last_request.endpoint == "https://api.example.com/test"

    def test_response_returned_unchanged(self):
        """Response from wrapped transport returned unchanged."""
        # Arrange
        fake_transport = FakeTransport()
        fake_transport.set_response(
            status_code=201,
            body={"id": 123},
            headers={"X-Custom": "value"},
        )

        proxy_transport = ProxyTransport(
            transport=fake_transport,
            proxy_config=ProxySettings(use_proxy=False, proxy_url=None, proxy_token=None),
        )

        request = TransportRequest(endpoint="https://api.example.com/create")

        # Act
        response = proxy_transport.post(request)

        # Assert
        assert response.status_code == 201
        assert response.body == {"id": 123}
        assert response.headers == {"X-Custom": "value"}


class TestLoadProxyConfig:
    """Tests for load_proxy_config function."""

    def test_load_from_env_proxy_url(self):
        """Loads PROXY_URL from environment."""
        with patch.dict(os.environ, {"PROXY_URL": "https://env-proxy.com"}, clear=False):
            config = load_proxy_config()
            assert config.proxy_url == "https://env-proxy.com"

    def test_load_from_env_anthropic_proxy_url(self):
        """Loads ANTHROPIC_PROXY_URL from environment."""
        with patch.dict(
            os.environ, {"ANTHROPIC_PROXY_URL": "https://anthropic-proxy.com"}, clear=False
        ):
            config = load_proxy_config()
            assert config.proxy_url == "https://anthropic-proxy.com"

    def test_load_from_env_proxy_token(self):
        """Loads PROXY_TOKEN from environment."""
        with patch.dict(os.environ, {"PROXY_TOKEN": "env-token"}, clear=False):
            config = load_proxy_config()
            assert config.proxy_token == "env-token"

    def test_load_from_env_anthropic_proxy_token(self):
        """Loads ANTHROPIC_PROXY_TOKEN from environment."""
        with patch.dict(os.environ, {"ANTHROPIC_PROXY_TOKEN": "anthropic-token"}, clear=False):
            config = load_proxy_config()
            assert config.proxy_token == "anthropic-token"

    def test_env_proxy_url_takes_precedence(self):
        """PROXY_URL takes precedence over ANTHROPIC_PROXY_URL."""
        with patch.dict(
            os.environ,
            {
                "PROXY_URL": "https://proxy.com",
                "ANTHROPIC_PROXY_URL": "https://anthropic.com",
            },
            clear=False,
        ):
            config = load_proxy_config()
            assert config.proxy_url == "https://proxy.com"

    def test_env_proxy_token_takes_precedence(self):
        """PROXY_TOKEN takes precedence over ANTHROPIC_PROXY_TOKEN."""
        with patch.dict(
            os.environ,
            {
                "PROXY_TOKEN": "token1",
                "ANTHROPIC_PROXY_TOKEN": "token2",
            },
            clear=False,
        ):
            config = load_proxy_config()
            assert config.proxy_token == "token1"

    def test_load_from_config_file(self, tmp_path):
        """Loads proxy settings from config.json."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "proxy_url": "https://file-proxy.com",
                    "proxy_token": "file-token",
                    "use_proxy": True,
                }
            )
        )

        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.proxy_url == "https://file-proxy.com"
        assert config.proxy_token == "file-token"
        assert config.use_proxy is True

    def test_load_anthropic_keys_from_config_file(self, tmp_path):
        """Loads anthropic_proxy_url and anthropic_proxy_token from config.json."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "anthropic_proxy_url": "https://anthropic-file-proxy.com",
                    "anthropic_proxy_token": "anthropic-file-token",
                    "use_proxy": True,
                }
            )
        )

        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.proxy_url == "https://anthropic-file-proxy.com"
        assert config.proxy_token == "anthropic-file-token"

    def test_env_overrides_config_file(self, tmp_path):
        """Environment variables override config file settings."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "proxy_url": "https://file-proxy.com",
                    "proxy_token": "file-token",
                }
            )
        )

        with patch.dict(
            os.environ,
            {
                "PROXY_URL": "https://env-proxy.com",
                "PROXY_TOKEN": "env-token",
            },
            clear=True,
        ):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.proxy_url == "https://env-proxy.com"
        assert config.proxy_token == "env-token"

    def test_config_file_keys_precedence(self, tmp_path):
        """proxy_url takes precedence over anthropic_proxy_url in config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "proxy_url": "https://proxy.com",
                    "anthropic_proxy_url": "https://anthropic.com",
                    "proxy_token": "token1",
                    "anthropic_proxy_token": "token2",
                }
            )
        )

        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.proxy_url == "https://proxy.com"
        assert config.proxy_token == "token1"

    def test_invalid_json_ignored(self, tmp_path):
        """Invalid JSON in config file is ignored."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        # Should return defaults
        assert config.proxy_url is None
        assert config.proxy_token is None
        assert config.use_proxy is False

    def test_no_config_file_returns_defaults(self):
        """No config file returns default values from env or None."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir="/nonexistent/path")

        assert config.proxy_url is None
        assert config.proxy_token is None
        assert config.use_proxy is False

    def test_use_proxy_default_false(self, tmp_path):
        """use_proxy defaults to False when not in config."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "proxy_url": "https://proxy.com",
                }
            )
        )

        with patch.dict(os.environ, {}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.use_proxy is False

    def test_partial_config_file(self, tmp_path):
        """Partial config file with only some fields works."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "use_proxy": True,
                }
            )
        )

        with patch.dict(os.environ, {"PROXY_URL": "https://env-proxy.com"}, clear=True):
            config = load_proxy_config(rp_dir=tmp_path)

        assert config.proxy_url == "https://env-proxy.com"
        assert config.proxy_token is None
        assert config.use_proxy is True
