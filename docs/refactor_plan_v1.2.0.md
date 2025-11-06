# Refactor Plan v1.2.0

This document tracks the major refactor effort to stabilize and modularize the RP Launcher codebase. Tasks are grouped by workstream; complete related subtasks before checking a parent item. Update this checklist as decisions are made or scope changes.

---

## Scope & Objectives
- [ ] Align on final boundaries between automation, domain, and infrastructure layers.
- [ ] Preserve current user-facing behaviour while improving testability and maintainability.
- [ ] Establish baseline test coverage (unit + smoke) for critical flows before invasive changes.
- [ ] Document migration steps for any breaking internal API adjustments.

## Guiding Principles
- [ ] Introduce seams (interfaces/adapters) before moving logic across modules.
- [ ] Prefer incremental migrations behind façade classes to maintain backward compatibility.
- [ ] Keep refactors behaviour-neutral unless bugs are explicitly fixed; note any behaviour changes.
- [ ] Add automated checks (tests, linters, type checks) as safety nets for each workstream.

---

## Workstream A — Architecture & Boundaries
- [ ] Draft updated architecture diagram + module responsibilities in `docs/architecture/README.md`.
- [ ] Enumerate dependency rules (who can import whom) and publish in the architecture doc.
- [ ] Add lightweight Python protocols/interfaces for shared services (logging, config, transport).
- [ ] Audit imports to flag boundary violations and capture follow-up cleanup tasks.

## Workstream B — File & Persistence Layer
- [ ] Snapshot current `FileManager` behaviour via integration tests (counter increments, IPC migration, backups).
- [ ] Extract `JsonStore` helper for JSON read/write/update with merge semantics.
- [ ] Extract `MarkdownStore` for plain/markdown read-write helpers.
- [ ] Add `StatePaths` utility to centralise path derivation (`state/`, `entities/`, backups).
- [ ] Isolate IPC-related logic into `IpcChannel` with schema validation.
- [ ] Wrap `fs_write_queue` calls in a `FileWriteQueue` façade for easier mocking.
- [ ] Refactor `FileManager` to delegate to new helpers while preserving public API.
- [ ] Deprecate unused helpers and update call sites incrementally.

## Workstream C — Entity Domain
- [ ] Capture representative entity cards and DeepSeek responses for fixture-based tests.
- [ ] Move parsing logic into `entity_parser.py` with unit tests for triggers, metadata, sections.
- [ ] Implement `EntityRepository` for filesystem access and index caching.
- [ ] Introduce `EntityService` (orchestrates parser/repository) to provide higher-level operations.
- [ ] Extract DeepSeek preference generation behind `PreferenceGenerator` interface (injectable).
- [ ] Update `EntityManager` façade to rely on the new service stack.

## Workstream D — Automation Pipeline
- [x] Define data contracts (`AutomationContext`, `AgentExecutionResult`) shared between steps.
- [x] Extract `ConfigService`, `CounterService`, `LoggingService`, and `TimeService` utilities.
- [x] Build `AutomationService` coordinating config, counters, file loading, agents, prompt building.
- [x] Refactor `AutomationOrchestratorV2` to become a thin façade instantiating defaults.
- [x] Implement agent execution strategies and `AgentRegistry`.
- [x] Implement full prompt building with modular sections.
- [x] Create service factory for dependency injection (`factory.py`).
- [x] Add smoke test covering end-to-end prompt assembly using a minimal RP directory.
- [x] Document lifecycle hooks (pre-run, post-run) for future module integrations.

## Workstream E — Agent System
- [ ] Catalogue agent inputs/outputs; define dataclasses for shared payloads.
- [ ] Split `AgentCoordinator` into `AgentRegistry`, `AgentRunner`, and `AgentFormatter`.
- [ ] Ensure thread pool execution lives in one place with configurable max workers.
- [ ] Unify immediate/background result serialization via pluggable formatter strategies.
- [ ] Add retry/backoff helper for transient DeepSeek failures; wire into runner.
- [ ] Update agent unit tests/stubs to use new abstractions.

## Workstream F — Trigger & Template Handling
- [x] Extract trigger evaluation into pure functions with deterministic tests.
- [x] Create trigger registry mapping IDs to evaluators and required context.
- [x] Implement keyword, regex, and semantic trigger evaluators with protocols.
- [x] Build trigger coordinator with frequency tracking and pattern loader.
- [x] Refine `PromptTemplateManager` to lazily load/cache templates by type.
- [x] Implement `NarrativeTemplateManager` for genre-specific guidance.
- [x] Integrate trigger system with `FallbackTriggerStrategy`.
- [x] Integrate template system with `PromptBuilder`.
- [x] Document trigger/template extension process for contributors.

## Workstream G — State & Session Management
- [ ] Specify minimal viable contract for `SessionManager` (load/save/list/checkpoints).
- [ ] Implement filesystem-backed session repository with version tagging.
- [ ] Separate archival/branching logic into dedicated helpers or services.
- [ ] Provide migration script for legacy session formats and update docs.
- [ ] Add smoke test covering session creation + load/save cycle.

## Workstream H — Logging & Telemetry
- [ ] Design logging façade with level support and structured event payloads.
- [ ] Replace direct `print`/`log_to_file` calls with façade usage across modules.
- [ ] Ensure façade writes via injected writer (supports tests and alternative sinks).
- [ ] Standardise timing/profiling events for integration with `PerformanceProfiler`.
- [ ] Document logging conventions and log file locations.

## Workstream I - Clients & Transport
- [ ] Build `Transport` interface (`post`, optional `get`) returning typed responses.
- [ ] Implement `RequestsTransport` (prod), `ProxyTransport` (proxy wrapping), and `LoggingTransport` (diagnostics).
- [ ] Refactor `deepseek`, `claude`, and related clients to accept transport instances via DI.
- [ ] Normalise error handling; map HTTP status codes to domain-specific exceptions.
- [ ] Add contract tests using fake transports to verify payloads and error translation.
- [ ] Review proxy configuration loading for redundancy; centralise in one utility.

## Workstream J — Configuration & Defaults
- [ ] Consolidate scattered defaults into `config/defaults.py` with schema comments.
- [ ] Implement deep-merge loader that validates keys/types and reports issues.
- [ ] Surface configuration warnings/errors through logging façade.
- [ ] Provide helper to locate misconfigured directories with actionable messages.
- [ ] Update docs to describe configuration precedence and override process.

## Workstream K — Testing & Tooling
- [ ] Introduce baseline linting (`ruff`) and formatting (`black` or equivalent) configs.
- [ ] Add `mypy` (or `pyright`) configuration; start with strictness on refactored modules.
- [ ] Create fixtures/factories for building temporary RP directories in tests.
- [ ] Expand CI (or local scripts) to run lint, type, and test suites for refactored code.
- [ ] Track test coverage for critical modules; set target thresholds post-refactor.
- [ ] Document how to run the new toolchain locally (`docs/tooling.md`).

## Workstream L — Documentation & Change Management
- [ ] Maintain changelog entries for refactor milestones (non-user-facing but vital).
- [ ] Create contributor guide explaining new module boundaries and conventions.
- [ ] Provide migration notes for anyone extending automation or entity systems.
- [ ] Review README/Working Guides to ensure references match new structure.
- [ ] Present status updates (weekly/bi-weekly) using this checklist to track progress.

---

## Completion Criteria
- [ ] All workstreams have either completed tasks or documented deferrals.
- [ ] Baseline automated tests cover new abstractions; legacy behaviour validated via smoke tests.
- [ ] Documentation updated to reflect new architecture, APIs, and tooling.
- [ ] Team sign-off recorded (engineering + narrative design stakeholders).
