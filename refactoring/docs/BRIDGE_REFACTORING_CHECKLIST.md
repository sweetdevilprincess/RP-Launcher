# Bridge Service Refactoring Checklist

## Overview
Refactor `bridge_service.py` (1027 LOC) by extracting 21 message handler methods into separate, organized handler modules while preserving the public API.

**Estimated Time**: 3-4 hours total

---

## Pre-Refactoring Analysis ✓

- [x] Identified external dependencies (launch.py only)
- [x] Confirmed public API to preserve (\_\_init\_\_, start, run, stop)
- [x] Verified no existing unit tests (0% coverage)
- [x] Catalogued 21 handler methods across 9 categories
- [x] Confirmed zero breaking changes to external code

---

## Phase 1: Handler Infrastructure (30 min)

### Step 1: Create Directory Structure
- [ ] Create `src/presentation/bridge/handlers/` directory
- [ ] Verify directory created successfully

### Step 2: Create Base Handler
- [ ] Create `handlers/base.py`
- [ ] Implement `BaseHandler` abstract class with:
  - [ ] `__init__(self, bridge: BridgeService)` constructor
  - [ ] `handle(self, request: IPCRequest) -> str` abstract method
  - [ ] Store bridge reference as `self.bridge`
- [ ] Add docstrings explaining handler pattern
- [ ] Test: Import `BaseHandler` successfully

### Step 3: Create Handler Registry
- [ ] Create `handlers/__init__.py`
- [ ] Define `HANDLER_REGISTRY` dict mapping `IPCMessageType` → handler class
- [ ] Import all handler classes (will be added incrementally)
- [ ] Export `HANDLER_REGISTRY` in `__all__`
- [ ] Add comprehensive module docstring
- [ ] Test: Import registry successfully

---

## Phase 2: Extract Handlers (2 hours)

### Handler 4: Entity Handler (~100 LOC)
- [ ] Create `handlers/entity_handler.py`
- [ ] Create `EntityHandler(BaseHandler)` class
- [ ] Extract `_handle_get_entities()` → `handle_get_entities()`
- [ ] Extract `_handle_create_entity()` → `handle_create_entity()`
- [ ] Extract `_handle_update_entity()` → `handle_update_entity()`
- [ ] Extract `_handle_delete_entity()` → `handle_delete_entity()`
- [ ] Implement `handle()` method routing to sub-handlers
- [ ] Update handlers to access `self.bridge.entity_service`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_ENTITIES: EntityHandler`
  - [ ] `IPCMessageType.CREATE_ENTITY: EntityHandler`
  - [ ] `IPCMessageType.UPDATE_ENTITY: EntityHandler`
  - [ ] `IPCMessageType.DELETE_ENTITY: EntityHandler`
- [ ] Test: TUI can load entities

### Handler 5: Branch Handler (~80 LOC)
- [ ] Create `handlers/branch_handler.py`
- [ ] Create `BranchHandler(BaseHandler)` class
- [ ] Extract `_handle_get_branches()` → `handle_get_branches()`
- [ ] Extract `_handle_create_branch()` → `handle_create_branch()`
- [ ] Extract `_handle_switch_branch()` → `handle_switch_branch()`
- [ ] Extract `_handle_compare_branches()` → `handle_compare_branches()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.session_state_service`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_BRANCHES: BranchHandler`
  - [ ] `IPCMessageType.CREATE_BRANCH: BranchHandler`
  - [ ] `IPCMessageType.SWITCH_BRANCH: BranchHandler`
  - [ ] `IPCMessageType.COMPARE_BRANCHES: BranchHandler`
- [ ] Test: TUI branches page loads

### Handler 6: Settings Handler (~70 LOC)
- [ ] Create `handlers/settings_handler.py`
- [ ] Create `SettingsHandler(BaseHandler)` class
- [ ] Extract `_handle_get_settings()` → `handle_get_settings()`
- [ ] Extract `_handle_update_settings()` → `handle_update_settings()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.config_loader`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_SETTINGS: SettingsHandler`
  - [ ] `IPCMessageType.UPDATE_SETTINGS: SettingsHandler`
- [ ] Test: TUI settings page loads

### Handler 7: Module Handler (~60 LOC)
- [ ] Create `handlers/module_handler.py`
- [ ] Create `ModuleHandler(BaseHandler)` class
- [ ] Extract `_handle_get_modules()` → `handle_get_modules()`
- [ ] Extract `_handle_toggle_module()` → `handle_toggle_module()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.config_loader`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_MODULES: ModuleHandler`
  - [ ] `IPCMessageType.TOGGLE_MODULE: ModuleHandler`
- [ ] Test: TUI modules page loads and toggles work

### Handler 8: Message Handler (~130 LOC)
- [ ] Create `handlers/message_handler.py`
- [ ] Create `MessageHandler(BaseHandler)` class
- [ ] Extract `_handle_send_message()` → `handle_send_message()` (119 LOC)
- [ ] Extract `_handle_get_state()` → `handle_get_state()` (11 LOC)
- [ ] Implement `handle()` method routing
- [ ] Preserve streaming response logic
- [ ] Update handlers to access `self.bridge.llm_client`, `automation_service`, `wip_executor`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.SEND_MESSAGE: MessageHandler`
  - [ ] `IPCMessageType.GET_STATE: MessageHandler`
- [ ] Test: TUI can send messages and receive responses

### Handler 9: Provider Handler (~35 LOC)
- [ ] Create `handlers/provider_handler.py`
- [ ] Create `ProviderHandler(BaseHandler)` class
- [ ] Extract `_handle_get_providers()` → `handle_get_providers()`
- [ ] Extract `_handle_set_provider()` → `handle_set_provider()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.llm_client`, `current_provider`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_PROVIDERS: ProviderHandler`
  - [ ] `IPCMessageType.SET_PROVIDER: ProviderHandler`
- [ ] Test: TUI can list and switch LLM providers

### Handler 10: Trigger Handler (~55 LOC)
- [ ] Create `handlers/trigger_handler.py`
- [ ] Create `TriggerHandler(BaseHandler)` class
- [ ] Extract `_handle_get_triggers()` → `handle_get_triggers()`
- [ ] Extract `_handle_set_trigger()` → `handle_set_trigger()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.automation_service`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_TRIGGERS: TriggerHandler`
  - [ ] `IPCMessageType.SET_TRIGGER: TriggerHandler`
- [ ] Test: TUI can view and update triggers

### Handler 11: Template Handler (~80 LOC)
- [ ] Create `handlers/template_handler.py`
- [ ] Create `TemplateHandler(BaseHandler)` class
- [ ] Extract `_handle_get_templates()` → `handle_get_templates()`
- [ ] Extract `_handle_set_template()` → `handle_set_template()`
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.automation_service`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.GET_TEMPLATES: TemplateHandler`
  - [ ] `IPCMessageType.SET_TEMPLATE: TemplateHandler`
- [ ] Test: TUI can view and update templates

### Handler 12: System Handler (~110 LOC)
- [ ] Create `handlers/system_handler.py`
- [ ] Create `SystemHandler(BaseHandler)` class
- [ ] Extract `_handle_test_mode()` → `handle_test_mode()` (102 LOC)
- [ ] Extract `_handle_ping()` → `handle_ping()` (4 LOC)
- [ ] Extract `_handle_shutdown()` → `handle_shutdown()` (4 LOC)
- [ ] Implement `handle()` method routing
- [ ] Update handlers to access `self.bridge.testing_mode`, `llm_client`
- [ ] Add comprehensive docstrings
- [ ] Register in `HANDLER_REGISTRY`:
  - [ ] `IPCMessageType.TEST_MODE: SystemHandler`
  - [ ] `IPCMessageType.PING: SystemHandler`
  - [ ] `IPCMessageType.SHUTDOWN: SystemHandler`
- [ ] Test: Ping works, test mode toggle works, shutdown works

---

## Phase 3: Refactor BridgeService (45 min)

### Step 13: Update Request Routing
- [ ] Import `HANDLER_REGISTRY` at top of `bridge_service.py`
- [ ] Replace 50-line if/elif chain in `_handle_request()` with:
  ```python
  request_type = IPCMessageType(request.type)
  handler_class = HANDLER_REGISTRY.get(request_type)

  if handler_class:
      handler = handler_class(self)
      return handler.handle(request)
  else:
      return create_error_response(...)
  ```
- [ ] Test: TUI starts without errors

### Step 14: Remove Extracted Handler Methods
- [ ] Delete `_handle_get_entities()`
- [ ] Delete `_handle_create_entity()`
- [ ] Delete `_handle_update_entity()`
- [ ] Delete `_handle_delete_entity()`
- [ ] Delete `_handle_get_branches()`
- [ ] Delete `_handle_create_branch()`
- [ ] Delete `_handle_switch_branch()`
- [ ] Delete `_handle_compare_branches()`
- [ ] Delete `_handle_get_settings()`
- [ ] Delete `_handle_update_settings()`
- [ ] Delete `_handle_get_modules()`
- [ ] Delete `_handle_toggle_module()`
- [ ] Delete `_handle_send_message()`
- [ ] Delete `_handle_get_state()`
- [ ] Delete `_handle_get_providers()`
- [ ] Delete `_handle_set_provider()`
- [ ] Delete `_handle_get_triggers()`
- [ ] Delete `_handle_set_trigger()`
- [ ] Delete `_handle_get_templates()`
- [ ] Delete `_handle_set_template()`
- [ ] Delete `_handle_test_mode()`
- [ ] Delete `_handle_ping()`
- [ ] Delete `_handle_shutdown()`
- [ ] Verify `bridge_service.py` is now ~300 LOC

### Step 15: Verify Public API Unchanged
- [ ] Verify `__init__(self, rp_dir, host, port)` signature unchanged
- [ ] Verify `start()` method unchanged
- [ ] Verify `run()` method unchanged
- [ ] Verify `stop()` method unchanged
- [ ] Verify all instance variables remain (services, logger, etc.)

---

## Phase 4: Update Imports (15 min)

### Step 16: Update bridge_service.py Imports
- [ ] Add `from .handlers import HANDLER_REGISTRY` at top
- [ ] Verify no other import changes needed
- [ ] Remove any unused imports from deleted handlers

### Step 17: Verify __init__.py Unchanged
- [ ] Confirm `__init__.py` still only exports `BridgeService`
- [ ] No changes to `__all__`
- [ ] Test: `from src.presentation.bridge import BridgeService` works

---

## Phase 5: Testing & Validation (30 min)

### Step 18: Automated Tests
- [ ] Run TUI startup test: `python launch.py test_rp`
- [ ] Verify bridge starts without errors
- [ ] Verify TUI connects successfully
- [ ] Check for any Python exceptions in output

### Step 19: Manual TUI Testing
- [ ] Test F1: Chat - Send message, receive response
- [ ] Test F2: Settings - Load settings, toggle SDK switch
- [ ] Test F3: Modules - View modules, toggle module on/off
- [ ] Test F4: Branches - View branch tree, branch details
- [ ] Test F5: Entities - View entity list, select entity
- [ ] Test Providers - List providers, switch provider
- [ ] Test Triggers - View triggers (if implemented)
- [ ] Test Templates - View templates (if implemented)
- [ ] Test Ping - Verify connection status
- [ ] Test Test Mode - Toggle test mode on/off

### Step 20: Error Handling Verification
- [ ] Test invalid message type → proper error response
- [ ] Test missing required data → proper error response
- [ ] Test handler exception → proper error response
- [ ] Check error messages are user-friendly

### Step 21: launch.py Compatibility
- [ ] Test `python launch.py test_rp` (both Bridge + TUI)
- [ ] Test `python launch.py test_rp --bridge-only`
- [ ] Test `python launch.py test_rp --tui-only`
- [ ] Verify no import errors
- [ ] Verify bridge process starts/stops cleanly

---

## Post-Refactoring Documentation

### Step 22: Code Documentation
- [ ] Add module docstrings to all handler files
- [ ] Ensure all handler methods have docstrings
- [ ] Document handler pattern in `handlers/README.md`
- [ ] Update `bridge_service.py` docstring to mention handler delegation

### Step 23: Update Architecture Docs
- [ ] Create `docs/architecture/BRIDGE_ARCHITECTURE.md`
- [ ] Document handler pattern and registry
- [ ] Add sequence diagram for request flow
- [ ] List all handler classes and their responsibilities
- [ ] Link to IPC message type documentation

---

## Success Criteria Checklist

- [ ] **Zero breaking changes**: launch.py works unchanged
- [ ] **Line count reduction**: bridge_service.py reduced from 1027 → ~300 LOC
- [ ] **Handler organization**: 9 handler files created (~50-130 LOC each)
- [ ] **All 21 handlers migrated**: Every `_handle_*` method extracted
- [ ] **Registry pattern implemented**: Clean message type → handler routing
- [ ] **Public API preserved**: Constructor and public methods unchanged
- [ ] **TUI fully functional**: All pages and features work
- [ ] **No test failures**: All existing integration tests pass
- [ ] **Clean imports**: No circular dependencies
- [ ] **Documentation complete**: Handler pattern documented

---

## Rollback Plan

If issues arise:
1. Git stash or commit current work
2. Git revert to last working commit
3. Review error messages and logs
4. Fix issues incrementally
5. Re-test before continuing

---

## Notes & Observations

### During Implementation:
- [Add notes here as you work]

### Issues Encountered:
- [Document any problems and solutions]

### Future Improvements:
- Consider adding unit tests for individual handlers
- Consider extracting handler routing to separate HandlerRouter class
- Consider adding handler middleware for logging/metrics

---

## Completion Sign-off

- [ ] All checklist items completed
- [ ] TUI fully tested and working
- [ ] Code review completed (if applicable)
- [ ] Documentation updated
- [ ] Ready for commit

**Completed by**: _________________
**Date**: _________________
**Commit hash**: _________________
