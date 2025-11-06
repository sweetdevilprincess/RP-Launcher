"""Claude API client with prompt caching support.

This client uses the Anthropic API directly to enable explicit control over
prompt caching. This is more efficient than the CLI for RP use cases where
TIER_1 files are loaded with every message.
"""

import os
import json
from urllib.parse import urlparse, urlunparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import anthropic

from .proxy_client import load_proxy_config


class ClaudeAPIClient:
    """Claude API client with intelligent prompt caching."""

    # Thinking mode presets (matching Claude Code CLI)
    THINKING_MODES = {
        "disabled": 0,           # No extended thinking
        "think": 5000,           # Quick planning, simple refactoring
        "think hard": 10000,     # Feature design, debugging
        "megathink": 10000,      # Standard reasoning (same as think hard)
        "think harder": 25000,   # Architecture decisions, complex bugs
        "ultrathink": 31999,     # Maximum reasoning - system design
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None
    ):
        """Initialize the Claude API client.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var
            base_url: Optional override for Anthropic base URL (proxy support)
            auth_token: Optional bearer token for Authorization header (proxy support)
        """
        resolved_api_key = (api_key or os.environ.get("ANTHROPIC_API_KEY") or "").strip() or None
        resolved_auth_token = (auth_token
                               or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                               or os.environ.get("ANTHROPIC_PROXY_TOKEN")
                               or "").strip() or None

        resolved_base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("ANTHROPIC_PROXY_URL")
        if resolved_base_url:
            resolved_base_url = self._normalize_base_url(resolved_base_url)

        if not resolved_api_key and not resolved_auth_token:
            raise ValueError(
                "Anthropic API credentials required. Provide an API key or auth token "
                "via environment variables, config, or constructor parameters."
            )

        client_kwargs: Dict[str, Any] = {}
        if resolved_api_key:
            client_kwargs["api_key"] = resolved_api_key
        if resolved_auth_token:
            client_kwargs["auth_token"] = resolved_auth_token
        if resolved_base_url:
            client_kwargs["base_url"] = resolved_base_url

        self.api_key = resolved_api_key
        self.auth_token = resolved_auth_token
        self.base_url = resolved_base_url
        self.client = anthropic.Anthropic(**client_kwargs)
        self.model = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 with extended thinking support

    @staticmethod
    def _normalize_base_url(url: str) -> str:
        """Normalize base URL and strip trailing /v1 segment if present."""
        cleaned = url.strip()
        if not cleaned:
            return cleaned

        parsed = urlparse(cleaned)
        path = parsed.path.rstrip("/")
        segments = [segment for segment in path.split("/") if segment]
        if segments == ["v1"]:
            path = ""

        normalized = urlunparse(parsed._replace(path=path))
        return normalized.rstrip("/")

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
            thinking_mode: Thinking mode preset ("disabled", "think", "think hard", "megathink", "think harder", "ultrathink")
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


def load_api_settings(config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Optional[str]]:
    """Load Anthropic API credentials and proxy settings from env/config.

    Args:
        config_override: Optional config dictionary (e.g. merged global/local config)

    Returns:
        Dict with keys: api_key, auth_token, base_url, proxy_url, proxy_token
    """
    base_dir = Path(__file__).parent.parent.parent
    config_data: Dict[str, Any] = {}

    if config_override is not None:
        config_data.update(config_override)
    else:
        config_file = base_dir / "config" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data.update(json.load(f))
            except Exception as e:
                print(f"⚠️  Failed to read config/config.json: {e}")

    env_file_vars: Dict[str, str] = {}
    env_file = base_dir / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    env_file_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Failed to read .env file: {e}")

    def pick(*values: Optional[str]) -> Optional[str]:
        for value in values:
            if value:
                cleaned = value.strip()
                if cleaned:
                    return cleaned
        return None

    # Load proxy configuration using shared loader
    proxy_config = load_proxy_config()
    proxy_url = proxy_config["proxy_url"]
    proxy_token = proxy_config["proxy_token"]
    use_proxy = proxy_config["use_proxy"]

    # Normalize proxy URL if present
    if proxy_url:
        proxy_url = ClaudeAPIClient._normalize_base_url(proxy_url)

    # Load Claude API key
    legacy_proxy_url: Optional[str] = None

    api_key = pick(
        os.environ.get("ANTHROPIC_API_KEY"),
        config_data.get("anthropic_api_key"),
        env_file_vars.get("ANTHROPIC_API_KEY"),
    )

    if api_key and api_key.lower().startswith(("http://", "https://")):
        # Legacy configs sometimes stored proxy URL in the API key slot
        legacy_proxy_url = ClaudeAPIClient._normalize_base_url(api_key)
        api_key = None

    # Use legacy proxy URL if no proxy configured
    if not proxy_url and legacy_proxy_url:
        proxy_url = legacy_proxy_url

    # If proxy is enabled, use proxy_url as base_url and proxy_token as auth_token
    if use_proxy and proxy_url:
        base_url = proxy_url
        auth_token = proxy_token
    else:
        # Normal flow - check for explicit base_url and auth_token
        base_url = pick(
            os.environ.get("ANTHROPIC_BASE_URL"),
            config_data.get("anthropic_base_url"),
            env_file_vars.get("ANTHROPIC_BASE_URL"),
        )

        auth_token = pick(
            os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            env_file_vars.get("ANTHROPIC_AUTH_TOKEN"),
        )

    if base_url:
        base_url = ClaudeAPIClient._normalize_base_url(base_url)

    return {
        "api_key": api_key,
        "auth_token": auth_token,
        "base_url": base_url,
        "proxy_url": proxy_url,
        "proxy_token": proxy_token,
    }


def load_api_key(config_override: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Load API key from config file or environment.

    Checks in order:
    1. ANTHROPIC_API_KEY environment variable
    2. Global config.json in RP Claude Code directory
    3. .env file in RP Claude Code directory

    Returns:
        API key or None if not found
    """
    settings = load_api_settings(config_override)
    return settings.get("api_key")
