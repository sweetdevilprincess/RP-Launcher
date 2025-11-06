# Branching Implementation Handoff Document

## Current Goal
Implement hover-based branching functionality in the TUI chat display. Users should be able to hover over any message to reveal action buttons (Branch, Bookmark, More), with the Branch button opening a dialog to create a new timeline branch from that message.

## What's Currently Working ✅
1. **Chat display works normally** - messages appear and scroll correctly with Rich Panel renderables
2. **Module registry updated** - Core modules (template_system, trigger_system, agent_coordinator, character_preferences) are now correctly marked as non-toggleable
3. **Branch creation dialog exists** - `branch_creation_dialog.py` is fully implemented
4. **BranchableMessage widget exists** - `branchable_message.py` with hover actions is coded
5. **IPC handlers exist** - App has handlers for branch creation in `app.py` (lines 493-627)
6. **Backend branch system works** - Branch creation via IPC is functional

## What's NOT Working ❌
**THE CORE PROBLEM:** When we try to use BranchableMessage widgets instead of Rich renderables, **messages don't appear in the chat window**. The app:
- Starts fine (no crashes)
- Accepts input (you can type)
- Sends messages (no errors)
- But the chat window **stays blank** - no messages visible

**IMPORTANT:** The user specifically clarified this is NOT a startup crash. The app runs, they can send messages, but nothing shows up.

## Files Involved

### Created/Modified Files:
1. **`branchable_message.py`** - Widget with hover actions (CREATED)
   - Location: `src/presentation/tui/components/branchable_message.py`
   - Has Enter/Leave event handlers
   - Yields Static (with Panel) + Horizontal (with Buttons)
   - Uses `on_enter()` to show actions, `on_leave()` to hide

2. **`branch_creation_dialog.py`** - Modal for creating branches (CREATED)
   - Location: `src/presentation/tui/screens/branch_creation_dialog.py`
   - Works correctly, tested in isolation

3. **`chat_display.py`** - Currently REVERTED to original working version
   - Location: `src/presentation/tui/components/chat_display.py`
   - Uses Rich renderables (Panel, Padding, Align, Group)
   - Works perfectly but doesn't support hover events

4. **`app.py`** - Has branch event handlers (MODIFIED)
   - Added `on_branchable_message_branch_requested()` handler
   - Added `_create_branch_via_ipc()` method
   - Added `_switch_branch_via_ipc()` method

5. **`module_registry.py`** - Core modules fixed (MODIFIED)
   - Lines 90, 92: template_system now CORE, toggleable=False
   - Lines 99, 101: trigger_system now CORE, toggleable=False
   - Lines 108, 110: agent_coordinator now CORE, toggleable=False
   - Lines 117, 119: character_preferences now CORE, toggleable=False

## What We've Tried (ALL FAILED)

### Attempt 1: Changed ChatDisplay to use VerticalScroll
- **What:** Changed base class from `ScrollableContainer` to `VerticalScroll`
- **Why it failed:** Got compose() error - but also messages didn't appear
- **Reverted:** Yes

### Attempt 2: Empty compose() with `yield from ()`
- **What:** Made compose() an empty generator: `yield from ()`
- **Why it failed:** Still got compose errors
- **Reverted:** Yes

### Attempt 3: Used Vertical container inside ScrollableContainer
- **What:**
  ```python
  def compose(self):
      self.message_container = Vertical(id="message-container")
      yield self.message_container
  ```
- **Why it failed:** Messages didn't appear (blank chat)
- **Reverted:** Yes

### Attempt 4: Used Static widget as container
- **What:**
  ```python
  def compose(self):
      self.message_container = Static(id="message-container")
      yield self.message_container
  ```
  Then mounted BranchableMessage widgets to it
- **Why it failed:** Messages didn't appear (blank chat)
- **Note:** User specifically suggested trying Static widget, but assistant ignored this initially
- **Reverted:** Yes

## Current Working Implementation (chat_display.py)

```python
class ChatDisplay(ScrollableContainer):
    def __init__(self):
        self.message_widget: Static | None = None
        self.messages: list[RenderableType] = []

    def compose(self):
        self.message_widget = Static(Group(), id="message-content")
        yield self.message_widget

    def add_message(self, sender, content):
        # Create Rich Panel
        bubble = Panel(...)  # Styled panel
        aligned = Align.right/center/left(bubble)
        padded = Padding(aligned, ...)

        self.messages.append(padded)
        self.message_widget.update(Group(*self.messages))
```

**Why this works:** Static.update() with Rich renderables

**Why we can't use it for branching:** Rich renderables (Panel, Padding, Align) are NOT Textual widgets, so they CANNOT receive Enter/Leave events

## BranchableMessage Widget Structure

```python
class BranchableMessage(Vertical):
    def compose(self):
        # Message bubble
        yield Static(
            self._create_message_bubble(),  # Returns Rich Panel
            classes="message-bubble"
        )

        # Action buttons (hidden by default)
        with Horizontal(classes="message-actions"):
            yield Button("🌿 Branch", ...)
            yield Button("📍 Bookmark", ...)
            yield Button("⋯ More", ...)

    def on_enter(self, event):
        actions = self.query_one(".message-actions")
        actions.styles.display = "block"

    def on_leave(self, event):
        actions = self.query_one(".message-actions")
        actions.styles.display = "none"
```

## Key Technical Facts

### Enter/Leave Events
- Only work on **Textual Widget** classes
- Do NOT work on **Rich renderables** (Panel, Padding, Align, Group)
- Static IS a widget and CAN receive events
- Vertical IS a widget and CAN receive events
- Containers (Vertical, Horizontal, Container) ARE widgets and CAN receive events

### Widget vs Renderable
- **Widget:** Textual class that can have events, compose children, etc.
  - Examples: Static, Button, Container, Vertical, Horizontal
- **Renderable:** Rich object for display only, no events
  - Examples: Panel, Text, Padding, Align, Group

### Static Widget Limitations
According to Textual docs:
- Static is "primarily designed for displaying Rich renderables"
- Static CAN hold child widgets (it's marked as a Container)
- BUT Static is "not the intended tool for managing dynamic, interactive child widgets"
- For dynamic widgets, use Vertical/Container instead

## The Mystery

**Why don't the BranchableMessage widgets appear when mounted?**

Theories:
1. ~~Compose error~~ - No, user confirmed app starts fine
2. ~~Container type wrong~~ - Tried Vertical, Static, VerticalScroll - all blank
3. **Rendering issue?** - Widgets mount but don't render?
4. **CSS issue?** - Something hiding them?
5. **Layout issue?** - Widgets have 0 height/width?

**What we DON'T know:**
- Are the widgets actually mounting? (No error suggests yes)
- Are they just invisible due to CSS?
- Is there a layout computation issue?
- Do we need to call refresh() or some update method?

## What Needs Investigation

1. **Test BranchableMessage in isolation** - Does it render at all in a simple app?
2. **Check widget tree** - Are BranchableMessages in the DOM when inspected?
3. **CSS debugging** - Are they being hidden by display:none or height:0?
4. **Layout debugging** - Do they have any computed size?

## Potential Solutions Not Yet Tried

### Option A: Debug why widgets don't appear
- Create minimal test app with just BranchableMessage
- Use Textual DevTools to inspect DOM
- Check if widgets are mounted but invisible
- Look for CSS/layout issues

### Option B: Hybrid approach
- Keep Rich renderables for messages
- Add invisible overlay widgets that capture Enter/Leave
- Overlay positioned on top of messages
- More complex but might work

### Option C: Always-visible buttons
- No hover, just show small buttons below each message always
- Simple, guaranteed to work
- Takes more space

### Option D: Different event approach
- Use click events instead of hover
- Click message to show action menu
- Less elegant but functional

## Cache Clearing
**IMPORTANT:** When testing changes, always clear Python cache:
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
```

Background processes use cached bytecode, so changes won't apply without clearing cache.

## Assistant Mistakes to Avoid

1. **Not listening to user suggestions** - User suggested Static widget, assistant ignored it
2. **Repeating failed approaches** - Suggested Vertical again after already trying it
3. **Misunderstanding the problem** - Kept thinking it was a startup crash when user said messages just don't appear
4. **Not reviewing past attempts** - Kept suggesting things already tried

## Next Steps Recommendation

1. **Create minimal test** - Single file with just BranchableMessage to see if it renders at all
2. **If it renders in test** - Issue is integration with ChatDisplay
3. **If it doesn't render in test** - Issue is in BranchableMessage itself
4. **Use Textual DevTools** - Inspect DOM to see if widgets exist but are hidden
5. **Check CSS** - Look for any styles that might be hiding content

## Questions to Answer

1. Does BranchableMessage render in a simple test app?
2. When mounted to ChatDisplay containers, do the widgets appear in the DOM?
3. If in DOM, what's their computed height/width?
4. Are there any CSS rules hiding them?
5. Does the Static.update() method need to be called for child widgets?

## Contact User About

- Whether they want to try minimal test approach
- Whether they prefer a different UI pattern (always-visible buttons, click instead of hover)
- Whether they have Textual DevTools available for debugging
