# Agent System Testing Plan

**Status:** 📋 Planning
**Date Created:** 2025-10-23
**Target Completion:** 1 week
**Current Coverage:** 0% → Target: 90%+

---

## Executive Summary

The agent system (11 modules, 2,207 LOC) currently has **ZERO test coverage**. This plan outlines a systematic 4-section approach to achieve comprehensive test coverage, organized by complexity and dependencies.

**Key Issue:** The existing smoke test DISABLES agents (`agents_enabled: False`), so we've never actually tested the agent pipeline end-to-end.

---

## Architecture Overview

### Two-Level System

```
┌─────────────────────────────────────────────────────────┐
│ STRATEGY LEVEL (Workstream D)                           │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ AgentRegistry│  │ AgentRunner  │  │ 3 Strategies │ │
│  │              │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│ INDIVIDUAL AGENT LEVEL (Workstream E)                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         AgentCoordinator (Facade)                 │  │
│  └──────────┬───────────────────────────────────────┘  │
│             │                                           │
│    ┌────────┼────────────┬─────────────┬──────────┐   │
│    ↓        ↓            ↓             ↓          ↓   │
│  Catalog  Factory   Executor      Formatter   Retry   │
└───────────────────────────────────────────────────────────┘
```

### 3 Agent Strategies

1. **ImmediateAgentStrategy** - Pre-response context gathering (3-5s)
2. **BackgroundAgentStrategy** - Post-response analysis (async)
3. **FallbackTriggerStrategy** - Legacy trigger system compatibility

---

## Test Organization Structure

```
tests/
└── automation/
    ├── agents/                           # NEW: Agent system tests
    │   ├── __init__.py
    │   ├── conftest.py                   # Shared fixtures
    │   │
    │   ├── section_1_unit/               # SECTION 1: Core Components
    │   │   ├── __init__.py
    │   │   ├── test_agent_catalog.py
    │   │   ├── test_agent_factory.py
    │   │   ├── test_agent_formatter.py
    │   │   └── README.md
    │   │
    │   ├── section_2_strategies/         # SECTION 2: Strategy Tests
    │   │   ├── __init__.py
    │   │   ├── test_immediate_strategy.py
    │   │   ├── test_background_strategy.py
    │   │   ├── test_fallback_strategy.py
    │   │   ├── test_agent_registry.py
    │   │   ├── test_agent_runner.py
    │   │   └── README.md
    │   │
    │   ├── section_3_integration/        # SECTION 3: Pipeline Integration
    │   │   ├── __init__.py
    │   │   ├── test_agent_executor.py
    │   │   ├── test_agent_coordinator.py
    │   │   ├── test_retry_policies.py
    │   │   ├── test_concurrent_execution.py
    │   │   └── README.md
    │   │
    │   └── section_4_e2e/                # SECTION 4: End-to-End
    │       ├── __init__.py
    │       ├── test_agent_pipeline_e2e.py
    │       ├── test_automation_with_agents.py
    │       ├── test_immediate_to_background.py
    │       └── README.md
    │
    └── test_automation_smoke.py          # EXISTING: Update to enable agents
```

---

## Section 1: Core Component Unit Tests

**Goal:** Test individual components in isolation with mocks
**Priority:** HIGHEST (foundation for all other tests)
**Estimated Time:** 2-3 hours
**Target Coverage:** 95%+

### Components to Test

#### 1.1 AgentCatalog
**File:** `src/automation/services/agent_catalog.py`
**Tests:** `tests/automation/agents/section_1_unit/test_agent_catalog.py`

**Test Cases:**
- [ ] `test_register_agent_success` - Register agent with metadata
- [ ] `test_register_duplicate_agent_error` - Duplicate agent_id rejection
- [ ] `test_get_registered_agent` - Retrieve registered agent
- [ ] `test_get_nonexistent_agent_returns_none` - Missing agent handling
- [ ] `test_list_agents_by_type` - Filter by IMMEDIATE/BACKGROUND
- [ ] `test_list_agents_by_priority` - Sort by priority (1-10)
- [ ] `test_get_enabled_agents_only` - Filter enabled agents
- [ ] `test_unregister_agent` - Remove agent from catalog
- [ ] `test_catalog_isolation` - Multiple catalogs don't interfere

**Fixtures Needed:**
```python
@pytest.fixture
def sample_agent_metadata():
    return AgentMetadata(
        agent_id="test_agent",
        description="Test agent",
        agent_type=AgentType.IMMEDIATE,
        priority=5,
        timeout_seconds=3.0,
        enabled=True
    )
```

#### 1.2 AgentFactory
**File:** `src/automation/services/agent_factory.py`
**Tests:** `tests/automation/agents/section_1_unit/test_agent_factory.py`

**Test Cases:**
- [ ] `test_create_agent_from_class` - Factory creates agent instance
- [ ] `test_create_agent_with_params` - Pass rp_dir, log_file correctly
- [ ] `test_create_agent_invalid_class_raises_error` - Error handling
- [ ] `test_create_multiple_agents` - Multiple instances don't interfere
- [ ] `test_factory_uses_catalog_metadata` - Reads from catalog
- [ ] `test_factory_respects_enabled_flag` - Skip disabled agents

**Mock Strategy:**
- Mock agent classes (don't need real agents)
- Verify constructor called with correct params

#### 1.3 AgentFormatter
**File:** `src/automation/services/agent_formatter.py`
**Tests:** `tests/automation/agents/section_1_unit/test_agent_formatter.py`

**Test Cases:**
- [ ] `test_format_immediate_results_to_prompt` - Format for prompt injection
- [ ] `test_format_background_results_to_json` - Format for cache storage
- [ ] `test_format_empty_results` - Handle no results gracefully
- [ ] `test_format_with_errors` - Include error messages
- [ ] `test_format_preserves_agent_metadata` - Include agent_id, duration
- [ ] `test_format_multiple_agents` - Combine multiple results
- [ ] `test_format_with_balance_errors` - Handle API quota errors specially

**Expected Outputs:**
```python
# Immediate format (for prompt)
"""
<!-- AGENT CONTEXT: quick_entity_analysis -->
- Entity: Alice
- Relevance: High
- Duration: 245ms
<!-- END AGENT CONTEXT -->
"""

# Background format (for cache)
{
    "agent_id": "memory_extraction",
    "timestamp": "2025-10-23T12:00:00Z",
    "success": true,
    "content": {...},
    "duration_ms": 1234
}
```

### Running Section 1 Tests

```bash
# Run all Section 1 tests
pytest tests/automation/agents/section_1_unit/ -v

# Run with coverage
pytest tests/automation/agents/section_1_unit/ --cov=src/automation/services --cov-report=html

# Run specific component
pytest tests/automation/agents/section_1_unit/test_agent_catalog.py -v

# Run with markers
pytest tests/automation/agents/section_1_unit/ -m "unit" -v
```

---

## Section 2: Strategy Tests

**Goal:** Test each agent strategy independently
**Priority:** HIGH (core business logic)
**Estimated Time:** 3-4 hours
**Target Coverage:** 90%+

### Components to Test

#### 2.1 ImmediateAgentStrategy
**File:** `src/automation/agents/immediate_agent_strategy.py`
**Tests:** `tests/automation/agents/section_2_strategies/test_immediate_strategy.py`

**Test Cases:**
- [ ] `test_create_context_from_automation_context` - Context transformation
- [ ] `test_execute_with_enabled_agents` - Run enabled agents only
- [ ] `test_execute_with_timeout` - Respect timeout limits (3-5s)
- [ ] `test_execute_concurrent_agents` - ThreadPoolExecutor usage
- [ ] `test_execute_handles_agent_failure` - Continue on individual failure
- [ ] `test_execute_returns_enhanced_prompt` - Inject context into prompt
- [ ] `test_execute_respects_priority_order` - Sort by priority
- [ ] `test_execute_with_no_enabled_agents` - Graceful no-op
- [ ] `test_execute_with_api_rate_limit` - Handle balance errors
- [ ] `test_timeout_kills_slow_agents` - Hard timeout enforcement

**Mock Strategy:**
```python
class MockImmediateAgent:
    def run(self, context):
        return {"entity": "Alice", "relevance": "high"}
```

#### 2.2 BackgroundAgentStrategy
**File:** `src/automation/agents/background_agent_strategy.py`
**Tests:** `tests/automation/agents/section_2_strategies/test_background_strategy.py`

**Test Cases:**
- [ ] `test_execute_background_agents` - Async execution
- [ ] `test_execute_with_longer_timeout` - Background gets more time
- [ ] `test_execute_returns_cache_data` - JSON format for storage
- [ ] `test_execute_does_not_block_response` - Non-blocking
- [ ] `test_execute_concurrent_background_agents` - Parallel execution
- [ ] `test_execute_with_retry_policy` - Use BACKGROUND_RETRY_POLICY
- [ ] `test_execute_handles_multiple_failures` - Resilience

#### 2.3 FallbackTriggerStrategy
**File:** `src/automation/agents/fallback_trigger_strategy.py`
**Tests:** `tests/automation/agents/section_2_strategies/test_fallback_strategy.py`

**Test Cases:**
- [ ] `test_fallback_when_no_agents_enabled` - Trigger system activation
- [ ] `test_fallback_loads_triggered_files` - Legacy tier3 loading
- [ ] `test_fallback_returns_empty_if_triggers_disabled` - Respects config
- [ ] `test_fallback_integrates_with_trigger_coordinator` - Use existing triggers

#### 2.4 AgentRegistry
**File:** `src/automation/agents/registry.py`
**Tests:** `tests/automation/agents/section_2_strategies/test_agent_registry.py`

**Test Cases:**
- [ ] `test_create_strategies_with_agents_enabled` - Creates immediate + background
- [ ] `test_create_strategies_with_agents_disabled` - Creates fallback only
- [ ] `test_create_strategies_respects_config` - Read agents.immediate/background
- [ ] `test_create_strategies_ordering` - Correct execution order
- [ ] `test_should_use_agents_logic` - Decision logic for agents vs fallback

#### 2.5 AgentRunner
**File:** `src/automation/services/agent_runner.py`
**Tests:** `tests/automation/agents/section_2_strategies/test_agent_runner.py`

**Test Cases:**
- [ ] `test_run_executes_all_strategies_in_order` - Sequential execution
- [ ] `test_run_accumulates_results` - Combine strategy outputs
- [ ] `test_run_continues_on_strategy_failure` - Resilience
- [ ] `test_run_with_no_strategies` - Returns original prompt
- [ ] `test_run_enhances_prompt_progressively` - Each strategy adds to prompt

### Running Section 2 Tests

```bash
# Run all Section 2 tests
pytest tests/automation/agents/section_2_strategies/ -v

# Run specific strategy
pytest tests/automation/agents/section_2_strategies/test_immediate_strategy.py -v

# Run with slow test marker
pytest tests/automation/agents/section_2_strategies/ -m "not slow" -v
```

---

## Section 3: Integration Tests

**Goal:** Test pipeline integration with real concurrency and retry
**Priority:** HIGH (verifies components work together)
**Estimated Time:** 3-4 hours
**Target Coverage:** 85%+

### Components to Test

#### 3.1 AgentExecutor
**File:** `src/automation/services/agent_executor.py`
**Tests:** `tests/automation/agents/section_3_integration/test_agent_executor.py`

**Test Cases:**
- [ ] `test_execute_agents_concurrently` - ThreadPoolExecutor integration
- [ ] `test_execute_with_retry_policy` - Retry on failure
- [ ] `test_execute_respects_max_workers` - Thread pool size
- [ ] `test_execute_times_out_slow_agents` - Timeout enforcement
- [ ] `test_execute_collects_stats` - AgentExecutionStats tracking
- [ ] `test_execute_handles_agent_exception` - Exception handling
- [ ] `test_execute_with_balance_error` - API rate limit detection
- [ ] `test_execute_cancels_on_timeout` - Cancel running futures

**Integration Points:**
- Real ThreadPoolExecutor (not mocked)
- Real RetryPolicy (from infrastructure.retry)
- Mock agents with configurable delays

#### 3.2 AgentCoordinator
**File:** `src/automation/services/agent_coordinator.py`
**Tests:** `tests/automation/agents/section_3_integration/test_agent_coordinator.py`

**Test Cases:**
- [ ] `test_register_and_run_immediate_agents` - Full pipeline
- [ ] `test_register_and_run_background_agents` - Background flow
- [ ] `test_coordinator_uses_catalog` - AgentCatalog integration
- [ ] `test_coordinator_uses_factory` - AgentFactory integration
- [ ] `test_coordinator_uses_executor` - AgentExecutor integration
- [ ] `test_coordinator_uses_formatter` - AgentFormatter integration
- [ ] `test_coordinator_writes_cache_file` - agent_analysis.json persistence
- [ ] `test_coordinator_reads_cache_file` - Load previous results

**Setup:**
```python
@pytest.fixture
def agent_coordinator(tmp_path):
    return AgentCoordinator(
        rp_dir=tmp_path,
        log_file=tmp_path / "test.log",
        logger=StubLogger(),
        immediate_workers=2,
        background_workers=3
    )
```

#### 3.3 Retry Policy Integration
**Tests:** `tests/automation/agents/section_3_integration/test_retry_policies.py`

**Test Cases:**
- [ ] `test_agent_retry_policy_2_attempts` - AGENT_RETRY_POLICY (2 max)
- [ ] `test_background_retry_policy_3_attempts` - BACKGROUND_RETRY_POLICY (3 max)
- [ ] `test_retry_with_exponential_backoff` - Backoff strategy
- [ ] `test_retry_logs_attempts` - Logging integration
- [ ] `test_retry_respects_exception_filter` - Only retry certain exceptions

### Running Section 3 Tests

```bash
# Run all Section 3 tests
pytest tests/automation/agents/section_3_integration/ -v

# Run with integration marker
pytest tests/automation/agents/section_3_integration/ -m "integration" -v

# Run with timeout (these tests may be slower)
pytest tests/automation/agents/section_3_integration/ -v --timeout=60
```

---

## Section 4: End-to-End Tests

**Goal:** Test complete automation pipeline with agents enabled
**Priority:** CRITICAL (validates everything works together)
**Estimated Time:** 2-3 hours
**Target Coverage:** Full pipeline

### Components to Test

#### 4.1 Full Agent Pipeline
**Tests:** `tests/automation/agents/section_4_e2e/test_agent_pipeline_e2e.py`

**Test Cases:**
- [ ] `test_full_pipeline_with_immediate_agents` - Context → Agents → Prompt
- [ ] `test_full_pipeline_with_background_agents` - Response → Agents → Cache
- [ ] `test_full_pipeline_immediate_then_background` - Complete flow
- [ ] `test_pipeline_with_real_agent_classes` - Use actual agent implementations
- [ ] `test_pipeline_with_mock_llm_client` - End-to-end without API calls

#### 4.2 Automation Service Integration
**Tests:** `tests/automation/agents/section_4_e2e/test_automation_with_agents.py`

**Test Cases:**
- [ ] `test_automation_service_with_agents_enabled` - Update smoke test
- [ ] `test_automation_creates_agent_registry` - Factory integration
- [ ] `test_automation_runs_immediate_agents_before_llm` - Timing
- [ ] `test_automation_runs_background_agents_after_llm` - Post-processing
- [ ] `test_automation_handles_agent_failures_gracefully` - Resilience

**Configuration:**
```python
config_data = {
    "version": "1.0.0",
    "agents": {
        "immediate": {
            "quick_entity_analysis": {
                "enabled": True,
                "timeout_seconds": 3.0
            }
        },
        "background": {
            "memory_extraction": {
                "enabled": True,
                "timeout_seconds": 10.0
            }
        }
    }
}
```

### Running Section 4 Tests

```bash
# Run all E2E tests
pytest tests/automation/agents/section_4_e2e/ -v

# Run E2E with markers
pytest tests/automation/agents/section_4_e2e/ -m "e2e" -v

# Run slow E2E tests (may take several seconds)
pytest tests/automation/agents/section_4_e2e/ -m "e2e and slow" -v --timeout=120
```

---

## Test Execution Strategy

### Phase 1: Setup (Day 1)
1. Create folder structure
2. Create `conftest.py` with shared fixtures
3. Create stub test files with TODOs
4. Write Section 1 README

### Phase 2: Unit Tests (Day 2)
1. Implement Section 1 tests
2. Run and achieve 95%+ coverage
3. Fix any issues discovered
4. Document findings

### Phase 3: Strategy Tests (Day 3-4)
1. Implement Section 2 tests
2. Run and achieve 90%+ coverage
3. Test with various configurations
4. Document edge cases

### Phase 4: Integration Tests (Day 5)
1. Implement Section 3 tests
2. Test concurrent execution
3. Test retry mechanisms
4. Verify pipeline integration

### Phase 5: E2E Tests (Day 6)
1. Implement Section 4 tests
2. Update smoke test to enable agents
3. Test complete automation flow
4. Verify all components working together

### Phase 6: Validation (Day 7)
1. Run full test suite
2. Generate coverage report
3. Fix any remaining issues
4. Update documentation

---

## Coverage Targets

| Section | Component | Target | Priority |
|---------|-----------|--------|----------|
| 1 | AgentCatalog | 95% | HIGH |
| 1 | AgentFactory | 95% | HIGH |
| 1 | AgentFormatter | 95% | HIGH |
| 2 | ImmediateAgentStrategy | 90% | HIGH |
| 2 | BackgroundAgentStrategy | 90% | HIGH |
| 2 | FallbackTriggerStrategy | 85% | MEDIUM |
| 2 | AgentRegistry | 90% | HIGH |
| 2 | AgentRunner | 90% | HIGH |
| 3 | AgentExecutor | 85% | HIGH |
| 3 | AgentCoordinator | 85% | HIGH |
| 4 | Full Pipeline | 80% | CRITICAL |

**Overall Target:** 90%+ coverage across all 11 agent modules

---

## Pytest Configuration

**Add to `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests for isolated components",
    "integration: Integration tests for component interaction",
    "e2e: End-to-end tests for complete pipeline",
    "slow: Tests that take >1 second",
    "agents: Agent system tests",
]
```

---

## Shared Fixtures

**`tests/automation/agents/conftest.py`:**

```python
"""Shared fixtures for agent system tests."""

import pytest
from pathlib import Path
from refactoring.src.automation.contracts import (
    AgentMetadata,
    AgentType,
    AgentContext,
    AutomationContext
)
from refactoring.src.shared.interfaces import LoggingService

class StubLogger(LoggingService):
    """Stub logger for testing."""
    def debug(self, message: str, *, context: dict = None) -> None: pass
    def info(self, message: str, *, context: dict = None) -> None: pass
    def warning(self, message: str, *, context: dict = None) -> None: pass
    def error(self, message: str, *, context: dict = None) -> None: pass
    def exception(self, message: str, *, context: dict = None, exc: BaseException = None) -> None: pass

@pytest.fixture
def stub_logger():
    return StubLogger()

@pytest.fixture
def sample_immediate_metadata():
    return AgentMetadata(
        agent_id="test_immediate",
        description="Test immediate agent",
        agent_type=AgentType.IMMEDIATE,
        priority=5,
        timeout_seconds=3.0,
        enabled=True
    )

@pytest.fixture
def sample_background_metadata():
    return AgentMetadata(
        agent_id="test_background",
        description="Test background agent",
        agent_type=AgentType.BACKGROUND,
        priority=7,
        timeout_seconds=10.0,
        enabled=True
    )

@pytest.fixture
def sample_automation_context(tmp_path):
    return AutomationContext(
        message="Test message",
        rp_dir=tmp_path,
        response_count=1,
        loaded_entities=["Alice", "Bob"],
    )

@pytest.fixture
def sample_agent_context():
    return AgentContext(
        message="Test message",
        response_number=1,
        characters_in_scene=["Alice"],
        loaded_entities=["Alice", "Bob"],
    )
```

---

## Success Criteria

### Section 1 Complete
- ✅ 25-30 unit tests passing
- ✅ 95%+ coverage on Catalog, Factory, Formatter
- ✅ All components tested in isolation
- ✅ Documentation updated

### Section 2 Complete
- ✅ 60-75 strategy tests passing
- ✅ 90%+ coverage on all strategies
- ✅ Registry and Runner fully tested
- ✅ Mock agents working correctly

### Section 3 Complete
- ✅ 30-35 integration tests passing
- ✅ 85%+ coverage on Executor, Coordinator
- ✅ Retry policies validated
- ✅ Concurrency tested

### Section 4 Complete
- ✅ 15-20 E2E tests passing
- ✅ Full pipeline validated
- ✅ Smoke test updated with agents enabled
- ✅ Complete flow working

### Final Success
- ✅ **ALL 567+ tests passing** (original + new agent tests)
- ✅ **90%+ coverage** on agent system
- ✅ **Agent pipeline working** end-to-end
- ✅ **Documentation complete** for all sections
- ✅ **Ready for release**

---

## Notes

- **Legacy Agent Import:** `immediate_agent_strategy.py` imports from old `src/automation/agents` (line 19-24). These are NOT refactored yet. We'll test with mocks first, then can add real agent tests later.

- **Mock vs Real:** Sections 1-2 use mocks, Section 3 uses partial mocks, Section 4 uses real components (with mock LLM client).

- **Parallel Execution:** Sections 1 and 2 are mostly independent and could be worked in parallel if needed.

- **Time Estimates:** Based on ~30 tests/hour with setup, debugging, and documentation.
