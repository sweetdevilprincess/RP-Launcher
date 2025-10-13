"""
Claude Code SDK Client - Python Wrapper

High-performance wrapper around the Claude Code SDK bridge (Node.js).
Provides streaming responses, proper caching, and session management.

Usage:
    from work_in_progress.clients.claude_sdk import ClaudeSDKClient

    client = ClaudeSDKClient()

    # Simple query
    for chunk in client.query("Hello, Claude!"):
        print(chunk, end='', flush=True)

    # With caching (recommended for RP)
    cached_context = "... your TIER_1 files ..."
    dynamic_prompt = "... user message with TIER_2/3 ..."

    for chunk in client.query(dynamic_prompt, cached_context=cached_context):
        print(chunk, end='', flush=True)

    # Get final response and stats
    response = client.get_last_response()
    stats = client.get_cache_stats()
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Iterator
from dataclasses import dataclass
import threading
import queue


@dataclass
class CacheStats:
    """Cache statistics from Claude API"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_savings_percent: float = 0.0
    cache_status: str = 'NONE'

    def __str__(self) -> str:
        """Format cache stats for display"""
        lines = []
        lines.append("📊 Token Usage:")
        lines.append(f"  Input: {self.input_tokens:,} tokens")
        lines.append(f"  Output: {self.output_tokens:,} tokens")

        if self.cache_read_input_tokens > 0:
            lines.append(f"  💾 Cache Read: {self.cache_read_input_tokens:,} tokens")
            lines.append(f"  💰 Savings: {self.cache_savings_percent}% ({self.cache_status})")
        elif self.cache_creation_input_tokens > 0:
            lines.append(f"  💾 Cache Created: {self.cache_creation_input_tokens:,} tokens (future savings)")

        return '\n'.join(lines)


@dataclass
class ResponseMetadata:
    """Metadata about the response"""
    session_id: Optional[str] = None
    num_turns: int = 0
    duration_ms: int = 0
    cost_usd: float = 0.0
    message_count: int = 0


class ClaudeSDKClient:
    """
    Python client for Claude Code SDK bridge.

    Manages a persistent Node.js process running the SDK bridge,
    communicating via JSON over stdin/stdout.
    """

    def __init__(self, cwd: Optional[Path] = None):
        """
        Initialize SDK client.

        Args:
            cwd: Working directory for Claude Code (defaults to current)
        """
        self.cwd = cwd or Path.cwd()
        self.process: Optional[subprocess.Popen] = None
        self.session_id: Optional[str] = None

        # Response state
        self._last_response = ""
        self._last_usage: Optional[Dict[str, Any]] = None
        self._last_metadata: Optional[ResponseMetadata] = None
        self._cache_stats: Optional[CacheStats] = None

        # Message queue for async reading
        self._message_queue: queue.Queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False

        # Start the bridge
        self._start_bridge()

    def _start_bridge(self):
        """Start the Node.js SDK bridge process"""
        # Find the bridge script
        bridge_script = Path(__file__).parent / "claude_sdk_bridge.mjs"

        if not bridge_script.exists():
            raise FileNotFoundError(f"SDK bridge script not found: {bridge_script}")

        # Start Node.js process
        try:
            self.process = subprocess.Popen(
                ['node', str(bridge_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                cwd=str(self.cwd)
            )

            self._running = True

            # Start reader thread
            self._reader_thread = threading.Thread(target=self._read_messages, daemon=True)
            self._reader_thread.start()

            # Wait for ready message
            msg = self._wait_for_message(timeout=5.0)
            if msg['type'] != 'status' or msg.get('status') != 'ready':
                raise RuntimeError(f"Bridge failed to initialize: {msg}")

        except FileNotFoundError:
            raise RuntimeError("Node.js not found. Please install Node.js to use the SDK bridge.")
        except Exception as e:
            if self.process:
                self.process.kill()
            raise RuntimeError(f"Failed to start SDK bridge: {e}")

    def _read_messages(self):
        """Background thread to read messages from bridge"""
        try:
            while self._running and self.process and self.process.stdout:
                line = self.process.stdout.readline()
                if not line:
                    break

                try:
                    msg = json.loads(line)
                    self._message_queue.put(msg)
                except json.JSONDecodeError:
                    # Log non-JSON output (errors, etc.)
                    print(f"SDK Bridge (non-JSON): {line.strip()}", file=sys.stderr)
        except Exception as e:
            if self._running:
                self._message_queue.put({
                    'type': 'error',
                    'error': str(e),
                    'context': 'reader_thread'
                })

    def _wait_for_message(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for next message from bridge"""
        try:
            return self._message_queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("No message received from SDK bridge")

    def _send_command(self, command: str, **kwargs):
        """Send a command to the bridge"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("SDK bridge not running")

        request = {
            'command': command,
            **kwargs
        }

        json_str = json.dumps(request) + '\n'
        self.process.stdin.write(json_str)
        self.process.stdin.flush()

    def query(
        self,
        message: str,
        cached_context: Optional[str] = None,
        session_id: Optional[str] = None,
        stream: bool = True,
        **options
    ) -> Iterator[str]:
        """
        Send a query to Claude Code.

        Args:
            message: The user message / dynamic prompt
            cached_context: Context to cache (TIER_1 files) - will be cached by Claude
            session_id: Session ID to resume (optional, will use current session if None)
            stream: If True, yields chunks as they arrive. If False, returns full response.
            **options: Additional options to pass to Claude Code SDK

        Yields:
            Text chunks as they arrive (if stream=True)

        Returns:
            Full response text (if stream=False)
        """
        # Reset response state
        self._last_response = ""
        self._last_usage = None
        self._last_metadata = None
        self._cache_stats = None

        # Send query command
        self._send_command(
            'query',
            message=message,
            cached_context=cached_context,
            session_id=session_id or self.session_id,
            cwd=str(self.cwd),
            options=options
        )

        # Process messages
        full_response = ""

        while True:
            msg = self._wait_for_message(timeout=300.0)  # 5 minute timeout
            msg_type = msg.get('type')

            if msg_type == 'error':
                error_msg = msg.get('error', 'Unknown error')
                raise RuntimeError(f"SDK Bridge error: {error_msg}")

            elif msg_type == 'status':
                status = msg.get('status')

                if status == 'initialized':
                    # Store session ID
                    self.session_id = msg.get('session_id')

                elif status == 'complete':
                    # Store metadata
                    self._last_metadata = ResponseMetadata(
                        session_id=self.session_id,
                        num_turns=msg.get('num_turns', 0),
                        duration_ms=msg.get('duration_ms', 0),
                        cost_usd=msg.get('cost_usd', 0.0)
                    )

                # Status messages don't need to be yielded
                continue

            elif msg_type == 'chunk':
                # Streaming content
                chunk = msg.get('content', '')
                full_response += chunk

                if stream:
                    yield chunk

            elif msg_type == 'response':
                # Final response
                self._last_response = msg.get('content', '')
                self._last_usage = msg.get('usage', {})

                # Update metadata with final info
                if self._last_metadata:
                    self._last_metadata.session_id = msg.get('session_id')
                    self._last_metadata.message_count = msg.get('message_count', 0)

                # If streaming, yield any content we haven't yielded yet
                # (in case no chunks were sent, or response came faster than chunks)
                if stream:
                    # Check if we've already yielded everything via chunks
                    if len(full_response) < len(self._last_response):
                        # There's content we haven't yielded yet
                        remaining = self._last_response[len(full_response):]
                        if remaining:
                            yield remaining
                            full_response = self._last_response
                else:
                    # Not streaming, yield the full response now
                    yield self._last_response

                # Response is complete, but wait for cache_stats
                continue

            elif msg_type == 'cache_stats':
                # Cache statistics
                self._cache_stats = CacheStats(
                    input_tokens=msg.get('input_tokens', 0),
                    output_tokens=msg.get('output_tokens', 0),
                    cache_creation_input_tokens=msg.get('cache_creation_input_tokens', 0),
                    cache_read_input_tokens=msg.get('cache_read_input_tokens', 0),
                    cache_savings_percent=msg.get('cache_savings_percent', 0.0),
                    cache_status=msg.get('cache_status', 'NONE')
                )

                # All done!
                break

    def get_last_response(self) -> str:
        """Get the last complete response"""
        return self._last_response

    def get_cache_stats(self) -> Optional[CacheStats]:
        """Get cache statistics from last query"""
        return self._cache_stats

    def get_metadata(self) -> Optional[ResponseMetadata]:
        """Get metadata from last query"""
        return self._last_metadata

    def clear_session(self):
        """Clear the current session - next query will start fresh"""
        self._send_command('clear_session')
        self.session_id = None

        # Wait for confirmation
        msg = self._wait_for_message(timeout=5.0)
        if msg['type'] == 'status' and msg.get('status') == 'session_cleared':
            return
        else:
            raise RuntimeError(f"Failed to clear session: {msg}")

    def close(self):
        """Close the SDK bridge"""
        if self.process:
            try:
                self._send_command('shutdown')
                self.process.wait(timeout=5.0)
            except:
                self.process.kill()
            finally:
                self._running = False
                self.process = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Convenience function for simple queries
def query_claude(
    message: str,
    cached_context: Optional[str] = None,
    cwd: Optional[Path] = None
) -> str:
    """
    Simple convenience function for one-off queries.

    Args:
        message: The message to send
        cached_context: Optional cached context (TIER_1 files)
        cwd: Working directory

    Returns:
        Full response text
    """
    with ClaudeSDKClient(cwd=cwd) as client:
        response = ""
        for chunk in client.query(message, cached_context=cached_context):
            response += chunk
        return response


if __name__ == "__main__":
    # Simple test
    print("Testing Claude SDK Client...")
    print()

    try:
        with ClaudeSDKClient() as client:
            print("Sending test query...")

            for chunk in client.query("Say 'Hello from the SDK!' in one sentence."):
                print(chunk, end='', flush=True)

            print("\n")
            print(client.get_cache_stats())

            print("\n✅ SDK bridge is working!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
