# RP Setup Wizard - Implementation Summary

## Overview

A complete setup wizard has been implemented for creating new RP (Role Play) folders with all required files and structure. The wizard collects user input through a multi-page TUI interface and generates a fully-configured RP directory ready for use.

## Components Created

### 1. RP Initialization Module (`src/infrastructure/rp_initialization/`)

**File:** `rp_creator.py`

This module handles the creation of RP directories and all required files.

**Key Features:**
- Creates complete directory structure (14 directories)
- Generates all 5 core story files (AUTHOR'S_NOTES, STORY_GENOME, etc.)
- Initializes 10 state tracking files (JSON and Markdown)
- Creates character sheets for {{user}} and {{char}}
- Generates initial chapter file
- Creates RP configuration file with metadata

**Usage:**
```python
from src.infrastructure.rp_initialization import RPCreator

creator = RPCreator(Path("RPs"))
rp_dir = creator.create_rp(wizard_data)
```

### 2. Setup Wizard TUI (`src/presentation/tui/screens/startup_wizard_screen.py`)

**10-Page Wizard Flow:**

1. **Welcome** - Introduction and overview
2. **Basic Info** - RP name, genre, setting, premise, content rating
3. **Story Rules** - Tone, writing style (→ AUTHOR'S_NOTES.md)
4. **World & Setting** - Time period, world notes (→ STORY_GENOME.md)
5. **Naming** - Culture, naming patterns (→ NAMING_CONVENTIONS.md)
6. **Scene Setup** - Starting location, time, atmosphere (→ SCENE_NOTES.md)
7. **Your Character** - Player character details (→ characters/{{user}}.md)
8. **Main NPC** - Main NPC details (→ characters/{{char}}.md)
9. **LLM Config** - API provider, keys, settings
10. **Review** - Final confirmation before creation

## Generated RP Structure

When the wizard completes, it creates:

```
RPs/[RP Name]/
├── [RP Name].md              # RP overview file
├── AUTHOR'S_NOTES.md         # Story rules and constraints
├── STORY_GENOME.md           # Story direction and arc
├── NAMING_CONVENTIONS.md     # Naming patterns for consistency
├── SCENE_NOTES.md            # Current scene guidance
├── rp_config.json            # RP metadata and settings
│
├── chapters/
│   └── chapter_001.md        # Initial chapter
│
├── characters/
│   ├── {{user}}.md           # Player character sheet
│   └── {{char}}.md           # Main NPC sheet (if provided)
│
├── entities/                 # Auto-generated entity cards (empty initially)
│
├── state/                    # State tracking files
│   ├── automation_config.json      # Automation settings
│   ├── current_state.md            # Current story state
│   ├── entity_tracker.json         # Entity tracking
│   ├── relationship_tracker.json   # Relationship data
│   ├── memory_index.json           # Memory index
│   ├── file_tracking.json          # File change tracking
│   ├── response_counter.json       # Response counter
│   ├── plot_threads_master.md      # Active plot threads
│   ├── plot_threads_archive.md     # Archived threads
│   └── knowledge_base.md           # World knowledge
│
├── memories/                 # Character memory files (empty initially)
├── relationships/            # Relationship preference files (empty initially)
├── locations/                # Location details (empty initially)
│
├── sessions/                 # Session logs
│   ├── branches/
│   └── archived/
│
├── exports/                  # Export outputs
│   ├── wiki/
│   ├── epub/
│   └── pdf/
│
├── backups/                  # Backup files (empty initially)
└── config/                   # Additional config (empty initially)
```

## File Format Compliance

All generated files follow the specifications discovered in the codebase exploration:

### Core Story Files (Required)

1. **[RP Name].md** - Overview file matching folder name
   - Quick Overview section (Genre, Setting, Tone, Rating)
   - Premise
   - Character list
   - Story goals
   - Current status

2. **AUTHOR'S_NOTES.md** - Story rules (HIGHEST PRIORITY in loading)
   - What MUST happen
   - What MUST NOT happen
   - Writing preferences (style, perspective, length)
   - Tone & themes
   - Content boundaries
   - Character notes

3. **STORY_GENOME.md** - Story direction (SECOND PRIORITY)
   - Genre & setting details
   - Story arc (Act 1, Midpoint, Climax)
   - Major plot points
   - Themes
   - Character arcs
   - World notes

4. **NAMING_CONVENTIONS.md** - Naming patterns (USED FOR GENERATION)
   - Primary culture/region
   - Character naming patterns (given names, family names)
   - Location naming patterns
   - Organization naming patterns
   - Titles & ranks

5. **SCENE_NOTES.md** - Session guidance (USED DURING SESSIONS)
   - Current scene details (location, time, characters, atmosphere)
   - Session goals
   - Active NPC notes
   - Guidance for Claude
   - Reminders

### State Files (Auto-Generated)

All state files are initialized with proper structure:

- **JSON files** - Valid JSON with all required fields
- **Markdown files** - Proper formatting with headers and sections
- **Timestamps** - ISO-8601 format
- **Default values** - Sensible defaults for all automation features

## Data Collection

The wizard collects data through form fields:

**Form Widget Types:**
- `Input` - Single-line text fields
- `TextArea` - Multi-line text fields
- `Select` - Dropdown menus with predefined options

**Data Validation:**
- RP name is required (checked in `action_finish()`)
- All other fields are optional with sensible defaults
- Safe widget value retrieval with error handling

## Testing

### Backend Test: `test_wizard_creation.py`

Tests the RP creation logic without TUI:

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python test_wizard_creation.py
```

Validates:
- RP directory creation
- All required files exist
- All required directories exist
- State files are valid JSON
- Character files are created
- Chapter file exists
- Content formatting is correct

**Test Results:** ✓ All validations pass

### TUI Test: `run_wizard_demo.py`

Runs the full wizard interface:

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python run_wizard_demo.py
```

This launches the complete wizard TUI where you can:
- Navigate through all 10 pages
- Fill in form fields
- Test the complete user experience
- Create a real RP folder

**Test Results:** ✓ TUI launches successfully

## Integration

To integrate with your main TUI app:

1. **Import the wizard:**
   ```python
   from src.presentation.tui.screens.startup_wizard_screen import StartupWizardScreen
   ```

2. **Push the wizard screen:**
   ```python
   # When user wants to create new RP
   wizard = StartupWizardScreen(base_rps_dir=Path("RPs"))
   self.push_screen(wizard)
   ```

3. **The wizard will:**
   - Guide user through all pages
   - Collect data from form fields
   - Create complete RP structure
   - Show success/error notifications
   - Pop itself when done

## Future Enhancements

Potential improvements:

1. **More Detailed Forms:**
   - Add list builders for story goals, themes, plot points
   - Character relationship builder
   - Multiple NPC creation

2. **Template System:**
   - Pre-fill common genres (Fantasy, Sci-Fi, etc.)
   - Load from template files
   - Save custom templates

3. **Validation:**
   - Check for invalid characters in RP name
   - Validate file paths
   - Check for reserved names

4. **Progress Indicators:**
   - Show completion percentage
   - Mark required vs optional fields
   - Highlight incomplete sections

5. **Import/Export:**
   - Import from existing RP
   - Export wizard data as JSON
   - Clone existing RP setup

## Files Modified

1. **Created:**
   - `src/infrastructure/rp_initialization/rp_creator.py` (719 lines)
   - `src/infrastructure/rp_initialization/__init__.py` (5 lines)
   - `test_wizard_creation.py` (149 lines - test file)

2. **Modified:**
   - `src/presentation/tui/screens/startup_wizard_screen.py`
     - Added 3 new wizard pages (Story Rules, Naming, Scene Setup)
     - Converted all pages to use form fields instead of static text
     - Added `_collect_wizard_data()` method
     - Implemented `action_finish()` with RPCreator integration
     - Added proper imports and initialization

## Summary

The RP setup wizard is **fully functional** and creates complete, properly-formatted RP folders that match the codebase specifications. All required files are generated with correct structure, and the wizard provides a user-friendly interface for configuration.

**Status:** ✓ Complete and tested
**Test Results:** ✓ All files created correctly
**Integration:** Ready for use in main TUI app
