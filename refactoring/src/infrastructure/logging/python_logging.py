"""Adapters that implement the shared ``LoggingService`` using ``logging``."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

from ...shared.interfaces import LoggingService


def _format_context(context: Mapping[str, Any] | None) -> str:
    if not context:
        return ""
    try:
        serialized = json.dumps(context, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        serialized = str(dict(context))
    return f" | context={serialized}"


class PythonLoggingService(LoggingService):
    """Concrete LoggingService backed by ``logging.Logger``."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("rp")

    def debug(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        self._logger.debug(message + _format_context(context))

    def info(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        self._logger.info(message + _format_context(context))

    def warning(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        self._logger.warning(message + _format_context(context))

    def error(self, message: str, *, context: Mapping[str, Any] | None = None) -> None:
        self._logger.error(message + _format_context(context))

    def exception(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None:
        if exc is not None:
            self._logger.exception(message + _format_context(context), exc_info=exc)
        else:
            self._logger.exception(message + _format_context(context))


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure the root logger with a sane default format."""

    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
