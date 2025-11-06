# Workstream I - Clients & Transport Implementation Plan

**Date Created:** 2025-10-20
**Date Completed:** 2025-10-20
**Status:** ✅ COMPLETE
**Actual Effort:** ~8 hours

---

## Progress Summary

### ✅ Completed
- **Phase 1:** Transport test suite (60 tests) - ALL PASSING
  - FakeTransport utility created
  - RequestsTransport: 20 tests
  - LoggingTransport: 15 tests
  - ProxyTransport: 25 tests

- **Phase 2:** Proxy configuration consolidation - COMPLETE
  - Created `ProxySettings` dataclass in `shared/models.py`
  - Updated `ProxyTransport` to use `ProxySettings` (type-safe)
  - Updated `load_proxy_config()` to return `ProxySettings`
  - Consolidated `llm/proxy.py` to use shared `ProxySettings`
  - Fixed `OpenRouterClient` to use shared `ProxySettings`
  - All 60 transport tests still passing

- **Phase 3:** ClaudeAPIClient refactored to use Transport - COMPLETE
  - Removed anthropic SDK dependency for API calls (now HTTP-based)
  - Added Transport parameter to `__init__` with logging/proxy support
  - Built transport chain: RequestsTransport → ProxyTransport → LoggingTransport
  - Replaced `anthropic.Anthropic` client with Transport POST requests
  - Manual request building (endpoint, headers, payload)
  - HTTP status code → LLM exception mapping (401→Auth, 429→RateLimit, etc.)
  - Updated response parsing to work with dict instead of anthropic objects
  - All transport tests still passing (60/60)

- **Phase 4:** OpenAIClient refactored to use Transport - COMPLETE
  - Removed openai SDK dependency for API calls (now HTTP-based)
  - Added Transport parameter to `__init__` with logging/proxy support
  - Built transport chain: RequestsTransport → ProxyTransport → LoggingTransport
  - Supports 2 endpoints: `/v1/responses` and `/v1/chat/completions`
  - Refactored both `_send_via_responses()` and `_send_via_chat_completions()`
  - HTTP status code → LLM exception mapping (401→Auth, 429→RateLimit, etc.)
  - Updated all response parsing helpers to work with dicts
  - Registry updated with `config_override` parameter
  - All transport tests still passing (60/60)

- **Phase 5:** ClaudeSDKClient documented as accessibility feature - COMPLETE
  - ClaudeSDKClient INTENTIONALLY not refactored to use Transport
  - Uses Node.js bridge instead of direct API calls
  - Critical accessibility feature for users without API keys
  - Provides first-class SDK access (not a fallback or exception)
  - Both SDK and API approaches equally supported by design

- **Phase 6:** Created TRANSPORT_SYSTEM.md with provider guide - COMPLETE
  - Comprehensive guide for adding new LLM providers
  - Step-by-step implementation instructions
  - Testing guide using FakeTransport
  - Best practices and common patterns
  - Reference to existing implementations
  - Troubleshooting section
  - Migration checklist for existing clients

---

## ClaudeSDKClient: Accessibility Feature

### Why ClaudeSDKClient Exists

**ClaudeSDKClient is NOT an exception or workaround** - it's a deliberate, first-class feature designed for accessibility:

1. **No API Key Required**: Users without Anthropic API keys can still use Claude
2. **Node.js Bridge**: Uses the official Anthropic SDK via Node.js subprocess
3. **Equal Status**: Both SDK and API approaches are fully supported design choices
4. **User Choice**: Users pick their preference based on their situation:
   - Have API key → Use `ClaudeAPIClient` (HTTP via Transport)
   - No API key → Use `ClaudeSDKClient` (Node.js SDK bridge)

### Why It's Not Refactored

**ClaudeSDKClient intentionally does NOT use Transport** because:

1. **Different Communication Model**: Communicates with Node.js subprocess, not HTTP endpoints
2. **Not HTTP-based**: Transport abstraction is for HTTP; SDK uses IPC/subprocess
3. **Correct Architecture**: Using the right tool for the job (subprocess communication ≠ HTTP)
4. **Accessibility First**: Refactoring would break access for users without API keys

### Multi-Provider Design Goal

From the user's design clarification:

> "I want to be clear, I want to eventually make it so that anyone can use any LLM provider that they want with this down the line, that is why I have the LLM options that I do now and why I have the SDK and the API options so that people can like then with the SDK if they do not have an API key, like I use it, or the API key as well."

**Key Principles:**
- ✅ Maximum flexibility: Any user, any provider, any access method
- ✅ SDK and API are both first-class citizens (not one better than the other)
- ✅ Accessibility is a core feature, not an afterthought
- ✅ Transport makes adding new providers easy (HTTP-based providers)
- ✅ Non-HTTP providers (like SDK bridges) use appropriate architecture

---

## Context

### Dependencies
- ✅ Workstream F complete (206/206 tests passing)
- ✅ Workstream H complete (Logging system available)
- ✅ Circular import fixed (EntityType → shared/models.py)
- ✅ Codebase stable and ready for Workstream I

### Requirements (from refactor_plan_v1.2.0.md)
1. Build `Transport` interface (`post`, optional `get`) returning typed responses
2. Implement `RequestsTransport`, `ProxyTransport`, and `LoggingTransport`
3. Refactor `deepseek`, `claude`, and related clients to accept transport via DI
4. Normalize error handling; map HTTP status codes to domain-specific exceptions
5. Add contract tests using fake transports
6. Review proxy configuration loading for redundancy; centralize in one utility

---

## Current State Analysis

### ✅ Already Implemented (Working)
1. **Transport Protocol** (`shared/interfaces/transport.py`)
   - TransportRequest dataclass (endpoint, payload, headers, timeout)
   - TransportResponse dataclass (status_code, body, headers)
   - TransportError exception
   - Transport protocol (post, get methods)

2. **RequestsTransport** (`infrastructure/transports/requests_transport.py`)
   - Production implementation using requests.Session
   - JSON/text response parsing
   - Exception wrapping to TransportError

3. **LoggingTransport** (`infrastructure/transports/logging_transport.py`)
   - Decorator pattern wrapping another transport
   - Structured logging for requests/responses
   - Header masking (authorization, proxy tokens)
   - Integrated with Workstream H logging

4. **ProxyTransport** (`infrastructure/transports/proxy_transport.py`)
   - Proxy URL rewriting
   - Proxy token injection
   - Config-driven proxy usage

5. **OpenRouterClient** (`infrastructure/llm/openrouter_client.py`)
   - **REFERENCE IMPLEMENTATION** - Already uses Transport correctly ✅
   - Shows proper Transport composition
   - Demonstrates error mapping pattern

### ❌ Work Needed

1. **ClaudeAPIClient** (`infrastructure/llm/claude_api_client.py`)
   - Currently uses anthropic SDK directly
   - Needs refactoring to use Transport
   - ~260 lines, uses anthropic.Anthropic client

2. **ClaudeSDKClient** (`infrastructure/llm/claude_sdk_client.py`)
   - Uses legacy Node.js bridge (IPC, not HTTP)
   - **Decision: SKIP** - Transport doesn't apply to IPC
   - Document as acceptable exception

3. **OpenAIClient** (`infrastructure/llm/openai_client.py`)
   - Currently uses openai SDK directly
   - Needs refactoring to use Transport
   - ~495 lines, uses two endpoints (responses, chat_completions)

4. **No Transport Tests**
   - No tests for RequestsTransport
   - No tests for LoggingTransport
   - No tests for ProxyTransport
   - No FakeTransport for contract testing

5. **Proxy Configuration Duplication**
   - `proxy_transport.py` has `load_proxy_config()` (returns dict)
   - `proxy.py` has `load_proxy_settings()` (returns ProxySettings dataclass)
   - **Decision:** Use `proxy.py` approach (typed, more complete)

6. **No Documentation**
   - No usage guide for Transport system
   - No examples for client integration
   - No testing guide

---

## Implementation Plan

### Phase 1: Create Transport Tests ⏱️ 2-3 hours
**Priority: HIGH** - Tests validate existing implementations and guide refactoring

#### 1.1 RequestsTransport Tests (~25 tests)

**File:** `tests/infrastructure/transports/test_requests_transport.py`

**Test Categories:**
- **Basic Operations** (5 tests)
  - POST request with JSON payload
  - GET request
  - Custom headers propagation
  - Timeout configuration
  - Response status code capture

- **Response Parsing** (6 tests)
  - JSON response parsing
  - Plain text response fallback
  - Empty response handling
  - Invalid JSON handling
  - Response headers capture
  - Binary content handling

- **Error Handling** (8 tests)
  - Network connection errors → TransportError
  - Timeout errors → TransportError
  - DNS resolution errors → TransportError
  - SSL/TLS errors → TransportError
  - Invalid URL errors → TransportError
  - HTTP errors (4xx, 5xx) still return response
  - Connection refused handling
  - Exception wrapping verification

- **Session Management** (3 tests)
  - Custom session injection
  - Session reuse across requests
  - Session configuration

- **Edge Cases** (3 tests)
  - None payload handling
  - Empty headers handling
  - Very large payloads

#### 1.2 LoggingTransport Tests (~15 tests)

**File:** `tests/infrastructure/transports/test_logging_transport.py`

**Test Categories:**
- **Logging Behavior** (6 tests)
  - Logs POST request with context
  - Logs GET request with context
  - Logs response with status code
  - Verifies log level (debug)
  - Verifies structured context format
  - Custom transport name in logs

- **Header Masking** (4 tests)
  - Masks Authorization header
  - Masks X-Proxy-Authorization header
  - Preserves other headers
  - Handles missing headers

- **Decorator Pattern** (3 tests)
  - Wraps another transport correctly
  - Passes through requests unchanged
  - Passes through responses unchanged

- **Integration** (2 tests)
  - Works with RequestsTransport
  - Works with ProxyTransport

#### 1.3 ProxyTransport Tests (~20 tests)

**File:** `tests/infrastructure/transports/test_proxy_transport.py`

**Test Categories:**
- **Proxy URL Rewriting** (5 tests)
  - Rewrites endpoint to proxy_url when use_proxy=True
  - Preserves original endpoint when use_proxy=False
  - Handles missing proxy_url gracefully
  - Handles empty proxy_url
  - Preserves payload when rewriting

- **Proxy Token Injection** (4 tests)
  - Adds X-Proxy-Authorization header when proxy_token provided
  - Uses Bearer format
  - Preserves existing headers
  - Skips token injection when no token

- **Configuration** (6 tests)
  - Loads config from ProxySettings
  - Loads config from dict (legacy)
  - Loads config from file (via load_proxy_config)
  - Respects use_proxy flag
  - Handles missing config gracefully
  - Config priority (env > config > .env)

- **Decorator Pattern** (3 tests)
  - Wraps another transport
  - POST passes through correctly
  - GET passes through correctly

- **Integration** (2 tests)
  - Works with RequestsTransport
  - Composable with LoggingTransport

#### 1.4 FakeTransport Implementation

**File:** `src/infrastructure/transports/fake_transport.py`

**Purpose:** Testing utility for contract testing and mocking

**Features:**
- Predictable responses (pre-configured)
- Error simulation (raise TransportError on demand)
- Request capture (for assertions)
- Configurable status codes and bodies
- Fluent API for test setup

**Example:**
```python
fake = FakeTransport()
fake.add_response(status_code=200, body={"result": "success"})
fake.add_error(TransportError("Network failure"))

# Use in tests
response = fake.post(request)
assert fake.last_request.endpoint == expected_url
```

**File:** `tests/infrastructure/transports/test_fake_transport.py`

**Tests:**
- FakeTransport returns configured responses
- FakeTransport raises configured errors
- Request capture works
- Multiple responses queue correctly

#### Files to Create
- `tests/infrastructure/transports/__init__.py`
- `tests/infrastructure/transports/test_requests_transport.py` (~25 tests)
- `tests/infrastructure/transports/test_logging_transport.py` (~15 tests)
- `tests/infrastructure/transports/test_proxy_transport.py` (~20 tests)
- `tests/infrastructure/transports/test_fake_transport.py` (~5 tests)
- `src/infrastructure/transports/fake_transport.py` (~100 lines)

**Total Tests:** ~65 tests

---

### Phase 2: Consolidate Proxy Configuration ⏱️ 1 hour
**Priority: MEDIUM** - Removes duplication, centralizes config

#### Current State

**proxy_transport.py:**
```python
def load_proxy_config(rp_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Returns dict with proxy_url, proxy_token, use_proxy"""
    # Loads from env vars + config.json
```

**proxy.py:**
```python
@dataclass(slots=True)
class ProxySettings:
    proxy_url: Optional[str]
    proxy_token: Optional[str]
    use_proxy: bool

def load_proxy_settings(...) -> ProxySettings:
    """Returns typed ProxySettings dataclass"""
    # Loads from env, config.json, .env with merge logic
```

#### Decision: Use proxy.py Approach

**Reasons:**
1. Typed dataclass (better than dict)
2. More complete (handles .env file)
3. Better merge logic (env > config > .env)
4. Already used by Claude/OpenAI clients
5. Has `to_proxy_config()` method for compatibility

#### Changes

**File:** `src/infrastructure/transports/proxy_transport.py`

**Updates:**
1. Remove `load_proxy_config()` function
2. Remove `_find_config_json()` helper
3. Update `ProxyTransport.__init__()` signature:
   ```python
   def __init__(
       self,
       transport: Transport,
       *,
       proxy_settings: Optional[ProxySettings] = None,
       rp_dir: Optional[Union[str, Path]] = None,
   ) -> None:
       self._transport = transport
       if proxy_settings:
           self._config = proxy_settings.to_proxy_config()
       else:
           from ..llm.proxy import load_proxy_settings
           settings = load_proxy_settings(start_path=str(rp_dir) if rp_dir else None)
           self._config = settings.to_proxy_config()
   ```

4. Update imports
5. Update tests to use ProxySettings

**Backward Compatibility:**
- Old: `ProxyTransport(transport, rp_dir="/path")`
- Still works! Calls `load_proxy_settings()` internally

**New Recommended:**
- `ProxyTransport(transport, proxy_settings=settings)`

---

### Phase 3: Refactor ClaudeAPIClient ⏱️ 2-3 hours
**Priority: HIGH** - Critical for consistency

#### Current Implementation

**Uses anthropic SDK:**
```python
self._client = anthropic.Anthropic(**client_kwargs)
response = self._client.messages.create(**params)
```

#### Challenge

The anthropic SDK has its own HTTP layer. We have 3 options:

1. **Extract HTTP layer** - Replace SDK's HTTP calls with Transport
2. **Wrapper Transport** - Create AnthropicTransport that wraps SDK
3. **Direct HTTP** - Bypass SDK, use Transport directly with Anthropic API

#### Recommended: Option 3 (Direct HTTP with Transport)

**Reasons:**
- OpenRouterClient already demonstrates this pattern successfully
- Full control over requests/responses
- Consistent error handling across all clients
- No SDK version coupling
- Simpler to test

**Trade-offs:**
- Must reimplement request/response formatting
- Must handle API versioning manually
- More code to maintain

#### Implementation Steps

1. **Add transport parameter to `__init__`**
   ```python
   def __init__(
       self,
       *,
       settings: Optional[ClaudeAPISettings] = None,
       proxy_settings: Optional[ProxySettings] = None,
       transport: Optional[Transport] = None,
       logger: Optional[LoggingService] = None,
   ) -> None:
       # Build transport stack
       base_transport = transport or RequestsTransport()
       if proxy_settings and proxy_settings.use_proxy:
           proxy_config = proxy_settings.to_proxy_config()
           base_transport = ProxyTransport(base_transport, proxy_config=proxy_config)
       if logger:
           base_transport = LoggingTransport(base_transport, logger, name="anthropic")
       self._transport = base_transport
   ```

2. **Update send_message() to use transport.post()**
   ```python
   def send_message(self, user_message: str, **kwargs) -> LLMResponse:
       # Build request payload (same as before)
       payload = self._build_request_payload(user_message, **kwargs)

       # Determine endpoint
       base_url = self._settings.base_url or "https://api.anthropic.com"
       endpoint = f"{base_url}/v1/messages"

       # Build headers
       headers = {
           "anthropic-version": "2023-06-01",
           "content-type": "application/json",
       }
       if self._settings.api_key:
           headers["x-api-key"] = self._settings.api_key
       if self._settings.auth_token:
           headers["authorization"] = f"Bearer {self._settings.auth_token}"

       # Make request
       try:
           response = self._transport.post(
               TransportRequest(
                   endpoint=endpoint,
                   payload=payload,
                   headers=headers,
                   timeout_seconds=kwargs.get("timeout", 120),
               )
           )
       except TransportError as exc:
           raise LLMError(f"Anthropic request failed: {exc}") from exc

       # Handle HTTP errors
       self._handle_http_errors(response)

       # Parse response
       body = response.body
       if not isinstance(body, dict):
           raise LLMError("Anthropic returned unexpected response format")

       return self._parse_response(body)
   ```

3. **Add HTTP error handling** (pattern from OpenRouterClient)
   ```python
   def _handle_http_errors(self, response: TransportResponse) -> None:
       status = response.status_code
       if status == 401:
           raise LLMAuthError("Anthropic rejected credentials (401)")
       if status == 429:
           raise LLMRateLimitError("Anthropic rate limit exceeded (429)")
       if status >= 500:
           raise LLMError(f"Anthropic service error ({status})")
       if status >= 400:
           detail = self._extract_error_detail(response)
           raise LLMError(f"Anthropic error ({status}): {detail}")
   ```

4. **Remove anthropic SDK dependency** (optional - could keep for reference)

5. **Update tests** to use FakeTransport

#### Files to Modify
- `src/infrastructure/llm/claude_api_client.py`

---

### Phase 4: Refactor OpenAIClient ⏱️ 2-3 hours
**Priority: HIGH** - Similar to Claude

#### Current Implementation

**Uses openai SDK:**
```python
self._client = OpenAI(**client_kwargs)
response = self._client.responses.create(**params)
# OR
response = self._client.chat.completions.create(**params)
```

#### Challenge

OpenAI has two different endpoints:
1. `/v1/responses` - For reasoning models (gpt-4.1, o4, o3)
2. `/v1/chat/completions` - For chat models (gpt-4o-mini, gpt-3.5)

#### Recommended: Same as Claude (Direct HTTP with Transport)

#### Implementation Steps

1. **Add transport parameter to `__init__`** (same pattern as Claude)

2. **Update `_send_via_responses()` to use transport.post()**
   ```python
   def _send_via_responses(self, model: str, messages: List[Dict], ...) -> LLMResponse:
       base_url = self._settings.api_base or "https://api.openai.com"
       endpoint = f"{base_url}/v1/responses"

       headers = {
           "Authorization": f"Bearer {self._settings.api_key}",
           "Content-Type": "application/json",
       }
       if self._settings.organization:
           headers["OpenAI-Organization"] = self._settings.organization

       payload = {
           "model": model,
           "input": self._convert_to_responses_input(messages),
           "temperature": temperature,
           "max_output_tokens": max_tokens,
           # ... other params
       }

       try:
           response = self._transport.post(
               TransportRequest(endpoint=endpoint, payload=payload, headers=headers, timeout_seconds=timeout)
           )
       except TransportError as exc:
           raise LLMError(f"OpenAI request failed: {exc}") from exc

       self._handle_http_errors(response)
       return self._parse_responses_response(response.body)
   ```

3. **Update `_send_via_chat_completions()` similarly**

4. **Add HTTP error handling**
   ```python
   def _handle_http_errors(self, response: TransportResponse) -> None:
       status = response.status_code
       if status == 401:
           raise LLMAuthError("OpenAI rejected API key (401)")
       if status == 429:
           raise LLMRateLimitError("OpenAI rate limit exceeded (429)")
       if status >= 500:
           raise LLMError(f"OpenAI service error ({status})")
       if status >= 400:
           detail = self._extract_error_detail(response)
           raise LLMError(f"OpenAI error ({status}): {detail}")
   ```

5. **Remove openai SDK dependency** (optional)

#### Files to Modify
- `src/infrastructure/llm/openai_client.py`

---

### Phase 5: ClaudeSDKClient Evaluation ⏱️ 30 mins
**Priority: LOW** - Document decision

#### Analysis

**ClaudeSDKClient** uses legacy `src.clients.claude_sdk`:
- Wraps Node.js process (not HTTP)
- Uses IPC/subprocess communication
- Has its own transport mechanism (stdin/stdout)

#### Decision: SKIP

**Reasons:**
1. Not HTTP-based (uses IPC)
2. Transport pattern doesn't apply to subprocess communication
3. Working correctly as-is
4. Would require complete rewrite for minimal benefit

#### Action
Document in `TRANSPORT_SYSTEM.md`:

> **Note on ClaudeSDKClient:** The ClaudeSDKClient uses a legacy Node.js bridge
> for streaming support and does not use the Transport abstraction. This is an
> acceptable exception as it communicates via IPC (subprocess) rather than HTTP.
> The Transport pattern is specifically designed for HTTP-based communication.

---

### Phase 6: Documentation ⏱️ 1-2 hours
**Priority: MEDIUM** - Guides future development

#### File: `docs/TRANSPORT_SYSTEM.md`

**Table of Contents:**
1. Overview
2. Architecture
3. Using Transports
4. Creating Custom Transports
5. Testing with FakeTransport
6. Client Integration
7. Best Practices
8. API Reference

**Content Outline:**

#### 1. Overview
- What is the Transport abstraction?
- Why use it? (testability, composability, consistency)
- Design goals

#### 2. Architecture
```
┌─────────────────────────────────────┐
│   LLM Clients                        │
│   (ClaudeAPIClient, OpenAIClient)    │
└──────────────┬──────────────────────┘
               │ uses
               ↓
┌─────────────────────────────────────┐
│   Transport Protocol                 │
│   - post(request) → response         │
│   - get(request) → response          │
└──────────────┬──────────────────────┘
               │ implemented by
               ↓
┌─────────────────────────────────────┐
│   Transport Implementations          │
│   - RequestsTransport (HTTP)         │
│   - LoggingTransport (decorator)     │
│   - ProxyTransport (decorator)       │
│   - FakeTransport (testing)          │
└─────────────────────────────────────┘
```

#### 3. Using Transports

**Basic Usage:**
```python
from infrastructure.transports import RequestsTransport
from shared.interfaces import TransportRequest

transport = RequestsTransport()
response = transport.post(
    TransportRequest(
        endpoint="https://api.example.com/v1/chat",
        payload={"message": "Hello"},
        headers={"Authorization": "Bearer token"},
        timeout_seconds=30,
    )
)
print(response.status_code, response.body)
```

**With Logging:**
```python
from infrastructure.transports import RequestsTransport, LoggingTransport
from shared.logging import get_logger

logger = get_logger(__name__)
base = RequestsTransport()
transport = LoggingTransport(base, logger, name="api_client")
```

**With Proxy:**
```python
from infrastructure.transports import RequestsTransport, ProxyTransport
from infrastructure.llm.proxy import load_proxy_settings

proxy_settings = load_proxy_settings()
base = RequestsTransport()
transport = ProxyTransport(base, proxy_settings=proxy_settings)
```

**Composition (Proxy + Logging):**
```python
base = RequestsTransport()
with_proxy = ProxyTransport(base, proxy_settings=settings)
with_logging = LoggingTransport(with_proxy, logger, name="claude")

client = ClaudeAPIClient(transport=with_logging)
```

#### 4. Creating Custom Transports

```python
from shared.interfaces import Transport, TransportRequest, TransportResponse

class RetryTransport(Transport):
    """Retries failed requests automatically."""

    def __init__(self, transport: Transport, max_retries: int = 3):
        self._transport = transport
        self._max_retries = max_retries

    def post(self, request: TransportRequest) -> TransportResponse:
        for attempt in range(self._max_retries):
            try:
                return self._transport.post(request)
            except TransportError as e:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def get(self, request: TransportRequest) -> TransportResponse:
        # Similar retry logic
        ...
```

#### 5. Testing with FakeTransport

```python
from infrastructure.transports import FakeTransport

def test_client_handles_auth_error():
    fake = FakeTransport()
    fake.add_response(status_code=401, body={"error": "Unauthorized"})

    client = MyClient(transport=fake)

    with pytest.raises(LLMAuthError):
        client.send_message("test")

    # Verify request
    assert fake.last_request.endpoint == expected_url
    assert "Authorization" in fake.last_request.headers
```

#### 6. Client Integration

**Error Mapping Pattern:**
```python
def _handle_http_errors(self, response: TransportResponse) -> None:
    """Map HTTP status codes to domain exceptions."""
    status = response.status_code
    if status == 401:
        raise LLMAuthError("Authentication failed")
    if status == 429:
        raise LLMRateLimitError("Rate limit exceeded")
    if status >= 500:
        raise LLMError(f"Service error ({status})")
    if status >= 400:
        detail = self._extract_error_detail(response)
        raise LLMError(f"API error ({status}): {detail}")
```

**Full Client Example:**
```python
class MyLLMClient:
    def __init__(
        self,
        *,
        api_key: str,
        transport: Optional[Transport] = None,
        logger: Optional[LoggingService] = None,
    ):
        base = transport or RequestsTransport()
        if logger:
            base = LoggingTransport(base, logger, name="myllm")
        self._transport = base
        self._api_key = api_key

    def send_message(self, message: str) -> LLMResponse:
        try:
            response = self._transport.post(
                TransportRequest(
                    endpoint="https://api.myllm.com/v1/chat",
                    payload={"message": message},
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            )
        except TransportError as exc:
            raise LLMError(f"Request failed: {exc}") from exc

        self._handle_http_errors(response)
        return self._parse_response(response.body)
```

#### 7. Best Practices

1. **Always use Transport composition** - Don't hardcode RequestsTransport
2. **Inject transport via constructor** - Enables testing
3. **Standardize error handling** - Use consistent HTTP → domain mapping
4. **Log at transport layer** - Use LoggingTransport, not client logging
5. **Test with FakeTransport** - Don't mock requests.Session
6. **Handle TransportError** - Wrap in domain exceptions
7. **Set reasonable timeouts** - Default to 60-120 seconds
8. **Use ProxySettings** - Don't reinvent proxy config

#### 8. API Reference

**Transport Protocol:**
- `post(request: TransportRequest) -> TransportResponse`
- `get(request: TransportRequest) -> TransportResponse`

**TransportRequest:**
- `endpoint: str` - Full URL
- `payload: Optional[Mapping[str, Any]]` - JSON body
- `headers: Optional[Mapping[str, str]]` - HTTP headers
- `timeout_seconds: Optional[float]` - Request timeout

**TransportResponse:**
- `status_code: int` - HTTP status
- `body: Any` - Parsed JSON or text
- `headers: Optional[Mapping[str, str]]` - Response headers

**TransportError:**
- Base exception for transport failures
- Wraps network errors, timeouts, etc.

---

## Success Criteria

- [ ] All 3 transport implementations have comprehensive tests (~65 tests total)
- [ ] FakeTransport created for contract testing
- [ ] ClaudeAPIClient refactored to use Transport
- [ ] OpenAIClient refactored to use Transport
- [ ] Proxy configuration consolidated (ProxySettings dataclass)
- [ ] All clients map HTTP status codes consistently
- [ ] ClaudeSDKClient exception documented
- [ ] TRANSPORT_SYSTEM.md complete with examples
- [ ] All tests passing
- [ ] No breaking changes to existing client APIs

---

## Files Summary

### New Files (7)
1. `tests/infrastructure/transports/__init__.py`
2. `tests/infrastructure/transports/test_requests_transport.py` (~25 tests)
3. `tests/infrastructure/transports/test_logging_transport.py` (~15 tests)
4. `tests/infrastructure/transports/test_proxy_transport.py` (~20 tests)
5. `tests/infrastructure/transports/test_fake_transport.py` (~5 tests)
6. `src/infrastructure/transports/fake_transport.py` (~100 lines)
7. `docs/TRANSPORT_SYSTEM.md` (~500 lines)

### Modified Files (3)
1. `src/infrastructure/transports/proxy_transport.py` (consolidate with proxy.py)
2. `src/infrastructure/llm/claude_api_client.py` (use Transport)
3. `src/infrastructure/llm/openai_client.py` (use Transport)

### Total
- **New:** 7 files (~65 tests + 600 lines)
- **Modified:** 3 files
- **Tests:** ~65 total

---

## Timeline

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| 1 | Transport Tests | 2-3 hours |
| 2 | Proxy Consolidation | 1 hour |
| 3 | Claude Refactor | 2-3 hours |
| 4 | OpenAI Refactor | 2-3 hours |
| 5 | SDK Evaluation | 30 mins |
| 6 | Documentation | 1-2 hours |
| **Total** | | **9-13 hours** |

---

## Next Steps

1. Start with Phase 1 (Transport Tests)
2. Create FakeTransport for testing
3. Proceed through phases sequentially
4. Update this document as work progresses
5. Mark completion criteria as tests pass

---

*Last updated: 2025-10-20*
*Status: Planning Complete*
