"""Claude API client with prompt caching support.

This client uses the Anthropic API directly to enable explicit control over
prompt caching. This is more efficient than the CLI for RP use cases where
TIER_1 files are loaded with every message.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import anthropic


class ClaudeAPIClient:
    """Claude API client with intelligent prompt caching."""

    # Thinking mode presets (matching Claude Code CLI)
    THINKING_MODES = {
        "disabled": 0,           # No extended thinking
        "think": 4000,           # Quick reasoning
        "megathink": 10000,      # Standard reasoning
        "ultrathink": 31999,     # Maximum reasoning
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude API client.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 with extended thinking support

    def send_message(
        self,
        user_message: str,
        cached_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        thinking_mode: str = "megathink",
        thinking_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send a message to Claude with prompt caching and extended thinking.

        Args:
            user_message: The user's message/prompt
            cached_context: Large static context to cache (TIER_1 files, etc.)
                          This will be cached and reused across requests
            conversation_history: Previous messages in format [{"role": "user"|"assistant", "content": "..."}]
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            thinking_mode: Thinking mode preset ("disabled", "think", "megathink", "ultrathink")
            thinking_budget: Custom thinking token budget (overrides thinking_mode if provided)

        Returns:
            Dict with:
                - content: The response text
                - thinking: The thinking process (if available)
                - usage: Token usage stats including cache hits
                - raw_response: Full API response object
        """
        # Build system prompt with caching
        system_messages = []

        if cached_context:
            # Cache the static context (TIER_1 files, automation instructions)
            system_messages.append({
                "type": "text",
                "text": cached_context,
                "cache_control": {"type": "ephemeral"}  # Cache for 5 minutes
            })

        # Build conversation messages
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Determine thinking budget
        if thinking_budget is not None:
            # Custom budget provided
            final_budget = thinking_budget
        elif thinking_mode in self.THINKING_MODES:
            # Use preset
            final_budget = self.THINKING_MODES[thinking_mode]
        else:
            # Unknown mode, default to megathink
            final_budget = self.THINKING_MODES["megathink"]

        # Build API call parameters
        api_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_messages if system_messages else None,
            "messages": messages
        }

        # Add thinking config only if budget > 0
        if final_budget > 0:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": final_budget
            }

        # Make API call
        response = self.client.messages.create(**api_params)

        # Extract response details
        # Handle multiple content blocks (thinking + text)
        text_content = ""
        thinking_content = ""

        for block in response.content:
            if block.type == "thinking":
                thinking_content = block.thinking
            elif block.type == "text":
                text_content = block.text

        result = {
            "content": text_content,
            "thinking": thinking_content,  # Include thinking for debugging if needed
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            },
            "raw_response": response
        }

        return result

    def format_cache_stats(self, usage: Dict[str, int]) -> str:
        """Format cache usage statistics for display.

        Args:
            usage: Usage dict from send_message response

        Returns:
            Formatted string with cache statistics
        """
        cache_created = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        lines = [
            f"📊 Token Usage:",
            f"  Input: {input_tokens:,}",
            f"  Output: {output_tokens:,}",
        ]

        if cache_created > 0:
            lines.append(f"  💾 Cache Created: {cache_created:,} tokens (1.25x cost)")

        if cache_read > 0:
            savings_percent = (cache_read / (cache_read + input_tokens)) * 100
            lines.append(f"  ⚡ Cache Hit: {cache_read:,} tokens (0.1x cost) - {savings_percent:.1f}% of input cached!")

        return "\n".join(lines)


class ConversationManager:
    """Manages conversation state and history for Claude API."""

    def __init__(self, state_dir: Path):
        """Initialize conversation manager.

        Args:
            state_dir: Directory to store conversation state
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.state_dir / "conversation_history.json"
        self.history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self):
        """Load conversation history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load conversation history: {e}")
                self.history = []

    def _save_history(self):
        """Save conversation history to disk."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save conversation history: {e}")

    def add_user_message(self, content: str):
        """Add a user message to history."""
        self.history.append({
            "role": "user",
            "content": content
        })
        self._save_history()

    def add_assistant_message(self, content: str):
        """Add an assistant message to history."""
        self.history.append({
            "role": "assistant",
            "content": content
        })
        self._save_history()

    def clear_history(self):
        """Clear conversation history."""
        self.history = []
        if self.history_file.exists():
            self.history_file.unlink()

    def get_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history."""
        return self.history.copy()


def load_api_key() -> Optional[str]:
    """Load API key from config file or environment.

    Checks in order:
    1. ANTHROPIC_API_KEY environment variable
    2. Global config.json in RP Claude Code directory
    3. .env file in RP Claude Code directory

    Returns:
        API key or None if not found
    """
    # Check environment variable first
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # Check global config.json (created by TUI settings)
    base_dir = Path(__file__).parent.parent.parent
    config_file = base_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("anthropic_api_key")
                if api_key:
                    return api_key
        except Exception as e:
            print(f"⚠️  Failed to read config.json: {e}")

    # Check .env file
    env_file = base_dir / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ANTHROPIC_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except Exception as e:
            print(f"⚠️  Failed to read .env file: {e}")

    return None
