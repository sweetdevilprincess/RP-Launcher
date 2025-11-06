# Transport System Guide

**Last Updated:** 2025-10-20
**Workstream:** I (Clients & Transport)

---

## Overview

The Transport system provides a clean HTTP abstraction layer for LLM API clients, enabling:
- **Testability**: Mock HTTP responses without external dependencies
- **Composability**: Chain transports (logging, proxy, retry, etc.)
- **Multi-Provider Support**: Easy integration of new LLM providers
- **Separation of Concerns**: HTTP logic separate from business logic

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────┐
│           LLM Client (e.g., ClaudeAPIClient)    │
│  - Business logic (messages, thinking, etc.)    │
│  - Error mapping (HTTP → domain exceptions)     │
└────────────────┬────────────────────────────────┘
                 │ uses
                 ▼
┌─────────────────────────────────────────────────┐
│              Transport Chain                     │
│  LoggingTransport → ProxyTransport →            │
│                → RequestsTransport               │
└─────────────────────────────────────────────────┘
                 │
                 ▼
         HTTP API Endpoint
```

### Transport Protocol

**Location:** `src/shared/interfaces/transport.py`

```python
class Transport(Protocol):
    """Contract for HTTP-like transports."""

    def post(self, request: TransportRequest) -> TransportResponse:
        """Send a POST request."""

    def get(self, request: TransportRequest) -> TransportResponse:
        """Send a GET request."""
```

**Request/Response Types:**
- `TransportRequest`: endpoint, payload, headers, timeout
- `TransportResponse`: status_code, body, headers
- `TransportError`: Exception for transport failures

### Available Transports

| Transport | Purpose | Location |
|-----------|---------|----------|
| `RequestsTransport` | Production HTTP using requests.Session | `infrastructure/transports/requests_transport.py` |
| `LoggingTransport` | Structured logging decorator | `infrastructure/transports/logging_transport.py` |
| `ProxyTransport` | Proxy routing and auth | `infrastructure/transports/proxy_transport.py` |
| `FakeTransport` | Testing utility | `infrastructure/transports/fake_transport.py` |

---

## Adding a New Provider

Follow this pattern to add a new LLM provider using Transport.

### Step 1: Create Settings Dataclass

```python
# src/infrastructure/llm/newprovider_client.py

@dataclass(slots=True)
class NewProviderSettings:
    api_key: Optional[str]
    model: Optional[str]
    base_url: Optional[str]
```

### Step 2: Create Settings Loader

```python
def load_newprovider_settings(
    config_override: Optional[Dict[str, Any]] = None,
    *,
    start_path: Optional[str] = None,
) -> NewProviderSettings:
    """Load credentials from env/config/.env."""

    start = Path(start_path) if start_path else None
    project_root = resolve_project_root(start)

    config_data: Dict[str, Any] = {}
    if config_override:
        config_data.update(config_override)
    else:
        config_data.update(read_json_file(project_root / "config" / "config.json"))

    env_file_values = read_env_file(project_root / ".env")

    merged = merge_config_sources(
        env_keys={
            "api_key": "NEWPROVIDER_API_KEY",
            "model": "NEWPROVIDER_MODEL",
            "base_url": "NEWPROVIDER_BASE_URL",
        },
        config_keys={
            "api_key": config_data.get("newprovider_api_key"),
            "model": config_data.get("newprovider_model"),
            "base_url": config_data.get("newprovider_base_url"),
        },
        env_file_keys=env_file_values,
    )

    return NewProviderSettings(
        api_key=merged.get("api_key"),
        model=merged.get("model"),
        base_url=merged.get("base_url"),
    )
```

### Step 3: Create Client Class

```python
from ...shared.interfaces import (
    LoggingService,
    Transport,
    TransportError,
    TransportRequest,
    TransportResponse,
)
from ..transports import LoggingTransport, ProxyTransport, RequestsTransport

_DEFAULT_MODEL = "provider-default-model"
_DEFAULT_BASE_URL = "https://api.newprovider.com/v1/chat"

class NewProviderClient(LLMClient):
    """HTTP client for NewProvider API using Transport abstraction."""

    provider_id = "newprovider_api"

    def __init__(
        self,
        *,
        settings: Optional[NewProviderSettings] = None,
        proxy_settings: Optional[ProxySettings] = None,
        transport: Optional[Transport] = None,
        logger: Optional[LoggingService] = None,
        config_override: Optional[Dict[str, Any]] = None,
        rp_dir: Optional[str] = None,
        request_timeout: Optional[int] = 60,
    ) -> None:
        start_path = rp_dir if rp_dir else None

        # Load settings
        self._settings = settings or load_newprovider_settings(
            config_override=config_override,
            start_path=start_path,
        )

        if not self._settings.api_key:
            raise LLMAuthError("NewProvider API key missing.")

        self._proxy_settings = proxy_settings or load_proxy_settings(
            config_override=config_override,
            start_path=start_path,
        )

        # Build transport chain: Base → Proxy → Logging
        base_transport: Transport = transport or RequestsTransport()
        base_transport = ProxyTransport(base_transport, proxy_config=self._proxy_settings)
        if logger is not None:
            base_transport = LoggingTransport(base_transport, logger, name="newprovider")
        self._transport = base_transport
        self._logger = logger

        self._model = self._settings.model or _DEFAULT_MODEL
        self._base_url = (self._settings.base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._timeout = request_timeout

        # Build base headers
        self._base_headers: Dict[str, str] = {
            "authorization": f"Bearer {self._settings.api_key}",
            "content-type": "application/json",
        }

        self._capabilities = ProviderCapabilities(
            supports_streaming=False,
            supports_prompt_cache=False,
            supports_thinking_budget=False,
            native_system_role=True,
        )

    def capabilities(self) -> ProviderCapabilities:
        return self._capabilities
```

### Step 4: Implement send_message()

```python
def send_message(
    self,
    user_message: str,
    *,
    cached_context: Optional[str] = None,
    conversation_history: Optional[ConversationHistory] = None,
    max_tokens: int = 2048,
    temperature: float = 1.0,
    **kwargs: Any,
) -> LLMResponse:
    """Send a message to the NewProvider API."""

    # Build messages array
    messages: List[Dict[str, str]] = []

    if cached_context:
        messages.append({"role": "system", "content": cached_context})

    if conversation_history:
        for entry in conversation_history:
            if isinstance(entry, ConversationMessage):
                role, content = entry.role, entry.content
            else:
                role = entry.get("role")
                content = entry.get("content")
            if role in {"user", "assistant", "system"}:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    # Build request payload
    payload: Dict[str, Any] = {
        "model": self._model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Make request via transport
    request = TransportRequest(
        endpoint=self._base_url,
        payload=payload,
        headers=self._base_headers,
        timeout_seconds=self._timeout,
    )

    try:
        transport_response = self._transport.post(request)
    except TransportError as exc:
        raise LLMError(f"Transport error: {exc}") from exc

    # Handle HTTP errors
    if transport_response.status_code == 401:
        error_msg = self._extract_error_message(transport_response.body)
        raise LLMAuthError(f"Authentication failed: {error_msg}")
    elif transport_response.status_code == 429:
        error_msg = self._extract_error_message(transport_response.body)
        raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
    elif transport_response.status_code >= 400:
        error_msg = self._extract_error_message(transport_response.body)
        raise LLMError(
            f"NewProvider API error ({transport_response.status_code}): {error_msg}"
        )

    # Parse successful response
    response_data = transport_response.body
    if not isinstance(response_data, dict):
        raise LLMError(f"Unexpected response format: {type(response_data)}")

    content = self._extract_content(response_data)
    usage = self._extract_usage(response_data)

    return LLMResponse(
        content=content,
        usage=usage,
        raw_response=response_data,
        thinking=None,
    )
```

### Step 5: Add Helper Methods

```python
@staticmethod
def _extract_content(response_data: Dict[str, Any]) -> str:
    """Extract text content from API response."""
    choices = response_data.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    return message.get("content", "")

@staticmethod
def _extract_usage(response_data: Dict[str, Any]) -> UsageStats:
    """Extract usage stats from API response."""
    usage = response_data.get("usage", {})
    return UsageStats(
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
    )

@staticmethod
def _extract_error_message(body: Any) -> str:
    """Extract error message from API error response."""
    if isinstance(body, dict):
        error = body.get("error", {})
        if isinstance(error, dict):
            return error.get("message", str(body))
        return str(error) if error else str(body)
    return str(body)
```

### Step 6: Register Provider

```python
# src/infrastructure/llm/registry.py

from .newprovider_client import (
    NewProviderClient,
    NewProviderSettings,
    load_newprovider_settings,
)

def _newprovider_factory(config: Dict[str, Any]) -> LLMClient:
    settings: NewProviderSettings = load_newprovider_settings(config_override=config)
    proxy_settings: ProxySettings = load_proxy_settings(config_override=config)
    return NewProviderClient(
        settings=settings,
        proxy_settings=proxy_settings,
        config_override=config,
        rp_dir=config.get("rp_dir"),
    )

register_provider(
    ProviderSpec(
        provider_id="newprovider_api",
        label="NewProvider API",
        supports_streaming=False,
        factory=_newprovider_factory,
        description="NewProvider LLM integration",
    )
)
```

---

## Testing Your Provider

### Unit Tests

Use `FakeTransport` to test without making real HTTP calls:

```python
from infrastructure.transports.fake_transport import FakeTransport

def test_newprovider_success():
    fake_transport = FakeTransport()
    fake_transport.set_response(
        status_code=200,
        body={
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    )

    client = NewProviderClient(
        settings=NewProviderSettings(api_key="test-key"),
        transport=fake_transport,
    )

    response = client.send_message("Hi")

    assert response.content == "Hello!"
    assert response.usage.input_tokens == 10
    assert fake_transport.last_request.endpoint.endswith("/chat")
```

---

## Best Practices

### 1. Error Handling

Always map HTTP status codes to domain exceptions:
- `401` → `LLMAuthError`
- `429` → `LLMRateLimitError`
- `4xx/5xx` → `LLMError`

### 2. Transport Chain

Build the chain in this order:
```python
RequestsTransport → ProxyTransport → LoggingTransport
```

This ensures:
1. Base HTTP happens first
2. Proxy wraps HTTP
3. Logging wraps everything (logs final request/response)

### 3. Configuration

Support all configuration sources:
- Environment variables (`PROVIDER_API_KEY`)
- Config file (`config/config.json`)
- .env file (`.env`)
- Direct override (`config_override` parameter)

### 4. Headers

Always include:
- `authorization` or `x-api-key` for authentication
- `content-type: application/json`
- Provider-specific headers (version, user-agent, etc.)

### 5. Response Parsing

Validate response format before accessing fields:
```python
if not isinstance(response_data, dict):
    raise LLMError(f"Unexpected response format: {type(response_data)}")
```

---

## Common Patterns

### Multiple Endpoints

If your provider has multiple endpoints (like OpenAI):

```python
_CHAT_ENDPOINT = "/v1/chat/completions"
_COMPLETION_ENDPOINT = "/v1/completions"

def _send_chat(self, ...) -> LLMResponse:
    request = TransportRequest(
        endpoint=f"{self._base_url}{_CHAT_ENDPOINT}",
        ...
    )

def _send_completion(self, ...) -> LLMResponse:
    request = TransportRequest(
        endpoint=f"{self._base_url}{_COMPLETION_ENDPOINT}",
        ...
    )
```

### Custom Headers Per Request

```python
headers = dict(self._base_headers)
headers["X-Custom-Header"] = "value"

request = TransportRequest(
    endpoint=self._base_url,
    headers=headers,
    ...
)
```

### Retry Logic

Add a retry transport to the chain:

```python
from infrastructure.retry import RetryTransport

base_transport = RequestsTransport()
base_transport = RetryTransport(base_transport, max_retries=3)
base_transport = ProxyTransport(base_transport, ...)
```

---

## Existing Implementations

### Reference Implementations

Study these for patterns:

| Provider | File | Notes |
|----------|------|-------|
| **OpenRouter** | `openrouter_client.py` | ✅ Best reference - cleanest Transport usage |
| **Claude API** | `claude_api_client.py` | HTTP-based, thinking support, prompt caching |
| **OpenAI** | `openai_client.py` | Multiple endpoints (responses + chat completions) |
| **Claude SDK** | `claude_sdk_client.py` | ⚠️ NOT Transport-based (Node.js bridge) |

### Transport Usage Comparison

```python
# ClaudeAPIClient - Single endpoint
request = TransportRequest(
    endpoint="https://api.anthropic.com/v1/messages",
    payload={"model": "...", "messages": [...]},
    headers={"x-api-key": "...", "anthropic-version": "2023-06-01"},
)

# OpenAIClient - Dynamic endpoint
request = TransportRequest(
    endpoint=f"{self._base_url}{_RESPONSES_ENDPOINT}",  # or _CHAT_COMPLETIONS_ENDPOINT
    payload={"model": "...", "input": [...]},
    headers={"authorization": "Bearer ..."},
)

# OpenRouterClient - Headers with referer
request = TransportRequest(
    endpoint="https://openrouter.ai/api/v1/chat/completions",
    payload={"model": "...", "messages": [...]},
    headers={
        "authorization": "Bearer ...",
        "http-referer": "...",  # Optional site_url
        "x-title": "...",        # Optional app_name
    },
)
```

---

## Troubleshooting

### Transport Not Called

**Problem:** Requests not going through transport chain
**Solution:** Verify you're calling `self._transport.post()`, not `self._client.create()`

### Proxy Not Working

**Problem:** Proxy settings ignored
**Solution:** Check `ProxySettings.use_proxy` is True and `proxy_url` is set

### Logging Not Appearing

**Problem:** No log output from requests
**Solution:** Ensure `LoggingTransport` is last in the chain and logger is passed to `__init__`

### Tests Failing with Real HTTP

**Problem:** Tests making actual HTTP calls
**Solution:** Pass `FakeTransport` to client in tests:
```python
client = MyClient(transport=FakeTransport())
```

---

## Migration Checklist

When converting an existing client to use Transport:

- [ ] Import Transport types (`Transport`, `TransportRequest`, `TransportResponse`, `TransportError`)
- [ ] Import transport implementations (`RequestsTransport`, `ProxyTransport`, `LoggingTransport`)
- [ ] Add `transport` and `logger` parameters to `__init__`
- [ ] Build transport chain: `RequestsTransport() → ProxyTransport() → LoggingTransport()`
- [ ] Replace SDK client calls with `self._transport.post(TransportRequest(...))`
- [ ] Update error handling to check `transport_response.status_code`
- [ ] Update response parsing to work with dicts instead of SDK objects
- [ ] Add `_extract_error_message()` helper
- [ ] Update registry factory to pass `config_override` and `rp_dir`
- [ ] Write tests using `FakeTransport`
- [ ] Verify all existing transport tests still pass

---

## Future Enhancements

Potential additions to the transport system:

1. **RetryTransport**: Automatic retry with exponential backoff
2. **CachingTransport**: Response caching for identical requests
3. **MetricsTransport**: Request/response metrics collection
4. **RateLimitTransport**: Client-side rate limiting
5. **CircuitBreakerTransport**: Fail fast when provider is down

---

*For questions or contributions, see the main refactoring plan and Workstream I documentation.*
