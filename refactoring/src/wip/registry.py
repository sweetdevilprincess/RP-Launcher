"""WIP Module Registry - Defines swappable components.

This registry explicitly lists which architectural components can be
replaced with WIP versions. This provides safety by preventing arbitrary
code injection while still allowing flexible testing.

To add a new swappable component:
1. Add entry to SWAPPABLE_COMPONENTS dict
2. Specify production module path and class name
3. Component is now available for WIP testing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ComponentInfo:
    """Information about a swappable component."""

    component_id: str  # Unique identifier (e.g., "prompt_builder")
    production_module: str  # Full module path (e.g., "src.automation.services.prompt_builder")
    class_name: str  # Class to instantiate (e.g., "PromptBuilder")
    category: str  # Component category (e.g., "automation", "domain")
    description: str  # Human-readable description
    constructor_args: dict[str, Any] | None = None  # Default constructor arguments


# Registry of components that can be swapped with WIP versions
SWAPPABLE_COMPONENTS: dict[str, ComponentInfo] = {
    # Automation Services
    "prompt_builder": ComponentInfo(
        component_id="prompt_builder",
        production_module="src.automation.services.prompt_builder",
        class_name="PromptBuilder",
        category="automation",
        description="Builds prompts from automation context",
    ),
    "file_loader": ComponentInfo(
        component_id="file_loader",
        production_module="src.automation.services.file_loader",
        class_name="FileLoader",
        category="automation",
        description="Loads and processes RP files",
    ),
    # Trigger System
    "trigger_evaluator": ComponentInfo(
        component_id="trigger_evaluator",
        production_module="src.automation.triggers.evaluator",
        class_name="TriggerEvaluator",
        category="automation",
        description="Evaluates semantic triggers",
    ),
    "semantic_evaluator": ComponentInfo(
        component_id="semantic_evaluator",
        production_module="src.automation.triggers.semantic_evaluator",
        class_name="SemanticEvaluator",
        category="automation",
        description="Semantic matching for triggers",
    ),
    # Template System
    "narrative_template_manager": ComponentInfo(
        component_id="narrative_template_manager",
        production_module="src.automation.templates.narrative_template_manager",
        class_name="NarrativeTemplateManager",
        category="automation",
        description="Manages narrative templates",
    ),
    "template_loader": ComponentInfo(
        component_id="template_loader",
        production_module="src.infrastructure.templates.template_loader",
        class_name="TemplateLoader",
        category="infrastructure",
        description="Loads template files",
    ),
    # LLM Clients
    "claude_client": ComponentInfo(
        component_id="claude_client",
        production_module="src.infrastructure.llm.claude_client",
        class_name="ClaudeAPIClient",
        category="infrastructure",
        description="Claude API client",
    ),
    "openai_client": ComponentInfo(
        component_id="openai_client",
        production_module="src.infrastructure.llm.openai_client",
        class_name="OpenAIChatClient",
        category="infrastructure",
        description="OpenAI API client",
    ),
    # Configuration
    "config_loader": ComponentInfo(
        component_id="config_loader",
        production_module="src.infrastructure.config.config_loader",
        class_name="ConfigLoader",
        category="infrastructure",
        description="Configuration loader",
    ),
    # Session Management
    "session_manager": ComponentInfo(
        component_id="session_manager",
        production_module="src.domain.sessions.session_manager",
        class_name="SessionManager",
        category="domain",
        description="Manages RP sessions",
    ),
}


def get_component_info(component_id: str) -> ComponentInfo | None:
    """Get component info by ID.

    Args:
        component_id: Component identifier

    Returns:
        ComponentInfo if found, None otherwise
    """
    return SWAPPABLE_COMPONENTS.get(component_id)


def list_components(category: str | None = None) -> list[ComponentInfo]:
    """List all swappable components, optionally filtered by category.

    Args:
        category: Optional category filter (e.g., "automation", "infrastructure")

    Returns:
        List of ComponentInfo objects
    """
    components = list(SWAPPABLE_COMPONENTS.values())

    if category:
        components = [c for c in components if c.category == category]

    return sorted(components, key=lambda c: c.component_id)


def list_categories() -> list[str]:
    """Get list of all component categories.

    Returns:
        Sorted list of unique categories
    """
    categories = {info.category for info in SWAPPABLE_COMPONENTS.values()}
    return sorted(categories)


def is_swappable(component_id: str) -> bool:
    """Check if a component can be swapped with WIP version.

    Args:
        component_id: Component identifier

    Returns:
        True if component is in registry
    """
    return component_id in SWAPPABLE_COMPONENTS


def validate_registry() -> list[str]:
    """Validate registry for common issues.

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    for component_id, info in SWAPPABLE_COMPONENTS.items():
        # Check ID matches
        if component_id != info.component_id:
            errors.append(f"ID mismatch: key '{component_id}' != info.component_id '{info.component_id}'")

        # Check required fields
        if not info.production_module:
            errors.append(f"{component_id}: Missing production_module")
        if not info.class_name:
            errors.append(f"{component_id}: Missing class_name")
        if not info.category:
            errors.append(f"{component_id}: Missing category")

    # Check for duplicate module paths
    modules = [info.production_module for info in SWAPPABLE_COMPONENTS.values()]
    duplicates = {m for m in modules if modules.count(m) > 1}
    if duplicates:
        errors.append(f"Duplicate production modules: {duplicates}")

    return errors
