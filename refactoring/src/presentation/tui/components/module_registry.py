"""Module Registry - Metadata for available system modules.

This registry defines all available modules in the RP system, including:
- Core modules (essential, always enabled)
- Automation modules (recommended for full functionality)
- Optional modules (enhanced features)

This serves as both documentation and a data source for the Modules settings page.
"""

from dataclasses import dataclass
from enum import Enum


class ModuleCategory(Enum):
    """Module category classification."""
    CORE = "core"
    AUTOMATION = "automation"
    OPTIONAL = "optional"


@dataclass
class ModuleInfo:
    """Module metadata and configuration.

    Attributes:
        id: Unique module identifier (matches config key)
        name: Display name for UI
        description: Brief description of module functionality
        category: Module category (core/automation/optional)
        dependencies: List of module IDs this module requires
        toggleable: Whether user can enable/disable this module
        default_enabled: Whether module is enabled by default
    """
    id: str
    name: str
    description: str
    category: ModuleCategory
    dependencies: list[str]
    toggleable: bool = True
    default_enabled: bool = True


# =============================================================================
# Module Registry
# =============================================================================
# Define all available modules here. This serves as both documentation and
# a data source for the UI. When real modules are implemented, this can be
# replaced with a bridge API call.

MODULE_REGISTRY: list[ModuleInfo] = [
    # =========================================================================
    # Core Modules (Essential - Always Enabled)
    # =========================================================================
    ModuleInfo(
        id="entity_manager",
        name="Entity Manager",
        description="Manages characters, locations, items, and world entities",
        category=ModuleCategory.CORE,
        dependencies=[],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="session_manager",
        name="Session Management",
        description="Save states, checkpoints, and session history",
        category=ModuleCategory.CORE,
        dependencies=[],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="file_manager",
        name="File Manager",
        description="File I/O operations and backup management",
        category=ModuleCategory.CORE,
        dependencies=[],
        toggleable=False,
        default_enabled=True
    ),

    # =========================================================================
    # Automation Modules (Recommended)
    # =========================================================================
    ModuleInfo(
        id="template_system",
        name="Template System",
        description="Processes prompt templates and narrative guides",
        category=ModuleCategory.CORE,
        dependencies=[],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="trigger_system",
        name="Trigger System",
        description="Evaluates and executes automation triggers",
        category=ModuleCategory.CORE,
        dependencies=["template_system"],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="agent_coordinator",
        name="Agent Coordinator",
        description="Background task management and agent orchestration",
        category=ModuleCategory.CORE,
        dependencies=["trigger_system"],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="character_preferences",
        name="Character Preferences",
        description="Auto-generates and tracks character preferences",
        category=ModuleCategory.CORE,
        dependencies=["entity_manager", "agent_coordinator"],
        toggleable=False,
        default_enabled=True
    ),
    ModuleInfo(
        id="time_tracking",
        name="Time Tracking",
        description="Tracks in-world time passage and calculates activity durations",
        category=ModuleCategory.AUTOMATION,
        dependencies=["agent_coordinator"],
        toggleable=True,
        default_enabled=True
    ),
    ModuleInfo(
        id="memory_creation",
        name="Memory Creation",
        description="Extracts memorable moments and saves to character memory logs",
        category=ModuleCategory.AUTOMATION,
        dependencies=["agent_coordinator", "entity_manager"],
        toggleable=True,
        default_enabled=True
    ),

    # =========================================================================
    # Optional Modules
    # =========================================================================
    ModuleInfo(
        id="branch_management",
        name="Branch Management",
        description="Timeline branching and alternative story paths",
        category=ModuleCategory.OPTIONAL,
        dependencies=["session_manager"],
        toggleable=True,
        default_enabled=True
    ),
    ModuleInfo(
        id="story_genome",
        name="Story Genome",
        description="Advanced narrative analysis and story structure tracking",
        category=ModuleCategory.OPTIONAL,
        dependencies=["entity_manager"],
        toggleable=True,
        default_enabled=False
    ),
    ModuleInfo(
        id="scene_tracking",
        name="Scene Tracking",
        description="Tracks scene changes, locations, and narrative flow",
        category=ModuleCategory.OPTIONAL,
        dependencies=["entity_manager"],
        toggleable=True,
        default_enabled=False
    ),
    ModuleInfo(
        id="advanced_analytics",
        name="Advanced Analytics",
        description="Performance metrics, usage statistics, and insights",
        category=ModuleCategory.OPTIONAL,
        dependencies=[],
        toggleable=True,
        default_enabled=False
    ),
    ModuleInfo(
        id="export_system",
        name="Export System",
        description="Export data to various formats (Markdown, JSON, etc.)",
        category=ModuleCategory.OPTIONAL,
        dependencies=["entity_manager", "session_manager"],
        toggleable=True,
        default_enabled=True
    ),
]


# =============================================================================
# Helper Functions
# =============================================================================

def get_modules_by_category(category: ModuleCategory) -> list[ModuleInfo]:
    """Get all modules in a specific category.

    Args:
        category: Module category to filter by

    Returns:
        List of modules in the specified category
    """
    return [m for m in MODULE_REGISTRY if m.category == category]


def get_module_by_id(module_id: str) -> ModuleInfo | None:
    """Get module info by ID.

    Args:
        module_id: Module identifier

    Returns:
        ModuleInfo if found, None otherwise
    """
    for module in MODULE_REGISTRY:
        if module.id == module_id:
            return module
    return None


def get_module_dependencies(module_id: str) -> list[ModuleInfo]:
    """Get all dependencies for a module.

    Args:
        module_id: Module identifier

    Returns:
        List of ModuleInfo objects for all dependencies
    """
    module = get_module_by_id(module_id)
    if not module:
        return []

    dependencies = []
    for dep_id in module.dependencies:
        dep_module = get_module_by_id(dep_id)
        if dep_module:
            dependencies.append(dep_module)

    return dependencies


def validate_dependencies(enabled_modules: set[str]) -> dict[str, list[str]]:
    """Validate that all dependencies are satisfied.

    Args:
        enabled_modules: Set of enabled module IDs

    Returns:
        Dict mapping module IDs to list of missing dependencies (empty if valid)
    """
    issues = {}

    for module_id in enabled_modules:
        module = get_module_by_id(module_id)
        if not module:
            continue

        missing_deps = []
        for dep_id in module.dependencies:
            if dep_id not in enabled_modules:
                missing_deps.append(dep_id)

        if missing_deps:
            issues[module_id] = missing_deps

    return issues


__all__ = [
    "ModuleCategory",
    "ModuleInfo",
    "MODULE_REGISTRY",
    "get_modules_by_category",
    "get_module_by_id",
    "get_module_dependencies",
    "validate_dependencies",
]
