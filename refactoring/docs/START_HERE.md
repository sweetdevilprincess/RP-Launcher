# TUI Integration - Start Here

Welcome to the TUI integration phase! This document will get you started quickly.

---

## What You're Working On

You'll be integrating two UI mockups into the main TUI application:
1. **Trigger Editor** - Manage character triggers
2. **Template Editor** - Manage narrative templates

Both mockups are **complete and tested** as standalone apps. Your job is to:
- Extract components from mockups
- Remove sample data
- Connect to Bridge via IPC
- Integrate into main TUI app
- Test the integration

---

## Quick Start (5 Minutes)

### 1. Explore the Mockups

Run both mockups to see what you'll be integrating:

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"

# Run trigger editor mockup
python scripts/run_trigger_editor_enhanced.py

# Run template editor mockup (in separate terminal)
python scripts/run_template_editor.py
```

**What to notice:**
- Trigger editor: 3-panel layout, horizontal character buttons, scrolling triggers
- Template editor: 3-panel layout, category organization, markdown preview

### 2. Review the Documentation

Read these docs in order:

1. **ARCHITECTURE_OVERVIEW.md** (10 min)
   - Understand system structure
   - See component hierarchy
   - Review data flow

2. **INTEGRATION_QUICK_REFERENCE.md** (15 min)
   - Code patterns you'll use
   - IPC examples
   - Common tasks

3. **TUI_INTEGRATION_GUIDE.md** (30 min)
   - Complete integration guide
   - Step-by-step tasks
   - Troubleshooting

### 3. Check Current State

```bash
# Verify tests are passing
pytest tests/ -v

# Expected: 60/60 tests passing ✓
```

### 4. Explore Existing Code

Look at these files to understand the codebase:

```bash
# Main TUI app
src/presentation/tui/app.py

# Existing integrated component (reference)
src/presentation/tui/components/character_editor.py

# IPC protocol
src/infrastructure/ipc/ipc_protocol.py

# Bridge service
src/application/bridge_service.py
```

---

## Your Task Overview

### Phase 4: Integration and Testing

**Goal**: Integrate trigger and template editors into main TUI and connect to Bridge.

**Estimated Time**: 6-8 hours

**Deliverables**:
- [ ] Working trigger editor in main TUI
- [ ] Working template editor in main TUI
- [ ] IPC integration for both editors
- [ ] Bridge handlers for trigger/template operations
- [ ] Tests for new components
- [ ] Manual testing completed

---

## Integration Roadmap

### Part 1: Trigger Editor (3-4 hours)

1. **Extract Components** (1 hour)
   - Copy `trigger_editor_enhanced_mockup.py` → `trigger_editor.py`
   - Remove `SAMPLE_CHARACTERS` data
   - Remove standalone `App` class
   - Remove `main()` function

2. **Add IPC Integration** (1 hour)
   - Add `load_characters()` method using IPC
   - Add `load_triggers(character_id)` method
   - Add `save_trigger()` method
   - Add `delete_trigger()` method

3. **Integrate into Main TUI** (1 hour)
   - Import `TriggerEditor` in `app.py`
   - Add overlay container
   - Add keybinding (F3)
   - Add toggle action

4. **Test** (30 min)
   - Manual testing with mockup data
   - Verify UI works in main app
   - Test keyboard shortcuts

### Part 2: Template Editor (2-3 hours)

1. **Extract Components** (30 min)
   - Copy `template_editor_mockup.py` → `template_editor.py`
   - Remove sample data
   - Remove standalone app code

2. **Add IPC Integration** (1 hour)
   - Add `load_templates()` method
   - Add `save_template()` method
   - Add `create_template()` method
   - Add `delete_template()` method

3. **Integrate into Main TUI** (30 min)
   - Import `TemplateEditor` in `app.py`
   - Add overlay container
   - Add keybinding (F4)
   - Add toggle action

4. **Test** (30 min)
   - Manual testing
   - Verify category organization
   - Test variable parsing

### Part 3: Bridge Integration (1-2 hours)

1. **Add Message Types** (15 min)
   - Add new message types to `IPCMessageType` enum
   - Document request/response formats

2. **Add Bridge Handlers** (1 hour)
   - Implement `handle_get_triggers()`
   - Implement `handle_set_trigger()`
   - Implement `handle_get_templates()`
   - Implement `handle_set_template()`
   - Implement `handle_create_template()`
   - Implement `handle_delete_template()`

3. **Add Persistence** (30 min)
   - Save triggers to character data
   - Save templates to storage
   - Add auto-save functionality

### Part 4: Testing (1 hour)

1. **Unit Tests**
   - Test component logic
   - Test message handling

2. **Integration Tests**
   - Test IPC communication
   - Test data persistence

3. **Manual E2E Tests**
   - Test full workflows
   - Verify error handling
   - Test with Bridge in test mode

---

## File Locations Reference

### Mockups (Source)
```
src/presentation/tui/components/
├── trigger_editor_enhanced_mockup.py    ← Extract from this
└── template_editor_mockup.py            ← Extract from this
```

### Integration Targets (Create These)
```
src/presentation/tui/components/
├── trigger_editor.py                    ← Create this
└── template_editor.py                   ← Create this
```

### Files to Modify
```
src/presentation/tui/app.py              ← Add editors here
src/infrastructure/ipc/ipc_protocol.py   ← Add message types
src/application/bridge_service.py        ← Add handlers
```

### Documentation
```
docs/
├── START_HERE.md                        ← You are here
├── ARCHITECTURE_OVERVIEW.md             ← Read first
├── INTEGRATION_QUICK_REFERENCE.md       ← Use while coding
└── TUI_INTEGRATION_GUIDE.md             ← Complete reference
```

---

## Code Templates

### Extract Component from Mockup

```python
# BEFORE (in mockup)
class TriggerEditorPanel(Container):
    def compose(self):
        # ... UI code ...

SAMPLE_CHARACTERS = {...}  # ← Remove this

class TriggerEditorApp(App):  # ← Remove entire class
    def compose(self):
        yield TriggerEditorPanel()

def main():  # ← Remove function
    TriggerEditorApp().run()

# AFTER (integrated component)
class TriggerEditor(Container):  # Rename to match convention
    def compose(self):
        # ... same UI code ...

    async def on_mount(self):
        """Load data from Bridge via IPC."""
        await self.load_characters()

    async def load_characters(self):
        """Load characters from Bridge."""
        request = IPCRequest.create(
            IPCMessageType.GET_STATE,
            str(uuid.uuid4())
        )
        response = await self.app.ipc_client.send_request(request)
        # Process response...
```

### Add to Main App

```python
# src/presentation/tui/app.py

from .components import (
    # ... existing imports ...
    TriggerEditor,
    TemplateEditor,
)

class RPClientApp(App):

    BINDINGS = [
        # ... existing bindings ...
        ("f3", "toggle_trigger_editor", "Triggers"),
        ("f4", "toggle_template_editor", "Templates"),
    ]

    def compose(self) -> ComposeResult:
        # ... existing layout ...

        # Add overlays
        yield TriggerEditor(id="trigger-editor", classes="overlay hidden")
        yield TemplateEditor(id="template-editor", classes="overlay hidden")

    def action_toggle_trigger_editor(self):
        editor = self.query_one("#trigger-editor")
        editor.toggle_class("hidden")
```

### IPC Request Example

```python
async def load_triggers(self, character_id: str):
    """Load triggers for a character."""
    try:
        request = IPCRequest.create(
            IPCMessageType.GET_TRIGGERS,
            str(uuid.uuid4()),
            character_id=character_id
        )

        response = await self.app.ipc_client.send_request(request)

        if response.type == IPCMessageType.RESPONSE.value:
            triggers = response.data.get("triggers", [])
            self.display_triggers(triggers)
        else:
            error = response.data.get("error", "Unknown error")
            self.notify(f"Failed to load triggers: {error}", severity="error")

    except Exception as e:
        self.log.error(f"Error loading triggers: {e}")
        self.notify(f"Error: {e}", severity="error")
```

---

## Testing Checklist

### Manual Testing

- [ ] Start Bridge in test mode
- [ ] Start TUI
- [ ] Press F3 to open trigger editor
- [ ] Select different characters
- [ ] View character sheet preview
- [ ] Scroll through triggers horizontally
- [ ] Edit a trigger and save
- [ ] Create new trigger
- [ ] Delete trigger
- [ ] Press F4 to open template editor
- [ ] Browse templates by category
- [ ] Select template and view preview
- [ ] Edit template content
- [ ] Save template changes
- [ ] Create new template
- [ ] Delete template
- [ ] Switch between editors (F3/F4)
- [ ] Verify data persists

### Automated Testing

- [ ] Run existing test suite: `pytest tests/ -v`
- [ ] Add tests for TriggerEditor component
- [ ] Add tests for TemplateEditor component
- [ ] Add IPC integration tests
- [ ] Verify 60+ tests passing

---

## Common Issues & Solutions

### Issue: Import errors when extracting mockup
**Solution**: Remove relative imports for sample data. Add IPC imports.

### Issue: UI looks different in main app vs mockup
**Solution**: Copy CSS from mockup to main app's CSS section.

### Issue: IPC timeout errors
**Solution**: Check Bridge is running. Verify message type is registered.

### Issue: Horizontal scrolling not working
**Solution**: Verify using `Horizontal` container and `overflow-x: auto` CSS.

### Issue: Messages not reaching parent component
**Solution**: Don't call `event.stop()` - let messages bubble.

---

## Getting Help

If you get stuck:

1. **Check the docs**
   - `INTEGRATION_QUICK_REFERENCE.md` - code snippets
   - `TUI_INTEGRATION_GUIDE.md` - detailed guide
   - `ARCHITECTURE_OVERVIEW.md` - system design

2. **Look at existing code**
   - `character_editor.py` - similar component
   - `provider_selector.py` - IPC example
   - `testing_mode_toggle.py` - simple component

3. **Use Textual dev tools**
   ```bash
   textual console  # Terminal 1
   textual run --dev src/presentation/tui/app.py  # Terminal 2
   ```

4. **Check test output**
   ```bash
   pytest tests/ -v
   ```

---

## Success Criteria

You'll know you're done when:

- [ ] Trigger editor opens with F3
- [ ] Template editor opens with F4
- [ ] Both editors load data from Bridge (not sample data)
- [ ] Users can create/edit/delete triggers
- [ ] Users can create/edit/delete templates
- [ ] All data persists after closing editors
- [ ] All tests pass (60+)
- [ ] No console errors
- [ ] UI is responsive and matches mockups

---

## Timeline Estimate

| Task | Time | Status |
|------|------|--------|
| Review docs & explore mockups | 1 hour | ⏸ |
| Extract & integrate trigger editor | 3-4 hours | ⏸ |
| Extract & integrate template editor | 2-3 hours | ⏸ |
| Add Bridge handlers & IPC | 1-2 hours | ⏸ |
| Testing & bug fixes | 1 hour | ⏸ |
| **Total** | **8-11 hours** | |

---

## Ready to Start?

1. ✅ Read this document
2. ✅ Run the mockups to see what you're building
3. ✅ Review `ARCHITECTURE_OVERVIEW.md`
4. ✅ Skim `INTEGRATION_QUICK_REFERENCE.md`
5. → Start with trigger editor integration

**First step**: Copy `trigger_editor_enhanced_mockup.py` to `trigger_editor.py` and start extracting components!

Good luck! 🚀

---

## Questions?

Refer to:
- **TUI_INTEGRATION_GUIDE.md** - Complete integration instructions
- **INTEGRATION_QUICK_REFERENCE.md** - Quick code snippets
- **ARCHITECTURE_OVERVIEW.md** - System architecture

All documentation is in: `refactoring/docs/`
