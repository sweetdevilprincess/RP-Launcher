Looking at your problem, I can see the core issues and provide a solution. The main problems are:

1. **Message passing direction** - `post_message()` bubbles up, not down
2. **Thread safety** - Background threads can't directly call UI methods
3. **Widget mounting** - Dynamic widgets need proper container management

Here's the complete solution:

## Solution 1: Fix Message Passing Architecture

### Create Proper Message Classes

```python
# src/presentation/tui/components/chat_messages.py
from textual.message import Message

class AddMessageRequest(Message):
    """Message to add a new chat message"""
    def __init__(self, sender: str, content: str, stream_id: str = None):
        self.sender = sender
        self.content = content
        self.stream_id = stream_id
        super().__init__()

class UpdateMessageRequest(Message):
    """Message to update an existing message (for streaming)"""
    def __init__(self, stream_id: str, chunk: str):
        self.stream_id = stream_id
        self.chunk = chunk
        super().__init__()
```

### Fix ChatDisplay to Handle Messages Properly

```python
# src/presentation/tui/components/chat_display.py
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from textual import work
from .branchable_message import BranchableMessage
from .chat_messages import AddMessageRequest, UpdateMessageRequest

class ChatDisplay(VerticalScroll):  # Use VerticalScroll instead of ScrollableContainer
    """Chat display that supports streaming and hover events"""
    
    def __init__(self):
        super().__init__()
        self.messages = []  # List of BranchableMessage widgets
        self.streaming_messages = {}  # stream_id -> BranchableMessage
        self.message_count = 0
    
    def compose(self) -> ComposeResult:
        # This creates the empty container that will hold our messages
        yield Static("", id="message-container")
    
    async def on_add_message_request(self, event: AddMessageRequest) -> None:
        """Handle add message request - called from UI thread"""
        await self._add_message(event.sender, event.content, event.stream_id)
        event.stop()
    
    async def on_update_message_request(self, event: UpdateMessageRequest) -> None:
        """Handle update message request - called from UI thread"""
        await self._update_message(event.stream_id, event.chunk)
        event.stop()
    
    async def _add_message(self, sender: str, content: str, stream_id: str = None) -> None:
        """Add a new message widget"""
        self.message_count += 1
        message_widget = BranchableMessage(
            sender=sender, 
            content=content,
            index=self.message_count,
            stream_id=stream_id
        )
        
        # Add to our tracking
        self.messages.append(message_widget)
        if stream_id:
            self.streaming_messages[stream_id] = message_widget
        
        # Mount the widget
        container = self.query_one("#message-container", Static)
        await container.mount(message_widget)
        
        # Scroll to bottom
        self.scroll_end()
        
        # Trim history if needed (keep last 100 messages)
        if len(self.messages) > 100:
            oldest = self.messages.pop(0)
            await oldest.remove()
    
    async def _update_message(self, stream_id: str, chunk: str) -> None:
        """Update an existing streaming message"""
        if stream_id in self.streaming_messages:
            message_widget = self.streaming_messages[stream_id]
            message_widget.append_content(chunk)
            self.scroll_end()
```

### Fix Your App to Route Messages Correctly

```python
# src/presentation/tui/app.py
from textual.app import App
from textual import work
from .components.chat_display import ChatDisplay
from .components.chat_messages import AddMessageRequest, UpdateMessageRequest

class TUIApp(App):
    def __init__(self):
        super().__init__()
        self.chat_display = None
    
    def compose(self) -> ComposeResult:
        self.chat_display = ChatDisplay()
        yield self.chat_display
    
    def on_mount(self) -> None:
        # Your existing IPC setup
        self.setup_ipc()
    
    def setup_ipc(self):
        # Your existing IPC setup, but use the new safe methods
        pass
    
    # THREAD-SAFE METHODS for background threads to call
    def safe_add_message(self, sender: str, content: str, stream_id: str = None):
        """Thread-safe method to add a message"""
        # This can be called from ANY thread
        self.call_from_thread(
            self.post_message,
            AddMessageRequest(sender, content, stream_id)
        )
    
    def safe_update_message(self, stream_id: str, chunk: str):
        """Thread-safe method to update a streaming message"""
        # This can be called from ANY thread
        self.call_from_thread(
            self.post_message, 
            UpdateMessageRequest(stream_id, chunk)
        )
    
    # Your existing methods, updated to use thread-safe approach
    async def action_submit_message(self, message: str):
        # User sends message - we're on UI thread so direct call is fine
        await self.chat_display._add_message("you", message)
        
        # Send to IPC
        self.ipc_client.send_message(message)
    
    def _handle_llm_response(self, response: str, stream_id: str = None):
        """IPC callback - runs on background thread"""
        if stream_id:
            # Streaming response
            for chunk in self.simulate_streaming(response):
                self.safe_update_message(stream_id, chunk)
        else:
            # Complete response
            self.safe_add_message("claude", response)
    
    def simulate_streaming(self, text: str):
        """Simulate streaming for testing"""
        words = text.split()
        for i, word in enumerate(words):
            if i == 0:
                yield word
            else:
                yield " " + word
            # Simulate network delay
            import time
            time.sleep(0.1)
```

## Solution 2: Alternative Direct Call Approach

If message passing feels too complex, here's a simpler alternative:

```python
# Simplified ChatDisplay with direct thread-safe calls
class ChatDisplay(VerticalScroll):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.streaming_messages = {}
        self.message_count = 0
    
    def compose(self) -> ComposeResult:
        yield Static("", id="message-container")
    
    @work(thread=True)  # This makes the method thread-safe
    async def add_message(self, sender: str, content: str, stream_id: str = None):
        """Thread-safe method that can be called from any thread"""
        self.message_count += 1
        message_widget = BranchableMessage(
            sender=sender, 
            content=content,
            index=self.message_count, 
            stream_id=stream_id
        )
        
        self.messages.append(message_widget)
        if stream_id:
            self.streaming_messages[stream_id] = message_widget
        
        container = self.query_one("#message-container", Static)
        await container.mount(message_widget)
        self.scroll_end()
        
        if len(self.messages) > 100:
            oldest = self.messages.pop(0)
            await oldest.remove()
    
    @work(thread=True)
    async def update_message(self, stream_id: str, chunk: str):
        """Thread-safe method to update streaming message"""
        if stream_id in self.streaming_messages:
            message_widget = self.streaming_messages[stream_id]
            message_widget.append_content(chunk)
            self.scroll_end()
```

Then in your app:
```python
# In background thread callback:
def _handle_llm_response(self, response: str, stream_id: str = None):
    if stream_id:
        for chunk in self.simulate_streaming(response):
            self.chat_display.update_message(stream_id, chunk)
    else:
        self.chat_display.add_message("claude", response)
```

## Solution 3: Enhanced BranchableMessage

Make sure your BranchableMessage is properly implemented:

```python
# src/presentation/tui/components/branchable_message.py
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

class BranchableMessage(Vertical):
    def __init__(self, sender: str, content: str, index: int, stream_id: str = None):
        super().__init__()
        self.sender = sender
        self.content = content
        self.index = index
        self.stream_id = stream_id
        self.add_class("message")
        
        # Set alignment based on sender
        if sender == "you":
            self.add_class("user-message")
        else:
            self.add_class("assistant-message")
    
    def compose(self):
        # Message bubble
        yield Static(self._create_message_bubble(), classes="message-bubble")
        
        # Action buttons (initially hidden)
        with Horizontal(classes="message-actions"):
            yield Button("🌿 Branch", id=f"branch-{self.index}")
            yield Button("📍 Bookmark", id=f"bookmark-{self.index}") 
            yield Button("⋯ More", id=f"more-{self.index}")
    
    def _create_message_bubble(self):
        """Create Rich renderable for message bubble"""
        # Use Text instead of str to preserve formatting
        text_content = Text(self.content)
        
        # Create panel with appropriate styling
        if self.sender == "you":
            bubble = Panel(
                text_content,
                title=f"👤 {self.sender}",
                title_align="right",
                style="blue",
                border_style="blue",
            )
            return Align.right(bubble)
        else:
            bubble = Panel(
                text_content, 
                title=f"🤖 {self.sender}",
                style="green",
                border_style="green",
            )
            return Align.left(bubble)
    
    def on_mount(self):
        # Hide buttons initially
        self.query_one(".message-actions").display = False
    
    def on_enter(self):
        # Show buttons on hover
        self.query_one(".message-actions").display = True
    
    def on_leave(self):
        # Hide buttons when not hovering
        self.query_one(".message-actions").display = False
    
    def append_content(self, chunk: str):
        """Append content for streaming updates"""
        self.content += chunk
        # Update the bubble with new content
        self.query_one(".message-bubble").update(self._create_message_bubble())
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button clicks"""
        button_id = event.button.id
        if button_id and button_id.startswith("branch-"):
            # Handle branch action
            self.app.notify(f"Branching message {self.index}")
        elif button_id and button_id.startswith("bookmark-"):
            # Handle bookmark action  
            self.app.notify(f"Bookmarking message {self.index}")
        elif button_id and button_id.startswith("more-"):
            # Handle more action
            self.app.notify(f"More actions for message {self.index}")
```

## CSS for Styling

```css
/* chat_display.css */
ChatDisplay {
    height: 1fr;
    overflow-y: auto;
    scrollbar-size: 1 1;
}

.message {
    margin: 1;
    width: 100%;
}

.message-bubble {
    width: auto;
    max-width: 80%;
}

.user-message {
    align: right;
}

.assistant-message {
    align: left;
}

.message-actions {
    height: auto;
    margin-top: 1;
    align: center;
}

.message-actions > Button {
    margin-right: 1;
}
```

## Why This Solution Works

1. **Proper Message Routing**: Messages are posted to the App, which bubbles them down to handlers
2. **Thread Safety**: `call_from_thread()` ensures UI operations happen on the correct thread
3. **Widget Management**: Using `VerticalScroll` with a container Static widget provides proper layout
4. **Streaming Support**: Message widgets can be incrementally updated
5. **Hover Events**: BranchableMessage is a real widget that receives mouse events

## Testing the Solution

Test with this sequence:

```python
# In your app testing
async def on_mount(self):
    # Test immediate display
    await self.chat_display.add_message("you", "Hello!")
    
    # Test streaming
    stream_id = "test-123"
    await self.chat_display.add_message("claude", "", stream_id)
    
    # Simulate streaming chunks
    for chunk in ["Hello", " there!", " How can I help?"]:
        await self.chat_display.update_message(stream_id, chunk)
        await asyncio.sleep(0.5)
```

This architecture should solve all your requirements: real-time streaming, hover interactions, thread safety, and proper chat history management.