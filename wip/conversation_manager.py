"""Shared conversation state helpers for multi-LLM prototype.

This WIP module mirrors the existing ConversationManager logic that currently
lives inside `src/clients/claude_api.py`, but removes Anthropic-specific naming
so we can share it between providers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationManager:
    """Persist conversation history for an RP session.

    The conversation history is stored as JSON at
    `<state_dir>/conversation_history.json` using the existing array-of-dicts
    format so we remain backward compatible.
    """

    def __init__(self, state_dir: Path | str) -> None:
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.state_dir / "conversation_history.json"
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        if self.history_file.exists():
            try:
                with self.history_file.open("r", encoding="utf-8") as fp:
                    loaded = json.load(fp)
                    if isinstance(loaded, list):
                        self.history = loaded
            except Exception as exc:
                print(f"??  Failed to load conversation history: {exc}")
                self.history = []

    def _save_history(self) -> None:
        try:
            with self.history_file.open("w", encoding="utf-8") as fp:
                json.dump(self.history, fp, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"??  Failed to save conversation history: {exc}")

    def add_user_message(self, content: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry: Dict[str, Any] = {"role": "user", "content": content}
        if metadata:
            entry["metadata"] = metadata
        self.history.append(entry)
        self._save_history()

    def add_assistant_message(self, content: str, *, metadata: Optional[Dict[str, Any]] = None) -> None:
        entry: Dict[str, Any] = {"role": "assistant", "content": content}
        if metadata:
            entry["metadata"] = metadata
        self.history.append(entry)
        self._save_history()

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def clear_history(self) -> None:
        self.history = []
        if self.history_file.exists():
            try:
                self.history_file.unlink()
            except Exception as exc:
                print(f"??  Failed to clear conversation history: {exc}")


__all__ = ["ConversationManager"]
