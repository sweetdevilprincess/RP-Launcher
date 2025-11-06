# How to Start the TUI

## Step 1: Start the Bridge (Terminal 1)

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python start_bridge.py
```

**You should see:**
```
============================================================
Starting Bridge Service
============================================================
RP Directory: C:\Users\green\Desktop\RP Claude Code\refactoring\test_rps_output\Test Adventure

[START] Starting Bridge Service...
[INFO] RP Directory: test_rps_output\Test Adventure
[CONFIG] Loading configuration...
[OK] Configuration loaded (version: 2.0.0)
[SERVICES] Initializing core services...
[SERVICES] Services initialized
[SOCKET] Starting IPC server on 127.0.0.1:5555...
[OK] IPC Server listening on 127.0.0.1:5555
[OK] Bridge Service ready
```

**If config.json doesn't exist**, it will create it automatically.

**Leave this terminal running!**

---

## Step 2: Start the TUI (Terminal 2)

In a **NEW** terminal:

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python start_tui.py
```

**You should see the TUI launch.**

---

## What Gets Created

When the bridge starts for the first time, it creates:

1. **config.json** - Contains all module configurations
2. **state/session.json** - Session state and timelines (if doesn't exist)

---

## Troubleshooting

### Bridge won't start

Check that the RP directory exists:
```bash
ls "test_rps_output/Test Adventure"
```

### TUI shows "Not connected to Bridge"

1. Make sure Bridge is running (see Terminal 1)
2. Check it says "[OK] Bridge Service ready"
3. Restart the TUI

### Modules page is empty

1. Stop both Bridge and TUI
2. Check if `config.json` was created: `ls "test_rps_output/Test Adventure/config.json"`
3. If not, the bridge didn't start properly
4. Start bridge again and watch for errors

### SDK toggle error

This should be fixed now. If you still see it:
1. Stop both services
2. Delete config.json: `rm "test_rps_output/Test Adventure/config.json"`
3. Start bridge (it will recreate config.json with correct defaults)
4. Start TUI

---

## What Should Work Now

After following these steps:

✅ **Modules Page** - Should show all 13 modules with toggle switches
✅ **Settings Page** - Provider dropdown should be readable, SDK toggle should work
✅ **Entities Page** - Should load entities from entities/ directory
✅ **Branches Page** - Should show timeline branches

---

## Files Created by This Guide

- `start_bridge.py` - Simple bridge launcher
- `start_tui.py` - Simple TUI launcher
- `test_bridge_connection.py` - Test script to verify IPC

---

**Next:** Once both are running, navigate to the Modules tab in the TUI to verify modules appear.
