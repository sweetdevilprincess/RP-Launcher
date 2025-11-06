"""App header widget for displaying RP title and context.

This module provides the header banner that shows:
- Current location and timestamp
- RP directory name and chapter
- Quick keyboard hints
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text
from textual.widgets import Static

from ..utils import get_chapter_info


class AppHeader(Static):
    """Compact banner showing RP title and quick hints.

    This header displays:
    - Top row: Location (left) and Timestamp (right)
    - Bottom row: RP name + Chapter (left) and Keyboard hints (right)

    Auto-refreshes every 15 seconds to stay current.
    """

    def __init__(self, rp_dir: Path, **kwargs):
        """Initialize app header.

        Args:
            rp_dir: Path to RP directory
            **kwargs: Additional arguments passed to Static
        """
        super().__init__(**kwargs)
        self.rp_dir = rp_dir

    def on_mount(self) -> None:
        """Set up auto-refresh after mounting."""
        self.refresh_header()
        self.set_interval(15.0, self.refresh_header)

    def refresh_header(self) -> None:
        """Update header display with current information."""
        chapter, timestamp, location = get_chapter_info(
            self.rp_dir / "state" / "current_state.md"
        )

        renderables: list[RenderableType] = []

        # Top row: Location and Timestamp (only if present)
        location_display = location if location and location != "Unknown" else ""
        timestamp_display = timestamp if timestamp and timestamp != "Unknown" else ""

        if location_display or timestamp_display:
            top_row = Table.grid(expand=True, padding=(0, 0))
            top_row.pad_edge = False
            top_row.add_column()
            top_row.add_column(justify="right")
            top_row.add_row(
                Text(location_display, style="bold cyan") if location_display else Text(""),
                Text(timestamp_display, style="bold cyan") if timestamp_display else Text(""),
            )
            renderables.append(top_row)

        # Bottom row: Title + Chapter and Hints
        title = Text(self.rp_dir.name, style="bold")
        if chapter and chapter != "Unknown":
            title.append("  -  ")
            title.append(chapter, style="bold yellow")

        hint_text = Text("F1 Help | Ctrl+T Theme | Ctrl+Q Quit", style="dim")

        bottom_row = Table.grid(expand=True, padding=(0, 0))
        bottom_row.pad_edge = False
        bottom_row.add_column()
        bottom_row.add_column(justify="right")
        bottom_row.add_row(title, hint_text)
        renderables.append(bottom_row)

        self.update(Group(*renderables))


__all__ = ["AppHeader"]
