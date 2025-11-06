# RP Setup Wizard - Quick Start Guide

## 🚀 Running the Wizard

### Test the Backend (No UI)
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python test_wizard_creation.py
```
This creates a test RP and validates all files are generated correctly.

### Test the Full Wizard (TUI)
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python run_wizard_demo.py
```
This launches the complete wizard interface where you can:
- Navigate pages with Next/Back buttons or sidebar
- Fill in all form fields
- Create a complete RP folder

**Controls:**
- `Ctrl+N` - Next page
- `Ctrl+P` - Previous page
- `Escape` - Cancel wizard
- Mouse click sidebar buttons to jump to pages

### Clean Up Test Output
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python -c "import shutil; from pathlib import Path; p = Path('test_rps_output'); shutil.rmtree(p) if p.exists() else None"
```

## 📋 Wizard Pages Overview

| Page | Purpose | Maps To |
|------|---------|---------|
| 1. Welcome | Introduction | - |
| 2. Basic Info | Name, genre, premise | `[RP Name].md` |
| 3. Story Rules | Tone, style | `AUTHOR'S_NOTES.md` |
| 4. World & Setting | Time period, world notes | `STORY_GENOME.md` |
| 5. Naming | Culture, patterns | `NAMING_CONVENTIONS.md` |
| 6. Scene Setup | Starting scene | `SCENE_NOTES.md` |
| 7. Your Character | Player character | `characters/{{user}}.md` |
| 8. Main NPC | Main NPC (optional) | `characters/{{char}}.md` |
| 9. LLM Config | API settings | `rp_config.json` |
| 10. Review | Confirmation | - |

## ✅ What Gets Created

After completing the wizard, you'll have:

```
RPs/[Your RP Name]/
├── 5 Core Story Files
│   ├── [RP Name].md
│   ├── AUTHOR'S_NOTES.md
│   ├── STORY_GENOME.md
│   ├── NAMING_CONVENTIONS.md
│   └── SCENE_NOTES.md
│
├── Configuration
│   └── rp_config.json
│
├── Characters
│   ├── characters/{{user}}.md
│   └── characters/{{char}}.md
│
├── Initial Chapter
│   └── chapters/chapter_001.md
│
└── State Files (10 files)
    └── state/
        ├── automation_config.json
        ├── current_state.md
        ├── entity_tracker.json
        ├── relationship_tracker.json
        ├── memory_index.json
        ├── file_tracking.json
        ├── response_counter.json
        ├── plot_threads_master.md
        ├── plot_threads_archive.md
        └── knowledge_base.md
```

Plus 14 directories ready for use!

## 🔧 Integration

To use in your main app:

```python
from pathlib import Path
from src.presentation.tui.screens.startup_wizard_screen import StartupWizardScreen

# In your app
def create_new_rp(self):
    wizard = StartupWizardScreen(base_rps_dir=Path("RPs"))
    self.push_screen(wizard)
```

The wizard will:
1. Guide user through setup
2. Create complete RP structure
3. Show success notification
4. Auto-close when done

## 📝 Required Fields

Only **one** field is required:
- **RP Name** (on Basic Info page)

All other fields are optional with sensible defaults!

## 🎯 Quick Test Workflow

1. Run wizard: `python run_wizard_demo.py`
2. Enter RP name: "My Test RP"
3. Click through pages (or just click "Next" to use defaults)
4. Click "Finish" on Review page
5. Check `test_rps_output/My Test RP/` for created files

## 🐛 Troubleshooting

**Import Error when running startup_wizard_screen.py directly:**
- Don't run the wizard file directly
- Use `run_wizard_demo.py` instead

**"RP already exists" error:**
- The RP name you chose already exists
- Choose a different name or delete the existing RP folder

**Unicode errors in console:**
- Windows console encoding issue
- The wizard will still work in the TUI
- Use `run_wizard_demo.py` which handles this properly

## 📚 Documentation

See `WIZARD_IMPLEMENTATION.md` for complete technical documentation.

## ✨ Features

- **10 comprehensive pages** collecting all RP setup data
- **Form validation** ensures required fields are filled
- **Error handling** with user-friendly notifications
- **Complete RP structure** generated automatically
- **Follows codebase standards** - all files match expected format
- **Safe defaults** - only RP name is required
- **Sidebar navigation** - jump to any page directly
- **Keyboard shortcuts** - Ctrl+N/P for quick navigation

---

**Status:** ✅ Fully functional and tested
**Version:** 1.0
**Last Updated:** 2025-10-22
