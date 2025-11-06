# Integration Quick Reference

Quick reference guide for integrating trigger and template editors into the main TUI.

---

## File Locations

```
Mockups:
  - src/presentation/tui/components/trigger_editor_enhanced_mockup.py
  - src/presentation/tui/components/template_editor_mockup.py

Main TUI:
  - src/presentation/tui/app.py
  - src/presentation/tui/components/*.py

IPC System:
  - src/infrastructure/ipc/ipc_protocol.py
  - src/infrastructure/ipc/socket_client.py
  - src/infrastructure/ipc/socket_server.py

Bridge:
  - src/application/bridge_service.py

Tests:
  - tests/ (60/60 passing)
```

---

## Component Extraction Checklist

### From Mockup → Integrated Component

1. **Copy mockup file to new name**
   ```bash
   cp trigger_editor_enhanced_mockup.py trigger_editor.py
   ```

2. **Remove sample data constants**
   ```python
   # Remove these
   SAMPLE_CHARACTERS = {...}
   SAMPLE_TEMPLATES = {...}
   ```

3. **Add IPC data loading**
   ```python
   async def on_mount(self):
       await self.load_data_from_bridge()

   async def load_data_from_bridge(self):
       request = IPCRequest.create(
           IPCMessageType.GET_TRIGGERS,
           str(uuid.uuid4()),
           character_id=self.character_id
       )
       response = await self.app.ipc_client.send_request(request)
       # Handle response...
   ```

4. **Remove standalone app code**
   ```python
   # Remove App class at bottom
   class EditorApp(App):  # DELETE THIS
       ...

   # Remove main() function
   def main():  # DELETE THIS
       ...
   ```

5. **Update imports**
   ```python
   # Add IPC imports
   from ...infrastructure.ipc import IPCMessageType, IPCRequest
   import uuid
   ```

---

## IPC Message Quick Reference

### Send Request from TUI

```python
from infrastructure.ipc import IPCMessageType, IPCRequest
import uuid

# Create request
request = IPCRequest.create(
    message_type=IPCMessageType.GET_TRIGGERS,
    request_id=str(uuid.uuid4()),
    character_id="emma"
)

# Send and await response
response = await self.app.ipc_client.send_request(request)

# Handle response
if response.type == IPCMessageType.RESPONSE.value:
    data = response.data
else:
    error = response.data.get("error")
```

### Common Message Types

```python
# Triggers
GET_TRIGGERS = "get_triggers"
SET_TRIGGER = "set_trigger"

# Templates
GET_TEMPLATES = "get_templates"
SET_TEMPLATE = "set_template"

# State
GET_STATE = "get_state"
SET_PROVIDER = "set_provider"
TEST_MODE = "test_mode"
```

### Add New Message Handler (Bridge Side)

```python
# 1. Add to IPCMessageType enum (ipc_protocol.py)
CREATE_TRIGGER = "create_trigger"

# 2. Add handler method (bridge_service.py)
async def handle_create_trigger(self, character_id: str, trigger_data: dict):
    # Validate
    # Save
    # Return response

# 3. Register handler (socket_server.py or bridge routing)
MESSAGE_HANDLERS[IPCMessageType.CREATE_TRIGGER] = bridge.handle_create_trigger
```

---

## Integration into Main TUI

### Add Component to App

```python
# src/presentation/tui/app.py

from .components import TriggerEditor, TemplateEditor

class RPClientApp(App):

    BINDINGS = [
        ("f3", "toggle_trigger_editor", "Triggers"),
        ("f4", "toggle_template_editor", "Templates"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        # ... existing layout ...

        # Add editors (hidden by default)
        yield TriggerEditor(classes="editor-overlay hidden")
        yield TemplateEditor(classes="editor-overlay hidden")

        yield Footer()

    def action_toggle_trigger_editor(self):
        editor = self.query_one(TriggerEditor)
        editor.toggle_class("hidden")

    def action_toggle_template_editor(self):
        editor = self.query_one(TemplateEditor)
        editor.toggle_class("hidden")
```

### CSS for Overlays

```css
.editor-overlay {
    layer: overlay;
    width: 90%;
    height: 85%;
    border: solid $primary;
    background: $surface;
    display: block;
}

.editor-overlay.hidden {
    display: none;
}
```

---

## Component Pattern Examples

### Three-Panel Grid Layout

```python
class EditorPanel(Container):
    def compose(self) -> ComposeResult:
        with Grid(classes="editor-grid"):
            yield LeftPanel()    # 1fr
            yield MiddlePanel()  # 1.5fr
            yield RightPanel()   # 1.5fr

# CSS
.editor-grid {
    layout: grid;
    grid-size: 3;
    grid-columns: 1fr 1.5fr 1.5fr;
}
```

### Horizontal Scrolling List

```python
class HorizontalList(Container):
    def compose(self) -> ComposeResult:
        with Horizontal(classes="scroll-container"):
            for item in self.items:
                yield Button(item, classes="scroll-item")

# CSS
.scroll-container {
    layout: horizontal;
    overflow-x: auto;
    overflow-y: hidden;
}

.scroll-item {
    min-width: 10;
    margin: 0 1;
}
```

### Message Communication

```python
class ItemList(Container):
    class ItemSelected(Message):
        def __init__(self, item_id: str):
            super().__init__()
            self.item_id = item_id

    def on_button_pressed(self, event):
        self.post_message(self.ItemSelected(event.button.id))

class ParentPanel(Container):
    def on_item_list_item_selected(self, message: ItemList.ItemSelected):
        # Auto-routed by Textual (snake_case of class name)
        self.load_item(message.item_id)
```

### Reactive State

```python
class Editor(Container):
    selected_id = reactive(None)

    def watch_selected_id(self, old, new):
        """Called automatically when selected_id changes."""
        if new:
            self.load_data(new)
```

---

## Testing Quick Guide

### Run All Tests

```bash
cd refactoring
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_trigger_editor.py -v
```

### Manual Testing

```bash
# Terminal 1: Start bridge
python -m src.application.bridge_service --test-mode

# Terminal 2: Start TUI
python -m src.presentation.tui.app

# Terminal 3: Run tests
pytest tests/ -v
```

### Test with Textual Dev Console

```bash
# Terminal 1: Console
textual console

# Terminal 2: App with dev mode
textual run --dev src/presentation/tui/app.py
```

---

## Common Patterns

### Load Data on Mount

```python
async def on_mount(self):
    """Load data when component is mounted."""
    await self.load_data()

async def load_data(self):
    """Load data from bridge via IPC."""
    try:
        response = await self.app.ipc_client.send_request(...)
        if response.type == IPCMessageType.RESPONSE.value:
            self.data = response.data
        else:
            self.notify(f"Error: {response.data['error']}", severity="error")
    except Exception as e:
        self.log.error(f"Failed to load data: {e}")
        self.notify(f"Failed to load data: {e}", severity="error")
```

### Save Data

```python
async def save_data(self, data: dict):
    """Save data to bridge via IPC."""
    request = IPCRequest.create(
        IPCMessageType.SET_TRIGGER,
        str(uuid.uuid4()),
        **data
    )

    response = await self.app.ipc_client.send_request(request)

    if response.type == IPCMessageType.RESPONSE.value:
        self.notify("Saved successfully", severity="information")
        return True
    else:
        self.notify(f"Save failed: {response.data.get('error')}", severity="error")
        return False
```

### Handle Button Click

```python
def on_button_pressed(self, event: Button.Pressed):
    """Handle button clicks."""
    if event.button.id == "save-btn":
        self.save()
    elif event.button.id == "cancel-btn":
        self.cancel()
    elif event.button.id.startswith("item-"):
        item_id = event.button.id.replace("item-", "")
        self.select_item(item_id)
```

---

## Color Palette

```python
PALETTE = {
    'primary': '#7c3aed',      # Violet
    'secondary': '#06b6d4',    # Cyan
    'accent': '#f59e0b',       # Amber
    'surface': '#1a1a2e',      # Dark blue-grey
    'panel': '#16213e',        # Panel background
    'border': '#4a5568',       # Grey border
    'text': '#e2e8f0',         # Light text
    'text-muted': '#94a3b8',   # Muted text
    'success': '#10b981',      # Green
    'error': '#ef4444',        # Red
}
```

Use in CSS:
```css
.my-component {
    background: $surface;
    border: solid $primary;
    color: $text;
}
```

---

## Debugging

### Add Logging

```python
def on_mount(self):
    self.log("Component mounted")
    self.log.debug(f"Data: {self.data}")
    self.log.error(f"Error: {error}")
```

### Check IPC Connection

```python
# In app
if not self.ipc_client.is_connected():
    self.notify("Not connected to bridge", severity="error")
```

### Inspect Component Tree

```python
# In Textual console
>>> app.query("TriggerEditor")
>>> app.query_one("#trigger-list")
```

---

## Key Component Methods

### Lifecycle

```python
def compose(self) -> ComposeResult:
    """Build initial UI structure."""
    yield Widget()

def on_mount(self):
    """Called when component is added to DOM."""
    pass

def on_unmount(self):
    """Called when component is removed from DOM."""
    pass
```

### Event Handlers

```python
def on_button_pressed(self, event: Button.Pressed):
    """Handle button clicks."""
    pass

def on_input_changed(self, event: Input.Changed):
    """Handle input changes."""
    pass

def on_option_list_option_selected(self, event: OptionList.OptionSelected):
    """Handle option selection."""
    pass
```

### Queries

```python
# Get one widget
widget = self.query_one("#widget-id", WidgetType)

# Get all widgets
widgets = self.query(".widget-class")

# Get typed widgets
buttons = self.query(Button)
```

---

## Run Scripts

```bash
# Run trigger editor mockup
python scripts/run_trigger_editor_enhanced.py

# Run template editor mockup
python scripts/run_template_editor.py

# Run main TUI app
python -m src.presentation.tui.app

# Run bridge service
python -m src.application.bridge_service

# Run tests
pytest tests/ -v
```

---

## Quick Links

- Full Guide: `docs/TUI_INTEGRATION_GUIDE.md`
- Textual Docs: https://textual.textualize.io/
- IPC Protocol: `src/infrastructure/ipc/ipc_protocol.py`
- Main App: `src/presentation/tui/app.py`
