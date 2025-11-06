"""Socket Client for TUI-side IPC.

This module implements the client-side socket that the TUI uses to
communicate with the Bridge server.
"""

import socket
import threading
import time
import uuid
from typing import Callable, Optional

from .ipc_protocol import (
    IPCMessageType,
    IPCRequest,
    IPCResponse,
    create_request,
    parse_message,
)


class SocketClient:
    """Socket client for TUI to communicate with Bridge.

    The client connects to the Bridge's socket server and sends requests.
    Responses are received asynchronously and matched by request ID.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        buffer_size: int = 65536,
        reconnect_delay: float = 1.0,
    ):
        """Initialize socket client.

        Args:
            host: Server host to connect to
            port: Server port to connect to
            buffer_size: Size of receive buffer in bytes
            reconnect_delay: Delay between reconnection attempts (seconds)
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.reconnect_delay = reconnect_delay

        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False

        # Response handling
        self.pending_responses: dict[str, IPCResponse] = {}
        self.response_callbacks: dict[str, Callable[[IPCResponse], None]] = {}
        self.streaming_callbacks: dict[str, Callable[[str], None]] = {}  # For streaming chunks
        self.streaming_active: dict[str, bool] = {}  # Track active streams

        # Threads
        self.receive_thread: Optional[threading.Thread] = None
        self.reconnect_thread: Optional[threading.Thread] = None

        # Lock for thread-safe operations
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to the server.

        Returns:
            True if connected successfully

        Raises:
            RuntimeError: If connection fails
        """
        if self.connected:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # Connection timeout
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # No timeout for normal operations
            self.connected = True
            self.running = True

            print(f"[OK] Connected to bridge at {self.host}:{self.port}")

            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            return True

        except Exception as e:
            print(f"[ERROR] Failed to connect to bridge: {e}")
            self.connected = False
            raise RuntimeError(f"Failed to connect: {e}") from e

    def _receive_loop(self) -> None:
        """Receive responses from server (runs in background thread)."""
        buffer = b""

        while self.running and self.socket:
            try:
                # Receive data
                data = self.socket.recv(self.buffer_size)
                if not data:
                    # Server disconnected
                    print("🔌 Bridge disconnected")
                    self.connected = False
                    self._schedule_reconnect()
                    break

                buffer += data

                # Process complete messages (newline-delimited)
                while b"\n" in buffer:
                    message, buffer = buffer.split(b"\n", 1)
                    if message:
                        self._process_response(message.decode("utf-8"))

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[WARNING] Error receiving data: {e}")
                    self.connected = False
                    self._schedule_reconnect()
                break

    def _process_response(self, response_json: str) -> None:
        """Process a received response.

        Args:
            response_json: JSON response string
        """
        try:
            # Parse message
            message = parse_message(response_json)
            request_id = message.request_id

            # Handle streaming chunks
            if message.type == IPCMessageType.STREAMING_CHUNK.value:
                chunk = message.data.get("chunk", "")

                with self.lock:
                    # Mark stream as active
                    self.streaming_active[request_id] = True

                    # Call streaming callback if registered
                    if request_id in self.streaming_callbacks:
                        callback = self.streaming_callbacks[request_id]
                        try:
                            callback(chunk)
                        except Exception as e:
                            print(f"[WARNING] Error in streaming callback: {e}")

                return

            # Handle streaming done
            if message.type == IPCMessageType.STREAMING_DONE.value:
                with self.lock:
                    # Mark stream as inactive
                    self.streaming_active[request_id] = False
                    # Keep streaming callback registered for final response
                return

            # Handle regular response
            if isinstance(message, IPCResponse):
                with self.lock:
                    # Clean up streaming state
                    self.streaming_callbacks.pop(request_id, None)
                    self.streaming_active.pop(request_id, None)

                    if request_id in self.response_callbacks:
                        callback = self.response_callbacks.pop(request_id)
                        # Execute callback
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"[WARNING] Error in response callback: {e}")
                    else:
                        # Store for synchronous retrieval
                        self.pending_responses[request_id] = message
            else:
                print(f"[WARNING] Unexpected message type: {message.type}")

        except Exception as e:
            print(f"[WARNING] Error processing response: {e}")

    def _schedule_reconnect(self) -> None:
        """Schedule automatic reconnection."""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return  # Already reconnecting

        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """Attempt to reconnect periodically."""
        print("🔄 Attempting to reconnect...")

        while self.running and not self.connected:
            try:
                time.sleep(self.reconnect_delay)
                self.connect()
                if self.connected:
                    print("[OK] Reconnected to bridge")
                    break
            except Exception:
                # Connection failed, will retry
                pass

    def send_request(
        self, message_type: IPCMessageType, timeout: float = 30.0, **kwargs
    ) -> IPCResponse:
        """Send a request and wait for response (synchronous).

        Args:
            message_type: Type of request
            timeout: Maximum time to wait for response (seconds)
            **kwargs: Request data

        Returns:
            Response from server

        Raises:
            RuntimeError: If not connected or request fails
            TimeoutError: If response not received within timeout
        """
        if not self.connected:
            raise RuntimeError("Not connected to bridge")

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Create and send request
        request_json = create_request(message_type, request_id, **kwargs)
        self._send_message(request_json)

        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                if request_id in self.pending_responses:
                    return self.pending_responses.pop(request_id)
            time.sleep(0.01)  # Small delay to avoid busy waiting

        raise TimeoutError(f"Request {request_id} timed out after {timeout}s")

    def send_request_async(
        self,
        message_type: IPCMessageType,
        callback: Callable[[IPCResponse], None],
        streaming_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> str:
        """Send a request with async callback (non-blocking).

        Args:
            message_type: Type of request
            callback: Function to call when final response received
            streaming_callback: Optional function to call for each streaming chunk
            **kwargs: Request data

        Returns:
            Request ID

        Raises:
            RuntimeError: If not connected
        """
        if not self.connected:
            raise RuntimeError("Not connected to bridge")

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Register callbacks
        with self.lock:
            self.response_callbacks[request_id] = callback
            if streaming_callback:
                self.streaming_callbacks[request_id] = streaming_callback

        # Create and send request
        request_json = create_request(message_type, request_id, **kwargs)
        self._send_message(request_json)

        return request_id

    def _send_message(self, message_json: str) -> None:
        """Send a message to server.

        Args:
            message_json: JSON message string

        Raises:
            RuntimeError: If send fails
        """
        if not self.socket:
            raise RuntimeError("Socket not initialized")

        try:
            # Send with newline delimiter
            message = (message_json + "\n").encode("utf-8")
            self.socket.sendall(message)
        except Exception as e:
            print(f"[WARNING] Error sending message: {e}")
            self.connected = False
            raise RuntimeError(f"Failed to send message: {e}") from e

    def ping(self, timeout: float = 5.0) -> bool:
        """Send a ping to check if server is responsive.

        Args:
            timeout: Maximum time to wait for response

        Returns:
            True if server responded
        """
        try:
            response = self.send_request(IPCMessageType.PING, timeout=timeout)
            return response.success
        except Exception:
            return False

    def disconnect(self) -> None:
        """Disconnect from server."""
        print("🔌 Disconnecting from bridge...")
        self.running = False
        self.connected = False

        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        # Wait for threads
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=2.0)

        print("[OK] Disconnected")

    def is_connected(self) -> bool:
        """Check if connected to server.

        Returns:
            True if connected
        """
        return self.connected

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
