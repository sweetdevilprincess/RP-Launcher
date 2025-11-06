# RP Launcher Setup Hub

**Welcome!** This folder contains everything you need to create and manage new roleplays with the RP Launcher system.

---

## 🚀 Quick Start (Choose Your Path)

### Path 1: I Just Want To Start (5 Minutes)
**→ Use the Quick Setup Script**

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python setup/quick_setup.py "My New RP"
```

This creates a complete RP folder with all required files. Then just launch it:

```bash
python launch_rp_tui.py "My New RP"
```

### Path 2: I Want To Understand Everything (30 Minutes)
**→ Follow the Comprehensive Guide**

1. Read: [`guides/02_CREATING_YOUR_FIRST_RP.md`](guides/02_CREATING_YOUR_FIRST_RP.md)
2. Use a starter template from `templates/starter_packs/`
3. Follow the [`CHECKLIST.md`](CHECKLIST.md) to verify setup

### Path 3: I'm Experienced (2 Minutes)
**→ Use Templates Directly**

1. Copy `templates/starter_packs/minimal/` to `RPs/` folder
2. Rename to your RP name
3. Fill in the templates
4. Launch!

---

## 📚 Documentation

### Quick Links to Main Guides

| Guide | Purpose | Audience |
|-------|---------|----------|
| [**Creating Your First RP**](guides/02_CREATING_YOUR_FIRST_RP.md) | Step-by-step RP creation | Everyone |
| [**Project CLAUDE.md**](../CLAUDE.md) | Project guidelines and file locations | Developers |
| [**DOCUMENTATION_INDEX.md**](../Working\ Guides/DOCUMENTATION_INDEX.md) | Navigation hub for all system docs | All users |

### Comprehensive Documentation Available

For detailed information beyond setup, see the **Working Guides** folder:

- **[RP_DIRECTORY_MAP.md](../Working\ Guides/RP_DIRECTORY_MAP.md)** - RP folder structure & file interactions
- **[LAUNCHER_DOCUMENTATION.md](../Working\ Guides/LAUNCHER_DOCUMENTATION.md)** - How to use the launcher (F-keys, settings)
- **[TUI_BRIDGE_DOCUMENTATION.md](../Working\ Guides/TUI_BRIDGE_DOCUMENTATION.md)** - How the backend works (SDK vs API modes)
- **[SYSTEM_ARCHITECTURE.md](../Working\ Guides/SYSTEM_ARCHITECTURE.md)** - Overall system design

### Setup Verification

- **Checklist:** [`CHECKLIST.md`](CHECKLIST.md) - Verify your setup is complete
- **Examples:** Check `RPs/Example RP/` or `RPs/Lilith and Silas/` folders for reference

---

## 🛠️ Setup Tools

### Automated Setup Scripts

#### 1. Quick Setup (Recommended)
```bash
python setup/quick_setup.py "RP Name"
```
**Features:**
- Creates complete RP structure
- Generates all required files
- Uses sensible defaults
- Fast and simple

**Options:**
```bash
# Use minimal template (bare essentials)
python setup/quick_setup.py "RP Name" --template minimal

# Use fantasy adventure template (pre-made fantasy content)
python setup/quick_setup.py "Epic Quest" --template fantasy_adventure

# Custom location
python setup/quick_setup.py "RP Name" --path "/path/to/rps"

# Overwrite existing
python setup/quick_setup.py "RP Name" --overwrite
```

### Planned Tools (Coming Soon)

#### Interactive Wizard
```bash
python setup/new_rp_wizard.py
```
Step-by-step guided setup with questions and examples.

#### Validate RP Structure
```bash
python setup/scripts/validate_rp.py "RP Name"
```
Checks if your RP has all required files and correct structure.

#### Fix Common Issues
```bash
python setup/scripts/fix_structure.py "RP Name"
```
Auto-creates missing files and fixes formatting issues.

---

## 📦 Starter Templates

### Available Template Packs

| Template | Description | Best For |
|----------|-------------|----------|
| **[minimal](templates/starter_packs/minimal/)** | Bare essentials only | Experienced users, custom setups |
| **[fantasy_adventure](templates/starter_packs/fantasy_adventure/)** | Pre-made fantasy RP | Knights, magic, quests, epic adventures |
| **modern_romance** *(coming soon)* | Contemporary setting | Real-world stories, relationships |
| **scifi_exploration** *(coming soon)* | Space & future | Technology, discovery |

### Template Contents

Each template pack includes:
- ✅ Complete directory structure
- ✅ Core story files (AUTHOR'S_NOTES.md, STORY_GENOME.md, etc.)
- ✅ Character sheet templates
- ✅ Starter chapter with guidance
- ✅ Ready to use immediately (state files auto-generate on first run)

### Using Templates

**Option 1: Via Script (Easiest)**
```bash
python setup/quick_setup.py "My RP" --template minimal
```

**Option 2: Manual Copy**
1. Copy entire template folder from `setup/templates/starter_packs/`
2. Paste into `RPs/` folder (create it if needed)
3. Rename to your RP name
4. Customize the template files

---

## 🎯 What You Get

When you create a new RP, the minimal template includes:

### Files You Edit
- **`{RP Name}.md`** - RP overview & metadata (ROLEPLAY_OVERVIEW - rename this to your RP name)
- **`AUTHOR'S_NOTES.md`** - Absolute story rules (what must/must not happen)
- **`STORY_GENOME.md`** - Intended story direction & themes
- **`NAMING_CONVENTIONS.md`** - World naming patterns (characters, places, factions)
- **`SCENE_NOTES.md`** - Current session guidance

### Files That Auto-Generate
When you run the RP, `initialize_rp.py` automatically creates all state files in the `state/` directory:

See **[RP_DIRECTORY_MAP.md](../Working\ Guides/RP_DIRECTORY_MAP.md#state-directory-files)** for complete state files reference. These include:

- **`state/current_state.md`** - Story position tracking
- **`state/story_arc.md`** - Current story arc progress
- **`state/automation_config.json`** - Automation settings
- **`state/plot_threads_master.md`** - Active plot threads
- And more (see docs for complete list)...

### Directories
- **`chapters/`** - Story chapters (your RP content)
- **`characters/`** - Character sheets (you create {{user}}.md and {{char}}.md)
- **`state/`** - Auto-created tracking & automation files
- **`memories/`** - Auto-created character-specific memory files
- **`relationships/`** - Character preference files for relationship tracking
- **`entities/`** - Auto-generated entity cards
- **`sessions/`** - Session logs
- **`locations/`** - Location details
- **`exports/`** - Exported content

---

## ❓ Common Questions

### Q: Do I need to fill out every template?
**A:** No! Here's what's actually required:
- Your RP name folder must exist
- `AUTHOR'S_NOTES.md`, `STORY_GENOME.md`, `NAMING_CONVENTIONS.md`, `SCENE_NOTES.md` (automation needs these)
- `characters/{{user}}.md` (your character sheet)
- At least one character in `characters/{{char}}.md`
- One chapter file (can start with `chapters/chapter_001.md`)

State files auto-generate on first run - you don't need to create them!

### Q: Can I skip the templates and start writing?
**A:** Yes! The minimal template gives you just the structure. You can start writing immediately in `chapters/chapter_001.md`.

### Q: What if I mess up the setup?
**A:** Delete the RP folder and run the setup script again. A validation tool is planned but not yet available. For troubleshooting help, check the main **[DOCUMENTATION_INDEX.md](../Working\ Guides/DOCUMENTATION_INDEX.md)** for guidance.

### Q: Can I have multiple RPs?
**A:** Absolutely! Create as many as you want. The launcher will let you choose which one to use.

### Q: How do I move between RPs?
**A:** Close the launcher (Ctrl+Q) and restart it. It will ask you which RP folder to use.

---

## 📖 Example Workflow

Here's a typical workflow for creating a new RP:

```bash
# 1. Create the RP
python setup/quick_setup.py "Epic Fantasy Quest"

# 2. Fill in the basics (optional but recommended)
#    Edit these files in your favorite text editor:
#    - Epic Fantasy Quest/AUTHOR'S_NOTES.md
#    - Epic Fantasy Quest/STORY_GENOME.md
#    - Epic Fantasy Quest/characters/{{user}}.md

# 3. Launch it!
python launch_rp_tui.py "Epic Fantasy Quest"

# 4. Start writing!
#    - Type your message
#    - Press Ctrl+Enter to send
#    - Get Claude's response
#    - Continue the story!
```

---

## 🆘 Getting Help

### If Something's Not Working

1. **Check the Troubleshooting Guide:** [`guides/99_TROUBLESHOOTING.md`](guides/99_TROUBLESHOOTING.md)
2. **Validate your setup:** `python setup/scripts/validate_rp.py "RP Name"` *(coming soon)*
3. **Look at Example RP:** See how a working RP is structured
4. **Check GitHub Issues:** https://github.com/sweetdevilprincess/RP-Launcher/issues

### Common Issues Quick Fixes

**"RP folder not found"**
→ Make sure your RP folder is in the `RPs/` directory

**"Missing state directory"**
→ Run `python setup/quick_setup.py "RP Name"` to recreate structure

**"No API key"**
→ Press F9 in the launcher to configure API keys

---

## 🎓 Learning Path

### Beginner Path (1 hour)
1. ✅ Run quick_setup.py
2. ✅ Read Creating Your First RP guide
3. ✅ Launch the RP
4. ✅ Write a few messages
5. ✅ Explore the F-key overlays (F1-F9)

### Intermediate Path (2-3 hours)
6. ✅ Fill in STORY_GENOME.md with your story plan
7. ✅ Create character sheets
8. ✅ Configure automation (F9 → Settings)
9. ✅ Try the /arc and /note commands
10. ✅ Review the automation guides

### Advanced Path (ongoing)
11. ✅ Customize automation_config.json
12. ✅ Set up proxy mode for custom prompts
13. ✅ Configure thinking modes
14. ✅ Create custom entity templates
15. ✅ Explore agent customization

---

## 📂 This Directory

```
setup/
├── README.md                    ← You are here!
├── CHECKLIST.md                 Setup completion checklist
├── quick_setup.py               Fast RP creation script
├── guides/                      Step-by-step documentation
│   ├── 01_FIRST_TIME_SETUP.md
│   ├── 02_CREATING_YOUR_FIRST_RP.md
│   ├── 03_UNDERSTANDING_STRUCTURE.md
│   ├── 04_WRITING_YOUR_STORY.md
│   ├── 05_ADVANCED_FEATURES.md
│   └── 99_TROUBLESHOOTING.md
├── templates/
│   ├── starter_packs/           Pre-made RP templates
│   │   └── minimal/             Bare essentials template
│   └── examples/                Example filled templates
└── scripts/                     Utility scripts
    ├── validate_rp.py           Check RP structure
    ├── fix_structure.py         Auto-fix issues
    └── migrate_existing.py      Migrate old RPs
```

---

## 🚀 Ready to Start?

**Quick Start (Easiest):**
```bash
python setup/quick_setup.py "My Amazing RP"
python launch_rp_tui.py "My Amazing RP"
```

**Full Walkthrough (Recommended for first time):**
→ Read [`guides/02_CREATING_YOUR_FIRST_RP.md`](guides/02_CREATING_YOUR_FIRST_RP.md)

**Already know what you're doing:**
→ Use a template from `templates/starter_packs/`

---

Happy roleplaying! 🎭✨
