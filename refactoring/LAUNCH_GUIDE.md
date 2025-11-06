# RP Client - Launch Guide

**Quick Start:** Run `launch.bat` or `python launch.py` to start everything!

## Prerequisites

Make sure you have installed:
```bash
pip install -r requirements-dev.txt
```

This includes:
- `textual` - TUI framework
- `requests` - HTTP client
- Other dependencies

## Launch Options

### Option 1: Start Everything (Recommended)

Start both Bridge and TUI together:

**Windows:**
```bash
launch.bat
```

**Linux/Mac or Python:**
```bash
python launch.py
```

Optionally specify RP directory:
```bash
python launch.py path/to/your/rp
```

### Option 2: Bridge Only

Useful for testing or running TUI separately:

**Windows:**
```bash
launch_bridge.bat
```

**Python:**
```bash
python launch.py --bridge-only
```

### Option 3: TUI Only

If Bridge is already running in another terminal:

**Windows:**
```bash
launch_tui.bat
```

**Python:**
```bash
python launch.py --tui-only
```

### Custom Host/Port

```bash
python launch.py --host 0.0.0.0 --port 5556 path/to/rp
```

## What Happens When You Launch

1. **Bridge Process Starts**
   - Loads configuration from RP directory
   - Initializes automation services
   - Starts socket server on localhost:5555
   - Ready to receive commands from TUI

2. **Launcher Waits**
   - Checks if Bridge is ready (max 10 seconds)
   - Retries every 0.5 seconds
   - Shows error if Bridge fails to start

3. **TUI Starts**
   - Connects to Bridge via socket
   - Displays chat interface
   - Ready for user input

4. **On Exit**
   - TUI closes cleanly
   - Bridge process terminates
   - All connections cleaned up

## Keyboard Shortcuts (TUI)

- **Ctrl+Enter** - Send message
- **Ctrl+Q / Ctrl+C** - Quit application
- **F1** - Show help
- **F2** - Toggle settings panel

## Settings Panel (F2)

- **Provider Selector** - Switch between LLM providers (Claude, OpenAI, etc.)
- **Testing Mode** - Enable mock LLM for testing without API calls
- **WIP Mode** - Enable WIP module testing (advanced)

## Troubleshooting

### Bridge Fails to Start

**Error:** "Bridge failed to start within 10 seconds"

**Solutions:**
1. Check if port 5555 is already in use:
   ```bash
   # Windows
   netstat -ano | findstr :5555

   # Linux/Mac
   lsof -i :5555
   ```

2. Try a different port:
   ```bash
   python launch.py --port 5556
   ```

3. Check for errors in Bridge output (shown above error message)

### TUI Won't Connect

**Error:** Connection refused or timeout

**Solutions:**
1. Make sure Bridge is running (try `--bridge-only` first)
2. Check host/port match between Bridge and TUI
3. Check firewall settings
4. Try restarting both

### Import Errors

**Error:** ModuleNotFoundError

**Solution:**
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Or install missing package directly
pip install textual requests
```

### RP Directory Not Found

**Error:** "RP directory does not exist"

**Solution:**
```bash
# Specify valid RP directory
python launch.py C:\path\to\your\rp

# Or run from within RP directory
cd C:\path\to\your\rp
python C:\path\to\refactoring\launch.py
```

## Testing Without RP Directory

You can test with a minimal RP directory:

```bash
# Create test RP
mkdir test_rp
cd test_rp
mkdir config state characters

# Create minimal config
echo '{"version": "2.0.0"}' > config/config.json

# Launch
python ../refactoring/launch.py .
```

## Advanced Usage

### Development Mode

Run Bridge and TUI in separate terminals for easier debugging:

**Terminal 1 (Bridge):**
```bash
python launch.py --bridge-only
```

**Terminal 2 (TUI):**
```bash
python launch.py --tui-only
```

This way you can see Bridge logs without TUI obscuring them.

### Custom Configuration

The Bridge automatically loads configuration from the RP directory:
- `config/config.json` - Main configuration
- `config/.env` - Environment variables (API keys, etc.)
- `config/defaults.py` - Default fallbacks

### WIP Module Testing

See `docs/WIP_TESTING_SYSTEM.md` for details on testing new implementations.

Quick example:
1. Enable testing mode (F2)
2. Copy module to `src/wip/`
3. Send TEST_MODE command with wip_action
4. See production vs WIP comparison

## Files Created

- `launch.py` - Main launcher script (Python)
- `launch.bat` - Windows launcher (both Bridge and TUI)
- `launch_bridge.bat` - Windows Bridge-only launcher
- `launch_tui.bat` - Windows TUI-only launcher
- `LAUNCH_GUIDE.md` - This file

## Architecture Overview

```
┌─────────────────┐
│   launch.py     │
│   (Launcher)    │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         v                  v
┌─────────────────┐  ┌──────────────────┐
│  Bridge Process │  │   TUI Process    │
│  (Background)   │  │   (Foreground)   │
└────────┬────────┘  └────────┬─────────┘
         │                    │
         │   Socket IPC       │
         │   (localhost:5555) │
         └────────────────────┘
```

## Next Steps

1. **Test the launcher:**
   ```bash
   python launch.py
   ```

2. **Try sending a message** via TUI

3. **Toggle testing mode** (F2) to test without API calls

4. **Explore settings** (F2) - switch providers, enable WIP mode

5. **Check the WIP system** - See `docs/WIP_TESTING_SYSTEM.md`

For issues or questions, see the test files in `tests/` or the comprehensive documentation in `docs/`.
