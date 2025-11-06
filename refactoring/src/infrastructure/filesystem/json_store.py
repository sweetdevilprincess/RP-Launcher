"""JSON storage helper with merge semantics."""

from __future__ import annotations

import json
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...shared.interfaces import LoggingService


@dataclass(frozen=True)
class JsonStore:
    """Provide read/write helpers for JSON documents."""

    root: Path
    logger: LoggingService

    def read(self, relative_path: Path, *, default: Any | None = None) -> Any:
        """Load JSON data from disk."""

        path = self._resolve(relative_path)
        if not path.exists():
            if default is not None:
                self.logger.debug(
                    "json_store.read.default",
                    context={"path": str(path), "default_type": type(default).__name__},
                )
                return default
            raise FileNotFoundError(f"JSON file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            self.logger.error(
                "json_store.read.invalid_json",
                context={"path": str(path), "error": str(exc)},
            )
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    def write(
        self,
        relative_path: Path,
        data: Any,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """Persist JSON data to disk atomically.

        Uses temp file + atomic rename to prevent corruption from partial writes
        (e.g., process crashes or power loss during write).
        """

        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

        # Write to temporary file, then atomically rename
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(path)  # Atomic operation on both POSIX and Windows

        self.logger.debug(
            "json_store.write",
            context={"path": str(path), "bytes": len(serialized.encode("utf-8"))},
        )

    def merge(
        self,
        relative_path: Path,
        updates: Mapping[str, Any],
        *,
        create_if_missing: bool = True,
    ) -> None:
        """Deep-merge updates into the existing JSON document."""

        path = self._resolve(relative_path)
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    current: MutableMapping[str, Any] = json.load(handle)
            except json.JSONDecodeError as exc:
                self.logger.error(
                    "json_store.merge.invalid_json",
                    context={"path": str(path), "error": str(exc)},
                )
                raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
        else:
            if not create_if_missing:
                raise FileNotFoundError(f"JSON file not found: {path}")
            current = {}

        merged = self._deep_merge(current, updates)
        self.write(relative_path, merged)

    def _resolve(self, relative_path: Path) -> Path:
        candidate = (self.root / relative_path).resolve()
        try:
            root = self.root.resolve()
        except FileNotFoundError:
            root = self.root
        if hasattr(candidate, "is_relative_to"):
            if not candidate.is_relative_to(root):  # type: ignore[attr-defined]
                raise ValueError("JsonStore paths must stay within the configured root")
        elif not str(candidate).startswith(str(root)):
            raise ValueError("JsonStore paths must stay within the configured root")
        return candidate

    @staticmethod
    def _deep_merge(
        base: MutableMapping[str, Any], updates: Mapping[str, Any]
    ) -> MutableMapping[str, Any]:
        """Recursively merge update mapping into base."""

        merged: MutableMapping[str, Any] = base.copy()
        for key, value in updates.items():
            if (
                key in merged
                and isinstance(merged[key], MutableMapping)
                and isinstance(value, Mapping)
            ):
                merged[key] = JsonStore._deep_merge(merged[key], value)  # type: ignore[assignment]
            else:
                merged[key] = value
        return merged
