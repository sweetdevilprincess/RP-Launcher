"""Tests for WIP (Work In Progress) Testing System."""

from __future__ import annotations

from pathlib import Path

import pytest
from refactoring.src.wip import WipExecutor, WipModuleLoader, WipModuleScanner
from refactoring.src.wip.registry import (
    get_component_info,
    is_swappable,
    list_categories,
    list_components,
    validate_registry,
)


class TestWipRegistry:
    """Tests for WIP module registry."""

    def test_registry_has_components(self):
        """Registry defines swappable components."""
        components = list_components()
        assert len(components) > 0

    def test_get_component_info_existing(self):
        """get_component_info returns info for valid component."""
        info = get_component_info("prompt_builder")

        assert info is not None
        assert info.component_id == "prompt_builder"
        assert info.class_name == "PromptBuilder"
        assert "automation" in info.production_module

    def test_get_component_info_nonexistent(self):
        """get_component_info returns None for invalid component."""
        info = get_component_info("nonexistent_component")
        assert info is None

    def test_is_swappable(self):
        """is_swappable correctly identifies registered components."""
        assert is_swappable("prompt_builder") is True
        assert is_swappable("trigger_evaluator") is True
        assert is_swappable("nonexistent") is False

    def test_list_categories(self):
        """list_categories returns unique categories."""
        categories = list_categories()

        assert len(categories) > 0
        assert "automation" in categories or "infrastructure" in categories

    def test_list_components_by_category(self):
        """list_components can filter by category."""
        all_components = list_components()
        automation_components = list_components(category="automation")

        assert len(automation_components) <= len(all_components)
        for comp in automation_components:
            assert comp.category == "automation"

    def test_validate_registry(self):
        """validate_registry finds no errors in current registry."""
        errors = validate_registry()
        assert len(errors) == 0


class TestWipModuleScanner:
    """Tests for WIP module scanner."""

    def test_scanner_initialization(self, tmp_path):
        """Scanner initializes with wip_root."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        scanner = WipModuleScanner(wip_root)

        assert scanner.wip_root == wip_root
        assert scanner.manifest_path == wip_root / "wip_manifest.json"

    def test_scan_empty_directory(self, tmp_path):
        """Scanning empty WIP directory returns no modules."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        scanner = WipModuleScanner(wip_root)
        modules = scanner.scan()

        assert len(modules) == 0

    def test_scan_with_wip_module(self, tmp_path):
        """Scanning directory with WIP file returns module info."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create WIP file matching registry
        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("# WIP PromptBuilder\nclass PromptBuilder:\n    pass\n")

        scanner = WipModuleScanner(wip_root)
        modules = scanner.scan()

        assert len(modules) == 1
        assert modules[0].component_id == "prompt_builder"
        assert modules[0].exists is True
        assert modules[0].file_size > 0

    def test_is_available(self, tmp_path):
        """is_available correctly detects WIP file presence."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        scanner = WipModuleScanner(wip_root)

        # Not available initially
        assert scanner.is_available("prompt_builder") is False

        # Create WIP file
        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        # Now available
        assert scanner.is_available("prompt_builder") is True

    def test_get_wip_module_path(self, tmp_path):
        """get_wip_module_path returns correct file path."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        scanner = WipModuleScanner(wip_root)
        path = scanner.get_wip_module_path("prompt_builder")

        assert path == wip_file
        assert path.exists()

    def test_list_available(self, tmp_path):
        """list_available returns component IDs with WIP versions."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create two WIP files
        for component_id in ["prompt_builder", "trigger_evaluator"]:
            info = get_component_info(component_id)
            if info:
                module_parts = info.production_module.replace("src.", "").split(".")
                wip_file = wip_root / Path(*module_parts).with_suffix(".py")
                wip_file.parent.mkdir(parents=True, exist_ok=True)
                wip_file.write_text(f"class {info.class_name}:\n    pass\n")

        scanner = WipModuleScanner(wip_root)
        available = scanner.list_available()

        assert "prompt_builder" in available
        assert "trigger_evaluator" in available

    def test_manifest_loading(self, tmp_path):
        """Scanner loads manifest file if present."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create manifest
        manifest_path = wip_root / "wip_manifest.json"
        manifest_path.write_text(
            '{"prompt_builder": {"description": "Test WIP", "status": "in_progress"}}'
        )

        scanner = WipModuleScanner(wip_root)
        manifest_data = scanner.get_manifest_data("prompt_builder")

        assert manifest_data is not None
        assert manifest_data["description"] == "Test WIP"
        assert manifest_data["status"] == "in_progress"


class TestWipModuleLoader:
    """Tests for WIP module loader."""

    def test_loader_initialization(self, tmp_path):
        """Loader initializes with wip_root."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        loader = WipModuleLoader(wip_root)

        assert loader.wip_root == wip_root

    def test_load_wip_class_not_found(self, tmp_path):
        """load_wip_class returns None if WIP file doesn't exist."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        loader = WipModuleLoader(wip_root)
        wip_class = loader.load_wip_class("prompt_builder")

        assert wip_class is None

    def test_load_wip_class_success(self, tmp_path):
        """load_wip_class successfully loads WIP class."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create WIP file with valid class
        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text(
            """
class PromptBuilder:
    def __init__(self):
        self.name = "WIP PromptBuilder"
"""
        )

        loader = WipModuleLoader(wip_root)
        wip_class = loader.load_wip_class("prompt_builder")

        assert wip_class is not None
        assert wip_class.__name__ == "PromptBuilder"

        # Can instantiate
        instance = wip_class()
        assert instance.name == "WIP PromptBuilder"

    def test_load_wip_class_caching(self, tmp_path):
        """load_wip_class caches loaded classes."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        loader = WipModuleLoader(wip_root)

        # First load
        class1 = loader.load_wip_class("prompt_builder")
        # Second load (from cache)
        class2 = loader.load_wip_class("prompt_builder")

        assert class1 is class2  # Same object (cached)

    def test_clear_cache(self, tmp_path):
        """clear_cache removes cached modules from loader."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    version = 1\n")

        loader = WipModuleLoader(wip_root)

        # Load and cache
        class1 = loader.load_wip_class("prompt_builder")
        assert class1.version == 1
        assert loader.is_wip_loaded("prompt_builder") is True

        # Clear cache
        loader.clear_cache()

        # Cache should be empty
        assert loader.is_wip_loaded("prompt_builder") is False
        assert len(loader._class_cache) == 0
        assert len(loader._module_cache) == 0

    def test_is_wip_loaded(self, tmp_path):
        """is_wip_loaded correctly reports loaded state."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        loader = WipModuleLoader(wip_root)

        assert loader.is_wip_loaded("prompt_builder") is False

        loader.load_wip_class("prompt_builder")

        assert loader.is_wip_loaded("prompt_builder") is True


class TestWipExecutor:
    """Tests for WIP executor."""

    def test_executor_initialization(self, tmp_path):
        """Executor initializes correctly."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        executor = WipExecutor(wip_root)

        assert executor.wip_root == wip_root
        assert executor.scanner is not None
        assert executor.loader is not None
        assert len(executor.enabled_components) == 0

    def test_enable_disable(self, tmp_path):
        """enable/disable WIP mode for components."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create WIP file
        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        executor = WipExecutor(wip_root)

        # Enable
        success = executor.enable("prompt_builder")
        assert success is True
        assert executor.is_enabled("prompt_builder") is True

        # Disable
        executor.disable("prompt_builder")
        assert executor.is_enabled("prompt_builder") is False

    def test_enable_nonexistent_wip(self, tmp_path):
        """Enabling nonexistent WIP module returns False."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        executor = WipExecutor(wip_root)

        success = executor.enable("prompt_builder")
        assert success is False

    def test_disable_all(self, tmp_path):
        """disable_all disables all WIP components."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        # Create WIP files
        for component_id in ["prompt_builder", "trigger_evaluator"]:
            info = get_component_info(component_id)
            if info:
                module_parts = info.production_module.replace("src.", "").split(".")
                wip_file = wip_root / Path(*module_parts).with_suffix(".py")
                wip_file.parent.mkdir(parents=True, exist_ok=True)
                wip_file.write_text(f"class {info.class_name}:\n    pass\n")

        executor = WipExecutor(wip_root)

        # Enable both
        executor.enable("prompt_builder")
        executor.enable("trigger_evaluator")

        assert len(executor.enabled_components) == 2

        # Disable all
        executor.disable_all()

        assert len(executor.enabled_components) == 0

    def test_get_status(self, tmp_path):
        """get_status returns correct status."""
        wip_root = tmp_path / "wip"
        wip_root.mkdir()

        wip_file = wip_root / "automation" / "services" / "prompt_builder.py"
        wip_file.parent.mkdir(parents=True)
        wip_file.write_text("class PromptBuilder:\n    pass\n")

        executor = WipExecutor(wip_root)
        executor.enable("prompt_builder")

        status = executor.get_status()

        assert "prompt_builder" in status["enabled_components"]
        assert "prompt_builder" in status["available_wip_modules"]
