# RP Client TUI - Usage Guide

## 🎯 What This Is

A Terminal User Interface (TUI) that enhances your RP experience with:
- Better text input (multi-line, no glitches)
- Quick reference overlays (Alt+M for memory, Alt+A for arc, etc.)
- Real-time context display (chapter, time, location, progress)
- Clean, organized layout

## 📦 Installation

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
pip install -r requirements.txt
```

## 🚀 Quick Start (One-Click Launch)

### **Easiest Way - Just Double-Click:**

**Option 1**: Double-click `launch_rp_tui.bat` (simplest)
**Option 2**: Double-click `launch_rp_tui.py` (auto-detects multiple RP folders)

Both will automatically open the Bridge and TUI for you!

📖 **See `LAUNCHER_GUIDE.md` for creating desktop shortcuts and customization**

---

## 🚀 Manual Usage

### Two-Terminal Setup:

**Terminal 1 - Start the Bridge:**
```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python tui_bridge.py "Example RP"
```
This monitors for TUI input and sends it to Claude Code automatically.

**Terminal 2 - Start the TUI:**
```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python rp_client_tui.py "Example RP"
```

### Workflow:

1. **Type your message** in the TUI (multi-line, no glitches!)
2. **Use quick references** while composing:
   - Click footer buttons to check memory, arc, characters, notes, etc.
   - Overlays open over your text without losing your place
3. **Press Ctrl+Enter** to send (Enter for new lines)
4. **Bridge automatically sends to Claude Code**
5. **Response appears in TUI** automatically
6. **Repeat!**

### How It Works:

```
TUI (Terminal 2)         Bridge (Terminal 1)         Claude Code
─────────────────        ──────────────────          ───────────
Type message      →      Detects input        →      Processes
                         Calls Claude CLI
                         Captures response     ←      Responds
Displays response ←      Sends back
```

**Cost**: Uses your Claude Code subscription (zero extra cost!)

## ⌨️ Keyboard Shortcuts

### Main Controls:
- `Ctrl+Enter` - Send message to Claude Code
- `Enter` - New line in message (works naturally)
- `Ctrl+Q` - Quit
- `F1` - Help

### Quick Access (Overlays):
Click the **footer buttons** at the bottom of the screen:
- Memory, Arc, Characters, Notes, Entities, Genome, Status

### In Overlays:
- `↑`/`↓` or `PgUp`/`PgDn` - Scroll
- `ESC` - Close overlay

## 🎨 Layout

```
┌─────────────────────────────────────────────────────────┐
│ Header (chapter, time, location)                       │
├──────────────┬──────────────────────────────────────────┤
│ Context      │ Chat History                             │
│ Panel:       │                                          │
│              │ Your messages and references             │
│ - Current    │ (Responses can be pasted here)           │
│   state      │                                          │
│ - Progress   │                                          │
│ - Quick      │                                          │
│   access     │                                          │
│   menu       │                                          │
├──────────────┴──────────────────────────────────────────┤
│ Text Input (Multi-line, scrollable)                    │
└─────────────────────────────────────────────────────────┘
```

## 💡 Benefits

1. **Better Text Input**: No terminal glitches, unlimited length, multi-line
2. **Quick Reference**: One-key access to all your RP documents
3. **Visual Context**: Always see chapter, time, location, progress
4. **Organized**: Clean separation of context/history/input

## 🔮 Future Features

- Automatic Claude Code integration (subprocess or API)
- Copy/paste buttons for easier workflow
- Message history saving
- Search within overlays
- Edit scene notes directly in TUI
- Theme customization

## ❓ Help

Press `F1` in the TUI for keyboard shortcuts.

---

**Note**: This TUI is designed to work alongside Claude Code, using your existing subscription. No additional API costs!
