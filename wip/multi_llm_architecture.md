# Multi-LLM Support Architecture Notes

## Goals
- Introduce a provider-agnostic conversation layer that both Anthropic and OpenAI clients can share.
- Allow the bridge (`src/tui_bridge.py`) to select the correct client based on config (`primary_llm`) without duplicating automation and logging flows.
- Extend configuration + TUI settings to capture provider choice and the necessary credentials for Anthropic and OpenAI.

## Current-State Findings
- `ConversationManager` lives inside `src/clients/claude_api.py` and is imported directly by the bridge. It is responsible for persisting history to `<RP>/state/conversation_history.json`.
- `tui_bridge.py` currently toggles between Claude SDK and Claude API via `use_api_mode`. There is no hook for additional providers; Anthropic-specific logging/messages are scattered through the loop.
- Configuration helpers live in `src/clients/claude_api.py` and `src/clients/proxy_client.py`. They read from env, `config/config.json`, and `.env`.
- Settings UI (`src/rp_client_tui.py`) exposes Anthropic-only credential fields plus some OpenRouter hooks.

## Proposed Refactors
1. **Shared Conversation Module**
   - Move `ConversationManager` to `src/clients/conversation_manager.py`.
   - Preserve existing JSON structure (`[{role, content}]`) so historical transcripts remain compatible.
   - Expose minimal API: `add_user_message`, `add_assistant_message`, `get_history`, `clear_history`, plus a `StatePaths` helper for future providers if needed.

2. **Provider Registry**
   - Create `src/clients/providers.py` (or update `__init__.py`) with a `get_llm_client(provider_id, config)` factory.
   - Provider IDs: `anthropic_sdk`, `anthropic_api`, `openai_api` (matching doc).
   - Factory should load provider-specific settings and return a `(client, conversation_manager)` tuple plus metadata (e.g., supports_streaming).

3. **OpenAI Client Skeleton**
   - Lives in `src/clients/openai_api.py`.
   - Uses `openai` Python SDK (>=1.0).
   - Mirrors `ClaudeAPIClient.send_message(...)` signature but:
     - Converts cached context into a prefixed system message.
     - Maps conversation history into OpenAI chat format.
     - Handles optional proxy (`ProxyClient.post`) wrapper.
   - Returns dict with `content`, `usage`, `raw_response`, optionally `thinking=None`.

4. **Configuration Surface**
   - `config/config.json.template` gains `primary_llm` plus OpenAI credential slots.
   - `load_api_settings` remains for Anthropic; add `load_openai_settings` (new file or module) with similar env/config lookup order: env vars (`OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_API_BASE`), config file, `.env`.
   - Provide graceful fallbacks when legacy configs omit the new keys.

5. **Bridge Integration**
   - Replace `use_api_mode` flag with a provider lookup.
   - On startup: merge config ➜ resolve `primary_llm` ➜ instantiate via registry.
   - Shared logging: describe provider/model, mention missing features (no caching for OpenAI).
   - When provider lacks streaming, disable SDK-specific behavior (progress logs, autop flush).

6. **TUI Adjustments (future steps)**
   - Add provider selection widget and OpenAI fields.
   - Ensure save/load includes new keys in config.

## Open Questions / TODOs
- Decide whether OpenAI should reuse `thinking_mode` settings (probably ignore and warn).
- Confirm how automation hooks reference Claude-specific features to avoid regressions.
- Determine how to expose proxy routing uniformly (Anthropic uses custom headers; OpenAI requires `Authorization`).
