# Module System Integration Guide

This document describes the module management system and how it's integrated between the UI and bridge.

## Overview

The module management system is **FULLY IMPLEMENTED** and ready to use. The UI communicates with the bridge via IPC to load module states and toggle modules on/off.

## Current State

### ✅ FULLY IMPLEMENTED

The entire module management system is complete and functional:

1. **Module Registry** (`src/presentation/tui/components/module_registry.py`)
   - `ModuleInfo` dataclass defining module metadata
   - `MODULE_REGISTRY` with 12 placeholder modules
   - Helper functions for querying modules by ID, category, dependencies

2. **Settings UI** (`src/presentation/tui/components/settings_overlay.py`)
   - Collapsible sections (Core, Automation, Optional, Extensions)
   - Module display with toggle switches
   - Status indicators (Running/Disabled)
   - Dependency display
   - Toggle functionality that sends IPC requests

3. **IPC Protocol** (`src/infrastructure/ipc/ipc_protocol.py`)
   - `GET_MODULES` message type defined
   - `TOGGLE_MODULE` message type defined

4. **Bridge Handler** (`src/presentation/bridge/handlers/module_handler.py`)
   - `ModuleHandler` class fully implemented
   - `GET_MODULES` handler with validation
   - `TOGGLE_MODULE` handler with safety checks
   - Registered in handler registry

5. **Config Infrastructure** (`src/infrastructure/config/config_loader.py`)
   - Module enable/disable methods
   - Config persistence to `config.json`

## IPC Message Specifications

### GET_MODULES

**Purpose:** Return the current state of all modules

**Request Format:**
```python
{
    "type": "get_modules",
    "request_id": "req_123",
    "data": {}
}
```

**Response Format:**
```python
{
    "type": "response",
    "request_id": "req_123",
    "success": true,
    "data": {
        "modules": {
            "entity_manager": {
                "enabled": true,
                "status": "running",
                "config": { /* module-specific config */ }
            },
            "template_system": {
                "enabled": true,
                "status": "running",
                "config": {}
            },
            "story_genome": {
                "enabled": false,
                "status": "disabled",
                "config": {}
            }
            # ... all modules from config.json
        }
    }
}
```

### TOGGLE_MODULE

**Purpose:** Enable or disable a module

**Request Format:**
```python
{
    "type": "toggle_module",
    "request_id": "req_124",
    "data": {
        "module_id": "story_genome",
        "enabled": true  # or false
    }
}
```

**Response Format (Success):**
```python
{
    "type": "response",
    "request_id": "req_124",
    "success": true,
    "data": {
        "module_id": "story_genome",
        "enabled": true,
        "message": "Module 'Story Genome' enabled"
    }
}
```

**Response Format (Success with Restart Note):**
```python
{
    "type": "response",
    "request_id": "req_125",
    "success": true,
    "data": {
        "module_id": "agent_coordinator",
        "enabled": false,
        "message": "Module 'Agent Coordinator' disabled (restart required for changes to take effect)"
    }
}
```

**Response Format (Failure - Active Provider):**
```python
{
    "type": "response",
    "request_id": "req_126",
    "success": false,
    "error_message": "Cannot disable active LLM provider 'claude_api_client'. Switch to a different provider first."
}
```

**Response Format (Failure - Unknown Module):**
```python
{
    "type": "response",
    "request_id": "req_127",
    "success": false,
    "error_message": "Unknown module: invalid_module_id"
}
```

## Safety Features

The `TOGGLE_MODULE` handler includes the following safety validations:

1. **Module Existence Check**
   - Validates that the `module_id` exists in config before toggling
   - Returns error if module not found

2. **Active Provider Protection**
   - Prevents disabling the currently active LLM provider
   - User must switch providers in LLM Setup first

3. **Restart Notifications**
   - Modules that require restart include notification in success message
   - Affected modules: `agent_coordinator`, `automation_orchestrator`, `entity_manager`, `session_manager`, `file_manager`

## Config Storage Format

Modules are stored in `config.json` with the following structure:
```json
{
  "modules": {
    "entity_manager": {
      "enabled": true,
      "config": { /* module-specific config */ }
    },
    "template_system": {
      "enabled": true,
      "config": { /* module-specific config */ }
    },
    "story_genome": {
      "enabled": false,
      "config": { /* module-specific config */ }
    }
  }
}
```

## UI Behavior

The UI is already configured to:

1. **On Mount:**
   - Call `GET_MODULES` to load current module states
   - Display switches in correct position (on/off)
   - Show status (Running/Disabled)

2. **On Toggle:**
   - Send `TOGGLE_MODULE` request to bridge
   - Wait for response
   - Update UI based on success/failure
   - Show notification to user
   - Revert toggle if operation fails

3. **Validation:**
   - Bridge validates module existence
   - Prevents disabling active LLM provider
   - Returns errors if validation fails

## Usage Guide

### For Users

1. **Open Settings → Modules tab**
2. **View Module States:**
   - Green checkmark = Running
   - Gray circle = Disabled
   - Modules are organized by category (Core, Automation, Optional)

3. **Toggle Modules:**
   - Click switch next to module name to enable/disable
   - Notifications appear confirming the action
   - Some modules show "(restart required)" message

4. **Understand Notifications:**
   - "Module enabled" = Change applied successfully
   - "Module disabled (restart required)" = Restart needed
   - "Cannot disable active LLM provider" = Switch provider in LLM Setup first

### For Developers

**Adding New Modules:**

1. Add module to `src/infrastructure/config/defaults.py`:
   ```python
   "new_module": {
       "enabled": True,
       "config": {
           # module-specific settings
       }
   }
   ```

2. Add description to `ModuleHandler._get_module_description()` in `module_handler.py`

3. Optionally add to `module_registry.py` for UI metadata

**Module States:**
- Config file is the source of truth
- Changes persist automatically
- No separate module state file needed

## Important Notes

- **Restart Requirement:** Most service modules (entities, sessions, agents) require bridge restart to fully apply changes
- **LLM Provider Protection:** Cannot disable currently active LLM provider
- **Config Persistence:** All changes immediately save to `config.json`
- **Module Registry:** UI uses `module_registry.py` for display metadata; bridge uses `config.json` for actual state
