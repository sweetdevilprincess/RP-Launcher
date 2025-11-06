# Claude API Client TODOs

## Validation Tasks
- Verify prompt caching behavior with existing RP sessions; ensure cache control metadata matches current production client.
- Exercise thinking mode overrides to confirm new budget mapping returns identical API params.
- Confirm proxy authentication flow (auth token vs API key) with SillyTavern-style proxy in both enabled/disabled states.
- Backfill unit tests mocking `anthropic.Anthropic.messages.create` for success + error paths to validate exception mapping.

## Integration Steps
1. Promote `wip/clients/base.py`, `proxy.py`, `claude_api_client.py`, and `openai_client.py` into `src/clients` once legacy callers are updated.
2. Refactor `src/tui_bridge.py` to use provider registry instead of direct `ClaudeAPIClient` import.
3. Update existing automation hooks to accept `LLMResponse` objects.
4. Remove redundant legacy helpers (`load_api_settings`, `ConversationManager` inside old client) after migration.
