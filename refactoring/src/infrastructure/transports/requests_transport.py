"""Requests-based implementation of the shared Transport protocol."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import requests

from ...shared.interfaces import Transport, TransportError, TransportRequest, TransportResponse


class RequestsTransport(Transport):
    """Concrete transport that delegates to ``requests.Session``."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def post(self, request: TransportRequest) -> TransportResponse:
        return self._send("post", request)

    def get(self, request: TransportRequest) -> TransportResponse:
        return self._send("get", request)

    def post_stream(self, request: TransportRequest) -> Iterable[str]:
        """Send a POST request with streaming enabled and yield text chunks.

        Parses Server-Sent Events (SSE) from Anthropic API and yields
        content deltas as they arrive.
        """
        try:
            response = self._session.post(
                request.endpoint,
                json=request.payload,
                headers=request.headers,
                timeout=request.timeout_seconds,
                stream=True,  # Enable streaming
            )
            response.raise_for_status()  # Raise for HTTP errors
        except requests.RequestException as exc:
            raise TransportError(str(exc)) from exc

        # Parse SSE stream and yield text chunks
        for chunk in _parse_sse_stream(response):
            yield chunk

    # ------------------------------------------------------------------

    def _send(self, method: str, request: TransportRequest) -> TransportResponse:
        try:
            response = self._session.request(
                method,
                request.endpoint,
                json=request.payload,
                headers=request.headers,
                timeout=request.timeout_seconds,
            )
        except requests.RequestException as exc:  # pragma: no cover - pass-through wrapper
            raise TransportError(str(exc)) from exc

        return TransportResponse(
            status_code=response.status_code,
            body=_parse_body(response),
            headers=dict(response.headers),
        )


def _parse_body(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _parse_sse_stream(response: requests.Response) -> Iterable[str]:
    """Parse Server-Sent Events stream from Anthropic API.

    Yields text chunks from content_block_delta events.

    SSE Format:
        event: content_block_delta
        data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}

    Args:
        response: Streaming response from requests

    Yields:
        Text chunks from delta events
    """
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        # Parse data lines
        if line.startswith("data: "):
            data_str = line[6:]  # Remove "data: " prefix

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue  # Skip malformed JSON

            # Extract text from content_block_delta events
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        yield text
