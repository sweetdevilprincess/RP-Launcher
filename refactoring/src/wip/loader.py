"""WIP Module Loader - Dynamically imports WIP implementations.

Uses importlib to dynamically load WIP modules at runtime, allowing the
Bridge to use WIP versions without hardcoded imports.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from .registry import get_component_info


class WipModuleLoader:
    """Loader for dynamically importing WIP modules."""

    def __init__(self, wip_root: Path):
        """Initialize loader.

        Args:
            wip_root: Root directory for WIP modules (typically src/wip/)
        """
        self.wip_root = wip_root
        self._module_cache: dict[str, Any] = {}
        self._class_cache: dict[str, type] = {}

    def load_wip_class(self, component_id: str) -> type | None:
        """Load WIP class for a component.

        Args:
            component_id: Component identifier from registry

        Returns:
            WIP class if successfully loaded, None otherwise
        """
        # Check cache first
        if component_id in self._class_cache:
            return self._class_cache[component_id]

        # Get component info from registry
        component_info = get_component_info(component_id)
        if not component_info:
            return None

        # Build WIP module path
        wip_module_path = self._get_wip_module_path(component_info.production_module)
        if not wip_module_path:
            return None

        # Check if file exists
        wip_file_path = self._module_path_to_file_path(wip_module_path)
        if not wip_file_path or not wip_file_path.exists():
            return None

        try:
            # Load module using importlib
            module = self._load_module(wip_module_path, wip_file_path)

            # Get class from module
            class_obj = getattr(module, component_info.class_name, None)
            if class_obj is None:
                return None

            # Cache and return
            self._class_cache[component_id] = class_obj
            return class_obj

        except Exception:
            # Import failed - return None
            return None

    def load_production_class(self, component_id: str) -> type | None:
        """Load production class for a component.

        Args:
            component_id: Component identifier from registry

        Returns:
            Production class if successfully loaded, None otherwise
        """
        component_info = get_component_info(component_id)
        if not component_info:
            return None

        try:
            # Import production module
            module = importlib.import_module(component_info.production_module)

            # Get class
            class_obj = getattr(module, component_info.class_name, None)
            return class_obj

        except Exception:
            return None

    def create_wip_instance(self, component_id: str, *args: Any, **kwargs: Any) -> Any:
        """Create instance of WIP class.

        Args:
            component_id: Component identifier
            *args: Positional arguments for constructor
            **kwargs: Keyword arguments for constructor

        Returns:
            Instance of WIP class

        Raises:
            ImportError: If WIP class cannot be loaded
            TypeError: If constructor fails
        """
        wip_class = self.load_wip_class(component_id)
        if wip_class is None:
            raise ImportError(f"WIP class not found for component: {component_id}")

        return wip_class(*args, **kwargs)

    def create_production_instance(self, component_id: str, *args: Any, **kwargs: Any) -> Any:
        """Create instance of production class.

        Args:
            component_id: Component identifier
            *args: Positional arguments for constructor
            **kwargs: Keyword arguments for constructor

        Returns:
            Instance of production class

        Raises:
            ImportError: If production class cannot be loaded
            TypeError: If constructor fails
        """
        prod_class = self.load_production_class(component_id)
        if prod_class is None:
            raise ImportError(f"Production class not found for component: {component_id}")

        return prod_class(*args, **kwargs)

    def _get_wip_module_path(self, production_module: str) -> str | None:
        """Convert production module path to WIP module path.

        Args:
            production_module: Production module path (e.g., "src.automation.services.prompt_builder")

        Returns:
            WIP module path (e.g., "src.wip.automation.services.prompt_builder")

        Example:
            "src.automation.services.prompt_builder"
            -> "src.wip.automation.services.prompt_builder"
        """
        if not production_module.startswith("src."):
            return None

        # Remove "src." prefix
        module_suffix = production_module[4:]  # Remove "src."

        # Build WIP module path
        wip_module_path = f"src.wip.{module_suffix}"

        return wip_module_path

    def _module_path_to_file_path(self, module_path: str) -> Path | None:
        """Convert module path to file path.

        Args:
            module_path: Module path (e.g., "src.wip.automation.services.prompt_builder")

        Returns:
            File path (e.g., src/wip/automation/services/prompt_builder.py)
        """
        if not module_path.startswith("src.wip."):
            return None

        # Remove "src.wip." prefix
        module_suffix = module_path[8:]  # Remove "src.wip."

        # Convert to path
        path_parts = module_suffix.split(".")
        relative_path = Path(*path_parts).with_suffix(".py")

        # Build full path
        full_path = self.wip_root / relative_path

        return full_path

    def _load_module(self, module_path: str, file_path: Path) -> Any:
        """Load module from file using importlib.

        Args:
            module_path: Full module path (e.g., "src.wip.automation.services.prompt_builder")
            file_path: Path to Python file

        Returns:
            Loaded module

        Raises:
            ImportError: If module cannot be loaded
        """
        # Check cache first
        if module_path in self._module_cache:
            return self._module_cache[module_path]

        # Create module spec
        spec = importlib.util.spec_from_file_location(module_path, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create spec for module: {module_path}")

        # Create module
        module = importlib.util.module_from_spec(spec)

        # Add to sys.modules so relative imports work
        sys.modules[module_path] = module

        try:
            # Execute module
            spec.loader.exec_module(module)

            # Cache and return
            self._module_cache[module_path] = module
            return module

        except Exception as e:
            # Remove from sys.modules on failure
            sys.modules.pop(module_path, None)
            raise ImportError(f"Failed to load module {module_path}: {e}") from e

    def clear_cache(self) -> None:
        """Clear the module and class caches.

        Useful for reloading WIP modules after changes.
        """
        # Remove WIP modules from sys.modules
        wip_modules = [name for name in sys.modules if name.startswith("src.wip.")]
        for name in wip_modules:
            del sys.modules[name]

        # Clear caches
        self._module_cache.clear()
        self._class_cache.clear()

    def reload_wip_module(self, component_id: str) -> type | None:
        """Reload a WIP module from disk.

        Args:
            component_id: Component identifier

        Returns:
            Reloaded WIP class, or None if failed
        """
        # Remove from caches
        self._class_cache.pop(component_id, None)

        # Get module path
        component_info = get_component_info(component_id)
        if not component_info:
            return None

        wip_module_path = self._get_wip_module_path(component_info.production_module)
        if wip_module_path:
            self._module_cache.pop(wip_module_path, None)
            sys.modules.pop(wip_module_path, None)

        # Load fresh
        return self.load_wip_class(component_id)

    def is_wip_loaded(self, component_id: str) -> bool:
        """Check if WIP module is currently loaded.

        Args:
            component_id: Component identifier

        Returns:
            True if WIP class is loaded in cache
        """
        return component_id in self._class_cache

    def get_loaded_components(self) -> list[str]:
        """Get list of component IDs with loaded WIP classes.

        Returns:
            List of component IDs
        """
        return list(self._class_cache.keys())
