# Launch.py Execution Flow

**File:** `refactoring/launch.py` (528 lines)
**Purpose:** Main entry point - Manages RP selection, starts Bridge service, launches TUI application
**Entry Point:** `if __name__ == "__main__":` (line 525)

---

## Imports

### Standard Library
- `argparse` (line 14) - CLI argument parsing
- `multiprocessing` (line 15) - Bridge subprocess management
- `shutil` (line 16) - File operations (unused in main flow)
- `sys` (line 17) - System operations, path manipulation
- `time` (line 18) - Delays and timing
- `pathlib.Path` (line 19) - Path handling
- `socket` (line 93, inside function) - Socket operations for bridge checking
- `datetime` (line 48, inside function) - Logging timestamps
- `logging` (line 410) - Logging configuration (minimal usage)

### Application Imports
- `src.presentation.bridge.bridge_service.BridgeService` (line 25) → **CRITICAL: Bridge service class**
- `src.presentation.tui.app.RPClientApp` (line 26) → **CRITICAL: TUI application class**
- `src.presentation.tui.screens.rp_selection_screen.RPSelectionScreen` (line 27) → RP selection UI
- `textual.app.App` (line 28) → Base class for launcher app
- `src.infrastructure.ipc.SocketClient` (line 94, inside function) → IPC client for bridge communication
- `src.infrastructure.ipc.IPCMessageType` (line 94, inside function) → IPC message types
- `src.infrastructure.sessions.SessionStateService` (line 295, inside function) → Session initialization
- `src.shared.logging_service.get_logger` (line 296, inside function) → Logging utility

---

## Main Function Flow

### Entry Point: `if __name__ == "__main__":` (lines 525-528)

```python
multiprocessing.freeze_support()  # Windows multiprocessing compatibility
main()                             # Jump to main function
```

### `main()` Function (lines 330-523)

#### Step 1: Parse Arguments (lines 332-363)
- Creates `argparse.ArgumentParser`
- Arguments:
  - `rp_dir` (optional) - Specific RP directory path
  - `--host` (default: 127.0.0.1) - Bridge host
  - `--port` (default: 5555) - Bridge port
  - `--bridge-only` - Start only Bridge (no TUI)
  - `--tui-only` - Start only TUI (Bridge separate)
- Calls `parser.parse_args()` → `args` object

#### Step 2: Determine RP Directory (lines 365-402)
**Path A: RP directory provided via CLI** (lines 366-377)
- Validates: `rp_dir.exists()`
- Validates: `(rp_dir / "state").exists()`
- Exits with error if invalid

**Path B: No RP provided - show selection UI** (lines 378-402)
1. Sets `base_dir = project_root / "RPs"` (line 380)
2. Creates `base_dir` if doesn't exist (lines 383-385)
3. **Instantiates:** `RPLauncherApp(base_dir, args.host, args.port)` (line 392)
   - → Go to **Class: RPLauncherApp** analysis below
4. Calls `launcher.run()` (line 393) - **BLOCKS until user selects RP**
5. Retrieves: `launcher.selected_rp_path` (line 397)
6. Exits if no RP selected (lines 400-402)

#### Step 3: Set Up Logging (lines 404-448)
1. Creates `log_dir = rp_dir / "logs"` (line 405)
2. Creates log file: `logs/launcher.log` (line 407)
3. **Instantiates:** `TeeLogger` class (lines 414-435)
   - Redirects stdout to both console and file
   - Writes header with timestamp
4. Redirects `sys.stdout` to TeeLogger (line 439)
5. Prints launcher banner (lines 441-448)

#### Step 4: Execute Operating Mode (lines 450-522)

**Mode 1: Bridge Only** (lines 453-457)
- Calls `run_bridge(rp_dir, args.host, args.port)` directly (line 456)
- → Go to **Function: run_bridge()** below
- **BLOCKS until interrupted** (bridge runs in main thread)
- Returns after bridge stops

**Mode 2: TUI Only** (lines 459-468)
- Assumes Bridge running externally
- **Instantiates:** `RPClientApp(rp_dir, args.host, args.port)` (line 466)
  - → Go to **1.3: TUI Application Trace** (pending)
- Calls `app.run()` (line 467) - **BLOCKS until TUI exits**
- Returns after TUI exits

**Mode 3: Both Bridge and TUI** (lines 470-496) **[DEFAULT PATH]**
1. **Starts Bridge Process** (lines 474-480)
   - Creates: `multiprocessing.Process(target=run_bridge, args=(...), daemon=True)`
   - Calls: `bridge_process.start()` (line 480)
   - → Bridge runs in background subprocess
   - → Go to **Function: run_bridge()** below

2. **Waits for Bridge Ready** (lines 482-489)
   - Calls: `wait_for_bridge(args.host, args.port, timeout=10)` (line 484)
   - → Go to **Function: wait_for_bridge()** below
   - Exits with error if Bridge not ready within 10 seconds

3. **Starts TUI** (lines 491-496)
   - Brief pause (0.5s) for user visibility
   - **Instantiates:** `RPClientApp(rp_dir, args.host, args.port)` (line 495)
     - → Go to **1.3: TUI Application Trace** (pending)
   - Calls: `app.run()` (line 496)
   - **BLOCKS until TUI exits**

#### Step 5: Cleanup (lines 498-522)
- Catches: `KeyboardInterrupt`, `Exception`
- **Finally block** (lines 504-522):
  1. Terminates bridge process (if alive)
  2. Waits max 2 seconds
  3. Force kills if still alive
  4. Closes TeeLogger
  5. Restores original stdout

---

## Objects Instantiated in Main Execution Path

### 1. `RPLauncherApp(base_dir, host, port)` (line 392)
- **File:** `src/presentation/tui/screens/rp_selection_screen.py`
- **Purpose:** Shows RP selection TUI, returns selected RP
- **Parent:** `textual.app.App`
- **Methods Used:**
  - `run()` (line 393) - Blocks until RP selected
  - `selected_rp_path` (property, line 397) - Retrieves selection
- **→ Trace Needed:** See Class Analysis below

### 2. `TeeLogger(launcher_log_file)` (line 439)
- **Defined:** Lines 414-435 (inner class)
- **Purpose:** Dual-stream stdout (console + file)
- **Methods:**
  - `write(message)` - Writes to both streams
  - `flush()` - Flushes both streams
  - `close()` - Closes file handle

### 3. `multiprocessing.Process(...)` (line 475)
- **Standard Library Class**
- **Target:** `run_bridge` function
- **Args:** `(rp_dir, args.host, args.port)`
- **Daemon:** True (terminates when main process exits)

### 4. `RPClientApp(rp_dir, host, port)` (lines 466, 495)
- **File:** `src/presentation/tui/app.py`
- **Purpose:** Main TUI application
- **Methods Used:**
  - `run()` - Blocks until app exits
- **→ Trace Needed:** Go to **EXECUTION_FLOW_3_TUI.md** (Phase 1.3)

---

## Functions Called

### `run_bridge(rp_dir, host, port)` (lines 31-79)

**Purpose:** Runs Bridge service in subprocess (or main thread if bridge-only mode)

**Flow:**
1. Creates: `log_dir = rp_dir / "logs"` (line 40)
2. Creates: `log_file = log_dir / "bridge.log"` (line 42)
3. Opens log file for append (line 46)
4. Writes header with timestamp (lines 47-54)
5. **Redirects stdout/stderr to log file** (lines 57-60)
6. **Instantiates:** `BridgeService(rp_dir, host, port)` (line 64)
   - **→ CRITICAL: Go to EXECUTION_FLOW_2_BRIDGE.md (Phase 1.2)**
7. Calls: `bridge.run()` (line 65)
   - **BLOCKS until bridge shutdown**
8. Catches: `KeyboardInterrupt`, `Exception`
9. Restores stdout/stderr (lines 73-75)

**Called From:**
- Line 456 (bridge-only mode) - main thread
- Line 475 (default mode) - subprocess target

---

### `wait_for_bridge(host, port, timeout=10)` (lines 82-131)

**Purpose:** Waits for Bridge socket to be available AND responding to requests

**Flow:**
1. **Phase 1: Wait for socket** (lines 99-110)
   - Attempts socket connection every 0.5s
   - Timeout after `timeout` seconds
   - Returns `False` if socket not available

2. **Brief pause** (line 113)
   - 1 second delay for Bridge initialization

3. **Phase 2: Verify Bridge responding** (lines 116-130)
   - **Instantiates:** `SocketClient(host, port)` (line 121)
   - Calls: `client.connect()` (line 122)
   - Sends: `IPCMessageType.PING` request (line 123)
   - Checks: `response.success` (line 126)
   - Retries until timeout
   - Returns `True` if ping successful, `False` otherwise

**Imports Used:**
- `socket` (standard library)
- `src.infrastructure.ipc.SocketClient` (line 94)
- `src.infrastructure.ipc.IPCMessageType` (line 94)

**Called From:**
- Line 484 (default mode - verifies Bridge ready before TUI)

---

### `find_rp_folders(base_dir)` (lines 172-185)

**Purpose:** Scans directory for valid RP folders (must have `state/` subdirectory)

**Flow:**
1. Iterates: `base_dir.iterdir()`
2. Checks: `item.is_dir() and (item / "state").exists()`
3. Returns: `sorted(rp_folders, key=lambda p: p.name.lower())`

**Returns:** `list[Path]`

**Called From:**
- Not called in main() directly
- **Likely called by:** `RPSelectionScreen` or `select_rp_folder`

---

### `select_rp_folder(rp_folders, base_dir)` (lines 188-217)

**Purpose:** Console-based RP folder selection (fallback if GUI not used)

**Flow:**
1. Prints numbered list of RP folders
2. Offers option to create new RP
3. Gets user input (number)
4. Returns selected folder OR calls `create_new_rp()`

**Returns:** `Path | None`

**Called From:**
- Not directly called in current main() flow
- **Likely legacy code** - replaced by `RPLauncherApp`

---

### `create_new_rp(base_dir)` (lines 220-327)

**Purpose:** Interactive RP creation wizard

**Flow:**
1. Prompts for RP name (lines 235-239)
2. Checks if exists (lines 244-255)
3. Creates directory structure (lines 263-268):
   - `state/`
   - `config/`
   - `characters/`
   - `entities/`
   - `logs/`
4. Creates files (lines 271-292):
   - `config/config.json` - minimal config
   - `state/current_state.md` - initial state
   - `state/session_triggers.json` - empty array
   - `state/response_counter.json` - counter at 0
5. **Instantiates:** `SessionStateService(logger)` (line 299)
6. Calls: `session_service.initialize_session_state(rp_dir, rp_title, session_id="main")` (lines 300-304)
   - **→ Trace Needed:** Session initialization
7. Returns: `Path` (new RP directory) or `None` on error

**Called From:**
- Line 212 (from `select_rp_folder()`)
- **Potentially:** From `RPSelectionScreen` (GUI)

---

## Class: RPLauncherApp (lines 134-169)

**Parent:** `textual.app.App`
**Purpose:** Thin wrapper app that displays RP selection screen

### Constructor: `__init__(base_dir, host, port)` (lines 141-153)
- Calls: `super().__init__()`
- Stores: `self.base_dir = base_dir`
- Stores: `self.host = host`
- Stores: `self.port = port`
- Initializes: `self.selected_rp_path = None`

### `on_mount()` (lines 155-157)
- **Instantiates:** `RPSelectionScreen(self.base_dir)` (line 157)
- Calls: `self.push_screen(screen, callback=self.handle_rp_selection)`
- **→ Trace Needed:** `RPSelectionScreen` implementation

### `handle_rp_selection(rp_path)` (lines 159-169)
- Called when: `RPSelectionScreen` returns result
- Sets: `self.selected_rp_path = rp_path` (if not None)
- Calls: `self.exit()` - terminates launcher app

---

## Files Accessed

### Read/Created by Launch.py:
- `{project_root}/RPs/` - RP storage directory (created if missing)
- `{rp_dir}/logs/` - Log directory (created)
- `{rp_dir}/logs/launcher.log` - Launcher log (append mode)
- `{rp_dir}/logs/bridge.log` - Bridge log (append mode, via `run_bridge()`)

### Created by `create_new_rp()`:
- `{rp_dir}/state/`
- `{rp_dir}/config/`
- `{rp_dir}/characters/`
- `{rp_dir}/entities/`
- `{rp_dir}/logs/`
- `{rp_dir}/config/config.json`
- `{rp_dir}/state/current_state.md`
- `{rp_dir}/state/session_triggers.json`
- `{rp_dir}/state/response_counter.json`
- Session state files (via `SessionStateService`)

---

## Next Traces Required

### Phase 1.2: BridgeService Initialization
- **File:** `src/presentation/bridge/bridge_service.py`
- **Line:** 64 in launch.py
- **Constructor:** `BridgeService(rp_dir, host, port)`
- **Method:** `bridge.run()`

### Phase 1.3: TUI Application Initialization
- **File:** `src/presentation/tui/app.py`
- **Lines:** 466, 495 in launch.py
- **Constructor:** `RPClientApp(rp_dir, host, port)`
- **Method:** `app.run()`

### Conditional Traces (Lower Priority):
- `RPSelectionScreen` (called by RPLauncherApp)
- `SessionStateService.initialize_session_state()` (called by create_new_rp)
- `SocketClient` (used in wait_for_bridge)

---

## Summary

**Launch.py is the orchestrator:**
1. Parses arguments or shows RP selection UI
2. Validates/creates RP directory
3. Starts Bridge service in background process
4. Waits for Bridge to be ready (PING test)
5. Starts TUI application (blocks until exit)
6. Cleans up Bridge process on exit

**Critical Dependencies:**
- `BridgeService` - Backend service (Phase 1.2)
- `RPClientApp` - Frontend TUI (Phase 1.3)
- `SessionStateService` - Session initialization (trace if needed)
- `SocketClient` - IPC communication (trace if needed)

**Operating Modes:**
- **Default:** Bridge + TUI (multiprocess)
- **Bridge-only:** Bridge in main thread (for debugging)
- **TUI-only:** Assumes external Bridge (for debugging)

---

**Analysis Complete:** Phase 1.1 - Entry Point
**Next Step:** Phase 1.1 - Read start_bridge.py and start_tui.py
