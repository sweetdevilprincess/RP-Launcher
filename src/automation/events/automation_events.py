#!/usr/bin/env python3
"""
Automation Events

Specific event types for the automation system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List

from src.automation.events.event_bus import Event


@dataclass
class FileLoadedEvent(Event):
    """Event fired when a file is loaded."""
    filename: str = ""
    file_path: Optional[Path] = None
    tier: Optional[str] = None
    size_bytes: int = 0


@dataclass
class AgentCompletedEvent(Event):
    """Event fired when an agent completes execution."""
    agent_id: str = ""
    agent_type: str = ""
    execution_time: float = 0.0
    success: bool = True
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentStartedEvent(Event):
    """Event fired when an agent starts."""
    agent_id: str = ""
    agent_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStageEvent(Event):
    """Event fired during pipeline execution."""
    stage_name: str = ""
    stage_type: str = ""  # 'started', 'completed', 'failed', 'skipped'
    execution_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ConfigurationChangedEvent(Event):
    """Event fired when configuration changes."""
    config_file: Optional[Path] = None
    changed_keys: List[str] = field(default_factory=list)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorEvent(Event):
    """Event fired when an error occurs."""
    error_type: str = ""
    error_message: str = ""
    component: str = ""
    stack_trace: Optional[str] = None
    recoverable: bool = True


@dataclass
class ResponseGeneratedEvent(Event):
    """Event fired when a response is generated."""
    response_number: int = 0
    response_length: int = 0
    model: str = ""
    cache_mode: bool = False


@dataclass
class EntityDetectedEvent(Event):
    """Event fired when entities are detected in a message."""
    entity_names: List[str] = field(default_factory=list)
    message: str = ""
    confidence: float = 0.0


@dataclass
class MemoryCreatedEvent(Event):
    """Event fired when a memory is created."""
    memory_type: str = ""
    entity_name: Optional[str] = None
    content: str = ""
    importance: int = 5


@dataclass
class StoryArcGeneratedEvent(Event):
    """Event fired when a story arc is generated."""
    arc_number: int = 0
    arc_content: str = ""
    trigger_reason: str = ""


@dataclass
class FileChangedEvent(Event):
    """Event fired when a file is changed (for file watching)."""
    file_path: Path = field(default_factory=Path)
    change_type: str = ""  # 'created', 'modified', 'deleted'
    previous_content: Optional[str] = None
    new_content: Optional[str] = None


@dataclass
class ProfilingEvent(Event):
    """Event fired for profiling data."""
    operation_name: str = ""
    duration_seconds: float = 0.0
    component: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationFailedEvent(Event):
    """Event fired when validation fails."""
    validation_type: str = ""
    failures: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheHitEvent(Event):
    """Event fired on cache hit/miss."""
    cache_key: str = ""
    hit: bool = False
    cache_type: str = ""


@dataclass
class StatusUpdateEvent(Event):
    """Event fired when status is updated."""
    status_file: Optional[Path] = None
    response_count: int = 0
    loaded_entities: List[str] = field(default_factory=list)
