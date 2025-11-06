"""WIP (Work In Progress) Testing System.

This module provides a dynamic, self-discovering system for testing new code
implementations alongside production code without requiring Bridge modifications.

Key Components:
- Registry: Defines which components can be swapped
- Scanner: Auto-discovers available WIP modules
- Loader: Dynamically imports WIP implementations
- Executor: Runs both versions and compares results

Workflow:
1. Copy production module to src/wip/ directory
2. Edit WIP version
3. Enable WIP mode via TUI
4. Test with automatic comparison
5. Move WIP to production when ready

The Bridge is modified ONCE to support this system, then never needs
touching again for new WIP modules.
"""

from .executor import ComparisonResult, WipExecutor
from .loader import WipModuleLoader
from .registry import SWAPPABLE_COMPONENTS, ComponentInfo
from .scanner import WipModuleScanner

__all__ = [
    "WipExecutor",
    "WipModuleLoader",
    "WipModuleScanner",
    "ComparisonResult",
    "ComponentInfo",
    "SWAPPABLE_COMPONENTS",
]
