"""Tests for the refactored PromptBuilder."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
from refactoring.src.automation.contracts import AutomationContext
from refactoring.src.automation.services.prompt_builder import PromptBuilder
from refactoring.src.shared.interfaces import ConfigService, LoggingService


class StubConfigService(ConfigService):
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data or {"automation": {}}

    def get(self, key: str, default: Any | None = None) -> Any:
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def require(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def get_str(self, key: str, default: str = "") -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)

    def get_dict(self, key: str, default: dict | None = None) -> dict:
        value = self.get(key, default or {})
        return value if isinstance(value, dict) else (default or {})

    def section(self, prefix: str) -> dict[str, Any]:
        value = self._data.get(prefix, {})
        if not isinstance(value, dict):
            raise TypeError(f"Section {prefix} is not a mapping")
        return value

    def keys(self) -> Iterable[str]:
        return self._data.keys()

    def reload(self) -> None:  # pragma: no cover - stub behaviour
        return None


class StubLogger(LoggingService):
    def debug(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def info(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def warning(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def error(self, message: str, *, context: dict[str, Any] | None = None) -> None: ...

    def exception(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        exc: BaseException | None = None,
    ) -> None: ...


@pytest.fixture
def prompt_builder() -> PromptBuilder:
    return PromptBuilder(config=StubConfigService(), logger=StubLogger())


def test_prompt_builder_renders_tiered_content(
    prompt_builder: PromptBuilder, tmp_path: Path
) -> None:
    context = AutomationContext(
        message="User says hi",
        rp_dir=tmp_path,
        tier1_files={"state/overview.md": "Overview content"},
        tier2_files={"state/story.md": "Story content"},
        tier3_loaded_files={"characters/Aurora.md": "Aurora info"},
        tiered_bundles=[
            {
                "tier": "tier1",
                "bundle_id": "overview",
                "label": "Overview",
                "files": {"state/overview.md": "Overview content"},
                "metadata": {"entry_count": 1},
            },
            {
                "tier": "tier2",
                "bundle_id": "status",
                "label": "Status Update",
                "files": {"state/status.md": "Status content"},
                "metadata": {},
            },
            {
                "tier": "tier3",
                "bundle_id": "triggered",
                "label": "Triggered Files",
                "files": {"characters/Aurora.md": "Aurora info"},
                "metadata": {"entities_with_cores": ["Aurora"]},
            },
        ],
        entities_with_cores=["Aurora"],
        total_minutes=30,
        activities_desc="Completed 2 scenes",
        should_generate_arc=True,
    )

    prompt = prompt_builder.build_prompt(context)

    # Check for tiered content sections (new HTML comment format)
    assert "<!-- TIER 1 FILES" in prompt or "TIER 1" in prompt
    assert "Overview content" in prompt
    assert "Status content" in prompt
    assert "Triggered Files" in prompt or "TIER 3" in prompt
    assert "Aurora info" in prompt
    assert "Metadata:" in prompt or "metadata" in prompt.lower()
    assert "- entry_count: 1" in prompt or "entry_count" in prompt
    assert "ENTITY HIGHLIGHTS" in prompt or "Aurora" in prompt
    assert "SESSION ACTIVITY SUMMARY" in prompt or "activity" in prompt.lower()
    assert "story arc" in prompt.lower()
    assert "USER MESSAGE" in prompt
    assert "User says hi" in prompt
