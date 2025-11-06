# TUI-Bridge Integration Plan
**Created:** 2025-10-22
**Status:** Ready for Implementation
**Estimated Effort:** ~370 lines of code across 5 files

---

## Executive Summary

This document outlines the plan to connect the TUI (Text User Interface) to real data sources via the Bridge service. The good news: the architecture is already well-designed for this! We just need to add IPC handlers and remove mock data.

**Key Insight:** We can leverage existing services that auto-discover data from the filesystem and config files, rather than implementing everything manually.

---

## Current Architecture (What's Already Working)

### ✅ Services Already Initialized in Bridge

The Bridge service (`src/presentation/bridge/bridge_service.py`) already has these services initialized:

1. **EntityService** (line 114)
   - Uses `FixtureEntityRepository(rp_dir)`
   - Auto-discovers entities from `rp_dir/entities/` or `rp_dir/characters/`
   - Patterns: `character_*.json`, `location_*.json`, `organization_*.json`, `item_*.json`, `*_memories.json`
   - Methods: `list_characters()`, `list_locations()`, `list_organizations()`, `list_items()`, `list_memory_logs()`

2. **SessionStateService** (line 118)
   - Manages `state/session.json` with timeline/branch tracking
   - Methods: `load_session_state(rp_dir)`, `switch_timeline()`, `get_current_timeline()`

3. **ConfigLoader** (line 87)
   - Loads `config.json` with all module configurations
   - Config structure: `config["modules"]["module_name"]["enabled"]` and `["config"]`

4. **AutomationService** (line 110)
   - Already wired through factory with all dependencies

### ✅ IPC Message Types Already Defined

All necessary message types added to `src/infrastructure/ipc/ipc_protocol.py` (lines 35-53):

**Entities:**
- `GET_ENTITIES` - Get all entities
- `CREATE_ENTITY` - Create new entity
- `UPDATE_ENTITY` - Update existing entity
- `DELETE_ENTITY` - Delete entity

**Settings:**
- `GET_SETTINGS` - Get LLM settings
- `UPDATE_SETTINGS` - Update LLM settings

**Modules:**
- `GET_MODULES` - Get module states
- `TOGGLE_MODULE` - Enable/disable module

**Branches:**
- `GET_BRANCHES` - Get all branches
- `CREATE_BRANCH` - Create new branch
- `SWITCH_BRANCH` - Switch to branch
- `COMPARE_BRANCHES` - Compare two branches

### ✅ TUI Components Already Built

All components exist with mock data placeholders:

1. **EntityManager** (`src/presentation/tui/components/entity_manager.py`)
   - Lines 31-97: Mock ENTITY_DATA (to be removed)
   - Lines 182-194: TODO comments showing where to add IPC calls

2. **ModulesPage** (`src/presentation/tui/components/modules_page.py`)
   - Lines 18-28: Hardcoded MODULES_DATA (to be removed)
   - Lines 104-119: TODO comments for IPC integration

3. **BranchesPage** (`src/presentation/tui/components/branches_page.py`)
   - Lines 20-53: Mock BRANCH_DATA (to be removed)
   - Lines 182-194: TODO comments for IPC integration

4. **LLMSettingsPage** (`src/presentation/tui/components/llm_settings_page.py`)
   - Lines 202-224: Default settings (to be replaced with config)
   - Lines 205-210: TODO comments for IPC integration

---

## Implementation Plan

### Phase 1: Add Bridge IPC Handlers (~200 lines)

**File:** `src/presentation/bridge/bridge_service.py`

#### 1.1 Update Request Router (line ~200)

Add routing for new message types in `_handle_request()`:

```python
elif request_type == IPCMessageType.GET_ENTITIES:
    return self._handle_get_entities(request)
elif request_type == IPCMessageType.CREATE_ENTITY:
    return self._handle_create_entity(request)
elif request_type == IPCMessageType.UPDATE_ENTITY:
    return self._handle_update_entity(request)
elif request_type == IPCMessageType.DELETE_ENTITY:
    return self._handle_delete_entity(request)
elif request_type == IPCMessageType.GET_SETTINGS:
    return self._handle_get_settings(request)
elif request_type == IPCMessageType.UPDATE_SETTINGS:
    return self._handle_update_settings(request)
elif request_type == IPCMessageType.GET_MODULES:
    return self._handle_get_modules(request)
elif request_type == IPCMessageType.TOGGLE_MODULE:
    return self._handle_toggle_module(request)
elif request_type == IPCMessageType.GET_BRANCHES:
    return self._handle_get_branches(request)
elif request_type == IPCMessageType.CREATE_BRANCH:
    return self._handle_create_branch(request)
elif request_type == IPCMessageType.SWITCH_BRANCH:
    return self._handle_switch_branch(request)
```

#### 1.2 Entity Handlers (~80 lines)

```python
def _handle_get_entities(self, request: IPCRequest) -> str:
    """Handle GET_ENTITIES request."""
    try:
        entity_type = request.data.get("entity_type", "all")

        entities = {}

        if entity_type in ("all", "character"):
            entities["characters"] = [
                {
                    "id": char.name,
                    "name": char.name,
                    "type": "character",
                    "description": char.description,
                    "tags": char.metadata.get("tags", []),
                }
                for char in self.entity_service.list_characters()
            ]

        if entity_type in ("all", "location"):
            entities["locations"] = [
                {
                    "id": loc.name,
                    "name": loc.name,
                    "type": "location",
                    "description": loc.description,
                    "tags": loc.metadata.get("tags", []),
                }
                for loc in self.entity_service.list_locations()
            ]

        if entity_type in ("all", "organization"):
            entities["organizations"] = [
                {
                    "id": org.name,
                    "name": org.name,
                    "type": "organization",
                    "description": org.description,
                    "tags": org.metadata.get("tags", []),
                }
                for org in self.entity_service.list_organizations()
            ]

        if entity_type in ("all", "item"):
            entities["items"] = [
                {
                    "id": item.name,
                    "name": item.name,
                    "type": "item",
                    "description": item.description,
                    "tags": item.metadata.get("tags", []),
                }
                for item in self.entity_service.list_items()
            ]

        return create_response(request.request_id, entities=entities)

    except Exception as e:
        return create_error_response(request.request_id, str(e))

def _handle_create_entity(self, request: IPCRequest) -> str:
    """Handle CREATE_ENTITY request."""
    # TODO: Implement entity creation
    return create_error_response(request.request_id, "Entity creation not yet implemented")

def _handle_update_entity(self, request: IPCRequest) -> str:
    """Handle UPDATE_ENTITY request."""
    # TODO: Implement entity updating
    return create_error_response(request.request_id, "Entity updating not yet implemented")

def _handle_delete_entity(self, request: IPCRequest) -> str:
    """Handle DELETE_ENTITY request."""
    # TODO: Implement entity deletion
    return create_error_response(request.request_id, "Entity deletion not yet implemented")
```

#### 1.3 Module Handlers (~40 lines)

```python
def _handle_get_modules(self, request: IPCRequest) -> str:
    """Handle GET_MODULES request."""
    try:
        config = self.config_loader.load()
        modules_config = config.get("modules", {})

        modules = []
        for module_id, module_data in modules_config.items():
            enabled = module_data.get("enabled", False)
            module_config = module_data.get("config", {})

            modules.append({
                "id": module_id,
                "name": self._format_module_name(module_id),
                "description": self._get_module_description(module_id),
                "enabled": enabled,
                "config": module_config,
            })

        return create_response(request.request_id, modules=modules)

    except Exception as e:
        return create_error_response(request.request_id, str(e))

def _handle_toggle_module(self, request: IPCRequest) -> str:
    """Handle TOGGLE_MODULE request."""
    try:
        module_id = request.data.get("module_id")
        enabled = request.data.get("enabled")

        if not module_id:
            return create_error_response(request.request_id, "Missing module_id")

        # Load current config
        config = self.config_loader.load()

        # Update module enabled state
        if module_id in config.get("modules", {}):
            config["modules"][module_id]["enabled"] = enabled

            # Save config
            self.config_loader.save(config)

            return create_response(
                request.request_id,
                module_id=module_id,
                enabled=enabled,
                message=f"Module {module_id} {'enabled' if enabled else 'disabled'}"
            )
        else:
            return create_error_response(request.request_id, f"Unknown module: {module_id}")

    except Exception as e:
        return create_error_response(request.request_id, str(e))
```

#### 1.4 Settings Handlers (~40 lines)

```python
def _handle_get_settings(self, request: IPCRequest) -> str:
    """Handle GET_SETTINGS request."""
    try:
        config = self.config_loader.load()

        # Extract LLM settings from config
        settings = {
            "primary_provider": self.current_provider or "claude_api_client",
            "testing_mode": self.testing_mode,
            "modules": {},
        }

        # Add LLM module configs
        for module_id in ["claude_api_client", "openai_client", "deepseek_client", "openrouter_client"]:
            if module_id in config.get("modules", {}):
                module_data = config["modules"][module_id]
                settings["modules"][module_id] = {
                    "enabled": module_data.get("enabled", False),
                    **module_data.get("config", {})
                }

        return create_response(request.request_id, settings=settings)

    except Exception as e:
        return create_error_response(request.request_id, str(e))

def _handle_update_settings(self, request: IPCRequest) -> str:
    """Handle UPDATE_SETTINGS request."""
    try:
        settings = request.data.get("settings", {})

        # Load current config
        config = self.config_loader.load()

        # Update settings in config
        # TODO: Implement settings update logic

        # Save config
        self.config_loader.save(config)

        return create_response(request.request_id, message="Settings updated")

    except Exception as e:
        return create_error_response(request.request_id, str(e))
```

#### 1.5 Branch Handlers (~40 lines)

```python
def _handle_get_branches(self, request: IPCRequest) -> str:
    """Handle GET_BRANCHES request."""
    try:
        session_state = self.session_state_service.load_session_state(self.rp_dir)
        timeline = session_state.get("timeline", {})

        # Build branch tree from session state
        # TODO: Implement branch discovery from filesystem

        current_branch = timeline.get("session_id", "main")

        branches = {
            current_branch: {
                "title": current_branch.title(),
                "tags": ["active"],
                "parent": timeline.get("parent_session"),
                "branch_point": timeline.get("branch_point"),
                "active": True,
            }
        }

        return create_response(request.request_id, branches=branches, current=current_branch)

    except Exception as e:
        return create_error_response(request.request_id, str(e))

def _handle_create_branch(self, request: IPCRequest) -> str:
    """Handle CREATE_BRANCH request."""
    # TODO: Implement branch creation
    return create_error_response(request.request_id, "Branch creation not yet implemented")

def _handle_switch_branch(self, request: IPCRequest) -> str:
    """Handle SWITCH_BRANCH request."""
    try:
        branch_id = request.data.get("branch_id")

        if not branch_id:
            return create_error_response(request.request_id, "Missing branch_id")

        # TODO: Implement branch switching via SessionStateService

        return create_response(request.request_id, message=f"Switched to branch: {branch_id}")

    except Exception as e:
        return create_error_response(request.request_id, str(e))
```

#### 1.6 Helper Methods (~20 lines)

```python
def _format_module_name(self, module_id: str) -> str:
    """Format module ID to display name."""
    return module_id.replace("_", " ").title()

def _get_module_description(self, module_id: str) -> str:
    """Get module description."""
    descriptions = {
        "file_manager": "Manages file operations with backup support",
        "session_manager": "Handles session checkpoints and branching",
        "entity_manager": "Tracks characters, locations, and other entities",
        "agent_coordinator": "Coordinates automation agents",
        "claude_api_client": "Claude AI API client",
        "openai_client": "OpenAI API client",
        # Add more as needed
    }
    return descriptions.get(module_id, "No description available")
```

---

### Phase 2: Remove Mock Data from TUI (~50 lines)

#### 2.1 EntityManager (`entity_manager.py`)

**Remove:** Lines 31-97 (ENTITY_DATA)

**Replace `load_entities()` method:**

```python
async def load_entities(self) -> None:
    """Load entities from Bridge via IPC."""
    if not self.app.ipc_client:
        self.app.notify("IPC client not connected", severity="warning")
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.GET_ENTITIES,
            timeout=5.0
        )

        if response.success:
            entities_data = response.data.get("entities", {})

            # Flatten all entity types into single dict
            self.entities = {}
            for entity_type, entity_list in entities_data.items():
                for entity in entity_list:
                    self.entities[entity["id"]] = entity

            self.refresh_entity_list()
            self.app.notify(f"Loaded {len(self.entities)} entities", severity="information")
        else:
            self.app.notify(f"Failed to load entities: {response.error_message}", severity="error")

    except Exception as e:
        self.app.notify(f"Error loading entities: {e}", severity="error")
```

#### 2.2 ModulesPage (`modules_page.py`)

**Remove:** Lines 18-28 (MODULES_DATA)

**Replace `load_module_states()` method:**

```python
async def load_module_states(self) -> None:
    """Load module states from Bridge via IPC."""
    if not self.app.ipc_client:
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.GET_MODULES,
            timeout=5.0
        )

        if response.success:
            modules = response.data.get("modules", [])
            self.module_states = {m["id"]: m["enabled"] for m in modules}
            self.apply_module_states()

    except Exception:
        pass  # Silent fail, use defaults
```

**Update `save_module_state()` method:**

```python
async def save_module_state(self, module_id: str, enabled: bool) -> None:
    """Save module state to Bridge via IPC."""
    if not self.app.ipc_client:
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.TOGGLE_MODULE,
            timeout=5.0,
            module_id=module_id,
            enabled=enabled
        )

        if response.success:
            self.app.notify(response.data.get("message", "Module updated"), severity="information")

    except Exception as e:
        self.app.notify(f"Error updating module: {e}", severity="error")
```

#### 2.3 BranchesPage (`branches_page.py`)

**Remove:** Lines 20-53 (BRANCH_DATA)

**Replace `load_branches()` method:**

```python
async def load_branches(self) -> None:
    """Load branches from SessionService via IPC."""
    if not self.app.ipc_client:
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.GET_BRANCHES,
            timeout=5.0
        )

        if response.success:
            self.branches = response.data.get("branches", {})
            self.refresh_display()

    except Exception:
        pass  # Silent fail
```

#### 2.4 LLMSettingsPage (`llm_settings_page.py`)

**Replace `load_settings()` method:**

```python
async def load_settings(self) -> None:
    """Load settings from Bridge via IPC."""
    if not self.app.ipc_client:
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.GET_SETTINGS,
            timeout=5.0
        )

        if response.success:
            self.settings = response.data.get("settings", {})
            self.apply_settings()

    except Exception:
        pass  # Silent fail, use defaults
```

---

### Phase 3: Add SDK vs API Toggle (~100 lines)

#### 3.1 Update LLMSettingsPage UI

Add toggle after primary provider selection:

```python
yield Label("API Mode:")
yield Select(
    [
        ("Use SDK (Recommended)", "sdk"),
        ("Use Direct API", "api"),
    ],
    id="api-mode",
    value="sdk"
)
```

#### 3.2 Update Config Structure

Add to `config.json`:

```json
{
  "modules": {
    "claude_api_client": {
      "enabled": true,
      "config": {
        "use_sdk": true,  // NEW FIELD
        "model": "claude-3-5-sonnet-20241022",
        ...
      }
    }
  }
}
```

#### 3.3 Modify `_initialize_llm_client()` in Bridge

```python
def _initialize_llm_client(self, provider_name: Optional[str] = None) -> None:
    """Initialize LLM client with SDK or API mode."""

    config = self.config_loader.load()
    provider_config = config.get("modules", {}).get(provider_name, {}).get("config", {})

    use_sdk = provider_config.get("use_sdk", True)

    if use_sdk:
        # Use anthropic SDK
        from anthropic import Anthropic
        # ... SDK initialization
    else:
        # Use direct API calls
        # ... HTTP client initialization
```

---

### Phase 4: Entity Filter Buttons (~20 lines)

**File:** `src/presentation/tui/components/entity_manager.py`

Update filter button handlers:

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle filter button presses."""
    button_id = event.button.id

    if button_id in ("filter-all", "filter-character", "filter-location", "filter-organization"):
        # Extract filter type
        filter_type = button_id.replace("filter-", "")
        self.current_filter = filter_type

        # Apply filter
        if filter_type == "all":
            self.filtered_entities = self.entities
        else:
            self.filtered_entities = {
                eid: entity
                for eid, entity in self.entities.items()
                if entity.get("type") == filter_type
            }

        # Refresh display
        self.refresh_entity_list()
```

---

## Summary Checklist

### Files to Modify

- [ ] `src/presentation/bridge/bridge_service.py` - Add all IPC handlers (~200 lines)
- [ ] `src/presentation/tui/components/entity_manager.py` - Remove mock data, add filters (~30 lines)
- [ ] `src/presentation/tui/components/modules_page.py` - Remove hardcoded data (~30 lines)
- [ ] `src/presentation/tui/components/branches_page.py` - Remove mock data (~20 lines)
- [ ] `src/presentation/tui/components/llm_settings_page.py` - Add SDK toggle (~100 lines)

### Implementation Order

1. **Bridge Handlers** - Add all IPC request handlers first
2. **TUI Components** - Remove mock data and wire to IPC
3. **SDK Toggle** - Add UI and config support
4. **Entity Filters** - Implement filter button logic
5. **Testing** - Test each feature end-to-end

### Testing Checklist

- [ ] Entities load from filesystem
- [ ] Modules load from config.json
- [ ] Module toggles update config file
- [ ] Settings load from config
- [ ] Settings updates save to config
- [ ] Branches load from session state
- [ ] Entity filters work correctly
- [ ] SDK vs API toggle works
- [ ] All error cases handled gracefully

---

## Architecture Benefits

1. **Config-Driven:** All modules/settings come from `config.json`
2. **File-Based Discovery:** Entities auto-discovered from filesystem
3. **Service Delegation:** Bridge delegates to existing services
4. **Minimal Code:** ~370 lines vs ~1000+ for manual implementation
5. **Already Wired:** Services initialized in Bridge startup

---

## Future Enhancements

1. Entity CRUD operations (create, update, delete)
2. Branch creation and comparison
3. Advanced settings validation
4. Module dependency checking
5. Real-time config file watching

---

**End of Document**
