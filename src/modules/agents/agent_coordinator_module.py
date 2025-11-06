"""
Agent Coordinator Module

Wraps AgentCoordinator for module-managed lifecycle and configuration.
Utilizes shared utilities for logging, timing, and result handling.
"""

from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
import logging

from src.core.base import RPModule
from src.automation.agent_coordinator import AgentCoordinator, AgentResult
from src.utils.agent_logger import AgentLogger


class AgentCoordinatorModule(RPModule):
    """Module wrapper for AgentCoordinator

    Provides multi-agent orchestration with concurrent execution,
    result collection, and cache management.

    Configuration:
        max_workers: Maximum concurrent agents (default: 4)
        default_timeout: Default timeout for agent execution in seconds (default: 60)
        allow_partial: Allow partial results if some agents fail (default: true)
        cache_file: Filename for agent cache (default: "agent_analysis.json")
    """

    name = "agent_coordinator"
    version = "1.0.0"
    dependencies = ["file_manager", "fs_write_queue"]
    optional = False

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize agent coordinator module

        Args:
            rp_dir: RP directory path
            config: Module configuration
            manager: Reference to module manager
        """
        super().__init__(rp_dir, config, manager)
        self.coordinator: Optional[AgentCoordinator] = None
        self._cache_file: Optional[Path] = None
        self._agent_logger: Optional[AgentLogger] = None

    def initialize(self) -> bool:
        """Initialize agent coordinator

        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing AgentCoordinator module...")

            # Get configuration
            module_config = self.config.get('config', {})
            max_workers = module_config.get('max_workers', 4)
            cache_filename = module_config.get('cache_file', 'agent_analysis.json')

            # Get file manager for log file
            file_manager = self.manager.get('file_manager')
            if not file_manager:
                self.logger.error("FileManager module not available")
                return False

            # Setup log file path
            log_file = self.rp_dir / "logs" / "automation.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Setup cache file path
            self._cache_file = self.rp_dir / cache_filename

            # Initialize agent logger
            self._agent_logger = AgentLogger(
                agent_id="coordinator",
                log_file=log_file,
                console_logger=self.logger
            )

            # Initialize coordinator
            self.coordinator = AgentCoordinator(
                rp_dir=self.rp_dir,
                log_file=log_file,
                max_workers=max_workers
            )

            self.logger.info(f"AgentCoordinator initialized (max_workers={max_workers})")
            self._initialized = True
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize AgentCoordinator: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def start(self) -> bool:
        """Start agent coordinator

        Returns:
            True if start successful
        """
        if not self._initialized or not self.coordinator:
            self.logger.error("Cannot start: not initialized")
            return False

        try:
            self.logger.info("Starting AgentCoordinator module...")

            # Clear any previous agent registrations
            self.coordinator.clear_agents()

            self._running = True
            self.logger.info("AgentCoordinator module started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start AgentCoordinator: {e}")
            return False

    def stop(self) -> bool:
        """Stop agent coordinator

        Returns:
            True if stop successful
        """
        if not self._running:
            return True

        try:
            self.logger.info("Stopping AgentCoordinator module...")

            # Clear agents (doesn't interrupt running agents, just clears queue)
            if self.coordinator:
                self.coordinator.clear_agents()

            self._running = False
            self.logger.info("AgentCoordinator module stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop AgentCoordinator: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup agent coordinator resources"""
        try:
            self.logger.info("Cleaning up AgentCoordinator module...")

            if self.coordinator:
                # Clear any registered agents
                self.coordinator.clear_agents()

                # Note: ThreadPoolExecutor cleanup happens automatically when
                # agents finish executing (via context manager in run_all_agents)
                self.coordinator = None

            self._agent_logger = None
            self._initialized = False
            self._running = False
            self.logger.info("AgentCoordinator cleanup complete")

        except Exception as e:
            self.logger.error(f"Error during AgentCoordinator cleanup: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get module status

        Returns:
            Dict with status information
        """
        status = super().get_status()

        if self.coordinator:
            stats = self.coordinator.get_stats()
            status.update({
                'agents_registered': stats.get('agents_registered', 0),
                'last_run': {
                    'agents_executed': stats.get('agents_executed', 0),
                    'successful': stats.get('successful', 0),
                    'failed': stats.get('failed', 0),
                    'avg_duration_ms': stats.get('avg_duration_ms', 0)
                }
            })

        return status

    # Public API methods

    def add_agent(self, agent_id: str, func: Callable, *args,
                  description: str = "", **kwargs) -> None:
        """Register an agent task

        Args:
            agent_id: Unique identifier for this agent
            func: Function to execute (should return string content)
            *args: Positional arguments for function
            description: Human-readable description
            **kwargs: Keyword arguments for function
        """
        if not self.coordinator:
            raise RuntimeError("AgentCoordinator not initialized")

        self.coordinator.add_agent(agent_id, func, *args, description=description, **kwargs)

    def clear_agents(self) -> None:
        """Clear all registered agents"""
        if self.coordinator:
            self.coordinator.clear_agents()

    def run_all_agents(self, timeout: Optional[float] = None,
                      allow_partial: Optional[bool] = None) -> str:
        """Execute all registered agents concurrently

        Args:
            timeout: Maximum time to wait (defaults to config or 60s)
            allow_partial: Allow partial results (defaults to config or True)

        Returns:
            Formatted context string ready for Claude injection
        """
        if not self.coordinator:
            raise RuntimeError("AgentCoordinator not initialized")

        # Use config defaults if not specified
        module_config = self.config.get('config', {})
        if timeout is None:
            timeout = module_config.get('default_timeout', 60.0)
        if allow_partial is None:
            allow_partial = module_config.get('allow_partial', True)

        return self.coordinator.run_all_agents(timeout=timeout, allow_partial=allow_partial)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about last agent run

        Returns:
            Dict with execution statistics
        """
        if not self.coordinator:
            return {}

        return self.coordinator.get_stats()

    def get_result(self, agent_id: str) -> Optional[AgentResult]:
        """Get result for a specific agent

        Args:
            agent_id: Agent identifier

        Returns:
            AgentResult or None if not found
        """
        if not self.coordinator:
            return None

        return self.coordinator.get_result(agent_id)

    def save_to_cache(self, response_number: int) -> Dict[str, Any]:
        """Save agent results to JSON cache file

        Args:
            response_number: Current response number

        Returns:
            Dict with timing stats including write_ms
        """
        if not self.coordinator or not self._cache_file:
            return {'write_ms': 0, 'agents_ok': 0, 'agents_total': 0}

        return self.coordinator.save_to_cache(self._cache_file, response_number)

    def load_from_cache(self) -> Optional[str]:
        """Load JSON cache and convert to condensed prompt format

        Returns:
            Condensed agent context for prompt injection or None if not found
        """
        if not self.coordinator or not self._cache_file:
            return None

        return self.coordinator.load_from_cache(self._cache_file)

    def clear_cache(self) -> None:
        """Clear agent cache file"""
        if self.coordinator and self._cache_file:
            self.coordinator.clear_cache(self._cache_file)

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle module-specific commands

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "stats":
            stats = self.get_stats()
            return f"Agent Stats: {stats}"

        elif command == "clear":
            self.clear_agents()
            return "Cleared all registered agents"

        elif command == "clear_cache":
            self.clear_cache()
            return "Cleared agent cache file"

        return None
