# Service Lifetime Management Analysis

**Analysis Date**: 2025-11-06
**Scope**: Service instantiation patterns, lifetime management, dependency injection
**Status**: ✅ Complete

---

## Executive Summary

The codebase has **NO active service lifetime management** despite having a ComponentRegistry defined. Services are instantiated independently in multiple locations with no coordination, singleton pattern, or dependency injection container.

**Key Finding**: ComponentRegistry exists but is **completely unused** - it's dead code.

**Severity**: 🟡 Medium - Creates maintainability issues and makes testing difficult

**Impact**:
- Services instantiated multiple times unnecessarily
- No control over service lifecycles
- Difficult to mock services for testing
- Repeated initialization overhead
- Inconsistent service state across instances
- No clear dependency graph

---

## Current State: Ad-Hoc Instantiation

### Pattern: Direct `new` Everywhere

Services are created directly with `SomeService(args)` wherever needed, with no centralized management.

**Example 1: AutomationOrchestrator.run_automation()** (src/automation/orchestrator.py:118-139)

```python
def run_automation(self, message: str) -> Tuple[str, List[str]]:
    # NEW instances created on EVERY automation run
    time_tracker = TimeTracker(self.timing_file, self.log_file)           # Line 118
    file_loader = FileLoader(self.rp_dir, self.log_file)                  # Line 123
    trigger_manager = TriggerManager(self.rp_dir, self.log_file, ...)    # Line 132
    status_manager = StatusManager(self.rp_dir)                           # Line 139

    # Use services...
```

**Problem**: New instances created on EVERY call, even though these could be reused.

**Example 2: EntityManager Duplication**

EntityManager instantiated independently in **5+ locations**:

| Location | Line | Purpose |
|----------|------|---------|
| rp_client_tui.py | 331 | TUI entity display |
| rp_client_tui.py | 556 | TUI entity editing |
| generate_preferences.py | 54 | Preference generation script |
| automation/orchestrator.py | 74 | Automation system |
| automation/orchestrator_v2.py | 80 | Alternative orchestrator |

**Each instance**:
- Scans and indexes entities independently
- No shared state
- Redundant file I/O
- No guarantee of consistency

---

## Defined But Unused: ComponentRegistry

### The Ghost System

**File**: src/automation/registry/registry.py (362 lines)

A **complete dependency injection system** exists with:
- ✅ Singleton scope support
- ✅ Transient scope support
- ✅ Scoped (per-request) support
- ✅ Dependency resolution by name or type
- ✅ Auto-wiring via type annotations
- ✅ Service locator pattern
- ✅ Global registry instance

**Code**: registry.py:40-248
```python
class ComponentRegistry:
    """
    Centralized component registry.

    Manages component registration, resolution, and lifecycle.
    """

    def register(self, name: str, factory: Callable,
                scope: ComponentScope = ComponentScope.SINGLETON, ...):
        """Register a component with lifecycle management."""

    def resolve(self, name_or_type: Any) -> Any:
        """Resolve a component by name or type."""

    def _resolve_component(self, component: Component) -> Any:
        """Resolve with singleton/transient/scoped handling."""
        # Singleton: cache and reuse
        if component.scope == ComponentScope.SINGLETON:
            if component.name not in self._singletons:
                self._singletons[component.name] = self._create_instance(component)
            return self._singletons[component.name]
```

### Usage Analysis: Zero References

**Search Results**:
```bash
grep -r "ComponentRegistry" src --exclude="*registry*"
→ Only found in: automation/registry/__init__.py (export only)

grep -r "get_registry\|register_singleton" src --exclude="*registry*"
→ Only found in: automation/registry/__init__.py (export only)
```

**Conclusion**: ComponentRegistry is **dead code** - defined but never used.

### Default Component Registration

**Code**: registry.py:291-335
```python
def _register_default_components(registry: ComponentRegistry) -> None:
    """
    Register default automation components.
    """
    # Register core components
    registry.register(
        "prompt_builder",
        lambda: PromptBuilder(get_rp_dir(), get_log_file()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "agent_factory",
        lambda: AgentFactory(get_rp_dir(), get_log_file()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "status_manager",
        lambda: StatusManager(get_rp_dir()),
        ComponentScope.SINGLETON
    )

    registry.register(
        "pipeline_builder",
        lambda: PipelineBuilder(log_file=get_log_file()),
        ComponentScope.TRANSIENT
    )
```

**Status**: This code runs when `get_registry()` is first called, but **`get_registry()` is never called** anywhere in the production code.

---

## Service Instantiation Patterns

### Pattern 1: New Instance Every Method Call

**Example**: AutomationOrchestrator (orchestrator.py:101-150)

```python
class AutomationOrchestrator:
    def run_automation(self, message: str):
        # Create new instances
        time_tracker = TimeTracker(...)
        file_loader = FileLoader(...)
        trigger_manager = TriggerManager(...)
        status_manager = StatusManager(...)

    def run_automation_new(self, message: str):
        # Duplicate creation in different method!
        time_tracker = TimeTracker(...)        # Line 186 - NEW instance again
        file_loader = FileLoader(...)          # Line 192 - NEW instance again
        trigger_manager = TriggerManager(...)  # Line 203 - NEW instance again
        status_manager = StatusManager(...)    # Line 249 - NEW instance again
```

**Instances Created Per Run**: 4 services × 2 methods = 8 service instances per automation run

**Overhead**:
- Repeated initialization
- Memory allocations
- File I/O (config loading, etc.)
- No state persistence

### Pattern 2: Instance Per Use Site

**Example**: EntityManager

```python
# TUI - Instance 1
def display_entities(self):
    entity_mgr = EntityManager(self.rp_dir)  # Scans files
    entity_mgr.scan_and_index()              # Indexes entities
    # Use it...

# TUI - Instance 2 (different method, same class!)
def edit_entity(self):
    entity_mgr = EntityManager(self.rp_dir)  # Scans AGAIN
    entity_mgr.scan_and_index()              # Indexes AGAIN
    # Use it...

# generate_preferences.py - Instance 3
def main():
    entity_mgr = EntityManager(rp_dir)       # Scans AGAIN
    entity_mgr.scan_and_index()              # Indexes AGAIN
    # Use it...

# orchestrator.py - Instance 4
def __init__(self, rp_dir):
    self.entity_manager = EntityManager(rp_dir)  # Scans AGAIN
    self.entity_manager.scan_and_index()          # Indexes AGAIN
```

**Cost of EntityManager.scan_and_index()**:
- Glob for `entities/*.json`
- Glob for `characters/*.json`
- Read and parse every JSON file
- Build index dictionary

**Repeated**: 4+ times per automation run across different components

### Pattern 3: Constructor Instantiation

**Example**: AutomationOrchestrator.__init__() (orchestrator.py:42-99)

```python
def __init__(self, rp_dir: Path):
    # Some services stored as instance variables
    self.entity_manager = EntityManager(rp_dir)           # Kept
    self.template_manager = PromptTemplateManager(rp_dir) # Kept
    self.prompt_builder = PromptBuilder(...)              # Kept

    # But others created fresh in run methods!
    # (TimeTracker, FileLoader, TriggerManager, StatusManager)
```

**Inconsistency**: No clear pattern for which services are instance variables vs created per-call

---

## Service Inventory

### Services Created Multiple Times

| Service | Instantiation Sites | Scope | Should Be |
|---------|-------------------|-------|-----------|
| **EntityManager** | 5+ locations | Per-use | Singleton |
| **TimeTracker** | Every automation run | Per-call | Could be singleton with reset() |
| **FileLoader** | Every automation run | Per-call | Singleton |
| **TriggerManager** | Every automation run | Per-call | Singleton |
| **StatusManager** | Every automation run | Per-call | Singleton |
| **PromptBuilder** | Stored in orchestrator | Instance | ✅ Correctly handled |
| **PromptTemplateManager** | Stored in orchestrator | Instance | ✅ Correctly handled |
| **ClaudeAPIClient** | Bridge initialization | Process | ✅ Correctly handled |
| **ClaudeSDKClient** | Bridge initialization | Process | ✅ Correctly handled |

### Services With Clear Lifetime

These are handled well:

**AgentFactory** (agent_factory.py:110-206)
```python
class AgentFactory:
    def __init__(self, rp_dir: Path, log_file: Path):
        self.rp_dir = rp_dir
        self.log_file = log_file
        # Stores paths, creates agents on demand

    def create_agent(self, agent_name: str, context: Dict):
        # Creates NEW agent instance (correct - agents are transient)
        agent = config.agent_class(self.rp_dir, self.log_file)
```

**Status**: ✅ Good pattern - factory is singleton, agents are transient

---

## Testing Impact

### Current Testing Difficulties

**Problem 1: Cannot Mock Services**

```python
# orchestrator.py:118
def run_automation(self, message: str):
    time_tracker = TimeTracker(self.timing_file, self.log_file)  # Hard-coded!
    # Cannot inject mock TimeTracker
```

**To test**, you must:
1. Create real file system structure
2. Provide real timing files
3. Actually run file I/O
4. Cannot test time calculation logic in isolation

**Problem 2: Cannot Control Service State**

```python
# Test wants to verify EntityManager caching
def test_entity_caching():
    mgr1 = EntityManager(test_dir)  # New instance
    mgr1.scan_and_index()

    mgr2 = EntityManager(test_dir)  # DIFFERENT instance!
    mgr2.scan_and_index()            # Scans again

    # Cannot test that caching works across calls
    # because different instances don't share state
```

**Problem 3: Setup Overhead**

Every test must:
- Create real RP directory structure
- Populate with test files
- Create real services
- No ability to stub/mock dependencies
- Slow integration tests, difficult unit tests

### Example Test (Current Approach)

```python
def test_automation_orchestrator():
    # Must create entire RP directory structure
    test_rp = tmp_path / "test_rp"
    (test_rp / "state").mkdir(parents=True)
    (test_rp / "entities").mkdir(parents=True)
    # ... create 10+ files

    # Create real orchestrator (cannot mock dependencies)
    orchestrator = AutomationOrchestrator(test_rp)

    # Run automation (creates 4 new services internally, cannot observe)
    result = orchestrator.run_automation("test message")

    # Can only test final output, not intermediate behavior
    assert "enhanced_prompt" in result
```

### Example Test (With DI)

```python
def test_automation_orchestrator_with_di():
    # Inject mock services
    mock_time_tracker = Mock(spec=TimeTracker)
    mock_time_tracker.calculate_time.return_value = (60, "activities")

    mock_file_loader = Mock(spec=FileLoader)
    mock_file_loader.load_tier1_files.return_value = ["tier1_content"]

    # Create orchestrator with mocked dependencies
    orchestrator = AutomationOrchestrator(
        time_tracker=mock_time_tracker,
        file_loader=mock_file_loader,
        # ... other mocks
    )

    # Test specific behavior
    result = orchestrator.run_automation("test")

    # Can verify interactions
    mock_time_tracker.calculate_time.assert_called_once_with("test", ...)
    mock_file_loader.load_tier1_files.assert_called_once()
```

---

## Global Singletons (Partial Solution)

### FSWriteQueue Global Singleton

**File**: src/fs_write_queue.py:260-281

```python
# Global singleton instance
_global_queue: Optional[FSWriteQueue] = None

def get_global_write_queue() -> FSWriteQueue:
    """Get or create global write queue singleton

    This provides a global write queue that can be used across the application.
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = FSWriteQueue()
    return _global_queue
```

**Status**: ✅ Working singleton pattern

**Usage**:
```bash
grep -r "get_global_write_queue" src --include="*.py"
→ Used in multiple locations for coordinated file writes
```

### BackgroundTaskQueue Global Singleton

**File**: src/automation/background_tasks.py:327

```python
# Global singleton task queue
_task_queue = None
```

**Status**: ✅ Working singleton pattern (implicit)

**Pattern**: These work because they're **global module-level variables**, but this approach:
- ❌ Hard to test (must reset global state)
- ❌ Not explicit in type signatures
- ❌ No lifecycle management
- ✅ Better than nothing

---

## Comparison: Current vs Ideal

### Current Approach: Direct Instantiation

```python
class AutomationOrchestrator:
    def __init__(self, rp_dir: Path):
        self.rp_dir = rp_dir
        # Some stored...
        self.entity_manager = EntityManager(rp_dir)
        self.prompt_builder = PromptBuilder(...)

    def run_automation(self, message: str):
        # Others created fresh every time
        time_tracker = TimeTracker(self.timing_file, self.log_file)
        file_loader = FileLoader(self.rp_dir, self.log_file)
        trigger_manager = TriggerManager(self.rp_dir, self.log_file, self.config)
        status_manager = StatusManager(self.rp_dir)
        # Use services...
```

**Issues**:
- Inconsistent lifetime decisions (why stored vs created?)
- No way to inject test doubles
- Repeated initialization overhead
- Hard-coded dependencies

### Ideal Approach 1: Constructor Injection

```python
class AutomationOrchestrator:
    def __init__(self,
                 rp_dir: Path,
                 entity_manager: EntityManager,
                 time_tracker: TimeTracker,
                 file_loader: FileLoader,
                 trigger_manager: TriggerManager,
                 status_manager: StatusManager,
                 prompt_builder: PromptBuilder):
        self.rp_dir = rp_dir
        self.entity_manager = entity_manager
        self.time_tracker = time_tracker
        self.file_loader = file_loader
        self.trigger_manager = trigger_manager
        self.status_manager = status_manager
        self.prompt_builder = prompt_builder

    def run_automation(self, message: str):
        # Use injected services
        total_minutes, activities = self.time_tracker.calculate_time(message, ...)
        tier1_files = self.file_loader.load_tier1_files()
        # ...
```

**Benefits**:
- ✅ Explicit dependencies in constructor
- ✅ Easy to inject mocks for testing
- ✅ Services can be singletons managed externally
- ✅ Clear dependency graph

### Ideal Approach 2: Using ComponentRegistry

```python
# Setup (app startup)
registry = get_registry()
registry.register_singleton("entity_manager", EntityManager(rp_dir))
registry.register("time_tracker", lambda: TimeTracker(...), scope=ComponentScope.SINGLETON)
registry.register("file_loader", lambda: FileLoader(...), scope=ComponentScope.SINGLETON)

# Usage
class AutomationOrchestrator:
    def __init__(self, rp_dir: Path, registry: ComponentRegistry):
        self.rp_dir = rp_dir
        self.registry = registry

    def run_automation(self, message: str):
        # Resolve services (gets singletons if registered as such)
        entity_manager = self.registry.resolve("entity_manager")
        time_tracker = self.registry.resolve("time_tracker")
        file_loader = self.registry.resolve("file_loader")
        # ...

# Testing
def test_orchestrator():
    test_registry = ComponentRegistry()
    test_registry.register_singleton("entity_manager", MockEntityManager())
    test_registry.register("time_tracker", lambda: MockTimeTracker())

    orchestrator = AutomationOrchestrator(test_dir, test_registry)
    # Test with mocks!
```

---

## Recommendations

### Recommendation 1: Enable ComponentRegistry (High Impact)

**Status**: Code exists, just needs to be wired up

**Effort**: 6-8 hours

**Steps**:

1. **Update AutomationOrchestrator** (2 hours)
   - Add registry parameter to `__init__`
   - Resolve services from registry instead of creating
   - Keep backward compatibility with factory functions

2. **Register services at app startup** (1 hour)
   - tui_bridge.py: Create and configure registry before orchestrator
   - Register EntityManager, TimeTracker, FileLoader, etc.

3. **Update service factory in registry** (1 hour)
   - Fix `_register_default_components()` to use actual rp_dir
   - Add missing services (TriggerManager, StatusManager)

4. **Update tests** (2-3 hours)
   - Create test registries with mocks
   - Remove file system setup where possible

5. **Documentation** (1 hour)
   - Update SYSTEM_ARCHITECTURE.md
   - Add service registration guide

**Example Migration**:

```python
# BEFORE (tui_bridge.py)
orchestrator = AutomationOrchestrator(rp_dir)

# AFTER
from src.automation.registry import get_registry

registry = get_registry()
# Registry auto-registers default components on first access
# Or manually register for custom setup:
# registry.register_singleton("entity_manager", EntityManager(rp_dir))

orchestrator = AutomationOrchestrator(rp_dir, registry=registry)
```

### Recommendation 2: Constructor Injection for Core Services (Medium Impact)

**Effort**: 4-6 hours (simpler than full registry)

**Approach**: Just inject services via constructor, manage lifecycles manually

**Steps**:

1. **Update AutomationOrchestrator.__init__()** (2 hours)
   ```python
   def __init__(self,
                rp_dir: Path,
                entity_manager: Optional[EntityManager] = None,
                time_tracker: Optional[TimeTracker] = None,
                file_loader: Optional[FileLoader] = None,
                ...):
       self.rp_dir = rp_dir
       self.entity_manager = entity_manager or EntityManager(rp_dir)
       self.time_tracker = time_tracker or TimeTracker(...)
       # ... with defaults for backward compatibility
   ```

2. **Store services as instance variables** (1 hour)
   - Remove per-call instantiation from run_automation()
   - Use self.time_tracker, self.file_loader, etc.

3. **Update call sites** (1-2 hours)
   - Create services once in bridge
   - Pass to orchestrator constructor

4. **Update tests** (1 hour)
   - Inject mocks via constructor

**Benefits**:
- ✅ Simpler than full registry
- ✅ Still enables testing
- ✅ Reduces repeated instantiation
- ✅ Backward compatible with defaults

### Recommendation 3: Document Current Pattern (Low Impact)

**Effort**: 1 hour

**If not ready to refactor**, at least document the current approach:

1. Update SYSTEM_ARCHITECTURE.md:
   - List which services are singletons (de facto)
   - List which are created per-call
   - Explain why (or acknowledge inconsistency)

2. Add comments to orchestrator.py:
   ```python
   def run_automation(self, message: str):
       # Note: Creates new instances per call for stateless operations
       # Future: Consider making these singletons for better performance
       time_tracker = TimeTracker(...)
   ```

3. Add testing guide:
   - How to test components given current architecture
   - Where mocking is difficult
   - Recommended test structure

### Recommendation 4: Gradual Migration Path

**Phase 1: Make services reusable** (2 hours)
- Convert orchestrator to store TimeTracker, FileLoader, etc. as instance variables
- Remove per-call instantiation

**Phase 2: Add optional DI** (3 hours)
- Add optional constructor parameters for services
- Default to current behavior if not provided
- Update tests to use DI

**Phase 3: Centralize instantiation** (2 hours)
- Create ServiceFactory class (simpler than ComponentRegistry)
- Use in bridge and TUI

**Phase 4: Full registry** (optional, 3 hours)
- Wire up existing ComponentRegistry
- Migrate from ServiceFactory

**Total**: 10 hours, but can stop at any phase

---

## Risk Assessment

### Risks of Current Approach

**🟡 Medium: Performance Overhead**
- Repeated EntityManager.scan_and_index() calls
- Multiple file I/O operations
- Memory allocations
- **Impact**: ~10-50ms overhead per automation run

**🟡 Medium: Testing Difficulty**
- Cannot unit test orchestrator logic in isolation
- Must use integration tests (slower, more brittle)
- Hard to reproduce edge cases
- **Impact**: Slower test suite, lower test coverage

**🟢 Low: Bugs from Instance Duplication**
- Services are mostly stateless, so different instances don't cause issues
- **Caveat**: EntityManager COULD have stale data if entities change between scans
- **Current Impact**: Minimal, but risk grows as system complexity increases

### Risks of Migration

**🟡 Medium: Breaking Changes**
- Changing constructor signatures affects all call sites
- **Mitigation**: Use optional parameters with defaults

**🟢 Low: Testing Overhead**
- Need to update existing tests
- **Mitigation**: Gradual migration, update tests incrementally

**🟢 Low: Registry Complexity**
- Adding DI container adds architectural complexity
- **Mitigation**: Start with constructor injection, only add registry if needed

---

## Comparison to Best Practices

### Industry Patterns

**Python DI Libraries**:
- **dependency_injector**: Full-featured DI container
- **injector**: Type-based dependency injection
- **FastAPI Depends**: Function-based DI

**Example (dependency_injector)**:
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    entity_manager = providers.Singleton(
        EntityManager,
        rp_dir=config.rp_dir
    )

    time_tracker = providers.Singleton(
        TimeTracker,
        timing_file=config.timing_file,
        log_file=config.log_file
    )

    orchestrator = providers.Factory(
        AutomationOrchestrator,
        rp_dir=config.rp_dir,
        entity_manager=entity_manager,
        time_tracker=time_tracker
    )
```

**Current RP Launcher vs Best Practice**:
| Aspect | Current | Best Practice | Gap |
|--------|---------|---------------|-----|
| **Dependency Injection** | ❌ None | ✅ DI container or constructor injection | Large |
| **Service Lifecycles** | ❌ Ad-hoc | ✅ Explicit singleton/transient scopes | Large |
| **Testability** | 🟡 Integration tests only | ✅ Unit + integration tests | Medium |
| **Code Exists** | ✅ ComponentRegistry defined | ✅ DI container | Just needs wiring |

---

## Conclusion

**Current State**: Services instantiated ad-hoc with no lifetime management

**Key Issues**:
1. ❌ ComponentRegistry defined but **completely unused** (dead code)
2. ❌ Services created multiple times unnecessarily (performance impact)
3. ❌ Cannot inject mocks for testing (testing difficulty)
4. ❌ Inconsistent patterns (some stored, some per-call)

**Recommended Action**: **Enable existing ComponentRegistry** (6-8 hours)

**Alternative**: **Constructor injection with defaults** (4-6 hours, simpler)

**Rationale**:
- ComponentRegistry code already exists and is well-designed
- Just needs to be wired up at app startup
- Provides singleton management, dependency resolution, testability
- Minimal risk with optional migration path

**Next Steps**:
1. Decide between full registry vs simple constructor injection
2. If registry: Wire up in tui_bridge.py, update orchestrator
3. If constructor: Add optional parameters with defaults
4. Update tests to use DI
5. Document service lifetimes in SYSTEM_ARCHITECTURE.md

**Estimated Total Effort**: 6-10 hours for full solution (depending on approach)

---

## Appendix: Code References

### Files With Service Instantiation

| File | Services Created | Pattern |
|------|-----------------|---------|
| src/automation/orchestrator.py:118-139 | TimeTracker, FileLoader, TriggerManager, StatusManager | Per-call |
| src/automation/orchestrator.py:74-99 | EntityManager, PromptTemplateManager, PromptBuilder | Instance variables |
| src/rp_client_tui.py:331 | EntityManager | Per-use |
| src/rp_client_tui.py:556 | EntityManager | Per-use |
| src/generate_preferences.py:54 | EntityManager | Per-script |
| src/tui_bridge.py:105 | AutomationOrchestrator | Process lifetime |
| src/automation/agents/agent_factory.py:145 | Agent instances | Transient |

### Dead Code

| File | Lines | Status |
|------|-------|--------|
| src/automation/registry/registry.py | 1-362 | ❌ Defined, never used |
| src/automation/registry/__init__.py | 1-10 | ❌ Exports unused registry |

### Working Patterns

| File | Pattern | Status |
|------|---------|--------|
| src/fs_write_queue.py:260-281 | Global singleton | ✅ Works |
| src/automation/background_tasks.py:327 | Global singleton | ✅ Works |
| src/automation/agents/agent_factory.py | Factory for transient objects | ✅ Good design |

---

**Analysis Complete** ✅
**Next Investigation**: Continue with remaining items in SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md
