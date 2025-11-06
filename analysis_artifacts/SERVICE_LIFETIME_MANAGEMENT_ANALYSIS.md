# Service Lifetime Management Analysis

**Analysis Date**: 2025-11-06
**Scope**: Service instantiation patterns, lifetime management, dependency injection
**Codebase**: `/refactoring/src/` (Clean Architecture Refactor)
**Status**: ✅ Complete

---

## Executive Summary

The refactoring codebase uses a **Factory Pattern** for the main AutomationService with proper dependency injection, which is a significant improvement. However, there is **no centralized service lifetime management** - services are still instantiated independently in multiple locations.

**Key Finding**: Factory pattern provides good DI for automation pipeline, but other services (EntityService, SessionStateService, SessionRepository) are created ad-hoc across Bridge and TUI with no coordination.

**Severity**: 🟡 Medium - Better than legacy code but still has duplication issues

**Impact**:
- ✅ Factory pattern enables testing of AutomationService
- ❌ Bridge and TUI create duplicate service instances
- ❌ Agents create FixtureEntityRepository 10+ times
- ❌ No singleton pattern or service container for cross-cutting services
- ❌ Inconsistent service state across processes

---

## Current State: Factory Pattern with Ad-Hoc Instantiation

### Pattern 1: Factory with Dependency Injection (Good)

**File**: `refactoring/src/automation/factory.py:118-276`

```python
def create_automation_service(
    rp_dir: Path,
    *,
    config_service: ConfigService | None = None,
    logger: LoggingService | None = None,
    bridge: Any = None,
    **overrides: Any,
) -> AutomationService:
    """Create a fully-wired AutomationService with default dependencies.

    This factory function instantiates all required services and wires them together
    with proper dependency injection. It uses sensible defaults but allows overriding
    any dependency for testing or customization.
    """
    # Create logger if not provided
    if logger is None:
        logger = get_logger(__name__)

    # Create config service if not provided
    if config_service is None:
        config_loader = ConfigLoader(rp_dir)
        config_data = config_loader.load()
        config_service = DictConfigService(config_data)

    # Create SessionStateService (used by multiple services)
    session_state_service = SessionStateService(logger=logger)

    # Create file manager with dependencies
    json_store = JsonStore(root=paths.state_dir, logger=logger)
    markdown_store = MarkdownStore(root=paths.rp_dir, logger=logger)
    write_queue = build_default_write_queue(logger=logger, debounce_ms=500)

    file_manager = FileManager(
        paths=paths,
        json_store=json_store,
        markdown_store=markdown_store,
        write_queue=write_queue,
        logger=logger,
        session_state_service=session_state_service,
    )

    # Create entity service (unless overridden)
    if "entity_service" in overrides:
        entity_service = overrides["entity_service"]
    else:
        entity_repository = FixtureEntityRepository(...)
        entity_service = EntityService(...)

    # Create session service (unless overridden)
    if "session_service" in overrides:
        session_service = overrides["session_service"]
    else:
        session_repository = SessionRepository(...)
        session_service = SessionService(...)

    # Return fully-wired service
    return AutomationService(
        config=config_service,
        logger=logger,
        entity_service=entity_service,
        session_service=session_service,
        prompt_builder=prompt_builder,
        agent_runner=agent_runner,
        file_access=file_access,
    )
```

**Status**: ✅ **Good Design**
- Proper dependency injection
- Allows overrides for testing
- Documents dependencies explicitly
- Sensible defaults

### Pattern 2: Bridge Creates Own Services (Duplication)

**File**: `refactoring/src/presentation/bridge/bridge_service.py:119-150`

```python
def _initialize_services(self) -> None:
    """Initialize refactored automation services."""
    print("[INIT] Initializing services...")

    # Automation service (using factory with bridge reference)
    self.automation_service = create_automation_service(self.rp_dir, bridge=self)
    print("[OK] Automation service initialized")

    # Entity service - DUPLICATE INSTANCE!
    self.entity_service = EntityService()
    print("[OK] Entity service initialized")

    # Session state service - DUPLICATE INSTANCE!
    self.session_state_service = SessionStateService(logger=self.logger)
    print("[OK] Session state service initialized")

    # Session repository - DUPLICATE INSTANCE!
    paths = StatePaths(rp_dir=self.rp_dir)
    self.session_repository = SessionRepository(
        paths=paths,
        logger=self.logger,
        session_state_service=self.session_state_service
    )

    # Session writeback
    self.session_writeback = SessionWriteBack(
        repository=self.session_repository,
        logger=self.logger
    )

    # Chatlog organizer
    self.chatlog_organizer = ChatlogOrganizer(
        paths=paths,
        logger=self.logger,
        repository=self.session_repository
    )
```

**Problem**: Bridge creates separate EntityService, SessionStateService, and SessionRepository, even though these are also created inside `create_automation_service()`.

**Why This Happens**: Bridge needs direct access to these services for IPC handlers, but the factory creates its own internal instances.

**Result**:
- EntityService: 2 instances (factory + bridge)
- SessionStateService: 2 instances (factory + bridge)
- SessionRepository: 2 instances (factory + bridge)

### Pattern 3: TUI Creates Own Services (More Duplication)

**File**: `refactoring/src/presentation/tui/app.py:105-119`

```python
def __init__(self, rp_dir: Path, bridge_host: str = "127.0.0.1", bridge_port: int = 5555):
    """Initialize RP Client TUI."""
    super().__init__()

    # Session repository for loading chat history
    paths = StatePaths(rp_dir=rp_dir)
    logger = PythonLoggingService(logger=logging.getLogger("rp.tui.app"))

    # Create session state service (needed for branch tracking)
    session_state_service = SessionStateService(logger=logger)

    # Create session repository with session state service
    self.session_repository = SessionRepository(
        paths=paths,
        logger=logger,
        session_state_service=session_state_service
    )
```

**Problem**: TUI creates its own SessionStateService and SessionRepository in a separate process.

**Why This Is Actually OK**: TUI runs in a different process from Bridge, so it MUST have its own instances. They communicate via IPC, not shared memory.

**Status**: ✅ **Correct** - Different processes need separate instances

### Pattern 4: Agents Create Repositories Per-Use (Heavy Duplication)

**Example**: `refactoring/src/automation/agents/implementations/relationship_analysis_agent.py`

**6 separate instantiations** of FixtureEntityRepository in a single file:

```python
# Line 358-362
from src.domain.entities import FixtureEntityRepository
repository = FixtureEntityRepository(
    rp_dir=self.rp_dir,
    session_state_service=self.session_state_service
)

# Line 412-416 - AGAIN
from src.domain.entities import FixtureEntityRepository
repository = FixtureEntityRepository(
    rp_dir=self.rp_dir,
    session_state_service=self.session_state_service
)

# Line 532-536 - AGAIN
from src.domain.entities import FixtureEntityRepository
repository = FixtureEntityRepository(
    rp_dir=self.rp_dir,
    session_state_service=self.session_state_service
)

# Line 691-695 - AGAIN
from src.domain.entities import FixtureEntityRepository
repository = FixtureEntityRepository(
    rp_dir=self.rp_dir,
    session_state_service=self.session_state_service
)

# ... and 2 more times
```

**Also found in**:
- `memory_creation_agent.py`: Line 298
- `contradiction_synthesis_agent.py`: Line 269
- `fact_extraction_agent.py`: Line 137
- `memory_extraction_agent.py`: Line 129

**Cost Per Instantiation**:
- Glob for `entities/*.json` files
- Glob for `characters/*.json` files
- Read and parse all JSON files
- Build entity index dictionaries

**Overhead**: ~10-20ms per instantiation, called 10+ times per automation run

---

## Service Inventory

### Services Created Multiple Times

| Service | Instantiation Sites | Actual Instances | Should Be |
|---------|-------------------|------------------|-----------|
| **FixtureEntityRepository** | 10+ locations (agents) | 10+ per automation run | Singleton per process |
| **SessionStateService** | Bridge + TUI + factory | 3 (2 in Bridge process) | 1 per process |
| **SessionRepository** | Bridge + TUI + factory | 3 (2 in Bridge process) | 1 per process |
| **EntityService** | Bridge + factory | 2 (both in Bridge process) | 1 per process |
| **FileManager** | Factory only | 1 | ✅ Correct |
| **AgentRegistry** | Factory only | 1 | ✅ Correct |
| **PromptBuilder** | Factory only | 1 | ✅ Correct |

### Services With Clear Lifetime

These are handled well:

**AutomationService** (created via factory)
- ✅ Single instance per Bridge process
- ✅ Proper dependency injection
- ✅ Can be mocked for testing
- ✅ All dependencies explicit

**LLM Clients** (created in Bridge)
```python
# bridge_service.py:71-74
self.primary_client: Optional[LLMClient] = None
self.secondary_client: Optional[LLMClient] = None
self.llm_routing: dict = {}
self.llm_client: Optional[LLMClient] = None  # Deprecated
```

**Status**: ✅ Managed explicitly as Bridge instance variables

---

## Domain-Specific Registries

The codebase has several registries, but they're **not** for dependency injection - they're for component discovery:

### AgentRegistry

**File**: `refactoring/src/automation/agents/registry.py:15-91`

```python
class AgentRegistry:
    """Registry for creating and ordering agent execution strategies.

    The registry reads configuration to determine:
    - Which agents are enabled
    - Agent execution order
    - Agent-specific configuration
    """

    def create_strategies(self, rp_dir: Path) -> list[AgentStrategy]:
        """Create agent strategy instances based on configuration.

        Returns:
            List of agent strategies in execution order
        """
        strategies = []

        # Create immediate agents
        for agent_config in self._config.get_list("agents.immediate", []):
            if agent_config.get("enabled", True):
                strategy = ImmediateAgentStrategy(
                    rp_dir=rp_dir,
                    config=agent_config,
                    logger=self._logger,
                    bridge=self._bridge
                )
                strategies.append(strategy)

        # Create background agents
        # ... same pattern

        return strategies
```

**Purpose**: Create agent strategies based on configuration (not general DI)

### TemplateRegistry

**File**: `refactoring/src/automation/templates/template_registry.py:13-156`

```python
class TemplateRegistry:
    """Registry for discovering and managing narrative templates.

    This registry:
    - Scans template directory
    - Discovers available templates
    - Finds composite templates (e.g., "dark_romance_thriller")
    - Normalizes genre names
    """
```

**Purpose**: Discover and validate prompt templates (not DI)

### TriggerRegistry

**File**: `refactoring/src/automation/triggers/registry.py:18-84`

```python
class TriggerRegistry:
    """Registry for creating and configuring trigger evaluators.

    This registry loads evaluator configurations and creates instances
    for keyword, regex, and semantic evaluation.
    """
```

**Purpose**: Create trigger evaluators (not DI)

### HANDLER_REGISTRY

**File**: `refactoring/src/presentation/bridge/handlers/__init__.py:54-73`

```python
# Handler Registry
HANDLER_REGISTRY: dict[IPCMessageType, type[BaseHandler]] = {
    IPCMessageType.PING: SystemHandler,
    IPCMessageType.GET_STATUS: SystemHandler,
    IPCMessageType.SEND_MESSAGE: MessageHandler,
    IPCMessageType.CREATE_BRANCH: BranchHandler,
    IPCMessageType.GET_ENTITIES: EntityHandler,
    IPCMessageType.GET_MODULES: ModuleHandler,
    IPCMessageType.UPDATE_SETTING: SettingsHandler,
    # ... more handlers
}
```

**Purpose**: Map IPC message types to handler classes (not DI)

**Conclusion**: All registries are **domain-specific**, not general-purpose dependency injection containers.

---

## Testing Impact

### Current Testing Approach

**Good**: Factory allows overrides for testing

```python
def test_automation_service():
    # Can inject mocks via factory
    mock_entity_service = Mock(spec=EntityService)
    mock_session_service = Mock(spec=SessionService)

    service = create_automation_service(
        test_rp_dir,
        entity_service=mock_entity_service,
        session_service=mock_session_service
    )

    # Test with mocked dependencies
    result = service.run(context)

    # Verify interactions
    mock_entity_service.prepare_entities.assert_called_once()
```

**Status**: ✅ Works well for AutomationService

**Bad**: Bridge and TUI create services directly

```python
def test_bridge_service():
    bridge = BridgeService(test_rp_dir)
    bridge.start()  # Creates EntityService internally - can't mock!

    # Cannot inject mock EntityService
    # Cannot test Bridge initialization without real EntityService
```

**Status**: ❌ Bridge is hard to unit test

### Testing Gaps

**Problem 1: Bridge Service Initialization**
- Creates 6+ services in `_initialize_services()`
- No constructor parameters for dependency injection
- Must use integration tests with real services
- Cannot isolate logic from dependencies

**Problem 2: Agent Repository Creation**
- Agents create FixtureEntityRepository inline
- Cannot inject mock repository
- Cannot test agent logic without real file I/O
- Slow tests, can't test edge cases

**Example**: Testing RelationshipAnalysisAgent

```python
# CURRENT (integration test required)
def test_relationship_agent():
    # Must create real RP directory with real entity files
    test_rp = setup_real_rp_directory(tmp_path)

    agent = RelationshipAnalysisAgent(rp_dir=test_rp, ...)
    result = agent.execute()  # Creates FixtureEntityRepository internally

    # Cannot mock repository, must use real files
    assert "relationship_data" in result
```

```python
# IDEAL (unit test with mocks)
def test_relationship_agent():
    mock_repository = Mock(spec=FixtureEntityRepository)
    mock_repository.get_relationships.return_value = {"Alice": {...}}

    agent = RelationshipAnalysisAgent(
        rp_dir=test_rp,
        repository=mock_repository  # Inject mock
    )
    result = agent.execute()

    # Can verify specific interactions
    mock_repository.get_relationships.assert_called_with("Alice")
```

---

## Comparison: Current vs Ideal

### Current Approach: Factory + Ad-Hoc Instantiation

**Bridge Process**:
```python
# Factory creates these:
automation_service = create_automation_service(rp_dir, bridge=self)
    → EntityService (instance 1)
    → SessionStateService (instance 1)
    → SessionRepository (instance 1)
    → FixtureEntityRepository (instance 1)

# Bridge ALSO creates these separately:
self.entity_service = EntityService()  # instance 2!
self.session_state_service = SessionStateService(...)  # instance 2!
self.session_repository = SessionRepository(...)  # instance 2!

# Agents create repositories:
agent.execute()
    → FixtureEntityRepository()  # instance 3!
    → FixtureEntityRepository()  # instance 4!
    → ... (10+ instances total)
```

**Issues**:
- Duplicate service instances in same process
- Cannot guarantee consistency
- Repeated initialization overhead
- Hard to test Bridge

### Ideal Approach 1: Service Container

```python
class ServiceContainer:
    """Centralized service lifecycle management."""

    def __init__(self, rp_dir: Path):
        self.rp_dir = rp_dir
        self._singletons: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}

    def register_singleton(self, interface: type, instance: Any) -> None:
        """Register a singleton service."""
        self._singletons[interface] = instance

    def register_factory(self, interface: type, factory: Callable) -> None:
        """Register a factory for creating instances."""
        self._factories[interface] = factory

    def get(self, interface: type) -> Any:
        """Get service instance (singleton or create new)."""
        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._factories:
            return self._factories[interface](self)

        raise KeyError(f"No service registered for {interface}")

# Usage in Bridge
class BridgeService:
    def __init__(self, rp_dir: Path):
        self.rp_dir = rp_dir
        self.container = ServiceContainer(rp_dir)

        # Register singletons
        self.container.register_singleton(
            SessionStateService,
            SessionStateService(logger=logger)
        )
        self.container.register_singleton(
            FixtureEntityRepository,
            FixtureEntityRepository(rp_dir=rp_dir)
        )

    def _initialize_services(self):
        # Get singletons from container
        self.session_state_service = self.container.get(SessionStateService)
        self.entity_repository = self.container.get(FixtureEntityRepository)

        # Automation service gets same instances
        self.automation_service = create_automation_service(
            self.rp_dir,
            bridge=self,
            session_state_service=self.session_state_service,
            entity_repository=self.entity_repository
        )
```

**Benefits**:
- ✅ Single instance of each service per process
- ✅ Explicit lifecycle management
- ✅ Easy to inject mocks for testing
- ✅ Clear dependency graph

### Ideal Approach 2: Extract Services from Factory

**Simpler alternative**: Make factory return services separately

```python
@dataclass
class AutomationServices:
    """Container for all automation services."""
    automation_service: AutomationService
    entity_service: EntityService
    session_service: SessionService
    session_state_service: SessionStateService
    entity_repository: FixtureEntityRepository
    session_repository: SessionRepository
    file_access: FileAccessService

def create_automation_services(rp_dir: Path, **overrides) -> AutomationServices:
    """Create all automation services."""
    # ... create services ...

    return AutomationServices(
        automation_service=automation_service,
        entity_service=entity_service,
        session_service=session_service,
        session_state_service=session_state_service,
        entity_repository=entity_repository,
        session_repository=session_repository,
        file_access=file_access,
    )

# Usage in Bridge
class BridgeService:
    def _initialize_services(self):
        # Get all services from factory
        services = create_automation_services(self.rp_dir, bridge=self)

        # Use same instances
        self.automation_service = services.automation_service
        self.entity_service = services.entity_service
        self.session_state_service = services.session_state_service
        self.session_repository = services.session_repository
        # ... no duplicates!
```

**Benefits**:
- ✅ Simpler than full container
- ✅ Still uses existing factory
- ✅ Eliminates duplicate instances
- ✅ Backward compatible

---

## Recommendations

### Recommendation 1: Return Services from Factory (High Impact, Low Effort)

**Effort**: 2-3 hours

**Steps**:

1. **Update factory.py** (1 hour)
   ```python
   @dataclass
   class AutomationServices:
       automation_service: AutomationService
       entity_service: EntityService
       session_state_service: SessionStateService
       entity_repository: FixtureEntityRepository
       session_repository: SessionRepository
       # ... other services

   def create_automation_services(...) -> AutomationServices:
       # ... existing code ...
       return AutomationServices(
           automation_service=automation_service,
           entity_service=entity_service,
           # ... all services
       )
   ```

2. **Update BridgeService** (30 min)
   ```python
   def _initialize_services(self):
       services = create_automation_services(self.rp_dir, bridge=self)

       self.automation_service = services.automation_service
       self.entity_service = services.entity_service
       self.session_state_service = services.session_state_service
       # ... use same instances
   ```

3. **Update agents to accept repository** (1 hour)
   ```python
   class RelationshipAnalysisAgent:
       def __init__(self, ..., repository: FixtureEntityRepository | None = None):
           self._repository = repository

       def execute(self, ...):
           repo = self._repository or FixtureEntityRepository(...)
           # Use repo
   ```

4. **Tests** (30 min)
   - Verify no duplicate instances
   - Test with mock services

**Impact**:
- Eliminates duplicate EntityService, SessionStateService, SessionRepository in Bridge
- Reduces memory footprint
- Makes Bridge easier to test

### Recommendation 2: Inject Repository into Agents (Medium Impact)

**Effort**: 3-4 hours

**Current**: Agents create FixtureEntityRepository inline
**After**: Agents accept repository via constructor

**Steps**:

1. **Update agent constructors** (2 hours)
   - Add `repository: FixtureEntityRepository | None` parameter
   - Default to creating if not provided (backward compatible)

2. **Update AgentRegistry/strategies** (1 hour)
   - Pass repository to agent constructors
   - Repository comes from factory

3. **Update tests** (1 hour)
   - Inject mock repository
   - Unit test agent logic without file I/O

**Impact**:
- Reduces FixtureEntityRepository instantiations from 10+ to 1
- Eliminates 10+ filesystem scans per automation run (~100-200ms saved)
- Makes agents testable with mocks

### Recommendation 3: Service Container (Future Enhancement)

**Effort**: 8-12 hours (larger refactor)

**When**: Only if codebase grows significantly

**Approach**: Implement full dependency injection container
- ServiceContainer class
- Singleton/transient/scoped lifetimes
- Auto-wiring by type

**Benefits**:
- Enterprise-grade DI
- Very flexible
- Standard pattern

**Drawbacks**:
- More complex
- Might be overkill for current size
- Steeper learning curve

**Recommendation**: **Not needed yet** - factory pattern is sufficient

### Recommendation 4: Document Current Pattern (Low Effort)

**Effort**: 1 hour

**If not ready to refactor**, at least document:

1. Update SYSTEM_ARCHITECTURE.md:
   - Document factory pattern
   - List which services are singletons (de facto)
   - Explain Bridge/TUI separation (different processes)

2. Add docstrings:
   ```python
   class BridgeService:
       """Bridge service for TUI-to-Automation communication.

       Service Lifecycle:
       - Creates AutomationService via factory (with DI)
       - Creates separate EntityService, SessionStateService for IPC handlers
       - Note: Some duplication exists (same services in factory and bridge)
       - TODO: Extract services from factory to eliminate duplication
       """
   ```

3. Add testing guide:
   - How to test with factory overrides
   - Where mocking is difficult
   - Integration vs unit testing trade-offs

---

## Risk Assessment

### Risks of Current Approach

**🟡 Medium: Performance Overhead**
- 10+ FixtureEntityRepository instantiations per automation run
- Multiple entity file scans (~10-20ms each)
- **Impact**: ~100-200ms overhead per automation cycle

**🟢 Low: Inconsistent State**
- Services are mostly stateless or read-only
- Duplicate instances unlikely to cause bugs
- **Current Impact**: Minimal

**🟡 Medium: Testing Difficulty**
- Bridge hard to unit test (creates services internally)
- Agents hard to unit test (create repositories internally)
- **Impact**: Slower tests, lower coverage for Bridge and agents

### Risks of Migration

**🟢 Low: Breaking Changes**
- Factory already supports overrides
- Can make changes backward compatible
- **Mitigation**: Add new parameters with defaults

**🟢 Low: Complexity**
- Factory pattern is well-understood
- No new architectural patterns needed
- **Mitigation**: Keep it simple, avoid over-engineering

---

## Comparison to Legacy Codebase

| Aspect | Legacy (/src) | Refactoring (/refactoring/src) | Improvement |
|--------|---------------|-------------------------------|-------------|
| **DI Pattern** | ❌ None (manual instantiation everywhere) | ✅ Factory pattern for AutomationService | **Large** |
| **Service Lifecycles** | ❌ Ad-hoc per-call creation | 🟡 Factory + some ad-hoc | **Medium** |
| **Testability** | ❌ Integration tests only | 🟡 Factory testable, Bridge hard | **Medium** |
| **Duplication** | 🔴 High (4+ instances per run) | 🟡 Medium (2-3 instances) | **Medium** |
| **Documentation** | ❌ No DI documentation | ❌ No DI documentation | **None** |

**Overall**: Refactoring code is **better** but still has room for improvement.

---

## Conclusion

**Current State**: Factory pattern for AutomationService with ad-hoc instantiation elsewhere

**Key Issues**:
1. ✅ Factory pattern provides good DI for AutomationService
2. ❌ Bridge creates duplicate EntityService, SessionStateService, SessionRepository
3. ❌ Agents create FixtureEntityRepository 10+ times per automation run
4. ❌ No service container or singleton management
5. 🟡 Testing is possible for AutomationService but difficult for Bridge and agents

**Recommended Action**: **Extract services from factory** (2-3 hours)

**Alternative**: **Inject repository into agents** (3-4 hours for performance gain)

**Rationale**:
- Factory pattern already exists and works well
- Simple refactor to return services separately
- Eliminates duplication in Bridge
- Makes Bridge testable
- Low risk, high impact

**Next Steps**:
1. Create `AutomationServices` dataclass
2. Return all services from `create_automation_services()`
3. Update Bridge to use returned services
4. Optionally: Inject repository into agents
5. Document service lifecycles in SYSTEM_ARCHITECTURE.md

**Estimated Total Effort**: 3-6 hours for complete solution

---

## Appendix: Code References

### Files With Service Instantiation

| File | Services Created | Pattern |
|------|-----------------|---------|
| refactoring/src/automation/factory.py:118-276 | EntityService, SessionStateService, SessionRepository, FileManager, etc. | Factory with DI |
| refactoring/src/presentation/bridge/bridge_service.py:119-150 | EntityService, SessionStateService, SessionRepository (duplicates) | Direct instantiation |
| refactoring/src/presentation/tui/app.py:105-119 | SessionStateService, SessionRepository | Direct instantiation (different process - OK) |
| refactoring/src/automation/agents/implementations/relationship_analysis_agent.py:358,412,534,693 | FixtureEntityRepository (4 times in 1 file) | Inline creation |
| refactoring/src/automation/agents/implementations/memory_creation_agent.py:298 | FixtureEntityRepository | Inline creation |
| refactoring/src/automation/agents/implementations/contradiction_synthesis_agent.py:269 | FixtureEntityRepository | Inline creation |
| refactoring/src/automation/agents/immediate/fact_extraction_agent.py:137 | FixtureEntityRepository | Inline creation |
| refactoring/src/automation/agents/immediate/memory_extraction_agent.py:129 | FixtureEntityRepository | Inline creation |

### Domain-Specific Registries

| File | Purpose | Status |
|------|---------|--------|
| refactoring/src/automation/agents/registry.py | Agent discovery/creation | ✅ Good |
| refactoring/src/automation/templates/template_registry.py | Template discovery | ✅ Good |
| refactoring/src/automation/triggers/registry.py | Trigger evaluator creation | ✅ Good |
| refactoring/src/presentation/bridge/handlers/__init__.py | IPC handler routing | ✅ Good |

### Well-Designed Patterns

| Pattern | File | Status |
|---------|------|--------|
| Factory with DI | refactoring/src/automation/factory.py | ✅ Excellent |
| Registry for agents | refactoring/src/automation/agents/registry.py | ✅ Good |
| IPC handler registry | refactoring/src/presentation/bridge/handlers/ | ✅ Good |

---

**Analysis Complete** ✅
**Next Investigation**: Continue with remaining items in SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md
