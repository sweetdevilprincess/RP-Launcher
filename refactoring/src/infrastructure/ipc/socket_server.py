"""Socket Server for Bridge-side IPC.

This module implements the server-side socket that the Bridge runs to
communicate with the TUI client.
"""

import socket
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from .ipc_protocol import (
    IPCMessageType,
    IPCRequest,
    IPCResponse,
    create_error_response,
    create_response,
    parse_message,
    validate_request,
)


class SocketServer:
    """Socket server for Bridge to communicate with TUI.

    The server listens on a local port and handles requests from the TUI client.
    Each request is processed by a handler function and a response is sent back.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        buffer_size: int = 65536,
    ):
        """Initialize socket server.

        Args:
            host: Host to bind to (default: localhost)
            port: Port to listen on
            buffer_size: Size of receive buffer in bytes
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size

        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.running = False
        self.handler: Optional[Callable[[IPCRequest], str]] = None

        # Thread for handling client
        self.client_thread: Optional[threading.Thread] = None

    def set_handler(self, handler: Callable[[IPCRequest], str]) -> None:
        """Set the request handler function.

        Args:
            handler: Function that takes IPCRequest and returns JSON response string
        """
        self.handler = handler

    def start(self) -> None:
        """Start the server and listen for connections."""
        if self.running:
            return

        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind and listen
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)  # Only one client (TUI)
            self.running = True
            print(f"[SOCKET] Socket server listening on {self.host}:{self.port}")
        except OSError as e:
            raise RuntimeError(f"Failed to start socket server: {e}") from e

        # Accept connection in background thread
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()

    def _accept_loop(self) -> None:
        """Accept incoming connections (runs in background thread)."""
        while self.running and self.server_socket:
            try:
                # Accept with timeout to allow checking self.running
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"[OK] TUI connected from {address}")

                    # Close previous client if exists
                    if self.client_socket:
                        try:
                            self.client_socket.close()
                        except Exception:
                            pass

                    self.client_socket = client_socket

                    # Start client handler thread
                    self.client_thread = threading.Thread(target=self._handle_client, daemon=True)
                    self.client_thread.start()

                except socket.timeout:
                    # No connection yet, loop continues
                    continue

            except Exception as e:
                if self.running:
                    print(f"[WARNING] Error accepting connection: {e}")
                    time.sleep(1)

    def _handle_client(self) -> None:
        """Handle requests from connected client (runs in background thread)."""
        if not self.client_socket:
            return

        buffer = b""

        while self.running:
            try:
                # Receive data
                data = self.client_socket.recv(self.buffer_size)
                if not data:
                    # Client disconnected
                    print("[SOCKET] TUI disconnected")
                    break

                buffer += data

                # Process complete messages (newline-delimited)
                while b"\n" in buffer:
                    message, buffer = buffer.split(b"\n", 1)
                    if message:
                        self._process_message(message.decode("utf-8"))

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[WARNING] Error handling client: {e}")
                break

        # Clean up client socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

    def _process_message(self, message_json: str) -> None:
        """Process a received message and send response.

        Args:
            message_json: JSON message string
        """
        try:
            # Parse message
            message = parse_message(message_json)

            if not isinstance(message, IPCRequest):
                # Unexpected message type
                error = create_error_response("unknown", "Expected request message, got response")
                self._send_response(error)
                return

            # Validate request
            validate_request(message)

            # Handle request
            if self.handler:
                response_json = self.handler(message)
                self._send_response(response_json)
            else:
                # No handler set
                error = create_error_response(
                    message.request_id, "No handler configured for requests"
                )
                self._send_response(error)

        except Exception as e:
            # Error processing message
            try:
                message_obj = parse_message(message_json)
                request_id = (
                    message_obj.request_id if hasattr(message_obj, "request_id") else "unknown"
                )
            except Exception:
                request_id = "unknown"

            error = create_error_response(request_id, f"Error processing request: {str(e)}")
            self._send_response(error)

    def _send_response(self, response_json: str) -> None:
        """Send response to client.

        Args:
            response_json: JSON response string
        """
        if not self.client_socket:
            return

        try:
            # Send with newline delimiter
            message = (response_json + "\n").encode("utf-8")
            self.client_socket.sendall(message)
        except Exception as e:
            print(f"[WARNING] Error sending response: {e}")

    def send_push_message(self, message_json: str) -> None:
        """Send a push message to client (not in response to a request).

        Args:
            message_json: JSON message string
        """
        self._send_response(message_json)

    def stop(self) -> None:
        """Stop the server and close all connections."""
        print("[STOP] Stopping socket server...")
        self.running = False

        # Close client socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        # Wait for threads to finish
        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.join(timeout=2.0)

        print("[OK] Socket server stopped")

    def is_connected(self) -> bool:
        """Check if a client is connected.

        Returns:
            True if client is connected
        """
        return self.client_socket is not None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
