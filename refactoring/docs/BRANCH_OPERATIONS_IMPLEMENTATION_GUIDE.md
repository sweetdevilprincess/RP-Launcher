# Branch Operations Implementation Guide

**Status:** Partially Implemented
**Priority:** Medium
**Estimated Effort:** ~250-350 lines of code

---

## Current State

### What Works ✅
- **GET_BRANCHES** - Loads all branches from session state
- **SWITCH_BRANCH** - Switches to a different timeline
- **Branch visualization** - ASCII tree display in TUI
- **Branch preview** - Shows first 100 chars from last entry

### What's Missing ❌
- **CREATE_BRANCH** - Returns "not yet implemented"
- **COMPARE_BRANCHES** - Returns "not yet implemented"
- UI for branch creation
- UI for branch comparison

---

## Branch System Overview

### Session State Structure

Branches (called "timelines") are stored in `state/session.json`:

```json
{
  "current_timeline": "main",
  "timelines": {
    "main": {
      "title": "Main Timeline",
      "tags": ["primary"],
      "parent": null,
      "created_at": "2025-10-20T10:00:00",
      "entries": [
        {
          "user_message": "Hello, how are you?",
          "llm_response": "I'm doing well, thanks!",
          "timestamp": "2025-10-20T10:01:00",
          "message_index": 0
        },
        {
          "user_message": "Tell me about the forest.",
          "llm_response": "The forest is dark and mysterious...",
          "timestamp": "2025-10-20T10:05:00",
          "message_index": 1
        }
      ]
    },
    "alternate_ending": {
      "title": "Alternate Ending",
      "tags": ["branch", "experiment"],
      "parent": "main",
      "branch_point": 1,
      "created_at": "2025-10-20T10:10:00",
      "entries": [
        {
          "user_message": "What if we go to the cave instead?",
          "llm_response": "The cave entrance beckons...",
          "timestamp": "2025-10-20T10:11:00",
          "message_index": 2
        }
      ]
    }
  }
}
```

### Branch Point Concept

When you create a branch:
1. Choose a **branch point** - the message index where the timeline diverges
2. New branch inherits all entries up to that point
3. New entries go into the new branch only

**Example:**
```
Main Timeline:
  [0] User: Hello
  [1] AI: Hi!
  [2] User: Let's go north
  [3] AI: You head north...

Branch from point [2]:
  [0] User: Hello         (inherited from main)
  [1] AI: Hi!             (inherited from main)
  [2] User: Let's go south   (NEW - diverges here)
  [3] AI: You head south...  (NEW)
```

---

## Implementation Plan

### Phase 1: Implement CREATE_BRANCH in BranchHandler

**File:** `src/presentation/bridge/handlers/branch_handler.py`

```python
def _handle_create_branch(self, request: IPCRequest) -> str:
    """Handle CREATE_BRANCH request - create new timeline branch.

    Request data:
        branch_name: Name for the new branch
        branch_point: Message index where branch diverges (optional, defaults to current position)
        parent_timeline: Parent timeline ID (optional, defaults to current timeline)
        tags: List of tags for the branch (optional)

    Returns:
        Response with new branch_id
    """
    branch_name = request.data.get("branch_name")
    if not branch_name:
        return create_error_response(request.request_id, "Missing branch_name")

    # Get optional parameters
    branch_point = request.data.get("branch_point")  # None = branch from current position
    parent_timeline = request.data.get("parent_timeline")  # None = current timeline
    tags = request.data.get("tags", ["branch"])

    try:
        # Load current session state
        session_state = self.bridge.session_state_service.load_session_state(self.bridge.rp_dir)

        if not session_state:
            return create_error_response(
                request.request_id,
                "No session state found. Start a conversation first."
            )

        # Determine parent timeline
        current_timeline = session_state.get("current_timeline", "main")
        parent = parent_timeline or current_timeline

        # Validate parent exists
        timelines = session_state.get("timelines", {})
        if parent not in timelines:
            return create_error_response(
                request.request_id,
                f"Parent timeline '{parent}' not found"
            )

        # Get parent timeline data
        parent_data = timelines[parent]
        parent_entries = parent_data.get("entries", [])

        # Determine branch point
        if branch_point is None:
            # Branch from end of parent timeline
            branch_point = len(parent_entries) - 1
        elif branch_point < 0 or branch_point >= len(parent_entries):
            return create_error_response(
                request.request_id,
                f"Invalid branch point: {branch_point}. Must be 0-{len(parent_entries)-1}"
            )

        # Generate branch ID from name
        branch_id = branch_name.lower().replace(' ', '_')

        # Check if branch already exists
        if branch_id in timelines:
            return create_error_response(
                request.request_id,
                f"Branch '{branch_id}' already exists"
            )

        # Copy entries up to branch point
        import copy
        inherited_entries = copy.deepcopy(parent_entries[:branch_point + 1])

        # Create new timeline
        from datetime import datetime
        new_timeline = {
            "title": branch_name,
            "tags": tags,
            "parent": parent,
            "branch_point": branch_point,
            "created_at": datetime.now().isoformat(),
            "entries": inherited_entries
        }

        # Add to session state
        timelines[branch_id] = new_timeline
        session_state["timelines"] = timelines

        # Optionally switch to new branch
        auto_switch = request.data.get("auto_switch", True)
        if auto_switch:
            session_state["current_timeline"] = branch_id

        # Save session state
        self.bridge.session_state_service.save_session_state(
            self.bridge.rp_dir,
            session_state
        )

        return create_response(
            request.request_id,
            branch_id=branch_id,
            branch_name=branch_name,
            parent=parent,
            branch_point=branch_point,
            entry_count=len(inherited_entries),
            switched=auto_switch,
            message=f"Created branch '{branch_name}' from {parent}[{branch_point}]"
        )

    except Exception as e:
        import traceback
        return create_error_response(
            request.request_id,
            f"Failed to create branch: {str(e)}\n{traceback.format_exc()}"
        )
```

**Estimated:** ~100 lines

---

### Phase 2: Implement COMPARE_BRANCHES in BranchHandler

```python
def _handle_compare_branches(self, request: IPCRequest) -> str:
    """Handle COMPARE_BRANCHES request - compare two timelines.

    Request data:
        branch_a: First branch ID
        branch_b: Second branch ID
        comparison_type: "entries" | "metadata" | "full" (default: "entries")

    Returns:
        Response with comparison data
    """
    branch_a = request.data.get("branch_a")
    branch_b = request.data.get("branch_b")

    if not branch_a or not branch_b:
        return create_error_response(
            request.request_id,
            "Missing branch_a or branch_b"
        )

    comparison_type = request.data.get("comparison_type", "entries")

    try:
        # Load session state
        session_state = self.bridge.session_state_service.load_session_state(self.bridge.rp_dir)
        timelines = session_state.get("timelines", {})

        # Validate branches exist
        if branch_a not in timelines:
            return create_error_response(request.request_id, f"Branch '{branch_a}' not found")
        if branch_b not in timelines:
            return create_error_response(request.request_id, f"Branch '{branch_b}' not found")

        timeline_a = timelines[branch_a]
        timeline_b = timelines[branch_b]

        # Find common ancestor and divergence point
        divergence_info = self._find_divergence_point(timeline_a, timeline_b, timelines)

        # Compare entries
        entries_a = timeline_a.get("entries", [])
        entries_b = timeline_b.get("entries", [])

        comparison = {
            "branch_a": {
                "id": branch_a,
                "title": timeline_a.get("title", branch_a),
                "entry_count": len(entries_a),
                "created": timeline_a.get("created_at"),
                "tags": timeline_a.get("tags", []),
            },
            "branch_b": {
                "id": branch_b,
                "title": timeline_b.get("title", branch_b),
                "entry_count": len(entries_b),
                "created": timeline_b.get("created_at"),
                "tags": timeline_b.get("tags", []),
            },
            "divergence": divergence_info,
            "comparison": self._compare_entries(entries_a, entries_b, divergence_info)
        }

        return create_response(
            request.request_id,
            comparison=comparison
        )

    except Exception as e:
        return create_error_response(
            request.request_id,
            f"Failed to compare branches: {str(e)}"
        )

def _find_divergence_point(self, timeline_a: dict, timeline_b: dict, all_timelines: dict) -> dict:
    """Find where two timelines diverged.

    Returns:
        {
            "common_ancestor": "main",
            "divergence_point": 5,
            "shared_entries": 5
        }
    """
    # Simple case: one is parent of the other
    if timeline_a.get("parent") == timeline_b.get("parent"):
        # Same parent, compare branch points
        return {
            "common_ancestor": timeline_a.get("parent"),
            "divergence_point": min(
                timeline_a.get("branch_point", 0),
                timeline_b.get("branch_point", 0)
            ),
            "relationship": "siblings"
        }

    # One is parent of the other
    # (For simplicity, we'll just count shared entries)
    entries_a = timeline_a.get("entries", [])
    entries_b = timeline_b.get("entries", [])

    shared_count = 0
    for i in range(min(len(entries_a), len(entries_b))):
        # Compare message content (simple heuristic)
        msg_a = entries_a[i].get("user_message", "")
        msg_b = entries_b[i].get("user_message", "")
        if msg_a == msg_b:
            shared_count += 1
        else:
            break

    return {
        "common_ancestor": "unknown",
        "divergence_point": shared_count,
        "shared_entries": shared_count,
        "relationship": "related" if shared_count > 0 else "unrelated"
    }

def _compare_entries(self, entries_a: list, entries_b: list, divergence_info: dict) -> dict:
    """Compare entry lists.

    Returns:
        {
            "shared": [...],
            "unique_to_a": [...],
            "unique_to_b": [...],
            "summary": "Branch A has 3 unique entries, Branch B has 5 unique entries"
        }
    """
    divergence_point = divergence_info.get("divergence_point", 0)

    shared = entries_a[:divergence_point]
    unique_a = entries_a[divergence_point:]
    unique_b = entries_b[divergence_point:]

    return {
        "shared_count": len(shared),
        "unique_to_a_count": len(unique_a),
        "unique_to_b_count": len(unique_b),
        "unique_to_a": [
            {
                "index": divergence_point + i,
                "user_message": entry.get("user_message", "")[:100],
                "timestamp": entry.get("timestamp")
            }
            for i, entry in enumerate(unique_a)
        ],
        "unique_to_b": [
            {
                "index": divergence_point + i,
                "user_message": entry.get("user_message", "")[:100],
                "timestamp": entry.get("timestamp")
            }
            for i, entry in enumerate(unique_b)
        ],
        "summary": f"Shared: {len(shared)} entries. Unique to A: {len(unique_a)}, Unique to B: {len(unique_b)}"
    }
```

**Estimated:** ~150 lines

---

### Phase 3: Add save_session_state Method

**Check:** Does `SessionStateService` have a `save_session_state()` method?

**File to check:** `src/infrastructure/sessions/session_state_service.py`

**If it doesn't exist, add:**

```python
def save_session_state(self, rp_dir: Path, session_state: dict) -> None:
    """Save session state to file.

    Args:
        rp_dir: Root directory of the RP
        session_state: Session state dict to save

    Raises:
        IOError: If unable to write file
    """
    session_file = rp_dir / "state" / "session.json"

    # Ensure directory exists
    session_file.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    import json
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, indent=2, ensure_ascii=False)

    self.logger.info(f"Session state saved to {session_file}")
```

**Estimated:** ~20 lines

---

### Phase 4: Add Branch Creation UI to BranchesPage

**File:** `src/presentation/tui/components/branches_page.py`

Update the create button handler:

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle action button presses."""
    button_id = event.button.id

    if button_id == "switch-branch-btn":
        # Existing switch logic...
        pass

    elif button_id == "create-branch-btn":
        # Show branch creation dialog
        self.create_branch_dialog()

    elif button_id == "compare-branch-btn":
        # Show branch comparison view
        self.show_branch_comparison()

def create_branch_dialog(self) -> None:
    """Show dialog for creating a new branch."""
    from textual.screen import ModalScreen
    from textual.widgets import Input, Button, Label
    from textual.containers import Vertical, Horizontal

    class BranchCreationDialog(ModalScreen):
        """Modal dialog for branch creation."""

        def compose(self) -> ComposeResult:
            with Vertical(id="dialog-container"):
                yield Label("Create New Branch")

                yield Label("Branch Name:")
                yield Input(id="branch-name", placeholder="e.g., 'Alternate Path'")

                yield Label("Branch from:")
                yield Label("Current position in: " + self.app.current_branch_id)

                yield Label("Auto-switch to new branch:")
                yield Switch(value=True, id="auto-switch")

                with Horizontal():
                    yield Button("Create", id="create", variant="primary")
                    yield Button("Cancel", id="cancel")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "create":
                # Get input values
                branch_name = self.query_one("#branch-name", Input).value.strip()
                auto_switch = self.query_one("#auto-switch", Switch).value

                if not branch_name:
                    self.app.notify("Branch name required", severity="warning")
                    return

                # Call IPC to create branch
                self.create_branch(branch_name, auto_switch)
                self.dismiss()

            elif event.button.id == "cancel":
                self.dismiss()

        def create_branch(self, branch_name: str, auto_switch: bool) -> None:
            """Create branch via IPC."""
            if not self.app.ipc_client or not self.app.connected:
                self.app.notify("Not connected to Bridge", severity="warning")
                return

            try:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.CREATE_BRANCH,
                    timeout=5.0,
                    branch_name=branch_name,
                    auto_switch=auto_switch
                )

                if response.success:
                    message = response.data.get("message", "Branch created")
                    self.app.notify(message, severity="information")

                    # Reload branches
                    branches_page = self.app.query_one(BranchesPage)
                    branches_page.load_branches()
                else:
                    self.app.notify(
                        f"Failed to create branch: {response.error_message}",
                        severity="error"
                    )

            except Exception as e:
                self.app.notify(f"Error creating branch: {e}", severity="error")

    # Push the dialog screen
    self.app.push_screen(BranchCreationDialog())
```

**Estimated:** ~80 lines

---

### Phase 5: Add Branch Comparison UI

```python
def show_branch_comparison(self) -> None:
    """Show branch comparison view."""
    from textual.screen import Screen
    from textual.widgets import Static, Button, Select
    from textual.containers import Vertical, Horizontal, ScrollableContainer

    class BranchComparisonScreen(Screen):
        """Screen for comparing two branches."""

        def compose(self) -> ComposeResult:
            with Vertical():
                yield Static("Compare Branches", classes="page-title")

                with Horizontal():
                    with Vertical():
                        yield Label("Branch A:")
                        yield Select(
                            [(name, name) for name in self.app.branches.keys()],
                            id="branch-a"
                        )

                    with Vertical():
                        yield Label("Branch B:")
                        yield Select(
                            [(name, name) for name in self.app.branches.keys()],
                            id="branch-b"
                        )

                yield Button("Compare", id="compare-btn", variant="primary")

                with ScrollableContainer(id="comparison-results"):
                    yield Static("Select two branches to compare", id="results")

                yield Button("Close", id="close-btn")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "compare-btn":
                self.run_comparison()
            elif event.button.id == "close-btn":
                self.app.pop_screen()

        def run_comparison(self) -> None:
            """Run branch comparison via IPC."""
            branch_a = self.query_one("#branch-a", Select).value
            branch_b = self.query_one("#branch-b", Select).value

            if not branch_a or not branch_b:
                self.app.notify("Select both branches", severity="warning")
                return

            if not self.app.ipc_client or not self.app.connected:
                self.app.notify("Not connected to Bridge", severity="warning")
                return

            try:
                response = self.app.ipc_client.send_request(
                    IPCMessageType.COMPARE_BRANCHES,
                    timeout=5.0,
                    branch_a=branch_a,
                    branch_b=branch_b
                )

                if response.success:
                    comparison = response.data.get("comparison", {})
                    self.display_comparison(comparison)
                else:
                    self.app.notify(
                        f"Failed to compare: {response.error_message}",
                        severity="error"
                    )

            except Exception as e:
                self.app.notify(f"Error comparing branches: {e}", severity="error")

        def display_comparison(self, comparison: dict) -> None:
            """Display comparison results."""
            results_widget = self.query_one("#results", Static)

            branch_a = comparison.get("branch_a", {})
            branch_b = comparison.get("branch_b", {})
            comp_data = comparison.get("comparison", {})

            results = f"""# Comparison Results

## Branch A: {branch_a.get('title')}
- Entries: {branch_a.get('entry_count')}
- Created: {branch_a.get('created')}
- Tags: {', '.join(branch_a.get('tags', []))}

## Branch B: {branch_b.get('title')}
- Entries: {branch_b.get('entry_count')}
- Created: {branch_b.get('created')}
- Tags: {', '.join(branch_b.get('tags', []))}

## Differences
{comp_data.get('summary', 'No differences found')}

### Unique to Branch A ({comp_data.get('unique_to_a_count', 0)} entries)
"""
            for entry in comp_data.get('unique_to_a', [])[:5]:  # Show first 5
                results += f"\n[{entry['index']}] {entry['user_message']}"

            results += f"\n\n### Unique to Branch B ({comp_data.get('unique_to_b_count', 0)} entries)"
            for entry in comp_data.get('unique_to_b', [])[:5]:  # Show first 5
                results += f"\n[{entry['index']}] {entry['user_message']}"

            results_widget.update(results)

    # Push the comparison screen
    self.app.push_screen(BranchComparisonScreen())
```

**Estimated:** ~100 lines

---

## Implementation Checklist

### Step 1: Implement CREATE_BRANCH ✓
- [ ] Add `_handle_create_branch()` to BranchHandler (~100 lines)
- [ ] Check if `save_session_state()` exists in SessionStateService
- [ ] If not, implement it (~20 lines)
- [ ] Test branch creation via IPC

### Step 2: Implement COMPARE_BRANCHES ✓
- [ ] Add `_handle_compare_branches()` to BranchHandler (~100 lines)
- [ ] Add helper methods: `_find_divergence_point()`, `_compare_entries()` (~50 lines)
- [ ] Test comparison via IPC

### Step 3: Add TUI for Branch Creation ✓
- [ ] Add `create_branch_dialog()` to BranchesPage (~80 lines)
- [ ] Add modal dialog UI
- [ ] Wire up to CREATE_BRANCH IPC call
- [ ] Test in TUI

### Step 4: Add TUI for Branch Comparison ✓
- [ ] Add `show_branch_comparison()` to BranchesPage (~100 lines)
- [ ] Add comparison screen UI
- [ ] Wire up to COMPARE_BRANCHES IPC call
- [ ] Test in TUI

### Step 5: Testing ✓
- [ ] Test creating branch from current position
- [ ] Test creating branch from specific point
- [ ] Test auto-switch functionality
- [ ] Test comparing sibling branches
- [ ] Test comparing unrelated branches
- [ ] Verify session.json is updated correctly

---

## Error Handling Requirements

### Validation
- **Branch name required:** Cannot create unnamed branch
- **Unique names:** Branch IDs must be unique
- **Valid branch point:** Must be within parent timeline range
- **Parent exists:** Parent timeline must exist

### State Management
- **Session state exists:** Cannot create branch without session
- **File I/O:** Handle errors writing to session.json
- **Concurrent access:** Handle multiple users/processes

### User Feedback
- **Success:** "Created branch 'Alternate Path' from main[5]"
- **Errors:** "Branch 'test' already exists"
- **Comparison:** Clear diff visualization

---

## Total Estimated Effort

**Handler Implementation:** ~250 lines
**TUI Implementation:** ~180 lines
**Testing:** ~2 hours

**Total:** ~430 lines of code, ~5-7 hours of work

---

## Advanced Features (Future)

### Branch Merging
- Merge entries from one branch into another
- Handle conflicts (different responses to same prompt)

### Branch Deletion
- Delete unused branches
- Cascade deletion (delete child branches)

### Branch Visualization
- Interactive tree view (click to switch)
- Timeline slider (scrub through history)
- Diff view (side-by-side comparison)

### Branch Metadata
- Add descriptions/notes to branches
- Track who created each branch
- Tag branches (experiment, canon, what-if)

---

**Related Document:** `ENTITY_CRUD_IMPLEMENTATION_GUIDE.md`
