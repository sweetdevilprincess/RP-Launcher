# RP Setup Completion Checklist

Use this checklist to verify your RP is set up correctly and ready to use.

---

## ✅ System Setup (One-Time)

These steps only need to be done once when you first set up the RP Launcher system.

### Prerequisites

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed (for SDK mode)
- [ ] Git installed (optional, for updates)

### Dependencies

- [ ] Python packages installed: `pip install -r requirements.txt`
- [ ] Node.js packages installed: `cd src && npm install`

### API Configuration

- [ ] OpenRouter API key configured (Press F9 → Settings)
  - Or: Anthropic API key if using API mode
- [ ] Model selected (default: deepseek/deepseek-chat-v3.1)

### Test Launch

- [ ] Launcher runs without errors: `python launch_rp_tui.py`
- [ ] Example RP is visible and selectable
- [ ] Can send a test message and get response

---

## 📁 RP Folder Setup

Check off each item as you create/verify your RP folder.

### Required Structure

#### Root Files
- [ ] **RP folder exists** in `RPs/` directory (e.g., `RPs/My RP/`)
- [ ] **`{RP Name}.md`** - RP overview file exists

#### Required Directories
- [ ] **`chapters/`** - For your story chapters
- [ ] **`characters/`** - For character sheets
- [ ] **`entities/`** - For auto-generated entities
- [ ] **`state/`** - For tracking/automation files

#### Required State Files
- [ ] **`state/plot_threads_master.md`** - Plot tracking
- [ ] **`state/current_state.md`** - Current state
- [ ] **`state/automation_config.json`** - Automation settings
- [ ] **`state/entity_tracker.json`** - Entity mentions
- [ ] **`state/file_tracking.json`** - File tracking

### Optional But Recommended

#### Root Files
- [ ] **`AUTHOR'S_NOTES.md`** - Story rules (what must/must not happen)
- [ ] **`STORY_GENOME.md`** - Story direction & themes
- [ ] **`SCENE_NOTES.md`** - Current session guidance
- [ ] **`CURRENT_STATUS.md`** - Auto-updated status

#### Optional Directories
- [ ] **`memories/`** - Character-specific memories
- [ ] **`relationships/`** - Relationship tracking
- [ ] **`locations/`** - Location details
- [ ] **`sessions/`** - Session logs
- [ ] **`exports/`** - Exported content

---

## 📝 Content Creation

Minimum content needed to start writing.

### Characters

- [ ] **`characters/{{user}}.md`** - Player character sheet (YOU)
  - Name, appearance, personality, background

- [ ] **`characters/{{char}}.md`** or named NPC - At least one NPC
  - Could be a companion, antagonist, or important character

### Story Setup

- [ ] **First chapter file created** - `chapters/chapter_001.md`
  - File exists (can be blank!)
  - OR: Opening scene pre-written
  - Note: You can start writing directly in the TUI - this file just needs to exist

### Story Planning (Optional)

- [ ] **Genre & themes defined** - in `STORY_GENOME.md`
- [ ] **Main plot outlined** - in `STORY_GENOME.md`
- [ ] **Story rules documented** - in `AUTHOR'S_NOTES.md`
- [ ] **Current scene notes** - in `SCENE_NOTES.md`

---

## ⚙️ Configuration

Verify automation and settings are configured.

### Automation Settings

In `state/automation_config.json`:

- [ ] **Auto entity cards** enabled/disabled as preferred
  - `"auto_entity_cards": true/false`
  - `"entity_mention_threshold": 2` (or your preference)

- [ ] **Auto story arc** enabled/disabled as preferred
  - `"auto_story_arc": true/false`
  - `"arc_frequency": 50` (or your preference)

### Launcher Settings (F9)

- [ ] **API key configured** (OpenRouter or Anthropic)
- [ ] **Model selected** (if using OpenRouter)
- [ ] **Thinking mode selected** (default: megathink)
- [ ] **API mode** enabled/disabled as preferred
- [ ] **Proxy mode** enabled/disabled as preferred

---

## 🧪 Test Launch

Verify everything works before starting your RP.

### Launch Test

- [ ] Launch the RP: `python launch_rp_tui.py "RP Name"`
- [ ] RP is automatically selected (or selectable from list)
- [ ] Bridge starts without errors
- [ ] TUI opens and displays correctly

### Interface Test

- [ ] Can type in the message area
- [ ] Press Enter creates new line
- [ ] Ctrl+Enter sends message
- [ ] F-keys open overlays (F1-F9)
  - F1: Help
  - F2: Memory
  - F3: Arc
  - F4: Characters
  - F5: Notes
  - F6: Entities
  - F7: Genome
  - F8: Status
  - F9: Settings

### First Message Test

- [ ] Send a test message
- [ ] Response appears in chat
- [ ] Response is coherent and relevant
- [ ] No error messages in terminal

### Automation Test

- [ ] After 2-3 messages, check for entity extraction
- [ ] After 50 messages (if enabled), check for story arc update
- [ ] Background agents run without errors (check terminal)

---

## 🎯 Ready to RP!

If all required items are checked, you're ready to start your roleplay!

### Final Steps

- [ ] **Save this checklist** for future reference
- [ ] **Bookmark useful guides** in `setup/guides/`
- [ ] **Join the community** (if available)
- [ ] **Star the repository** on GitHub (optional!)

### When You're Ready

1. Launch: `python launch_rp_tui.py "RP Name"`
2. Type your opening message
3. Press Ctrl+Enter
4. Start your adventure!

---

## 🆘 Something Not Working?

### Quick Fixes

**RP Not Found**
→ Make sure folder is in `RPs/` directory and has `state/` subdirectory

**Missing Files Error**
→ Run: `python setup/quick_setup.py "RP Name"` to recreate structure

**API Key Error**
→ Press F9 in launcher to configure API key

**No Response**
→ Check terminal for errors, verify API key is valid

**Bridge Won't Start**
→ Restart with F10 or close and relaunch

### Get Help

- Read: [`setup/guides/99_TROUBLESHOOTING.md`](guides/99_TROUBLESHOOTING.md)
- Check: `RPs/Example RP/` folder for reference
- Validate: `python setup/scripts/validate_rp.py "RP Name"` *(coming soon)*
- Issues: https://github.com/sweetdevilprincess/RP-Launcher/issues

---

## 📊 Setup Progress Tracker

Use this to track your overall progress:

```
System Setup:       [    ] 0/5   (Prerequisites, dependencies, config, test)
Folder Structure:   [    ] 0/8   (Required dirs and files)
Content Creation:   [    ] 0/4   (Characters, chapters, planning)
Configuration:      [    ] 0/6   (Automation, launcher settings)
Testing:            [    ] 0/4   (Launch, interface, message, automation)
```

### Completion Levels

- **Minimum Viable (50%):** Can launch and write
- **Recommended (75%):** All required + basic content
- **Complete (100%):** Everything including optional features

---

## 🎉 Congratulations!

Once you've checked off all required items, you have a fully functional RP ready to use!

**Next steps:**
- Read: [`setup/guides/04_WRITING_YOUR_STORY.md`](guides/04_WRITING_YOUR_STORY.md)
- Explore: Automation features and customization
- Create: Your amazing story!

Happy roleplaying! 🎭✨
