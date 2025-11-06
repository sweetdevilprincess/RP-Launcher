"""Logging wrapper around another transport."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ...shared.interfaces import LoggingService, Transport, TransportRequest, TransportResponse


class LoggingTransport(Transport):
    """Decorates another transport to emit structured logs."""

    def __init__(
        self, transport: Transport, logger: LoggingService, *, name: str = "transport"
    ) -> None:
        self._transport = transport
        self._logger = logger
        self._name = name

    def post(self, request: TransportRequest) -> TransportResponse:
        self._log_request("post", request)
        response = self._transport.post(request)
        self._log_response("post", request, response)
        return response

    def get(self, request: TransportRequest) -> TransportResponse:
        self._log_request("get", request)
        response = self._transport.get(request)
        self._log_response("get", request, response)
        return response

    def post_stream(self, request: TransportRequest) -> Iterable[str]:
        """Log streaming request start and pass through chunks from wrapped transport."""
        self._log_request("post_stream", request)
        chunk_count = 0

        # Yield chunks from wrapped transport
        for chunk in self._transport.post_stream(request):
            chunk_count += 1
            yield chunk

        # Log completion with chunk count
        self._logger.debug(
            f"{self._name}.post_stream.complete",
            context={
                "endpoint": request.endpoint,
                "chunks_received": chunk_count,
            },
        )

    # ------------------------------------------------------------------

    def _log_request(self, method: str, request: TransportRequest) -> None:
        self._logger.debug(
            f"{self._name}.{method}",
            context={
                "endpoint": request.endpoint,
                "headers": _mask_sensitive_headers(request.headers),
                "timeout": request.timeout_seconds,
            },
        )

    def _log_response(
        self,
        method: str,
        request: TransportRequest,
        response: TransportResponse,
    ) -> None:
        self._logger.debug(
            f"{self._name}.{method}.response",
            context={
                "endpoint": request.endpoint,
                "status_code": response.status_code,
            },
        )


def _mask_sensitive_headers(headers: Mapping[str, str] | None) -> Mapping[str, str]:
    if not headers:
        return {}
    masked = dict(headers)
    for key in list(masked.keys()):
        if key.lower() in {"authorization", "x-proxy-authorization"}:
            masked[key] = "***"
    return masked
