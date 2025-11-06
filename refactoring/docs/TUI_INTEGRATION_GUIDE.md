# TUI Integration Guide

## Overview

This document provides comprehensive guidance for integrating the UI mockups into the main TUI application and connecting them to the Bridge service via socket IPC.

**Project**: RP Client TUI/Bridge Refactoring
**Workstream**: Workstream M (TUI/Bridge refactoring)
**Current Phase**: Phase 4 - Integration and Testing
**Last Updated**: 2025-10-21

---

## Table of Contents

1. [Project Background](#project-background)
2. [Current State](#current-state)
3. [Architecture Overview](#architecture-overview)
4. [Mockup Files Reference](#mockup-files-reference)
5. [Integration Tasks](#integration-tasks)
6. [IPC Communication Guide](#ipc-communication-guide)
7. [Testing Approach](#testing-approach)
8. [Design Patterns and Conventions](#design-patterns-and-conventions)
9. [Troubleshooting](#troubleshooting)

---

## Project Background

### Goals
The refactoring aims to:
- Separate concerns between TUI (presentation) and Bridge (business logic)
- Implement socket-based IPC for TUI-Bridge communication
- Create modular, maintainable TUI components
- Add testing mode with mock LLM client
- Enhance UI for triggers, templates, and settings

### Completed Phases

**Phase 1: Core Infrastructure** ✅
- Socket-based IPC system (server, client, protocol)
- Refactored Bridge service with dependency injection
- Mock LLM client for testing mode

**Phase 2: TUI Modular Architecture** ✅
- Split TUI into modular components
- Implemented core widgets (ChatDisplay, ContextPanel, RPTextArea, etc.)
- Updated TUI to use refactored services

**Phase 3: Enhanced UI Components** ✅
- Provider dropdown UI
- Enhanced trigger editor UI (horizontal scrolling)
- Template editor UI (three-panel layout)
- Testing mode toggle

**Phase 4: Integration and Testing** ⏳ (Current)
- Integrate mockups into main TUI
- Connect to Bridge via IPC
- End-to-end testing

**Phase 5: Documentation and Polish** 📋 (Pending)

---

## Current State

### Completed Components

#### Core TUI Components (Integrated)
Located in: `src/presentation/tui/components/`

- **AppHeader** (`app_header.py`) - Main header with title and status
- **ChatDisplay** (`chat_display.py`) - Center panel for chat messages
- **ContextPanel** (`context_panel.py`) - Sidebar for context/progress
- **ProviderSelector** (`provider_selector.py`) - LLM provider dropdown
- **RPTextArea** (`rp_textarea.py`) - Text input area with send button
- **TestingModeToggle** (`testing_mode_toggle.py`) - Toggle for test mode
- **CharacterEditor** (`character_editor.py`) - Character management UI

#### Mockup Components (Not Yet Integrated)
Located in: `src/presentation/tui/components/`

- **TriggerEditorEnhancedMockup** (`trigger_editor_enhanced_mockup.py`) - 698 lines
  - Three-panel layout with tabbed interface
  - Horizontal character selection grid
  - Horizontal scrolling trigger chips
  - Character sheet preview
  - Trigger form editor

- **TemplateEditorMockup** (`template_editor_mockup.py`) - 470+ lines
  - Three-panel layout
  - Category-based template organization
  - Variable support (`{{variable_name}}`)
  - Live markdown preview
  - Create/Edit/Delete operations

#### Runner Scripts
Located in: `scripts/`

- `run_trigger_editor_enhanced.py` - Run trigger editor mockup standalone
- `run_template_editor.py` - Run template editor mockup standalone
- `run_character_editor.py` - Run character editor

---

## Architecture Overview

### Directory Structure

```
refactoring/
├── src/
│   ├── application/
│   │   └── bridge_service.py         # Main bridge business logic
│   ├── domain/
│   │   ├── character.py               # Character entity
│   │   ├── llm_client.py              # LLM client interface
│   │   └── mock_llm_client.py         # Mock client for testing
│   ├── infrastructure/
│   │   └── ipc/
│   │       ├── ipc_protocol.py        # Message types and protocol
│   │       ├── ipc_channel.py         # Channel abstraction
│   │       ├── socket_server.py       # Bridge-side server
│   │       └── socket_client.py       # TUI-side client
│   └── presentation/
│       └── tui/
│           ├── app.py                 # Main TUI application
│           ├── components/            # Reusable widgets
│           └── styles.py              # Color palette and styles
├── tests/                             # 60/60 tests passing
└── scripts/                           # Runner scripts
```

### Component Hierarchy

```
RPClientApp (app.py)
├── AppHeader
├── Horizontal (main content)
│   ├── ContextPanel (sidebar)
│   │   ├── Static (character info)
│   │   ├── Static (progress)
│   │   └── ProviderSelector
│   │       └── TestingModeToggle
│   └── Vertical (center panel)
│       ├── ChatDisplay
│       └── RPTextArea
└── Footer
```

### IPC Architecture

```
┌─────────────────┐      Socket IPC      ┌─────────────────┐
│   TUI Client    │◄───────────────────►│  Bridge Server   │
│  (Presentation) │   JSON Messages      │ (Business Logic) │
└─────────────────┘                      └─────────────────┘
         │                                        │
         │                                        │
    SocketClient                            SocketServer
         │                                        │
         └────────── IPCMessage Protocol ────────┘
```

---

## Mockup Files Reference

### 1. Trigger Editor Enhanced Mockup

**File**: `src/presentation/tui/components/trigger_editor_enhanced_mockup.py`
**Lines**: 698
**Status**: Mockup complete, needs integration

#### Key Features
- **Three-panel grid layout**: Character grid | Sheet preview | Trigger editor
- **Horizontal character selection**: Emma | Marcus | Silas (buttons)
- **Horizontal scrolling triggers**: Chip-style buttons with `overflow-x: auto`
- **Tabbed interface**: Triggers, Settings, Templates tabs
- **Responsive sizing**: Uses `1fr`, `2fr`, `1.5fr` fractional units

#### Key Components

```python
class CharacterButton(Button):
    """Button for character selection with trigger count."""

class CharacterGrid(Container):
    """Horizontal grid of character buttons (2-column)."""

class TriggerList(Container):
    """Horizontal scrolling list of trigger chips."""

class CharacterSheetPreview(Container):
    """Markdown preview of character sheet for reference."""

class TriggerEditor(Container):
    """Form editor for creating/modifying triggers."""

class TriggerEditorPanel(Container):
    """Main panel combining all three sections."""
```

#### Sample Data Structure

```python
SAMPLE_CHARACTERS = {
    "Emma": {
        "full_name": "Emma Watson",
        "role": "Protagonist",
        "background": "...",
        "personality": "...",
        "triggers": [
            "Mention of magic",
            "Questions about identity",
            ...
        ]
    },
    ...
}
```

#### CSS Highlights

```css
.character-grid {
    layout: horizontal;  /* Side-by-side buttons */
    width: 100%;
    height: 100%;
}

.trigger-scroll {
    overflow-x: auto;    /* Horizontal scrolling */
    overflow-y: hidden;
}

.trigger-chip {
    height: 3;
    min-width: 10;
    margin: 0 1;
}
```

#### Runner Script
```bash
python scripts/run_trigger_editor_enhanced.py
```

---

### 2. Template Editor Mockup

**File**: `src/presentation/tui/components/template_editor_mockup.py`
**Lines**: 470+
**Status**: Mockup complete, needs integration

#### Key Features
- **Three-panel grid layout**: Template list | Preview | Editor
- **Category organization**: System, Story, Character, Scene, Dialogue
- **Variable support**: `{{variable_name}}` syntax
- **Live markdown preview**: Shows template content with metadata
- **Full CRUD operations**: Create, Read, Update, Delete templates

#### Key Components

```python
class TemplateButton(Button):
    """Button for template selection with category."""

class TemplateList(Container):
    """Category-organized list of templates."""

class TemplatePreview(Container):
    """Markdown preview with template metadata."""

class TemplateEditor(Container):
    """Form editor for template content and settings."""

class TemplateEditorPanel(Container):
    """Main panel combining all three sections."""
```

#### Sample Data Structure

```python
SAMPLE_TEMPLATES = {
    "System Prompt": {
        "category": "System",
        "content": "You are roleplaying as {{character_name}}...",
        "variables": ["character_name", "character_details"],
        "description": "Main system prompt for character roleplay"
    },
    ...
}
```

#### Key Messages

```python
class TemplateList:
    class TemplateSelected(Message):
        """Posted when a template is selected."""
        template_name: str
```

#### Runner Script
```bash
python scripts/run_template_editor.py
```

---

## Integration Tasks

### Task Checklist

#### 1. Integrate Trigger Editor into Main TUI

- [ ] **Extract reusable components from mockup**
  - [ ] Create `trigger_editor.py` from mockup
  - [ ] Remove sample data, add data loading from IPC
  - [ ] Update component names to match TUI conventions

- [ ] **Add to main TUI application**
  - [ ] Import TriggerEditor in `app.py`
  - [ ] Add trigger editor tab/overlay to main UI
  - [ ] Connect to app keybindings (e.g., F3 for triggers)

- [ ] **Connect to Bridge via IPC**
  - [ ] Add `get_triggers(character_id)` IPC call
  - [ ] Add `set_trigger(character_id, trigger_data)` IPC call
  - [ ] Add `delete_trigger(character_id, trigger_id)` IPC call
  - [ ] Handle streaming responses for trigger updates

- [ ] **Update character selection**
  - [ ] Load characters from Bridge (via `get_state`)
  - [ ] Sync with main character state
  - [ ] Handle character switching events

- [ ] **Add trigger CRUD operations**
  - [ ] Save trigger on form submit
  - [ ] Delete trigger with confirmation
  - [ ] Create new trigger
  - [ ] Validate trigger data before saving

#### 2. Integrate Template Editor into Main TUI

- [ ] **Extract reusable components from mockup**
  - [ ] Create `template_editor.py` from mockup
  - [ ] Remove sample data, add IPC data loading
  - [ ] Update component naming conventions

- [ ] **Add to main TUI application**
  - [ ] Import TemplateEditor in `app.py`
  - [ ] Add template editor tab/overlay
  - [ ] Connect to keybindings (e.g., F4 for templates)

- [ ] **Connect to Bridge via IPC**
  - [ ] Add `get_templates()` IPC call
  - [ ] Add `set_template(template_id)` IPC call
  - [ ] Add `create_template(template_data)` IPC call
  - [ ] Add `update_template(template_id, template_data)` IPC call
  - [ ] Add `delete_template(template_id)` IPC call

- [ ] **Add variable support**
  - [ ] Parse `{{variable_name}}` syntax
  - [ ] Show detected variables in preview
  - [ ] Validate variable references

- [ ] **Add import/export functionality**
  - [ ] Export templates to JSON
  - [ ] Import templates from JSON
  - [ ] Handle merge conflicts

#### 3. Update Bridge Service

- [ ] **Add trigger management endpoints**
  - [ ] `handle_get_triggers(character_id)`
  - [ ] `handle_set_trigger(character_id, trigger_data)`
  - [ ] `handle_delete_trigger(character_id, trigger_id)`

- [ ] **Add template management endpoints**
  - [ ] `handle_get_templates()`
  - [ ] `handle_create_template(template_data)`
  - [ ] `handle_update_template(template_id, template_data)`
  - [ ] `handle_delete_template(template_id)`
  - [ ] `handle_set_active_template(template_id)`

- [ ] **Add persistence**
  - [ ] Save triggers to character data
  - [ ] Save templates to template storage
  - [ ] Auto-save on changes

- [ ] **Add validation**
  - [ ] Validate trigger structure
  - [ ] Validate template syntax
  - [ ] Check for duplicate names

#### 4. Testing

- [ ] **Unit tests for new components**
  - [ ] Test TriggerEditor widget
  - [ ] Test TemplateEditor widget
  - [ ] Test message handling

- [ ] **Integration tests**
  - [ ] Test TUI-Bridge trigger sync
  - [ ] Test TUI-Bridge template sync
  - [ ] Test error handling

- [ ] **End-to-end tests**
  - [ ] Test full trigger creation workflow
  - [ ] Test full template creation workflow
  - [ ] Test character switching with triggers

- [ ] **Manual testing**
  - [ ] Test UI responsiveness
  - [ ] Test horizontal scrolling
  - [ ] Test tab navigation
  - [ ] Test keyboard shortcuts

---

## IPC Communication Guide

### Message Protocol

All IPC messages use JSON serialization with this structure:

```python
{
    "type": "message_type",       # IPCMessageType enum value
    "request_id": "unique-id",    # UUID for request/response matching
    "data": {                      # Message-specific payload
        "key": "value"
    }
}
```

### Available Message Types

Located in: `src/infrastructure/ipc/ipc_protocol.py`

```python
class IPCMessageType(Enum):
    # Client → Server (Requests)
    SEND_MESSAGE = "send_message"      # Send user message to LLM
    GET_STATE = "get_state"            # Get current session state
    GET_PROVIDERS = "get_providers"    # Get available LLM providers
    SET_PROVIDER = "set_provider"      # Switch LLM provider
    GET_TRIGGERS = "get_triggers"      # Get active triggers
    SET_TRIGGER = "set_trigger"        # Enable/disable trigger
    GET_TEMPLATES = "get_templates"    # Get available templates
    SET_TEMPLATE = "set_template"      # Switch narrative template
    TEST_MODE = "test_mode"            # Toggle testing mode
    PING = "ping"                       # Health check
    SHUTDOWN = "shutdown"               # Graceful shutdown

    # Server → Client (Responses)
    RESPONSE = "response"               # Generic successful response
    ERROR = "error"                     # Error response
    STREAMING_CHUNK = "streaming_chunk" # Streaming response chunk
    STREAMING_DONE = "streaming_done"   # Streaming complete
```

### Sending Requests from TUI

Example: Getting triggers for a character

```python
from infrastructure.ipc import IPCMessageType, IPCRequest, SocketClient
import uuid

# In your TUI component
async def load_triggers(self, character_id: str):
    """Load triggers for a character via IPC."""

    # Create request
    request = IPCRequest.create(
        message_type=IPCMessageType.GET_TRIGGERS,
        request_id=str(uuid.uuid4()),
        character_id=character_id
    )

    # Send via socket client (from app)
    response = await self.app.ipc_client.send_request(request)

    # Handle response
    if response.type == IPCMessageType.RESPONSE.value:
        triggers = response.data.get("triggers", [])
        self.display_triggers(triggers)
    else:
        self.show_error(response.data.get("error", "Unknown error"))
```

### Adding New Message Types

If you need additional message types for triggers/templates:

1. **Add to IPCMessageType enum** (`ipc_protocol.py`)
   ```python
   CREATE_TRIGGER = "create_trigger"
   UPDATE_TRIGGER = "update_trigger"
   DELETE_TRIGGER = "delete_trigger"
   ```

2. **Add handler in Bridge** (`bridge_service.py`)
   ```python
   async def handle_create_trigger(self, character_id: str, trigger_data: dict):
       """Handle trigger creation request."""
       # Validate data
       # Save to character
       # Return success response
   ```

3. **Register handler in IPC server** (`socket_server.py`)
   ```python
   MESSAGE_HANDLERS = {
       IPCMessageType.CREATE_TRIGGER: bridge.handle_create_trigger,
       ...
   }
   ```

### Request/Response Examples

#### Get Triggers

**Request:**
```json
{
    "type": "get_triggers",
    "request_id": "abc-123",
    "data": {
        "character_id": "emma"
    }
}
```

**Response:**
```json
{
    "type": "response",
    "request_id": "abc-123",
    "data": {
        "triggers": [
            {
                "id": "trigger-1",
                "name": "Mention of magic",
                "pattern": "magic|spell|wizard",
                "response_template": "Emma's eyes light up..."
            }
        ]
    }
}
```

#### Create Trigger

**Request:**
```json
{
    "type": "set_trigger",
    "request_id": "def-456",
    "data": {
        "character_id": "emma",
        "trigger": {
            "name": "Questions about identity",
            "pattern": "who are you|what's your name",
            "response_template": "Emma pauses thoughtfully..."
        }
    }
}
```

**Response:**
```json
{
    "type": "response",
    "request_id": "def-456",
    "data": {
        "success": true,
        "trigger_id": "trigger-2"
    }
}
```

#### Get Templates

**Request:**
```json
{
    "type": "get_templates",
    "request_id": "ghi-789",
    "data": {}
}
```

**Response:**
```json
{
    "type": "response",
    "request_id": "ghi-789",
    "data": {
        "templates": [
            {
                "id": "template-1",
                "name": "System Prompt",
                "category": "System",
                "content": "You are {{character_name}}...",
                "variables": ["character_name", "character_details"]
            }
        ]
    }
}
```

---

## Testing Approach

### Test Environment Setup

1. **Start Bridge in test mode:**
   ```bash
   cd refactoring
   python -m src.application.bridge_service --test-mode
   ```

2. **Start TUI client:**
   ```bash
   python -m src.presentation.tui.app
   ```

3. **Run test suite:**
   ```bash
   pytest tests/ -v
   ```

### Manual Testing Checklist

#### Trigger Editor
- [ ] Open trigger editor (F3 or tab)
- [ ] Select different characters
- [ ] Verify character sheet preview updates
- [ ] Scroll through triggers horizontally
- [ ] Click trigger to edit
- [ ] Modify trigger and save
- [ ] Create new trigger
- [ ] Delete existing trigger
- [ ] Verify triggers persist after character switch

#### Template Editor
- [ ] Open template editor (F4 or tab)
- [ ] Browse templates by category
- [ ] Select template and verify preview
- [ ] Edit template content
- [ ] Add/remove variables (`{{var}}`)
- [ ] Save template changes
- [ ] Create new template with category
- [ ] Delete template with confirmation
- [ ] Test import/export (if implemented)

#### Integration
- [ ] Switch between trigger and template editors
- [ ] Verify data persists when switching views
- [ ] Test with testing mode enabled
- [ ] Test with testing mode disabled (real LLM)
- [ ] Verify IPC connection status in header
- [ ] Test error handling (disconnect bridge)

### Automated Test Examples

```python
# tests/test_trigger_editor.py

import pytest
from src.presentation.tui.components.trigger_editor import TriggerEditor

@pytest.fixture
async def trigger_editor(mock_ipc_client):
    """Create trigger editor with mock IPC."""
    editor = TriggerEditor()
    editor.app = MockApp(ipc_client=mock_ipc_client)
    return editor

async def test_load_triggers(trigger_editor, mock_ipc_client):
    """Test loading triggers via IPC."""
    # Mock response
    mock_ipc_client.set_response({
        "type": "response",
        "request_id": "test-123",
        "data": {
            "triggers": [
                {"id": "1", "name": "Test Trigger"}
            ]
        }
    })

    # Load triggers
    await trigger_editor.load_triggers("emma")

    # Verify UI updated
    assert len(trigger_editor.trigger_buttons) == 1
    assert trigger_editor.trigger_buttons[0].label == "Test Trigger"
```

---

## Design Patterns and Conventions

### Component Design Patterns

#### 1. Three-Panel Layout Pattern
Used by both trigger and template editors:

```python
class EditorPanel(Container):
    """Main panel with three-column grid."""

    def compose(self) -> ComposeResult:
        with Grid(classes="editor-grid"):
            yield ListPanel(classes="list-panel")      # 1fr
            yield PreviewPanel(classes="preview-panel") # 1.5fr
            yield EditorPanel(classes="editor-panel")   # 1.5fr
```

**CSS:**
```css
.editor-grid {
    layout: grid;
    grid-size: 3;
    grid-columns: 1fr 1.5fr 1.5fr;
    height: 100%;
}
```

#### 2. Message-Based Communication
Components communicate via Textual messages:

```python
class ItemSelected(Message):
    """Posted when an item is selected."""

    def __init__(self, item_id: str):
        super().__init__()
        self.item_id = item_id

# Posting
self.post_message(self.ItemSelected("emma"))

# Handling
def on_list_panel_item_selected(self, message: ListPanel.ItemSelected):
    self.load_item(message.item_id)
```

#### 3. Reactive State Management
Use Textual's reactive properties:

```python
class Editor(Container):
    selected_item = reactive(None)

    def watch_selected_item(self, old_value, new_value):
        """Called when selected_item changes."""
        if new_value:
            self.load_item_data(new_value)
```

#### 4. Async IPC Pattern
All IPC calls should be async:

```python
async def save_data(self):
    """Save data via IPC."""
    try:
        response = await self.app.ipc_client.send_request(request)
        if response.type == IPCMessageType.RESPONSE.value:
            self.notify("Saved successfully", severity="information")
        else:
            self.notify(f"Error: {response.data['error']}", severity="error")
    except Exception as e:
        self.notify(f"Failed to save: {e}", severity="error")
```

### Naming Conventions

- **Components**: PascalCase (e.g., `TriggerEditor`, `TemplateList`)
- **Methods**: snake_case (e.g., `load_triggers`, `save_template`)
- **IDs**: kebab-case (e.g., `trigger-editor`, `template-list`)
- **CSS classes**: kebab-case (e.g., `editor-panel`, `trigger-chip`)
- **Files**: snake_case (e.g., `trigger_editor.py`)

### CSS Organization

```css
/* Component container */
.component-name {
    layout: grid;
    width: 100%;
}

/* Child elements */
.component-name .child-element {
    border: solid $primary;
}

/* State classes */
.component-name.active {
    background: $accent;
}

/* ID selectors for unique elements */
#unique-element-id {
    height: 10;
}
```

### Color Palette Reference

Located in: `src/presentation/tui/styles.py`

```python
PALETTE = {
    'primary': '#7c3aed',      # Violet
    'secondary': '#06b6d4',    # Cyan
    'accent': '#f59e0b',       # Amber
    'surface': '#1a1a2e',      # Dark blue-grey
    'panel': '#16213e',        # Slightly lighter
    'border': '#4a5568',       # Grey
    'text': '#e2e8f0',         # Light grey
    'text-muted': '#94a3b8',   # Muted grey
    'success': '#10b981',      # Green
    'error': '#ef4444',        # Red
}
```

---

## Troubleshooting

### Common Issues

#### Issue: Mockup won't import in main TUI
**Error**: `ImportError: attempted relative import beyond top-level package`

**Solution**: Mockups have sample data embedded. Extract components and remove sample data:
```python
# In mockup (has sample data)
SAMPLE_CHARACTERS = {...}

# In integrated component (loads from IPC)
async def on_mount(self):
    await self.load_characters_from_bridge()
```

#### Issue: Horizontal scrolling not working
**Error**: Triggers stack vertically instead of horizontally

**Solution**: Ensure using `Horizontal` container with correct CSS:
```css
.trigger-scroll {
    layout: horizontal;  /* Not vertical or grid */
    overflow-x: auto;
    overflow-y: hidden;  /* Important! */
}
```

#### Issue: IPC request times out
**Error**: `TimeoutError: Request abc-123 timed out`

**Solution**:
1. Check Bridge is running: `ps aux | grep bridge_service`
2. Verify socket connection in TUI header (should show "Connected")
3. Check Bridge logs for errors
4. Ensure message type is registered in handler

#### Issue: Grid layout not displaying correctly
**Error**: Panels overlapping or wrong sizes

**Solution**: Check grid configuration:
```python
# Correct
with Grid(classes="editor-grid"):
    # Grid should have matching CSS

# CSS
.editor-grid {
    layout: grid;
    grid-size: 3;              # Must match number of children
    grid-columns: 1fr 1.5fr 1.5fr;  # Must match grid-size
}
```

#### Issue: Messages not bubbling to parent
**Error**: Parent handler not receiving child messages

**Solution**: Ensure message is not stopped:
```python
# Wrong
def on_button_pressed(self, event):
    event.stop()  # Prevents bubbling!

# Right
def on_button_pressed(self, event):
    # Don't call event.stop() if parent needs it
    self.post_message(...)
```

### Debugging Tips

1. **Enable IPC logging:**
   ```python
   # In socket_client.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Use Textual's dev console:**
   ```bash
   textual console
   # In another terminal
   textual run --dev src/presentation/tui/app.py
   ```

3. **Add debug logs in components:**
   ```python
   def on_mount(self):
       self.log("Component mounted")
       self.log(f"Data: {self.data}")
   ```

4. **Test components standalone:**
   ```python
   # Create simple app to test component
   class TestApp(App):
       def compose(self):
           yield YourComponent()

   TestApp().run()
   ```

---

## Additional Resources

### Documentation
- Textual Guide: https://textual.textualize.io/guide/
- Textual Widgets: https://textual.textualize.io/widgets/
- Project README: `README.md`
- Bridge Service Docs: `src/application/README.md`

### Key Files to Reference
- IPC Protocol: `src/infrastructure/ipc/ipc_protocol.py`
- Bridge Service: `src/application/bridge_service.py`
- Main TUI App: `src/presentation/tui/app.py`
- Component Examples: `src/presentation/tui/components/`

### Contact
For questions or issues, check:
- GitHub Issues: (if applicable)
- Project documentation
- Code comments in source files

---

## Next Steps

1. **Start with Trigger Editor Integration**
   - Extract components from mockup
   - Add IPC data loading
   - Integrate into main TUI
   - Test thoroughly

2. **Then Template Editor Integration**
   - Follow same pattern as trigger editor
   - Add variable parsing
   - Test import/export

3. **End-to-End Testing**
   - Test full workflows
   - Verify data persistence
   - Check error handling

4. **Polish and Documentation**
   - Update user documentation
   - Add inline code comments
   - Create video demos (optional)

Good luck with the integration! 🚀
