"""Immutable automation data contracts used across the refactored pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AutomationContext:
    """Immutable context passed through the automation pipeline."""

    message: str
    rp_dir: Path
    config: dict[str, Any] = field(default_factory=dict)
    response_count: int = 0
    should_generate_arc: bool = False
    total_minutes: int = 0
    activities_desc: str = ""
    author_notes: str = ""  # AUTHOR'S_NOTES.md content (highest priority)
    active_genome: str | None = None  # Active Genome file if referenced in Author's Notes
    tier1_files: dict[str, str] = field(default_factory=dict)
    tier2_files: dict[str, str] = field(default_factory=dict)
    tier3_loaded_files: dict[str, str] = field(default_factory=dict)
    tiered_bundles: list[dict[str, Any]] = field(default_factory=list)
    tier3_files: list[Path] = field(default_factory=list)
    tier3_referenced_files: list[Path] = field(default_factory=list)
    escalated_files: list[Path] = field(default_factory=list)
    loaded_entities: list[str] = field(default_factory=list)
    in_scene_entities: list[str] = field(default_factory=list)
    referenced_entities: list[str] = field(default_factory=list)
    entities_with_cores: list[str] = field(default_factory=list)
    entities_with_archetypes: list[str] = field(default_factory=list)
    archetype_categories: dict[str, list[str]] = field(default_factory=dict)
    entities_with_modifiers: list[str] = field(default_factory=list)
    agent_context: str | None = None
    cached_background_context: str | None = None
    immediate_agent_context: str | None = None
    file_updates: list[dict[str, Any]] = field(default_factory=list)
    update_notification: str = ""
    profiler: Any | None = None
    profiling_enabled: bool = True
    # Session/timeline tracking for temporal consistency
    session_id: str = "main"
    parent_session: str | None = None
    branch_point: int | None = None

    def with_update(self, **kwargs: Any) -> AutomationContext:
        """Return a new context with updated values (immutably)."""

        return replace(self, **kwargs)

    def merge_agent_context(self) -> str:
        """Combine cached background and immediate agent contexts."""

        parts: list[str] = []
        if self.cached_background_context:
            parts.append(self.cached_background_context)
        if self.immediate_agent_context:
            parts.append(self.immediate_agent_context)
        return "\n\n".join(parts) if parts else ""

    @property
    def state_dir(self) -> Path:
        """Location of the RP state directory."""

        return self.rp_dir / "state"

    @property
    def has_file_updates(self) -> bool:
        """Return True if there are file updates queued."""

        return bool(self.file_updates)

    @property
    def arc_frequency(self) -> int:
        """Arc generation frequency from configuration."""

        return int(self.config.get("arc_frequency", 50))

    @property
    def auto_story_arc(self) -> bool:
        """Whether automatic story arc generation is enabled."""

        return bool(self.config.get("auto_story_arc", True))


@dataclass(frozen=True)
class LoadingContext:
    """Context used during tiered file loading operations."""

    rp_dir: Path
    response_count: int
    message: str
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def should_load_tier2(self) -> bool:
        """Determine if TIER2 files should be loaded based on response count."""

        return self.response_count % 10 == 0 or self.response_count == 1


@dataclass(frozen=True)
class AgentContext:
    """Context provided to automation agents."""

    message: str
    response_number: int
    loaded_entities: list[str] = field(default_factory=list)
    characters_in_scene: list[str] = field(default_factory=list)
    chapter: str | None = None
    previous_scenes: list[str] = field(default_factory=list)
    session_metadata: dict[str, Any] = field(default_factory=dict)  # Session/timeline metadata
    in_scene_entities: list[str] = field(default_factory=list)  # Entities in scene (full cards)
    referenced_entities: list[str] = field(default_factory=list)  # Referenced entities (basics only)

    @property
    def has_characters(self) -> bool:
        """Return True when characters are present in the scene."""

        return bool(self.characters_in_scene)


@dataclass(frozen=True)
class AutomationResult:
    """Outcome of automation execution."""

    success: bool
    enhanced_prompt: str | None = None
    cached_context: str | None = None
    dynamic_prompt: str | None = None
    loaded_entities: list[str] = field(default_factory=list)
    profiler: Any | None = None
    error: str | None = None

    @property
    def is_cached_mode(self) -> bool:
        """Return True when both cached and dynamic prompts are available."""

        return self.cached_context is not None and self.dynamic_prompt is not None
