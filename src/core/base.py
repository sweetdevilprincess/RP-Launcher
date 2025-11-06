"""
Base Module Class for RP System

Defines the interface that all RP system modules must implement.
Provides lifecycle management, dependency tracking, and common utilities.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime


class RPModule(ABC):
    """Abstract base class for all RP system modules.

    All modules must inherit from this class and implement the required methods.
    The module manager uses this interface to manage module lifecycle.

    Lifecycle:
        1. __init__() - Create module instance
        2. initialize() - Load config, setup state
        3. start() - Begin operations
        4. [Module runs]
        5. stop() - Pause operations
        6. cleanup() - Free resources
    """

    # Module metadata (override in subclass)
    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base module"
    dependencies: List[str] = []  # Names of modules this depends on
    optional: bool = False  # If True, system can run without this module

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize module with configuration and manager reference.

        Args:
            rp_dir: Path to RP directory
            config: Module-specific configuration dict
            manager: Reference to ModuleManager instance
        """
        self.rp_dir = Path(rp_dir)
        self.config = config
        self.manager = manager

        # Module state
        self._initialized = False
        self._running = False
        self._error = None
        self._init_time = None
        self._start_time = None

        # Setup logger
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup module logger.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(f"rp.modules.{self.name}")

        # Only add handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[%(asctime)s] [MODULE:{self.name}] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    # ==================== Lifecycle Methods (Abstract) ====================

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize module (load config, setup state).

        Called once during module manager initialization.
        Should load configuration, setup internal state, validate dependencies.
        Should NOT start background tasks or operations yet.

        Returns:
            True if initialization successful, False otherwise

        Raises:
            Exception: Any exception will be caught by module manager
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """Start module operations.

        Called after all modules are initialized.
        Can start background tasks, open connections, begin operations.

        Returns:
            True if start successful, False otherwise

        Raises:
            Exception: Any exception will be caught by module manager
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop module operations.

        Should pause operations but keep state intact.
        Should be reversible (can call start() again after stop()).

        Returns:
            True if stop successful, False otherwise

        Raises:
            Exception: Any exception will be caught by module manager
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup module resources.

        Called during shutdown. Should free all resources, close connections,
        save state if needed. After cleanup, module cannot be restarted.

        Should not raise exceptions (log errors instead).
        """
        pass

    # ==================== Status & Info Methods ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status information.

        Returns:
            Dict with status information including:
                - name: Module name
                - version: Module version
                - initialized: Whether initialized
                - running: Whether running
                - error: Last error message (if any)
                - uptime: Seconds since start (if running)
        """
        status = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized": self._initialized,
            "running": self._running,
            "error": str(self._error) if self._error else None,
            "optional": self.optional,
            "dependencies": self.dependencies.copy()
        }

        # Add uptime if running
        if self._running and self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
            status["uptime"] = uptime

        return status

    def is_initialized(self) -> bool:
        """Check if module is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def is_running(self) -> bool:
        """Check if module is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def get_error(self) -> Optional[Exception]:
        """Get last error that occurred.

        Returns:
            Last exception or None
        """
        return self._error

    # ==================== Command Handling (Optional) ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle module-specific commands.

        Optional method - modules can override to handle custom commands.
        Module manager will route commands to appropriate modules.

        Args:
            command: Command name (e.g., "status", "reload")
            args: Command arguments

        Returns:
            Response string or None if command not handled
        """
        # Default: status command
        if command == "status":
            status = self.get_status()
            lines = [f"Module: {self.name} v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")
            if status.get("uptime"):
                lines.append(f"Uptime: {status['uptime']:.1f}s")
            return "\n".join(lines)

        return None

    # ==================== Helper Methods ====================

    def get_dependency(self, module_name: str) -> Optional['RPModule']:
        """Get a module this module depends on.

        Args:
            module_name: Name of dependency module

        Returns:
            Module instance or None if not found
        """
        return self.manager.get(module_name)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def log_info(self, message: str) -> None:
        """Log info message.

        Args:
            message: Message to log
        """
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning message.

        Args:
            message: Message to log
        """
        self.logger.warning(message)

    def log_error(self, message: str, exc: Optional[Exception] = None) -> None:
        """Log error message.

        Args:
            message: Message to log
            exc: Optional exception to log
        """
        if exc:
            self.logger.error(f"{message}: {exc}", exc_info=True)
        else:
            self.logger.error(message)

    # ==================== Internal Lifecycle Wrappers ====================

    def _do_initialize(self) -> bool:
        """Internal wrapper for initialize().

        Called by module manager. Updates state and handles errors.

        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            self.log_warning("Module already initialized")
            return True

        try:
            self.log_info("Initializing module...")
            success = self.initialize()

            if success:
                self._initialized = True
                self._init_time = datetime.now()
                self.log_info("Module initialized successfully")
            else:
                self.log_error("Module initialization failed")

            return success

        except Exception as e:
            self._error = e
            self.log_error("Module initialization error", e)
            return False

    def _do_start(self) -> bool:
        """Internal wrapper for start().

        Called by module manager. Updates state and handles errors.

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            self.log_error("Cannot start - module not initialized")
            return False

        if self._running:
            self.log_warning("Module already running")
            return True

        try:
            self.log_info("Starting module...")
            success = self.start()

            if success:
                self._running = True
                self._start_time = datetime.now()
                self.log_info("Module started successfully")
            else:
                self.log_error("Module start failed")

            return success

        except Exception as e:
            self._error = e
            self.log_error("Module start error", e)
            return False

    def _do_stop(self) -> bool:
        """Internal wrapper for stop().

        Called by module manager. Updates state and handles errors.

        Returns:
            True if successful, False otherwise
        """
        if not self._running:
            self.log_warning("Module not running")
            return True

        try:
            self.log_info("Stopping module...")
            success = self.stop()

            if success:
                self._running = False
                self.log_info("Module stopped successfully")
            else:
                self.log_error("Module stop failed")

            return success

        except Exception as e:
            self._error = e
            self.log_error("Module stop error", e)
            return False

    def _do_cleanup(self) -> None:
        """Internal wrapper for cleanup().

        Called by module manager. Handles errors gracefully.
        """
        try:
            self.log_info("Cleaning up module...")
            self.cleanup()
            self._initialized = False
            self._running = False
            self.log_info("Module cleaned up successfully")

        except Exception as e:
            self._error = e
            self.log_error("Module cleanup error", e)

    # ==================== String Representation ====================

    def __repr__(self) -> str:
        """String representation of module.

        Returns:
            String representation
        """
        state = "running" if self._running else ("initialized" if self._initialized else "not initialized")
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}', state='{state}')>"
