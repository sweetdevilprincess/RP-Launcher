#!/usr/bin/env python3
"""Runner script for the Trigger Editor UI mockup.

This script launches the standalone trigger editor mockup for preview and testing.

Usage:
    python scripts/run_trigger_editor_mockup.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.presentation.tui.components.trigger_editor_mockup import TriggerEditorMockupApp


def main():
    """Launch the trigger editor mockup."""
    print("=" * 60)
    print("Trigger Editor UI Mockup")
    print("=" * 60)
    print()
    print("This is a standalone preview of the trigger editor interface.")
    print()
    print("Features:")
    print("  - Add new characters with trigger words")
    print("  - Edit existing characters")
    print("  - Remove characters")
    print("  - Interactive table with selection")
    print()
    print("Controls:")
    print("  - Click rows to select")
    print("  - Use buttons to Add, Edit, Remove")
    print("  - Ctrl+Q to quit")
    print()
    print("=" * 60)
    print()

    app = TriggerEditorMockupApp()
    app.run()


if __name__ == "__main__":
    main()
