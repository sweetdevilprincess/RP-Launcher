# Module Implementation Tracking

**Project**: Module Manager System
**Started**: 2025-10-17
**Status**: Planning / In Progress

---

## Overview

This document tracks the conversion of existing RP system components to the new module-managed architecture. The goal is to create a centralized `ModuleManager` that handles initialization, dependencies, lifecycle, and configuration for all major system components.

### Why Modules?

**Current Problem**:
- Adding new features requires modifying launcher/bridge initialization code
- Dependencies between components aren't explicit
- Initialization order matters but isn't enforced
- Hard to enable/disable features
- Shutdown/cleanup is scattered

**Module Manager Benefits**:
- ✅ Add modules without touching core code
- ✅ Enable/disable features via config
- ✅ Automatic dependency resolution
- ✅ Consistent lifecycle (init → start → stop → cleanup)
- ✅ Centralized error handling
- ✅ Hot reloading capability
- ✅ Easier testing (load only needed modules)

---

## Module Conversion Status

| System | Status | Priority | Dependencies | Est. Time | Assignee | Notes |
|--------|--------|----------|--------------|-----------|----------|-------|
| **SessionManager** | 🟢 Complete | High | None (optional) | 1-2 hours | - | Module wrapper created and ready to use |
| **FileManager** | 🟢 Complete | Critical | None | 2-3 hours | - | Module wrapper created and ready to use |
| **FSWriteQueue** | 🟢 Complete | High | FileManager | 1-2 hours | - | Module wrapper created and ready to use |
| **AgentCoordinator** | 🟢 Complete | High | FileManager, FSWriteQueue | 2-3 hours | - | Module wrapper created and ready to use |
| **EntityManager** | 🟢 Complete | Medium | FileManager | 1-2 hours | - | Module wrapper created and ready to use |
| **AutomationOrchestrator** | 🟢 Complete | Critical | AgentCoordinator, FileManager | 3-4 hours | - | V2 pipeline architecture, module wrapper created |
| **BackgroundTaskQueue** | 🟢 Complete | High | None | 1-2 hours | - | Module wrapper created and ready to use |
| **UpdateChecker** | 🟢 Complete | Low | None | 30 min | - | Module wrapper created and ready to use |
| **ProxyClient** | ⏭️ Skipped | Medium | None | N/A | - | Keeping as core infrastructure (not a module) |
| **ClaudeAPIClient** | ⏭️ Skipped | Medium | ProxyClient | N/A | - | Keeping as core infrastructure (not a module) |
| **DeepSeekClient** | ⏭️ Skipped | Medium | ProxyClient | N/A | - | Keeping as core infrastructure (not a module) |

**Legend**:
- 🟢 Complete - Module implemented and tested
- 🟡 Ready - Code ready, needs wrapping
- 🔵 In Progress - Currently being converted
- ⬜ Not Started - Not yet begun
- 🔴 Blocked - Waiting on dependencies

**Total Estimated Time**: 15-20 hours for all modules

---

## Core Systems

### 1. FileManager

**Current Location**: `src/file_manager.py`
**New Location**: `src/modules/files/file_manager.py`
**Status**: ⬜ Not Started
**Priority**: Critical (foundation for many other modules)

**Why First?**:
- No dependencies on other modules
- Many modules depend on it
- Critical infrastructure component

**Current Usage**:
```python
# In bridge/automation
file_manager = FileManager(rp_dir)
file_manager.read_json("config.json")
```

**After Module Conversion**:
```python
# In bridge
manager = ModuleManager(rp_dir, config)
file_manager = manager.get('file_manager')
file_manager.read_json("config.json")
```

**Conversion Steps**:
1. Create `FileManagerModule` wrapper class
2. Move to `src/modules/files/`
3. Add to module registry
4. Update imports in dependent code
5. Test file operations still work

**Testing**:
- ✅ Read JSON files
- ✅ Write JSON files
- ✅ IPC operations
- ✅ Directory management

---

### 2. SessionManager

**Current Location**: `src/session_manager.py`
**New Location**: `src/modules/session/session_manager.py`
**Status**: 🟡 Ready (newly implemented)
**Priority**: High
**Dependencies**: FileManager (for config, but could be optional)

**Current Usage**:
```python
# In bridge
from src.session_manager import SessionManager
session_manager = SessionManager(rp_dir)
session_manager.retry()
```

**After Module Conversion**:
```python
# In bridge
manager = ModuleManager(rp_dir, config)
session_manager = manager.get('session_manager')
session_manager.retry()
```

**Conversion Steps**:
1. Create `SessionManagerModule` wrapper
2. Move to `src/modules/session/`
3. Add configuration options (auto-checkpoint, etc.)
4. Add to module registry
5. Update bridge command handlers

**Configuration**:
```json
{
  "modules": {
    "session_manager": {
      "enabled": true,
      "config": {
        "auto_checkpoint_frequency": 10,
        "keep_archived": 20,
        "compression": false
      }
    }
  }
}
```

**Testing**:
- ✅ All session commands work
- ✅ Configuration loaded correctly
- ✅ Module lifecycle works

---

### 3. FSWriteQueue

**Current Location**: `src/fs_write_queue.py`
**New Location**: `src/modules/files/fs_write_queue.py`
**Status**: ⬜ Not Started
**Priority**: High
**Dependencies**: FileManager

**Why Important?**:
- Async write operations prevent UI blocking
- Used by automation for chapter files
- Must coordinate with session manager

**Module Responsibilities**:
- Queue write operations
- Flush on demand or interval
- Handle write failures
- Coordinate with FileManager

**Conversion Considerations**:
- Needs clean shutdown (flush pending writes)
- Should respect session boundaries
- May need to notify SessionManager of writes

---

### 4. AgentCoordinator

**Current Location**: `src/automation/agent_coordinator.py`
**New Location**: `src/modules/agents/agent_coordinator.py`
**Status**: ⬜ Not Started
**Priority**: High
**Dependencies**: FileManager, FSWriteQueue

**Current Role**:
- Coordinates background agents
- Manages agent cache
- Schedules agent execution
- Tracks agent results

**Module Responsibilities**:
- Same as current, but managed lifecycle
- Clean shutdown of agents
- Dependency on file operations
- Integration with SessionManager for agent data

**Conversion Considerations**:
- Agents currently write separate cache file
- Need to integrate with session log system
- Background task coordination
- Graceful shutdown important

---

### 5. EntityManager

**Current Location**: `src/entity_manager.py`
**New Location**: `src/modules/entities/entity_manager.py`
**Status**: ⬜ Not Started
**Priority**: Medium
**Dependencies**: FileManager

**Current Role**:
- Tracks entity mentions
- Creates entity cards
- Manages entity data

**Module Conversion**:
- Relatively straightforward
- Mainly needs FileManager
- Configuration for auto-generation thresholds

---

### 6. AutomationOrchestrator

**Current Location**: `src/automation/orchestrator.py`
**New Location**: Keep in `src/automation/` (too complex to move)
**Status**: ⬜ Not Started
**Priority**: Critical
**Dependencies**: AgentCoordinator, FileManager

**Strategy**:
- Keep in automation folder (already well-organized)
- Wrap as module for lifecycle management
- Don't move files, just add module interface
- Handle as special case

**Why Not Move?**:
- automation/ is already a well-organized subsystem
- Moving would break many internal imports
- Better to keep automation/ as unit and wrap the orchestrator

---

### 7. BackgroundTaskQueue

**Current Location**: `src/automation/background_tasks.py`
**New Location**: `src/modules/tasks/background_task_queue.py`
**Status**: ⬜ Not Started
**Priority**: High
**Dependencies**: None

**Current Role**:
- Queue background tasks
- Execute tasks asynchronously
- Graceful shutdown with timeout

**Module Responsibilities**:
- Same as current
- Managed lifecycle
- Configuration for max workers, timeout

**Conversion**:
- Simple wrapper
- Add configuration support
- Ensure clean shutdown

---

## Support Systems

### 8. UpdateChecker

**Current Location**: `src/update_checker.py`
**New Location**: `src/modules/updates/update_checker.py`
**Status**: ⬜ Not Started
**Priority**: Low
**Dependencies**: None

**Simple Conversion**:
- Wrap existing class
- Add configuration (check interval, auto-check)
- Optional module (can be disabled)

---

### 9. ProxyClient

**Current Location**: `src/clients/proxy_client.py`
**New Location**: Keep in `src/clients/` (client infrastructure)
**Status**: ⬜ Not Started
**Priority**: Medium
**Dependencies**: None

**Strategy**:
- Keep in clients/ folder
- Wrap as module for configuration
- Used by all LLM clients

---

### 10-11. LLM Clients

**Current Locations**: `src/clients/claude_api.py`, `src/clients/deepseek.py`
**New Location**: Keep in `src/clients/`
**Status**: ⬜ Not Started
**Priority**: Medium
**Dependencies**: ProxyClient

**Strategy**:
- Keep in clients/ folder
- Wrap as modules for configuration
- Enable/disable per client
- Configuration for model selection, temperature, etc.

---

## Implementation Order

### Phase 1: Foundation (Week 1)
1. Create module manager core
2. Create base RPModule class
3. Convert FileManager (no dependencies)
4. Convert FSWriteQueue (depends on FileManager)
5. Test foundation modules

**Goal**: Establish module system with 2-3 working modules

### Phase 2: Core Modules (Week 2)
6. Convert BackgroundTaskQueue
7. Convert SessionManager
8. Convert AgentCoordinator
9. Test core modules together

**Goal**: Core session and agent systems module-managed

### Phase 3: Support Modules (Week 3)
10. Convert EntityManager
11. Convert UpdateChecker
12. Wrap AutomationOrchestrator
13. Test full system

**Goal**: All major systems module-managed

### Phase 4: Client Modules (Week 4)
14. Wrap ProxyClient
15. Wrap LLM clients
16. Add configuration UI
17. Final testing

**Goal**: Complete module system with configuration

---

## Module Interface Specification

Every module must implement this interface:

```python
class RPModule:
    """Base class for all RP system modules."""

    # Module metadata
    name: str = "base"
    version: str = "1.0.0"
    dependencies: List[str] = []
    optional: bool = False

    def __init__(self, rp_dir: Path, config: Dict, manager: 'ModuleManager'):
        """Initialize module with config and manager reference."""
        self.rp_dir = rp_dir
        self.config = config
        self.manager = manager
        self.logger = self._setup_logger()
        self._initialized = False
        self._running = False

    def initialize(self) -> bool:
        """Initialize module (load config, setup state).

        Returns:
            True if initialization successful, False otherwise
        """
        raise NotImplementedError

    def start(self) -> bool:
        """Start module (begin operations).

        Returns:
            True if start successful, False otherwise
        """
        raise NotImplementedError

    def stop(self) -> bool:
        """Stop module (pause operations).

        Returns:
            True if stop successful, False otherwise
        """
        raise NotImplementedError

    def cleanup(self) -> None:
        """Cleanup module (free resources)."""
        raise NotImplementedError

    def get_status(self) -> Dict:
        """Get module status.

        Returns:
            Dict with status information
        """
        return {
            "name": self.name,
            "initialized": self._initialized,
            "running": self._running,
            "version": self.version
        }

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle module-specific commands.

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        return None
```

---

## Testing Strategy

### Module-Level Testing
Each module needs:
- Unit tests for module wrapper
- Integration tests with dependencies
- Lifecycle tests (init → start → stop → cleanup)
- Configuration tests

### System-Level Testing
- All modules initialize in correct order
- Dependency resolution works
- Modules can be enabled/disabled
- System works with and without optional modules
- Performance impact minimal

### Test Checklist per Module
- [ ] Initialize with valid config
- [ ] Initialize with missing config (use defaults)
- [ ] Start successfully
- [ ] Stop successfully
- [ ] Cleanup successfully
- [ ] Handle errors gracefully
- [ ] Dependencies satisfied
- [ ] Can be disabled via config

---

## Configuration Format

```json
{
  "modules": {
    "file_manager": {
      "enabled": true,
      "priority": 1,
      "config": {}
    },
    "fs_write_queue": {
      "enabled": true,
      "priority": 2,
      "dependencies": ["file_manager"],
      "config": {
        "flush_interval": 5,
        "max_queue_size": 100
      }
    },
    "session_manager": {
      "enabled": true,
      "priority": 3,
      "dependencies": ["file_manager"],
      "config": {
        "auto_checkpoint_frequency": 10,
        "keep_archived": 20
      }
    },
    "agent_coordinator": {
      "enabled": true,
      "priority": 4,
      "dependencies": ["file_manager", "fs_write_queue"],
      "config": {
        "max_concurrent_agents": 3,
        "timeout": 60
      }
    },
    "entity_manager": {
      "enabled": true,
      "priority": 5,
      "dependencies": ["file_manager"],
      "config": {
        "auto_generate_threshold": 3
      }
    },
    "update_checker": {
      "enabled": false,
      "priority": 10,
      "config": {
        "check_interval": 86400,
        "auto_check": false
      }
    }
  }
}
```

---

## Benefits Tracking

### Maintainability
- **Before**: Add feature = modify launcher + bridge + initialization
- **After**: Add feature = drop module in modules/ folder, add to config

### Flexibility
- **Before**: All features always loaded
- **After**: Enable/disable any feature via config

### Testing
- **Before**: Hard to test individual components
- **After**: Load only needed modules for testing

### Error Handling
- **Before**: Scattered error handling
- **After**: Centralized in module manager

### Documentation
- **Before**: Hard to see what systems exist
- **After**: Easy to list all modules and their purpose

---

## Risks & Mitigation

### Risk 1: Performance Overhead
**Risk**: Module manager adds initialization/runtime overhead
**Mitigation**:
- Benchmark before/after
- Cache module references
- Lazy load optional modules

### Risk 2: Complex Dependencies
**Risk**: Circular dependencies or complex graphs
**Mitigation**:
- Use topological sort for initialization order
- Detect cycles early
- Keep dependencies simple

### Risk 3: Breaking Changes
**Risk**: Converting to modules breaks existing code
**Mitigation**:
- Keep old imports working temporarily
- Gradual migration
- Comprehensive testing

### Risk 4: Configuration Complexity
**Risk**: Config becomes too complex for users
**Mitigation**:
- Provide sensible defaults
- Config UI in TUI
- Validation and error messages

---

## Success Criteria

Module system is successful when:
- ✅ All major systems are module-managed
- ✅ Can add new module without modifying core code
- ✅ Can enable/disable features via config
- ✅ Dependencies resolve automatically
- ✅ Initialization order is correct
- ✅ Performance overhead < 100ms startup
- ✅ All tests pass
- ✅ Documentation complete
- ✅ User can understand and modify config

---

## Next Steps

1. **Create module manager core** (today)
   - Base RPModule class
   - ModuleManager class
   - Configuration loading
   - Dependency resolution

2. **Convert FileManager** (tomorrow)
   - Create FileManagerModule wrapper
   - Test module lifecycle
   - Verify functionality unchanged

3. **Convert SessionManager** (tomorrow)
   - Create SessionManagerModule wrapper
   - Add configuration options
   - Test with bridge commands

4. **Document process** (ongoing)
   - Create conversion guide
   - Update architecture docs
   - Add examples

---

**Last Updated**: 2025-10-17
**Status**: ✅ **COMPLETE** - All modules implemented and integrated

## Final Status Summary

All major systems have been successfully converted to the module-managed architecture:

### ✅ Completed Modules (9 total)
1. **FileManager** - Core file operations
2. **FSWriteQueue** - Debounced write operations
3. **BackgroundTaskQueue** - Async task execution
4. **SessionManager** - Session management (checkpoint/retry/branch)
5. **EntityManager** - Entity card management
6. **UpdateChecker** - GitHub version checking
7. **AgentCoordinator** - Multi-agent orchestration
8. **AutomationOrchestrator** - V2 pipeline architecture (UPGRADED FROM V1)

### ⏭️ Skipped (Remaining Core Infrastructure)
- **ProxyClient** - Core infrastructure, not a module
- **ClaudeAPIClient** - Core infrastructure, not a module
- **DeepSeekClient** - Core infrastructure, not a module

### 🎯 Key Achievements
- ✅ Migrated to OrchestratorV2 with modern pipeline architecture
- ✅ All modules registered in tui_bridge with automatic dependency resolution
- ✅ Clean module lifecycle (initialize → start → stop → cleanup)
- ✅ Configuration-driven enable/disable per module
- ✅ Graceful shutdown with proper cleanup
- ✅ Shared utilities created (file_utils, json_utils, agent_result, agent_logger, time_utils)
