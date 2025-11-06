# Module Enable/Disable Feature - TUI Integration Plan

## Overview

This document outlines the plan for adding a user-facing module management page to the TUI, allowing users to customize their RP experience by enabling/disabling features like entity sheets, memory systems, automation, and more.

### Current State

The system already has module enable/disable infrastructure in place:
- `ConfigLoader.is_module_enabled(module_name)` - src/infrastructure/config/config_loader.py:318
- `ConfigLoader.set_module_enabled(module_name, enabled)` - src/infrastructure/config/config_loader.py:336
- `ConfigLoader.list_enabled_modules()` - src/infrastructure/config/config_loader.py:358
- `ConfigLoader.list_disabled_modules()` - src/infrastructure/config/config_loader.py:370

**Existing Modules** (from defaults.py):
- `file_manager` - File management system
- `session_manager` - Session checkpointing and branching
- `agent_coordinator` - Background agent execution
- `entity_manager` - Character/location/organization sheets
- `automation_orchestrator` - Trigger and template automation
- `fs_write_queue` - Async file write queue
- `background_task_queue` - Background task execution
- `update_checker` - Automatic update checking
- Various LLM providers (Claude, OpenAI, DeepSeek, OpenRouter)

### Goals

1. **User-Friendly Module Management**: Provide a TUI interface for toggling modules
2. **Clear Descriptions**: Help users understand what each module does
3. **Dependency Awareness**: Warn users about module dependencies
4. **Persistence**: Save changes to config.json
5. **Live Updates**: Apply changes without restarting (where possible)

---

## User-Facing Modules

Not all technical modules should be exposed to users. Here's the recommended classification:

### Core User Features (Always Show)

These are features users might want to customize:

| Module ID | Display Name | Description | Default |
|-----------|--------------|-------------|---------|
| `entity_manager` | Entity Sheets | Track characters, locations, organizations, and items | ON |
| `memory_system` | Memory & History | Store and recall conversation memories | ON |
| `session_manager` | Session Management | Save checkpoints and branch timelines | ON |
| `automation_orchestrator` | Automation System | Trigger-based responses and templates | ON |
| `agent_coordinator` | Background Agents | Async agent processing for complex tasks | ON |
| `preference_generation` | AI Preference Generation | Generate character preferences from personality cores | OFF |

### Advanced Features (Show in "Advanced" Section)

More technical features for power users:

| Module ID | Display Name | Description | Default |
|-----------|--------------|-------------|---------|
| `file_manager` | File Management | Handle file I/O with backups | ON |
| `fs_write_queue` | Async File Writes | Queue file writes for better performance | ON |
| `background_task_queue` | Background Tasks | Execute non-critical tasks asynchronously | ON |
| `update_checker` | Update Notifications | Check for system updates | OFF |
| `performance_tracking` | Performance Monitoring | Track and log performance metrics | OFF |

### System Modules (Hide or Show in "Expert" Section)

Critical system components that should rarely be disabled:

| Module ID | Display Name | Description | Default | Warning |
|-----------|--------------|-------------|---------|---------|
| `proxy_client` | Proxy Support | Enable proxy routing for API calls | ON | Disabling may break connectivity |

### LLM Providers (Separate Section or Hide)

These are better managed in the "Provider Selector" rather than modules page:
- `claude_api`, `openai_api`, `deepseek`, `openrouter`

---

## TUI Page Design

### Wireframe

```
┌─────────────────────────── Modules ────────────────────────────┐
│                                                                  │
│  Configure which features are enabled for your RP sessions      │
│                                                                  │
│  ┌────────────────── Core Features ────────────────────┐       │
│  │                                                       │       │
│  │  [✓] Entity Sheets                                   │       │
│  │      Track characters, locations, and organizations  │       │
│  │                                                       │       │
│  │  [✓] Memory & History                                │       │
│  │      Store and recall conversation memories          │       │
│  │                                                       │       │
│  │  [✓] Session Management                              │       │
│  │      Save checkpoints and branch timelines           │       │
│  │                                                       │       │
│  │  [✓] Automation System                               │       │
│  │      Trigger-based responses and templates           │       │
│  │                                                       │       │
│  │  [✓] Background Agents                               │       │
│  │      Async agent processing for complex tasks        │       │
│  │                                                       │       │
│  │  [ ] AI Preference Generation                        │       │
│  │      Generate character preferences (experimental)   │       │
│  │                                                       │       │
│  └───────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────── Advanced ─────────────────────┐           │
│  │  [Show]                                           │           │
│  └───────────────────────────────────────────────────┘           │
│                                                                  │
│  Changes are saved immediately to config.json                   │
│                                                                  │
│  [Apply & Restart]  [Reset to Defaults]  [Close]                │
└──────────────────────────────────────────────────────────────────┘
```

### Component Structure

```
ModulesScreen (ModalScreen)
  └─ Container
      ├─ Header ("Modules Configuration")
      ├─ Description (Static text)
      ├─ CoreFeaturesPanel (Collapsible)
      │   └─ ModuleToggleList
      │       └─ ModuleToggle (x6)
      ├─ AdvancedFeaturesPanel (Collapsible, collapsed by default)
      │   └─ ModuleToggleList
      │       └─ ModuleToggle (x5)
      ├─ ExpertFeaturesPanel (Collapsible, collapsed by default)
      │   └─ ModuleToggleList
      │       └─ ModuleToggle (x1)
      └─ ActionBar
          ├─ ApplyButton
          ├─ ResetButton
          └─ CloseButton
```

---

## Implementation Details

### Phase 1: Data Layer (1-2 hours)

**File**: `src/domain/modules/module_registry.py`

Create a registry for user-facing modules:

```python
"""User-facing module registry for TUI."""

from dataclasses import dataclass
from enum import Enum


class ModuleCategory(Enum):
    """Module categorization for UI display."""
    CORE = "core"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class ModuleSpec:
    """Specification for a user-facing module."""

    module_id: str  # Config key (e.g., "entity_manager")
    display_name: str  # User-friendly name
    description: str  # Brief explanation
    category: ModuleCategory  # UI grouping
    default_enabled: bool  # Default state
    experimental: bool = False  # Show experimental badge
    requires: list[str] | None = None  # Module dependencies
    warns_on_disable: str | None = None  # Warning message


# Core user features
CORE_MODULES: list[ModuleSpec] = [
    ModuleSpec(
        module_id="entity_manager",
        display_name="Entity Sheets",
        description="Track characters, locations, organizations, and items",
        category=ModuleCategory.CORE,
        default_enabled=True,
    ),
    ModuleSpec(
        module_id="memory_system",
        display_name="Memory & History",
        description="Store and recall conversation memories",
        category=ModuleCategory.CORE,
        default_enabled=True,
        requires=["entity_manager"],
    ),
    ModuleSpec(
        module_id="session_manager",
        display_name="Session Management",
        description="Save checkpoints and branch timelines",
        category=ModuleCategory.CORE,
        default_enabled=True,
    ),
    ModuleSpec(
        module_id="automation_orchestrator",
        display_name="Automation System",
        description="Trigger-based responses and templates",
        category=ModuleCategory.CORE,
        default_enabled=True,
    ),
    ModuleSpec(
        module_id="agent_coordinator",
        display_name="Background Agents",
        description="Async agent processing for complex tasks",
        category=ModuleCategory.CORE,
        default_enabled=True,
        requires=["automation_orchestrator"],
    ),
    ModuleSpec(
        module_id="preference_generation",
        display_name="AI Preference Generation",
        description="Generate character preferences from personality cores",
        category=ModuleCategory.CORE,
        default_enabled=False,
        experimental=True,
        requires=["entity_manager"],
    ),
]

# Advanced features
ADVANCED_MODULES: list[ModuleSpec] = [
    ModuleSpec(
        module_id="file_manager",
        display_name="File Management",
        description="Handle file I/O with automatic backups",
        category=ModuleCategory.ADVANCED,
        default_enabled=True,
        warns_on_disable="Disabling may cause data loss. Not recommended.",
    ),
    ModuleSpec(
        module_id="fs_write_queue",
        display_name="Async File Writes",
        description="Queue file writes for better performance",
        category=ModuleCategory.ADVANCED,
        default_enabled=True,
        requires=["file_manager"],
    ),
    ModuleSpec(
        module_id="background_task_queue",
        display_name="Background Tasks",
        description="Execute non-critical tasks asynchronously",
        category=ModuleCategory.ADVANCED,
        default_enabled=True,
    ),
    ModuleSpec(
        module_id="update_checker",
        display_name="Update Notifications",
        description="Check for system updates automatically",
        category=ModuleCategory.ADVANCED,
        default_enabled=False,
    ),
    ModuleSpec(
        module_id="performance_tracking",
        display_name="Performance Monitoring",
        description="Track and log performance metrics",
        category=ModuleCategory.ADVANCED,
        default_enabled=False,
    ),
]

# Expert features
EXPERT_MODULES: list[ModuleSpec] = [
    ModuleSpec(
        module_id="proxy_client",
        display_name="Proxy Support",
        description="Enable proxy routing for API calls",
        category=ModuleCategory.EXPERT,
        default_enabled=True,
        warns_on_disable="May break API connectivity if using a proxy.",
    ),
]

# Combined registry
MODULE_REGISTRY: dict[str, ModuleSpec] = {
    spec.module_id: spec
    for spec in CORE_MODULES + ADVANCED_MODULES + EXPERT_MODULES
}


def get_module_spec(module_id: str) -> ModuleSpec | None:
    """Get module specification by ID."""
    return MODULE_REGISTRY.get(module_id)


def list_modules_by_category(category: ModuleCategory) -> list[ModuleSpec]:
    """List all modules in a category."""
    return [
        spec for spec in MODULE_REGISTRY.values()
        if spec.category == category
    ]


def validate_dependencies(module_id: str, enabled_modules: set[str]) -> list[str]:
    """Check if enabling a module would violate dependencies.

    Args:
        module_id: Module to check
        enabled_modules: Set of currently enabled module IDs

    Returns:
        List of missing dependencies (empty if all satisfied)
    """
    spec = get_module_spec(module_id)
    if not spec or not spec.requires:
        return []

    missing = [
        req for req in spec.requires
        if req not in enabled_modules
    ]
    return missing


def get_dependents(module_id: str) -> list[str]:
    """Get list of modules that depend on this module.

    Args:
        module_id: Module to check

    Returns:
        List of module IDs that require this module
    """
    dependents = []
    for spec in MODULE_REGISTRY.values():
        if spec.requires and module_id in spec.requires:
            dependents.append(spec.module_id)
    return dependents
```

### Phase 2: IPC Protocol Extension (30 min)

**File**: `src/infrastructure/ipc/ipc_protocol.py` (modify)

Add new IPC commands for module management:

```python
# New request types
class ListModulesRequest(TypedDict):
    """Request list of available modules."""
    pass


class GetModuleStateRequest(TypedDict):
    """Request current state of a specific module."""
    module_id: str


class SetModuleStateRequest(TypedDict):
    """Request to enable/disable a module."""
    module_id: str
    enabled: bool


class GetEnabledModulesRequest(TypedDict):
    """Request list of enabled module IDs."""
    pass


# New response types
class ListModulesResponse(TypedDict):
    """Response with available modules."""
    modules: list[dict[str, Any]]  # List of ModuleSpec as dicts


class GetModuleStateResponse(TypedDict):
    """Response with module state."""
    module_id: str
    enabled: bool
    spec: dict[str, Any]  # ModuleSpec as dict


class SetModuleStateResponse(TypedDict):
    """Response after setting module state."""
    module_id: str
    enabled: bool
    success: bool
    restart_required: bool
    warnings: list[str]


class GetEnabledModulesResponse(TypedDict):
    """Response with enabled module IDs."""
    enabled: list[str]
    disabled: list[str]
```

### Phase 3: Bridge Handlers (1 hour)

**File**: `src/presentation/bridge/handlers/module_handlers.py` (new)

Create Bridge handlers for module operations:

```python
"""Bridge handlers for module management."""

from typing import Any

from ...domain.modules.module_registry import (
    MODULE_REGISTRY,
    ModuleCategory,
    get_dependents,
    get_module_spec,
    validate_dependencies,
)
from ...infrastructure.config.config_loader import ConfigLoader
from ...infrastructure.ipc.ipc_protocol import (
    GetEnabledModulesRequest,
    GetEnabledModulesResponse,
    GetModuleStateRequest,
    GetModuleStateResponse,
    ListModulesRequest,
    ListModulesResponse,
    SetModuleStateRequest,
    SetModuleStateResponse,
)


class ModuleHandlers:
    """Handlers for module management IPC commands."""

    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader

    def handle_list_modules(self, request: ListModulesRequest) -> ListModulesResponse:
        """Handle request to list available modules."""
        modules = [
            {
                "module_id": spec.module_id,
                "display_name": spec.display_name,
                "description": spec.description,
                "category": spec.category.value,
                "default_enabled": spec.default_enabled,
                "experimental": spec.experimental,
                "requires": spec.requires or [],
                "warns_on_disable": spec.warns_on_disable,
            }
            for spec in MODULE_REGISTRY.values()
        ]

        return ListModulesResponse(modules=modules)

    def handle_get_module_state(self, request: GetModuleStateRequest) -> GetModuleStateResponse:
        """Handle request to get module state."""
        module_id = request["module_id"]
        spec = get_module_spec(module_id)

        if not spec:
            raise ValueError(f"Unknown module: {module_id}")

        enabled = self.config_loader.is_module_enabled(module_id)

        return GetModuleStateResponse(
            module_id=module_id,
            enabled=enabled,
            spec={
                "display_name": spec.display_name,
                "description": spec.description,
                "category": spec.category.value,
            },
        )

    def handle_set_module_state(self, request: SetModuleStateRequest) -> SetModuleStateResponse:
        """Handle request to enable/disable a module."""
        module_id = request["module_id"]
        enabled = request["enabled"]

        spec = get_module_spec(module_id)
        if not spec:
            return SetModuleStateResponse(
                module_id=module_id,
                enabled=False,
                success=False,
                restart_required=False,
                warnings=[f"Unknown module: {module_id}"],
            )

        warnings = []

        # Check dependencies if enabling
        if enabled:
            enabled_modules = set(self.config_loader.list_enabled_modules())
            missing_deps = validate_dependencies(module_id, enabled_modules)
            if missing_deps:
                return SetModuleStateResponse(
                    module_id=module_id,
                    enabled=False,
                    success=False,
                    restart_required=False,
                    warnings=[
                        f"Cannot enable: missing dependencies: {', '.join(missing_deps)}"
                    ],
                )

        # Check dependents if disabling
        if not enabled:
            dependents = get_dependents(module_id)
            enabled_dependents = [
                dep for dep in dependents
                if self.config_loader.is_module_enabled(dep)
            ]
            if enabled_dependents:
                warnings.append(
                    f"Disabling will also disable: {', '.join(enabled_dependents)}"
                )

            # Add warning if spec has one
            if spec.warns_on_disable:
                warnings.append(spec.warns_on_disable)

        # Update config
        self.config_loader.set_module_enabled(module_id, enabled)

        # Disable dependents if disabling this module
        if not enabled:
            for dep in enabled_dependents:
                self.config_loader.set_module_enabled(dep, False)

        # Determine if restart required (most modules require restart)
        restart_required = True  # Conservative default

        return SetModuleStateResponse(
            module_id=module_id,
            enabled=enabled,
            success=True,
            restart_required=restart_required,
            warnings=warnings,
        )

    def handle_get_enabled_modules(self, request: GetEnabledModulesRequest) -> GetEnabledModulesResponse:
        """Handle request to list enabled/disabled modules."""
        enabled = self.config_loader.list_enabled_modules()
        disabled = self.config_loader.list_disabled_modules()

        return GetEnabledModulesResponse(
            enabled=enabled,
            disabled=disabled,
        )
```

**File**: `src/presentation/bridge/bridge_service.py` (modify)

Register module handlers:

```python
from .handlers.module_handlers import ModuleHandlers

class BridgeService:
    def __init__(self, ...):
        # ...existing code...
        self.module_handlers = ModuleHandlers(self.config_loader)

    def _register_handlers(self):
        # ...existing handlers...

        # Module management
        self.server.register("list_modules", self.module_handlers.handle_list_modules)
        self.server.register("get_module_state", self.module_handlers.handle_get_module_state)
        self.server.register("set_module_state", self.module_handlers.handle_set_module_state)
        self.server.register("get_enabled_modules", self.module_handlers.handle_get_enabled_modules)
```

### Phase 4: TUI Components (2-3 hours)

**File**: `src/presentation/tui/components/module_toggle.py` (new)

Create reusable toggle component:

```python
"""Module toggle component for TUI."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Checkbox, Label, Static


class ModuleToggle(Container):
    """Toggle switch for a module with description."""

    enabled = reactive(False)

    def __init__(
        self,
        module_id: str,
        display_name: str,
        description: str,
        enabled: bool = False,
        experimental: bool = False,
    ):
        super().__init__()
        self.module_id = module_id
        self.display_name = display_name
        self.description = description
        self.enabled = enabled
        self.experimental = experimental

    def compose(self) -> ComposeResult:
        with Container(classes="module-toggle-row"):
            checkbox = Checkbox(self.display_name, value=self.enabled)
            checkbox.id = f"toggle-{self.module_id}"

            if self.experimental:
                yield Static(f"{self.display_name} [EXPERIMENTAL]", classes="module-name")
            else:
                yield checkbox

            yield Static(self.description, classes="module-description")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox toggle."""
        self.enabled = event.value
        # Post custom event
        self.post_message(self.ModuleToggled(self.module_id, self.enabled))

    class ModuleToggled(Message):
        """Posted when module toggle changes."""

        def __init__(self, module_id: str, enabled: bool):
            super().__init__()
            self.module_id = module_id
            self.enabled = enabled
```

**File**: `src/presentation/tui/screens/modules_screen.py` (new)

Create modules management screen:

```python
"""Modules management screen for TUI."""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Footer, Header, Static

from ..components.module_toggle import ModuleToggle


class ModulesScreen(ModalScreen):
    """Screen for managing user-facing modules."""

    CSS = """
    ModulesScreen {
        align: center middle;
    }

    #modules-dialog {
        width: 80;
        height: 40;
        border: thick $background 80%;
        background: $surface;
    }

    .module-section {
        margin: 1 2;
    }

    .module-toggle-row {
        height: auto;
        margin: 1 0;
    }

    .module-name {
        text-style: bold;
    }

    .module-description {
        color: $text-muted;
        margin-left: 4;
    }

    .action-bar {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 1 2;
    }

    .restart-warning {
        color: $warning;
        text-align: center;
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.modules_state: dict[str, bool] = {}
        self.needs_restart = False

    def compose(self) -> ComposeResult:
        with Container(id="modules-dialog"):
            yield Header("Modules Configuration")

            yield Static(
                "Configure which features are enabled for your RP sessions",
                classes="description",
            )

            with VerticalScroll():
                # Core features
                with Collapsible(title="Core Features", collapsed=False, classes="module-section"):
                    yield from self._create_core_modules()

                # Advanced features
                with Collapsible(title="Advanced", collapsed=True, classes="module-section"):
                    yield from self._create_advanced_modules()

                # Expert features
                with Collapsible(title="Expert", collapsed=True, classes="module-section"):
                    yield from self._create_expert_modules()

            if self.needs_restart:
                yield Static(
                    "⚠ Restart required for changes to take effect",
                    classes="restart-warning",
                )

            with Container(classes="action-bar"):
                yield Button("Apply & Restart", id="apply-button", variant="primary")
                yield Button("Reset to Defaults", id="reset-button")
                yield Button("Close", id="close-button")

            yield Footer()

    def _create_core_modules(self) -> ComposeResult:
        """Create core module toggles."""
        # This would be populated from IPC call to list_modules
        yield ModuleToggle(
            module_id="entity_manager",
            display_name="Entity Sheets",
            description="Track characters, locations, and organizations",
            enabled=True,
        )
        yield ModuleToggle(
            module_id="memory_system",
            display_name="Memory & History",
            description="Store and recall conversation memories",
            enabled=True,
        )
        # ... etc

    def _create_advanced_modules(self) -> ComposeResult:
        """Create advanced module toggles."""
        yield ModuleToggle(
            module_id="file_manager",
            display_name="File Management",
            description="Handle file I/O with automatic backups",
            enabled=True,
        )
        # ... etc

    def _create_expert_modules(self) -> ComposeResult:
        """Create expert module toggles."""
        yield ModuleToggle(
            module_id="proxy_client",
            display_name="Proxy Support",
            description="Enable proxy routing for API calls",
            enabled=True,
        )

    async def on_module_toggle_module_toggled(self, event: ModuleToggle.ModuleToggled) -> None:
        """Handle module toggle."""
        # Send IPC request to Bridge to update module state
        response = await self.app.send_ipc_request(
            "set_module_state",
            {
                "module_id": event.module_id,
                "enabled": event.enabled,
            },
        )

        if response.get("success"):
            self.modules_state[event.module_id] = event.enabled
            if response.get("restart_required"):
                self.needs_restart = True
                self.refresh()  # Show restart warning

            # Show warnings if any
            if response.get("warnings"):
                # Show notification or dialog
                pass
        else:
            # Revert toggle and show error
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id == "apply-button":
            # Restart application
            self.app.restart()
        elif event.button.id == "reset-button":
            # Reset to defaults
            self.reset_to_defaults()

    async def reset_to_defaults(self) -> None:
        """Reset all modules to default state."""
        # Send IPC requests to reset each module
        pass
```

### Phase 5: TUI Integration (30 min)

**File**: `src/presentation/tui/app.py` (modify)

Add modules screen to keybindings:

```python
from .screens.modules_screen import ModulesScreen

class RPAssistantApp(App):
    BINDINGS = [
        # ...existing bindings...
        ("ctrl+m", "toggle_modules", "Modules"),
    ]

    def action_toggle_modules(self) -> None:
        """Show modules configuration screen."""
        self.push_screen(ModulesScreen())
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/domain/modules/test_module_registry.py`

```python
def test_get_module_spec():
    """Test retrieving module specifications."""

def test_list_modules_by_category():
    """Test filtering modules by category."""

def test_validate_dependencies():
    """Test dependency validation."""

def test_get_dependents():
    """Test finding dependent modules."""
```

**File**: `tests/unit/presentation/bridge/handlers/test_module_handlers.py`

```python
def test_list_modules():
    """Test listing available modules."""

def test_get_module_state():
    """Test getting module enabled state."""

def test_set_module_state_enable():
    """Test enabling a module."""

def test_set_module_state_disable():
    """Test disabling a module."""

def test_set_module_state_missing_dependencies():
    """Test enabling module with missing dependencies."""

def test_set_module_state_disable_with_dependents():
    """Test disabling module disables dependents."""
```

### Integration Tests

**File**: `tests/integration/test_module_management.py`

```python
def test_module_enable_disable_round_trip():
    """Test enabling and disabling modules via IPC."""

def test_module_state_persistence():
    """Test module state persists to config.json."""

def test_dependency_cascade():
    """Test disabling module cascades to dependents."""
```

### Manual Testing Checklist

- [ ] Open modules screen (Ctrl+M)
- [ ] Toggle entity_manager off
- [ ] Verify warning about dependents
- [ ] Verify memory_system and preference_generation also disabled
- [ ] Close and reopen screen - verify state persisted
- [ ] Enable entity_manager
- [ ] Verify can now enable memory_system
- [ ] Click "Reset to Defaults"
- [ ] Verify all modules return to default state
- [ ] Click "Apply & Restart"
- [ ] Verify application restarts with new settings

---

## Implementation Checklist

### Phase 1: Data Layer (1-2 hours)
- [ ] Create `src/domain/modules/` directory
- [ ] Create `module_registry.py` with ModuleSpec definitions
- [ ] Add CORE_MODULES, ADVANCED_MODULES, EXPERT_MODULES
- [ ] Implement dependency validation functions
- [ ] Add unit tests for registry

### Phase 2: IPC Protocol (30 min)
- [ ] Add module management request/response types to ipc_protocol.py
- [ ] Update IPC protocol version
- [ ] Document new commands

### Phase 3: Bridge Handlers (1 hour)
- [ ] Create `handlers/module_handlers.py`
- [ ] Implement ModuleHandlers class
- [ ] Add handlers to BridgeService
- [ ] Add unit tests for handlers

### Phase 4: TUI Components (2-3 hours)
- [ ] Create `components/module_toggle.py`
- [ ] Create `screens/modules_screen.py`
- [ ] Add CSS styling for module screen
- [ ] Implement IPC communication from TUI to Bridge
- [ ] Add warning dialogs for dangerous operations

### Phase 5: TUI Integration (30 min)
- [ ] Add keybinding (Ctrl+M) to open modules screen
- [ ] Add menu item if menu exists
- [ ] Test screen navigation

### Phase 6: Testing (1-2 hours)
- [ ] Write unit tests for registry
- [ ] Write unit tests for handlers
- [ ] Write integration tests
- [ ] Manual testing with checklist
- [ ] Test restart behavior

### Phase 7: Documentation (30 min)
- [ ] Update user guide with module descriptions
- [ ] Document keybindings
- [ ] Add screenshots to docs
- [ ] Update config.json examples

---

## Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 1-2 hours | Data layer and registry |
| Phase 2 | 30 min | IPC protocol extension |
| Phase 3 | 1 hour | Bridge handlers |
| Phase 4 | 2-3 hours | TUI components and screens |
| Phase 5 | 30 min | TUI integration |
| Phase 6 | 1-2 hours | Testing |
| Phase 7 | 30 min | Documentation |
| **Total** | **7-9.5 hours** | Complete implementation |

---

## Future Enhancements

### Phase 2 Features (Future)

1. **Live Reload**: Apply some module changes without restart
2. **Module Presets**: "Story Mode", "Combat Mode", "Lightweight" presets
3. **Module Statistics**: Show memory usage, performance impact per module
4. **Module Marketplace**: Download community modules (requires plugin system)
5. **Conditional Modules**: Enable modules based on provider or session type
6. **Module Health**: Show status indicators (healthy, warning, error)

### Example: Module Presets

```python
PRESETS = {
    "story_focused": {
        "entity_manager": True,
        "memory_system": True,
        "session_manager": True,
        "automation_orchestrator": True,
        "agent_coordinator": False,  # Disable for faster responses
        "performance_tracking": False,
    },
    "performance": {
        "entity_manager": False,
        "memory_system": False,
        "session_manager": True,
        "automation_orchestrator": False,
        "agent_coordinator": False,
        "performance_tracking": True,
    },
}
```

---

## User Experience Flow

### Scenario 1: Disabling Entity Sheets

1. User presses Ctrl+M to open Modules screen
2. User unchecks "Entity Sheets"
3. System shows warning: "Disabling will also disable: Memory & History, AI Preference Generation"
4. User confirms
5. System updates config.json and shows "Restart required" warning
6. User clicks "Apply & Restart"
7. Application restarts with entity management disabled

### Scenario 2: Enabling Experimental Feature

1. User opens Modules screen
2. User checks "AI Preference Generation [EXPERIMENTAL]"
3. System checks dependencies - requires entity_manager
4. entity_manager is enabled, so change succeeds
5. System shows notification: "Experimental features may be unstable"
6. User clicks "Apply & Restart"
7. Preference generation now available in entity editor

---

## Questions for User

Before implementation, please confirm:

1. **Module Categories**: Should we use Core/Advanced/Expert, or different groupings?
2. **Restart Behavior**: Should we implement live reload for some modules, or always require restart?
3. **Keybinding**: Is Ctrl+M acceptable, or prefer different key?
4. **Warnings**: Should dependency warnings be dismissible, or block changes?
5. **Presets**: Should module presets be included in Phase 1, or deferred?

---

## Success Criteria

1. ✅ Users can view all available modules
2. ✅ Users can enable/disable modules via checkbox
3. ✅ Dependency warnings appear when trying invalid operations
4. ✅ Changes persist to config.json
5. ✅ Restart applies changes correctly
6. ✅ All tests pass (unit + integration)
7. ✅ Documentation complete with examples

---

## Conclusion

This plan provides a comprehensive module management system for the TUI, allowing users to customize their RP experience without editing config files directly. The implementation leverages existing infrastructure (ConfigLoader) and follows the established IPC pattern for Bridge/TUI communication.

The estimated 7-9.5 hour implementation includes all phases from data layer to documentation, providing users with a polished, intuitive interface for feature management.
