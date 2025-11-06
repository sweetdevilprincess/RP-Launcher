# Development Workflows

**Last Updated**: 2025-10-17
**Purpose**: Step-by-step workflows for common development tasks

---

## Complete Workflows

### Adding an Agent (Complete Workflow)

This is the most common development task. Follow these steps:

```
1. Read @Claude Instructions/DOCUMENTATION.md#adding-an-agent (documentation requirements)
2. Read AGENT_DOCUMENTATION.md (understand agent system)
3. Read AGENT_DEVELOPMENT_GUIDE.md (understand patterns and template)
4. Create src/automation/agents/[background|immediate]/agent_name.py
5. Copy template from AGENT_DEVELOPMENT_GUIDE.md
6. Implement the 5 required methods:
   - get_agent_id()
   - get_description()
   - gather_data()
   - build_prompt()
   - format_output()
7. Register in src/automation/agents/agent_factory.py
8. Add to config/templates/TEMPLATE_automation_config.json
9. Add entry to Working Guides/AGENT_DOCUMENTATION.md
10. Update Working Guides/COMPONENT_DATA_FLOW.md if needed
11. Update Working Guides/SYSTEM_ARCHITECTURE.md if needed
12. Test using guide in AGENT_DEVELOPMENT_GUIDE.md
13. Update docs/changelogs/CHANGELOG_[DATE_VERSION].md
```

**Expected outcome:** New agent registered, documented, and integrated

---

### Adding a Core Component (Complete Workflow)

For new managers, systems, or infrastructure components:

```
1. Understand what component does (clear requirements)
2. Check Working Guides/SYSTEM_ARCHITECTURE.md for similar components
3. Check Working Guides/COMPONENT_DATA_FLOW.md for data flow implications
4. Write component following patterns of similar components
5. Add comprehensive docstrings
6. Use FSWriteQueue for file writes (not direct writes)
7. Handle errors gracefully (never raise in pipeline)
8. Log operations to hook.log
9. Test thoroughly
10. Add documentation to Working Guides/SUPPORTING_COMPONENTS.md
11. Update Working Guides/COMPONENT_DATA_FLOW.md if data flow affected
12. Update Working Guides/SYSTEM_ARCHITECTURE.md if architecture affected
13. Add examples to AGENT_DEVELOPMENT_GUIDE.md if useful pattern
14. Update docs/changelogs/CHANGELOG_[DATE_VERSION].md
```

**Expected outcome:** Component documented and integrated into system

---

### Fixing a Bug (Complete Workflow)

When you encounter a bug:

```
1. Find where bug occurs (identify problem area)
2. Check relevant documentation
3. Understand what code should do (review intent)
4. Fix the bug
5. Update docstring if behavior unclear
6. Test fix thoroughly
7. Update docs/changelogs/CHANGELOG_[DATE_VERSION].md with "Fixed" entry
```

**Expected outcome:** Bug fixed, documented, tested

---

### Adding a State File

When you need to track new state or configuration:

```
1. Check Working Guides/SYSTEM_ARCHITECTURE.md#state-management
2. Check Working Guides/COMPONENT_DATA_FLOW.md#state-files---who-reads-and-writes
3. Plan what will read/write this file
4. Create template in src/state_templates.py (StateTemplates class)
5. Document structure with comments
6. Add to StateTemplates documentation
7. Update Working Guides/SYSTEM_ARCHITECTURE.md state management section
8. Update Working Guides/COMPONENT_DATA_FLOW.md state files matrix
9. Update docs/changelogs/CHANGELOG_[DATE_VERSION].md
```

**Expected outcome:** State file integrated and documented

---

## Quick Decision Checklists

### Before Writing Code

**Always ask these questions:**

- [ ] Did I read the relevant documentation?
- [ ] Does a similar component already exist?
- [ ] Am I following established patterns?
- [ ] What files will I need to update after coding?
- [ ] How will this affect the data flow?

### Before Considering Work Done

**Verify these items:**

- [ ] Code is written and working
- [ ] Docstrings are comprehensive
- [ ] Tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG is updated
- [ ] All referenced docs are current
- [ ] No new exceptions in pipeline code
- [ ] Using FSWriteQueue for file writes

### After Completing Feature

**Final verification:**

- [ ] All affected documentation updated
- [ ] CHANGELOG entry created
- [ ] Code follows established patterns
- [ ] Tests pass
- [ ] No token/context warnings
- [ ] Ready for next task

---

## Common Patterns Reference

### Pattern: Reading/Writing Files

**Use FSWriteQueue:**
```python
from src.fs_write_queue import FSWriteQueue

queue = FSWriteQueue(rp_path)
queue.queue_write(file_path, content)
```

**Don't use direct writes:**
```python
# ❌ WRONG
with open(file_path, 'w') as f:
    f.write(content)
```

### Pattern: Error Handling in Pipeline

**Graceful handling:**
```python
try:
    result = do_something()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return default_value  # Don't raise
```

**Don't propagate exceptions:**
```python
# ❌ WRONG
raise Exception("Something went wrong")
```

### Pattern: Logging Important Operations

**Use logger:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Starting process...")
```

### Pattern: Adding Docstrings

**Required format:**
```python
def my_function(param1: str, param2: int) -> dict:
    """
    Brief description of what function does.

    This function handles X and returns Y. It's used by Z component.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        dict: Description of return value structure

    Raises:
        None (handle errors gracefully)
    """
```

---

## When You Get Stuck

### "I don't know where to start"

1. Read @Claude Instructions/DOCUMENTATION.md - find your task type
2. Follow the relevant workflow above
3. Reference similar components in the codebase
4. Check AGENT_DEVELOPMENT_GUIDE.md for examples

### "I don't know what to update"

1. Check @Claude Instructions/DOCUMENTATION.md#what-docs-get-updated-when
2. Look at recent commits/changelogs to see what was updated
3. Follow the checklist for your task type

### "I need to understand how something works"

1. Check @Claude Instructions/SESSION_PROTOCOL.md (context management)
2. Read Working Guides/SYSTEM_ARCHITECTURE.md (system design)
3. Check Working Guides/COMPONENT_DATA_FLOW.md (who reads/writes what)
4. Look at actual code examples

### "The code doesn't match the docs"

1. Check Working Guides/AUDIT_FINDINGS.md for known issues
2. If it's a recent change, verify documentation was updated
3. Report as a bug to be fixed

---

**Last Updated**: 2025-10-17
**Status**: Active development workflows
