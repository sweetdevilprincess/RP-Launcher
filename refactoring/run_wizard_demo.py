#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone wizard demo - properly imports the wizard."""

import sys
from pathlib import Path

# Add src to path for proper imports
sys.path.insert(0, str(Path(__file__).parent))

from textual.app import App

# Import only what we need, not the whole TUI app
from src.presentation.tui.screens.startup_wizard_screen import StartupWizardScreen


class WizardDemoApp(App):
    """Demo app for the startup wizard."""

    TITLE = "RP Setup Wizard Demo"

    def on_mount(self) -> None:
        """Push the wizard screen on mount."""
        # Use current directory / RPs for testing
        base_rps_dir = Path.cwd() / "test_rps_output"
        base_rps_dir.mkdir(exist_ok=True)

        wizard = StartupWizardScreen(base_rps_dir=base_rps_dir)
        self.push_screen(wizard)


if __name__ == "__main__":
    try:
        app = WizardDemoApp()
        app.run()
    except Exception as e:
        print(f"Error running wizard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
