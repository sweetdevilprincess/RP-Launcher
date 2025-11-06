# Branch Widget Implementation Summary

## Overview
Successfully implemented message-level branching functionality with hover actions in the TUI chat display. Users can now hover over any message to reveal branch/bookmark actions.

## Files Created

### 1. `branchable_message.py`
**Location:** `src/presentation/tui/components/branchable_message.py`

**Features:**
- Displays chat messages with sender-based styling
- Shows action buttons on mouse hover (Branch, Bookmark, More)
- Emits custom messages when actions are triggered
- Maintains message index for branch point identification

**Key Components:**
- `BranchableMessage` widget class
- `BranchRequested` message (bubbles to app)
- `BookmarkRequested` message (bubbles to app)
- Built-in CSS with hover effects

### 2. `branch_creation_dialog.py`
**Location:** `src/presentation/tui/screens/branch_creation_dialog.py`

**Features:**
- Modal dialog for branch creation
- Form fields:
  - Branch name (required)
  - Description (optional)
  - Tags (optional, comma-separated)
  - Switch immediately checkbox (default: true)
- Shows message context (which message is being branched from)
- Validates branch name before submission
- Supports Enter key submission

## Files Modified

### 1. `chat_display.py`
**Changes:**
- Switched from Rich renderables to widget-based approach
- Now mounts `BranchableMessage` widgets directly
- Changed base class from `ScrollableContainer` to `VerticalScroll`
- Tracks `message_count` for indexing
- Automatic message trimming (keeps last 100)

### 2. `components/__init__.py`
**Changes:**
- Added `BranchableMessage` import and export

### 3. `screens/__init__.py`
**Changes:**
- Added `BranchCreationDialog` import and export

### 4. `app.py`
**Changes:**
- Added imports for `BranchableMessage` and `BranchCreationDialog`
- Added event handlers:
  - `on_branchable_message_branch_requested()` - Shows dialog
  - `on_branchable_message_bookmark_requested()` - Placeholder for bookmarks
- Added IPC helper methods:
  - `_create_branch_via_ipc()` - Sends CREATE_BRANCH IPC request
  - `_switch_branch_via_ipc()` - Sends SWITCH_BRANCH IPC request

## How It Works

### User Flow

1. **Hover over message** → Action buttons appear
2. **Click "🌿 Branch"** → Dialog opens
3. **Fill in branch details** → Press Create or Enter
4. **Dialog submits** → IPC request sent to Bridge
5. **Branch created** → Notification shown
6. **Optional auto-switch** → Switches to new branch if checkbox was checked

### Event Flow

```
BranchableMessage (hover)
    ↓
[User clicks "🌿 Branch"]
    ↓
BranchRequested message posted
    ↓
app.on_branchable_message_branch_requested()
    ↓
BranchCreationDialog shown
    ↓
User fills form and submits
    ↓
Dialog returns result dict
    ↓
app._create_branch_via_ipc()
    ↓
IPC request to Bridge
    ↓
CREATE_BRANCH handled by bridge
    ↓
Response received
    ↓
Notification shown to user
    ↓
[Optional] Switch to new branch
```

## CSS Styling

The hover effect is achieved through:
```css
BranchableMessage .message-actions {
    display: none;  /* Hidden by default */
}

BranchableMessage:hover .message-bubble {
    border: solid $accent;  /* Highlight on hover */
}
```

JavaScript-like behavior via Textual events:
- `on_enter()` - Sets `display: block` for actions
- `on_leave()` - Sets `display: none` for actions

## IPC Integration

### CREATE_BRANCH Request
**Parameters:**
- `branch_name` (str) - Required
- `branch_point` (int) - Message index
- `description` (str) - Optional
- `tags` (list[str]) - Optional

**Response:**
- `branch_id` - New branch session ID
- `branch_point` - Confirmed branch point
- `message_count` - Number of messages in new branch

### SWITCH_BRANCH Request
**Parameters:**
- `timeline_id` (str) - Branch ID to switch to

**Response:**
- `timeline_id` - Confirmed timeline ID
- `message` - Success message

## Testing Recommendations

1. **Test hover behavior:**
   - Hover over different message types (you, system, DM)
   - Verify actions appear/disappear correctly
   - Check button click responses

2. **Test dialog:**
   - Submit with only required field (branch name)
   - Submit with all fields filled
   - Test Enter key submission
   - Test Cancel button
   - Test ESC key to dismiss

3. **Test IPC integration:**
   - Create branch and verify backend creates it
   - Test with "switch immediately" checked/unchecked
   - Verify error handling when disconnected
   - Test with invalid branch names

4. **Test message indexing:**
   - Create branches from different message positions
   - Verify correct message count in new branches

## Future Enhancements

1. **Bookmark functionality** - Complete the bookmark feature
2. **More options menu** - Expand the "⋯ More" button
3. **Chat history reload** - Auto-reload messages when switching branches
4. **Visual branch indicators** - Show branch points in chat history
5. **Keyboard shortcuts** - Add hotkeys for branching (e.g., Ctrl+B)
6. **Branch preview** - Show preview of messages at branch point before creating

## Notes

- Messages are automatically trimmed to last 100 for performance
- Message indices persist across the session
- Branch creation is asynchronous via IPC
- Dialog auto-focuses the branch name input
- Tags are parsed from comma-separated string
- Error notifications use severity levels for styling
