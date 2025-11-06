"""Shared configuration helpers for multi-provider LLM settings."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ...shared.logging import get_logger

_logger = get_logger(__name__)


def read_json_file(path: Path) -> dict[str, Any]:
    """Read and parse a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON data as dict, or empty dict if file doesn't exist or parsing fails
    """
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                return data
    except Exception as exc:
        _logger.error(
            "config.json_file.read_failed",
            context={"path": str(path), "error": str(exc)},
        )
    return {}


def read_env_file(path: Path) -> dict[str, str]:
    """Read and parse an environment file.

    Args:
        path: Path to .env file

    Returns:
        Dict of environment variables, or empty dict if file doesn't exist or parsing fails
    """
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    except Exception as exc:
        _logger.error(
            "config.env_file.parse_failed",
            context={"path": str(path), "error": str(exc)},
        )
    return values


def pick_first(values: Iterable[str | None]) -> str | None:
    for value in values:
        if value:
            cleaned = value.strip()
            if cleaned:
                return cleaned
    return None


def resolve_project_root(start: Path | None = None) -> Path:
    current = start or Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "config").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def merge_config_sources(
    *,
    env_keys: dict[str, str],
    config_keys: dict[str, str],
    env_file_keys: dict[str, str],
) -> dict[str, str | None]:
    merged: dict[str, str | None] = {}
    for logical_key, env_key in env_keys.items():
        candidates = [
            os.environ.get(env_key),
            config_keys.get(logical_key),
            env_file_keys.get(env_key),
        ]
        merged[logical_key] = pick_first(candidates)
    return merged


__all__ = [
    "merge_config_sources",
    "pick_first",
    "read_env_file",
    "read_json_file",
    "resolve_project_root",
]
