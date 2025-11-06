# Multi-LLM Support (ChatGPT / Codex Integration)

## Summary
- Extend RP Claude Code so the runtime and tooling can target Anthropic, OpenAI (ChatGPT/Codex-style), and future providers interchangeably.
- Deliver a first-class OpenAI client that matches the existing Claude API contract while reusing shared conversation state, proxy support, and automation hooks.
- Update configuration, UI, and documentation so users can pick their preferred model with minimal friction.

## Background
The current stack assumes Anthropic everywhere:
- `src/tui_bridge.py` switches between Claude SDK (Node bridge) and Claude API mode only.
- `src/clients/claude_api.py` owns both the Anthropic transport and the conversation-history helper.
- Settings forms (`src/rp_client_tui.py`) expose Anthropic and OpenRouter (DeepSeek) fields but cannot configure OpenAI.
- Automation features (entity cards, story arcs, background agents) call DeepSeek via OpenRouter for analysis, but the main conversational loop is still Anthropic-only.

Adding OpenAI support requires a provider abstraction so the same automation pipeline can talk to either service.

## Goals
- [x] Users can select an OpenAI model (e.g., `gpt-4.1`, `gpt-4o`, or Codex successor) as the primary conversation model.
- [x] Prompt automation (cached Tier 1 context, dynamic prompts, proxy prompts) keeps working without code duplication.
- [x] Bridge runtime, session logging, and background tasks remain provider-agnostic.
- [x] Configuration templates, settings UI, and CLI guidance cover OpenAI setup.
- [x] Documentation captures setup, caveats, and testing guidance for multi-provider deployments.

## Non-Goals
- Streaming parity with the Claude SDK bridge (unless we spin up a dedicated OpenAI streaming bridge later).
- Replacing DeepSeek/OpenRouter for automation agents; they can stay independent but should allow future provider swaps.
- Implementing per-RP provider overrides beyond what’s already supported for API keys (global first, local override optional).

## Implementation Plan

### 1. Shared Conversation Layer
- Extract `ConversationManager` from `src/clients/claude_api.py:229` into `src/clients/conversation_manager.py`.
- Update both Anthropic and OpenAI clients to import this shared helper.
- Ensure serialization format stays stable so existing conversation history files continue working.

### 2. OpenAI Client Module
- Create `src/clients/openai_api.py` with a public `OpenAIChatClient` class that mirrors `ClaudeAPIClient.send_message`.
  - Use the official `openai` Python SDK (>=1.0).
  - Support `model`, `max_tokens`, `temperature`, optional `top_p`, `frequency_penalty`, etc.
  - Accept cached context + user message just like Claude: combine into a pseudo "system" prompt + user message array (OpenAI doesn’t expose prompt caching, so warn/adjust).
  - Call `ProxyClient.post` when proxy routing is enabled (header: `Authorization: Bearer <OPENAI_API_KEY>`).
  - Return a dict with `content`, `usage`, and raw response for parity; map OpenAI usage fields into the existing shape.
- Add basic error handling (rate limiting, authentication) and convert them into friendly error messages for the bridge.
- Add convenience loader similar to `load_api_settings` (`load_openai_settings`) honoring env vars, global config, and `.env` overrides.

### 3. Client Registry Updates
- Update `src/clients/__init__.py` to expose the OpenAI client.
- Consider a tiny `src/clients/utils.py` for shared helper functions used by both loaders.

### 4. Configuration Schema
- `config/config.json.template`:
  - Add `"primary_llm": "anthropic_sdk"` as default; allow values like `anthropic_sdk`, `anthropic_api`, `openai_api`.
  - Add placeholders for `"openai_api_key"`, `"openai_model"`, `"openai_api_base"`.
- Update live `config/config.json` only if shipping defaults (leave user-specific secrets out of version control).
- Adjust any code that reads config to fall back gracefully when new keys are missing.

### 5. Settings UI (TUI)
- Expand the global settings screen (`src/rp_client_tui.py`) with:
  - Provider selector (radio group or dropdown) bound to `primary_llm`.
  - Input fields for OpenAI key/model/base URL with validation similar to existing keys.
  - Update `save_settings()` to persist new fields, validate provider choice, and notify users when a bridge restart is required.
- Ensure per-RP settings overlays either respect the global provider or document that only the global picker is honored.

### 6. Bridge Orchestration
- Refactor `src/tui_bridge.py`:
  - Read `primary_llm` from merged config (global + RP override).
  - Decide between Claude SDK (`anthropic_sdk`), Claude API (`anthropic_api`), or OpenAI (`openai_api`).
  - Factor shared setup (automation run, proxy prompt injection, background agent queueing) into provider-neutral code paths.
  - Handle provider capability differences (no prompt caching/thinking budget with OpenAI) and guard calls accordingly.

### 7. Automation Hooks
- Audit automation code (`src/automation`) for hard-coded references to Claude thinking budgets.
- Update logging language to refer to “LLM” when provider varies.
- (Optional) Allow future selection of provider for background agents.

### 8. Requirements & Packaging
- Add `openai>=1.0.0` to `requirements.txt`.
- Document that Node bridge remains required for Claude SDK mode but not for OpenAI.

### 9. Testing Strategy
- Unit tests: mock OpenAI responses to verify `OpenAIChatClient.send_message` success + error paths.
- Integration smoke tests: launch TUI in each provider mode to confirm conversation flow, history persistence, proxy routing, and automation triggers.

### 10. Documentation Deliverables
- Update `README.md`, `docs/WIKI_SETUP_GUIDE.md`, `Working Guides/TUI_BRIDGE_DOCUMENTATION.md` with OpenAI setup instructions & troubleshooting.
- Note in `docs/guides/PROMPT_CACHING_GUIDE.md` that caching is Anthropic-only and describe the OpenAI fallback behavior.

## Risks & Mitigations
- **API differences** (thinking budgets, caching): guard features per provider, surface status in UI.
- **Credential handling**: reuse existing config/env loading; avoid logging secrets.
- **Regression risk**: rely on new unit tests + manual provider rotation during QA.

## Open Questions
- Should we ship OpenAI streaming in v1 or wait for a dedicated bridge?
- Do we expose advanced OpenAI parameters (top_p, penalties) in settings now or later?
- What interface do we want for future providers (Google, Cohere)?

## Timeline & Milestones
1. Shared conversation manager + OpenAI client (Week 1).
2. Config/Settings/Bridge refactor (Week 2).
3. Docs, tests, QA (Week 3).
4. Release candidate, polish, feedback.
