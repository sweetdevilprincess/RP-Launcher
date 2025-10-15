# File Change Tracking System

## Problem Solved

When DeepSeek auto-generates or updates files (entity cards, story arcs, etc.), Claude Code doesn't know the files have changed. The files are reloaded each turn, but Claude doesn't receive any notification that they're **new** or **updated**, so it might not pay attention to the changes.

This system solves that by:
1. **Tracking file modification times**
2. **Detecting when files are updated**
3. **Notifying Claude explicitly** about file changes
4. **Marking auto-generated files** for special handling

---

## How It Works

### 1. File Change Tracker (`file_change_tracker.py`)

The `FileChangeTracker` class:
- Tracks modification times of all RP files
- Stores tracking data in `state/file_changes.json`
- Compares current mtimes to last-seen mtimes
- Generates formatted notifications for Claude

### 2. Integration with WIP Bridge

The WIP bridge now:
1. **Initializes tracker** at the start of automation
2. **Checks for updates** before building the prompt
3. **Generates notifications** if files were updated
4. **Adds notifications to prompt** (highest priority!)
5. **Marks files** as auto-generated when DeepSeek creates them

### 3. Notification Format

When files are updated, Claude receives:

```markdown
<!-- ========================================
📢 FILE UPDATE NOTIFICATIONS
======================================== -->

⚠️ **IMPORTANT: The following files have been UPDATED since you last saw them:**

## 🎭 Character/Entity Updates
- **[CHAR] Marcus.md** [AUTO-GENERATED]
  - Last seen: 2025-10-13 14:30:15
  - Updated at: 2025-10-13 14:35:42
  - ⚠️ **REREAD this file carefully - content has changed!**

## 📖 Story Arc Updates
- **story_arc.md** [AUTO-GENERATED]
  - Updated at: 2025-10-13 14:35:50
  - ⚠️ **Story arc has been regenerated - review new direction!**

**Action Required:**
1. Carefully REREAD all updated files above
2. Acknowledge any new information or changes
3. Integrate updates into your understanding of the story
<!-- ======================================== -->
```

---

## Features

### Automatic Detection

The tracker automatically detects updates to:
- **Entity cards** (`entities/*.md`, `characters/*.md`)
- **Story arcs** (`state/story_arc.md`)
- **State files** (`state/current_state.md`)
- **Core RP files** (`AUTHOR'S_NOTES.md`, `STORY_GENOME.md`, etc.)
- **Recent chapters** (last 5 chapters)

### Smart Categorization

Files are categorized for better notifications:
- `entity` - Characters, locations, items
- `story_arc` - Story arc files
- `state` - Current state and other state files
- `chapter` - Chapter summaries
- `other` - Misc files

### Auto-Generated Marking

When DeepSeek generates files, they're marked as `auto_generated`:
- Shows `[AUTO-GENERATED]` tag in notifications
- Tracked in `file_changes.json`
- Helps Claude know which content is AI-generated vs user-edited

---

## Usage

### In WIP Bridge (Already Integrated)

The system works automatically! Just use the WIP bridge:

```bash
python wip/tui_bridge.py "Example RP"
```

The file tracker will:
1. Track all files as they're loaded
2. Detect when files are updated (by DeepSeek or manually)
3. Notify Claude on the next turn
4. Mark DeepSeek-generated files automatically

### Manual Usage (Advanced)

```python
from file_change_tracker import FileChangeTracker

# Initialize
tracker = FileChangeTracker(rp_dir)

# Check for updates
files_to_check = [
    rp_dir / "entities" / "[CHAR] Marcus.md",
    rp_dir / "state" / "story_arc.md"
]

updates, updated_files = tracker.check_files_for_updates(files_to_check)

# Generate notification
if updates:
    notification = tracker.generate_update_notification(updates)
    # Add notification to prompt...

# Mark file as auto-generated
card_file = rp_dir / "entities" / "[CHAR] NewCharacter.md"
tracker.mark_file_as_auto_generated(card_file)
```

---

## Tracking Data

File tracking data is stored in `state/file_changes.json`:

```json
{
  "entities/[CHAR] Marcus.md": {
    "mtime": 1728841542.123456,
    "auto_generated": true,
    "generated_at": "2025-10-13T14:35:42"
  },
  "state/story_arc.md": {
    "mtime": 1728841550.789012,
    "auto_generated": true,
    "generated_at": "2025-10-13T14:35:50"
  }
}
```

**Note**: This file is automatically managed - you don't need to edit it manually!

---

## Benefits

### 1. **Claude Actually Notices Updates**
- Before: Claude might ignore updated files
- After: Explicit notifications ensure Claude sees changes

### 2. **Transparency**
- Shows when files were updated
- Marks auto-generated content
- Provides timestamps

### 3. **Better Context Integration**
- Claude is prompted to REREAD updated files
- Claude acknowledges changes in responses
- Better story continuity

### 4. **Debugging**
- Log shows all detected file updates
- Easy to track what changed when
- Helps troubleshoot issues

---

## Examples

### Example 1: Entity Card Update

**Scenario**: DeepSeek updates Marcus's character card to note he got a new job.

**What Happens**:
1. Turn 1: Marcus card updated by DeepSeek
2. Turn 2 (next user message):
   - File tracker detects change
   - Notification injected into prompt
   - Claude sees: "⚠️ **REREAD this file carefully - content has changed!**"
   - Claude responds: "I see Marcus's character card was updated - he's now working at Morrison Law Firm instead of Coffee Corner Cafe..."

### Example 2: Story Arc Regeneration

**Scenario**: After 50 responses, story arc auto-regenerates.

**What Happens**:
1. Response 50: Arc generation triggered
2. DeepSeek creates new `story_arc.md`
3. File marked as auto-generated
4. Turn 51 (next user message):
   - Notification: "Story arc has been regenerated - review new direction!"
   - Claude reads updated arc
   - Claude adjusts story direction accordingly

### Example 3: Manual Edit

**Scenario**: User manually edits `AUTHOR'S_NOTES.md`.

**What Happens**:
1. User edits file in editor
2. Saves changes
3. Next turn:
   - File tracker detects change
   - Notification shown (without `[AUTO-GENERATED]` tag)
   - Claude sees the manual changes

---

## Configuration

The system works out of the box with sensible defaults, but you can customize:

### Tracked Files

By default, tracks:
- All characters (`characters/*.md`)
- All entities (`entities/*.md`)
- State files (`state/current_state.md`, `state/story_arc.md`)
- Core RP files (`AUTHOR'S_NOTES.md`, etc.)
- Recent chapters (last 5)

To track more/different files, modify `track_all_rp_files()` in `file_change_tracker.py`.

### Notification Format

To customize notifications, modify `generate_update_notification()` in `file_change_tracker.py`.

---

## Testing

Test the file change tracker:

```bash
cd wip
python -c "
from pathlib import Path
from file_change_tracker import FileChangeTracker

# Initialize
rp_dir = Path('../Example RP')
tracker = FileChangeTracker(rp_dir)

# Check for updates
files = tracker.track_all_rp_files()
updates, updated_files = tracker.check_files_for_updates(files)

print(f'Checked {len(files)} files')
print(f'Found {len(updates)} updates')

if updates:
    print(tracker.generate_update_notification(updates))
"
```

---

## Logs

File change activity is logged to `state/hook.log`:

```
[2025-10-13 14:35:42] --- Checking for file updates ---
[2025-10-13 14:35:42] File updates detected: 2 files
[2025-10-13 14:35:42]   - [CHAR] Marcus.md (entity)
[2025-10-13 14:35:42]   - story_arc.md (story_arc)
```

---

## Future Enhancements

Possible improvements:
- **Change summaries**: Diff the files and show what changed
- **Smart reloading**: Only reload changed files in TIER_1
- **Change history**: Track multiple versions with diffs
- **Selective notifications**: Notify only for significant changes

---

## Technical Details

### Performance

- **Fast**: Only checks mtimes (no file reading)
- **Lightweight**: Minimal overhead (<1ms)
- **Cached**: Tracking data persisted between sessions

### File Format

- **Tracking**: JSON format in `state/file_changes.json`
- **Portable**: Relative paths, works across systems
- **Resilient**: Handles missing/deleted files gracefully

### Integration Points

1. **Entity generation** (`auto_generate_entity_card()`)
   - Marks files as auto-generated
   - Updates mtime tracking

2. **Automation** (`run_automation_with_caching()`)
   - Checks files before building prompt
   - Generates notifications
   - Logs detected changes

3. **Prompt building**
   - Notifications added at highest priority
   - Appears before all other content
   - Claude sees it first!

---

**The file change tracking system ensures Claude never misses important updates to your RP files!** 📢
