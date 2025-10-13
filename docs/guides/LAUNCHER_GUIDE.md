# 🚀 One-Click Launcher Guide

You now have two easy ways to launch the RP Client TUI!

---

## 🎯 Option 1: Batch File (Simplest)

**Just double-click**: `launch_rp_tui.bat`

### What it does:
- ✅ Opens both Bridge and TUI automatically
- ✅ Uses Windows Terminal split panes (if available)
- ✅ Falls back to two separate cmd windows if not
- ✅ Automatically uses "Example RP" folder

### For different RP folders:
Right-click the batch file, create a shortcut, and edit the target:
```
"C:\Users\green\Desktop\RP Claude Code\launch_rp_tui.bat" "Your RP Name"
```

---

## 🎨 Option 2: Python Launcher (More Features)

**Double-click**: `launch_rp_tui.py`

### What it does:
- ✅ Auto-detects all RP folders
- ✅ Shows menu if you have multiple RPs
- ✅ Uses Windows Terminal split panes (if available)
- ✅ Falls back to two separate cmd windows if not

### Example:
```
========================================================
🎭 RP Client TUI Launcher
========================================================

📁 Available RP folders:

  1. Example RP
  2. My Campaign
  3. Test Story

Select folder (1-3): 1

🚀 Launching RP Client for: Example RP

✨ Using Windows Terminal (split panes)...

✅ Launched!
```

---

## 📌 Create Desktop Shortcut

### For the Batch File:
1. Right-click `launch_rp_tui.bat`
2. Click "Create shortcut"
3. Drag shortcut to your Desktop
4. (Optional) Right-click → Properties → Change Icon for a custom icon

### For the Python Launcher:
1. Right-click `launch_rp_tui.py`
2. Click "Create shortcut"
3. Edit the shortcut target to:
   ```
   python "C:\Users\green\Desktop\RP Claude Code\launch_rp_tui.py"
   ```
4. Drag shortcut to your Desktop

---

## 🖥️ Windows Terminal vs Standard CMD

### If you have Windows Terminal (Recommended):
- ✅ Both windows open in **split panes** (side-by-side)
- ✅ Easier to see both Bridge and TUI at once
- ✅ Looks nicer!

**Get Windows Terminal**: Available free in Microsoft Store

### If you don't have Windows Terminal:
- ✅ Two separate **cmd windows** open
- ✅ Works perfectly fine, just arrange them manually

---

## ⚙️ Customization

### Change Default RP Folder (Batch File):
Edit `launch_rp_tui.bat`, find this line:
```batch
set RP_FOLDER=Example RP
```
Change to:
```batch
set RP_FOLDER=My Campaign
```

### Always Ask Which Folder (Python):
The Python launcher already does this automatically if you have multiple RP folders!

---

## 🎯 What Happens When You Launch

```
Click launcher
     ↓
Terminal 1 opens: Bridge starts monitoring
     ↓
Terminal 2 opens: TUI starts, ready to RP
     ↓
You're ready to go!
```

In the TUI:
1. Type your message (Enter for new lines)
2. Press `Ctrl+Enter` to send
3. Bridge automatically sends to Claude Code
4. Response appears in TUI
5. Repeat!

---

## ❓ Troubleshooting

### "Python not recognized"
- Make sure Python is installed
- Make sure Python is in your PATH
- Try: `python --version` in cmd to test

### Windows open then immediately close
- Check that you're in the correct directory
- Check that `tui_bridge.py` and `rp_client_tui.py` exist
- Try running manually to see error messages

### Only one window opens
- Bridge might have an error
- Check the bridge window for error messages
- Make sure the RP folder name is correct

### "RP folder not found"
- Check that the folder exists
- Check that it has a `state/` subdirectory
- Verify the folder name matches exactly (case-sensitive)

---

## 💡 Pro Tips

### Keep the Launcher on Desktop
Create a shortcut so you can start RPing with just one double-click!

### Use Windows Terminal
Much nicer experience with split panes. Free in Microsoft Store.

### Multiple RP Projects
Use the Python launcher - it auto-detects all your RP folders!

### Custom Icons
Right-click shortcut → Properties → Change Icon to make it look cool!

---

## 🎉 You're All Set!

Just double-click `launch_rp_tui.bat` or `launch_rp_tui.py` and start RPing!

**Quick Reference:**
- `Ctrl+Enter` - Send message
- `Enter` - New line (works naturally!)
- `F1` - Help
- `Ctrl+Q` - Quit
- **Footer buttons** - Quick access to Memory, Arc, Characters, etc.
