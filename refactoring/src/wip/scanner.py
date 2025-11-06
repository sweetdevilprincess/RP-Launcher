"""WIP Module Scanner - Auto-discovers available WIP modules.

Scans the src/wip/ directory to find available WIP implementations,
checks them against the registry, and optionally reads metadata from
a manifest file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .registry import SWAPPABLE_COMPONENTS, ComponentInfo, get_component_info


@dataclass
class WipModuleInfo:
    """Information about a discovered WIP module."""

    component_id: str  # Component identifier from registry
    wip_path: Path  # Path to WIP implementation file
    production_info: ComponentInfo  # Info from registry
    manifest_data: dict[str, Any] | None = None  # Optional manifest metadata
    exists: bool = True  # Whether file actually exists
    file_size: int = 0  # File size in bytes
    last_modified: float = 0.0  # Last modification timestamp


class WipModuleScanner:
    """Scanner for discovering available WIP modules."""

    def __init__(self, wip_root: Path):
        """Initialize scanner.

        Args:
            wip_root: Root directory for WIP modules (typically src/wip/)
        """
        self.wip_root = wip_root
        self.manifest_path = wip_root / "wip_manifest.json"
        self._manifest_cache: dict[str, Any] | None = None

    def scan(self) -> list[WipModuleInfo]:
        """Scan for available WIP modules.

        Returns:
            List of discovered WIP modules with metadata
        """
        wip_modules = []
        manifest = self._load_manifest()

        # Check each registered component
        for component_id, component_info in SWAPPABLE_COMPONENTS.items():
            wip_path = self._get_wip_path(component_info)

            if wip_path and wip_path.exists():
                # Get file stats
                stat = wip_path.stat()

                # Get manifest data for this component
                manifest_data = manifest.get(component_id) if manifest else None

                wip_module = WipModuleInfo(
                    component_id=component_id,
                    wip_path=wip_path,
                    production_info=component_info,
                    manifest_data=manifest_data,
                    exists=True,
                    file_size=stat.st_size,
                    last_modified=stat.st_mtime,
                )
                wip_modules.append(wip_module)

        return sorted(wip_modules, key=lambda m: m.component_id)

    def scan_by_category(self, category: str) -> list[WipModuleInfo]:
        """Scan for WIP modules in a specific category.

        Args:
            category: Category to filter by (e.g., "automation", "infrastructure")

        Returns:
            List of WIP modules in the specified category
        """
        all_modules = self.scan()
        return [m for m in all_modules if m.production_info.category == category]

    def is_available(self, component_id: str) -> bool:
        """Check if WIP version is available for a component.

        Args:
            component_id: Component identifier

        Returns:
            True if WIP file exists
        """
        component_info = get_component_info(component_id)
        if not component_info:
            return False

        wip_path = self._get_wip_path(component_info)
        return wip_path is not None and wip_path.exists()

    def get_wip_module_path(self, component_id: str) -> Path | None:
        """Get the filesystem path for a WIP module.

        Args:
            component_id: Component identifier

        Returns:
            Path to WIP file if it exists, None otherwise
        """
        component_info = get_component_info(component_id)
        if not component_info:
            return None

        wip_path = self._get_wip_path(component_info)
        if wip_path and wip_path.exists():
            return wip_path

        return None

    def _get_wip_path(self, component_info: ComponentInfo) -> Path | None:
        """Convert production module path to WIP file path.

        Args:
            component_info: Component information from registry

        Returns:
            Path to WIP file (may not exist)

        Example:
            production_module: "src.automation.services.prompt_builder"
            -> src/wip/automation/services/prompt_builder.py
        """
        # Remove "src." prefix from module path
        module_path = component_info.production_module
        if module_path.startswith("src."):
            module_path = module_path[4:]  # Remove "src."

        # Convert dot notation to path
        path_parts = module_path.split(".")
        relative_path = Path(*path_parts).with_suffix(".py")

        # Build full WIP path
        wip_path = self.wip_root / relative_path

        return wip_path

    def _load_manifest(self) -> dict[str, Any]:
        """Load WIP manifest file if it exists.

        The manifest is optional and provides additional metadata about
        WIP modules like descriptions, authors, status, etc.

        Returns:
            Manifest data dictionary (empty if file doesn't exist)
        """
        if self._manifest_cache is not None:
            return self._manifest_cache

        if not self.manifest_path.exists():
            self._manifest_cache = {}
            return self._manifest_cache

        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                self._manifest_cache = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Invalid JSON or read error - ignore and return empty
            self._manifest_cache = {}

        return self._manifest_cache

    def reload_manifest(self) -> None:
        """Force reload of manifest file from disk."""
        self._manifest_cache = None
        self._load_manifest()

    def get_manifest_data(self, component_id: str) -> dict[str, Any] | None:
        """Get manifest data for a specific component.

        Args:
            component_id: Component identifier

        Returns:
            Manifest data for component, or None if not found
        """
        manifest = self._load_manifest()
        return manifest.get(component_id)

    def list_available(self) -> list[str]:
        """Get list of component IDs that have WIP versions available.

        Returns:
            Sorted list of component IDs with WIP implementations
        """
        modules = self.scan()
        return [m.component_id for m in modules]

    def get_summary(self) -> dict[str, Any]:
        """Get summary of WIP modules.

        Returns:
            Summary dictionary with counts and lists
        """
        modules = self.scan()

        return {
            "total_swappable": len(SWAPPABLE_COMPONENTS),
            "available_wip": len(modules),
            "by_category": self._count_by_category(modules),
            "wip_modules": [
                {
                    "component_id": m.component_id,
                    "category": m.production_info.category,
                    "file_size": m.file_size,
                    "has_manifest": m.manifest_data is not None,
                }
                for m in modules
            ],
        }

    def _count_by_category(self, modules: list[WipModuleInfo]) -> dict[str, int]:
        """Count WIP modules by category.

        Args:
            modules: List of WIP modules

        Returns:
            Dictionary mapping category to count
        """
        counts: dict[str, int] = {}
        for module in modules:
            category = module.production_info.category
            counts[category] = counts.get(category, 0) + 1
        return counts
