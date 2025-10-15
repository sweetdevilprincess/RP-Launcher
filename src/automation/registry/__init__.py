"""
Component Registry

Centralized registry for managing automation components.
Provides dependency injection and service location.
"""

from src.automation.registry.registry import (
    ComponentRegistry,
    Component,
    ComponentScope,
    get_registry,
    register,
    resolve
)

__all__ = [
    'ComponentRegistry',
    'Component',
    'ComponentScope',
    'get_registry',
    'register',
    'resolve'
]