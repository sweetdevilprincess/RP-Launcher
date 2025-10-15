"""
Configuration Module

Provides structured configuration management with validation and defaults.
"""

from src.automation.config.config_container import (
    ConfigContainer,
    AgentConfig,
    AutomationConfig,
    load_config_container
)

__all__ = [
    'ConfigContainer',
    'AgentConfig',
    'AutomationConfig',
    'load_config_container'
]
