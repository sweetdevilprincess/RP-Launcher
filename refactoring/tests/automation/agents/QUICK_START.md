# Quick Start - Running Agent Tests

## ✅ Correct Way to Run Tests

**Always run pytest from the PROJECT ROOT:**

```bash
# Navigate to project root first
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"

# Then run pytest
pytest tests/automation/agents/ -v
```

## ❌ Common Mistake

**Don't run from inside the tests directory:**

```bash
# DON'T DO THIS:
cd tests/automation/agents
pytest tests/automation/agents/ -v  # Won't work!
```

## Current Status

✅ Import error FIXED
✅ Structure created
✅ Fixtures created
⏳ No test files yet (that's why you see "0 items collected")

## Next Steps

1. **Create first test file:**
   ```bash
   # From project root
   cd "C:\Users\green\Desktop\RP Claude Code\refactoring"

   # Create test file
   touch tests/automation/agents/section_1_unit/test_agent_catalog.py
   ```

2. **Run tests:**
   ```bash
   pytest tests/automation/agents/section_1_unit/test_agent_catalog.py -v
   ```

## Test What We Have Now

```bash
# From project root
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"

# This should show "0 items collected" (correct - no tests yet)
pytest tests/automation/agents/ -v

# This verifies conftest.py loads correctly
pytest tests/automation/agents/ --collect-only
```

## Ready to Create Tests?

See:
- `docs/AGENT_TESTING_PLAN.md` - Comprehensive guide
- `tests/automation/agents/section_1_unit/README.md` - First section to implement
- `AGENT_TESTING_SUMMARY.md` - Quick overview
