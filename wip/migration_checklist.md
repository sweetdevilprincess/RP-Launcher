# Migration Checklist for Shared LLM Components

## Goal
Track the steps required to move WIP shared modules into `src/clients` without breaking existing Claude functionality.

## Steps
1. **Introduce Shared Conversation Manager**
   - Copy `wip/conversation_manager.py` to `src/clients/conversation_manager.py`.
   - Update imports in `src/tui_bridge.py` and `src/clients/claude_api.py` to use the new module.
   - Run existing tests/manual flows to confirm history persistence.

2. **Adopt Base Interfaces**
   - Port `wip/clients/base.py` to `src/clients/base.py`.
   - Update `ClaudeAPIClient.send_message` to return `LLMResponse` instead of raw dict.
   - Wrap SDK client responses similarly (consider adapter for streaming).

3. **Shared Config Utilities**
   - Move `wip/clients/config_utils.py` into `src/clients/utils/config.py` (or similar).
   - Refactor `load_api_settings` to reuse helpers; implement `load_openai_settings` using the same utilities.

4. **Provider Registry**
   - Migrate `wip/clients/registry.py` into `src/clients/providers.py`.
   - Replace bridge flags with registry lookup + provider spec metadata.
   - Ensure SDK/API factories construct clients with merged config/flags.

5. **OpenAI Client Integration**
   - Promote `wip/openai_api_client.py` into `src/clients/openai_api.py` once error handling and proxy routing are complete.
   - Register the OpenAI factory + add configuration entries (TUI + templates).

6. **Testing + Validation**
   - Add unit tests for shared helpers.
   - Smoke test bridge in SDK, Anthropic API, and OpenAI modes.

## Notes
- Keep WIP files until each migration step is fully validated to avoid breaking parallel workstreams.
- Provider registry intentionally uses simple IDs so config + TUI logic can bind via strings.

7. **Bridge Refactor Prototype**
   - Validate `wip/tui_bridge_multi.py` with Anthropic API + SDK + OpenAI clients via manual dry run (flag handling, automation hooks).
   - Compare logging/output versus legacy bridge to ensure user guidance unchanged.
   - Prepare migration plan: replace `src/tui_bridge.py` once provider clients move into `src/clients` and config schema updated.

8. **OpenRouter Client Integration**
   - Wire `openrouter_api` into the registry and bridge once secondary client is validated.
   - Validate config lookup for `OPENROUTER_*` keys and add TUI prompts mirroring existing DeepSeek settings.
   - Add mocked HTTP tests (401/402/429) before promoting to `src/clients/openrouter.py`.
