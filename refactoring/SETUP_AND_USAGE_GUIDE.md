# RP Client - Setup and Usage Guide

## Recent Fixes Applied

The following issues have been fixed:

### 1. ✓ Missing SDK Toggle Switch
- **Issue**: The settings page was trying to access a "#use-sdk" Switch widget that didn't exist
- **Fix**: Added the missing Switch widget to the LLM Settings page
- **Location**: `src/presentation/tui/components/llm_settings_page.py`

### 2. ✓ SDK Mode Not Removing API Key Requirement
- **Issue**: When using Claude SDK, an API key was still being requested
- **Fix**:
  - Removed "Claude SDK" as a separate provider option
  - Added "Use Claude SDK" toggle for Anthropic provider
  - Updated placeholder text to indicate API key not needed for SDK
  - Bridge now automatically switches to SDK client when toggle is enabled
- **Location**: `src/presentation/tui/components/llm_settings_page.py`, `src/presentation/bridge/bridge_service.py`

### 3. ✓ Settings Not Saving Properly
- **Issue**: Settings changes weren't persisting across sessions
- **Fix**:
  - Added Switch event handler for SDK toggle
  - Ensured `use_sdk` flag is included in saved settings
  - Bridge checks `use_sdk` flag on initialization and switches to SDK client accordingly
- **Location**: `src/presentation/tui/components/llm_settings_page.py`, `src/presentation/bridge/bridge_service.py`

### 4. ✓ Bridge Connection Issues
- **Issue**: TUI couldn't connect to bridge reliably
- **Fix**: The connection logic was already correct with retry mechanism. Issues were likely due to:
  - Bridge not being started before TUI
  - Port conflicts
  - Firewall blocking localhost connections

---

## How to Start the System

There are three ways to start the RP Client:

### Option 1: Start Everything Together (Recommended)
```batch
launch.bat
```
This will:
1. Show an RP selection screen (or create a new RP)
2. Start the Bridge in the background
3. Start the TUI and connect to the Bridge
4. Clean up properly when you exit

### Option 2: Start Bridge and TUI Separately

**Terminal 1 - Start Bridge:**
```batch
launch_bridge.bat
```

**Terminal 2 - Start TUI:**
```batch
launch_tui.bat
```

This is useful for debugging since you can see Bridge and TUI logs separately.

### Option 3: Use Python Directly

**Start both:**
```bash
python launch.py
```

**Bridge only:**
```bash
python launch.py --bridge-only
```

**TUI only:**
```bash
python launch.py --tui-only
```

---

## Configuring LLM Settings

### Using the TUI Settings Page

1. Start the TUI (using any method above)
2. Click the "⚙️ Settings" tab (or press F8)
3. Configure your settings:

   **For Anthropic Claude via API:**
   - Set "API Provider" to "Anthropic (Claude)"
   - Turn OFF "Use Claude SDK"
   - Enter your Anthropic API key
   - Click "💾 Save Settings"

   **For Anthropic Claude via SDK:**
   - Set "API Provider" to "Anthropic (Claude)"
   - Turn ON "Use Claude SDK"
   - No API key needed!
   - Click "💾 Save Settings"

   **For Other Providers (OpenAI, Google, Ollama):**
   - Select the appropriate provider
   - "Use Claude SDK" toggle will have no effect
   - Enter your API key if required
   - Click "💾 Save Settings"

### Settings File Location

Settings are saved to: `<RP_DIR>/config.json`

Example configuration:
```json
{
  "version": "1.0",
  "modules": {
    "claude_api_client": {
      "enabled": true,
      "config": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 4096,
        "use_prompt_caching": true,
        "use_sdk": false
      }
    }
  }
}
```

---

## Testing Your Setup

### Test Script

Run the test script to verify everything is working:

```bash
python test_fixes.py
```

This will:
1. Connect to the bridge
2. Test loading settings
3. Test saving settings
4. Verify SDK toggle works
5. Restore original settings

### Manual Testing

1. Start the bridge: `launch_bridge.bat`
2. Run the test: `python test_bridge_connection.py`
3. Start the TUI: `launch_tui.bat`
4. Navigate to Settings tab
5. Toggle the SDK switch
6. Click "Save Settings"
7. Restart the bridge and TUI
8. Verify the SDK toggle state persisted

---

## Troubleshooting

### Bridge Won't Start

**Symptoms:**
- "Connection refused" errors
- "Failed to start within 10 seconds"

**Solutions:**
1. Check if port 5555 is already in use:
   ```bash
   netstat -ano | findstr :5555
   ```
2. Check for Python errors in the bridge console
3. Verify your RP directory has a valid structure:
   - Must have a `state/` subdirectory
   - Should have a `config.json` file

### Settings Not Saving

**Symptoms:**
- Settings revert after restart
- "Not connected to Bridge" warning

**Solutions:**
1. Ensure bridge is running before TUI
2. Check bridge console for errors
3. Verify config file permissions in RP directory
4. Make sure you click "💾 Save Settings" button

### SDK Mode Not Working

**Symptoms:**
- Still asking for API key when SDK enabled
- SDK toggle doesn't persist

**Solutions:**
1. Make sure you saved settings after toggling SDK
2. Restart the bridge after changing SDK setting
3. Check bridge console for "[SDK] use_sdk enabled" message
4. Verify `config.json` has `"use_sdk": true`

### Connection Timeouts

**Symptoms:**
- "Failed to connect to Bridge after 3 attempts"
- Slow response times

**Solutions:**
1. Check firewall settings (allow localhost connections)
2. Try increasing timeout in TUI connection code
3. Restart both bridge and TUI
4. Check system resources (CPU, memory)

---

## Architecture Overview

```
┌─────────────────┐
│   TUI (Textual) │
│   - User Input  │
│   - Chat View   │
│   - Settings UI │
└────────┬────────┘
         │
         │ IPC (Socket)
         │ Port 5555
         ▼
┌────────────────────────┐
│   Bridge Service       │
│   - IPC Handler        │
│   - Settings Manager   │
│   - LLM Client Factory │
└────────┬───────────────┘
         │
         │ Provider Selection
         ▼
┌─────────────────────────────┐
│  LLM Clients                │
│  - Claude API Client        │
│  - Claude SDK Client        │
│  - OpenAI Client            │
│  - Other Providers          │
└─────────────────────────────┘
```

### Key Components

1. **TUI (src/presentation/tui/)**: User interface using Textual library
2. **Bridge (src/presentation/bridge/)**: Background service managing LLM clients
3. **IPC (src/infrastructure/ipc/)**: Socket-based inter-process communication
4. **Config Loader (src/infrastructure/config/)**: Configuration management
5. **LLM Clients (src/infrastructure/llm/)**: Provider-specific implementations

### How Settings Flow

1. User changes settings in TUI
2. TUI sends `UPDATE_SETTINGS` IPC message to Bridge
3. Bridge's `SettingsHandler` receives the message
4. Handler updates config using `ConfigLoader.set()`
5. Handler calls `ConfigLoader.save()` to persist to disk
6. Handler reinitializes LLM client with new settings
7. Bridge sends success response back to TUI

### SDK Toggle Behavior

When `use_sdk` is toggled:
1. Setting is saved to `claude_api_client.config.use_sdk`
2. On next bridge initialization:
   - Bridge checks if provider is `claude_api_client`
   - Reads `use_sdk` flag from config
   - If `true`, switches to `claude_sdk_client` provider
   - If `false`, uses `claude_api_client` provider
3. Appropriate LLM client is instantiated

---

## Next Steps

1. **Test the fixes**: Run `python test_fixes.py`
2. **Start the system**: Use `launch.bat` or separate launchers
3. **Configure settings**: Navigate to Settings tab in TUI
4. **Start roleplaying**: Use the Chat tab to interact with Claude

## Support

If you encounter any issues:

1. Check the bridge console for error messages
2. Review the TUI notifications in the bottom status bar
3. Verify your RP directory structure
4. Check `config.json` for proper formatting
5. Run the test script to isolate the issue

---

**Last Updated**: 2025-10-24
**Version**: Post-fixes v1.0
