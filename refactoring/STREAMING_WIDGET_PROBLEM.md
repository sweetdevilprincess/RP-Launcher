# Textual TUI: Streaming Chat Widget with Hover Events Problem

## Objective
Create a chat message display widget in Textual (Python TUI framework) that supports:
1. **Real-time streaming** - LLM responses appear character-by-character as they arrive
2. **Hover interactions** - Mouse Enter/Leave events show/hide action buttons (Branch, Bookmark, More)
3. **Thread safety** - Messages arrive from both UI thread AND background IPC threads
4. **Chat history** - Scrollable message history with proper styling per sender

## Current Working Implementation (WITHOUT Streaming/Hover)

### Architecture:
```
TUI App (Textual)
    ↓
ChatDisplay (ScrollableContainer)
    ↓
Static widget
    ↓
Rich renderables (Panel, Padding, Align, Group)
```

### How It Works Now:
```python
class ChatDisplay(ScrollableContainer):
    def __init__(self):
        self.message_widget = Static(Group())  # Single Static widget
        self.messages = []  # List of Rich renderables

    def add_message(self, sender: str, content: str):
        # Create Rich Panel with styling
        bubble = Panel(content, title=sender, ...)
        aligned = Align.right/left/center(bubble)  # Based on sender
        padded = Padding(aligned, ...)

        # Append and re-render entire group
        self.messages.append(padded)
        self.message_widget.update(Group(*self.messages))
```

### Message Flow:
```
[UI Thread] User sends message → app.action_submit_message()
    → self.chat_display.add_message("you", message) ✅ Works

[UI Thread] IPC client sends request with callback

[BACKGROUND Thread] IPC receives response → callback(_handle_llm_response)
    → self.chat_display.add_message("claude", response) ✅ Works (surprisingly thread-safe)
```

**Why this works:** `Static.update()` with Rich renderables appears to be thread-safe enough.

**Why this doesn't meet requirements:**
- ❌ Rich renderables (Panel, Padding, Align) are NOT Textual widgets
- ❌ Cannot receive Enter/Leave mouse events (not interactive)
- ❌ Cannot have child buttons/widgets
- ❌ Cannot update incrementally (must recreate entire Group)
- ❌ No streaming support (must show complete message)

## What We Need

### BranchableMessage Widget (Already Created):
```python
class BranchableMessage(Vertical):  # IS a widget, CAN receive events
    def compose(self):
        # Message bubble (Rich Panel wrapped in Static)
        yield Static(self._create_message_bubble())

        # Action buttons (initially hidden)
        with Horizontal(classes="message-actions"):
            yield Button("🌿 Branch")
            yield Button("📍 Bookmark")
            yield Button("⋯ More")

    def on_enter(self, event):
        # Show buttons on hover
        self.query_one(".message-actions").styles.display = "block"

    def on_leave(self, event):
        # Hide buttons
        self.query_one(".message-actions").styles.display = "none"

    def append_content(self, chunk: str):
        # Append chunk for streaming
        self.content += chunk
        # Update the Static widget with new Panel
        self.query_one(".message-bubble").update(self._create_message_bubble())
```

**This widget:**
- ✅ Can receive Enter/Leave events (it's a Vertical widget)
- ✅ Can have action buttons as children
- ✅ Can update content incrementally via `append_content()`
- ✅ Works in isolation when tested

## The Challenge

**We need ChatDisplay to:**
1. Mount BranchableMessage widgets dynamically (not use Static.update() with renderables)
2. Track widgets by ID for streaming updates
3. Be thread-safe (messages arrive from background threads)
4. Support both:
   - Complete messages (non-streaming LLMs)
   - Incremental updates (streaming LLMs)

## What We've Tried (FAILED)

### Attempt 1: Direct Widget Mounting
```python
class ChatDisplay(ScrollableContainer):
    async def add_message(self, sender, content):
        widget = BranchableMessage(sender, content, index)
        await self.mount(widget)
```

**Problem:** `mount()` is async and must be called from UI thread. IPC callbacks run on background threads. Calling `await self.mount()` from background thread crashes or doesn't work.

### Attempt 2: Message Passing (Current Implementation)
```python
# Created AddMessageRequest and UpdateMessageRequest messages
# App posts messages: self.chat_display.post_message(AddMessageRequest(...))
# ChatDisplay has handlers: async def on_add_message_request(self, event)
```

**Problem:** Textual's `post_message()` sends messages UP the widget tree (to parents), not DOWN. When App calls `self.chat_display.post_message(...)`, it posts FROM ChatDisplay upward to App, so ChatDisplay's handler never receives it. Messages don't appear.

### Attempt 3: Various Container Types
- Tried `VerticalScroll` instead of `ScrollableContainer` - widgets don't appear
- Tried `Vertical` container with mounting - widgets don't appear
- Tried mounting to `Static` widget - widgets don't appear

**Mystery:** Widgets seem to mount (no errors) but don't render/display.

## Technical Constraints

### Textual Framework Rules:
1. **Widget mounting** - `mount()` is async, must be called from UI thread
2. **Message bubbling** - `post_message()` sends messages UP tree, not down
3. **Thread safety** - Most widget methods are NOT thread-safe
4. **Event handling** - Enter/Leave events only work on Widget subclasses, not Rich renderables

### Our Application Constraints:
1. **IPC callbacks run on background threads** - We cannot change this
2. **Must support both streaming and non-streaming LLMs**
3. **Need to maintain message history** (100 message limit with trimming)
4. **Message indexing** - Messages need index numbers for branch points

## Thread Safety Approaches Available

Textual provides:
1. **`app.call_from_thread(func, *args)`** - Schedule function to run on UI thread
2. **`post_message()`** - Thread-safe, but bubbles upward
3. **`run_worker()`** - Run async work in background, update UI safely

## Questions for LLMs

1. **How do we properly mount widgets dynamically from background threads in Textual?**
   - Should we use `call_from_thread()` with mount?
   - Should handlers be on App level instead of ChatDisplay level?

2. **Why don't mounted widgets appear even when no errors occur?**
   - Do we need specific CSS for dynamic widgets?
   - Is there a refresh/update call we're missing?

3. **What's the correct architecture for this pattern?**
   - Widget that displays chat messages
   - Messages arrive from background threads
   - Support incremental updates (streaming)
   - Support hover events

4. **Alternative approaches?**
   - Custom widget that wraps Rich renderable but receives events?
   - Overlay transparent widget on top of Rich renderables?
   - Different container hierarchy?

## Files Involved

- `src/presentation/tui/components/chat_display.py` - Main chat container
- `src/presentation/tui/components/branchable_message.py` - Message widget with hover
- `src/presentation/tui/components/chat_messages.py` - Message event classes
- `src/presentation/tui/app.py` - Main app, handles IPC callbacks
- `src/infrastructure/ipc/socket_client.py` - Background thread IPC receiver

## What Works / What Doesn't

✅ **Works:**
- BranchableMessage widget renders in isolation
- Enter/Leave events work on BranchableMessage
- Rich renderable approach (current, but no hover/streaming)
- IPC communication and callbacks

❌ **Doesn't Work:**
- Dynamically mounting BranchableMessage widgets (they don't appear)
- Message passing architecture (messages not received)
- Calling mount() from background threads
- Streaming updates to existing messages

## Success Criteria

We'll know it works when:
1. ✅ User sends message → message appears immediately
2. ✅ LLM response streams in character-by-character in real-time
3. ✅ Hovering over any message shows action buttons
4. ✅ Clicking "Branch" button opens dialog
5. ✅ All of this is thread-safe (no crashes from background threads)
