# Generic OpenAI-Compatible Provider Client - Implementation Plan

## Overview

This document outlines the implementation plan for adding support for unlimited OpenAI-compatible LLM providers through a single, config-driven generic client.

### Goals

1. **Support Multiple Providers**: Enable Ollama, Groq, Together.ai, Fireworks, LM Studio, and any other OpenAI-compatible API with zero code changes
2. **Config-Driven**: Add new providers by editing config.json only
3. **Reuse Infrastructure**: Leverage existing transport layer, proxy support, and logging
4. **Streaming Support**: Support streaming responses via existing transport infrastructure
5. **Maintain Compatibility**: Keep existing `OpenAIChatClient` unchanged for backward compatibility

### Providers This Will Support

- **Local LLMs**: Ollama, LM Studio, Jan, LocalAI, vLLM
- **Cloud Providers**: Groq, Together.ai, Fireworks, Perplexity, Anyscale, Deepinfra, Replicate
- **Proxy Services**: OpenRouter (already supported), any custom proxy
- **Future Providers**: Any new OpenAI-compatible API

---

## Architecture

### Design Principles

1. **Single Client, Multiple Providers**: One `GenericOpenAIClient` class handles all providers
2. **Provider Specs in Config**: Each provider defined as a configuration entry
3. **Runtime Registration**: Providers registered dynamically at startup
4. **Standard Interface**: Implements `StreamingLLMClient` protocol

### Component Diagram

```
Config File (config.json)
    ↓
load_generic_provider_config()
    ↓
GenericOpenAIClient
    ↓
Transport Chain (Base → Proxy → Logging)
    ↓
Provider API (Ollama, Groq, Together.ai, etc.)
```

---

## Implementation Details

### Phase 1: Create GenericOpenAIClient

**File**: `src/infrastructure/llm/generic_openai_client.py`

**Class Structure**:

```python
@dataclass(slots=True)
class GenericOpenAISettings:
    """Settings for any OpenAI-compatible provider."""
    provider_id: str              # Unique identifier (e.g., "ollama", "groq")
    api_key: str | None          # Optional API key
    base_url: str                # Base URL (e.g., "http://localhost:11434")
    default_model: str           # Default model name
    custom_headers: dict[str, str] | None = None  # Optional custom headers
    organization: str | None = None               # Optional organization ID


class GenericOpenAIClient(StreamingLLMClient):
    """HTTP client for any OpenAI-compatible API using Transport abstraction.

    Supports both streaming and non-streaming responses.
    """

    def __init__(
        self,
        *,
        settings: GenericOpenAISettings,
        proxy_settings: ProxySettings | None = None,
        transport: Transport | None = None,
        logger: LoggingService | None = None,
        request_timeout: int | None = 120,
    ) -> None:
        # Build transport chain
        # Set up headers
        # Configure capabilities

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=True,
            supports_prompt_cache=False,
            supports_thinking_budget=False,
            native_system_role=True,
        )

    def send_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        **kwargs: Any,
    ) -> LLMResponse:
        # Build messages
        # Create payload for /chat/completions
        # Send via transport
        # Parse response

    def stream_message(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        conversation_history: ConversationHistory | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        **kwargs: Any,
    ) -> Iterable[str]:
        # Build messages
        # Create payload with stream=true
        # Stream via transport.post_stream()
        # Yield chunks
```

**Key Features**:

1. **Generic Settings**: `GenericOpenAISettings` works for any provider
2. **Custom Headers**: Support for provider-specific headers (e.g., Groq's rate limit headers)
3. **Streaming**: Uses existing `post_stream()` transport method
4. **Standard Endpoint**: Only supports `/v1/chat/completions` (OpenAI-compatible standard)
5. **Error Handling**: Maps HTTP errors to `LLMAuthError`, `LLMRateLimitError`, etc.

### Phase 2: Configuration System

**File**: `src/infrastructure/llm/generic_openai_config.py`

**Purpose**: Load provider configurations from config.json and environment variables

```python
def load_generic_provider_config(
    provider_id: str,
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> GenericOpenAISettings:
    """Load configuration for a generic OpenAI-compatible provider.

    Args:
        provider_id: Provider identifier (e.g., "ollama", "groq")
        config_override: Optional config dict to override file values
        start_path: Optional starting path for config resolution

    Returns:
        GenericOpenAISettings for the provider
    """
    # Resolve project root
    # Load config.json
    # Load .env file
    # Merge sources with priority: env vars > .env file > config.json
    # Return GenericOpenAISettings


def list_configured_generic_providers(
    config_override: dict[str, Any] | None = None,
    *,
    start_path: str | None = None,
) -> list[str]:
    """List all generic providers configured in config.json.

    Returns:
        List of provider IDs (e.g., ["ollama", "groq", "together"])
    """
    # Load config.json
    # Extract generic_openai_providers section
    # Return list of provider IDs
```

**Configuration Priority**:

1. **Environment Variables**: `OLLAMA_API_KEY`, `GROQ_BASE_URL`, etc.
2. **`.env` File**: Same format as environment variables
3. **`config.json`**: Structured configuration (see below)

### Phase 3: Provider Registry Integration

**File**: `src/infrastructure/llm/registry.py` (modify existing)

**Add Factory Functions**:

```python
def create_ollama_client(
    *,
    config_override: dict[str, Any] | None = None,
    logger: LoggingService | None = None,
    rp_dir: str | None = None,
) -> GenericOpenAIClient:
    """Factory for Ollama provider."""
    from .generic_openai_client import GenericOpenAIClient
    from .generic_openai_config import load_generic_provider_config

    settings = load_generic_provider_config(
        provider_id="ollama",
        config_override=config_override,
        start_path=rp_dir,
    )

    return GenericOpenAIClient(
        settings=settings,
        logger=logger,
        request_timeout=120,
    )


def create_groq_client(...) -> GenericOpenAIClient:
    """Factory for Groq provider."""
    # Similar pattern


def create_together_client(...) -> GenericOpenAIClient:
    """Factory for Together.ai provider."""
    # Similar pattern
```

**Register Providers**:

```python
# Add to registry.py initialization
register_provider(
    ProviderSpec(
        provider_id="ollama",
        display_name="Ollama (Local)",
        factory=create_ollama_client,
        requires_api_key=False,
    )
)

register_provider(
    ProviderSpec(
        provider_id="groq",
        display_name="Groq",
        factory=create_groq_client,
        requires_api_key=True,
    )
)

register_provider(
    ProviderSpec(
        provider_id="together",
        display_name="Together.ai",
        factory=create_together_client,
        requires_api_key=True,
    )
)
```

**Alternative: Dynamic Registration** (Future Enhancement)

Instead of hardcoding factory functions, we could auto-register all providers found in config:

```python
def auto_register_generic_providers(
    config_override: dict[str, Any] | None = None,
    rp_dir: str | None = None,
) -> None:
    """Automatically register all generic providers from config."""
    provider_ids = list_configured_generic_providers(
        config_override=config_override,
        start_path=rp_dir,
    )

    for provider_id in provider_ids:
        register_provider(
            ProviderSpec(
                provider_id=provider_id,
                display_name=provider_id.title(),
                factory=lambda **kwargs: create_generic_client(provider_id, **kwargs),
                requires_api_key=True,  # Infer from config
            )
        )
```

---

## Configuration Format

### config.json Structure

```json
{
  "generic_openai_providers": {
    "ollama": {
      "base_url": "http://localhost:11434/v1",
      "default_model": "llama2",
      "api_key": null,
      "custom_headers": null
    },
    "groq": {
      "base_url": "https://api.groq.com/openai/v1",
      "default_model": "mixtral-8x7b-32768",
      "api_key": null,
      "custom_headers": {
        "X-API-Version": "2024-01"
      }
    },
    "together": {
      "base_url": "https://api.together.xyz/v1",
      "default_model": "meta-llama/Llama-3-70b-chat-hf",
      "api_key": null,
      "custom_headers": null
    },
    "lm_studio": {
      "base_url": "http://localhost:1234/v1",
      "default_model": "local-model",
      "api_key": null,
      "custom_headers": null
    },
    "fireworks": {
      "base_url": "https://api.fireworks.ai/inference/v1",
      "default_model": "accounts/fireworks/models/mixtral-8x7b-instruct",
      "api_key": null,
      "custom_headers": null
    }
  }
}
```

### Environment Variables

```bash
# Ollama (typically no API key needed)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama2

# Groq
GROQ_API_KEY=gsk_...
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=mixtral-8x7b-32768

# Together.ai
TOGETHER_API_KEY=...
TOGETHER_BASE_URL=https://api.together.xyz/v1
TOGETHER_MODEL=meta-llama/Llama-3-70b-chat-hf

# LM Studio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model

# Fireworks
FIREWORKS_API_KEY=...
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
FIREWORKS_MODEL=accounts/fireworks/models/mixtral-8x7b-instruct
```

### .env File

```env
# Same format as environment variables
OLLAMA_BASE_URL=http://localhost:11434/v1
GROQ_API_KEY=gsk_...
TOGETHER_API_KEY=...
```

---

## Streaming Implementation

The `GenericOpenAIClient` will support streaming using the existing transport infrastructure:

```python
def stream_message(self, user_message: str, **kwargs) -> Iterable[str]:
    """Stream response from OpenAI-compatible API."""

    # Build payload with stream=true
    payload = {
        "model": self._model,
        "messages": messages,
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    # Make streaming request
    request = TransportRequest(
        endpoint=f"{self._base_url}/chat/completions",
        payload=payload,
        headers=self._headers,
        timeout_seconds=self._timeout,
    )

    try:
        # Yield chunks from transport
        for chunk in self._transport.post_stream(request):
            yield chunk
    except TransportError as exc:
        raise LLMError(f"Transport error during streaming: {exc}") from exc
```

**Note**: The existing `RequestsTransport.post_stream()` already handles SSE parsing, so the client just needs to pass through chunks.

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/infrastructure/llm/test_generic_openai_client.py`

```python
def test_generic_client_initialization():
    """Test GenericOpenAIClient initializes correctly."""

def test_build_messages_with_system_prompt():
    """Test message building with system prompt."""

def test_send_message_success():
    """Test successful message send with mock transport."""

def test_send_message_auth_error():
    """Test authentication error handling."""

def test_send_message_rate_limit():
    """Test rate limit error handling."""

def test_stream_message_chunks():
    """Test streaming message returns chunks."""
```

### Integration Tests

**File**: `tests/integration/test_generic_providers.py`

```python
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not running")
def test_ollama_send_message():
    """Test sending message to local Ollama instance."""

@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not running")
def test_ollama_stream_message():
    """Test streaming message from Ollama."""

@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="Groq API key not set")
def test_groq_send_message():
    """Test sending message to Groq."""
```

### Manual Testing

1. **Ollama Local Testing**:
   ```bash
   # Start Ollama
   ollama serve

   # Pull a model
   ollama pull llama2

   # Test with Python
   python -c "
   from src.infrastructure.llm.registry import create_client
   client = create_client('ollama', rp_dir='.')
   response = client.send_message('Hello!')
   print(response.content)
   "
   ```

2. **Groq Cloud Testing**:
   ```bash
   export GROQ_API_KEY=gsk_...
   python -c "
   from src.infrastructure.llm.registry import create_client
   client = create_client('groq', rp_dir='.')
   response = client.send_message('Hello!')
   print(response.content)
   "
   ```

---

## Migration Path

### Adding a New Provider (User Perspective)

**Option 1: Edit config.json**

```json
{
  "generic_openai_providers": {
    "my_custom_provider": {
      "base_url": "https://api.mycustom.com/v1",
      "default_model": "my-model-v1",
      "api_key": null,
      "custom_headers": {
        "X-Custom-Header": "value"
      }
    }
  }
}
```

**Option 2: Set environment variables**

```bash
export MY_CUSTOM_PROVIDER_BASE_URL=https://api.mycustom.com/v1
export MY_CUSTOM_PROVIDER_MODEL=my-model-v1
export MY_CUSTOM_PROVIDER_API_KEY=...
```

**Option 3: Use programmatically**

```python
from src.infrastructure.llm.generic_openai_client import GenericOpenAIClient, GenericOpenAISettings

settings = GenericOpenAISettings(
    provider_id="my_custom",
    api_key="...",
    base_url="https://api.mycustom.com/v1",
    default_model="my-model-v1",
)

client = GenericOpenAIClient(settings=settings)
response = client.send_message("Hello!")
```

### Developer: Adding Factory to Registry

To make the provider selectable in the TUI/Bridge, add a factory function:

```python
# In registry.py
def create_my_custom_client(**kwargs) -> GenericOpenAIClient:
    from .generic_openai_config import load_generic_provider_config
    settings = load_generic_provider_config("my_custom_provider", **kwargs)
    return GenericOpenAIClient(settings=settings, **kwargs)

register_provider(
    ProviderSpec(
        provider_id="my_custom",
        display_name="My Custom Provider",
        factory=create_my_custom_client,
        requires_api_key=True,
    )
)
```

---

## Implementation Checklist

### Phase 1: Core Client (2-3 hours)
- [ ] Create `src/infrastructure/llm/generic_openai_client.py`
  - [ ] `GenericOpenAISettings` dataclass
  - [ ] `GenericOpenAIClient` class
  - [ ] `send_message()` implementation
  - [ ] `stream_message()` implementation
  - [ ] Error handling (auth, rate limit, general)
  - [ ] Response parsing

### Phase 2: Configuration System (1 hour)
- [ ] Create `src/infrastructure/llm/generic_openai_config.py`
  - [ ] `load_generic_provider_config()` function
  - [ ] `list_configured_generic_providers()` function
  - [ ] Environment variable merging
  - [ ] Config validation

### Phase 3: Registry Integration (1 hour)
- [ ] Modify `src/infrastructure/llm/registry.py`
  - [ ] Add `create_ollama_client()` factory
  - [ ] Add `create_groq_client()` factory
  - [ ] Add `create_together_client()` factory
  - [ ] Register providers with specs
  - [ ] Update `__all__` exports

### Phase 4: Testing (1-2 hours)
- [ ] Create unit tests
  - [ ] Test client initialization
  - [ ] Test message building
  - [ ] Test send_message with mock transport
  - [ ] Test stream_message with mock transport
  - [ ] Test error handling
- [ ] Create integration tests
  - [ ] Test Ollama (local)
  - [ ] Test Groq (cloud, requires API key)
- [ ] Manual testing
  - [ ] Verify Ollama connection
  - [ ] Verify streaming works
  - [ ] Verify error messages

### Phase 5: Documentation (30 minutes)
- [ ] Update `README.md` with provider setup instructions
- [ ] Create `docs/PROVIDER_CONFIGURATION.md`
- [ ] Document environment variables
- [ ] Add example configurations

---

## Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2-3 hours | Core GenericOpenAIClient implementation |
| Phase 2 | 1 hour | Configuration loading system |
| Phase 3 | 1 hour | Registry integration and factories |
| Phase 4 | 1-2 hours | Testing (unit + integration) |
| Phase 5 | 30 min | Documentation |
| **Total** | **5.5-7.5 hours** | Complete implementation |

---

## Future Enhancements

### Dynamic Provider Discovery
Auto-register all providers found in config without requiring factory functions:

```python
# Automatically discover and register all generic providers at startup
auto_register_generic_providers(rp_dir=".")
```

### Provider Templates
Pre-defined templates for common providers:

```python
PROVIDER_TEMPLATES = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama2",
        "requires_api_key": False,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "mixtral-8x7b-32768",
        "requires_api_key": True,
    },
}
```

### Model Discovery API
Query provider for available models:

```python
client = create_client("ollama")
models = client.list_available_models()  # Query /v1/models endpoint
```

### Advanced Features
- Retry logic with exponential backoff
- Request caching
- Token counting utilities
- Cost tracking per provider

---

## Dependencies

### Existing Code (No Changes Needed)
- ✅ `Transport` protocol and implementations
- ✅ `StreamingLLMClient` protocol
- ✅ `RequestsTransport.post_stream()` SSE parsing
- ✅ `ProxyTransport` and `LoggingTransport` decorators
- ✅ `config_utils` for configuration loading

### New Files to Create
1. `src/infrastructure/llm/generic_openai_client.py` (~250 lines)
2. `src/infrastructure/llm/generic_openai_config.py` (~150 lines)
3. `tests/unit/infrastructure/llm/test_generic_openai_client.py` (~200 lines)
4. `tests/integration/test_generic_providers.py` (~100 lines)
5. `docs/PROVIDER_CONFIGURATION.md` (documentation)

### Files to Modify
1. `src/infrastructure/llm/registry.py` (add factory functions)
2. `src/infrastructure/llm/__init__.py` (export new classes)
3. `config/config.json` (add example provider configs)

---

## Success Criteria

1. ✅ Can connect to Ollama locally without API key
2. ✅ Can connect to Groq with API key
3. ✅ Can connect to Together.ai with API key
4. ✅ Streaming works for all providers
5. ✅ Adding new provider requires only config changes
6. ✅ All tests pass (unit + integration)
7. ✅ Existing `OpenAIChatClient` continues to work
8. ✅ Documentation complete with examples

---

## Questions for User

Before implementation, please confirm:

1. **Provider Priority**: Should we implement all providers at once, or start with Ollama + Groq?
2. **Config Location**: Should generic provider configs go in the main `config.json`, or a separate `providers.json`?
3. **Auto-Registration**: Should we implement dynamic provider discovery now, or keep manual factory functions?
4. **Testing Requirements**: Do you have Ollama installed for integration testing, or should we focus on unit tests with mocks?
5. **Documentation**: Should provider setup docs be in main README or separate guide?

---

## Conclusion

This plan provides a comprehensive, extensible system for supporting unlimited OpenAI-compatible LLM providers. The implementation is clean, config-driven, and reuses existing infrastructure. Users can add new providers by editing config.json without touching code.

The estimated 5.5-7.5 hour implementation time includes all testing and documentation, making this a high-value addition that unlocks the entire OpenAI-compatible ecosystem.
