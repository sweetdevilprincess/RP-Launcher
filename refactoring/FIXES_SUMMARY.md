# TUI and Bridge Fixes Summary

## Date: 2025-10-24

## Issues Fixed

### 1. Missing SDK Toggle Switch Widget
**Problem**: The LLM settings page code referenced a `#use-sdk` Switch widget that didn't exist in the UI, causing errors when trying to load/apply settings.

**Files Changed**:
- `src/presentation/tui/components/llm_settings_page.py:183-185`

**Changes Made**:
```python
# Added missing Switch widget
yield Label("Use Claude SDK (for Anthropic only):")
yield Switch(id="use-sdk", value=False)
yield Static("Enable SDK mode - no API key needed, uses local Claude SDK bridge", classes="section-description")
```

---

### 2. SDK Still Requesting API Key
**Problem**: The SDK option was listed as a separate provider ("Claude SDK"), but users still saw API key fields, creating confusion since the SDK doesn't need an API key.

**Files Changed**:
- `src/presentation/tui/components/llm_settings_page.py:170-184`

**Changes Made**:
1. Removed "Claude SDK" from provider dropdown (it was "claude_sdk_client")
2. Kept only "Anthropic (Claude)" as single Anthropic option
3. Added SDK toggle switch to control API vs SDK mode
4. Updated placeholder text: `"Enter your API key (not needed for SDK)"`

**Before**:
```python
("Claude SDK", "claude_sdk_client"),  # Separate option
("Anthropic (API)", "claude_api_client"),
```

**After**:
```python
("Anthropic (Claude)", "claude_api_client"),  # Single option
# SDK toggle controls whether to use SDK or API
```

---

### 3. Settings Not Saving Properly
**Problem**: Changes to settings (especially the SDK toggle) weren't being persisted to the config file.

**Files Changed**:
- `src/presentation/tui/components/llm_settings_page.py:354-359` (Added Switch handler)
- `src/presentation/tui/components/llm_settings_page.py:373-385` (Updated save method)

**Changes Made**:

**Added Switch change handler**:
```python
def on_switch_changed(self, event: Switch.Changed) -> None:
    """Handle switch toggle changes."""
    switch_id = event.switch.id
    if switch_id == "use-sdk":
        self.settings["use_sdk"] = event.value
        self.post_message(self.SettingsChanged("use_sdk", str(event.value)))
```

**Updated save method to include SDK toggle**:
```python
def save_all_settings(self) -> None:
    # ...
    use_sdk_switch = self.query_one("#use-sdk", Switch)

    self.settings = {
        "provider": provider,
        "use_sdk": use_sdk_switch.value,  # Now saved!
        # ... other settings
    }
```

---

### 4. Bridge Not Using SDK When Enabled
**Problem**: Even when `use_sdk` was saved to config, the bridge didn't check this flag and still tried to use the API client.

**Files Changed**:
- `src/presentation/bridge/bridge_service.py:164-171`

**Changes Made**:

**Added SDK flag check in LLM client initialization**:
```python
def _initialize_llm_client(self, provider_name: Optional[str] = None) -> None:
    # ... existing code ...

    # Check if Claude API client has use_sdk enabled
    config = self.config_loader.load()
    if provider_name == "claude_api_client":
        claude_config = config.get("modules", {}).get("claude_api_client", {}).get("config", {})
        use_sdk = claude_config.get("use_sdk", False)
        if use_sdk:
            provider_name = "claude_sdk_client"
            print("[SDK] use_sdk enabled - switching to claude_sdk_client")

    # ... continue with provider initialization ...
```

**How It Works**:
1. Bridge loads config on startup
2. Checks if selected provider is `claude_api_client`
3. Reads `use_sdk` flag from that provider's config
4. If `True`, switches provider to `claude_sdk_client`
5. Instantiates the appropriate client

---

## New Files Created

### 1. `test_fixes.py`
A comprehensive test script that verifies:
- Bridge connectivity
- Settings loading
- Settings saving
- SDK toggle persistence
- Settings restoration

**Usage**:
```bash
python test_fixes.py
```

### 2. `SETUP_AND_USAGE_GUIDE.md`
Complete guide covering:
- How to start the system (3 different methods)
- How to configure LLM settings
- Testing procedures
- Troubleshooting common issues
- Architecture overview
- Settings flow diagrams

### 3. `FIXES_SUMMARY.md` (This File)
Quick reference for all changes made.

---

## How to Use the SDK Toggle

### Setting Up SDK Mode

1. **Start the Bridge**:
   ```batch
   launch_bridge.bat
   ```

2. **Start the TUI**:
   ```batch
   launch_tui.bat
   ```

3. **Configure Settings**:
   - Navigate to "⚙️ Settings" tab (or press F8)
   - Set "API Provider" to "Anthropic (Claude)"
   - Toggle "Use Claude SDK" to ON
   - Click "💾 Save Settings"

4. **Restart Bridge**:
   - Close bridge (Ctrl+C)
   - Restart: `launch_bridge.bat`
   - You should see: `[SDK] use_sdk enabled - switching to claude_sdk_client`

### Switching Back to API Mode

1. Open TUI Settings
2. Toggle "Use Claude SDK" to OFF
3. Enter your Anthropic API key
4. Click "💾 Save Settings"
5. Restart the bridge

---

## Config File Changes

The `use_sdk` flag is now saved in the config file:

**Location**: `<RP_DIR>/config.json`

**Example**:
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
        "use_sdk": true    ← This flag controls SDK vs API mode
      }
    }
  }
}
```

---

## Testing Checklist

- [✓] Bridge starts without errors
- [✓] TUI connects to bridge successfully
- [✓] Settings page loads without crashes
- [✓] SDK toggle switch is visible
- [✓] SDK toggle can be changed and saved
- [✓] Settings persist across bridge restarts
- [✓] Bridge switches to SDK client when flag is enabled
- [✓] Bridge uses API client when flag is disabled
- [✓] Test script passes all checks

---

## Before vs After

### Before
- ❌ Missing SDK switch widget → crash on settings load
- ❌ Confusing provider options (Claude SDK vs Claude API)
- ❌ API key always required, even for SDK
- ❌ Settings changes not persisted
- ❌ Bridge didn't respect use_sdk flag

### After
- ✅ SDK switch widget properly defined
- ✅ Single "Anthropic (Claude)" provider option
- ✅ SDK toggle clearly indicates "no API key needed"
- ✅ Settings saved to config.json
- ✅ Bridge automatically switches to SDK when enabled
- ✅ Test script to verify everything works
- ✅ Comprehensive documentation

---

## Next Steps for Users

1. **Run the test script**: `python test_fixes.py`
2. **Read the setup guide**: `SETUP_AND_USAGE_GUIDE.md`
3. **Start using the TUI**: `launch.bat`
4. **Configure your provider**: Settings tab → Choose provider → Save
5. **Start roleplaying**: Chat tab → Send messages

---

## Technical Notes

### Why These Changes Were Needed

1. **Separation of Concerns**: The provider (Anthropic) should be separate from the transport mechanism (API vs SDK)
2. **User Experience**: Users shouldn't need to know about internal implementation details
3. **Configuration**: Settings should persist so users don't have to reconfigure every time
4. **Flexibility**: Easy to switch between API and SDK mode without changing provider

### Design Decisions

1. **SDK as a Toggle, Not a Provider**: Makes it clear that SDK is just an alternative way to use Claude
2. **Single Source of Truth**: Config file is the authoritative source for settings
3. **Bridge Handles Switching**: TUI doesn't need to know about SDK vs API implementation details
4. **Graceful Degradation**: If SDK isn't available, falls back to API client

---

**Summary**: All reported issues have been fixed. The TUI now properly supports toggling between Claude API and Claude SDK modes, with settings persisting correctly across sessions.
