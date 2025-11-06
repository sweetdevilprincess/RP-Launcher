"""Multi-provider LLM client implementations."""

from .base import (
    ConversationHistory,
    ConversationMessage,
    LLMAuthError,
    LLMClient,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
    MessageRole,
    ProviderCapabilities,
    StreamingLLMClient,
    UsageStats,
)
from .claude_api_client import (
    ClaudeAPIClient,
    ClaudeAPISettings,
    load_claude_settings,
)
from .claude_sdk_client import ClaudeSDKStreamingClient
from .config_utils import (
    merge_config_sources,
    pick_first,
    read_env_file,
    read_json_file,
    resolve_project_root,
)
from .openai_client import (
    OpenAIChatClient,
    OpenAISettings,
    load_openai_settings,
)
from .openrouter_client import (
    OpenRouterClient,
    OpenRouterSettings,
    load_openrouter_settings,
)
from .proxy import ProxySettings, load_proxy_settings
from .registry import (
    ProviderSpec,
    get_provider,
    list_providers,
    register_provider,
)
from .semantic_ai_client import SemanticAiClient
from .mock_client import MockLLMClient
from .llm_router import (
    call_primary_llm,
    call_secondary_llm,
)
