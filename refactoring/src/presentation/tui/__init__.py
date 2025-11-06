"""Refactored TUI (Terminal User Interface) for RP Client.

This package provides a modular, socket-based TUI that connects to the
Bridge service via IPC for all automation functionality.
"""

from .app import RPClientApp

__all__ = ["RPClientApp"]
