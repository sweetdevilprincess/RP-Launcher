# TUI Separation and Integration Plan

## Executive Summary

This document outlines the architectural refactoring needed to separate TUI concerns for parallel development, testability, and maintainability. The plan separates presentation (styles/layout) from business logic (controllers) and data access (services).

**Timeline**: 3-5 hours total
- **Phase 1 (Quick Win)**: Extract CSS → 30 minutes
- **Phase 2**: Create Controller layer → 2 hours
- **Phase 3**: Create Service layer → 1-2 hours

---

## Current Architecture Issues

### 1. Monolithic app.py (509 lines)
- **Lines 39-240**: 200+ lines of embedded CSS with f-string interpolation
- **Lines 327-421**: Business logic mixed with UI orchestration
- **Result**: Merge conflicts when multiple developers work on UI

### 2. Direct File Access in Components
`context_panel.py` lines 66-72:
```python
state_file = self.rp_dir / "state" / "current_state.md"
counter_file = self.rp_dir / "state" / "response_counter.json"
# Direct file reads...
```
- **Problem**: Components tightly coupled to filesystem
- **Impact**: Cannot test components without real files

### 3. Business Logic in UI Layer
`app.py` lines 348-384:
```python
def action_submit_message(self) -> None:
    # Validation
    # IPC communication
    # Streaming callback registration
    # Error handling
```
- **Problem**: UI responsibilities mixed with business logic
- **Impact**: Cannot unit test message sending without UI framework

---

## Target Architecture

```
src/presentation/tui/
├── app.py                      # Orchestrator (< 150 lines)
├── components/                 # Pure UI widgets
│   ├── app_header.py
│   ├── chat_display.py
│   ├── context_panel.py       # Receives data via props
│   ├── provider_selector.py
│   ├── rp_textarea.py
│   └── testing_mode_toggle.py
├── screens/                    # Overlay screens
│   └── base_overlay.py
├── styles/
│   ├── theme.py               # Colors/palette (existing)
│   └── layout.tcss            # ALL CSS extracted here ← NEW
├── controllers/               # Business logic ← NEW
│   ├── __init__.py
│   ├── message_controller.py  # Send/receive messages
│   ├── connection_controller.py  # Bridge IPC lifecycle
│   └── settings_controller.py # Provider/triggers/templates
└── services/                  # Data access ← NEW
    ├── __init__.py
    ├── state_service.py       # File reads for state
    └── ipc_service.py         # Wrapped IPC client
```

---

## Phase 1: Extract CSS to Separate File (30 min)

### Files to Create:
**`src/presentation/tui/styles/layout.tcss`**

### Changes to `app.py`:
```python
# Before (line 39):
CSS = dedent(f"""
/* 200+ lines of CSS */
""")

# After:
CSS_PATH = Path(__file__).parent / "styles" / "layout.tcss"
```

### Benefits:
- Visual developer can edit `layout.tcss` exclusively
- No merge conflicts on `app.py`
- CSS syntax highlighting in IDEs
- Can still use Python f-strings via template rendering

### Template System:
```python
# In styles/__init__.py
def render_css_template(palette: dict) -> str:
    """Render TCSS template with palette colors."""
    template = (Path(__file__).parent / "layout.tcss").read_text()
    return template.format(**palette)
```

---

## Phase 2: Create Controller Layer (2 hours)

### 2.1 MessageController

**File**: `src/presentation/tui/controllers/message_controller.py`

**Responsibilities**:
- Message validation
- Send messages via IPC
- Handle streaming responses
- Error handling

**Interface**:
```python
class MessageController:
    def __init__(self, ipc_client: SocketClient):
        self.ipc = ipc_client

    def send_message(
        self,
        message: str,
        *,
        on_chunk: Callable[[str], None],
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None]
    ) -> None:
        """Send message with callbacks for streaming."""
        # Validation
        # IPC communication
        # Callback orchestration
```

**Extracted from**: `app.py` lines 348-384

---

### 2.2 ConnectionController

**File**: `src/presentation/tui/controllers/connection_controller.py`

**Responsibilities**:
- Bridge connection lifecycle
- Health checks (ping)
- Reconnection logic
- Connection state management

**Interface**:
```python
class ConnectionController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.ipc_client: SocketClient | None = None
        self.connected = False

    def connect(self) -> bool:
        """Establish connection to Bridge."""

    def disconnect(self) -> None:
        """Close connection cleanly."""

    def is_healthy(self) -> bool:
        """Check if connection is alive via ping."""

    def get_client(self) -> SocketClient:
        """Get IPC client (raises if not connected)."""
```

**Extracted from**: `app.py` lines 327-346

---

### 2.3 SettingsController

**File**: `src/presentation/tui/controllers/settings_controller.py`

**Responsibilities**:
- Get/set LLM provider
- Get/set triggers
- Get/set templates
- Toggle testing mode
- Get session state

**Interface**:
```python
class SettingsController:
    def __init__(self, ipc_client: SocketClient):
        self.ipc = ipc_client

    # Provider management
    def get_providers(self) -> list[str]:
        """Get list of available LLM providers."""

    def get_current_provider(self) -> str:
        """Get currently selected provider."""

    def set_provider(self, provider_id: str) -> bool:
        """Switch to a different provider."""

    # Trigger management
    def get_triggers(self) -> list[dict]:
        """Get active character triggers."""

    def set_trigger(self, trigger_id: str, enabled: bool) -> bool:
        """Enable/disable a trigger."""

    # Template management
    def get_templates(self) -> list[str]:
        """Get available narrative templates."""

    def set_template(self, template_id: str) -> bool:
        """Switch narrative template."""

    # Testing mode
    def toggle_testing_mode(self, enabled: bool) -> bool:
        """Enable/disable mock LLM testing mode."""

    # State
    def get_session_state(self) -> dict:
        """Get current session state."""
```

**IPC Messages Used**:
- `IPCMessageType.GET_PROVIDERS`
- `IPCMessageType.SET_PROVIDER`
- `IPCMessageType.GET_TRIGGERS`
- `IPCMessageType.SET_TRIGGER`
- `IPCMessageType.GET_TEMPLATES`
- `IPCMessageType.SET_TEMPLATE`
- `IPCMessageType.TEST_MODE`
- `IPCMessageType.GET_STATE`

**Bridge Handlers** (Already Implemented):
- `bridge_service.py:345` - `_handle_get_providers()`
- `bridge_service.py:364` - `_handle_set_provider()`
- Similar handlers exist for other settings

---

## Phase 3: Create Service Layer (1-2 hours)

### 3.1 StateService

**File**: `src/presentation/tui/services/state_service.py`

**Responsibilities**:
- Abstract file system access
- Parse state files
- Cache frequently accessed data
- Provide reactive updates

**Interface**:
```python
class StateService:
    def __init__(self, rp_dir: Path):
        self.rp_dir = rp_dir
        self._cache: dict = {}
        self._cache_ttl = 3.0  # seconds

    def get_chapter_info(self) -> tuple[str, str, str]:
        """Get (chapter, timestamp, location) from current_state.md"""

    def get_active_characters(self) -> list[str]:
        """Get list of active character names."""

    def get_arc_progress(self) -> tuple[int, int, float]:
        """Get (progress, next_arc, percentage)."""

    def get_response_count(self) -> int:
        """Get total response count."""

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        """Subscribe to state changes."""
```

**Extracted from**:
- `utils/helpers.py` - Pure functions
- `context_panel.py` lines 66-72 - Direct file access

**Benefits**:
- Testable with mock filesystem
- Can implement caching/memoization
- Single source of truth for state
- Can add file watchers later

---

### 3.2 IPCService (Optional Wrapper)

**File**: `src/presentation/tui/services/ipc_service.py`

**Responsibilities**:
- Wrap SocketClient with higher-level interface
- Automatic retry logic
- Request queuing
- Error translation

**Interface**:
```python
class IPCService:
    def __init__(self, client: SocketClient):
        self._client = client

    def request(
        self,
        message_type: IPCMessageType,
        timeout: float = 30.0,
        **kwargs
    ) -> dict:
        """Send request and return parsed response data."""

    def request_async(
        self,
        message_type: IPCMessageType,
        callback: Callable[[dict], None],
        **kwargs
    ) -> str:
        """Send async request with callback."""
```

---

## Updated app.py Structure

**Target**: < 150 lines

```python
class RPClientApp(App):
    """Main RP Client TUI Application."""

    # Load CSS from file
    CSS_PATH = Path(__file__).parent / "styles" / "layout.tcss"

    def __init__(self, rp_dir: Path, host: str, port: int):
        super().__init__()
        self.rp_dir = rp_dir

        # Initialize services
        self.state_service = StateService(rp_dir)

        # Initialize controllers
        self.connection_controller = ConnectionController(host, port)
        self.message_controller = None  # Created after connection
        self.settings_controller = None  # Created after connection

        # UI components (assigned during compose)
        self.chat_display: ChatDisplay | None = None
        self.context_panel: ContextPanel | None = None

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        # Navigation tabs
        yield Tabs(...)

        # Main content
        with Container(id="main-container"):
            self.context_panel = ContextPanel(self.state_service)
            yield self.context_panel

            self.chat_display = ChatDisplay()
            yield self.chat_display

        # Input area
        yield self._compose_input_area()

        # Footer
        yield AppHeader(self.rp_dir)

    def on_mount(self) -> None:
        """Initialize after mounting."""
        # Connect to Bridge
        if self.connection_controller.connect():
            client = self.connection_controller.get_client()
            self.message_controller = MessageController(client)
            self.settings_controller = SettingsController(client)

            self.chat_display.add_message("system", "Connected to Bridge")
        else:
            self.chat_display.add_message("system", "Failed to connect")

    def action_submit_message(self) -> None:
        """Handle message submission."""
        message = self.text_area.text.strip()
        if not message:
            return

        # Delegate to controller
        self.message_controller.send_message(
            message,
            on_chunk=self._on_stream_chunk,
            on_complete=self._on_message_complete,
            on_error=self._on_message_error
        )

    def _on_stream_chunk(self, chunk: str) -> None:
        """Handle streaming chunk."""
        # Update UI

    def _on_message_complete(self, response: str) -> None:
        """Handle completed message."""
        self.chat_display.add_message("claude", response)

    def _on_message_error(self, error: str) -> None:
        """Handle error."""
        self.chat_display.add_message("system", f"Error: {error}")
```

---

## Settings Integration Points

### Current TUI Components for Settings:

1. **`provider_selector.py`**
   - Should use `SettingsController.get_providers()`
   - Should call `SettingsController.set_provider()` on selection

2. **`testing_mode_toggle.py`**
   - Should use `SettingsController.toggle_testing_mode()`

3. **Settings Screen** (Not yet implemented)
   - Needs to be created
   - Should display all settings from `SettingsController`

### Bridge Settings Handlers (Already Implemented):

From `bridge_service.py`:

| IPC Message Type | Handler Method | Line | Status |
|-----------------|----------------|------|--------|
| `GET_PROVIDERS` | `_handle_get_providers()` | 345 | ✅ Implemented |
| `SET_PROVIDER` | `_handle_set_provider()` | 364 | ✅ Implemented |
| `GET_TRIGGERS` | Not visible in grep | ? | ❓ Check bridge |
| `SET_TRIGGER` | Not visible in grep | ? | ❓ Check bridge |
| `GET_TEMPLATES` | Not visible in grep | ? | ❓ Check bridge |
| `SET_TEMPLATE` | Not visible in grep | ? | ❓ Check bridge |
| `TEST_MODE` | Not visible in grep | ? | ❓ Check bridge |
| `GET_STATE` | Not visible in grep | ? | ❓ Check bridge |

**Action Items**:
1. ✅ Provider switching fully implemented
2. ❓ Verify all other handlers exist in Bridge
3. ⚠️ If missing, implement remaining handlers in Bridge first
4. ✅ Then implement SettingsController to use them

---

## Launcher Integration Points

### Current Launch Flow:

**`launch.py` lines 334-360**:
```python
# 1. Start Bridge in background process
bridge_process = multiprocessing.Process(
    target=run_bridge,
    args=(rp_dir, host, port)
)
bridge_process.start()

# 2. Wait for Bridge readiness (socket connection test)
wait_for_bridge(host, port, timeout=10)

# 3. Start TUI
app = RPClientApp(rp_dir, host, port)
app.run()
```

### What Launcher Needs to Pass to TUI:

| Parameter | Source | Used For |
|-----------|--------|----------|
| `rp_dir` | User selection / CLI arg | State files, config |
| `host` | CLI arg (default: 127.0.0.1) | Bridge connection |
| `port` | CLI arg (default: 5555) | Bridge connection |

### What TUI Needs on Startup:

1. **Connection Info**: host + port → ConnectionController
2. **RP Directory**: rp_dir → StateService
3. **Initial State**: Loaded via StateService on mount
4. **Bridge Health Check**: ConnectionController.connect()

### Settings Initialization Flow:

```
1. TUI starts → on_mount()
2. ConnectionController.connect() → establishes IPC
3. SettingsController created with IPC client
4. TUI queries: SettingsController.get_current_provider()
5. TUI displays current provider in UI
6. User changes provider → SettingsController.set_provider()
7. Bridge receives SET_PROVIDER → switches provider
8. Bridge sends response → TUI updates display
```

---

## Testing Strategy

### Unit Tests

**Controllers** (No UI framework needed):
```python
def test_message_controller_validates_empty():
    controller = MessageController(mock_ipc_client)

    with pytest.raises(ValueError):
        controller.send_message("")
```

**Services** (Mock filesystem):
```python
def test_state_service_parses_chapter(tmp_path):
    state_file = tmp_path / "current_state.md"
    state_file.write_text("**Current Chapter:** Act 2")

    service = StateService(tmp_path)
    chapter, _, _ = service.get_chapter_info()

    assert chapter == "Act 2"
```

### Integration Tests

**TUI + Controllers** (Mock IPC):
```python
def test_tui_sends_message():
    mock_ipc = MockSocketClient()
    app = RPClientApp(test_rp_dir, "localhost", 5555)
    app.connection_controller._client = mock_ipc

    # Simulate user input
    app.text_area.text = "Hello"
    app.action_submit_message()

    # Verify IPC was called
    assert mock_ipc.last_request.type == "send_message"
```

---

## Migration Path

### Step 1: Extract CSS (Quick Win)
- **Time**: 30 minutes
- **Risk**: Low
- **Benefit**: Immediate parallel development
- **Files Changed**: `app.py`, `styles/layout.tcss`, `styles/__init__.py`

### Step 2: Create Controllers
- **Time**: 2 hours
- **Risk**: Medium (behavior changes)
- **Benefit**: Testable business logic
- **Files Changed**: `app.py`, `controllers/*.py`
- **Tests**: Unit tests for each controller

### Step 3: Create Services
- **Time**: 1-2 hours
- **Risk**: Low (internal refactor)
- **Benefit**: Testable data access
- **Files Changed**: `context_panel.py`, `services/*.py`
- **Tests**: Unit tests with mock filesystem

### Step 4: Update Components
- **Time**: 1 hour
- **Risk**: Low
- **Benefit**: Loose coupling
- **Files Changed**: `context_panel.py`, `provider_selector.py`
- **Tests**: Component tests with mock services

---

## Dependency Injection Pattern

### Before (Tight Coupling):
```python
class ContextPanel(ScrollableContainer):
    def __init__(self, rp_dir: Path):
        self.rp_dir = rp_dir  # Direct filesystem dependency

    def refresh_context(self):
        state_file = self.rp_dir / "state" / "current_state.md"
        content = state_file.read_text()  # Direct file I/O
```

### After (Loose Coupling):
```python
class ContextPanel(ScrollableContainer):
    def __init__(self, state_service: StateService):
        self.state_service = state_service  # Injected dependency

    def refresh_context(self):
        chapter, time, loc = self.state_service.get_chapter_info()
        # Use data, no file I/O
```

**Benefits**:
- Can pass MockStateService in tests
- ContextPanel doesn't know about files
- Can swap StateService implementation (database, API, etc.)

---

## Backward Compatibility

### During Migration:

**Option 1**: Feature flags
```python
class RPClientApp(App):
    USE_CONTROLLERS = True  # Toggle new architecture

    def action_submit_message(self):
        if self.USE_CONTROLLERS:
            self.message_controller.send_message(...)
        else:
            # Old implementation
```

**Option 2**: Gradual migration
```python
# Start with controllers but keep old code commented
def action_submit_message(self):
    # NEW: Use controller
    self.message_controller.send_message(...)

    # OLD: (remove after testing)
    # if not self.text_area or not self.chat_display:
    #     return
    # ...
```

---

## File Structure After Refactoring

```
src/presentation/tui/
├── __init__.py
├── app.py                      # 120 lines (down from 509)
│
├── components/                 # Pure UI widgets
│   ├── __init__.py
│   ├── app_header.py
│   ├── chat_display.py
│   ├── context_panel.py       # Uses StateService
│   ├── provider_selector.py   # Uses SettingsController
│   ├── rp_textarea.py
│   ├── testing_mode_toggle.py # Uses SettingsController
│   ├── character_editor.py
│   ├── trigger_editor_mockup.py
│   ├── template_editor_mockup.py
│   └── trigger_editor_enhanced_mockup.py
│
├── screens/                    # Overlay screens
│   ├── __init__.py
│   ├── base_overlay.py
│   ├── settings_screen.py     # NEW: Full settings UI
│   └── help_screen.py         # NEW: Help overlay
│
├── styles/
│   ├── __init__.py
│   ├── theme.py               # PALETTE, STYLES
│   └── layout.tcss            # NEW: All CSS here
│
├── controllers/               # NEW: Business logic
│   ├── __init__.py
│   ├── message_controller.py
│   ├── connection_controller.py
│   └── settings_controller.py
│
├── services/                  # NEW: Data access
│   ├── __init__.py
│   ├── state_service.py
│   └── ipc_service.py
│
└── utils/
    ├── __init__.py
    └── helpers.py             # Keep pure utility functions
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] CSS extracted to `styles/layout.tcss`
- [ ] `app.py` loads CSS from file
- [ ] Visual developer can edit CSS without touching Python
- [ ] No merge conflicts on `app.py` when changing styles

### Phase 2 Complete When:
- [ ] Controllers created and tested
- [ ] `app.py` delegates to controllers
- [ ] Controllers have 80%+ unit test coverage
- [ ] Business logic separated from UI

### Phase 3 Complete When:
- [ ] Services created and tested
- [ ] Components use dependency injection
- [ ] Services have 80%+ unit test coverage
- [ ] No direct file I/O in components

### Overall Success:
- [ ] `app.py` < 150 lines
- [ ] All existing functionality preserved
- [ ] Parallel development possible (no conflicts)
- [ ] Test coverage > 80% for new code
- [ ] Settings fully functional via SettingsController

---

## Next Steps

1. **Verify Bridge Handlers**: Check if all IPC message handlers exist in `bridge_service.py`
2. **Extract CSS**: Start with Phase 1 (quick win)
3. **Create Controllers**: Implement Phase 2 in order (Connection → Message → Settings)
4. **Create Services**: Implement Phase 3 (State → IPC wrapper)
5. **Update Components**: Refactor to use dependency injection
6. **Write Tests**: Achieve 80%+ coverage
7. **Create Settings Screen**: Full UI for all settings

---

## Questions to Answer

1. **Are all Bridge handlers implemented?**
   - Need to check `bridge_service.py` for GET_TRIGGERS, SET_TRIGGER, etc.

2. **Should we create a Settings screen now or later?**
   - Recommend: After Phase 2 (controllers exist)

3. **Do we need the IPCService wrapper?**
   - Optional: SocketClient might be sufficient

4. **Should context panel auto-refresh?**
   - Current: Every 3 seconds
   - Better: Event-driven updates via StateService

5. **How to handle streaming chunk display?**
   - Current: Accumulate and display on complete
   - Better: Update ChatDisplay in real-time (needs widget enhancement)

---

## End of Plan

**Ready to implement?** Start with Phase 1 (CSS extraction) for immediate wins.
**Need clarification?** Review "Questions to Answer" section first.
**Multiple developers?** Visual dev takes `layout.tcss`, logic dev takes controllers.
