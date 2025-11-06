"""Branches Page - Visualize and manage RP storyline branches.

This page provides:
- ASCII tree visualization of branch hierarchy
- Branch details and metadata
- Actions for switching, creating, and comparing branches
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Container
from textual.widgets import Static, Button, Tree
from textual.message import Message

from ....infrastructure.ipc import IPCMessageType


class BranchesPage(Horizontal):
    """Branches page for managing RP storyline branches.

    Features:
    - ASCII tree visualization showing branch hierarchy
    - Branch details panel with metadata
    - Action buttons (Switch, Create, Compare)
    - Connects to SessionService for real branch data
    """

    DEFAULT_CSS = """
    BranchesPage {
        background: $panel;
        width: 1fr;
        height: 1fr;
        layout: horizontal;
    }

    BranchesPage .tree-section {
        width: 30%;
        height: 100%;
        background: $surface;
        border-right: solid $primary;
        padding: 1 2;
    }

    BranchesPage .section-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    BranchesPage Tree {
        width: 100%;
        height: 1fr;
        background: $surface;
    }

    BranchesPage Tree:focus .tree--cursor {
        background: $accent;
        color: $panel;
    }

    BranchesPage .tree--guides {
        color: $primary;
    }

    BranchesPage .tree--label {
        color: $text;
    }

    BranchesPage .details-section {
        width: 70%;
        height: 100%;
        background: $panel;
        padding: 2;
    }

    BranchesPage .page-title {
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
        text-align: center;
    }

    BranchesPage #timeline-position {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        color: $text-muted;
    }

    BranchesPage #message-preview {
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
        color: $text;
    }

    BranchesPage .section-header {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }

    BranchesPage .action-buttons {
        layout: horizontal;
        height: auto;
        margin-top: 2;
    }

    BranchesPage Button {
        margin: 0 1 0 0;
    }
    """

    class BranchSelected(Message, bubble=True):
        """Posted when a branch is selected."""
        def __init__(self, branch_id: str) -> None:
            super().__init__()
            self.branch_id = branch_id

    class BranchAction(Message, bubble=True):
        """Posted when a branch action button is clicked."""
        def __init__(self, action: str, branch_id: str | None = None) -> None:
            super().__init__()
            self.action = action
            self.branch_id = branch_id

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.branches: dict[str, dict] = {}
        self.current_branch_id: str | None = None

    def compose(self) -> ComposeResult:
        # Left section - Branch tree
        with Container(classes="tree-section"):
            yield Static("Branch Timeline", classes="section-title")
            self.branch_tree = Tree("Branches", id="branch-tree")
            self.branch_tree.show_root = False
            self.branch_tree.show_guides = True
            yield self.branch_tree

        # Right section - Branch details and actions
        with VerticalScroll(classes="details-section"):
            yield Static("RP Branches", classes="page-title")

            # Branch details container
            yield Static(id="branch-details")

            # Timeline position display
            yield Static(id="timeline-position")

            # Message preview
            yield Static(id="message-preview")

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("Switch to This", id="switch-branch-btn", variant="primary")
                yield Button("Create New Branch", id="create-branch-btn")
                yield Button("Compare Branches", id="compare-branch-btn")

    def on_mount(self) -> None:
        """Load branches from SessionService when mounted."""
        # TEMPORARY: Load mock data for testing visualization
        self._load_mock_branches()
        # self.load_branches()  # Uncomment when bridge is ready

    def load_branches(self) -> None:
        """Load branches from SessionService via IPC."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            self.branches = {}
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.GET_BRANCHES,
                timeout=5.0
            )

            if response.success:
                self.branches = response.data.get("branches", {})
                self.current_timeline = response.data.get("current_timeline")

                if self.branches:
                    self.app.notify(f"Loaded {len(self.branches)} branches", severity="information")
                else:
                    self.app.notify("No branches found - session may be empty", severity="information")

                self.refresh_display()
            else:
                self.app.notify(f"Failed to load branches: {response.error_message}", severity="error")
                self.branches = {}

        except Exception as e:
            self.app.notify(f"Error loading branches: {e}", severity="error")
            self.branches = {}

    def _load_mock_branches(self) -> None:
        """Load mock branch data for testing visualization."""
        self.branches = {
            "main": {
                "title": "Main Storyline",
                "active": False,
                "parent": None,
                "branch_point": None,
                "tags": ["canon", "primary"],
                "in_game_datetime": "Day 15, Evening - The Harvest Moon",
                "entry_count": 45,
                "description": "The heroes arrive at the ancient temple of Thaldrin, seeking the legendary Crystal of Souls. The air is thick with magic and danger.",
                "messages": [
                    {"response_num": 43, "sender": "You", "content": "We approach the ancient temple cautiously"},
                    {"response_num": 44, "sender": "DM", "content": "The temple looms before you, covered in mysterious runes"},
                    {"response_num": 45, "sender": "You", "content": "I study the runes for any warnings or clues"}
                ]
            },
            "branch_temple_explore": {
                "title": "Explore Temple Thoroughly",
                "active": True,
                "parent": "main",
                "branch_point": 45,
                "tags": ["exploration", "lore"],
                "in_game_datetime": "Day 15, Late Evening - The Harvest Moon",
                "entry_count": 12,
                "description": "Taking time to investigate every corner, they discover hidden murals depicting the temple's history. Ancient warnings speak of those who rushed ahead.",
                "messages": [
                    {"response_num": 46, "sender": "You", "content": "I decide to explore every corner carefully"},
                    {"response_num": 47, "sender": "DM", "content": "You discover hidden murals depicting the temple's ancient history"},
                    {"response_num": 48, "sender": "You", "content": "I take notes on the murals and search for more clues"}
                ]
            },
            "branch_temple_rush": {
                "title": "Rush Through Temple",
                "active": False,
                "parent": "main",
                "branch_point": 45,
                "tags": ["action", "combat"],
                "in_game_datetime": "Day 15, Late Evening - The Harvest Moon",
                "entry_count": 8,
                "description": "Hearing the sound of pursuit echoing through the halls, the party decides speed is more important than caution. They press deeper into the temple.",
                "messages": [
                    {"response_num": 46, "sender": "You", "content": "We hear footsteps behind us - time to move fast!"},
                    {"response_num": 47, "sender": "DM", "content": "You rush through the corridors, the sound of pursuit growing closer"},
                    {"response_num": 48, "sender": "You", "content": "I sprint toward the inner chamber"}
                ]
            },
            "branch_artifact_choice": {
                "title": "Take Artifact Immediately",
                "active": False,
                "parent": "branch_temple_explore",
                "branch_point": 48,
                "tags": ["consequence"],
                "in_game_datetime": "Day 16, Midnight - The Harvest Moon",
                "entry_count": 5,
                "description": "Without hesitation, they grab the glowing crystal from its pedestal. The room begins to shake as ancient defenses activate.",
                "messages": [
                    {"response_num": 49, "sender": "You", "content": "I grab the crystal without hesitation"},
                    {"response_num": 50, "sender": "DM", "content": "The room begins to shake violently! Traps activate!"},
                    {"response_num": 51, "sender": "You", "content": "I run for the exit with the crystal!"}
                ]
            },
            "branch_artifact_study": {
                "title": "Study Artifact First",
                "active": False,
                "parent": "branch_temple_explore",
                "branch_point": 48,
                "tags": ["knowledge", "safe"],
                "in_game_datetime": "Day 16, Midnight - The Harvest Moon",
                "entry_count": 7,
                "description": "The mage suggests examining the protective runes before touching anything. Her caution proves wise as they discover the proper ritual to safely claim the crystal.",
                "messages": [
                    {"response_num": 49, "sender": "You", "content": "Wait - let's examine the runes around the pedestal first"},
                    {"response_num": 50, "sender": "DM", "content": "The mage deciphers a ritual that can safely remove the crystal"},
                    {"response_num": 51, "sender": "You", "content": "I perform the ritual carefully and claim the crystal"}
                ]
            },
            "branch_combat_route": {
                "title": "Fight the Guards",
                "active": False,
                "parent": "branch_temple_rush",
                "branch_point": 48,
                "tags": ["combat", "aggressive"],
                "in_game_datetime": "Day 16, Just Past Midnight - The Harvest Moon",
                "entry_count": 3,
                "description": "Steel clashes against stone as the party engages the temple's animated guardians. The battle is fierce and costly.",
                "messages": [
                    {"response_num": 49, "sender": "You", "content": "The guards appear! I draw my sword!"},
                    {"response_num": 50, "sender": "DM", "content": "Steel clashes as battle erupts in the chamber!"},
                    {"response_num": 51, "sender": "You", "content": "I fight with everything I have!"}
                ]
            },
            "alternate_start": {
                "title": "Alternate Beginning",
                "active": False,
                "parent": None,
                "branch_point": None,
                "tags": ["what-if", "experimental"],
                "in_game_datetime": "Day 12, Morning - The Harvest Moon",
                "entry_count": 15,
                "description": "What if the heroes had taken the northern mountain route instead of the forest path? This timeline explores that alternate beginning to their journey.",
                "messages": [
                    {"response_num": 13, "sender": "You", "content": "I suggest we take the northern mountain route"},
                    {"response_num": 14, "sender": "DM", "content": "The mountain path is treacherous but faster"},
                    {"response_num": 15, "sender": "You", "content": "We begin our ascent into the mountains"}
                ]
            },
            "branch_northern_path": {
                "title": "Mountain Pass",
                "active": False,
                "parent": "alternate_start",
                "branch_point": 15,
                "tags": ["environmental"],
                "in_game_datetime": "Day 13, Afternoon - The Harvest Moon",
                "entry_count": 6,
                "description": "The cold mountain air bites at their skin as they climb higher. Snow begins to fall, and they spot tracks in the ice that weren't there moments ago.",
                "messages": [
                    {"response_num": 16, "sender": "You", "content": "The air grows colder as we climb higher"},
                    {"response_num": 17, "sender": "DM", "content": "Snow begins to fall, and you spot strange tracks in the ice"},
                    {"response_num": 18, "sender": "You", "content": "I investigate the tracks carefully"}
                ]
            }
        }
        self.current_timeline = "branch_temple_explore"
        self.refresh_display()

    def refresh_display(self) -> None:
        """Refresh the tree and details display."""
        # Populate tree widget
        self.populate_tree()

        # Update details for active branch
        active_branch = self._get_active_branch()
        if active_branch:
            branch_id, branch = active_branch
            self.current_branch_id = branch_id
            self._update_branch_details(branch_id, branch)
            self._update_timeline_position(branch_id, branch)
            self._update_message_preview(branch_id, branch)

    def populate_tree(self) -> None:
        """Build interactive tree from branch data."""
        self.branch_tree.clear()

        # Find root branches (no parent)
        roots = [(bid, b) for bid, b in self.branches.items() if b.get("parent") is None]

        # Add root branches
        for branch_id, branch in roots:
            title = branch.get("title", branch_id)
            entry_count = branch.get("entry_count", 0)
            active_marker = " ●" if branch.get("active") else ""

            node = self.branch_tree.root.add(
                f"[bold]{title}[/] ({entry_count}){active_marker}",
                data={"id": branch_id, "branch": branch},
                expand=True
            )
            self._add_children(node, branch_id)

    def _add_children(self, parent_node, parent_id: str) -> None:
        """Recursively add child branches to tree."""
        children = [
            (bid, b) for bid, b in self.branches.items()
            if b.get("parent") == parent_id
        ]

        for child_id, child in children:
            title = child.get("title", child_id)
            entry_count = child.get("entry_count", 0)
            active_marker = " ●" if child.get("active") else ""

            child_node = parent_node.add(
                f"{title} ({entry_count}){active_marker}",
                data={"id": child_id, "branch": child},
                expand=True
            )
            self._add_children(child_node, child_id)

    def _get_active_branch(self):
        """Get the currently active branch."""
        for branch_id, branch in self.branches.items():
            if branch.get("active"):
                return (branch_id, branch)
        return None

    def _update_branch_details(self, branch_id: str, branch: dict) -> None:
        """Update the branch details panel."""
        details_widget = self.query_one("#branch-details", Static)

        # Safely access fields with defaults
        title = branch.get('title', branch_id)
        tags = branch.get('tags', [])
        tags_str = ', '.join(tags) if tags else 'None'

        parent = branch.get('parent', 'None')
        in_game_datetime = branch.get('in_game_datetime', 'Unknown')
        entry_count = branch.get('entry_count', 0)
        description = branch.get('description', 'No description available')

        details = f"""[bold]Current Branch: {title}[/bold]

[dim]Branch ID:[/dim] {branch_id}

[dim]Tags:[/dim] {tags_str}

[dim]Parent:[/dim] {parent}

[dim]Entries:[/dim] {entry_count}

[dim]In-Game Date/Time:[/dim] {in_game_datetime}

[dim]Description:[/dim]
{description}
"""
        details_widget.update(details)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle branch selection in tree."""
        if not event.node.data:
            return

        branch_id = event.node.data["id"]
        branch = event.node.data["branch"]

        # Update details panels
        self._update_branch_details(branch_id, branch)
        self._update_timeline_position(branch_id, branch)
        self._update_message_preview(branch_id, branch)

        # Store current selection
        self.current_branch_id = branch_id

    def _update_timeline_position(self, branch_id: str, branch: dict) -> None:
        """Show visual timeline of branch divergence."""
        position_widget = self.query_one("#timeline-position", Static)

        parent_id = branch.get("parent")
        branch_point = branch.get("branch_point")

        if parent_id and branch_point is not None:
            # Show divergence point
            parent_title = self.branches.get(parent_id, {}).get("title", parent_id)
            entry_count = branch.get("entry_count", 0)

            timeline_text = f"""[bold]Timeline Position:[/bold]

[dim]{parent_title}[/dim]
  ├─ Entry 1-{branch_point} [dim](shared history)[/dim]
  │
  └─ [bold][Branch Point #{branch_point}][/bold]
      └─ [accent]{branch.get("title", branch_id)}[/accent] [bold]●[/bold]
         └─ Entry {branch_point + 1}-{entry_count}
"""
        else:
            # Root branch (main timeline)
            entry_count = branch.get("entry_count", 0)
            timeline_text = f"""[bold]Timeline Position:[/bold]

[accent]{branch.get("title", branch_id)}[/accent] [dim](Root Timeline)[/dim]
  └─ Entry 1-{entry_count} [bold]●[/bold]
"""

        position_widget.update(timeline_text)

    def _update_message_preview(self, branch_id: str, branch: dict) -> None:
        """Update message preview with last 3 messages."""
        preview_widget = self.query_one("#message-preview", Static)

        # Get messages from branch
        messages = branch.get("messages", [])

        if not messages:
            preview_widget.update("[dim]No messages in this branch[/dim]")
            return

        # Get last 3 messages
        preview_messages = messages[-3:] if len(messages) >= 3 else messages

        preview_lines = ["[bold]Preview (Last 3 entries):[/bold]\n"]
        for msg in preview_messages:
            sender = msg.get("sender", "You")
            content = msg.get("content", msg.get("user_message", ""))
            # Truncate long messages
            if len(content) > 60:
                content = content[:60] + "..."
            preview_lines.append(f"[dim]#{msg.get('response_num', '?')}[/dim] [bold]{sender}:[/bold] {content}")

        preview_widget.update("\n".join(preview_lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action button presses."""
        button_id = event.button.id

        if button_id == "switch-branch-btn":
            self.post_message(self.BranchAction("switch", self.current_branch_id))
            # TODO: Show branch selection dialog
            self.app.notify("Branch switching coming soon", severity="information")

        elif button_id == "create-branch-btn":
            self.post_message(self.BranchAction("create"))
            # TODO: Show branch creation dialog
            self.app.notify("Branch creation coming soon", severity="information")

        elif button_id == "compare-branch-btn":
            self.post_message(self.BranchAction("compare", self.current_branch_id))
            # TODO: Show branch comparison view
            self.app.notify("Branch comparison coming soon", severity="information")

    def switch_branch(self, branch_id: str) -> None:
        """Switch to a different branch via SessionService."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.SWITCH_BRANCH,
                timeout=5.0,
                timeline_id=branch_id
            )

            if response.success:
                message = response.data.get("message", f"Switched to {branch_id}")
                self.app.notify(message, severity="information")
                self.load_branches()  # Reload to show updated active branch
            else:
                self.app.notify(f"Failed to switch branch: {response.error_message}", severity="error")

        except Exception as e:
            self.app.notify(f"Error switching branch: {e}", severity="error")

    def create_branch(self, name: str, parent_id: str) -> None:
        """Create a new branch via SessionService."""
        if not self.app.ipc_client or not self.app.connected:
            self.app.notify("Not connected to Bridge", severity="warning")
            return

        try:
            response = self.app.ipc_client.send_request(
                IPCMessageType.CREATE_BRANCH,
                timeout=5.0,
                name=name,
                parent_id=parent_id
            )

            if response.success:
                message = response.data.get("message", f"Created branch: {name}")
                self.app.notify(message, severity="information")
                self.load_branches()  # Reload to show new branch
            else:
                self.app.notify(f"Failed to create branch: {response.error_message}", severity="error")

        except Exception as e:
            self.app.notify(f"Error creating branch: {e}", severity="error")


__all__ = ["BranchesPage"]
