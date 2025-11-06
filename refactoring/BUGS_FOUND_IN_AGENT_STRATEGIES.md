# Bugs Found in Agent Strategy Implementation

**Date:** 2025-10-23
**Discovered During:** Section 2 strategy testing
**Status:** Blocking full test coverage

---

## Bug #1: Invalid `AutomationResult` Parameter

### Location
`src/automation/agents/immediate_agent_strategy.py`

### Lines Affected
- Line 116
- Line 140
- Line 179

### Issue
The `ImmediateAgentStrategy.execute()` method returns `AutomationResult` with an `immediate_agent_context` parameter, but **this parameter doesn't exist** in the `AutomationResult` dataclass.

### Code
```python
# Line 116 - When agents unavailable
return AutomationResult(
    success=True,
    enhanced_prompt=prompt,
    immediate_agent_context="",  # ❌ INVALID PARAMETER
    error="Immediate agents not available (import error)",
)

# Line 140 - When no agents enabled
return AutomationResult(
    success=True, enhanced_prompt=prompt, immediate_agent_context=""  # ❌ INVALID
)

# Line 179 - Success case
return AutomationResult(
    success=True,
    enhanced_prompt=enhanced_prompt,
    immediate_agent_context=agent_context_text,  # ❌ INVALID
)
```

### Actual `AutomationResult` Definition
```python
@dataclass(frozen=True)
class AutomationResult:
    """Outcome of automation execution."""

    success: bool
    enhanced_prompt: str | None = None
    cached_context: str | None = None  # ✅ This exists
    dynamic_prompt: str | None = None
    loaded_entities: list[str] = field(default_factory=list)
    profiler: Any | None = None
    error: str | None = None
    # ❌ immediate_agent_context does NOT exist
```

### Root Cause
Confusion between two different contracts:
1. **AutomationContext** (input) - HAS `immediate_agent_context` field
2. **AutomationResult** (output) - DOES NOT have `immediate_agent_context` field

### How It Should Work

**Flow:**
1. Strategy returns `AutomationResult(cached_context=agent_text)`
2. AgentRunner accumulates `cached_context` from all strategies
3. AutomationService (or caller) takes the `cached_context` and updates `AutomationContext.immediate_agent_context`

**Evidence from `agent_runner.py:72-73`:**
```python
# Accumulate context for final result
if result.cached_context:
    accumulated_cached_context += result.cached_context
```

**Evidence from `agent_runner.py:108`:**
```python
return AutomationResult(
    success=strategies_successful > 0,
    enhanced_prompt=current_prompt,
    cached_context=accumulated_cached_context or None,  # ✅ Uses cached_context
    error=last_failure if strategies_successful == 0 else None,
)
```

### Fix Required
Change all three occurrences from `immediate_agent_context=` to `cached_context=`

```python
# Line 116 - Fixed
return AutomationResult(
    success=True,
    enhanced_prompt=prompt,
    cached_context="",  # ✅ FIXED
    error="Immediate agents not available (import error)",
)

# Line 140 - Fixed
return AutomationResult(
    success=True,
    enhanced_prompt=prompt,
    cached_context=""  # ✅ FIXED
)

# Line 179 - Fixed
return AutomationResult(
    success=True,
    enhanced_prompt=enhanced_prompt,
    cached_context=agent_context_text,  # ✅ FIXED
)
```

---

## Bug #2: Agent Class References Without Availability Check

### Location
`src/automation/agents/immediate_agent_strategy.py:192`
`src/automation/agents/background_agent_strategy.py:184`

### Issue
The `_prepare_agent_tasks()` method references legacy agent classes directly in a dictionary, which causes `NameError` when `AGENTS_AVAILABLE=False`.

### Code
```python
def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type, int]]:
    available_agents = {
        "quick_entity_analysis": QuickEntityAnalysisAgent,  # ❌ NameError if not imported
        "fact_extraction": FactExtractionAgent,
        "memory_extraction": MemoryExtractionAgent,
        "plot_thread_extraction": PlotThreadExtractionAgent,
    }
    # ... rest of method
```

### Root Cause
The agent classes are imported in a try/except block at module level:

```python
try:
    from src.automation.agents import (
        FactExtractionAgent,
        MemoryExtractionAgent,
        # ...
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False  # But names still referenced later!
```

When the import fails, `AGENTS_AVAILABLE=False`, but the agent class names are still referenced in `_prepare_agent_tasks()`, causing `NameError`.

### Why This Breaks Testing
Tests that want to verify the "agents unavailable" path cannot call `_prepare_agent_tasks()` without getting a `NameError`, even though they're not trying to execute agents.

### Fix Options

**Option A: Guard the dictionary creation**
```python
def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type, int]]:
    if not AGENTS_AVAILABLE:
        return []  # Early return if agents not available

    available_agents = {
        "quick_entity_analysis": QuickEntityAnalysisAgent,
        # ...
    }
```

**Option B: Use string-based lookup**
```python
# At module level
_AGENT_CLASSES = {}
if AGENTS_AVAILABLE:
    _AGENT_CLASSES = {
        "quick_entity_analysis": QuickEntityAnalysisAgent,
        # ...
    }

def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type, int]]:
    if not _AGENT_CLASSES:
        return []

    tasks = []
    for agent_id in self._enabled_agents:
        if agent_id in _AGENT_CLASSES:
            # ...
```

**Option C: Use globals() lookup (most flexible)**
```python
def _prepare_agent_tasks(self, agent_context: AgentContext) -> list[tuple[str, type, int]]:
    if not AGENTS_AVAILABLE:
        return []

    agent_class_names = {
        "quick_entity_analysis": "QuickEntityAnalysisAgent",
        # ...
    }

    tasks = []
    for agent_id, class_name in agent_class_names.items():
        agent_class = globals().get(class_name)
        if agent_class and self._enabled_agents.get(agent_id, {}).get("enabled"):
            # ...
```

---

## Impact on Testing

### Tests Blocked
- ❌ Full execution tests for immediate strategy
- ❌ Full execution tests for background strategy
- ❌ Integration tests for AgentRunner
- ❌ End-to-end pipeline tests with agents

### Tests Passing (8 tests)
- ✅ Context transformation
- ✅ Strategy initialization
- ✅ Result formatting (4 tests)
- ✅ Prompt injection (2 tests)

### Coverage Gap
Without fixing these bugs:
- Cannot test agent execution path
- Cannot test timeout handling
- Cannot test concurrent execution
- Cannot test error handling during execution

**Estimated impact:** ~15-20 tests blocked per strategy

---

## Related Issues

### Same Bug in `background_agent_strategy.py`

The background strategy has the same `_prepare_agent_tasks()` issue at line 184:

```python
available_agents = {
    "response_analyzer": ResponseAnalyzerAgent,  # ❌ NameError if not imported
    "memory_creation": MemoryCreationAgent,
    # ...
}
```

**Note:** Background strategy does NOT have the `immediate_agent_context` bug because it correctly uses `enhanced_prompt` only (line 172).

---

## Verification

### How Bugs Were Discovered

1. Created unit tests for `ImmediateAgentStrategy`
2. Tests failed with: `TypeError: AutomationResult.__init__() got an unexpected keyword argument 'immediate_agent_context'`
3. Traced through code to find `AutomationResult` doesn't have this field
4. Found `AgentRunner` uses `cached_context` instead
5. Attempted to test `_prepare_agent_tasks()` with `AGENTS_AVAILABLE=False`
6. Got `NameError: name 'QuickEntityAnalysisAgent' is not defined`

### Test Command to Reproduce
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
pytest tests/automation/agents/section_2_strategies/test_immediate_strategy.py -v
```

### Expected After Fix
- All 17 immediate strategy tests should pass
- Can add execution tests with mocked agents
- Full strategy coverage achievable

---

## Recommendation

**Priority:** HIGH - Blocks test completion

**Fix Order:**
1. Fix Bug #1 (immediate_agent_context → cached_context) - 3 lines
2. Fix Bug #2 (add AGENTS_AVAILABLE guard) - 1 line per strategy
3. Re-run tests to verify fixes
4. Add execution tests with mocked legacy agents

**Estimated Fix Time:** 15 minutes

**Estimated New Test Time:** 2-3 hours (to add execution tests)

---

## Files Requiring Changes

1. `src/automation/agents/immediate_agent_strategy.py`
   - Lines 116, 140, 179 (Bug #1)
   - Line 192+ (Bug #2)

2. `src/automation/agents/background_agent_strategy.py`
   - Line 184+ (Bug #2)

3. **No test changes required** - tests are correct, implementation is wrong
