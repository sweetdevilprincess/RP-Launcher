# OpenAI Client Implementation Notes

## Features
- Implements the shared `LLMClient` protocol via `OpenAIChatClient`.
- Uses OpenAI Responses API for unified handling of GPT-4.1/GPT-4o family models.
- Pulls credentials from env/config/.env using `config_utils.merge_config_sources`.
- Honors proxy configuration by reusing `load_proxy_config` and attaching `X-Proxy-Authorization` header when enabled.
- Normalizes output + usage into `LLMResponse` / `UsageStats` objects and surfaces provider capabilities (no streaming/prompt caching).
- Maps OpenAI authentication and rate-limit errors to shared `LLMAuthError` / `LLMRateLimitError` exceptions.

## TODO before promoting to `src/clients`
1. Add unit tests with mocked `OpenAI` client covering success, auth failure, rate limit, and generic API errors.
2. Confirm Responses API compatibility with legacy models (`gpt-3.5`, `gpt-4o`); add fallback to Chat Completions if necessary.
3. Decide how to handle provider-specific parameters (`response_format`, tool calls) and expose them via kwargs.
4. Wire into provider registry + bridge once Claude clients adopt `LLMResponse` return type.
5. Update documentation to explain the lack of prompt caching/thinking modes in OpenAI mode.
