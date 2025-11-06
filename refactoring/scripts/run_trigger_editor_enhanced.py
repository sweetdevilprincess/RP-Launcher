#!/usr/bin/env python3
"""Runner script for the Enhanced Trigger Editor UI mockup.

This script launches the improved three-panel trigger editor mockup.

Usage:
    python scripts/run_trigger_editor_enhanced.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.presentation.tui.components.trigger_editor_enhanced_mockup import EnhancedTriggerEditorApp


def main():
    """Launch the enhanced trigger editor mockup."""
    print("=" * 70)
    print("Enhanced Trigger Editor UI Mockup - Multi-Panel Responsive Layout")
    print("=" * 70)
    print()
    print("This mockup demonstrates an improved three-panel interface:")
    print()
    print("Layout:")
    print("  +------------+------------------+------------------+")
    print("  | Character  |  Character       |  Trigger         |")
    print("  | List       |  Sheet Preview   |  Editor          |")
    print("  | (sidebar)  |  (content)       |  (form)          |")
    print("  +------------+------------------+------------------+")
    print()
    print("Features:")
    print("  * Responsive three-panel grid layout")
    print("  * Character list sidebar for quick navigation")
    print("  * Live character sheet preview to inform trigger selection")
    print("  * Dedicated trigger editor with dynamic fields")
    print("  * Adaptive sizing based on window dimensions")
    print()
    print("Controls:")
    print("  - Click character names in left panel to select")
    print("  - View character details in middle panel")
    print("  - Edit triggers in right panel")
    print("  - Use 'Add Trigger' button to add more fields")
    print("  - Ctrl+S to save (mockup)")
    print("  - Ctrl+Q to quit")
    print()
    print("=" * 70)
    print()

    app = EnhancedTriggerEditorApp()
    app.run()


if __name__ == "__main__":
    main()
