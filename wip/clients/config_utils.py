"""Shared configuration helpers for multi-provider LLM settings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def read_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                return data
    except Exception as exc:
        print(f"??  Failed to read JSON from {path}: {exc}")
    return {}


def read_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}

    values: Dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    except Exception as exc:
        print(f"??  Failed to parse env file {path}: {exc}")
    return values


def pick_first(values: Iterable[Optional[str]]) -> Optional[str]:
    for value in values:
        if value:
            cleaned = value.strip()
            if cleaned:
                return cleaned
    return None


def resolve_project_root(start: Optional[Path] = None) -> Path:
    current = start or Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "config").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def merge_config_sources(
    *,
    env_keys: Dict[str, str],
    config_keys: Dict[str, str],
    env_file_keys: Dict[str, str],
) -> Dict[str, Optional[str]]:
    merged: Dict[str, Optional[str]] = {}
    for logical_key, env_key in env_keys.items():
        candidates = [
            os.environ.get(env_key),
            config_keys.get(logical_key),
            env_file_keys.get(env_key),
        ]
        merged[logical_key] = pick_first(candidates)
    return merged


__all__ = [
    "read_json_file",
    "read_env_file",
    "pick_first",
    "resolve_project_root",
    "merge_config_sources",
]
