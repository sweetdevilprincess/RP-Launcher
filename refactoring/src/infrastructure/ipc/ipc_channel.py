"""Schema-validated IPC channel for automation state exchanges."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...shared.interfaces import LoggingService

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from ..filesystem.file_manager import FileManager


_INPUT_FILE = Path("rp_client_input.json")
_RESPONSE_FILE = Path("rp_client_response.json")
_TRIGGERS_FILE = Path("session_triggers.json")


@dataclass(frozen=True)
class IpcInputPayload:
    message: str
    timestamp: str


@dataclass(frozen=True)
class IpcResponsePayload:
    response: str
    timestamp: str
    model: str | None = None
    cache_stats: Mapping[str, Any] | None = None


class IpcChannel:
    """High-level API for reading/writing automation IPC payloads."""

    def __init__(self, *, file_manager: FileManager, logger: LoggingService) -> None:
        self._file_manager = file_manager
        self._logger = logger

    # ------------------------------------------------------------------
    # Input payloads

    def write_input(self, message: str) -> None:
        message = message.strip()
        if not message:
            raise ValueError("IPC input message cannot be empty")
        payload = {
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._file_manager.write_json(_INPUT_FILE, payload)

    def read_input(self) -> IpcInputPayload | None:
        data = self._file_manager.read_json(_INPUT_FILE, default=None)
        if data is None:
            legacy_file = self._legacy_path("rp_client_input.txt")
            if legacy_file.exists():
                legacy_message = legacy_file.read_text(encoding="utf-8").strip()
                if legacy_message:
                    self.write_input(legacy_message)
                legacy_file.unlink(missing_ok=True)  # type: ignore[arg-type]
                return IpcInputPayload(
                    message=legacy_message, timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                )
            return None
        return self._validate_input_payload(data)

    # ------------------------------------------------------------------
    # Response payloads

    def write_response(
        self,
        response: str,
        *,
        model: str | None = None,
        cache_stats: Mapping[str, Any] | None = None,
    ) -> None:
        response = response.strip()
        if not response:
            raise ValueError("IPC response cannot be empty")
        payload: dict[str, Any] = {
            "response": response,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if model:
            payload["model"] = model
        if cache_stats is not None:
            payload["cache_stats"] = dict(cache_stats)
        self._file_manager.write_json(_RESPONSE_FILE, payload)

    def read_response(self) -> IpcResponsePayload | None:
        data = self._file_manager.read_json(_RESPONSE_FILE, default=None)
        if data is None:
            legacy_file = self._legacy_path("rp_client_response.txt")
            if legacy_file.exists():
                response = legacy_file.read_text(encoding="utf-8").strip()
                if response:
                    self.write_response(response)
                legacy_file.unlink(missing_ok=True)  # type: ignore[arg-type]
                return IpcResponsePayload(
                    response=response, timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                )
            return None
        return self._validate_response_payload(data)

    # ------------------------------------------------------------------
    # Session triggers

    def read_session_triggers(self) -> list[str]:
        data = self._file_manager.read_json(_TRIGGERS_FILE, default=None)
        if isinstance(data, list):
            return [str(item).strip() for item in data if str(item).strip()]
        legacy_file = self._legacy_path("session_triggers.txt")
        if legacy_file.exists():
            names = [
                line.strip()
                for line in legacy_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if names:
                self.write_session_triggers(names)
            legacy_file.unlink(missing_ok=True)  # type: ignore[arg-type]
            return names
        return []

    def write_session_triggers(self, characters: Sequence[str]) -> None:
        cleaned = [name.strip() for name in characters if name and name.strip()]
        self._file_manager.write_json(_TRIGGERS_FILE, cleaned)

    # ------------------------------------------------------------------
    # Validation helpers

    def _validate_input_payload(self, data: Mapping[str, Any]) -> IpcInputPayload:
        message = data.get("message")
        timestamp = data.get("timestamp")
        if not isinstance(message, str):
            raise ValueError("IPC input payload missing string 'message'")
        if not isinstance(timestamp, str):
            raise ValueError("IPC input payload missing string 'timestamp'")
        return IpcInputPayload(message=message, timestamp=timestamp)

    def _validate_response_payload(self, data: Mapping[str, Any]) -> IpcResponsePayload:
        response = data.get("response")
        timestamp = data.get("timestamp")
        model = data.get("model")
        cache_stats = data.get("cache_stats")
        if not isinstance(response, str):
            raise ValueError("IPC response payload missing string 'response'")
        if not isinstance(timestamp, str):
            raise ValueError("IPC response payload missing string 'timestamp'")
        if model is not None and not isinstance(model, str):
            raise ValueError("IPC response payload 'model' must be a string if provided")
        if cache_stats is not None and not isinstance(cache_stats, Mapping):
            raise ValueError("IPC response payload 'cache_stats' must be a mapping if provided")
        return IpcResponsePayload(
            response=response,
            timestamp=timestamp,
            model=model,
            cache_stats=cache_stats if cache_stats is None else dict(cache_stats),
        )

    def _legacy_path(self, name: str) -> Path:
        return self._file_manager.paths.state_dir / name
