"""Utilities for deriving stateful file system paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StatePaths:
    """Derive common filesystem locations for an RP directory."""

    rp_dir: Path

    @property
    def state_dir(self) -> Path:
        return self.rp_dir / "state"

    @property
    def entities_dir(self) -> Path:
        return self.rp_dir / "entities"

    @property
    def characters_dir(self) -> Path:
        return self.rp_dir / "characters"

    @property
    def memories_dir(self) -> Path:
        return self.rp_dir / "memories"

    @property
    def chapters_dir(self) -> Path:
        return self.rp_dir / "chapters"

    @property
    def backups_dir(self) -> Path:
        return self.state_dir / "backups"

    @property
    def sessions_dir(self) -> Path:
        return self.rp_dir / "sessions"

    @property
    def session_branches_dir(self) -> Path:
        return self.sessions_dir / "branches"

    @property
    def session_archived_dir(self) -> Path:
        return self.sessions_dir / "archived"

    def response_counter_file(self) -> Path:
        return self.state_dir / "response_counter.json"

    def automation_config_file(self) -> Path:
        return self.state_dir / "automation_config.json"

    def agent_cache_file(self) -> Path:
        return self.state_dir / "agent_analysis.json"

    def active_session_file(self) -> Path:
        return self.sessions_dir / "session_main.json"

    def proxy_prompt_file(self) -> Path:
        return self.rp_dir.parent / "config" / "proxy_prompt.txt"

    def chapter_file(self, chapter_num: int) -> Path:
        return self.chapters_dir / f"chapter_{chapter_num:03d}.md"

    def memory_file(self, character_name: str) -> Path:
        return self.memories_dir / f"{character_name}_memories.md"

    def character_file(self, character_name: str) -> Path:
        return self.characters_dir / f"{character_name}.md"

    def state_file(self, filename: str) -> Path:
        return self.state_dir / filename
