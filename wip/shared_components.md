# Shared vs Provider-Specific Responsibilities

## Claude API (`src/clients/claude_api.py`)
- **Shared candidates**
  - `ConversationManager`: file-backed history store (moved to wip prototype).
  - Token usage formatting (`format_cache_stats`) partly generic except for cache fields.
  - Config loading pattern (`load_api_settings`) suitable template for OpenAI loader.

- **Claude-specific**
  - Anthropic `thinking` budget presets (`THINKING_MODES`).
  - Cache-control payload structure for `system` messages with `cache_control` metadata.
  - Anthropic client initialization (`anthropic.Anthropic`).
  - Error handling relying on Anthropic exceptions.

## Claude SDK (`src/clients/claude_sdk.py`)
- **Shared candidates**
  - Cache stats dataclass, streaming interface, general lifecycle methods.

- **Claude-specific**
  - Node bridge command protocol, SDK-specific commands.
  - Thinking mode translation inside `_send_command` / `query`.

## Bridge (`src/tui_bridge.py`)
- **Shared candidates**
  - RP folder + state directory resolution.
  - Flag monitoring, automation integration.
  - Logging scaffolding that reports provider, thinking mode, etc.

- **Anthropic-specific pain points**
  - Binary switch `use_api_mode` assumes only SDK/API options.
  - Hard-coded prompt caching messaging.
  - Imports tied directly to Claude clients.

## Config / Proxy Helpers
- `src/clients/proxy_client.py` already abstracts proxy detection.
- Need provider-neutral helpers for API base URLs and credential selection.

## Next Extraction Targets
1. Create `wip/clients/base.py` with a `LLMClient` protocol + usage dataclass.
2. Introduce `wip/clients/config.py` capturing shared config resolution (env/config/.env precedence) so both Anthropic and OpenAI loaders reuse logic.
3. Add `wip/clients/registry.py` to map provider IDs to constructors; this will replace bridge's `use_api_mode` flag.
