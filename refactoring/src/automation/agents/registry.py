"""Agent registry for loading and configuring agent strategies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...shared.interfaces import ConfigService, LoggingService
from ..services.agent_runner import AgentStrategy
from .background_agent_strategy import BackgroundAgentStrategy
from .fallback_trigger_strategy import FallbackTriggerStrategy
from .immediate_agent_strategy import ImmediateAgentStrategy


class AgentRegistry:
    """Registry for creating and ordering agent execution strategies.

    The registry reads configuration to determine:
    - Which agent strategies are enabled
    - What priority order to execute them
    - Strategy-specific configuration (timeouts, enabled agents, etc.)

    Strategies are executed in order:
    1. ImmediateAgentStrategy (if enabled) - gathers context before Claude call
    2. FallbackTriggerStrategy (if agents disabled) - legacy trigger system
    3. BackgroundAgentStrategy (if enabled) - post-response analysis
    """

    def __init__(
        self,
        *,
        config: ConfigService,
        logger: LoggingService,
        bridge: Any = None
    ) -> None:
        """Initialize agent registry.

        Args:
            config: Configuration service for reading agent settings
            logger: Logging service for diagnostics
            bridge: Optional bridge service for agent LLM access
        """
        self._config = config
        self._logger = logger
        self._bridge = bridge

    def create_strategies(self, *, rp_dir: Any) -> list[AgentStrategy]:
        """Create and order agent strategies based on configuration.

        Args:
            rp_dir: RP directory path (needed by agents)

        Returns:
            Ordered list of agent strategies to execute
        """
        self._logger.debug("agent_registry.create_strategies.start")

        strategies: list[AgentStrategy] = []

        # Load agent configuration
        agents_config = self._config.get("agents", {})
        fallback_config = self._config.get("fallback", {})

        # Determine if we should use agent system or fallback to triggers
        use_agents = self._should_use_agents(agents_config, fallback_config)

        if use_agents:
            # Create immediate agent strategy if configured
            immediate_strategy = self._create_immediate_strategy(agents_config, rp_dir)
            if immediate_strategy:
                strategies.append(immediate_strategy)
                self._logger.debug("agent_registry.registered.immediate")

            # Create background agent strategy if configured
            background_strategy = self._create_background_strategy(agents_config, rp_dir)
            if background_strategy:
                strategies.append(background_strategy)
                self._logger.debug("agent_registry.registered.background")
        else:
            # Fall back to legacy trigger system
            trigger_strategy = self._create_trigger_strategy(fallback_config)
            if trigger_strategy:
                strategies.append(trigger_strategy)
                self._logger.debug("agent_registry.registered.trigger_fallback")

        self._logger.info(
            "agent_registry.create_strategies.complete",
            context={"strategy_count": len(strategies)},
        )

        return strategies

    def _should_use_agents(
        self, agents_config: dict[str, Any], fallback_config: dict[str, Any]
    ) -> bool:
        """Determine whether to use agent system or fallback to triggers.

        Args:
            agents_config: Agent configuration section
            fallback_config: Fallback configuration section

        Returns:
            True to use agents, False to use trigger fallback
        """
        # Check if trigger system is set as primary
        if fallback_config.get("trigger_system_primary", False):
            return False

        # Check if at least one immediate or background agent is enabled
        immediate_config = agents_config.get("immediate", {})
        background_config = agents_config.get("background", {})

        has_immediate_agents = any(
            agent_conf.get("enabled", False)
            for agent_conf in immediate_config.values()
            if isinstance(agent_conf, dict)
        )

        has_background_agents = any(
            agent_conf.get("enabled", False)
            for agent_conf in background_config.values()
            if isinstance(agent_conf, dict)
        )

        return has_immediate_agents or has_background_agents

    def _create_immediate_strategy(
        self, agents_config: dict[str, Any], rp_dir: Any
    ) -> ImmediateAgentStrategy | None:
        """Create immediate agent strategy if configured.

        Args:
            agents_config: Agent configuration section
            rp_dir: RP directory path

        Returns:
            ImmediateAgentStrategy instance or None
        """
        immediate_config = agents_config.get("immediate", {})
        if not immediate_config:
            return None

        # Check if any immediate agents are enabled
        enabled_agents = {
            agent_id: agent_conf
            for agent_id, agent_conf in immediate_config.items()
            if isinstance(agent_conf, dict) and agent_conf.get("enabled", False)
        }

        if not enabled_agents:
            return None

        return ImmediateAgentStrategy(
            logger=self._logger,
            enabled_agents=enabled_agents,
            max_workers=4,  # TODO: Make configurable
            rp_dir=rp_dir,
            bridge=self._bridge,
        )

    def _create_background_strategy(
        self, agents_config: dict[str, Any], rp_dir: Any
    ) -> BackgroundAgentStrategy | None:
        """Create background agent strategy if configured.

        Args:
            agents_config: Agent configuration section
            rp_dir: RP directory path

        Returns:
            BackgroundAgentStrategy instance or None
        """
        background_config = agents_config.get("background", {})
        if not background_config:
            return None

        # Extract enabled status for each background agent
        enabled_agents = {
            agent_id: agent_conf.get("enabled", False)
            for agent_id, agent_conf in background_config.items()
            if isinstance(agent_conf, dict)
        }

        # Check if any background agents are enabled
        if not any(enabled_agents.values()):
            return None

        return BackgroundAgentStrategy(
            logger=self._logger,
            enabled_agents=enabled_agents,
            max_workers=4,  # TODO: Make configurable
            rp_dir=rp_dir,
            bridge=self._bridge,
        )

    def _create_trigger_strategy(
        self, fallback_config: dict[str, Any]
    ) -> FallbackTriggerStrategy | None:
        """Create trigger fallback strategy if configured.

        Args:
            fallback_config: Fallback configuration section

        Returns:
            FallbackTriggerStrategy instance or None
        """
        use_trigger_system = fallback_config.get("use_trigger_system", True)

        if not use_trigger_system:
            return None

        return FallbackTriggerStrategy(
            logger=self._logger,
            config_service=self._config,
            use_trigger_system=use_trigger_system,
        )
