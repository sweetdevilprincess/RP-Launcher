# TUI Quick Start Guide

## ⚡ 3-Minute Setup

### Step 1: Install Dependencies (First Time Only)
```bash
cd "C:\Users\green\Desktop\RP Claude Code"
pip install -r requirements.txt
```

### Step 2: Launch!

**🎯 EASIEST WAY - Just double-click:**
- `launch_rp_tui.bat`

That's it! Both the Bridge and TUI will open automatically!

---

## 📖 Manual Launch (Alternative)

If you prefer to launch manually:

### Open Two Terminals

**Terminal 1 (Bridge):**
```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python tui_bridge.py "Example RP"
```

**Terminal 2 (TUI):**
```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python rp_client_tui.py "Example RP"
```

### Step 3: Start RPing!

1. Type your message in the TUI (Enter for new lines)
2. Press `Ctrl+Enter` to send
3. Wait for Claude's response (appears automatically)
4. Continue the story!

---

## 🎯 Quick Reference While RPing

While typing, click footer buttons to check references:

**Example workflow:**
```
You're typing: "I confront Silas about the camera"
↓
Click "Memory" button - Check: Does Lilith know about cameras yet?
Click "Characters" button - Check: What's Silas's current state?
Click "Arc" button - Check: Is this the right story beat?
↓
Adjust your message based on what you learned
↓
Press Ctrl+Enter to send
```

---

## 📋 Full Keyboard Shortcuts

### Sending Messages:
- `Ctrl+Enter` - Send message
- `Enter` - New line in message (works naturally!)
- `Ctrl+Q` - Quit TUI
- `F1` - Help

### Quick Reference:
Use **footer buttons** at bottom of screen to open overlays:
- Memory, Arc, Characters, Notes, Entities, Genome, Status

### In Overlays:
- `ESC` - Close overlay
- `↑` / `↓` - Scroll up/down
- `PgUp` / `PgDn` - Page up/down

---

## 🎨 Screen Layout

```
┌─────────────────────────────────────────────────────────┐
│ 🎭 RP Client - Ch 23 | 11:30 PM | Apartment           │ ← Header
├──────────────┬──────────────────────────────────────────┤
│ 📍 CONTEXT   │  Chat History                            │
│              │  (Your messages + Claude's responses)    │
│ Chapter: 23  │                                          │
│ Time: 11:30  │  Scroll up to see previous messages      │
│ Location:    │                                          │
│  Apartment   │                                          │
│              │                                          │
│ 📊 PROGRESS  │                                          │
│ 217/250 resp │                                          │
│ ████████░ 87%│                                          │
│              │                                          │
│ 📖 QUICK     │                                          │
│    ACCESS    │                                          │
│ Ctrl+M  Mem  │                                          │
│ Ctrl+A  Arc  │                                          │
│ Ctrl+C  Char │                                          │
├──────────────┴──────────────────────────────────────────┤
│ ✍️ Your Response:                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Type your message here                              │ │
│ │ Multi-line supported!                               │ │
│ │ No glitches!                                        │ │
│ └─────────────────────────────────────────────────────┘ │
│ [Ctrl+Enter Send] [Enter New Line] [F1 Help]           │
└─────────────────────────────────────────────────────────┘
```

---

## ❓ Troubleshooting

### Bridge says "claude command not found"
- Make sure Claude Code is installed
- Check that `claude` is in your PATH
- Try running `claude --version` in terminal

### TUI not receiving responses
- Make sure bridge is running in Terminal 1
- Check that both terminals are in the correct directory
- Look for error messages in the bridge terminal

### Overlays not showing content
- Make sure state files exist (run `/arc`, `/memory` commands first)
- Check that you're in the correct RP folder

### Context panel shows "Unknown"
- Make sure `state/current_state.md` exists
- Update it using `/continue` or manually

---

## 💡 Tips

### Split Terminal Windows
Most terminals support splitting:
- **Windows Terminal**: `Alt+Shift+-` (horizontal) or `Alt+Shift++` (vertical)
- **iTerm2 (Mac)**: `Cmd+D` (vertical) or `Cmd+Shift+D` (horizontal)
- **Tmux**: `Ctrl+B "` (horizontal) or `Ctrl+B %` (vertical)

### Keep References Visible
Press `Alt+M`, `Alt+A`, etc. while composing to check facts without leaving the TUI!

### Switch Between Overlays
No need to close one overlay to open another - just press the Alt+Key for the overlay you want!

### Use Multi-line Input
The text input supports multiple lines - great for longer, more detailed responses!

---

## 🎉 Enjoy!

You now have:
- ✅ Better text input (no terminal glitches)
- ✅ Quick reference access (one keypress away)
- ✅ Visual context (always visible)
- ✅ Auto Claude Code integration (zero extra cost)

Happy RPing! 🎭
