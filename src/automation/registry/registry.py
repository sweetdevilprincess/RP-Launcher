#!/usr/bin/env python3
"""
Component Registry Implementation

Centralized registry for dependency injection and service location.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Generic
import inspect


class ComponentScope(Enum):
    """Component lifecycle scope."""
    SINGLETON = "singleton"      # Single instance for entire application
    TRANSIENT = "transient"      # New instance each time
    SCOPED = "scoped"           # Single instance per request/context


@dataclass
class Component:
    """Registered component metadata."""
    name: str
    factory: Callable[[], Any]
    scope: ComponentScope
    interface: Optional[Type] = None
    dependencies: Dict[str, str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}


T = TypeVar('T')


class ComponentRegistry:
    """
    Centralized component registry.

    Manages component registration, resolution, and lifecycle.
    """

    def __init__(self):
        """Initialize registry."""
        self._components: Dict[str, Component] = {}
        self._singletons: Dict[str, Any] = {}
        self._scoped: Dict[str, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register(self, name: str,
                factory: Callable[[], Any],
                scope: ComponentScope = ComponentScope.SINGLETON,
                interface: Optional[Type] = None,
                dependencies: Optional[Dict[str, str]] = None) -> None:
        """
        Register a component.

        Args:
            name: Component name
            factory: Factory function to create component
            scope: Component lifecycle scope
            interface: Optional interface/base class
            dependencies: Optional dependency mapping
        """
        component = Component(
            name=name,
            factory=factory,
            scope=scope,
            interface=interface,
            dependencies=dependencies or {}
        )

        self._components[name] = component

        # Register by interface if provided
        if interface:
            self._factories[interface] = factory

    def register_singleton(self, name: str, instance: Any,
                          interface: Optional[Type] = None) -> None:
        """
        Register an existing instance as singleton.

        Args:
            name: Component name
            instance: Existing instance
            interface: Optional interface
        """
        self._components[name] = Component(
            name=name,
            factory=lambda: instance,
            scope=ComponentScope.SINGLETON,
            interface=interface
        )
        self._singletons[name] = instance

        if interface:
            self._factories[interface] = lambda: instance

    def register_factory(self, interface: Type,
                        factory: Callable[[ComponentRegistry], Any]) -> None:
        """
        Register a factory for an interface.

        Args:
            interface: Interface type
            factory: Factory function
        """
        self._factories[interface] = lambda: factory(self)

    def resolve(self, name_or_type: Any) -> Any:
        """
        Resolve a component by name or type.

        Args:
            name_or_type: Component name or type

        Returns:
            Resolved component instance

        Raises:
            KeyError: If component not found
        """
        # Resolve by type
        if isinstance(name_or_type, type):
            if name_or_type in self._factories:
                return self._factories[name_or_type]()

            # Try to find by interface
            for component in self._components.values():
                if component.interface == name_or_type:
                    return self._resolve_component(component)

            raise KeyError(f"No component registered for type {name_or_type}")

        # Resolve by name
        if name_or_type not in self._components:
            raise KeyError(f"Component '{name_or_type}' not registered")

        component = self._components[name_or_type]
        return self._resolve_component(component)

    def _resolve_component(self, component: Component) -> Any:
        """
        Resolve a component with its dependencies.

        Args:
            component: Component to resolve

        Returns:
            Component instance
        """
        # Handle singleton scope
        if component.scope == ComponentScope.SINGLETON:
            if component.name not in self._singletons:
                self._singletons[component.name] = self._create_instance(component)
            return self._singletons[component.name]

        # Handle scoped
        elif component.scope == ComponentScope.SCOPED:
            if component.name not in self._scoped:
                self._scoped[component.name] = self._create_instance(component)
            return self._scoped[component.name]

        # Handle transient
        else:
            return self._create_instance(component)

    def _create_instance(self, component: Component) -> Any:
        """
        Create component instance with dependency injection.

        Args:
            component: Component to create

        Returns:
            Component instance
        """
        # Get factory signature
        sig = inspect.signature(component.factory)

        # No parameters - simple factory
        if not sig.parameters:
            return component.factory()

        # Resolve dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            # Skip self/cls
            if param_name in ('self', 'cls'):
                continue

            # Check explicit dependency mapping
            if param_name in component.dependencies:
                dep_name = component.dependencies[param_name]
                kwargs[param_name] = self.resolve(dep_name)

            # Try to resolve by type annotation
            elif param.annotation != param.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                except KeyError:
                    # Use default if available
                    if param.default != param.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise

        return component.factory(**kwargs)

    def clear_scoped(self) -> None:
        """Clear scoped instances (for new request/context)."""
        self._scoped.clear()

    def has(self, name: str) -> bool:
        """
        Check if component is registered.

        Args:
            name: Component name

        Returns:
            True if registered
        """
        return name in self._components

    def get_all(self, interface: Type[T]) -> list[T]:
        """
        Get all components implementing an interface.

        Args:
            interface: Interface type

        Returns:
            List of components
        """
        results = []
        for component in self._components.values():
            if component.interface == interface or (
                component.interface and issubclass(component.interface, interface)
            ):
                results.append(self._resolve_component(component))
        return results


# Global registry instance
_global_registry: Optional[ComponentRegistry] = None


def get_registry() -> ComponentRegistry:
    """Get global registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ComponentRegistry()
        _register_default_components(_global_registry)
    return _global_registry


def register(name: str, factory: Callable,
            scope: ComponentScope = ComponentScope.SINGLETON,
            **kwargs) -> None:
    """
    Register component in global registry.

    Args:
        name: Component name
        factory: Factory function
        scope: Component scope
        **kwargs: Additional registration options
    """
    get_registry().register(name, factory, scope, **kwargs)


def resolve(name_or_type: Any) -> Any:
    """
    Resolve component from global registry.

    Args:
        name_or_type: Component name or type

    Returns:
        Resolved component
    """
    return get_registry().resolve(name_or_type)


def _register_default_components(registry: ComponentRegistry) -> None:
    """
    Register default automation components.

    Args:
        registry: Registry to populate
    """
    from pathlib import Path
    from src.automation.helpers import PromptBuilder
    from src.automation.agents import AgentFactory
    from src.automation.status import StatusManager
    from src.automation.pipeline import PipelineBuilder

    # Get default paths
    def get_rp_dir():
        # This would be set by the application
        return Path.cwd()

    def get_log_file():
        return get_rp_dir() / "logs" / "automation.log"

    # Register core components
    registry.register(
        "prompt_builder",
        lambda: PromptBuilder(get_rp_dir(), get_log_file()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "agent_factory",
        lambda: AgentFactory(get_rp_dir(), get_log_file()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "status_manager",
        lambda: StatusManager(get_rp_dir()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "pipeline_builder",
        lambda: PipelineBuilder(log_file=get_log_file()),
        ComponentScope.TRANSIENT
    )


class ServiceLocator:
    """
    Service locator pattern implementation.

    Alternative to dependency injection for simpler cases.
    """

    _services: Dict[Type, Any] = {}

    @classmethod
    def register(cls, service_type: Type[T], instance: T) -> None:
        """Register a service."""
        cls._services[service_type] = instance

    @classmethod
    def get(cls, service_type: Type[T]) -> T:
        """Get a service."""
        if service_type not in cls._services:
            raise KeyError(f"Service {service_type} not registered")
        return cls._services[service_type]

    @classmethod
    def clear(cls) -> None:
        """Clear all services."""
        cls._services.clear()