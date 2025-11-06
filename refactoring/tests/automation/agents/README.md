# Agent System Test Suite

**Status:** 📋 Planning Complete - Ready to Implement
**Created:** 2025-10-23
**Target:** 90%+ coverage on 11 agent modules (2,207 LOC)

---

## Quick Reference

### Test Structure

```
tests/automation/agents/
├── conftest.py                  # Shared fixtures
├── section_1_unit/              # Core component unit tests
│   ├── test_agent_catalog.py
│   ├── test_agent_factory.py
│   └── test_agent_formatter.py
├── section_2_strategies/        # Strategy tests
│   ├── test_immediate_strategy.py
│   ├── test_background_strategy.py
│   ├── test_fallback_strategy.py
│   ├── test_agent_registry.py
│   └── test_agent_runner.py
├── section_3_integration/       # Pipeline integration tests
│   ├── test_agent_executor.py
│   ├── test_agent_coordinator.py
│   ├── test_retry_policies.py
│   └── test_concurrent_execution.py
└── section_4_e2e/               # End-to-end tests
    ├── test_agent_pipeline_e2e.py
    ├── test_automation_with_agents.py
    └── test_immediate_to_background.py
```

---

## Quick Start

### Run All Agent Tests

```bash
pytest tests/automation/agents/ -v
```

### Run by Section

```bash
# Section 1: Unit Tests (foundation)
pytest tests/automation/agents/section_1_unit/ -v

# Section 2: Strategy Tests (business logic)
pytest tests/automation/agents/section_2_strategies/ -v

# Section 3: Integration Tests (pipeline)
pytest tests/automation/agents/section_3_integration/ -v

# Section 4: E2E Tests (complete flow)
pytest tests/automation/agents/section_4_e2e/ -v
```

### Run with Coverage

```bash
pytest tests/automation/agents/ --cov=src/automation/agents --cov=src/automation/services --cov-report=html
```

### Run by Marker

```bash
# Unit tests only
pytest tests/automation/agents/ -m "unit" -v

# Integration tests only
pytest tests/automation/agents/ -m "integration" -v

# E2E tests only
pytest tests/automation/agents/ -m "e2e" -v

# Exclude slow tests
pytest tests/automation/agents/ -m "not slow" -v
```

---

## Implementation Order

### ✅ Phase 0: Setup (COMPLETE)
- [x] Create folder structure
- [x] Create conftest.py with shared fixtures
- [x] Create README files for each section
- [x] Create main planning document

### 🚧 Phase 1: Section 1 - Unit Tests (NEXT)
**Estimated Time:** 2-3 hours

- [ ] `test_agent_catalog.py` - 9 tests
- [ ] `test_agent_factory.py` - 6 tests
- [ ] `test_agent_formatter.py` - 7 tests

**Start Command:**
```bash
pytest tests/automation/agents/section_1_unit/test_agent_catalog.py -v
```

### 🔜 Phase 2: Section 2 - Strategy Tests
**Estimated Time:** 3-4 hours

- [ ] `test_immediate_strategy.py` - 10 tests
- [ ] `test_background_strategy.py` - 7 tests
- [ ] `test_fallback_strategy.py` - 4 tests
- [ ] `test_agent_registry.py` - 5 tests
- [ ] `test_agent_runner.py` - 5 tests

### 🔜 Phase 3: Section 3 - Integration Tests
**Estimated Time:** 3-4 hours

- [ ] `test_agent_executor.py` - 8 tests
- [ ] `test_agent_coordinator.py` - 8 tests
- [ ] `test_retry_policies.py` - 5 tests
- [ ] `test_concurrent_execution.py` - 5 tests

### 🔜 Phase 4: Section 4 - E2E Tests
**Estimated Time:** 2-3 hours

- [ ] `test_agent_pipeline_e2e.py` - 5 tests
- [ ] `test_automation_with_agents.py` - 5 tests
- [ ] `test_immediate_to_background.py` - 3 tests

---

## Coverage Targets

| Module | Target | Section |
|--------|--------|---------|
| agent_catalog.py | 95% | 1 |
| agent_factory.py | 95% | 1 |
| agent_formatter.py | 95% | 1 |
| immediate_agent_strategy.py | 90% | 2 |
| background_agent_strategy.py | 90% | 2 |
| fallback_trigger_strategy.py | 85% | 2 |
| registry.py | 90% | 2 |
| agent_runner.py | 90% | 2 |
| agent_executor.py | 85% | 3 |
| agent_coordinator.py | 85% | 3 |
| Full Pipeline | 80% | 4 |

**Overall Target:** 90%+ across all agent modules

---

## Key Documentation

- **Main Plan:** `docs/AGENT_TESTING_PLAN.md` (comprehensive guide)
- **Section 1:** `tests/automation/agents/section_1_unit/README.md`
- **Section 2:** `tests/automation/agents/section_2_strategies/README.md`
- **Section 3:** `tests/automation/agents/section_3_integration/README.md`
- **Section 4:** `tests/automation/agents/section_4_e2e/README.md`

---

## Shared Fixtures

All tests have access to fixtures in `conftest.py`:
- `stub_logger` - Logging mock
- `sample_immediate_metadata` - Immediate agent metadata
- `sample_background_metadata` - Background agent metadata
- `sample_automation_context` - Automation context
- `sample_agent_context` - Agent context
- `mock_agent_factory` - Create mock agents

---

## Notes

- **Current Status:** Agent system has 0% test coverage
- **Smoke Test Issue:** `test_automation_smoke.py` disables agents (`agents_enabled: False`)
- **Legacy Agents:** Immediate/Background strategies import from old codebase (not refactored yet)
- **Testing Strategy:** Use mocks in Sections 1-2, partial mocks in Section 3, real components in Section 4

---

## Success Criteria

- ✅ 120-140 new agent tests created
- ✅ 90%+ coverage on agent system
- ✅ All 567+ tests passing (existing + new)
- ✅ Agent pipeline validated end-to-end
- ✅ Ready for release
