"""Factory for creating automation pipeline services with proper dependency injection.

This module provides a centralized way to instantiate the AutomationService with all
its dependencies properly wired up. It uses sensible defaults but allows overrides
for testing and customization.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain.entities import EntityService, FixtureEntityRepository
from ..domain.sessions import SessionRepository, SessionService
from ..infrastructure.config.config_loader import ConfigLoader
from ..infrastructure.filesystem import (
    FileAccessService,
    FileManager,
    JsonStore,
    MarkdownStore,
    StatePaths,
    TieredFileLoader,
)
from ..infrastructure.filesystem.write_queue import build_default_write_queue
from ..infrastructure.sessions import SessionStateService
from ..infrastructure.templates import StateTemplateService
from ..shared.interfaces import ConfigService, LoggingService
from ..shared.logging import get_logger
from .agents import AgentRegistry
from .services import AgentRunner, AutomationService, PromptBuilder


class DictConfigService:
    """Simple dict-based ConfigService implementation for the factory."""

    def __init__(self, config_data: dict[str, Any]) -> None:
        """Initialize with configuration dictionary.

        Args:
            config_data: Configuration data dictionary
        """
        self._config = config_data

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value."""
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1")
        return bool(value)

    def get_dict(self, key: str, default: dict | None = None) -> dict:
        """Get dict configuration value."""
        value = self.get(key, default or {})
        return value if isinstance(value, dict) else (default or {})

    def require(self, key: str) -> Any:
        """Get required configuration value, raise if missing."""
        value = self.get(key)
        if value is None:
            raise KeyError(f"Required configuration key missing: {key}")
        return value

    def section(self, prefix: str) -> dict[str, Any]:
        """Get configuration section."""
        keys = prefix.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                return {}
        return value if isinstance(value, dict) else {}

    def keys(self) -> list[str]:
        """Get all configuration keys."""
        return list(self._config.keys())

    def reload(self) -> None:
        """Reload configuration (no-op for dict-based config)."""


def create_automation_service(
    rp_dir: Path,
    *,
    config_service: ConfigService | None = None,
    logger: LoggingService | None = None,
    bridge: Any = None,
    **overrides: Any,
) -> AutomationService:
    """Create a fully-wired AutomationService with default dependencies.

    This factory function instantiates all required services and wires them together
    with proper dependency injection. It uses sensible defaults but allows overriding
    any dependency for testing or customization.

    Args:
        rp_dir: RP directory path
        config_service: Optional config service (will load from file if not provided)
        logger: Optional logger (will create default if not provided)
        bridge: Optional bridge service for LLM access (required for agent LLM calls)
        **overrides: Optional dependency overrides:
            - file_manager: Custom FileManager
            - file_access: Custom FileAccessService
            - entity_service: Custom EntityService
            - session_service: Custom SessionService
            - prompt_builder: Custom PromptBuilder
            - agent_runner: Custom AgentRunner

    Returns:
        Fully configured AutomationService instance

    Example:
        >>> service = create_automation_service(Path("/path/to/rp"))
        >>> result = service.run(context)

        >>> # With bridge for agent LLM access
        >>> service = create_automation_service(Path("/path/to/rp"), bridge=bridge)

        >>> # With overrides for testing
        >>> mock_entities = Mock(spec=EntityService)
        >>> service = create_automation_service(
        ...     Path("/path/to/rp"),
        ...     entity_service=mock_entities
        ... )
    """
    # Create logger if not provided
    if logger is None:
        logger = get_logger(__name__)

    # Create config service if not provided
    if config_service is None:
        config_loader = ConfigLoader(rp_dir)
        config_data = config_loader.load()
        config_service = DictConfigService(config_data)

    # Create StatePaths (used by multiple services)
    paths = StatePaths(rp_dir=rp_dir)

    # Create SessionStateService (used by multiple services for timeline consistency)
    session_state_service = SessionStateService(logger=logger)

    # Create file access service (unless overridden)
    if "file_access" not in overrides:
        if "file_manager" in overrides:
            file_manager = overrides["file_manager"]
        else:
            # Create file manager with dependencies
            json_store = JsonStore(root=paths.state_dir, logger=logger)
            markdown_store = MarkdownStore(root=paths.rp_dir, logger=logger)
            write_queue = build_default_write_queue(logger=logger, debounce_ms=500)

            file_manager = FileManager(
                paths=paths,
                json_store=json_store,
                markdown_store=markdown_store,
                write_queue=write_queue,
                logger=logger,
                session_state_service=session_state_service,
            )

        # Create tiered loader
        tier_loader = TieredFileLoader(
            paths=paths,
            markdown_store=markdown_store,
            logger=logger,
            config=config_service.section("tiered_loading") or {},
        )

        # Create file access service
        file_access = FileAccessService(
            file_manager=file_manager,
            tier_loader=tier_loader,
            logger=logger,
            rp_dir=rp_dir,
        )
    else:
        file_access = overrides["file_access"]

    # Create entity service (unless overridden)
    if "entity_service" in overrides:
        entity_service = overrides["entity_service"]
    else:
        entity_repository = FixtureEntityRepository(
            rp_dir=rp_dir,
            session_state_service=session_state_service,
        )
        template_service = StateTemplateService()
        entity_service = EntityService(
            repository=entity_repository,
            templates=template_service,
            logger=logger,
            session_state=session_state_service,  # For scene context access
            rp_dir=rp_dir,  # For entity file path resolution
        )

    # Create session service (unless overridden)
    if "session_service" in overrides:
        session_service = overrides["session_service"]
    else:
        # Create session repository
        session_repository = SessionRepository(
            paths=paths,
            logger=logger,
            session_state_service=session_state_service,
        )
        # Create session service with repository
        session_service = SessionService(
            repository=session_repository,
            logger=logger,
            session_state_service=session_state_service,
        )

    # Create prompt builder (unless overridden)
    if "prompt_builder" in overrides:
        prompt_builder = overrides["prompt_builder"]
    else:
        prompt_builder = PromptBuilder(config=config_service, logger=logger)

    # Create agent runner (unless overridden)
    if "agent_runner" in overrides:
        agent_runner = overrides["agent_runner"]
    else:
        agent_registry = AgentRegistry(
            config=config_service,
            logger=logger,
            bridge=bridge  # Pass bridge for agent LLM access
        )
        strategies = agent_registry.create_strategies(rp_dir=rp_dir)
        agent_runner = AgentRunner(strategies=strategies, logger=logger)

    # Create and return automation service
    return AutomationService(
        config=config_service,
        logger=logger,
        entity_service=entity_service,
        session_service=session_service,
        prompt_builder=prompt_builder,
        agent_runner=agent_runner,
        file_access=file_access,
    )
