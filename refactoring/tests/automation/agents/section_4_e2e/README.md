# Section 4: End-to-End Tests

**Status:** 🚧 Not Started
**Target Coverage:** 80%+ (full pipeline)
**Estimated Time:** 2-3 hours

## Objectives

Test complete automation pipeline with agents enabled:
- Full agent pipeline (Registry → Runner → Strategies → Agents)
- AutomationService integration with agents
- Immediate to background agent flow
- Complete automation lifecycle with real components

## Test Files

- `test_agent_pipeline_e2e.py` - ~5 tests
- `test_automation_with_agents.py` - ~5 tests
- `test_immediate_to_background.py` - ~3 tests

**Total:** ~15-20 E2E tests

## Running These Tests

```bash
# Run all E2E tests
pytest tests/automation/agents/section_4_e2e/ -v

# With E2E marker
pytest tests/automation/agents/section_4_e2e/ -m "e2e" -v

# Slow E2E tests (may take several seconds)
pytest tests/automation/agents/section_4_e2e/ -m "e2e and slow" -v --timeout=120
```

## Success Criteria

- [ ] All E2E tests passing
- [ ] Full pipeline validated end-to-end
- [ ] Smoke test updated with agents enabled
- [ ] AutomationService creates agent pipeline correctly
- [ ] Immediate agents run before LLM call
- [ ] Background agents run after LLM response
- [ ] Complete flow working with mock LLM
