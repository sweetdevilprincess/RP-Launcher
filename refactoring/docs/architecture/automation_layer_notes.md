# Automation Layer Notes

- Contracts (`refactoring/src/automation/contracts`) now host the immutable contexts and results previously under `src/automation/context`.
- `AutomationContext` tracks tiered bundle snapshots (`tier3_loaded_files`, `tiered_bundles`) so downstream services can render filesystem output without reloading disk.
- `AutomationService` wires FileAccessService output into the context, determines story-arc cadence, and surfaces bundle metadata for prompt construction.
- `PromptBuilder` renders tiered bundles, entity highlights, and session summaries into the final prompt (see `tests/test_prompt_builder.py`).
- `AutomationOrchestrator` remains a thin facade over `AutomationService` to preserve the public entry point.
- `automation/factory.py` exposes `build_file_access_service` and `build_automation_service` so downstream callers can wire the new infrastructure without touching legacy modules.
- TODO as migration continues:
  - Flesh out remaining pipeline hooks (time tracking, triggers, agent orchestration specifics).
  - Replace placeholder Protocols with concrete implementations from domain/infrastructure packages.
  - Expand PromptBuilder with narrative template integration and agent strategy context once those modules are ported.
  - Author a dedicated README for the automation layer detailing responsibilities and dependency boundaries.
