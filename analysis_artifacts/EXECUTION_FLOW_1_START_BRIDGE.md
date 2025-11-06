# start_bridge.py Execution Flow

**File:** `refactoring/start_bridge.py` (22 lines)
**Purpose:** Standalone Bridge service starter (for debugging/testing)
**Entry Point:** `if __name__ == "__main__":` (line 6)

---

## Imports

### Standard Library
- `pathlib.Path` (line 3) - Path handling

### Application Imports
- `src.presentation.bridge.bridge_service.BridgeService` (line 4) → **CRITICAL: Bridge service class**

---

## Execution Flow

### `if __name__ == "__main__":` (lines 6-22)

**Hardcoded Configuration:**
- `rp_dir = Path("test_rps_output/Test Adventure")` (line 7)
  - **⚠️ HARDCODED** - Test RP path
  - Not production code - testing/debugging only

**Steps:**
1. Prints banner (lines 9-13)
2. **Instantiates:** `BridgeService(rp_dir, host="127.0.0.1", port=5555)` (line 15)
   - **→ Go to EXECUTION_FLOW_2_BRIDGE.md (Phase 1.2)**
3. Calls: `bridge.run()` (line 18)
   - **BLOCKS until interrupted**
4. Catches: `KeyboardInterrupt` (line 19)
5. Calls: `bridge.stop()` (line 21)

---

## Usage

This is a **test/debug script**, NOT a production entry point.

**Purpose:**
- Start Bridge service standalone (without TUI)
- Test Bridge functionality independently
- Debug Bridge issues

**Production Equivalent:**
- `launch.py --bridge-only <rp_dir>`

---

## Analysis

### Status: **DEBUG/TEST SCRIPT**

**Findings:**
- Simple wrapper around `BridgeService`
- Hardcoded test RP path
- No argument parsing
- No logging setup
- No error handling beyond KeyboardInterrupt

**Usage Pattern:**
- Developer runs this to test Bridge in isolation
- Not called by launch.py or any production code
- Likely used during development for quick Bridge testing

**Next Trace:**
- `BridgeService.__init__()` and `BridgeService.run()` (Phase 1.2)
