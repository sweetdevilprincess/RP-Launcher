"""Integration tests for socket-based IPC."""

from __future__ import annotations

import threading
import time
import uuid

import pytest
from refactoring.src.infrastructure.ipc import (
    IPCMessageType,
    IPCRequest,
    IPCResponse,
    SocketClient,
    SocketServer,
    create_error_response,
    create_response,
)


class TestSocketIntegration:
    """Integration tests for SocketServer and SocketClient."""

    def test_server_starts_and_accepts_connection(self):
        """Server starts and accepts client connection."""
        server = SocketServer(host="127.0.0.1", port=5556)

        # Set dummy handler
        def handler(request: IPCRequest) -> str:
            return create_response(request.request_id, result="pong")

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)  # Give server time to start

            # Client should connect successfully
            client = SocketClient(host="127.0.0.1", port=5556)
            connected = client.connect()

            assert connected is True
            assert client.connected is True

            client.disconnect()
        finally:
            server.stop()

    def test_client_sends_request_and_receives_response(self):
        """Client can send request and receive response."""
        server = SocketServer(host="127.0.0.1", port=5557)

        # Handler that echoes back
        def handler(request: IPCRequest) -> str:
            return create_response(
                request.request_id,
                echo=request.data.get("message", "")
            )

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5557)
            client.connect()
            time.sleep(0.1)

            # Send request
            response = client.send_request(
                IPCMessageType.SEND_MESSAGE,
                message="Hello server"
            )

            assert response is not None
            assert response.success is True
            assert response.data.get("echo") == "Hello server"

            client.disconnect()
        finally:
            server.stop()

    def test_ping_request(self):
        """PING request works."""
        server = SocketServer(host="127.0.0.1", port=5558)

        def handler(request: IPCRequest) -> str:
            if request.type == IPCMessageType.PING.value:
                return create_response(request.request_id, status="alive")
            return create_error_response(request.request_id, "Unknown request")

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5558)
            client.connect()
            time.sleep(0.1)

            response = client.send_request(IPCMessageType.PING)

            assert response.success is True
            assert response.data.get("status") == "alive"

            client.disconnect()
        finally:
            server.stop()

    def test_multiple_requests_in_sequence(self):
        """Multiple requests work in sequence."""
        server = SocketServer(host="127.0.0.1", port=5559)

        request_count = {"count": 0}

        def handler(request: IPCRequest) -> str:
            request_count["count"] += 1
            return create_response(
                request.request_id,
                request_number=request_count["count"]
            )

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5559)
            client.connect()
            time.sleep(0.1)

            # Send 5 requests
            for i in range(1, 6):
                response = client.send_request(IPCMessageType.GET_STATE)
                assert response.success is True
                assert response.data.get("request_number") == i

            client.disconnect()
        finally:
            server.stop()

    def test_error_response_handling(self):
        """Client handles error responses correctly."""
        server = SocketServer(host="127.0.0.1", port=5560)

        def handler(request: IPCRequest) -> str:
            return create_error_response(
                request.request_id,
                "Intentional error",
                code=400
            )

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5560)
            client.connect()
            time.sleep(0.1)

            response = client.send_request(IPCMessageType.GET_STATE)

            assert response.success is False
            assert response.error_message == "Intentional error"
            assert response.data.get("code") == 400

            client.disconnect()
        finally:
            server.stop()

    def test_request_timeout(self):
        """Client times out if no response received."""
        server = SocketServer(host="127.0.0.1", port=5561)

        def handler(request: IPCRequest) -> str:
            # Simulate slow handler
            time.sleep(3.0)
            return create_response(request.request_id, result="delayed")

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5561)
            client.connect()
            time.sleep(0.1)

            # Should timeout and raise TimeoutError
            with pytest.raises(TimeoutError):
                client.send_request(IPCMessageType.PING, timeout=1.0)

            client.disconnect()
        finally:
            server.stop()

    def test_concurrent_server_client_operation(self):
        """Server and client work concurrently."""
        server = SocketServer(host="127.0.0.1", port=5562)

        results = []

        def handler(request: IPCRequest) -> str:
            results.append(request.data.get("index"))
            return create_response(request.request_id, received=True)

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5562)
            client.connect()
            time.sleep(0.1)

            # Send 10 requests rapidly
            for i in range(10):
                client.send_request(IPCMessageType.SEND_MESSAGE, index=i)
                time.sleep(0.05)  # Small delay between requests

            # All requests should have been processed
            time.sleep(0.5)
            assert len(results) == 10
            assert results == list(range(10))

            client.disconnect()
        finally:
            server.stop()

    def test_newline_delimited_protocol(self):
        """Messages are newline-delimited as expected."""
        server = SocketServer(host="127.0.0.1", port=5563)

        received_messages = []

        def handler(request: IPCRequest) -> str:
            received_messages.append(request.data.get("content"))
            return create_response(request.request_id, ok=True)

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5563)
            client.connect()
            time.sleep(0.1)

            # Send messages with newlines in content
            messages = [
                "First message",
                "Second message\nwith newline",
                "Third message"
            ]

            for msg in messages:
                client.send_request(IPCMessageType.SEND_MESSAGE, content=msg)

            time.sleep(0.3)

            # All messages should be received correctly
            assert len(received_messages) == 3
            assert received_messages == messages

            client.disconnect()
        finally:
            server.stop()


class TestSocketReconnection:
    """Tests for socket reconnection behavior."""

    def test_client_reconnects_after_disconnect(self):
        """Client can reconnect after disconnection."""
        server = SocketServer(host="127.0.0.1", port=5564)

        def handler(request: IPCRequest) -> str:
            return create_response(request.request_id, status="ok")

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5564)

            # First connection
            client.connect()
            time.sleep(0.1)
            assert client.connected is True

            # Disconnect
            client.disconnect()
            time.sleep(0.1)
            assert client.connected is False

            # Reconnect
            client.connect()
            time.sleep(0.1)
            assert client.connected is True

            # Should still work
            response = client.send_request(IPCMessageType.PING)
            assert response is not None
            assert response.success is True

            client.disconnect()
        finally:
            server.stop()


class TestThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_requests_from_single_client(self):
        """Single client can handle concurrent requests safely."""
        server = SocketServer(host="127.0.0.1", port=5565)

        def handler(request: IPCRequest) -> str:
            # Simulate some processing time
            time.sleep(0.05)
            return create_response(
                request.request_id,
                thread_id=request.data.get("thread_id")
            )

        server.set_handler(handler)

        try:
            server.start()
            time.sleep(0.2)

            client = SocketClient(host="127.0.0.1", port=5565)
            client.connect()
            time.sleep(0.1)

            results = {}
            threads = []

            def send_request(thread_id):
                response = client.send_request(
                    IPCMessageType.GET_STATE,
                    thread_id=thread_id,
                    timeout=5.0
                )
                if response:
                    results[thread_id] = response.data.get("thread_id")

            # Start 5 concurrent requests
            for i in range(5):
                thread = threading.Thread(target=send_request, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # All requests should succeed
            assert len(results) == 5
            for i in range(5):
                assert results[i] == i

            client.disconnect()
        finally:
            server.stop()
