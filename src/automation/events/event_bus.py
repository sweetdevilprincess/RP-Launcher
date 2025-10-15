#!/usr/bin/env python3
"""
Event Bus Implementation

Provides pub/sub event system for decoupling components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type
from collections import defaultdict
import traceback


@dataclass
class Event:
    """Base class for all events."""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set event type automatically."""
        if not hasattr(self, 'event_type'):
            self.event_type = self.__class__.__name__


class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    def handle(self, event: Event) -> None:
        """
        Handle an event.

        Args:
            event: Event to handle
        """
        pass

    def can_handle(self, event: Event) -> bool:
        """
        Check if this handler can handle the event.

        Args:
            event: Event to check

        Returns:
            True if handler can handle this event
        """
        return True


class EventBus:
    """
    Event bus for pub/sub messaging.

    Provides decoupled communication between components.
    """

    def __init__(self):
        """Initialize event bus."""
        # Map of event type -> list of handlers
        self._handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)

        # Map of event type -> list of filters
        self._filters: Dict[Type[Event], List[Callable]] = defaultdict(list)

        # Event history (for debugging)
        self._history: List[Event] = []
        self._max_history = 100

        # Statistics
        self._stats: Dict[str, int] = defaultdict(int)

    def subscribe(self, event_type: Type[Event],
                 handler: Callable[[Event], None],
                 filter_func: Optional[Callable[[Event], bool]] = None) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Handler function
            filter_func: Optional filter function
        """
        self._handlers[event_type].append(handler)

        if filter_func:
            self._filters[event_type].append(filter_func)

        self._stats['subscriptions'] += 1

    def unsubscribe(self, event_type: Type[Event],
                   handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self._stats['subscriptions'] -= 1
            except ValueError:
                pass

    def publish(self, event: Event, async_mode: bool = False) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event to publish
            async_mode: Whether to handle events asynchronously
        """
        # Add to history
        self._add_to_history(event)

        # Update stats
        self._stats['events_published'] += 1
        self._stats[f'events_{event.__class__.__name__}'] += 1

        # Get handlers for this event type
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        # Also get handlers for parent types
        for parent in event_type.__mro__[1:]:
            if parent in self._handlers:
                handlers.extend(self._handlers[parent])

        if not handlers:
            return

        # Get filters for this event type
        filters = self._filters.get(event_type, [])

        # Apply filters
        for filter_func in filters:
            try:
                if not filter_func(event):
                    return  # Event filtered out
            except Exception as e:
                self._log_error(f"Filter error: {e}")

        # Dispatch to handlers
        if async_mode:
            self._dispatch_async(event, handlers)
        else:
            self._dispatch_sync(event, handlers)

    def _dispatch_sync(self, event: Event, handlers: List[Callable]) -> None:
        """
        Dispatch event synchronously.

        Args:
            event: Event to dispatch
            handlers: List of handlers
        """
        for handler in handlers:
            try:
                handler(event)
                self._stats['events_handled'] += 1
            except Exception as e:
                self._stats['handler_errors'] += 1
                self._log_error(f"Handler error: {e}\n{traceback.format_exc()}")

    def _dispatch_async(self, event: Event, handlers: List[Callable]) -> None:
        """
        Dispatch event asynchronously.

        Args:
            event: Event to dispatch
            handlers: List of handlers
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for handler in handlers:
                future = executor.submit(self._safe_handle, handler, event)
                futures.append(future)

            # Wait for all handlers to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                    self._stats['events_handled'] += 1
                except Exception as e:
                    self._stats['handler_errors'] += 1
                    self._log_error(f"Handler error: {e}")

    def _safe_handle(self, handler: Callable, event: Event) -> None:
        """
        Safely execute a handler.

        Args:
            handler: Handler function
            event: Event to handle
        """
        try:
            handler(event)
        except Exception as e:
            raise RuntimeError(f"Handler {handler.__name__} failed: {e}")

    def _add_to_history(self, event: Event) -> None:
        """
        Add event to history.

        Args:
            event: Event to add
        """
        self._history.append(event)

        # Trim history if too long
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, event_type: Optional[Type[Event]] = None,
                   limit: int = 10) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Optional filter by event type
            limit: Max number of events to return

        Returns:
            List of events
        """
        history = self._history

        if event_type:
            history = [e for e in history if isinstance(e, event_type)]

        return history[-limit:]

    def get_stats(self) -> Dict[str, int]:
        """
        Get event bus statistics.

        Returns:
            Dict of statistics
        """
        return dict(self._stats)

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()

    def clear_stats(self) -> None:
        """Clear statistics."""
        self._stats.clear()

    def _log_error(self, message: str) -> None:
        """
        Log an error.

        Args:
            message: Error message
        """
        # In production, this would log to a file
        print(f"[EventBus Error] {message}")


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def subscribe(event_type: Type[Event], handler: Callable[[Event], None],
             filter_func: Optional[Callable[[Event], bool]] = None) -> None:
    """
    Subscribe to event in global bus.

    Args:
        event_type: Event type
        handler: Handler function
        filter_func: Optional filter
    """
    get_event_bus().subscribe(event_type, handler, filter_func)


def publish(event: Event, async_mode: bool = False) -> None:
    """
    Publish event to global bus.

    Args:
        event: Event to publish
        async_mode: Whether to handle asynchronously
    """
    get_event_bus().publish(event, async_mode)


# Decorator for event handlers
def event_handler(event_type: Type[Event],
                 filter_func: Optional[Callable[[Event], bool]] = None):
    """
    Decorator for marking event handlers.

    Usage:
    ```python
    @event_handler(FileLoadedEvent)
    def on_file_loaded(event: FileLoadedEvent):
        print(f"File loaded: {event.filename}")
    ```

    Args:
        event_type: Event type to handle
        filter_func: Optional filter function

    Returns:
        Decorator function
    """
    def decorator(func: Callable[[Event], None]) -> Callable[[Event], None]:
        # Register with global bus
        subscribe(event_type, func, filter_func)
        return func
    return decorator