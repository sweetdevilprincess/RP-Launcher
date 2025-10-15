#!/usr/bin/env python3
"""
Automation Context Objects

Immutable context objects that flow through the automation pipeline.
Replaces parameter sprawl and makes data flow explicit.
"""

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class AutomationContext:
    """
    Immutable context passed through automation pipeline.

    This replaces the dozens of parameters passed between methods,
    providing a clean, typed, and traceable data flow.
    """
    # Core inputs
    message: str
    rp_dir: Path

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Computed values
    response_count: int = 0
    should_generate_arc: bool = False
    total_minutes: int = 0
    activities_desc: str = ""

    # File collections
    tier1_files: Dict[str, str] = field(default_factory=dict)
    tier2_files: Dict[str, str] = field(default_factory=dict)
    tier3_files: List[Path] = field(default_factory=list)
    escalated_files: List[Path] = field(default_factory=list)

    # Entity data
    loaded_entities: List[str] = field(default_factory=list)
    entities_with_cores: List[str] = field(default_factory=list)

    # Agent results
    agent_context: Optional[str] = None
    cached_background_context: Optional[str] = None
    immediate_agent_context: Optional[str] = None

    # File updates
    file_updates: List[Dict] = field(default_factory=list)
    update_notification: str = ""

    # Profiling
    profiler: Optional[Any] = None
    profiling_enabled: bool = True

    def with_update(self, **kwargs) -> 'AutomationContext':
        """
        Return new context with updates (immutable pattern).

        Example:
            context = context.with_update(response_count=5, should_generate_arc=True)
        """
        return replace(self, **kwargs)

    def merge_agent_context(self) -> str:
        """Combine cached background and immediate agent contexts."""
        parts = []
        if self.cached_background_context:
            parts.append(self.cached_background_context)
        if self.immediate_agent_context:
            parts.append(self.immediate_agent_context)
        return "\n\n".join(parts) if parts else ""

    @property
    def state_dir(self) -> Path:
        """Convenience property for state directory."""
        return self.rp_dir / "state"

    @property
    def has_file_updates(self) -> bool:
        """Check if there are file updates to notify about."""
        return bool(self.file_updates)

    @property
    def arc_frequency(self) -> int:
        """Get arc frequency from config."""
        return self.config.get('arc_frequency', 50)

    @property
    def auto_story_arc(self) -> bool:
        """Check if automatic story arc generation is enabled."""
        return self.config.get('auto_story_arc', True)


@dataclass(frozen=True)
class LoadingContext:
    """Context for file loading operations."""
    rp_dir: Path
    response_count: int
    message: str
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def should_load_tier2(self) -> bool:
        """Determine if TIER2 files should be loaded based on response count."""
        # Load every 10 responses or on first response
        return self.response_count % 10 == 0 or self.response_count == 1


@dataclass(frozen=True)
class AgentContext:
    """Context for agent execution."""
    message: str
    response_number: int
    loaded_entities: List[str] = field(default_factory=list)
    characters_in_scene: List[str] = field(default_factory=list)
    chapter: Optional[str] = None
    previous_scenes: List[str] = field(default_factory=list)

    @property
    def has_characters(self) -> bool:
        """Check if there are characters in the scene."""
        return bool(self.characters_in_scene)


@dataclass(frozen=True)
class AutomationResult:
    """Result of automation execution."""
    success: bool
    enhanced_prompt: Optional[str] = None
    cached_context: Optional[str] = None
    dynamic_prompt: Optional[str] = None
    loaded_entities: List[str] = field(default_factory=list)
    profiler: Optional[Any] = None
    error: Optional[str] = None

    @property
    def is_cached_mode(self) -> bool:
        """Check if this result is from cached mode execution."""
        return self.cached_context is not None and self.dynamic_prompt is not None