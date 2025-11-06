# Trigger Editor UI Mockup

This document describes the standalone Trigger Editor UI mockup for previewing and testing the interface design before full integration.

## Overview

The Trigger Editor allows users to manage character triggers - words or phrases that activate when mentioned in messages. Each character can have multiple trigger words including their name, pronouns, and relationship terms.

## Running the Mockup

### Method 1: Using the runner script
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python scripts/run_trigger_editor_mockup.py
```

### Method 2: Direct execution
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python src/presentation/tui/components/trigger_editor_mockup.py
```

## Features

### Main Interface

**Header Section:**
- Title: "✨ Character Trigger Editor"
- Description explaining trigger functionality
- Tips about trigger usage

**Data Table:**
- **Columns:**
  - Character name
  - Trigger words (comma-separated)
  - Count of triggers
- **Interactive:**
  - Click rows to select
  - Selected row highlighted
  - Cursor navigation with arrow keys

**Button Bar:**
- ➕ **Add Character** (Primary button) - Opens modal to add new character
- ✏️ **Edit** (Default button) - Opens modal to edit selected character
- 🗑️ **Remove** (Error/Red button) - Removes selected character

**Info Panel:**
- Usage tips
- Reminder about case-insensitive matching

### Edit Modal

**Fields:**
- **Character Name** (Input)
  - Text input for character name
  - Example: "Silas"

- **Trigger Words** (Input)
  - Comma-separated list of triggers
  - Example: "Silas, him, he, boyfriend"

**Buttons:**
- **Cancel** - Close without saving
- **Save** (Primary) - Save changes and close

**Validation:**
- Character name is required
- At least one trigger word is required
- Displays error notifications if validation fails

## Sample Data

The mockup includes sample data for three characters:

1. **Silas**
   - Triggers: Silas, him, he, boyfriend

2. **Emma**
   - Triggers: Emma, she, her, sister

3. **Marcus**
   - Triggers: Marcus, he, him, best friend

## Color Scheme

Follows the RP Client TUI color palette:
- **Primary**: `#723d46` (Wine) - Headers, borders
- **Surface**: `#eaeada` (Sage 800) - Main background
- **Panel**: `#dfe0c8` (Sage 700) - Secondary panels
- **Boost**: `#ffedcb` (Peach Yellow) - Description box
- **Text**: `#472d30` (Van Dyke) - Primary text

## User Interactions

### Adding a Character
1. Click "➕ Add Character" button
2. Modal appears
3. Enter character name
4. Enter trigger words (comma-separated)
5. Click "Save"
6. Character appears in table
7. Notification confirms success

### Editing a Character
1. Click on a row to select character
2. Click "✏️ Edit" button
3. Modal appears with pre-filled data
4. Modify name or triggers
5. Click "Save"
6. Table updates
7. Notification confirms success

### Removing a Character
1. Click on a row to select character
2. Click "🗑️ Remove" button
3. Character removed from table
4. Notification confirms removal

### Keyboard Shortcuts
- **Ctrl+Q**: Quit application
- **Ctrl+S**: Save (shows notification in mockup)
- **Arrow Keys**: Navigate table rows
- **Enter**: Confirm in modals
- **Escape**: Cancel/close modals

## Technical Details

### Components

**TriggerEditor (Main Widget)**
- Container with DataTable
- Manages trigger data dictionary
- Handles button events
- Tracks selected row

**TriggerEditModal (Modal Screen)**
- Input fields for name and triggers
- Validation logic
- Returns data dictionary or None

**TriggerEditorMockupApp (App)**
- Standalone Textual app
- Listens for TriggersChanged events
- Provides global keybindings

### State Management

```python
triggers: dict[str, list[str]] = {
    "Silas": ["Silas", "him", "he", "boyfriend"],
    "Emma": ["Emma", "she", "her", "sister"],
    ...
}
```

### Events

**TriggerEditor.TriggersChanged**
- Posted when triggers dictionary is modified
- Contains updated triggers dictionary
- Bubbles to parent components

## Integration Notes

To integrate into the main TUI:

1. **Create TriggerEditor component** from the mockup code
2. **Add IPC integration:**
   - GET_TRIGGERS request on mount
   - SET_TRIGGER request on save

3. **Add to settings panel or overlay:**
   - Option 1: Add to settings panel (below provider selector)
   - Option 2: Open as modal overlay (F3 keybinding)

4. **Handle persistence:**
   - Save changes to Bridge via IPC
   - Bridge updates session_triggers.json
   - Reload triggers from file when needed

## Future Enhancements

Potential improvements:
- Bulk import/export (CSV, JSON)
- Trigger word suggestions based on character name
- Conflict detection (overlapping triggers between characters)
- Search/filter characters
- Drag-and-drop reordering
- Trigger usage statistics
- Validation for common pronouns (avoid conflicts)

## Screenshots

### Main Editor View
```
┌─────────────────────────────────────────────────────────┐
│         ✨ Character Trigger Editor                     │
├─────────────────────────────────────────────────────────┤
│ 📋 Manage character triggers that activate when         │
│ mentioned in your messages.                             │
├─────────────────────────────────────────────────────────┤
│ Character │ Trigger Words                 │ Count      │
├───────────┼──────────────────────────────┼────────────┤
│ Emma      │ Emma, she, her, sister       │ 4          │
│ Marcus    │ Marcus, he, him, best friend │ 4          │
│ Silas     │ Silas, him, he, boyfriend    │ 4          │
└─────────────────────────────────────────────────────────┘
                    [➕ Add] [✏️ Edit] [🗑️ Remove]

💡 Select a row and click Edit to modify, or Remove to delete.
   Triggers are case-insensitive and match whole words.
```

### Edit Modal
```
┌──────────────────────────────────────┐
│        Edit: Silas                   │
├──────────────────────────────────────┤
│                                      │
│ Character Name:                      │
│ ┌──────────────────────────────────┐ │
│ │ Silas                            │ │
│ └──────────────────────────────────┘ │
│                                      │
│ Trigger Words (comma-separated):    │
│ ┌──────────────────────────────────┐ │
│ │ Silas, him, he, boyfriend        │ │
│ └──────────────────────────────────┘ │
│                                      │
│ 💡 Tip: Include the character's     │
│    name, pronouns, and relationship │
│    terms                            │
│                                      │
├──────────────────────────────────────┤
│                    [Cancel] [Save]   │
└──────────────────────────────────────┘
```

## Testing Checklist

- [ ] Mockup launches successfully
- [ ] Table displays sample data
- [ ] Row selection works (click and arrows)
- [ ] Add button opens modal
- [ ] Edit button opens modal with correct data
- [ ] Remove button deletes character
- [ ] Modal validation works (empty fields)
- [ ] Modal save updates table
- [ ] Modal cancel discards changes
- [ ] Notifications appear for all actions
- [ ] Keyboard shortcuts work (Ctrl+Q, etc.)
- [ ] UI is responsive to window resize
- [ ] Colors match theme palette
