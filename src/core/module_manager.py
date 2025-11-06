"""
Module Manager for RP System

Manages lifecycle, dependencies, and configuration for all system modules.
Provides centralized initialization, access, and shutdown functionality.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Any
import logging
from collections import defaultdict, deque

from .base import RPModule


class ModuleManager:
    """Manages all RP system modules.

    The module manager handles:
    - Module registration
    - Dependency resolution
    - Initialization ordering
    - Module lifecycle management
    - Configuration loading
    - Error handling

    Usage:
        manager = ModuleManager(rp_dir, config)
        manager.register(SessionManagerModule)
        manager.register(FileManagerModule)
        manager.initialize_all()

        # Access modules
        session_mgr = manager.get('session_manager')
        session_mgr.retry()

        # Shutdown
        manager.shutdown_all()
    """

    def __init__(self, rp_dir: Path, config: Dict[str, Any]):
        """Initialize module manager.

        Args:
            rp_dir: Path to RP directory
            config: Global configuration dict (should contain 'modules' key)
        """
        self.rp_dir = Path(rp_dir)
        self.config = config

        # Module storage
        self._module_classes: Dict[str, Type[RPModule]] = {}  # name -> class
        self._modules: Dict[str, RPModule] = {}  # name -> instance
        self._initialized_modules: Set[str] = set()
        self._started_modules: Set[str] = set()

        # Initialization order (resolved dependencies)
        self._init_order: List[str] = []

        # Setup logger
        self.logger = self._setup_logger()

        self.logger.info(f"Module manager created for RP: {rp_dir}")

    def _setup_logger(self) -> logging.Logger:
        """Setup module manager logger.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("rp.module_manager")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [MODULE_MANAGER] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    # ==================== Module Registration ====================

    def register(self, module_class: Type[RPModule]) -> None:
        """Register a module class.

        Args:
            module_class: Module class (subclass of RPModule)

        Raises:
            ValueError: If module with same name already registered
        """
        # Get module name from class
        module_name = module_class.name

        if module_name in self._module_classes:
            raise ValueError(f"Module '{module_name}' already registered")

        self._module_classes[module_name] = module_class
        self.logger.info(f"Registered module: {module_name}")

    def unregister(self, module_name: str) -> None:
        """Unregister a module.

        Args:
            module_name: Name of module to unregister

        Raises:
            ValueError: If module is initialized
        """
        if module_name in self._initialized_modules:
            raise ValueError(f"Cannot unregister initialized module: {module_name}")

        if module_name in self._module_classes:
            del self._module_classes[module_name]
            self.logger.info(f"Unregistered module: {module_name}")

    # ==================== Module Configuration ====================

    def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module.

        Args:
            module_name: Name of module

        Returns:
            Module configuration dict (empty if not found)
        """
        modules_config = self.config.get('modules', {})
        module_config = modules_config.get(module_name, {})

        # Return the 'config' sub-dict, or empty dict if not present
        return module_config.get('config', {})

    def _is_module_enabled(self, module_name: str) -> bool:
        """Check if module is enabled in configuration.

        Args:
            module_name: Name of module

        Returns:
            True if enabled (or not specified), False if explicitly disabled
        """
        modules_config = self.config.get('modules', {})
        module_config = modules_config.get(module_name, {})

        # Default to enabled if not specified
        return module_config.get('enabled', True)

    # ==================== Dependency Resolution ====================

    def _resolve_dependencies(self, module_names: List[str]) -> List[str]:
        """Resolve module dependencies using topological sort.

        Args:
            module_names: List of module names to initialize

        Returns:
            List of module names in initialization order

        Raises:
            ValueError: If circular dependency detected or missing dependency
        """
        # Build dependency graph
        graph = defaultdict(list)  # module -> list of dependencies
        in_degree = defaultdict(int)  # module -> number of dependents

        # Initialize all nodes
        for name in module_names:
            if name not in self._module_classes:
                raise ValueError(f"Module not registered: {name}")

            module_class = self._module_classes[name]
            dependencies = module_class.dependencies

            # Check all dependencies exist
            for dep in dependencies:
                if dep not in self._module_classes:
                    if not module_class.optional:
                        raise ValueError(
                            f"Module '{name}' depends on unregistered module '{dep}'"
                        )
                    else:
                        self.logger.warning(
                            f"Optional module '{name}' missing dependency '{dep}', skipping"
                        )
                        continue

                graph[dep].append(name)
                in_degree[name] += 1

        # Topological sort using Kahn's algorithm
        queue = deque([name for name in module_names if in_degree[name] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for circular dependencies
        if len(result) != len(module_names):
            missing = set(module_names) - set(result)
            raise ValueError(f"Circular dependency detected involving: {missing}")

        return result

    # ==================== Module Initialization ====================

    def initialize_all(self) -> bool:
        """Initialize all registered and enabled modules.

        Resolves dependencies and initializes modules in correct order.

        Returns:
            True if all modules initialized successfully, False otherwise
        """
        self.logger.info("Initializing all modules...")

        # Filter to enabled modules only
        enabled_modules = [
            name for name in self._module_classes.keys()
            if self._is_module_enabled(name)
        ]

        if not enabled_modules:
            self.logger.warning("No modules enabled")
            return True

        self.logger.info(f"Enabled modules: {', '.join(enabled_modules)}")

        # Resolve dependencies
        try:
            self._init_order = self._resolve_dependencies(enabled_modules)
            self.logger.info(f"Initialization order: {' -> '.join(self._init_order)}")
        except ValueError as e:
            self.logger.error(f"Dependency resolution failed: {e}")
            return False

        # Initialize modules in order
        for module_name in self._init_order:
            if not self._initialize_module(module_name):
                self.logger.error(f"Failed to initialize module: {module_name}")
                return False

        self.logger.info(f"Successfully initialized {len(self._initialized_modules)} modules")
        return True

    def _initialize_module(self, module_name: str) -> bool:
        """Initialize a single module.

        Args:
            module_name: Name of module to initialize

        Returns:
            True if successful, False otherwise
        """
        if module_name in self._initialized_modules:
            self.logger.warning(f"Module already initialized: {module_name}")
            return True

        # Get module class
        module_class = self._module_classes[module_name]

        # Get module config
        module_config = self._get_module_config(module_name)

        # Create instance
        try:
            module = module_class(self.rp_dir, module_config, self)
        except Exception as e:
            self.logger.error(f"Failed to create module instance '{module_name}': {e}")
            return False

        # Store instance
        self._modules[module_name] = module

        # Initialize
        success = module._do_initialize()

        if success:
            self._initialized_modules.add(module_name)

        return success

    # ==================== Module Lifecycle ====================

    def start_all(self) -> bool:
        """Start all initialized modules.

        Returns:
            True if all modules started successfully, False otherwise
        """
        self.logger.info("Starting all modules...")

        # Start in initialization order
        for module_name in self._init_order:
            if module_name not in self._initialized_modules:
                continue

            module = self._modules[module_name]
            success = module._do_start()

            if success:
                self._started_modules.add(module_name)
            else:
                self.logger.error(f"Failed to start module: {module_name}")
                return False

        self.logger.info(f"Successfully started {len(self._started_modules)} modules")
        return True

    def stop_all(self) -> bool:
        """Stop all running modules (in reverse order).

        Returns:
            True if all modules stopped successfully, False otherwise
        """
        self.logger.info("Stopping all modules...")

        # Stop in reverse order
        success = True
        for module_name in reversed(self._init_order):
            if module_name not in self._started_modules:
                continue

            module = self._modules[module_name]
            if not module._do_stop():
                self.logger.error(f"Failed to stop module: {module_name}")
                success = False
            else:
                self._started_modules.remove(module_name)

        if success:
            self.logger.info("Successfully stopped all modules")

        return success

    def shutdown_all(self) -> None:
        """Shutdown and cleanup all modules (in reverse order).

        Should be called during application shutdown.
        Stops and cleans up all modules gracefully.
        """
        self.logger.info("Shutting down all modules...")

        # Stop all running modules first
        self.stop_all()

        # Cleanup in reverse order
        for module_name in reversed(self._init_order):
            if module_name not in self._modules:
                continue

            module = self._modules[module_name]
            module._do_cleanup()

            if module_name in self._initialized_modules:
                self._initialized_modules.remove(module_name)

        # Clear all storage
        self._modules.clear()
        self._init_order.clear()

        self.logger.info("All modules shut down")

    # ==================== Module Access ====================

    def get(self, module_name: str) -> Optional[RPModule]:
        """Get a module by name.

        Args:
            module_name: Name of module

        Returns:
            Module instance or None if not found
        """
        return self._modules.get(module_name)

    def has(self, module_name: str) -> bool:
        """Check if module exists and is initialized.

        Args:
            module_name: Name of module

        Returns:
            True if module exists and is initialized, False otherwise
        """
        return module_name in self._initialized_modules

    def list_modules(self) -> List[str]:
        """List all registered module names.

        Returns:
            List of module names
        """
        return list(self._module_classes.keys())

    def list_initialized(self) -> List[str]:
        """List all initialized module names.

        Returns:
            List of initialized module names
        """
        return list(self._initialized_modules)

    def list_running(self) -> List[str]:
        """List all running module names.

        Returns:
            List of running module names
        """
        return list(self._started_modules)

    # ==================== Status & Debugging ====================

    def get_status(self) -> Dict[str, Any]:
        """Get status of all modules.

        Returns:
            Dict with overall status and per-module status
        """
        return {
            "total_registered": len(self._module_classes),
            "total_initialized": len(self._initialized_modules),
            "total_running": len(self._started_modules),
            "initialization_order": self._init_order.copy(),
            "modules": {
                name: module.get_status()
                for name, module in self._modules.items()
            }
        }

    def print_status(self) -> None:
        """Print status of all modules to console."""
        print("\n=== Module Manager Status ===")
        print(f"Registered: {len(self._module_classes)}")
        print(f"Initialized: {len(self._initialized_modules)}")
        print(f"Running: {len(self._started_modules)}")
        print(f"\nInitialization order: {' -> '.join(self._init_order)}")

        print("\nModules:")
        for name in self._init_order:
            if name in self._modules:
                module = self._modules[name]
                status = "✓ Running" if module.is_running() else "○ Stopped"
                error = f" (Error: {module.get_error()})" if module.get_error() else ""
                print(f"  {status} {name} v{module.version}{error}")
        print()

    # ==================== Command Routing ====================

    def handle_command(self, command: str) -> Optional[str]:
        """Handle module manager commands.

        Routes commands to appropriate modules or handles manager commands.

        Args:
            command: Full command string

        Returns:
            Response string or None if command not handled
        """
        parts = command.strip().split()
        if not parts:
            return None

        cmd = parts[0].lower()

        # Manager commands
        if cmd == "modules":
            if len(parts) == 1:
                # List all modules
                lines = ["📦 Registered Modules:"]
                for name in self.list_modules():
                    enabled = "✓" if self._is_module_enabled(name) else "✗"
                    status = ""
                    if name in self._modules:
                        module = self._modules[name]
                        if module.is_running():
                            status = " [RUNNING]"
                        elif module.is_initialized():
                            status = " [INITIALIZED]"
                    lines.append(f"  {enabled} {name}{status}")
                return "\n".join(lines)

            elif len(parts) == 2 and parts[1].lower() == "status":
                # Detailed status
                status = self.get_status()
                lines = ["📊 Module Manager Status:"]
                lines.append(f"  Registered: {status['total_registered']}")
                lines.append(f"  Initialized: {status['total_initialized']}")
                lines.append(f"  Running: {status['total_running']}")
                return "\n".join(lines)

        # Route to specific module
        # Format: /module_name command args
        if cmd.startswith("/"):
            module_name = cmd[1:]  # Remove /
            if module_name in self._modules:
                module = self._modules[module_name]
                return module.handle_command(parts[1] if len(parts) > 1 else "status", parts[2:])

        return None

    # ==================== Utility Methods ====================

    def reload_config(self) -> bool:
        """Reload configuration for all modules.

        Note: This only updates config, doesn't reinitialize modules.

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Reloading module configurations...")

        # Would need to reload config from file here
        # For now, just update existing modules with new config
        for module_name, module in self._modules.items():
            new_config = self._get_module_config(module_name)
            module.config = new_config

        self.logger.info("Configuration reloaded")
        return True

    def __repr__(self) -> str:
        """String representation of module manager.

        Returns:
            String representation
        """
        return (
            f"<ModuleManager(registered={len(self._module_classes)}, "
            f"initialized={len(self._initialized_modules)}, "
            f"running={len(self._started_modules)})>"
        )
