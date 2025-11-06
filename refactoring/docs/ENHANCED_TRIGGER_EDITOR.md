# Enhanced Trigger Editor UI - Three-Panel Responsive Layout

## Overview

The enhanced trigger editor features a modern three-panel layout that adapts to window size changes, provides character sheet previews to inform trigger selection, and allows easy navigation between characters.

## Running the Mockup

```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
python scripts/run_trigger_editor_enhanced.py
```

## Layout

```
+------------+------------------+------------------+
| Character  |  Character       |  Trigger         |
| List       |  Sheet Preview   |  Editor          |
| (sidebar)  |  (content)       |  (form)          |
+------------+------------------+------------------+
```

### Panel Breakdown

**Left Panel - Character List (1fr)**
- Clickable list of all characters
- Shows character name and trigger count
- Scrollable if many characters
- Border separates from middle panel

**Middle Panel - Character Sheet Preview (2fr)**
- Live markdown preview of selected character's sheet
- Displays full character information:
  - Overview (age, role, personality)
  - Physical description
  - Background
  - Relationships
  - Traits
  - Speech patterns
- Helps inform which trigger words to add
- Scrollable for long sheets

**Right Panel - Trigger Editor (1.5fr)**
- Character name display (read-only when selected)
- Scrollable list of trigger input fields
- Each trigger on its own line
- "Add Trigger" button to dynamically add more fields
- "Save" button to persist changes
- Tips and hints about good triggers

## Features

### Responsive Grid Layout
- Uses Textual's Grid container
- Fractional unit sizing (`1fr`, `2fr`, `1.5fr`)
- Adapts automatically to window resize
- Maintains proportions across screen sizes

### Character Navigation
- Click any character in the left list
- Middle panel updates with their sheet
- Right panel loads their triggers for editing
- Visual feedback on selection

### Dynamic Trigger Fields
- Start with 4 trigger input fields
- Click "Add Trigger" to add more
- Each field is a separate Input widget
- Scrollable container if many triggers

### Live Sheet Preview
- View character details while editing triggers
- Inform trigger selection from:
  - Character name
  - Pronouns mentioned in description
  - Relationship terms
  - Nicknames or titles
  - Speech patterns

## User Workflow

1. **Select Character**
   - Click "Silas" in left panel
   - Middle shows Silas's character sheet
   - Right loads Silas's 4 triggers

2. **Review Sheet**
   - Read through character details
   - Note pronouns: "him", "he"
   - Note relationship: "boyfriend"
   - Note nickname: "darling" (used by character)

3. **Edit Triggers**
   - See existing: "Silas", "him", "he", "boyfriend"
   - Add new trigger: "darling"
   - Click "Add Trigger" to get new field
   - Type "detective" (from role)

4. **Save**
   - Click "Save" button
   - Notification confirms save
   - Changes persist in mockup data

5. **Switch Character**
   - Click "Emma" in left panel
   - All panels update automatically
   - Repeat editing process

## Technical Implementation

### Reactive Properties

```python
class CharacterSheetPreview(ScrollableContainer):
    character_name: reactive[str | None] = reactive(None)

    def watch_character_name(self, character_name: str | None) -> None:
        """Update preview when character changes."""
        # Load and display character sheet
```

### Grid Sizing

```css
EnhancedTriggerEditor {
    layout: grid;
    grid-size: 3 1;           /* 3 columns, 1 row */
    grid-columns: 1fr 2fr 1.5fr;  /* Proportional widths */
}
```

### Event Handling

```python
def on_option_list_option_selected(self, event: OptionList.OptionSelected):
    """Handle character selection from list."""
    character_name = event.option.id

    # Update all panels
    self.sheet_preview.character_name = character_name
    self.editor_panel.character_name = character_name
```

## Sample Character Data

The mockup includes 3 fully-fleshed characters:

### Silas Mercer
- **Triggers**: Silas, him, he, boyfriend
- **Role**: Detective, Romantic Partner
- **Sheet**: 200+ word detailed character description

### Emma Rodriguez
- **Triggers**: Emma, she, her, sister
- **Role**: Artist, Younger Sister
- **Sheet**: Full background and personality

### Marcus Chen
- **Triggers**: Marcus, he, him, best friend
- **Role**: Detective Partner, Mediator
- **Sheet**: Complete character profile

## Keyboard Shortcuts

- **Arrow Keys**: Navigate character list
- **Enter**: Select character in list
- **Tab**: Navigate between input fields
- **Ctrl+S**: Save all changes (mockup notification)
- **Ctrl+Q**: Quit application

## Integration Plan

To integrate this into the main TUI:

### 1. Create TriggerEditor Component
Extract the enhanced editor as a reusable component:
```python
from .trigger_editor_enhanced_mockup import EnhancedTriggerEditor
```

### 2. Add IPC Integration
Connect to Bridge for data:
```python
def load_characters(self):
    response = ipc_client.send_request(
        IPCMessageType.GET_TRIGGERS
    )
    # Populate character list
```

### 3. Add to Settings Panel or Modal
- **Option A**: Add as tab in settings panel
- **Option B**: Open as full-screen modal (F3)
- **Option C**: Dedicated settings screen

### 4. Implement Persistence
```python
def save_triggers(self, character_name, triggers):
    response = ipc_client.send_request(
        IPCMessageType.SET_TRIGGER,
        character=character_name,
        triggers=triggers
    )
```

## Advantages Over Original

**Original Design:**
- Single-panel table view
- Modals for editing
- No context while editing
- Fixed column widths

**Enhanced Design:**
- Three-panel simultaneous view
- Inline editing without modals
- Live character sheet reference
- Responsive proportional sizing
- Sidebar navigation
- Better workflow for trigger creation

## Color Scheme

Maintains the RP Client aesthetic:
- **Primary**: Wine (#723d46) - Borders, titles
- **Surface**: Sage (#eaeada) - Backgrounds
- **Boost**: Peach Yellow (#ffedcb) - Tips panel
- **Text**: Van Dyke (#472d30) - Text color

## Performance Considerations

- **Reactive Updates**: Only re-render changed panels
- **Scrollable Containers**: Handle large character sheets
- **Dynamic Fields**: Add triggers without full reload
- **Grid Layout**: Efficient layout calculation by Textual

## Future Enhancements

- Character sheet editing inline
- Autocomplete for common triggers
- Highlight trigger mentions in sheet preview
- Import/export trigger sets
- Conflict detection (overlapping triggers)
- Trigger usage statistics
- Bulk operations (copy triggers between characters)
