Got you — this is a classic Textual pattern clash: **widgets and messages want to live on the UI thread**, while your **chunks arrive on background threads**. The clean fix is:

* **Never mount/update widgets from a background thread.**
* **Don’t try to “post down”** the tree — `post_message()` bubbles upward by design.
* Use **`App.call_from_thread(...)`** (or `self.app.call_from_thread(...)` from any widget) to schedule *UI-thread* methods that do mounting and incremental updates.
* Give the chat view a **dedicated child container** to mount into (so layout is stable) and always mount **after** `on_mount` (or from `compose`).

Below is a drop-in, minimal but complete pattern you can adapt. It solves:

* dynamic mounting
* streaming (char/word chunks)
* hover show/hide buttons
* message indexing + trimming
* thread safety from IPC/background

---

# ✅ Reference Implementation

### `branchable_message.py`

```python
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button
from rich.panel import Panel
from rich.padding import Padding
from rich.align import Align

class BranchableMessage(Vertical):
    """A single chat bubble + hover actions, streamable."""

    # Keep message text as reactive so a re-render is cheap and automatic
    content: str = reactive("")
    sender: str = reactive("")

    DEFAULT_CSS = """
    BranchableMessage {
        width: 100%;
        padding: 0 1;
    }
    BranchableMessage > .message-actions {
        display: none;
        height: auto;
        layout: horizontal;
        content-align: right middle;
        padding: 0 1;
    }
    BranchableMessage:hover > .message-actions {
        display: block;
    }
    """

    def __init__(self, message_id: str, sender: str, initial: str = "", align: str = "left"):
        super().__init__(id=message_id)
        self.sender = sender
        self.content = initial
        self._align = align  # "left" or "right"

    def _bubble(self):
        bubble = Panel(
            self.content or "",              # rich renderable content
            title=self.sender,
            border_style="bright_black" if self.sender != "you" else "green",
            title_align="left" if self._align == "left" else "right",
            padding=(0, 1),
        )
        aligned = Align.left(bubble) if self._align == "left" else Align.right(bubble)
        return Padding(aligned, (0, 0))

    def compose(self):
        # The text bubble
        yield Static(self._bubble(), classes="message-bubble")

        # Hover actions (hidden by default via CSS)
        with Horizontal(classes="message-actions"):
            yield Button("🌿 Branch", id="branch")
            yield Button("📍 Bookmark", id="bookmark")
            yield Button("⋯ More", id="more")

    # ——— Streaming ———
    def append_content(self, chunk: str) -> None:
        self.content += chunk  # triggers watch_content

    def set_content(self, text: str) -> None:
        self.content = text    # triggers watch_content

    # ——— Reactive hook ———
    def watch_content(self, _old: str, _new: str) -> None:
        # Re-render bubble in place; stays on UI thread
        self.query_one(".message-bubble", Static).update(self._bubble())
```

---

### `chat_display.py`

```python
from typing import Dict, Deque
from collections import deque
from textual.containers import ScrollableContainer, Vertical
from textual.app import ComposeResult
from textual.widget import Widget
from .branchable_message import BranchableMessage

MAX_MESSAGES = 100

class ChatDisplay(ScrollableContainer):
    """Scrollable chat history that mounts BranchableMessage widgets."""

    DEFAULT_CSS = """
    ChatDisplay {
        height: 1fr;
        overflow-y: auto;
        background: $panel;
    }
    #messages {
        width: 100%;
        padding: 1 0;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._messages_v: Vertical | None = None
        self._by_id: Dict[str, BranchableMessage] = {}
        self._order: Deque[str] = deque()

    def compose(self) -> ComposeResult:
        # A stable child container to mount messages into.
        yield Vertical(id="messages")

    def on_mount(self) -> None:
        self._messages_v = self.query_one("#messages", Vertical)

    # ——————————————————————————————————————————
    # UI-THREAD methods (safe to call ONLY via call_from_thread from bg threads)
    # ——————————————————————————————————————————

    def _ensure_unique(self, message_id: str) -> None:
        if message_id in self._by_id:
            return

    async def _ui_add_message(self, message_id: str, sender: str, initial: str = "", align: str = "left"):
        """UI-thread: create and mount a BranchableMessage."""
        self._ensure_unique(message_id)
        msg = BranchableMessage(message_id=message_id, sender=sender, initial=initial, align=align)
        self._by_id[message_id] = msg
        self._order.append(message_id)
        await self._messages_v.mount(msg)
        await self.scroll_end(animate=False, force=True)
        self._trim_if_needed()

    async def _ui_append_chunk(self, message_id: str, chunk: str):
        """UI-thread: append streaming text to an existing message."""
        msg = self._by_id.get(message_id)
        if msg is None:
            # Late chunk for a message we don't have yet:
            # create it empty and then append so nothing is lost.
            await self._ui_add_message(message_id, sender="claude", initial="", align="left")
            msg = self._by_id[message_id]
        msg.append_content(chunk)
        await self.scroll_end(animate=False, force=True)

    async def _ui_finish_message(self, message_id: str):
        """UI-thread: finalize a message (optional: apply post-processing)."""
        # placeholder for markdown parse, syntax highlight, etc.
        pass

    def _trim_if_needed(self):
        while len(self._order) > MAX_MESSAGES:
            oldest_id = self._order.popleft()
            widget = self._by_id.pop(oldest_id, None)
            if widget:
                widget.remove()

    # ——————————————————————————————————————————
    # THREAD-SAFE public API (call from ANY thread, including IPC)
    # ——————————————————————————————————————————

    def add_message(self, message_id: str, sender: str, initial: str = "", align: str = "left"):
        """Thread-safe: schedule a UI-thread mount."""
        self.app.call_from_thread(self.run_worker, self._ui_add_message(message_id, sender, initial, align), thread=False)

    def append_chunk(self, message_id: str, chunk: str):
        """Thread-safe: schedule a UI-thread content append."""
        self.app.call_from_thread(self.run_worker, self._ui_append_chunk(message_id, chunk), thread=False)

    def finish_message(self, message_id: str):
        """Thread-safe: schedule a UI-thread finalize step."""
        self.app.call_from_thread(self.run_worker, self._ui_finish_message(message_id), thread=False)
```

> Notes
>
> * `run_worker(coro, thread=False)` is a convenient way to schedule an async UI coroutine from the UI loop. We wrap it in `call_from_thread(...)` so **background threads** can request it safely.
> * If you prefer, you can skip `run_worker` and use `self.app.call_from_thread(self.call_later, self._ui_append_chunk, ...)` in newer Textuals — either way, the important bit is **“schedule on UI thread.”**

---

### `app.py` (the mediator)

```python
from textual.app import App
from textual.containers import Vertical
from .components.chat_display import ChatDisplay

class ChatApp(App):
    CSS = """
    Screen { layout: vertical; }
    """

    def compose(self):
        yield ChatDisplay(id="chat")

    def on_mount(self):
        self.chat: ChatDisplay = self.query_one("#chat", ChatDisplay)

    # ————— Example: user sends a complete message (UI thread) —————
    def action_submit_message(self, text: str):
        message_id = f"user-{self._next_id()}"
        self.chat.add_message(message_id, sender="you", initial=text, align="right")

    # ————— Example: LLM streaming from a BACKGROUND thread —————
    def handle_llm_stream_from_ipc(self, stream, mid: str):
        """This is called on a background IPC thread."""
        # Create the placeholder message on first chunk:
        self.chat.add_message(mid, sender="claude", initial="", align="left")
        for chunk in stream:
            self.chat.append_chunk(mid, chunk)
        self.chat.finish_message(mid)

    # ——— minor utility ———
    _id_counter = 0
    def _next_id(self):
        self.__class__._id_counter += 1
        return self.__class__._id_counter
```

---

## Why your earlier attempts failed

1. **`mount()` from background thread**
   Textual is single-threaded for UI. Mount/update must be on the UI loop. Calling `await self.mount(...)` in a non-UI thread either no-ops or explodes.

2. **`post_message()` “down” the tree**
   In Textual, `post_message()` **bubbles upward** from the sender to parents. Posting a message *to* `ChatDisplay` from `App` doesn’t route *into* it. That’s by design. For cross-tree dispatch, **directly call methods via `app.call_from_thread(...)`** (as above) or have the intended receiver be a **parent** and use message bubbling.

3. **Mounted widgets not appearing**
   Common culprits:

   * Mounting **before** the container exists (e.g., doing work in `__init__`, not after `compose`/`on_mount`).
   * Mounting into a widget you never yielded (no stable container).
   * Styles that collapse layout (e.g., `display:none` or zero height).
     The `compose()` → `on_mount()` → `mount(child)` pattern in the code above ensures predictable layout, and `ScrollableContainer` + a nested `Vertical` works reliably.

---

## Recommended Architecture (TL;DR)

* **`ChatDisplay`** owns a `Vertical#messages` container and a `dict` of `message_id → BranchableMessage`.
* **Only UI-thread methods** perform `mount()`, `remove()`, and content updates on widgets.
* **Public “thread-safe” wrappers** (`add_message`, `append_chunk`, `finish_message`) simply do:
  `self.app.call_from_thread(self.run_worker, self._ui_..., thread=False)`
* **IPC/background** producers call those thread-safe wrappers freely.
* **Hover buttons** are pure CSS: `.message-actions { display: none }` + `:hover` to show.
  You can still manually show/hide in `on_enter/on_leave`, but CSS hover is simpler and flicker-free.

---

## Optional Enhancements

* **Markdown rendering:** in `finish_message`, parse the final text to a `rich.markdown.Markdown` before updating the bubble.
* **Auto-scroll only if at bottom:** track whether the user has scrolled up; only call `scroll_end()` when they’re at the end.
* **Virtualization:** switch to `ListView`/`ListItem` if you anticipate thousands of messages.
* **Actions wiring:** handle `on_button_pressed` inside `BranchableMessage` and bubble an `ActionRequested` custom `Message` upward to the `App` for modals/branching dialogs.

---

## Quick sanity checklist

* [x] All UI mutations scheduled on UI thread (`call_from_thread(...)`)
* [x] Messages mounted into a real child container yielded in `compose()`
* [x] Streaming uses `append_chunk()` which only touches UI on UI thread
* [x] Hover buttons appear via CSS (no extra work)
* [x] 100-message trim removes widgets safely

If you paste these three files into your project (adjust imports/paths), you should see:

1. user messages appear instantly,
2. LLM responses stream smoothly,
3. hover actions show/hide,
4. no thread crashes.

If anything still acts up, drop me your `Textual` version and the exact CSS you’re using in the chat area — tiny style differences (like `display: none` on a parent) can invisibly swallow mounts.
