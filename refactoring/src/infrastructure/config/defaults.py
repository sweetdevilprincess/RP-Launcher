"""
Default Configuration Schema for RP System

This module defines all default configuration values with comprehensive
documentation and type information. Configuration precedence:

1. Environment variables (highest priority)
2. config/config.json file
3. .env file
4. Defaults defined here (lowest priority)

Schema Version: 2.0.0
Last Updated: 2025-10-20
"""

import copy
from typing import Any, TypedDict

# =============================================================================
# System Defaults
# =============================================================================


class SystemConfig(TypedDict, total=False):
    """System-level configuration.

    Fields:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        auto_save: Automatically save state changes
        backup_frequency: Number of responses between automatic backups
        max_backups: Maximum number of backup files to keep
        performance_tracking: Enable performance profiling
        theme: TUI theme name (e.g., "textual-dark", "nord", "monokai")
    """

    log_level: str
    auto_save: bool
    backup_frequency: int
    max_backups: int
    performance_tracking: bool
    theme: str


SYSTEM_DEFAULTS: SystemConfig = {
    "log_level": "INFO",
    "auto_save": True,
    "backup_frequency": 10,
    "max_backups": 20,
    "performance_tracking": False,
    "theme": "textual-dark",
}


# =============================================================================
# LLM Routing Configuration
# =============================================================================


class LLMRoutingConfig(TypedDict, total=False):
    """LLM routing configuration for primary/secondary provider setup.

    Fields:
        primary_provider: Provider module for main conversation
                         (e.g., "claude_sdk_client", "openrouter_client", "openai_client")
        secondary_provider: Provider module for automation agents
                           (empty string = use primary for everything)
        use_secondary_for_automation: Route automation agents to secondary provider
    """

    primary_provider: str
    secondary_provider: str
    use_secondary_for_automation: bool


LLM_ROUTING_DEFAULTS: LLMRoutingConfig = {
    "primary_provider": "claude_sdk_client",
    "secondary_provider": "",  # Empty = use primary
    "use_secondary_for_automation": False,
}


# =============================================================================
# File Management Defaults
# =============================================================================


class FileManagerConfig(TypedDict, total=False):
    """File manager configuration.

    Fields:
        enabled: Enable file management module
        backup_on_write: Create backup before modifying files
        use_write_queue: Use async write queue for file operations
    """

    enabled: bool
    backup_on_write: bool
    use_write_queue: bool


FILE_MANAGER_DEFAULTS: FileManagerConfig = {
    "enabled": True,
    "backup_on_write": True,
    "use_write_queue": True,
}


# =============================================================================
# Session Management Defaults
# =============================================================================


class SessionManagerConfig(TypedDict, total=False):
    """Session management configuration.

    Fields:
        enabled: Enable session management
        auto_checkpoint_frequency: Responses between auto-checkpoints (0=disabled)
        keep_archived: Maximum archived sessions to retain
        compression: Enable compression for archived sessions
        auto_branch_on_restore: Create branch when restoring checkpoint
    """

    enabled: bool
    auto_checkpoint_frequency: int
    keep_archived: int
    compression: bool
    auto_branch_on_restore: bool


SESSION_MANAGER_DEFAULTS: SessionManagerConfig = {
    "enabled": True,
    "auto_checkpoint_frequency": 10,
    "keep_archived": 20,
    "compression": False,
    "auto_branch_on_restore": True,
}


# =============================================================================
# Agent System Defaults
# =============================================================================


class AgentCoordinatorConfig(TypedDict, total=False):
    """Agent coordination configuration.

    Fields:
        enabled: Enable agent system
        max_concurrent_agents: Max agents running concurrently
        timeout: Agent timeout in seconds
        cache_enabled: Cache agent results
        immediate_workers: Thread pool size for immediate agents
        background_workers: Thread pool size for background agents
        retry_enabled: Enable automatic retry on transient failures
        max_retries: Maximum retry attempts
    """

    enabled: bool
    max_concurrent_agents: int
    timeout: int
    cache_enabled: bool
    immediate_workers: int
    background_workers: int
    retry_enabled: bool
    max_retries: int


AGENT_COORDINATOR_DEFAULTS: AgentCoordinatorConfig = {
    "enabled": True,
    "max_concurrent_agents": 6,
    "timeout": 60,
    "cache_enabled": True,
    "immediate_workers": 4,
    "background_workers": 6,
    "retry_enabled": True,
    "max_retries": 2,
}


# =============================================================================
# Entity Management Defaults
# =============================================================================


class EntityManagerConfig(TypedDict, total=False):
    """Entity management configuration.

    Fields:
        enabled: Enable entity management
        auto_generate_threshold: Mentions before auto-generating preferences
        track_mentions: Track entity mentions in messages
        use_repository: Use repository pattern for entity storage
    """

    enabled: bool
    auto_generate_threshold: int
    track_mentions: bool
    use_repository: bool


ENTITY_MANAGER_DEFAULTS: EntityManagerConfig = {
    "enabled": True,
    "auto_generate_threshold": 3,
    "track_mentions": True,
    "use_repository": True,
}


# =============================================================================
# Automation Defaults
# =============================================================================


class AutomationOrchestratorConfig(TypedDict, total=False):
    """Automation orchestrator configuration.

    Fields:
        enabled: Enable automation system
        auto_start: Auto-start automation on launch
        use_triggers: Enable trigger evaluation
        use_templates: Enable template system
        fallback_enabled: Enable fallback trigger when no triggers match
    """

    enabled: bool
    auto_start: bool
    use_triggers: bool
    use_templates: bool
    fallback_enabled: bool


AUTOMATION_ORCHESTRATOR_DEFAULTS: AutomationOrchestratorConfig = {
    "enabled": True,
    "auto_start": False,
    "use_triggers": True,
    "use_templates": True,
    "fallback_enabled": True,
}


# =============================================================================
# Background Agent Defaults
# =============================================================================


class BackgroundAgentConfig(TypedDict, total=False):
    """Background agent configuration.

    Background agents run AFTER Claude responds to analyze and extract information.

    Fields:
        response_analyzer: Extract scene metadata (chapter, location, characters)
        time_tracking: Track in-world time passage and activity durations
        memory_creation: Extract memorable moments for each character
        relationship_analysis: Track relationship changes between characters
        knowledge_extraction: Extract world-building facts and lore
        plot_thread_detection: Identify and track narrative threads
        contradiction_synthesis: Detect inconsistencies and synthesize explanations (chapter-level)
    """

    response_analyzer: dict[str, bool]
    time_tracking: dict[str, bool]
    memory_creation: dict[str, bool]
    relationship_analysis: dict[str, bool]
    knowledge_extraction: dict[str, bool]
    plot_thread_detection: dict[str, bool]
    contradiction_synthesis: dict[str, bool]


BACKGROUND_AGENT_DEFAULTS: BackgroundAgentConfig = {
    "response_analyzer": {"enabled": True},
    "time_tracking": {"enabled": True},
    "memory_creation": {"enabled": True},
    "relationship_analysis": {"enabled": True},  # Track relationships on -100 to 100 scale
    "knowledge_extraction": {"enabled": True},  # Extract world-building facts with contradiction synthesis
    "plot_thread_detection": {"enabled": True},  # Tracks narrative plot threads with outcomes
    "contradiction_synthesis": {"enabled": False},  # Runs during chapter compression (disabled by default)
}


# =============================================================================
# Immediate Agent Defaults
# =============================================================================


class ImmediateAgentConfig(TypedDict, total=False):
    """Immediate agent configuration.

    Immediate agents run BEFORE Claude responds to gather context for prompt injection.

    Fields:
        memory_extraction: Find relevant memories for characters in scene
        fact_extraction: Extract relevant facts and knowledge
        plot_thread_extraction: Identify active plot threads
        quick_entity_analysis: Fast analysis of mentioned entities
    """

    memory_extraction: dict[str, bool | int]
    fact_extraction: dict[str, bool | int]
    plot_thread_extraction: dict[str, bool | int]
    quick_entity_analysis: dict[str, bool | int]


IMMEDIATE_AGENT_DEFAULTS: ImmediateAgentConfig = {
    "memory_extraction": {"enabled": True, "timeout_seconds": 5},  # Extract relevant memories for context
    "fact_extraction": {"enabled": True, "timeout_seconds": 5},  # Extract relevant entity facts (reduces context bloat)
    "plot_thread_extraction": {"enabled": True, "timeout_seconds": 5},  # Inject active plot threads
    "quick_entity_analysis": {"enabled": False, "timeout_seconds": 3},  # Not yet implemented
}


# =============================================================================
# LLM Client Defaults
# =============================================================================


class ClaudeSDKConfig(TypedDict, total=False):
    """Claude SDK client configuration (official Anthropic SDK).

    Fields:
        enabled: Enable Claude SDK client
        model: Default model to use
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        api_key: API key for authentication (saved by TUI)
    """

    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    api_key: str


CLAUDE_SDK_DEFAULTS: ClaudeSDKConfig = {
    "enabled": False,
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 1.0,
    "max_tokens": 8192,
    "api_key": "",
}


class ClaudeAPIConfig(TypedDict, total=False):
    """Claude API client configuration.

    Fields:
        enabled: Enable Claude API client
        model: Default model to use
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        use_prompt_caching: Enable prompt caching
        thinking_budget_tokens: Tokens allocated for extended thinking
        api_key: API key for authentication (saved by TUI)
    """

    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    use_prompt_caching: bool
    thinking_budget_tokens: int
    api_key: str


CLAUDE_API_DEFAULTS: ClaudeAPIConfig = {
    "enabled": False,
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 1.0,
    "max_tokens": 8192,
    "use_prompt_caching": True,
    "thinking_budget_tokens": 5000,
    "api_key": "",
}


class OpenAIConfig(TypedDict, total=False):
    """OpenAI API client configuration.

    Fields:
        enabled: Enable OpenAI client
        model: Default model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        endpoint: Which endpoint to use (responses or chat_completions)
        api_key: API key for authentication (saved by TUI)
    """

    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    endpoint: str
    api_key: str


OPENAI_DEFAULTS: OpenAIConfig = {
    "enabled": False,
    "model": "gpt-4.1",
    "temperature": 1.0,
    "max_tokens": 4000,
    "endpoint": "responses",
    "api_key": "",
}


class OpenRouterConfig(TypedDict, total=False):
    """OpenRouter client configuration.

    Fields:
        enabled: Enable OpenRouter client
        model: Default model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        site_url: Optional site URL for OpenRouter
        app_name: Optional app name for OpenRouter
        api_key: API key for authentication (saved by TUI)
    """

    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    site_url: str
    app_name: str
    api_key: str


OPENROUTER_DEFAULTS: OpenRouterConfig = {
    "enabled": True,
    "model": "anthropic/claude-3-5-sonnet",
    "temperature": 1.0,
    "max_tokens": 8192,
    "site_url": "",
    "app_name": "RP Launcher",
    "api_key": "",
}


# =============================================================================
# Proxy Configuration Defaults
# =============================================================================


class ProxyClientConfig(TypedDict, total=False):
    """Proxy client configuration.

    Fields:
        enabled: Enable proxy usage
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts
        use_proxy: Whether to route through proxy
        proxy_url: Proxy server URL (saved by TUI)
        proxy_username: Proxy authentication username (saved by TUI)
        proxy_password: Proxy authentication password (saved by TUI)
    """

    enabled: bool
    timeout: int
    retry_attempts: int
    use_proxy: bool
    proxy_url: str
    proxy_username: str
    proxy_password: str


PROXY_CLIENT_DEFAULTS: ProxyClientConfig = {
    "enabled": True,
    "timeout": 30,
    "retry_attempts": 3,
    "use_proxy": False,
    "proxy_url": "",
    "proxy_username": "",
    "proxy_password": "",
}


# =============================================================================
# Write Queue Defaults
# =============================================================================


class FSWriteQueueConfig(TypedDict, total=False):
    """File system write queue configuration.

    Fields:
        enabled: Enable write queue
        flush_interval: Seconds between queue flushes
        max_queue_size: Maximum queued operations before force flush
    """

    enabled: bool
    flush_interval: int
    max_queue_size: int


FS_WRITE_QUEUE_DEFAULTS: FSWriteQueueConfig = {
    "enabled": True,
    "flush_interval": 5,
    "max_queue_size": 100,
}


# =============================================================================
# Background Task Queue Defaults
# =============================================================================


class BackgroundTaskQueueConfig(TypedDict, total=False):
    """Background task queue configuration.

    Fields:
        enabled: Enable background task queue
        max_workers: Maximum worker threads
        shutdown_timeout: Timeout for graceful shutdown (seconds)
    """

    enabled: bool
    max_workers: int
    shutdown_timeout: int


BACKGROUND_TASK_QUEUE_DEFAULTS: BackgroundTaskQueueConfig = {
    "enabled": True,
    "max_workers": 4,
    "shutdown_timeout": 30,
}


# =============================================================================
# Update Checker Defaults
# =============================================================================


class UpdateCheckerConfig(TypedDict, total=False):
    """Update checker configuration.

    Fields:
        enabled: Enable update checking
        check_interval: Seconds between update checks
        auto_check: Automatically check on startup
    """

    enabled: bool
    check_interval: int
    auto_check: bool


UPDATE_CHECKER_DEFAULTS: UpdateCheckerConfig = {
    "enabled": False,
    "check_interval": 86400,  # 24 hours
    "auto_check": False,
}


# =============================================================================
# Full Default Configuration
# =============================================================================


def get_default_config() -> dict[str, Any]:
    """Get complete default configuration with all modules.

    Returns a deep copy of the default configuration to prevent accidental
    mutation of the global default constants.

    Returns:
        Complete default configuration dictionary (deep copy)
    """
    config = {
        "version": "2.0.0",
        "system": SYSTEM_DEFAULTS,
        "llm": LLM_ROUTING_DEFAULTS,
        "modules": {
            "file_manager": {
                "enabled": FILE_MANAGER_DEFAULTS["enabled"],
                "config": FILE_MANAGER_DEFAULTS,
            },
            "session_manager": {
                "enabled": SESSION_MANAGER_DEFAULTS["enabled"],
                "config": SESSION_MANAGER_DEFAULTS,
            },
            "fs_write_queue": {
                "enabled": FS_WRITE_QUEUE_DEFAULTS["enabled"],
                "config": FS_WRITE_QUEUE_DEFAULTS,
            },
            "background_task_queue": {
                "enabled": BACKGROUND_TASK_QUEUE_DEFAULTS["enabled"],
                "config": BACKGROUND_TASK_QUEUE_DEFAULTS,
            },
            "agent_coordinator": {
                "enabled": AGENT_COORDINATOR_DEFAULTS["enabled"],
                "config": AGENT_COORDINATOR_DEFAULTS,
            },
            "entity_manager": {
                "enabled": ENTITY_MANAGER_DEFAULTS["enabled"],
                "config": ENTITY_MANAGER_DEFAULTS,
            },
            "automation_orchestrator": {
                "enabled": AUTOMATION_ORCHESTRATOR_DEFAULTS["enabled"],
                "config": AUTOMATION_ORCHESTRATOR_DEFAULTS,
            },
            "update_checker": {
                "enabled": UPDATE_CHECKER_DEFAULTS["enabled"],
                "config": UPDATE_CHECKER_DEFAULTS,
            },
            "proxy_client": {
                "enabled": PROXY_CLIENT_DEFAULTS["enabled"],
                "config": PROXY_CLIENT_DEFAULTS,
            },
            "claude_sdk_client": {
                "enabled": CLAUDE_SDK_DEFAULTS["enabled"],
                "config": CLAUDE_SDK_DEFAULTS,
            },
            "claude_api_client": {
                "enabled": CLAUDE_API_DEFAULTS["enabled"],
                "config": CLAUDE_API_DEFAULTS,
            },
            "openai_client": {
                "enabled": OPENAI_DEFAULTS["enabled"],
                "config": OPENAI_DEFAULTS,
            },
            "openrouter_client": {
                "enabled": OPENROUTER_DEFAULTS["enabled"],
                "config": OPENROUTER_DEFAULTS,
            },
        },
        "agents": {
            "background": BACKGROUND_AGENT_DEFAULTS,
            "immediate": IMMEDIATE_AGENT_DEFAULTS,
        },
    }
    # Return deep copy to prevent mutation of global defaults
    return copy.deepcopy(config)


# =============================================================================
# Schema Information
# =============================================================================


def get_schema_info() -> dict[str, str]:
    """Get schema information for documentation.

    Returns:
        Dictionary with schema metadata
    """
    return {
        "version": "2.0.0",
        "last_updated": "2025-10-20",
        "description": "RP Launcher configuration schema",
        "precedence": "ENV > config.json > .env > defaults",
    }


__all__ = [
    "AGENT_COORDINATOR_DEFAULTS",
    "AUTOMATION_ORCHESTRATOR_DEFAULTS",
    "BACKGROUND_AGENT_DEFAULTS",
    "BACKGROUND_TASK_QUEUE_DEFAULTS",
    "CLAUDE_API_DEFAULTS",
    "CLAUDE_SDK_DEFAULTS",
    "ENTITY_MANAGER_DEFAULTS",
    "FILE_MANAGER_DEFAULTS",
    "FS_WRITE_QUEUE_DEFAULTS",
    "IMMEDIATE_AGENT_DEFAULTS",
    "LLM_ROUTING_DEFAULTS",
    "LLMRoutingConfig",
    "OPENAI_DEFAULTS",
    "OPENROUTER_DEFAULTS",
    "PROXY_CLIENT_DEFAULTS",
    "SESSION_MANAGER_DEFAULTS",
    "SYSTEM_DEFAULTS",
    "UPDATE_CHECKER_DEFAULTS",
    "get_default_config",
    "get_schema_info",
]
