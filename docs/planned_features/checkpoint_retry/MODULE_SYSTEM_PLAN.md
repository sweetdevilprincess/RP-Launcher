# Checkpoint & Retry Module – Module System Integration Plan

**Status**: Planning (post-module-system migration)  
**Intent**: Translate the existing checkpoint/retry roadmap into the new modular architecture so the feature ships as a first-class module bundle.

---

## 1. Target Module Topology

| Module | Responsibility | Notes |
|--------|----------------|-------|
| `session_manager` (existing core) | Own JSON session logs and copy/switch helpers | Already wrapped by `SessionManagerModule`; will expose richer APIs to sibling modules. |
| `modules/checkpoints/checkpoint_module.py` | High-level checkpoint/retry orchestration (slash commands, auto-checkpoints, tags) | New module; depends on `session_manager`, `file_manager`, and optionally `background_task_queue`. |
| `modules/ui/checkpoint_panel_module.py` | (Phase 2) Provide UI panes / menu bindings | Optional module loaded by TUI when feature flag enabled. |
| `modules/automation/checkpoint_hooks.py` | (Phase 3) Broadcast session events to automation agents | Optional; subscribe to module event bus for merge/comparison features. |

**Dependency rule**: `checkpoint_module` is the orchestration layer; it never directly touches raw files—everything routes through existing modules (`session_manager`, `file_manager`, `entity_manager` if needed).

---

## 2. Phase 1 (Core Commands) – Module-centric Tasks

1. **SessionManager enhancements (within current module)**
   - Add methods surfaced via module API for: `create_retry`, `create_branch`, `create_checkpoint`, `switch_session`, `list_sessions`, `tag_session`.
   - Ensure all mutations return structured results (`SessionActionResult`) for CLI/TUI printing.
   - Embed agent cache snapshots directly in session JSON (already planned).

2. **Command dispatcher integration**
   - Create `CheckpointModule` class with `handle_command(command, args)` entry point.
   - Register slash commands (`/retry`, `/branch`, `/checkpoint`, `/switch`, `/sessions`, `/tag`) under module metadata so the bridge can auto-discover them.
   - Expose CLI-friendly help strings per command for `/help checkpoints`.

3. **Bridge wiring**
   - Update module loader in `tui_bridge.py` (or its module wrapper) to invoke command modules before falling back to legacy handlers.
   - Ensure module responses feed back through existing IPC writer (JSON payload with `type: "system_message"`).

4. **Auto-checkpoint hooks**
   - Provide `CheckpointModule.on_response_generated(response_number, metadata)` so the bridge can notify the module after each assistant reply.
   - Use module config (`auto_checkpoint_interval`, `auto_branch_tags`) stored via ModuleManager’s config facilities.

5. **State/Config schema**
   - Define default config in `config/modules/checkpoint_module.json` (optional).
   - Add validation schema inside module for user overrides (e.g., enable auto-checkpoints, maximum archive size).

Deliverables: working slash commands, session copy logic via module API, checkpoint metadata persisted in `state/sessions/**`.

---

## 3. Phase 2 (UI Integration)

1. **Module-provided UI components**
   - New `checkpoint_panel_module.py` implementing `RPModule` with `init_ui(app)` hook to register overlays/panels.
   - Provide `SessionListOverlay`, `CheckpointDetailsOverlay`, actions for switching/branching from UI.

2. **Event subscription**
   - Subscribe to ModuleManager event bus (`module_manager.events.subscribe("session:created", ...)`) broadcast by `CheckpointModule`.
   - Update TUI badges/notifications when new checkpoints appear.

3. **Background sync**
   - Optional: register `on_tick()` to refresh UI from session manager state every N seconds or when module emits `session:updated`.

---

## 4. Phase 3 (Advanced Features)

Optional submodules that can be toggled independently:

- **Diff/Merge Module** (`modules/checkpoints/diff_module.py`)
  - Depends on `checkpoint_module`.
  - Provides `/diff`, `/merge` commands and UI overlay.
  - Uses shared utility `utils/diff_utils.py` (to be created).

- **Search Module**
  - Implements tag/keyword search across archived sessions.
  - Adds `/search sessions <query>` command and optional UI filter panel.

- **Analytics Hooks**
  - Emits telemetry (session counts, branch depth) to `automation/status` module for dashboard display.

---

## 5. Data & File Layout

```
RPs/<RP>/sessions/
  session_main.json            # active session
  branches/session_<name>.json # branches
  archived/checkpoint_<name>.json
  manifest.json                # (new) meta-index with tags, timestamps, module version
```

- `CheckpointModule` maintains `manifest.json` for fast listings (cached in memory, invalidated on write).
- Each session JSON embeds:
  ```json
  {
    "session_id": "...",
    "session_type": "branch|checkpoint|main",
    "created": "...",
    "tags": ["romance", "bad_ending"],
    "messages": [...],
    "agents": {...},    // embedded agent outputs
    "module_meta": {
      "checkpoint_module": {"version": "1.0.0", "auto_created": false}
    }
  }
  ```

---

## 6. Module Lifecycle & APIs

```python
class CheckpointModule(RPModule):
    name = "checkpoint_module"
    version = "1.0.0"
    dependencies = ["session_manager", "file_manager", "background_task_queue?"]

    def register(self):
        self.commands = {
            "/retry": self.cmd_retry,
            "/branch": self.cmd_branch,
            "/checkpoint": self.cmd_checkpoint,
            "/switch": self.cmd_switch,
            "/sessions": self.cmd_sessions,
            "/tag": self.cmd_tag,
        }
        self.events.subscribe("bridge:response_generated", self.on_response_generated)
```

- Bridge dispatches commands via `module_manager.execute_command(command, args)`.
- Module returns `ModuleCommandResult(message, attachments, follow_up_actions)` for IPC writer.

---

## 7. Testing Strategy

1. **Unit Tests**
   - `tests/modules/test_checkpoint_module.py` with fixtures for session JSONs.
   - Mock `SessionManagerModule` to validate delegation calls.
2. **Integration Tests**
   - Simulate slash commands via module manager to ensure session files copy correctly.
   - Verify auto-checkpoint triggers when response count matches config.
3. **Regression**
   - Ensure existing automation/background agents still function (no stale references to removed orchestrator code).
   - Confirm module unload/load cycles restore state cleanly (ModuleManager reset).

---

## 8. Migration Checklist (from pre-module plan)

- [ ] Remove old direct references to `SessionManager.copy_session` in `tui_bridge.py`; route through module.
- [ ] Replace legacy command handlers with module registration.
- [ ] Update docs (`PHASE_1_SIMPLE_RETRY.md`, UI docs) to reflect module-based flow.
- [ ] Add module entry to `docs/modules/MODULE_INDEX.md` (create if missing).
- [ ] Document configuration keys in `docs/config/CONFIG_REFERENCE.md`.

---

## 9. Open Questions

- Where should module configs live by default? (Proposed: `config/modules/<module>.json` with overrides in RP `state/module_configs/`.)
- Do we want module hot-reload commands (`/module reload checkpoints`) during development?
- How will module versions be tracked across sessions (embedded metadata vs manifest)?

---

**Next Actions**
1. Extend `SessionManagerModule` API surface per Sect. 2.1.
2. Scaffold `checkpoint_module.py` with command registration + ModuleManager integration tests.
3. Update bridge command dispatcher to invoke modules.
4. Iterate on Phase 1 commands, then schedule UI work when ready.
