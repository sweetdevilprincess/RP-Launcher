#!/usr/bin/env python3
"""
Configuration Container

Typed configuration objects replacing dictionary-based config.
Provides validation, defaults, and type safety.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    enabled: bool = True
    priority: int = 5
    timeout_seconds: int = 10
    retry_count: int = 0
    fallback_enabled: bool = True


@dataclass
class ImmediateAgentsConfig:
    """Configuration for immediate agents."""
    enabled: bool = True
    quick_entity_analysis: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, timeout_seconds=5
    ))
    fact_extraction: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, timeout_seconds=5
    ))
    memory_extraction: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, timeout_seconds=5
    ))
    plot_thread_extraction: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, timeout_seconds=5
    ))


@dataclass
class BackgroundAgentsConfig:
    """Configuration for background agents."""
    enabled: bool = True
    response_analyzer: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, priority=1
    ))
    memory_creation: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, priority=2
    ))
    relationship_analysis: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, priority=3
    ))
    plot_thread_detection: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, priority=4
    ))
    knowledge_extraction: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True, priority=5
    ))
    contradiction_detection: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=False, priority=6
    ))


@dataclass
class AgentsConfig:
    """Configuration for all agents."""
    immediate: ImmediateAgentsConfig = field(default_factory=ImmediateAgentsConfig)
    background: BackgroundAgentsConfig = field(default_factory=BackgroundAgentsConfig)


@dataclass
class FallbackConfig:
    """Configuration for fallback triggers."""
    enabled: bool = True
    timeout_threshold: int = 10
    error_threshold: int = 3
    use_simple_context: bool = True


@dataclass
class AutomationConfig:
    """Main automation configuration."""
    # Feature flags
    auto_entity_cards: bool = True
    auto_story_arc: bool = True
    enable_profiling: bool = True
    enable_caching: bool = False
    continue_on_error: bool = True

    # Thresholds
    entity_mention_threshold: int = 2
    arc_frequency: int = 50

    # Agent configuration
    agents: AgentsConfig = field(default_factory=AgentsConfig)

    # Fallback configuration
    fallback: FallbackConfig = field(default_factory=FallbackConfig)

    # Other settings
    current_chapter: Optional[str] = None
    max_workers: int = 4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationConfig':
        """
        Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            AutomationConfig instance
        """
        # Handle nested agent config
        if 'agents' in data and isinstance(data['agents'], dict):
            agents_data = data['agents']

            # Parse immediate agents
            immediate = ImmediateAgentsConfig()
            if 'immediate' in agents_data:
                immediate_data = agents_data['immediate']
                if isinstance(immediate_data, dict):
                    # Update enabled flag
                    if 'enabled' in immediate_data:
                        immediate.enabled = immediate_data['enabled']

                    # Update individual agents
                    for agent_name in ['quick_entity_analysis', 'fact_extraction',
                                      'memory_extraction', 'plot_thread_extraction']:
                        if agent_name in immediate_data:
                            agent_cfg = immediate_data[agent_name]
                            if isinstance(agent_cfg, dict):
                                setattr(immediate, agent_name, AgentConfig(**agent_cfg))

            # Parse background agents
            background = BackgroundAgentsConfig()
            if 'background' in agents_data:
                background_data = agents_data['background']
                if isinstance(background_data, dict):
                    # Update enabled flag
                    if 'enabled' in background_data:
                        background.enabled = background_data['enabled']

                    # Update individual agents
                    for agent_name in ['response_analyzer', 'memory_creation',
                                      'relationship_analysis', 'plot_thread_detection',
                                      'knowledge_extraction', 'contradiction_detection']:
                        if agent_name in background_data:
                            agent_cfg = background_data[agent_name]
                            if isinstance(agent_cfg, dict):
                                setattr(background, agent_name, AgentConfig(**agent_cfg))

            data['agents'] = AgentsConfig(immediate=immediate, background=background)

        # Handle fallback config
        if 'fallback' in data and isinstance(data['fallback'], dict):
            data['fallback'] = FallbackConfig(**data['fallback'])

        # Create config, filtering out unknown keys
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}

        return cls(**filtered_data)


@dataclass
class ConfigContainer:
    """
    Container for all configuration.

    Provides typed access to configuration with validation.
    """
    automation: AutomationConfig

    @classmethod
    def load(cls, config_file: Path) -> 'ConfigContainer':
        """
        Load configuration from file.

        Args:
            config_file: Path to config.json

        Returns:
            ConfigContainer with loaded config
        """
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    automation = AutomationConfig.from_dict(data)
                    return cls(automation=automation)
            except Exception:
                # Return defaults on error
                pass

        # Return defaults
        return cls(automation=AutomationConfig())

    def save(self, config_file: Path) -> None:
        """
        Save configuration to file.

        Args:
            config_file: Path to config.json
        """
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.automation.to_dict(), f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return self.automation.to_dict()


def load_config_container(config_file: Path) -> ConfigContainer:
    """
    Load configuration container from file.

    Args:
        config_file: Path to config.json

    Returns:
        ConfigContainer instance
    """
    return ConfigContainer.load(config_file)


def migrate_legacy_config(legacy_dict: Dict[str, Any]) -> AutomationConfig:
    """
    Migrate legacy dictionary config to typed config.

    Args:
        legacy_dict: Legacy configuration dictionary

    Returns:
        Typed AutomationConfig
    """
    return AutomationConfig.from_dict(legacy_dict)
