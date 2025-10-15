"""
Event Bus System

Provides event-driven architecture for decoupling components.
"""

from src.automation.events.event_bus import (
    Event,
    EventHandler,
    EventBus,
    get_event_bus,
    subscribe,
    publish
)
from src.automation.events.automation_events import (
    FileLoadedEvent,
    AgentCompletedEvent,
    PipelineStageEvent,
    ConfigurationChangedEvent,
    ErrorEvent
)

__all__ = [
    # Core
    'Event',
    'EventHandler',
    'EventBus',
    'get_event_bus',
    'subscribe',
    'publish',

    # Events
    'FileLoadedEvent',
    'AgentCompletedEvent',
    'PipelineStageEvent',
    'ConfigurationChangedEvent',
    'ErrorEvent'
]
