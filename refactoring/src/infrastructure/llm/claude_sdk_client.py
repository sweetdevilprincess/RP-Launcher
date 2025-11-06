"""Claude SDK streaming client - Full implementation using Node.js bridge."""

from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Dict

from .base import (
    ConversationHistory,
    LLMResponse,
    ProviderCapabilities,
    StreamingLLMClient,
    UsageStats,
)


@dataclass
class CacheStats:
    """Cache statistics from Claude API."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_savings_percent: float = 0.0
    cache_status: str = 'NONE'


@dataclass
class ResponseMetadata:
    """Metadata about the response."""
    session_id: Optional[str] = None
    num_turns: int = 0
    duration_ms: int = 0
    cost_usd: float = 0.0
    message_count: int = 0


class ClaudeSDKStreamingClient(StreamingLLMClient):
    """Python client for Claude Code SDK bridge.

    Manages a persistent Node.js process running the SDK bridge,
    communicating via JSON over stdin/stdout.
    """

    provider_id = "anthropic_sdk"

    def __init__(
        self,
        *,
        rp_dir: Path | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize SDK client.

        Args:
            rp_dir: Working directory for Claude Code (defaults to current)
            project_root: Alternative to rp_dir for compatibility
        """
        self.cwd = rp_dir or project_root or Path.cwd()
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

        self._capabilities = ProviderCapabilities(
            supports_streaming=True,
            supports_prompt_cache=True,
            supports_thinking_budget=True,
            native_system_role=False,  # SDK handles system via cache/session
        )

    def _start_bridge(self):
        """Start the Node.js SDK bridge process."""
        # Find bridge script relative to this file
        bridge_script = Path(__file__).parent / "claude_sdk_bridge.mjs"

        if not bridge_script.exists():
            raise FileNotFoundError(
                f"SDK bridge script not found: {bridge_script}\n"
                f"Run 'setup.sh' (or 'setup.bat' on Windows) from project root to install dependencies."
            )

        # Start Node.js process
        try:
            self.process = subprocess.Popen(
                ['node', str(bridge_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # Explicitly use UTF-8 to handle all Unicode characters
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
            raise RuntimeError(
                "Node.js not found. Please install Node.js to use the SDK bridge.\n"
                "Download from: https://nodejs.org"
            )
        except Exception as e:
            if self.process:
                self.process.kill()
            raise RuntimeError(f"Failed to start SDK bridge: {e}")

    def _read_messages(self):
        """Background thread to read messages from bridge."""
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
        """Wait for next message from bridge."""
        try:
            return self._message_queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("No message received from SDK bridge")

    def _send_command(self, command: str, **kwargs):
        """Send a command to the bridge."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("SDK bridge not running")

        request = {
            'command': command,
            **kwargs
        }

        json_str = json.dumps(request) + '\n'
        self.process.stdin.write(json_str)
        self.process.stdin.flush()

    # ------------------------------------------------------------------
    # StreamingLLMClient interface implementation
    # ------------------------------------------------------------------

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities

    def stream_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        thinking_mode: str = "megathink",
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> Iterable[str]:
        """Send a query to Claude Code with streaming response.

        Args:
            user_message: The user message / dynamic prompt
            cached_context: Context to cache (TIER_1 files) - will be cached by Claude
            conversation_history: Previous conversation messages (loaded from session file)
            max_tokens: Not used - SDK controls this
            thinking_mode: Thinking mode preset ("disabled", "think", "megathink", etc.)
            thinking_budget: Custom thinking token budget (overrides thinking_mode)
            **kwargs: Additional options to pass to Claude Code SDK

        Note:
            The SDK does not expose temperature configuration - it uses its own optimized settings.

        Yields:
            Text chunks as they arrive
        """
        # Reset response state
        self._last_response = ""
        self._last_usage = None
        self._last_metadata = None
        self._cache_stats = None

        # Send query command
        self._send_command(
            'query',
            message=user_message,
            cached_context=cached_context,
            conversation_history=conversation_history,
            session_id=self.session_id,
            cwd=str(self.cwd),
            thinking_mode=thinking_mode,
            thinking_budget=thinking_budget,
            options=kwargs
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
                yield chunk

            elif msg_type == 'response':
                # Final response
                self._last_response = msg.get('content', '')
                self._last_usage = msg.get('usage', {})

                # Update metadata with final info
                if self._last_metadata:
                    self._last_metadata.session_id = msg.get('session_id')
                    self._last_metadata.message_count = msg.get('message_count', 0)

                # Only yield content if we haven't streamed it already
                # The bridge sends empty content if it already streamed chunks
                if self._last_response and len(full_response) < len(self._last_response):
                    # There's content we haven't yielded yet
                    remaining = self._last_response[len(full_response):]
                    if remaining:
                        yield remaining
                        full_response = self._last_response

                # If response was already streamed, use the accumulated chunks
                if not self._last_response and full_response:
                    self._last_response = full_response

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

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        thinking_mode: str = "megathink",
        thinking_budget: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send message and get complete response (non-streaming).

        Args:
            user_message: The user message
            cached_context: Context to cache
            conversation_history: Previous conversation messages (loaded from session file)
            max_tokens: Not used - SDK controls this
            thinking_mode: Thinking mode preset
            thinking_budget: Custom thinking budget
            **kwargs: Additional options

        Note:
            The SDK does not expose temperature configuration - it uses its own optimized settings.

        Returns:
            Complete LLM response with usage stats
        """
        # Collect all chunks
        chunks = list(self.stream_message(
            user_message,
            cached_context=cached_context,
            conversation_history=conversation_history,
            max_tokens=max_tokens,
            thinking_mode=thinking_mode,
            thinking_budget=thinking_budget,
            **kwargs
        ))

        content = "".join(chunks)
        usage = self._build_usage_stats()

        return LLMResponse(
            content=content,
            usage=usage,
            raw_response={
                "cache_stats": self._cache_stats,
                "metadata": self._last_metadata,
            },
            thinking=None,  # SDK doesn't separate thinking output yet
        )

    # ------------------------------------------------------------------
    # Additional helpers
    # ------------------------------------------------------------------

    def clear_session(self) -> None:
        """Clear the current session - next query will start fresh."""
        self._send_command('clear_session')
        self.session_id = None

        # Wait for confirmation
        msg = self._wait_for_message(timeout=5.0)
        if msg['type'] == 'status' and msg.get('status') == 'session_cleared':
            return
        else:
            raise RuntimeError(f"Failed to clear session: {msg}")

    def close(self):
        """Close the SDK bridge."""
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
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    def get_last_response(self) -> str:
        """Get the last complete response."""
        return self._last_response

    def get_cache_stats(self) -> Optional[CacheStats]:
        """Get cache statistics from last query."""
        return self._cache_stats

    def get_metadata(self) -> Optional[ResponseMetadata]:
        """Get metadata from last query."""
        return self._last_metadata

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_usage_stats(self) -> UsageStats:
        """Build usage stats from SDK response."""
        usage_data: dict[str, Any] = self._last_usage or {}
        cache_stats = self._cache_stats

        input_tokens = (
            usage_data.get("input_tokens")
            or usage_data.get("prompt_tokens")
            or (cache_stats.input_tokens if cache_stats else 0)
        )
        output_tokens = (
            usage_data.get("output_tokens")
            or usage_data.get("completion_tokens")
            or (cache_stats.output_tokens if cache_stats else 0)
        )

        cache_creation = cache_read = 0
        if cache_stats:
            cache_creation = cache_stats.cache_creation_input_tokens
            cache_read = cache_stats.cache_read_input_tokens

        return UsageStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
        )


__all__ = ["ClaudeSDKStreamingClient"]
