# TUI Application Execution Flow

**File:** `refactoring/src/presentation/tui/app.py` (964 lines)
**Purpose:** Main TUI application - user interface for RP client
**Class:** `RPClientApp(App)` (lines 56-964)
**Parent:** `textual.app.App` (Textual framework)

---

## Imports

### Standard Library
- `sys` (line 16)
- `pathlib.Path` (line 17)

### Textual Framework (lines 19-22)
- `textual.app.App` - Base application class
- `textual.app.ComposeResult` - Layout composition
- `textual.binding.Binding` - Keyboard bindings
- `textual.containers.*` - Layout containers
- `textual.widgets.*` - UI widgets

### Infrastructure Layer (lines 24-28)
- `infrastructure.ipc.IPCMessageType` - IPC message types
- `infrastructure.ipc.SocketClient` → **IPC CLIENT**
- `infrastructure.filesystem.StatePaths` - Path utilities
- `infrastructure.logging.LoggingService` - Logging
- `infrastructure.logging.PythonLoggingService` - Python logger wrapper
- `infrastructure.sessions.SessionStateService` - Session state
- `domain.sessions.SessionRepository` - Session data access

### Components (lines 29-40)
All from `.components`:
- `AddMessageRequest` - Message addition event
- `AppHeader` - Header component
- `SimpleMessage` - Message display
- `BranchesPage` - Branch visualization
- `ChatDisplay` - Chat area
- `ContextPanel` - Context sidebar
- `EntityManager` - Entity management
- `RPTextArea` - Text input
- `SettingsOverlay` - Settings panel
- `UpdateMessageRequest` - Message update event

### Screens (lines 41-48)
All from `.screens`:
- `BaseOverlay` - Base overlay class
- `BranchCreationDialog` - Branch creation UI
- `ChapterCompressionDialog` - Compression UI
- `CharacterSheetOverlay` - Character sheet display
- `StoryOverviewOverlay` - Story overview
- `HelpOverlay` - Help screen

### Styles (line 49)
- `.styles.get_app_css` - CSS stylesheet function

---

## Constructor: `__init__(rp_dir, bridge_host, bridge_port)` (lines 79-122)

### Parameters
- `rp_dir: Path` - RP directory path
- `bridge_host: str = "127.0.0.1"` - Bridge server host
- `bridge_port: int = 5555` - Bridge server port

### Initialization Steps:

#### 1. Call Parent Constructor (line 87)
```python
super().__init__()
```

#### 2. Store Basic State (lines 88-90)
- `self.rp_dir = rp_dir`
- `self.bridge_host = bridge_host`
- `self.bridge_port = bridge_port`

#### 3. Initialize Component References - All None (lines 93-98)
- `self.header: AppHeader | None = None`
- `self.context_panel: ContextPanel | None = None`
- `self.chat_display: ChatDisplay | None = None`
- `self.text_area: RPTextArea | None = None`
- `self.entity_manager: EntityManager | None = None`
- `self.settings_overlay: SettingsOverlay | None = None`

**Note:** Components created in `compose()`, not constructor

#### 4. Initialize IPC State (lines 101-103)
- `self.ipc_client: SocketClient | None = None`
- `self.connected = False`
- `self.connection_time: float = 0.0`

#### 5. Create StatePaths (line 106)
```python
paths = StatePaths(rp_dir=rp_dir)
```
- **File:** `src/infrastructure/filesystem/state_paths.py`
- **→ Trace if needed**

#### 6. Create Logger (lines 108-109)
```python
import logging
logger = PythonLoggingService(logger=logging.getLogger("rp.tui.app"))
```
- **File:** `src/infrastructure/logging/python_logging.py`
- Wraps Python's standard logging.Logger

#### 7. Create SessionStateService (line 112)
```python
session_state_service = SessionStateService(logger=logger)
```
- **File:** `src/infrastructure/sessions/session_state_service.py`
- **→ TRACE THIS:** Session state management

#### 8. Create SessionRepository (lines 115-119)
```python
self.session_repository = SessionRepository(
    paths=paths,
    logger=logger,
    session_state_service=session_state_service
)
```
- **File:** `src/domain/sessions/repository.py`
- **Parameters:**
  - `paths`: StatePaths instance
  - `logger`: PythonLoggingService instance
  - `session_state_service`: SessionStateService instance
- **→ TRACE THIS:** Session data access

#### 9. Initialize Tab Tracking (line 122)
```python
self.last_non_entity_tab = "tab-chat"
```

### Constructor Services Summary:
- **StatePaths** - Path utilities
- **PythonLoggingService** - Logger wrapper
- **SessionStateService** - Session state management
- **SessionRepository** - Session data persistence

**NO IPC connection yet** - deferred to `on_mount()`

---

## `compose()` Method (lines 124-244)

**Called by:** Textual framework during app initialization

**Purpose:** Build UI layout and create all components

### Layout Structure:

#### 1. Top Tabs Navigation (lines 127-135)
```python
Tabs(
    Tab("💬 Chat", id="tab-chat"),
    Tab("🎭 Entities", id="tab-entities"),
    Tab("🌳 Branches", id="tab-branches"),
    Tab("⚙️ Settings", id="tab-settings"),
    Tab("❓ Help", id="tab-help"),
    Tab("📊 Status", id="tab-status"),
    id="top-tabs"
)
```

#### 2. Content Switcher (line 138)
Contains different page layouts based on active tab

### Components Created:

#### A. Chat Page (lines 140-159)
1. **ContextPanel** (line 142)
   - **Constructor:** `ContextPanel(self.rp_dir, id="context-panel")`
   - **Stored:** `self.context_panel`
   - **→ TRACE THIS:** Context sidebar component

2. **ChatDisplay** (line 145)
   - **Constructor:** `ChatDisplay(id="chat-panel")`
   - **Stored:** `self.chat_display`
   - **→ TRACE THIS:** Chat message display

3. **RPTextArea** (line 152)
   - **Constructor:** `RPTextArea(id="input-area")`
   - **Stored:** `self.text_area`
   - **→ TRACE THIS:** Text input component

4. **Buttons** (lines 156, 158)
   - Send button (line 156)
   - Compress Chapter button (line 158)

#### B. Entities Page (lines 162-163)
- Placeholder static text (component added later in compose)

#### C. Branches Page (line 166)
- **BranchesPage** component
- **→ TRACE THIS:** Branch visualization

#### D. Settings Page (lines 169-170)
- Empty container (overlay shown on demand)

#### E. Help Page (lines 173-207)
- Static Markdown with help text

#### F. Status Page (lines 210-231)
- Static Markdown with status info

#### G. Footer/Header (lines 234-235)
- **AppHeader** (line 234)
  - **Constructor:** `AppHeader(self.rp_dir, id="app-header")`
  - **Stored:** `self.header`
  - **→ TRACE THIS:** Header component

#### H. Floating Overlays (lines 238-244)
1. **EntityManager** (line 238)
   - **Constructor:** `EntityManager(id="entity-manager")`
   - **Stored:** `self.entity_manager`

2. **SettingsOverlay** (line 242)
   - **Constructor:** `SettingsOverlay(id="settings-overlay")`
   - **Stored:** `self.settings_overlay`
   - Initially hidden (line 243)

### compose() Summary:
Creates **7+ major components** plus all UI widgets

---

## `on_mount()` Method (lines 246-268)

**Called by:** Textual framework after `compose()` completes

**Purpose:** Initialize state after UI is ready

### Steps:

#### 1. Load Theme (line 249)
```python
self._load_theme()
```
- → Go to `_load_theme()` section below

#### 2. Connect to Bridge (line 252)
```python
self._connect_to_bridge()
```
- → Go to `_connect_to_bridge()` section below
- **CRITICAL:** Establishes IPC connection

#### 3. Load Chat History (line 255)
```python
self._load_chat_history()
```
- → Go to `_load_chat_history()` section below

#### 4. Display Welcome Message (lines 258-268)
- Posts `AddMessageRequest` to chat display
- Shows connection status
- Shows help hints

---

## `_load_theme()` Method (lines 316-331)

### Flow:
1. Loads `{rp_dir}/config/config.json` (line 320)
2. Reads: `config["system"]["theme"]` (line 324)
3. Sets: `self.theme = theme` (line 325)
4. Fallback: Uses default theme if error

---

## `_connect_to_bridge()` Method (lines 358-409)

**CRITICAL:** Establishes IPC connection to Bridge service

### Configuration:
- `max_retries = 3` (line 362)
- `retry_delay = 1.0` seconds (line 363)

### Retry Loop (lines 365-409):

#### Attempt 1-3:

1. **Create SocketClient** (lines 367-370)
   ```python
   self.ipc_client = SocketClient(
       host=self.bridge_host,
       port=self.bridge_port
   )
   ```
   - **File:** `src/infrastructure/ipc/socket_client.py`
   - **→ TRACE THIS:** IPC client implementation

2. **Connect** (line 371)
   ```python
   self.ipc_client.connect()
   ```
   - Opens socket connection to Bridge

3. **Test with PING** (lines 374-375)
   ```python
   response = self.ipc_client.send_request(IPCMessageType.PING, timeout=5.0)
   ```
   - Sends PING message to Bridge
   - Waits up to 5 seconds for response

4. **Check Success** (lines 375-380)
   - **If ping successful:**
     - Sets: `self.connected = True`
     - Sets: `self.connection_time = time.time()`
     - Notifies user
     - **Returns successfully**

   - **If ping failed:**
     - Disconnects (line 383)
     - Retries (continues loop)

5. **Handle Errors** (lines 386-405)
   - Catches all exceptions
   - Cleans up connection
   - Waits before retry (if not last attempt)
   - Notifies user if all retries fail

### Result:
- **Success:** `self.ipc_client` connected, `self.connected = True`
- **Failure:** `self.ipc_client = None`, `self.connected = False`

---

## `_load_chat_history()` Method (lines 270-314)

### Flow:

1. **Load Session** (line 277)
   ```python
   session = self.session_repository.load_active_session()
   ```
   - Uses SessionRepository created in constructor

2. **Iterate Messages** (line 280)
   - For each message in session

3. **Post User Messages** (lines 282-290)
   - **If exists:** `message.user_message`
   - Posts `AddMessageRequest` with:
     - sender="you"
     - content from session
     - message_id with "history-" prefix
     - response_num from session

4. **Post Assistant Messages** (lines 293-301)
   - **If exists:** `message.assistant_response`
   - Posts `AddMessageRequest` with:
     - sender="claude"
     - content from session
     - message_id with "history-" prefix
     - response_num from session

5. **Log Results** (lines 304-306)
   - Logs count of loaded messages

6. **Error Handling** (lines 308-314)
   - Catches `FileNotFoundError` (new RP, no session yet)
   - Catches general exceptions
   - Logs errors but doesn't crash

---

## Key IPC Communication Methods

### `action_submit_message()` (lines 411-471)

**Triggered by:** Ctrl+Enter or Send button

### Flow:

1. **Validate Input** (lines 413-419)
   - Checks text_area exists
   - Checks message not empty

2. **Generate Message IDs** (lines 422-424)
   ```python
   self._user_message_id = str(uuid.uuid4())
   self._streaming_message_id = str(uuid.uuid4())
   ```

3. **Display User Message** (lines 427-433)
   - Posts `AddMessageRequest` for user message

4. **Clear Input** (line 436)

5. **Send to Bridge** (lines 439-460)
   - **If connected:**
     - Initializes streaming buffer (line 442)
     - Creates empty assistant message (lines 445-451)
     - **Sends async IPC request** (lines 454-459):
       ```python
       self.ipc_client.send_request_async(
           IPCMessageType.SEND_MESSAGE,
           callback=self._handle_llm_response,
           streaming_callback=self._handle_streaming_chunk,
           user_message=message
       )
       ```
     - **→ TRACE THIS:** Async IPC implementation

   - **If not connected:** (lines 465-471)
     - Shows error message

### `_handle_streaming_chunk(chunk)` (lines 473-489)

**Called by:** IPC client for each streaming chunk

### Flow:
1. Accumulates: `self._streaming_buffer += chunk` (line 480)
2. Posts: `UpdateMessageRequest` to chat display (lines 483-489)

### `_handle_llm_response(response)` (lines 491-499)

**Called by:** IPC client when response complete

**Purpose:** Handle final response from Bridge

---

## Service Dependencies Graph

```
RPClientApp
├─> StatePaths (rp_dir)
├─> PythonLoggingService (logger)
├─> SessionStateService (logger)
├─> SessionRepository (paths, logger, session_state_service)
├─> SocketClient (host, port) ──> BRIDGE IPC
│
└─> Components (created in compose())
     ├─> AppHeader (rp_dir)
     ├─> ContextPanel (rp_dir)
     ├─> ChatDisplay ()
     ├─> RPTextArea ()
     ├─> EntityManager ()
     ├─> SettingsOverlay ()
     └─> BranchesPage ()
```

---

## IPC Message Types Used

From this file:
1. **IPCMessageType.PING** (line 374)
   - Connection test
   - Sent in `_connect_to_bridge()`

2. **IPCMessageType.SEND_MESSAGE** (line 455)
   - Send user message to LLM
   - Sent in `action_submit_message()`

**→ TRACE:** Other message types in handlers

---

## Keyboard Bindings (lines 69-77)

- `Ctrl+Q` → `quit` - Exit app
- `Ctrl+J` → `submit_message` - Send message
- `Ctrl+T` → `cycle_theme` - Change theme
- `F1` → `show_help` - Help overlay
- `F2` → `show_character_sheet` - Character sheet
- `F3` → `show_story_overview` - Story overview
- `F4` → `show_status` - Status overlay

---

## Next Traces Required

### High Priority:
1. **SocketClient** - IPC communication
   - File: `src/infrastructure/ipc/socket_client.py`
   - Methods: `connect()`, `send_request()`, `send_request_async()`

2. **ChatDisplay** - Message rendering
   - File: `src/presentation/tui/components/chat_display.py`
   - Handles `AddMessageRequest` and `UpdateMessageRequest`

### Medium Priority:
3. **SessionRepository** - Session persistence
4. **ContextPanel** - Context sidebar
5. **EntityManager** - Entity management
6. **BranchesPage** - Branch visualization

---

## Summary

**RPClientApp is the user interface:**
1. Creates session repository for chat history
2. Builds UI with tabs and components
3. Connects to Bridge via SocketClient (IPC)
4. Loads chat history from session
5. Handles user input and streaming responses
6. Routes messages to/from Bridge

**Service Count:**
- 4 core services (paths, logger, session state, session repo)
- 7+ UI components
- 1 IPC client

**Communication Flow:**
```
User Input (Ctrl+Enter)
  → action_submit_message()
    → ipc_client.send_request_async(SEND_MESSAGE)
      → Bridge processes message
        → Streaming chunks arrive
          → _handle_streaming_chunk()
            → ChatDisplay updates
        → Final response arrives
          → _handle_llm_response()
```

---

**Analysis Complete:** Phase 1.3 - TUI Application Initialization
**Next Step:** Phase 1.4 - Build complete runtime call graph
