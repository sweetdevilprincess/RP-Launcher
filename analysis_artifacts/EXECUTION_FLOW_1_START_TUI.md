# start_tui.py Execution Flow

**File:** `refactoring/start_tui.py` (18 lines)
**Purpose:** Standalone TUI starter (for debugging/testing)
**Entry Point:** `if __name__ == "__main__":` (line 6)

---

## Imports

### Standard Library
- `pathlib.Path` (line 3) - Path handling

### Application Imports
- `src.presentation.tui.app.RPClientApp` (line 4) → **CRITICAL: TUI application class**

---

## Execution Flow

### `if __name__ == "__main__":` (lines 6-17)

**Hardcoded Configuration:**
- `rp_dir = Path("test_rps_output/Test Adventure")` (line 7)
  - **⚠️ HARDCODED** - Test RP path
  - Not production code - testing/debugging only
- `bridge_host = "127.0.0.1"` (line 16)
- `bridge_port = 5555` (line 16)

**Steps:**
1. Prints banner (lines 9-14)
2. **Instantiates:** `RPClientApp(rp_dir, bridge_host="127.0.0.1", bridge_port=5555)` (line 16)
   - **→ Go to EXECUTION_FLOW_3_TUI.md (Phase 1.3)**
3. Calls: `app.run()` (line 17)
   - **BLOCKS until TUI exits**

---

## Usage

This is a **test/debug script**, NOT a production entry point.

**Purpose:**
- Start TUI standalone (Bridge must be running separately)
- Test TUI functionality independently
- Debug TUI issues
- Pair with `start_bridge.py` for two-terminal debugging

**Production Equivalent:**
- `launch.py --tui-only <rp_dir>`

---

## Analysis

### Status: **DEBUG/TEST SCRIPT**

**Findings:**
- Simple wrapper around `RPClientApp`
- Hardcoded test RP path
- Assumes Bridge already running on 127.0.0.1:5555
- No argument parsing
- No logging setup
- No error handling

**Usage Pattern:**
- Developer runs `start_bridge.py` in one terminal
- Developer runs `start_tui.py` in another terminal
- Allows debugging Bridge and TUI separately
- Not called by launch.py or any production code

**Next Trace:**
- `RPClientApp.__init__()` and `RPClientApp.run()` (Phase 1.3)
