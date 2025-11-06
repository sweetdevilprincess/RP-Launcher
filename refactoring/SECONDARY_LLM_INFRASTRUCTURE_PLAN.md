# Secondary LLM Infrastructure - Complete Implementation Plan

**Date:** 2025-10-24
**Status:** Ready for Implementation
**Complexity:** Medium (reuse existing patterns)

---

## TL;DR

**Good News:** You already have 95% of the LLM infrastructure built! You just need to:
1. Add secondary LLM config to defaults.py
2. Initialize a second LLM client instance (reuse existing registry)
3. Pass it to AgentFactory via dependency injection
4. Implement the 10 agents that use it

**Estimated Time:** 4-6 hours (down from 40-54 hours!)

---

## What You Already Have ✅

### 1. Complete LLM Client Architecture

**File:** `src/infrastructure/llm/base.py`

```python
class LLMClient(Protocol):
    """Common client interface for ALL LLM providers."""

    provider_id: str

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 8192,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse: ...

    def capabilities(self) -> ProviderCapabilities: ...
```

**What this means:**
- Protocol-based interface (any provider works)
- Standard `send_message()` method
- Uniform response format (`LLMResponse` with usage stats)
- Common exception handling (LLMError, LLMAuthError, LLMRateLimitError)

---

### 2. Multiple Provider Implementations

**Files:** `src/infrastructure/llm/*.py`

Available providers:
- ✅ **ClaudeAPIClient** - Anthropic API with prompt caching
- ✅ **ClaudeSDKStreamingClient** - Claude SDK (streaming)
- ✅ **OpenAIChatClient** - OpenAI GPT-4o/GPT-4.1
- ✅ **OpenRouterClient** - DeepSeek, Mistral, etc. (multi-model gateway)
- ✅ **MockLLMClient** - Testing without API calls

**All implement the same `LLMClient` protocol** - completely interchangeable!

---

### 3. Provider Registry System

**File:** `src/infrastructure/llm/registry.py`

```python
# Provider registration (already done for all providers)
register_provider(
    ProviderSpec(
        provider_id="openrouter_client",
        label="OpenRouter API",
        supports_streaming=False,
        factory=_openrouter_factory,  # ← Factory creates client
        description="OpenRouter multi-model gateway (DeepSeek, Mistral, etc.)",
    )
)

# Get provider and create client (one-liner!)
provider_spec = get_provider("openrouter_client")
llm_client = provider_spec.factory(config)  # ← Returns LLMClient
```

**What this means:**
- Registry already has all providers registered
- Factory functions already create clients from config
- Just call `get_provider()` + `factory()` = instant LLM client!

---

### 4. Configuration System

**Files:** `src/infrastructure/config/defaults.py`, `config_loader.py`

**Already has TypedDict schemas for all LLM providers:**

```python
# defaults.py lines 297-324
class OpenRouterConfig(TypedDict, total=False):
    enabled: bool
    model: str
    temperature: float
    max_tokens: int
    site_url: str
    app_name: str

OPENROUTER_DEFAULTS: OpenRouterConfig = {
    "enabled": True,
    "model": "anthropic/claude-3-5-sonnet",
    "temperature": 0.7,
    "max_tokens": 8192,
    "site_url": "",
    "app_name": "RP Launcher",
}

# Automatically added to config structure (lines 500-503)
"openrouter_client": {
    "enabled": OPENROUTER_DEFAULTS["enabled"],
    "config": OPENROUTER_DEFAULTS,
}
```

**Configuration loading is layered** (line 140-207):
1. Defaults from `defaults.py`
2. `.env` file
3. `config.json`
4. Environment variables (highest priority)

**API keys already mapped** (line 84-87):
```python
ENV_VAR_MAPPING = {
    "ANTHROPIC_API_KEY": "modules.claude_api_client.config.api_key",
    "OPENAI_API_KEY": "modules.openai_client.config.api_key",
    "OPENROUTER_API_KEY": "modules.openrouter_client.config.api_key",
}
```

---

### 5. Existing LLM Client Initialization Pattern

**File:** `src/presentation/bridge/bridge_service.py` (lines 130-174)

```python
def _initialize_llm_client(self, provider_name: Optional[str] = None) -> None:
    """Initialize LLM client - PRIMARY conversation LLM."""

    # Get provider from config
    if not provider_name:
        config = self.config_loader.load()
        modules = config.get("modules", {})
        llm_providers = [
            "claude_api_client", "claude_sdk_client",
            "openai_client", "openrouter_client"
        ]
        for module_name, module_config in modules.items():
            if module_config.get("enabled") and module_name in llm_providers:
                provider_name = module_name
                break

    # Get provider from registry
    provider_spec = get_provider(provider_name)

    # Create client using factory
    config = self.config_loader.load()
    self.llm_client = provider_spec.factory(config)  # ← MAGIC LINE!
    self.current_provider = provider_name
```

**This pattern already works!** We just need to duplicate it for secondary LLM.

---

### 6. Settings UI Already Exists

**File:** `src/presentation/tui/components/llm_settings_page.py` (lines 193-208)

```python
# Secondary LLM Section (already in UI!)
yield Static("Secondary LLM (Optional)", classes="section-title")
yield Static("Used for automation purposes (task management, summaries, etc.)",
             classes="section-description")

yield Label("API Key:")
yield Input(
    placeholder="Enter secondary API key",
    id="secondary-api-key",
    password=True
)

yield Label("Model Name:")
yield Input(
    placeholder="e.g., gpt-4, claude-3-opus",
    id="secondary-model"
)
```

**UI exists but not wired to backend yet!**

---

## What You Need to Add ❌

### 1. Secondary LLM Configuration Schema

**File:** `src/infrastructure/config/defaults.py`

**Add after line 324:**

```python
# =============================================================================
# Agent LLM Defaults (Secondary LLM for Automation)
# =============================================================================


class AgentLLMConfig(TypedDict, total=False):
    """Agent LLM configuration (secondary LLM for automation tasks).

    This is a separate LLM instance from the primary conversation LLM,
    typically using a cheaper model (DeepSeek, GPT-3.5) for background
    analysis tasks like memory creation, relationship analysis, etc.

    Fields:
        enabled: Enable agent LLM (if false, agents won't run)
        provider: Which provider to use ("openrouter_client", "openai_client", etc.)
        model: Model name (e.g., "deepseek/deepseek-chat-v3")
        temperature: Sampling temperature (0.0 = deterministic for analysis)
        max_tokens: Maximum tokens in response (agents need less than conversation)
        timeout: Request timeout in seconds
    """

    enabled: bool
    provider: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int


AGENT_LLM_DEFAULTS: AgentLLMConfig = {
    "enabled": True,
    "provider": "openrouter_client",  # Use OpenRouter for cheap DeepSeek access
    "model": "deepseek/deepseek-chat-v3",  # ~$0.0001 per call
    "temperature": 0.0,  # Deterministic for analysis
    "max_tokens": 2048,  # Agents need less tokens than conversation
    "timeout": 30,
}
```

**Add to module list in `get_default_config()` (after line 502):**

```python
"agent_llm": {
    "enabled": AGENT_LLM_DEFAULTS["enabled"],
    "config": AGENT_LLM_DEFAULTS,
},
```

**Add to exports (line 529):**

```python
__all__ = [
    "AGENT_COORDINATOR_DEFAULTS",
    "AGENT_LLM_DEFAULTS",  # ← ADD THIS
    # ... rest
]
```

---

### 2. Agent LLM Client Initialization

**File:** `src/presentation/bridge/bridge_service.py`

**Add method after `_initialize_llm_client()` (after line 174):**

```python
def _initialize_agent_llm_client(self) -> LLMClient | None:
    """Initialize secondary LLM client for agent automation.

    This creates a separate LLM client instance for agents to use,
    typically with a cheaper model (DeepSeek) than the primary
    conversation LLM (Claude).

    Returns:
        Initialized LLM client, or None if agent LLM disabled
    """
    if self.testing_mode:
        # Use mock client in testing mode
        from refactoring.src.infrastructure.llm.mock_client import MockLLMClient
        print("[TEST] Testing mode: Using mock agent LLM client")
        return MockLLMClient()

    # Get agent LLM config
    config = self.config_loader.load()
    agent_llm_config = config.get("modules", {}).get("agent_llm", {})

    # Check if agent LLM is enabled
    if not agent_llm_config.get("enabled", True):
        print("[INFO] Agent LLM disabled - agents will not run")
        return None

    # Get provider name from agent LLM config
    agent_config_inner = agent_llm_config.get("config", {})
    provider_name = agent_config_inner.get("provider", "openrouter_client")

    # Get provider from registry
    provider_spec = get_provider(provider_name)
    if not provider_spec:
        print(f"[WARNING] Agent LLM provider not found: {provider_name}")
        return None

    # Create override config with agent-specific settings
    agent_override_config = config.copy()

    # Override the provider's config with agent LLM settings
    if provider_name in agent_override_config.get("modules", {}):
        provider_module = agent_override_config["modules"][provider_name]
        if "config" in provider_module:
            # Merge agent LLM settings into provider config
            provider_module["config"]["model"] = agent_config_inner.get("model")
            provider_module["config"]["temperature"] = agent_config_inner.get("temperature", 0.0)
            provider_module["config"]["max_tokens"] = agent_config_inner.get("max_tokens", 2048)

    try:
        # Create client using factory
        agent_llm_client = provider_spec.factory(agent_override_config)
        print(f"[OK] Agent LLM client initialized: {provider_name} ({agent_config_inner.get('model')})")
        return agent_llm_client

    except Exception as e:
        print(f"[WARNING] Failed to initialize agent LLM client: {e}")
        print("[INFO] Agents will not run without secondary LLM")
        return None
```

**Update `_initialize_services()` to call it (line 107-128):**

```python
def _initialize_services(self) -> None:
    """Initialize refactored automation services."""
    print("[INIT] Initializing services...")

    # Automation service (using factory)
    self.automation_service = create_automation_service(self.rp_dir)
    print("[OK] Automation service initialized")

    # Entity service
    self.entity_service = EntityService()
    print("[OK] Entity service initialized")

    # Session state service
    self.session_state_service = SessionStateService(logger=self.logger)
    print("[OK] Session state service initialized")

    # PRIMARY LLM client (main conversation)
    try:
        self._initialize_llm_client()
    except Exception as e:
        print(f"[WARNING] LLM client initialization skipped: {e}")
        print("[INFO] You can enable Testing Mode via F2 settings to test without API keys")

    # SECONDARY LLM client (agent automation) ← ADD THIS
    try:
        self.agent_llm_client = self._initialize_agent_llm_client()
    except Exception as e:
        print(f"[WARNING] Agent LLM client initialization skipped: {e}")
        print("[INFO] Agents will not run without secondary LLM configured")
```

**Add instance variable (line 63):**

```python
self.automation_service: Optional[AutomationService] = None
self.llm_client: Optional[LLMClient] = None
self.agent_llm_client: Optional[LLMClient] = None  # ← ADD THIS
self.entity_service: Optional[EntityService] = None
```

---

### 3. Update AgentFactory to Accept LLM Client

**File:** `src/automation/services/agent_factory.py`

**Update constructor (lines 53-72):**

```python
def __init__(
    self,
    *,
    catalog: AgentCatalog,
    rp_dir: Path,
    log_file: Path,
    agent_llm_client: LLMClient | None = None,  # ← ADD THIS
    entity_repo: FixtureEntityRepository | None = None,  # ← ADD THIS
    logger: LoggingService | None = None,
) -> None:
    """Initialize agent factory.

    Args:
        catalog: Agent registry for metadata lookup
        rp_dir: RP directory path (passed to agent constructors)
        log_file: Log file path (passed to agent constructors)
        agent_llm_client: Optional LLM client for agent analysis (secondary LLM)
        entity_repo: Optional entity repository for memory/entity access
        logger: Optional logging service for factory events
    """
    self.catalog = catalog
    self.rp_dir = rp_dir
    self.log_file = log_file
    self.agent_llm_client = agent_llm_client  # ← ADD THIS
    self.entity_repo = entity_repo  # ← ADD THIS
    self.logger = logger
```

**Update agent instantiation (line 103):**

```python
# OLD:
agent = agent_class(self.rp_dir, self.log_file)

# NEW:
agent = agent_class(
    rp_dir=self.rp_dir,
    log_file=self.log_file,
    llm_client=self.agent_llm_client,  # ← ADD THIS
    entity_repo=self.entity_repo,  # ← ADD THIS
)
```

**Add import at top:**

```python
from ...domain.entities.entity_repository import FixtureEntityRepository
from ...infrastructure.llm.base import LLMClient
```

---

### 4. Update AgentCoordinator to Pass Dependencies

**File:** `src/automation/services/agent_coordinator.py`

**Update factory creation** (find where AgentFactory is instantiated):

```python
# OLD (current):
factory = AgentFactory(
    catalog=catalog,
    rp_dir=self.rp_dir,
    log_file=self.log_file,
    logger=self.logger,
)

# NEW:
factory = AgentFactory(
    catalog=catalog,
    rp_dir=self.rp_dir,
    log_file=self.log_file,
    agent_llm_client=self.agent_llm_client,  # ← ADD THIS
    entity_repo=self.entity_repo,  # ← ADD THIS
    logger=self.logger,
)
```

**Add constructor parameters:**

```python
def __init__(
    self,
    rp_dir: Path,
    log_file: Path,
    *,
    agent_llm_client: LLMClient | None = None,  # ← ADD THIS
    entity_repo: FixtureEntityRepository | None = None,  # ← ADD THIS
    logger: LoggingService | None = None,
):
    self.rp_dir = rp_dir
    self.log_file = log_file
    self.agent_llm_client = agent_llm_client  # ← ADD THIS
    self.entity_repo = entity_repo  # ← ADD THIS
    self.logger = logger
```

---

### 5. Wire Settings UI to Backend

**File:** `src/presentation/tui/components/llm_settings_page.py`

**Update field mapping** (lines 316-324):

```python
field_map = {
    "primary-api-key": "primary_api_key",
    "secondary-api-key": "agent_llm_api_key",  # ← FIX THIS
    "secondary-model": "agent_llm_model",  # ← FIX THIS
    "temperature": "temperature",
    "max-tokens": "max_tokens",
    "system-prompt": "system_prompt",
    "context-window": "context_window",
}
```

**Update save_all_settings** (lines 355-383):

```python
self.settings = {
    "provider": provider,
    "primary_api_key": primary_key.value,

    # Agent LLM settings ← ADD THIS SECTION
    "agent_llm_enabled": True,  # TODO: Add checkbox to UI
    "agent_llm_provider": "openrouter_client",  # TODO: Add dropdown to UI
    "agent_llm_api_key": secondary_key.value,
    "agent_llm_model": secondary_model.value,
    "agent_llm_temperature": "0.0",  # Deterministic for agents

    "temperature": temperature.value,
    "max_tokens": max_tokens.value,
    "system_prompt": system_prompt.value,
    "context_window": context_window.value,
    "response_format": str(response_format.value),
}
```

---

## Agent Implementation Pattern

Once infrastructure is ready, each agent follows this pattern:

```python
from src.infrastructure.llm.base import LLMClient, LLMError
from src.domain.entities.entity_repository import FixtureEntityRepository
from pathlib import Path

class MemoryCreationAgent:
    """Analyzes responses and creates memory entries."""

    def __init__(
        self,
        rp_dir: Path,
        log_file: Path,
        llm_client: LLMClient | None = None,
        entity_repo: FixtureEntityRepository | None = None,
    ):
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.llm_client = llm_client
        self.entity_repo = entity_repo

    def execute(self, response_text: str, context: dict) -> dict:
        """Execute agent logic."""

        if not self.llm_client:
            return {"success": False, "error": "No LLM client available"}

        # Build prompt
        prompt = self._build_prompt(response_text, context)

        # Call LLM
        try:
            llm_response = self.llm_client.send_message(
                user_message=prompt,
                max_tokens=2048,
                temperature=0.0,
            )

            # Parse response
            memories = self._parse_response(llm_response.content)

            # Save via repository
            if self.entity_repo:
                for memory in memories:
                    self.entity_repo.append_memory_entry(
                        character_name=memory["character"],
                        entry=memory["entry"]
                    )

            return {"success": True, "memories_created": len(memories)}

        except LLMError as e:
            return {"success": False, "error": str(e)}

    def _build_prompt(self, response_text: str, context: dict) -> str:
        return f"""Analyze this response and extract memorable moments...

Response: {response_text}

Respond with JSON:
{{"memories": [...]}}
"""

    def _parse_response(self, content: str) -> list[dict]:
        import json
        data = json.loads(content)
        return data.get("memories", [])
```

---

## Implementation Steps

### Phase 1: Configuration & Initialization (2-3 hours)

1. **Add AgentLLMConfig to defaults.py** ✅
   - TypedDict schema
   - Default values
   - Add to module list
   - Add to exports

2. **Add `_initialize_agent_llm_client()` to bridge_service.py** ✅
   - Reuse registry pattern
   - Override config for agent-specific settings
   - Handle disabled case gracefully

3. **Update BridgeService to initialize agent LLM** ✅
   - Call in `_initialize_services()`
   - Store in `self.agent_llm_client`

4. **Update AgentFactory signature** ✅
   - Add `agent_llm_client` parameter
   - Add `entity_repo` parameter
   - Pass to agent constructors

5. **Update AgentCoordinator** ✅
   - Add constructor parameters
   - Pass to factory

### Phase 2: First Agent Implementation (2-3 hours)

6. **Implement MemoryCreationAgent** (proof of concept)
   - Follow pattern above
   - Build prompt template
   - Parse JSON response
   - Save via entity repository
   - Write tests

7. **Test end-to-end**
   - Set up secondary LLM in settings
   - Run agent via coordinator
   - Verify memory creation works
   - Check costs

### Phase 3: Remaining Agents (Later)

8. **Implement other 9 agents** (use MemoryCreationAgent as template)
   - Each follows same pattern
   - Different prompts and parsing logic
   - 4-6 hours per agent

---

## Cost Analysis

### Current State
- Primary LLM: ~$0.03/message
- Agent LLM: $0 (not implemented)
- Triggers: $0 (semantic disabled)
- **Total: ~$0.03/message**

### After Implementation (DeepSeek via OpenRouter)
- Primary LLM: ~$0.03/message
- Agent LLM: ~$0.002/message (2 agent calls @ $0.001 each)
- Triggers: $0 (semantic still disabled)
- **Total: ~$0.032/message** (6% increase)

### Per Month (100 messages/day)
- Before: $90/month
- After: $96/month (+$6/month for agent automation)

---

## Testing Without API Costs

Use `MockLLMClient` for development:

```python
# In bridge_service.py _initialize_agent_llm_client()
from refactoring.src.infrastructure.llm.mock_client import MockLLMClient
return MockLLMClient()  # Returns "Mock response" for all calls
```

Or enable Testing Mode in TUI (F2 settings).

---

## Summary

### What Makes This Easy ✅

1. **LLM client protocol already exists** - all providers implement same interface
2. **Provider registry already built** - factory pattern ready to use
3. **Configuration system already works** - just add agent_llm section
4. **Settings UI already exists** - just needs wiring
5. **Pattern already proven** - SemanticAiClient shows exactly how to use LLMClient in agents

### What You Need to Do ❌

1. Add 40 lines to `defaults.py` (config schema)
2. Add 50 lines to `bridge_service.py` (initialize agent LLM client)
3. Update 3 lines in `agent_factory.py` (add parameters)
4. Update 3 lines in `agent_coordinator.py` (pass parameters)
5. Update 10 lines in `llm_settings_page.py` (wire UI)

**Total new code: ~100 lines** (not 40-54 hours of work!)

Then implement agents one by one, each following the proven pattern.

---

## Next Step

Shall we start with Phase 1 (Configuration & Initialization)?

I can implement all 5 steps in one go, or we can do it incrementally with testing between each step.
