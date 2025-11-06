"""WIP Execution Wrapper - Runs both versions and compares results.

This module provides the core functionality of the WIP testing system:
executing operations through both production and WIP code, catching errors,
and comparing results to detect bugs and conflicts.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .loader import WipModuleLoader
from .registry import get_component_info
from .scanner import WipModuleScanner


@dataclass
class ComparisonResult:
    """Result of comparing production and WIP execution."""

    component_id: str  # Component that was tested
    method_name: str  # Method that was called
    production_result: Any  # Result from production code
    wip_result: Any | None  # Result from WIP code (None if error)
    wip_error: str | None  # Error from WIP code (None if success)
    wip_traceback: str | None = None  # Full traceback if WIP errored
    execution_time_prod: float = 0.0  # Production execution time (seconds)
    execution_time_wip: float = 0.0  # WIP execution time (seconds)
    differences: list[str] = field(default_factory=list)  # Detected differences
    success: bool = True  # Overall success (WIP didn't crash)

    def has_wip_error(self) -> bool:
        """Check if WIP execution failed."""
        return self.wip_error is not None

    def has_differences(self) -> bool:
        """Check if results differ between production and WIP."""
        return len(self.differences) > 0

    def is_identical(self) -> bool:
        """Check if results are identical."""
        return not self.has_wip_error() and not self.has_differences()

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.has_wip_error():
            return f"WIP ERROR: {self.wip_error}"

        if self.is_identical():
            return "Results identical"

        return f"Found {len(self.differences)} difference(s)"


class WipExecutor:
    """Executor for running operations through both production and WIP code."""

    def __init__(self, wip_root: Path):
        """Initialize executor.

        Args:
            wip_root: Root directory for WIP modules (typically src/wip/)
        """
        self.wip_root = wip_root
        self.scanner = WipModuleScanner(wip_root)
        self.loader = WipModuleLoader(wip_root)
        self.enabled_components: set[str] = set()

    def enable(self, component_id: str) -> bool:
        """Enable WIP mode for a component.

        Args:
            component_id: Component to enable

        Returns:
            True if enabled successfully, False if WIP not available
        """
        if not self.scanner.is_available(component_id):
            return False

        self.enabled_components.add(component_id)
        return True

    def disable(self, component_id: str) -> None:
        """Disable WIP mode for a component.

        Args:
            component_id: Component to disable
        """
        self.enabled_components.discard(component_id)

    def disable_all(self) -> None:
        """Disable WIP mode for all components."""
        self.enabled_components.clear()

    def is_enabled(self, component_id: str) -> bool:
        """Check if WIP mode is enabled for a component.

        Args:
            component_id: Component to check

        Returns:
            True if WIP mode is enabled
        """
        return component_id in self.enabled_components

    def execute_with_comparison(
        self,
        component_id: str,
        method_name: str,
        args: tuple = (),
        kwargs: dict | None = None,
        *,
        production_instance: Any = None,
        wip_instance: Any = None,
    ) -> ComparisonResult:
        """Execute method through both production and WIP code.

        Args:
            component_id: Component identifier
            method_name: Name of method to call
            args: Positional arguments for method
            kwargs: Keyword arguments for method
            production_instance: Optional pre-created production instance
            wip_instance: Optional pre-created WIP instance

        Returns:
            ComparisonResult with execution results and comparison
        """
        import time

        kwargs = kwargs or {}

        # Execute production version
        prod_start = time.time()
        try:
            if production_instance:
                method = getattr(production_instance, method_name)
                production_result = method(*args, **kwargs)
            else:
                production_result = None  # Need instance
        except Exception as e:
            # Production shouldn't fail, but handle it
            production_result = None
            prod_error = str(e)
        else:
            prod_error = None
        prod_time = time.time() - prod_start

        # Execute WIP version if enabled
        wip_start = time.time()
        wip_result = None
        wip_error = None
        wip_traceback = None

        if self.is_enabled(component_id):
            try:
                if wip_instance:
                    method = getattr(wip_instance, method_name)
                    wip_result = method(*args, **kwargs)
                else:
                    wip_result = None  # Need instance
            except Exception as e:
                wip_error = str(e)
                wip_traceback = traceback.format_exc()

        wip_time = time.time() - wip_start

        # Compare results
        differences = []
        if wip_result is not None and production_result is not None:
            differences = self._compare_results(production_result, wip_result)

        return ComparisonResult(
            component_id=component_id,
            method_name=method_name,
            production_result=production_result,
            wip_result=wip_result,
            wip_error=wip_error,
            wip_traceback=wip_traceback,
            execution_time_prod=prod_time,
            execution_time_wip=wip_time,
            differences=differences,
            success=wip_error is None,
        )

    def create_instances(
        self,
        component_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> tuple[Any, Any | None]:
        """Create both production and WIP instances.

        Args:
            component_id: Component identifier
            *args: Positional arguments for constructors
            **kwargs: Keyword arguments for constructors

        Returns:
            Tuple of (production_instance, wip_instance)
            wip_instance is None if WIP not enabled or failed to create
        """
        # Create production instance
        try:
            production_instance = self.loader.create_production_instance(
                component_id, *args, **kwargs
            )
        except Exception:
            production_instance = None

        # Create WIP instance if enabled
        wip_instance = None
        if self.is_enabled(component_id):
            try:
                wip_instance = self.loader.create_wip_instance(component_id, *args, **kwargs)
            except Exception:
                # WIP creation failed - will be reported when method is called
                pass

        return production_instance, wip_instance

    def _compare_results(self, production: Any, wip: Any) -> list[str]:
        """Compare production and WIP results.

        Args:
            production: Result from production code
            wip: Result from WIP code

        Returns:
            List of difference descriptions
        """
        differences = []

        # Type comparison
        if type(production) != type(wip):
            differences.append(
                f"Type mismatch: {type(production).__name__} (prod) vs {type(wip).__name__} (WIP)"
            )
            return differences  # Can't compare further if types differ

        # String comparison
        if isinstance(production, str):
            if production != wip:
                differences.append(f"String length: {len(production)} (prod) vs {len(wip)} (WIP)")
                if len(production) < 200 and len(wip) < 200:
                    differences.append(f"Production: {production!r}")
                    differences.append(f"WIP: {wip!r}")

        # Numeric comparison
        elif isinstance(production, (int, float)):
            if production != wip:
                differences.append(f"Value: {production} (prod) vs {wip} (WIP)")

        # List/tuple comparison
        elif isinstance(production, (list, tuple)):
            if len(production) != len(wip):
                differences.append(f"Length: {len(production)} (prod) vs {len(wip)} (WIP)")

            # Compare elements
            for i, (p_item, w_item) in enumerate(zip(production, wip)):
                if p_item != w_item:
                    differences.append(f"Element {i}: {p_item!r} (prod) vs {w_item!r} (WIP)")

        # Dict comparison
        elif isinstance(production, dict):
            # Check keys
            prod_keys = set(production.keys())
            wip_keys = set(wip.keys())

            if prod_keys != wip_keys:
                missing_in_wip = prod_keys - wip_keys
                extra_in_wip = wip_keys - prod_keys

                if missing_in_wip:
                    differences.append(f"Missing keys in WIP: {missing_in_wip}")
                if extra_in_wip:
                    differences.append(f"Extra keys in WIP: {extra_in_wip}")

            # Compare common keys
            for key in prod_keys & wip_keys:
                if production[key] != wip[key]:
                    differences.append(
                        f"Key '{key}': {production[key]!r} (prod) vs {wip[key]!r} (WIP)"
                    )

        # Generic equality
        elif production != wip:
            differences.append(f"Values differ: {production!r} (prod) vs {wip!r} (WIP)")

        return differences

    def get_status(self) -> dict[str, Any]:
        """Get status of WIP executor.

        Returns:
            Status dictionary with enabled components and available WIP modules
        """
        available = self.scanner.list_available()

        return {
            "enabled_components": sorted(self.enabled_components),
            "available_wip_modules": sorted(available),
            "loaded_wip_modules": sorted(self.loader.get_loaded_components()),
        }

    def reload_wip_module(self, component_id: str) -> bool:
        """Reload a WIP module from disk.

        Useful during development when WIP code changes.

        Args:
            component_id: Component to reload

        Returns:
            True if reloaded successfully
        """
        reloaded_class = self.loader.reload_wip_module(component_id)
        return reloaded_class is not None
