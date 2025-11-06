# Architecture Overview

Visual guide to the refactored RP Client architecture, component relationships, and data flow.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                        (Textual TUI)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User Actions
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TUI APPLICATION LAYER                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Main App   │  │   Trigger    │  │   Template   │          │
│  │  (app.py)    │  │   Editor     │  │    Editor    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                  │                   │
│         └─────────────────┴──────────────────┘                  │
│                           │                                      │
│                           │ IPC Requests                         │
│                           ▼                                      │
│                 ┌─────────────────┐                             │
│                 │  Socket Client  │                             │
│                 └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JSON over Socket
                              │ (localhost:5555)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
│                                                                  │
│                 ┌─────────────────┐                             │
│                 │  Socket Server  │                             │
│                 └─────────────────┘                             │
│                           │                                      │
│                           │ Route Messages                       │
│                           ▼                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Bridge Service                        │  │
│  │                                                           │  │
│  │  ├─ Character Management                                │  │
│  │  ├─ Trigger Management                                  │  │
│  │  ├─ Template Management                                 │  │
│  │  ├─ Session State                                       │  │
│  │  └─ Provider Management                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│           ┌────────────────────────────────┐                    │
│           │         LLM Client             │                    │
│           │  (Real / Mock for testing)     │                    │
│           └────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                          │
│                                                                  │
│        Claude API  │  OpenAI API  │  Local Models               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
refactoring/
│
├── src/
│   │
│   ├── presentation/          # TUI Layer (User Interface)
│   │   └── tui/
│   │       ├── app.py                    # Main TUI application
│   │       ├── styles.py                 # Color palette & styles
│   │       │
│   │       └── components/               # Reusable widgets
│   │           ├── app_header.py         # Header with status
│   │           ├── chat_display.py       # Chat message display
│   │           ├── context_panel.py      # Sidebar context
│   │           ├── provider_selector.py  # Provider dropdown
│   │           ├── rp_textarea.py        # Message input
│   │           ├── testing_mode_toggle.py # Test mode toggle
│   │           ├── character_editor.py   # Character management
│   │           │
│   │           # Mockups (to be integrated)
│   │           ├── trigger_editor_enhanced_mockup.py  ← INTEGRATE
│   │           └── template_editor_mockup.py          ← INTEGRATE
│   │
│   ├── application/           # Business Logic Layer
│   │   └── bridge_service.py            # Core bridge logic
│   │
│   ├── domain/                # Domain Models
│   │   ├── character.py                 # Character entity
│   │   ├── llm_client.py                # LLM client interface
│   │   └── mock_llm_client.py           # Mock for testing
│   │
│   └── infrastructure/        # Infrastructure Layer
│       └── ipc/                          # Inter-Process Communication
│           ├── ipc_protocol.py          # Message protocol
│           ├── ipc_channel.py           # Channel abstraction
│           ├── socket_server.py         # Server (Bridge side)
│           └── socket_client.py         # Client (TUI side)
│
├── tests/                     # Test Suite (60/60 passing)
│   ├── test_ipc.py
│   ├── test_bridge_service.py
│   ├── test_mock_llm.py
│   └── ...
│
├── scripts/                   # Utility Scripts
│   ├── run_trigger_editor_enhanced.py
│   ├── run_template_editor.py
│   └── ...
│
└── docs/                      # Documentation
    ├── TUI_INTEGRATION_GUIDE.md
    ├── INTEGRATION_QUICK_REFERENCE.md
    └── ARCHITECTURE_OVERVIEW.md  (this file)
```

---

## Component Hierarchy

### Main TUI Application

```
RPClientApp
├── AppHeader
│   ├── Static (title: "RP Client")
│   └── Static (connection status)
│
├── Horizontal (main-container)
│   │
│   ├── ContextPanel (sidebar)
│   │   ├── Static (character-info)
│   │   ├── Static (progress-info)
│   │   ├── Static (context-info)
│   │   └── Vertical (settings-panel)
│   │       ├── ProviderSelector
│   │       │   ├── Select (provider-dropdown)
│   │       │   └── TestingModeToggle
│   │       │       └── Checkbox (test-mode)
│   │       └── Button (settings-toggle)
│   │
│   └── Vertical (center-panel)
│       ├── ChatDisplay
│       │   └── RichLog (messages)
│       │
│       └── RPTextArea
│           ├── TextArea (message-input)
│           └── Button (send-button)
│
├── TriggerEditor (overlay, hidden)     ← TO BE INTEGRATED
│
├── TemplateEditor (overlay, hidden)    ← TO BE INTEGRATED
│
└── Footer
```

### Trigger Editor (Mockup)

```
TriggerEditorPanel
└── TabbedContent
    ├── TabPane: "Triggers"
    │   ├── CharacterSelection (docked, height: 8)
    │   │   └── Horizontal (character-grid)
    │   │       ├── CharacterButton ("Emma")
    │   │       ├── CharacterButton ("Marcus")
    │   │       └── CharacterButton ("Silas")
    │   │
    │   └── Grid (3 columns: 1fr, 2fr, 1.5fr)
    │       │
    │       ├── TriggerList (left panel)
    │       │   └── Horizontal (scroll-container)
    │       │       ├── Button (trigger-chip-1)
    │       │       ├── Button (trigger-chip-2)
    │       │       └── ...
    │       │
    │       ├── CharacterSheetPreview (center panel)
    │       │   └── Static (markdown content)
    │       │
    │       └── TriggerEditor (right panel)
    │           ├── Input (trigger-name)
    │           ├── Input (trigger-pattern)
    │           ├── TextArea (trigger-response)
    │           └── Horizontal (action-buttons)
    │               ├── Button (save)
    │               ├── Button (delete)
    │               └── Button (add-new)
    │
    ├── TabPane: "Settings"
    │   └── Static (placeholder)
    │
    └── TabPane: "Templates"
        └── Static (placeholder)
```

### Template Editor (Mockup)

```
TemplateEditorPanel
└── TabbedContent
    ├── TabPane: "Templates"
    │   └── Grid (3 columns: 1fr, 1.5fr, 1.5fr)
    │       │
    │       ├── TemplateList (left panel)
    │       │   ├── Static (header)
    │       │   └── Vertical (scroll-container)
    │       │       ├── Static (category: "System")
    │       │       ├── Button (template: "System Prompt")
    │       │       ├── Button (template: "Response Format")
    │       │       ├── Static (category: "Story")
    │       │       ├── Button (template: "Scene Introduction")
    │       │       └── ...
    │       │
    │       ├── TemplatePreview (center panel)
    │       │   └── Static (markdown preview)
    │       │
    │       └── TemplateEditor (right panel)
    │           ├── Input (template-name)
    │           ├── Select (category)
    │           ├── Input (description)
    │           ├── TextArea (content)
    │           └── Horizontal (action-buttons)
    │               ├── Button (save)
    │               ├── Button (delete)
    │               └── Button (new)
    │
    ├── TabPane: "Settings"
    │   └── Static (placeholder)
    │
    └── TabPane: "Import/Export"
        └── Static (placeholder)
```

---

## Data Flow

### Trigger CRUD Operations

#### Get Triggers
```
┌─────────┐                  ┌────────┐                 ┌────────┐
│   TUI   │                  │  IPC   │                 │ Bridge │
└─────────┘                  └────────┘                 └────────┘
     │                            │                          │
     │  1. User selects char     │                          │
     ├───────────────────────────►│                          │
     │                            │  2. GET_TRIGGERS         │
     │                            ├─────────────────────────►│
     │                            │                          │
     │                            │  3. Load from storage    │
     │                            │                          ├─┐
     │                            │                          │ │
     │                            │                          │◄┘
     │                            │  4. RESPONSE (triggers)  │
     │  5. Display triggers       │◄─────────────────────────┤
     │◄───────────────────────────┤                          │
     │                            │                          │
```

#### Create/Update Trigger
```
┌─────────┐                  ┌────────┐                 ┌────────┐
│   TUI   │                  │  IPC   │                 │ Bridge │
└─────────┘                  └────────┘                 └────────┘
     │                            │                          │
     │  1. User fills form       │                          │
     │      & clicks save        │                          │
     ├───────────────────────────►│                          │
     │                            │  2. SET_TRIGGER          │
     │                            ├─────────────────────────►│
     │                            │     (trigger_data)       │
     │                            │                          │
     │                            │  3. Validate data        │
     │                            │                          ├─┐
     │                            │  4. Save to storage      │ │
     │                            │                          │◄┘
     │                            │  5. RESPONSE (success)   │
     │  6. Show notification      │◄─────────────────────────┤
     │◄───────────────────────────┤                          │
     │  7. Reload triggers        │                          │
     ├───────────────────────────►│                          │
     │                            │                          │
```

### Template Operations

#### Get Templates
```
┌─────────┐                  ┌────────┐                 ┌────────┐
│   TUI   │                  │  IPC   │                 │ Bridge │
└─────────┘                  └────────┘                 └────────┘
     │                            │                          │
     │  1. Open template editor  │                          │
     ├───────────────────────────►│                          │
     │                            │  2. GET_TEMPLATES        │
     │                            ├─────────────────────────►│
     │                            │                          │
     │                            │  3. Load all templates   │
     │                            │                          ├─┐
     │                            │                          │ │
     │                            │                          │◄┘
     │                            │  4. RESPONSE (templates) │
     │  5. Display by category    │◄─────────────────────────┤
     │◄───────────────────────────┤                          │
     │                            │                          │
```

#### Select Template
```
┌─────────┐                  ┌────────┐                 ┌────────┐
│   TUI   │                  │  IPC   │                 │ Bridge │
└─────────┘                  └────────┘                 └────────┘
     │                            │                          │
     │  1. User clicks template  │                          │
     │      in list              │                          │
     ├───────────────────────────►│                          │
     │                            │  2. SET_TEMPLATE         │
     │                            ├─────────────────────────►│
     │                            │     (template_id)        │
     │                            │                          │
     │                            │  3. Set as active        │
     │                            │                          ├─┐
     │                            │                          │ │
     │                            │                          │◄┘
     │                            │  4. RESPONSE (success)   │
     │  5. Update UI state        │◄─────────────────────────┤
     │◄───────────────────────────┤                          │
     │                            │                          │
```

---

## Message Protocol

### IPC Message Structure

```json
{
    "type": "message_type",
    "request_id": "unique-uuid",
    "data": {
        "key": "value"
    }
}
```

### Message Types Enum

```python
class IPCMessageType(Enum):
    # Requests (Client → Server)
    SEND_MESSAGE = "send_message"
    GET_STATE = "get_state"
    GET_PROVIDERS = "get_providers"
    SET_PROVIDER = "set_provider"
    GET_TRIGGERS = "get_triggers"
    SET_TRIGGER = "set_trigger"
    GET_TEMPLATES = "get_templates"
    SET_TEMPLATE = "set_template"
    TEST_MODE = "test_mode"
    PING = "ping"
    SHUTDOWN = "shutdown"

    # Responses (Server → Client)
    RESPONSE = "response"
    ERROR = "error"
    STREAMING_CHUNK = "streaming_chunk"
    STREAMING_DONE = "streaming_done"
```

### Example Messages

#### Request: Get Triggers
```json
{
    "type": "get_triggers",
    "request_id": "a1b2c3d4-...",
    "data": {
        "character_id": "emma"
    }
}
```

#### Response: Trigger List
```json
{
    "type": "response",
    "request_id": "a1b2c3d4-...",
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

#### Error Response
```json
{
    "type": "error",
    "request_id": "a1b2c3d4-...",
    "data": {
        "error": "Character not found",
        "code": "CHARACTER_NOT_FOUND"
    }
}
```

---

## State Management

### TUI State

```python
# In RPClientApp
class RPClientApp(App):
    # Connection state
    ipc_client: SocketClient
    connected: bool

    # Session state
    current_character: str | None
    current_provider: str
    test_mode: bool

    # UI state
    settings_visible: bool
    trigger_editor_visible: bool
    template_editor_visible: bool
```

### Bridge State

```python
# In BridgeService
class BridgeService:
    # Session data
    characters: dict[str, Character]
    templates: dict[str, Template]
    active_template: str | None

    # LLM state
    llm_client: LLMClient
    current_provider: str
    test_mode: bool

    # Conversation state
    message_history: list[Message]
    context: dict[str, Any]
```

---

## Component Communication Patterns

### Pattern 1: Textual Messages (Internal TUI)

```python
# Child component posts message
class TriggerList(Container):
    class TriggerSelected(Message):
        def __init__(self, trigger_id: str):
            self.trigger_id = trigger_id

    def on_button_pressed(self, event):
        self.post_message(self.TriggerSelected("trigger-1"))

# Parent handles message (auto-routed by naming convention)
class TriggerEditorPanel(Container):
    def on_trigger_list_trigger_selected(
        self, message: TriggerList.TriggerSelected
    ):
        self.load_trigger(message.trigger_id)
```

### Pattern 2: IPC Messages (TUI ↔ Bridge)

```python
# TUI sends request
async def send_message():
    request = IPCRequest.create(
        IPCMessageType.SEND_MESSAGE,
        str(uuid.uuid4()),
        message="Hello, world!"
    )
    response = await ipc_client.send_request(request)

# Bridge handles request
async def handle_send_message(message: str):
    # Process message
    result = await llm_client.generate(message)

    # Return response
    return IPCResponse.create(
        request_id=request.request_id,
        result=result
    )
```

### Pattern 3: Reactive Properties

```python
# Define reactive property
class Editor(Container):
    selected_id = reactive(None)

    # Watcher called automatically on change
    def watch_selected_id(self, old, new):
        if new:
            self.load_data(new)

# Setting property triggers watcher
editor.selected_id = "trigger-1"  # watch_selected_id called
```

---

## Integration Points

### Where Mockups Connect to Main TUI

```python
# app.py

from .components import (
    # Existing components
    AppHeader,
    ChatDisplay,
    ContextPanel,
    ProviderSelector,
    RPTextArea,
    TestingModeToggle,

    # NEW: Add integrated editors
    TriggerEditor,    # From trigger_editor_enhanced_mockup.py
    TemplateEditor,   # From template_editor_mockup.py
)

class RPClientApp(App):

    BINDINGS = [
        # Existing bindings
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+s", "toggle_settings", "Settings"),

        # NEW: Add editor bindings
        ("f3", "toggle_trigger_editor", "Triggers"),
        ("f4", "toggle_template_editor", "Templates"),
    ]

    def compose(self) -> ComposeResult:
        yield AppHeader()

        # ... existing layout ...

        # NEW: Add editor overlays
        yield TriggerEditor(id="trigger-editor", classes="overlay hidden")
        yield TemplateEditor(id="template-editor", classes="overlay hidden")

        yield Footer()

    # NEW: Add toggle actions
    def action_toggle_trigger_editor(self):
        editor = self.query_one("#trigger-editor")
        editor.toggle_class("hidden")

    def action_toggle_template_editor(self):
        editor = self.query_one("#template-editor")
        editor.toggle_class("hidden")
```

### Data Loading Flow

```
TUI Component Mount
       │
       ├─► Check if data cached
       │       │
       │       ├─ Yes ─► Display cached data
       │       │
       │       └─ No ──► Load from Bridge
       │               │
       │               ├─► Create IPC request
       │               │
       │               ├─► Send via SocketClient
       │               │
       │               ├─► Await response
       │               │
       │               ├─► Parse response data
       │               │
       │               ├─► Update component state
       │               │
       │               └─► Render UI
       │
       └─► Ready for user interaction
```

---

## Testing Strategy

### Test Levels

```
┌─────────────────────────────────────────┐
│         End-to-End Tests                │  Manual & Automated
│  (Full TUI ↔ Bridge ↔ LLM flow)        │  - User workflows
└─────────────────────────────────────────┘  - UI interactions
                  │
┌─────────────────────────────────────────┐
│       Integration Tests                 │  Automated
│  (TUI ↔ Bridge via IPC)                │  - Component integration
└─────────────────────────────────────────┘  - IPC communication
                  │
┌─────────────────────────────────────────┐
│          Unit Tests                     │  Automated (60/60 ✓)
│  (Individual components)                │  - Component logic
└─────────────────────────────────────────┘  - Data structures
```

### Current Test Coverage

```
tests/
├── test_ipc_protocol.py          ✓ Protocol serialization
├── test_socket_client.py          ✓ Client communication
├── test_socket_server.py          ✓ Server handling
├── test_bridge_service.py         ✓ Bridge logic
├── test_mock_llm_client.py        ✓ Mock LLM
└── test_integration.py            ✓ E2E flows

Total: 60/60 tests passing
```

---

## Key Design Principles

### 1. Separation of Concerns
- **TUI**: Presentation only, no business logic
- **Bridge**: Business logic, no UI code
- **IPC**: Communication protocol, no knowledge of domain

### 2. Message-Driven Architecture
- Components communicate via messages
- Loose coupling between components
- Easy to add new features

### 3. Async-First
- All IPC calls are async
- Non-blocking UI updates
- Smooth user experience

### 4. Testability
- Mock IPC for testing TUI
- Mock LLM for testing Bridge
- Independent component testing

### 5. Modularity
- Reusable components
- Clear interfaces
- Easy to extend

---

## Next Steps for Integration

1. **Extract Trigger Editor** → `trigger_editor.py`
   - Remove sample data
   - Add IPC loading
   - Connect to main app

2. **Extract Template Editor** → `template_editor.py`
   - Remove sample data
   - Add IPC loading
   - Connect to main app

3. **Update Bridge Service**
   - Add trigger endpoints
   - Add template endpoints
   - Add persistence

4. **Test Integration**
   - Unit tests for new components
   - Integration tests for IPC
   - Manual testing for UX

5. **Polish & Document**
   - User documentation
   - Code comments
   - Video demos (optional)

---

## Useful Commands

```bash
# Run mockups standalone
python scripts/run_trigger_editor_enhanced.py
python scripts/run_template_editor.py

# Run main app
python -m src.presentation.tui.app

# Run bridge
python -m src.application.bridge_service --test-mode

# Run tests
pytest tests/ -v

# Dev mode with console
textual console  # Terminal 1
textual run --dev src/presentation/tui/app.py  # Terminal 2
```

---

**For detailed integration steps, see:** `TUI_INTEGRATION_GUIDE.md`

**For quick code snippets, see:** `INTEGRATION_QUICK_REFERENCE.md`
