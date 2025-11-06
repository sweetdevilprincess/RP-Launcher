# Section 2: Strategy Tests

**Status:** 🚧 Not Started
**Target Coverage:** 90%+
**Estimated Time:** 3-4 hours

## Objectives

Test each agent strategy independently with mocked agents:
- ImmediateAgentStrategy - Pre-response context gathering
- BackgroundAgentStrategy - Post-response analysis
- FallbackTriggerStrategy - Legacy trigger system
- AgentRegistry - Strategy creation and configuration
- AgentRunner - Strategy orchestration

## Test Files

- `test_immediate_strategy.py` - ~10 tests
- `test_background_strategy.py` - ~7 tests
- `test_fallback_strategy.py` - ~4 tests
- `test_agent_registry.py` - ~5 tests
- `test_agent_runner.py` - ~5 tests

**Total:** ~60-75 tests

## Running These Tests

```bash
# Run all Section 2 tests
pytest tests/automation/agents/section_2_strategies/ -v

# Specific strategy
pytest tests/automation/agents/section_2_strategies/test_immediate_strategy.py -v

# Without slow tests
pytest tests/automation/agents/section_2_strategies/ -m "not slow" -v
```

## Success Criteria

- [ ] All strategy tests passing
- [ ] 90%+ coverage on ImmediateAgentStrategy
- [ ] 90%+ coverage on BackgroundAgentStrategy
- [ ] 85%+ coverage on FallbackTriggerStrategy
- [ ] 90%+ coverage on AgentRegistry
- [ ] 90%+ coverage on AgentRunner
- [ ] Mock agents working correctly
