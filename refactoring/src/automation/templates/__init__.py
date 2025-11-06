"""Template management system for narrative guidance.

This module provides template loading, caching, and rendering for
genre-specific narrative instructions.

Core Components:
- TemplateCache: LRU cache for template files
- TemplateLoader: Loads and parses templates from JSON files
- TemplateRegistry: Discovers and manages available templates
- NarrativeTemplateManager: High-level template selection and rendering

Refactored from src/automation/prompt_templates.py
"""

from .narrative_template_manager import NarrativeTemplateManager
from .template_cache import TemplateCache
from .template_loader import TemplateLoader
from .template_registry import TemplateRegistry

__all__ = [
    "NarrativeTemplateManager",
    "TemplateCache",
    "TemplateLoader",
    "TemplateRegistry",
]
