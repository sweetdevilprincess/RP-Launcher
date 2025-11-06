"""Context panel widget for displaying story state and progress.

This module provides the left sidebar panel that shows:
- Active characters
- Arc progress bar
- Story momentum (response count)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from ..utils import get_active_characters, get_arc_progress, get_chapter_info, get_response_count


class ContextPanel(ScrollableContainer):
    """Left panel showing context, progress, and quick access menu.

    This scrollable container displays:
    - Active characters in the session
    - Arc progress (visual bar and percentage)
    - Story momentum (total response count)

    The panel auto-refreshes every 3 seconds to stay current.
    """

    def __init__(self, rp_dir: Path, **kwargs):
        """Initialize context panel.

        Args:
            rp_dir: Path to RP directory
            **kwargs: Additional arguments passed to ScrollableContainer
        """
        super().__init__(**kwargs)
        self.rp_dir = rp_dir
        self.content_widget = Static("", expand=True)

    def compose(self) -> ComposeResult:
        """Compose the scrollable context panel.

        Yields:
            Static widget containing panel content
        """
        yield self.content_widget

    def on_mount(self) -> None:
        """Set up auto-refresh after mounting."""
        self.set_interval(3.0, self.refresh_context)
        self.refresh_context()

    def refresh_context(self) -> None:
        """Update context display with current state information."""
        state_file = self.rp_dir / "state" / "current_state.md"
        counter_file = self.rp_dir / "state" / "response_counter.json"

        chapter, timestamp, location = get_chapter_info(state_file)
        active_chars = get_active_characters(self.rp_dir / "state" / "session_triggers.json")
        progress, next_arc, percentage = get_arc_progress(counter_file)
        count = get_response_count(counter_file)

        def clean_value(value: Optional[str]) -> str:
            """Normalize strings for display within the context sidebar.

            Args:
                value: String to clean

            Returns:
                Cleaned string or em dash if empty
            """
            if not value:
                return "-"
            value = value.strip()
            return value or "-"

        def make_panel(title: str, lines: list[Text], border: str) -> Panel:
            """Build a compact panel with centered content.

            Args:
                title: Panel title
                lines: List of text lines to display
                border: Border color style

            Returns:
                Rich Panel object
            """
            renderables = lines or [Text("-", justify="center", style="dim")]
            content = Align.center(Group(*renderables), vertical="middle")
            return Panel(
                content,
                title=f"[b]{title}[/]",
                border_style=border,
                box=box.ROUNDED,
                padding=(0, 1),
                style=Style(bgcolor="rgb(50,50,45)"),
            )

        cards: list[RenderableType] = []

        def add_card(panel: Panel) -> None:
            """Add a panel with padding to cards list.

            Args:
                panel: Panel to add
            """
            cards.append(Padding(panel, (0, 0, 1, 0)))

        # Active Characters Card
        active_list = [
            char for char in active_chars if char and char.strip().lower() != "none"
        ]
        if not active_list:
            active_lines = [Text("No active characters", justify="center", style="dim")]
        else:
            display_names = active_list[:3]
            if len(active_list) > 3:
                display_names.append(f"+{len(active_list) - 3} more")
            active_lines = [
                Text(
                    name,
                    justify="center",
                    style="bold" if idx == 0 else ""
                )
                for idx, name in enumerate(display_names)
            ]
        add_card(make_panel("Active Characters", active_lines, border="cyan"))

        # Arc Progress Card
        arc_total = max(progress + next_arc, 1)
        completion_ratio = progress / arc_total
        bar_length = 20
        filled = int(completion_ratio * bar_length)
        empty = bar_length - filled
        bar_body = "#" * filled + "-" * empty

        if completion_ratio < 0.33:
            bar_color = "red"
        elif completion_ratio < 0.66:
            bar_color = "yellow"
        else:
            bar_color = "green"

        bar_text = Text(f"[{bar_body}]", justify="center", style=bar_color)
        progress_text = Text(
            f"{percentage:>5.1f}% complete",
            justify="center",
            style="bold",
        )
        plural_suffix = "s" if next_arc != 1 else ""
        next_text = Text(
            f"{next_arc} more turn{plural_suffix} to next beat",
            justify="center",
            style="dim",
        )
        arc_panel = make_panel(
            "Arc Progress",
            [
                Text(f"{progress}/{arc_total} turns", justify="center", style="bold"),
                bar_text,
                progress_text,
                next_text,
            ],
            border=bar_color,
        )
        add_card(arc_panel)

        # Story Momentum Card
        momentum_text = Text(
            f"{count} total responses",
            justify="center",
            style="bold",
        )
        add_card(make_panel("Story Momentum", [momentum_text], border="magenta"))

        # Update display
        self.content_widget.update(Group(*cards))


__all__ = ["ContextPanel"]
