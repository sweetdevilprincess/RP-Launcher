"""Client modules for external services (Claude Code, DeepSeek API)."""

# Legacy CLI client
from . import claude

# API clients
from . import claude_api
from . import deepseek

# NEW: High-performance SDK client
from . import claude_sdk
