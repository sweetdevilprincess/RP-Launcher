# Quick Start Checklist

## ✓ Step-by-Step Guide to Get Running

### 1. Verify the Fixes
- [ ] Read `FIXES_SUMMARY.md` to understand what was changed
- [ ] Review `SETUP_AND_USAGE_GUIDE.md` for detailed instructions

### 2. Test the Bridge Connection

**Option A: Automated Test**
```bash
# Terminal 1: Start the bridge
launch_bridge.bat

# Terminal 2: Run the test
python test_fixes.py
```

**Option B: Manual Test**
```bash
# Terminal 1: Start the bridge
launch_bridge.bat

# Terminal 2: Test connection
python test_bridge_connection.py
```

- [ ] Bridge starts without errors
- [ ] Test script shows "ALL TESTS PASSED"
- [ ] Settings load successfully
- [ ] Settings save successfully

### 3. Start the TUI

**Easy Mode (Recommended)**:
```bash
launch.bat
```
This starts both bridge and TUI automatically.

**Manual Mode**:
```bash
# Terminal 1: Bridge
launch_bridge.bat

# Terminal 2: TUI
launch_tui.bat
```

- [ ] TUI launches successfully
- [ ] TUI connects to bridge (check footer for connection status)
- [ ] No error messages in TUI or bridge console

### 4. Configure Settings

1. **Open Settings**:
   - [ ] Click "⚙️ Settings" tab OR press `F8`

2. **Configure Your Provider**:

   **For Claude SDK (no API key needed)**:
   - [ ] Set "API Provider" to "Anthropic (Claude)"
   - [ ] Toggle "Use Claude SDK" to ON (should show green)
   - [ ] Note the helper text: "no API key needed"
   - [ ] Click "💾 Save Settings"
   - [ ] Wait for "Settings saved" notification

   **For Claude API (requires API key)**:
   - [ ] Set "API Provider" to "Anthropic (Claude)"
   - [ ] Toggle "Use Claude SDK" to OFF (should show gray)
   - [ ] Enter your Anthropic API key in "API Key" field
   - [ ] Click "💾 Save Settings"
   - [ ] Wait for "Settings saved" notification

   **For OpenAI/Other Providers**:
   - [ ] Select your provider from dropdown
   - [ ] SDK toggle will have no effect (Anthropic only)
   - [ ] Enter your API key
   - [ ] Click "💾 Save Settings"

### 5. Verify Settings Persisted

1. **Restart the Bridge**:
   - [ ] Stop bridge (Ctrl+C in bridge terminal)
   - [ ] Restart: `launch_bridge.bat`

2. **Check Bridge Console**:
   - [ ] If SDK enabled, you should see: `[SDK] use_sdk enabled - switching to claude_sdk_client`
   - [ ] If SDK disabled, you should see: `[OK] LLM client initialized: claude_api_client`

3. **Restart TUI and Check Settings**:
   - [ ] Close TUI (Ctrl+Q)
   - [ ] Restart: `launch_tui.bat`
   - [ ] Go to Settings tab
   - [ ] Verify SDK toggle is in the same state you saved

### 6. Test Chat Functionality (Optional)

1. **Go to Chat Tab**:
   - [ ] Click "💬 Chat" tab
   - [ ] Type a test message in the input area
   - [ ] Press Ctrl+Enter to send

2. **Verify Response**:
   - [ ] Message appears in chat display
   - [ ] You see "⏳ Sending message..." status
   - [ ] Response appears from Claude
   - [ ] No error messages

### 7. Explore Other Features

- [ ] Try the "🎭 Entities" tab
- [ ] Check out "🌳 Branches" tab
- [ ] Explore "🔧 Modules" tab
- [ ] Read "❓ Help" tab for keyboard shortcuts
- [ ] Check "📊 Status" tab for system info

---

## Troubleshooting Quick Reference

### Bridge Won't Start
1. Check if port 5555 is already in use: `netstat -ano | findstr :5555`
2. Verify RP directory has `state/` folder
3. Check console for Python errors

### TUI Can't Connect
1. Make sure bridge is running first
2. Wait 10-15 seconds for bridge to fully initialize
3. Check firewall isn't blocking localhost:5555

### Settings Not Saving
1. Verify you clicked "💾 Save Settings" button
2. Check bridge console for errors
3. Verify config file permissions in RP directory
4. Make sure bridge is running when you save

### SDK Mode Not Working
1. Verify SDK toggle is ON and saved
2. Restart the bridge
3. Check for `[SDK] use_sdk enabled` message in bridge console
4. Check `config.json` file for `"use_sdk": true`

---

## Success Indicators

You'll know everything is working when:

✅ Bridge starts and shows: `[OK] Bridge Service ready`
✅ TUI connects without errors
✅ Settings page loads and shows all widgets
✅ Settings can be saved and persist across restarts
✅ SDK toggle controls whether API key is required
✅ Chat messages can be sent and receive responses

---

## Where to Get Help

1. **Documentation**:
   - `SETUP_AND_USAGE_GUIDE.md` - Complete setup guide
   - `FIXES_SUMMARY.md` - What was fixed and why

2. **Test Scripts**:
   - `test_fixes.py` - Comprehensive automated test
   - `test_bridge_connection.py` - Manual bridge connection test

3. **Config Files**:
   - Check `<RP_DIR>/config.json` for current settings
   - Look at bridge console for initialization messages
   - Review TUI notifications for errors

---

## Common First-Time Setup

### Scenario 1: Using Claude SDK (Easiest)
1. Start bridge: `launch_bridge.bat`
2. Start TUI: `launch_tui.bat`
3. Go to Settings → Enable "Use Claude SDK" → Save
4. Restart bridge
5. Start chatting!

### Scenario 2: Using Claude API
1. Get API key from https://console.anthropic.com/
2. Start bridge: `launch_bridge.bat`
3. Start TUI: `launch_tui.bat`
4. Go to Settings → Disable "Use Claude SDK" → Enter API key → Save
5. Restart bridge
6. Start chatting!

### Scenario 3: Using OpenAI
1. Get API key from https://platform.openai.com/
2. Start bridge: `launch_bridge.bat`
3. Start TUI: `launch_tui.bat`
4. Go to Settings → Select "OpenAI" → Enter API key → Save
5. Restart bridge
6. Start chatting!

---

**Ready to go?** Start with `launch.bat` and follow the prompts! 🚀
