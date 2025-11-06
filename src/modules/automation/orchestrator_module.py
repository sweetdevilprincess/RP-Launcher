"""
Orchestrator Module

Wraps AutomationOrchestratorV2 (Simplified) for module-managed lifecycle and configuration.
Uses hybrid approach combining V1's simplicity with V2's decorator profiling.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import logging

from src.core.base import RPModule
from src.automation.orchestrator_v2_simplified import AutomationOrchestratorV2
from src.automation.profiling import PerformanceProfiler


class OrchestratorModule(RPModule):
    """Module wrapper for AutomationOrchestratorV2

    Provides high-level coordination of all automation tasks including:
    - Response counter management
    - Time tracking
    - Tiered file loading (TIER_1, TIER_2, TIER_3)
    - Trigger management
    - Background agent orchestration
    - Status updates
    - Performance profiling

    Configuration:
        enable_profiling: Enable performance profiling (default: true)
        cache_mode: Use prompt caching mode (default: true)
    """

    name = "orchestrator"
    version = "2.0.0"
    dependencies = ["file_manager", "agent_coordinator"]
    optional = False

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize orchestrator module

        Args:
            rp_dir: RP directory path
            config: Module configuration
            manager: Reference to module manager
        """
        super().__init__(rp_dir, config, manager)
        self.orchestrator: Optional[AutomationOrchestratorV2] = None

    def initialize(self) -> bool:
        """Initialize orchestrator

        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing OrchestratorV2 module...")

            # Get configuration
            module_config = self.config.get('config', {})
            enable_profiling = module_config.get('enable_profiling', True)

            # Initialize V2 orchestrator
            self.orchestrator = AutomationOrchestratorV2(
                rp_dir=self.rp_dir,
                enable_profiling=enable_profiling
            )

            self.logger.info(f"OrchestratorV2 initialized (profiling={'enabled' if enable_profiling else 'disabled'})")
            self._initialized = True
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize OrchestratorV2: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def start(self) -> bool:
        """Start orchestrator

        Returns:
            True if start successful
        """
        if not self._initialized or not self.orchestrator:
            self.logger.error("Cannot start: not initialized")
            return False

        try:
            self.logger.info("Starting OrchestratorV2 module...")
            self._running = True
            self.logger.info("OrchestratorV2 module started")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start OrchestratorV2: {e}")
            return False

    def stop(self) -> bool:
        """Stop orchestrator

        Returns:
            True if stop successful
        """
        if not self._running:
            return True

        try:
            self.logger.info("Stopping OrchestratorV2 module...")
            self._running = False
            self.logger.info("OrchestratorV2 module stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop OrchestratorV2: {e}")
            return False

    def cleanup(self) -> None:
        """Cleanup orchestrator resources"""
        try:
            self.logger.info("Cleaning up OrchestratorV2 module...")

            if self.orchestrator:
                # Orchestrator cleanup (file tracker, entity manager, etc.)
                self.orchestrator = None

            self._initialized = False
            self._running = False
            self.logger.info("OrchestratorV2 cleanup complete")

        except Exception as e:
            self.logger.error(f"Error during OrchestratorV2 cleanup: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get module status

        Returns:
            Dict with status information
        """
        status = super().get_status()

        if self.orchestrator:
            status.update({
                'profiling_enabled': self.orchestrator.profiling_enabled,
                'state_dir': str(self.orchestrator.state_dir),
                'has_entity_manager': self.orchestrator.entity_manager is not None,
                'has_template_manager': self.orchestrator.template_manager is not None
            })

        return status

    # Public API methods

    def run_automation(self, message: str) -> Tuple[str, List[str]]:
        """Run automation in simple mode (no caching)

        Args:
            message: User message

        Returns:
            Tuple of (enhanced_prompt, loaded_entity_names)
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")

        return self.orchestrator.run_automation(message)

    def run_automation_with_caching(
        self,
        message: str,
        enable_profiling: Optional[bool] = None
    ) -> Tuple[str, str, List[str], Optional[PerformanceProfiler]]:
        """Run automation with prompt caching support

        Args:
            message: User message
            enable_profiling: Override profiling setting

        Returns:
            Tuple of (cached_context, dynamic_prompt, loaded_entities, profiler)
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")

        # Use module config if not overridden
        if enable_profiling is None:
            enable_profiling = self.orchestrator.profiling_enabled

        return self.orchestrator.run_automation_with_caching(
            message,
            enable_profiling=enable_profiling
        )

    def run_background_agents(self, response_text: str) -> None:
        """Run background agents after response is generated

        Note: V2 uses simplified interface - gets response_number internally

        Args:
            response_text: Generated response text
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")

        self.orchestrator.run_background_agents_after_response(response_text)

    def get_profiler(self) -> Optional[PerformanceProfiler]:
        """Get performance profiler instance

        Returns:
            PerformanceProfiler or None if profiling disabled
        """
        if self.orchestrator:
            return self.orchestrator.profiler
        return None

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle module-specific commands

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "profile":
            profiler = self.get_profiler()
            if profiler:
                return f"Profiler: {profiler.get_summary()}"
            else:
                return "Profiling is disabled"

        elif command == "status":
            return f"Orchestrator Status: {self.get_status()}"

        return None
