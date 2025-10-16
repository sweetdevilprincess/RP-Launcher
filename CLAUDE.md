# RP Claude Code - Project Instructions

This file contains project-wide guidelines for how to work on this codebase. It's automatically loaded and read by Claude Code to understand the system architecture and development standards.

---

## DOCUMENTATION FIRST

This project is **comprehensively documented**. Before making ANY changes, modifications, or additions:

1. **Read the relevant documentation** from the list below
2. **Understand the existing patterns** in the code
3. **Follow the format** used by similar components
4. **Update documentation** as part of your change

**All changes MUST update documentation** - this is not optional.

---

## DOCUMENTATION STRUCTURE

### Primary Documents (Read in This Order)

1. **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - START HERE
   - Navigation hub for all docs
   - Quick lookup tables
   - Task-based navigation
   - "I want to..." guides

2. **[AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md)** - Agent Reference
   - All 10 agents and what they do
   - Agent system behavior (caching, write queue, timeouts, priorities)
   - Orchestration and coordination
   - New agent behavior guidelines

3. **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - System Design
   - Core components and their purposes
   - Complete request/response flow with timeline
   - Data flow diagrams
   - Design patterns used
   - Performance optimization strategies
   - Error handling approaches

4. **[COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md)** - Quick Reference
   - One-page matrix: who reads/writes what
   - State file R/W tracking
   - Entity system tracking
   - IPC communication format
   - Debugging tips
   - Component modification checklist

5. **[SUPPORTING_COMPONENTS.md](SUPPORTING_COMPONENTS.md)** - Infrastructure
   - API clients (Claude, DeepSeek)
   - Configuration system
   - Context and data flow objects
   - Event system
   - Pipeline architecture
   - Prompt building system
   - Performance profiling
   - Setup and initialization
   - Status and time tracking
   - Trigger system (fallback)

6. **[AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md)** - Build Agents
   - Agent architecture and patterns
   - The 5-method template (required for all agents)
   - BaseAgent reference
   - JSON output schemas for every agent type
   - Step-by-step guide to create agents
   - Registration and integration checklist
   - Real code examples
   - Quick reference template (copy-paste to start)
   - Common patterns and snippets
   - Debugging guide

7. **[AUDIT_FINDINGS.md](AUDIT_FINDINGS.md)** - Codebase Health
   - Audit results and findings
   - Legacy code locations
   - Cleanup recommendations
   - Current issues needing decisions

8. **[PROMPT_TEMPLATES_GUIDE.md](PROMPT_TEMPLATES_GUIDE.md)** - Genre Templates
   - 11 built-in genre templates
   - Template structure and JSON format
   - 4 configuration modes
   - How template injection works
   - Creating custom templates
   - Integration with automation system
   - Debugging template issues

---

## WHEN ADDING SOMETHING NEW

### Adding an Agent

**Before writing code:**
1. Read: [AGENT_DOCUMENTATION.md](AGENT_DOCUMENTATION.md) (all sections)
2. Read: [AGENT_DEVELOPMENT_GUIDE.md](AGENT_DEVELOPMENT_GUIDE.md) (all sections)
3. Reference: Real agent examples in `src/automation/agents/`

**While writing code:**
- Use the template from AGENT_DEVELOPMENT_GUIDE.md
- Follow the 5-method pattern (get_agent_id, get_description, gather_data, build_prompt, format_output)
- Use JSON output schemas from AGENT_DEVELOPMENT_GUIDE.md
- Follow naming conventions
- Include comprehensive docstrings

**After writing code:**
- Complete the integration checklist in AGENT_DEVELOPMENT_GUIDE.md
- Update AGENT_DOCUMENTATION.md with new agent entry
- Update COMPONENT_DATA_FLOW.md if data sources/destinations changed
- Update SYSTEM_ARCHITECTURE.md if it affects request/response flow
- Register in AgentFactory
- Add to automation_config.json
- Update CHANGELOG_[DATE_VERSION].md in `/docs/changelogs`

### Adding a Core Component (State File, Manager, System)

**Before writing code:**
1. Read: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - relevant section
2. Read: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md) - see what reads/writes what
3. Check: [AUDIT_FINDINGS.md](AUDIT_FINDINGS.md) - verify not duplicate of something removed

**While writing code:**
- Follow patterns from similar components
- Include comprehensive docstrings
- Handle errors gracefully (never raise exceptions in production pipeline)
- Use FSWriteQueue for file writes (not direct writes)
- Log important operations to hook.log
- Use TypeHints in function signatures

**After writing code:**
- Add documentation entry to SUPPORTING_COMPONENTS.md
- Update SYSTEM_ARCHITECTURE.md if adds/changes core flow
- Update COMPONENT_DATA_FLOW.md to show R/W
- Create example in AGENT_DEVELOPMENT_GUIDE.md common patterns if useful
- Update CHANGELOG_[DATE_VERSION].md

### Adding a State File

**Before:**
1. Check: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md#state-management) - existing state files
2. Check: [COMPONENT_DATA_FLOW.md](COMPONENT_DATA_FLOW.md#state-files---who-reads-and-writes) - who reads/writes

**While:**
- Create template in StateTemplates class
- Document structure with comments
- Plan who will read/write it

**After:**
- Add to StateTemplates documentation
- Add to SYSTEM_ARCHITECTURE.md state management section
- Add to COMPONENT_DATA_FLOW.md state files matrix
- Update CHANGELOG_[DATE_VERSION].md

### Modifying Existing Code

**Before:**
1. Check where it's documented in the docs
2. Understand impact on data flow
3. Check what depends on this component (COMPONENT_DATA_FLOW.md)

**While:**
- Update docstrings if behavior changes
- Update related comments
- Don't change documented behavior without updating docs

**After:**
- Update affected documentation
- Update CHANGELOG_[DATE_VERSION].md with "Fixed", "Changed", or "Improved"

---

## DOCUMENTATION FORMAT REQUIREMENTS

### Consistency Standards

**All documentation must:**

1. **Follow Markdown format** with proper headers (# ## ### ####)
2. **Use consistent terminology** as defined in docs
3. **Include file paths** when referencing code: `src/automation/agents/`
4. **Include line numbers** when relevant: `src/automation/agents/base_agent.py:50`
5. **Include code examples** when explaining functionality
6. **Use tables** for comparisons and quick reference
7. **Use code blocks** with language specified (python, json, etc.)

### Agent Documentation Standards

When adding agent documentation:

1. **Location**: Specify `src/automation/agents/background/` or `immediate/`
2. **What It Does**: Clear description of purpose
3. **Pulls From**: Explicit list of files/data it reads
4. **Sends To**: Explicit list of files/data it writes
5. **JSON Schema**: If background/output, show exact JSON structure
6. **Purpose**: Why it exists, what problem it solves
7. **Configuration**: How to enable/disable, timeout settings, priority

### Component Documentation Standards

When adding component documentation:

1. **Location**: File path in codebase
2. **Purpose**: What problem it solves
3. **Key Methods**: Public API and signatures
4. **Inputs**: What it reads/receives
5. **Outputs**: What it writes/returns
6. **Used By**: Who calls this component
7. **Configuration**: If applicable
8. **Example Usage**: Code showing how to use it

### Changelog Entry Standards

When updating CHANGELOG:

1. **Version Format**: YYYY-MM-DD_X.X.X (date_major.minor.patch)
2. **Categories**: Added, Fixed, Changed, Improved, Removed
3. **Format**: `- [Category] Description of change`
4. **Link to Docs**: Reference updated documentation
5. **Agent Changes**: List which agents added/modified
6. **Breaking Changes**: Flag if behavior changed

---

## VERSION & CHANGELOG

**Current Version**: 1.0.1
**Current Date**: 2025-10-16

**Changelog File**: [CHANGELOG_2025-10-16_1.0.1.md](CHANGELOG_2025-10-16_1.0.1.md)

When creating a new version:
1. Create new CHANGELOG_[DATE_VERSION].md file
2. Update version in this file
3. Document all changes
4. Link previous changelog

**Version History**:
- 1.0.0 - Previous launcher version
- 1.0.1 - Comprehensive documentation suite (current)

---

## DEVELOPMENT WORKFLOW

### Adding an Agent (Complete Workflow)

```
1. Read AGENT_DOCUMENTATION.md
2. Read AGENT_DEVELOPMENT_GUIDE.md
3. Create src/automation/agents/[background|immediate]/agent_name.py
4. Copy template from AGENT_DEVELOPMENT_GUIDE.md
5. Implement 5 methods
6. Register in agent_factory.py
7. Add to automation_config.json
8. Add entry to AGENT_DOCUMENTATION.md
9. Update COMPONENT_DATA_FLOW.md if needed
10. Update SYSTEM_ARCHITECTURE.md if needed
11. Test using guide in AGENT_DEVELOPMENT_GUIDE.md
12. Update CHANGELOG_[DATE_VERSION].md
```

### Adding a Component (Complete Workflow)

```
1. Understand what component does
2. Check SYSTEM_ARCHITECTURE.md for similar components
3. Check COMPONENT_DATA_FLOW.md for data flow implications
4. Write component following patterns of similar components
5. Add comprehensive docstrings
6. Test thoroughly
7. Add documentation to SUPPORTING_COMPONENTS.md
8. Update COMPONENT_DATA_FLOW.md if data flow affected
9. Update SYSTEM_ARCHITECTURE.md if architecture affected
10. Add examples to AGENT_DEVELOPMENT_GUIDE.md if useful pattern
11. Update CHANGELOG_[DATE_VERSION].md
```

### Fixing a Bug

```
1. Find where bug occurs
2. Check relevant documentation
3. Understand what code should do
4. Fix the bug
5. Update docstring if behavior unclear
6. Test fix thoroughly
7. Update CHANGELOG_[DATE_VERSION].md with "Fixed"
```

---

## CLAUDE CODE WORKING SESSION PROTOCOL

**This protocol ensures critical context is preserved during active working sessions with the user.**

### Session Initialization (START OF EVERY SESSION)

When continuing from a previous conversation:
1. **IMMEDIATELY read CLAUDE.md** (this file) - do not wait for user instruction
2. **Read any active CLAUDE.md files** in project-specific directories
3. **Check for session state files**: `state/session_context.md` or similar
4. **Load TodoWrite list** to understand current task state
5. **DO NOT** proceed with work until these are all reviewed

### Critical Information to Always Preserve

**High Priority - ALWAYS keep in context:**
- Current task/goal being worked on
- CLAUDE.md project instructions and guidelines
- File paths and recent modifications
- Decisions already made in this session
- TIER_1 automation files (AUTHOR'S_NOTES.md, STORY_GENOME.md, etc.)
- Active todo list status

**Medium Priority - Preserve when possible:**
- Code snippets from recent edits
- Previous error messages and debugging findings
- Documentation references made
- Verification results

**Can sacrifice if needed:**
- Early exploratory searches (if documented in notes)
- Redundant explanations already given
- Tool output that's been summarized
- Verbose command results

### Context Management During Work

**At regular intervals (approximately every 30 messages or when feeling near limits):**

1. **Proactively signal context concerns:**
   - Inform user: "Context approaching limit, let me create a summary"
   - Create bullet-point summary of:
     - Current task and progress
     - Key decisions made
     - Files modified
     - Next immediate steps
   - Save summary to user or file

2. **Never assume compacting will work:**
   - Don't rely on `/compact` command
   - Assume context will keep growing
   - Plan to preserve information differently

3. **Create hand-offs between message groups:**
   - Before starting new work phase, recap what was done
   - Explicitly state what must be remembered
   - Reference documentation instead of re-explaining

### If Context Gets Too Full

**When approaching limits:**
1. **Create session summary** with:
   - Task completed
   - Task in progress
   - Task pending
   - Critical context (file paths, recent changes, decisions)
   - Command/reference to resume from

2. **Update project files** to reflect current state:
   - Update CHANGELOG for work done
   - Update relevant documentation
   - Commit important context to files the user can reference

3. **Ask user to start new session** with explicit instructions:
   - "Please start a new Claude Code session and say: 'Continue session: [specific task]. Context: [key info].'"

### What To Include In Every Message

- **At start of work task:** Reference current task from todo list
- **At end of work phase:** Summary of what was completed
- **On context signals:** Save information to files or explicit recaps
- **Before major decisions:** Confirm understanding of requirements

### Critical DO's

- ✅ Read CLAUDE.md at session start
- ✅ Read any project CLAUDE.md files
- ✅ Check todo list status
- ✅ Proactively signal context concerns
- ✅ Create summaries before context gets critical
- ✅ Reference files instead of carrying all context
- ✅ Ask for clarification about session continuation

### Critical DON'Ts

- ❌ Assume manual `/compact` will work
- ❌ Wait for user to remind you about context
- ❌ Skip reading CLAUDE.md at session start
- ❌ Miss important context by not checking early
- ❌ Continue working when context is obviously full
- ❌ Lose decisions or progress by relying on conversation alone

---

## CRITICAL GUIDELINES

### DO:
- ✅ Read existing documentation before coding
- ✅ Follow established patterns and conventions
- ✅ Update documentation as part of your change
- ✅ Use consistent naming and formatting
- ✅ Include comprehensive docstrings
- ✅ Handle errors gracefully
- ✅ Log important operations
- ✅ Test before considering done
- ✅ Update CHANGELOG for every significant change

### DON'T:
- ❌ Add code without updating docs
- ❌ Create new patterns when existing ones work
- ❌ Change documented behavior without updating docs
- ❌ Skip the documentation checklist
- ❌ Raise exceptions in pipeline code (handle gracefully)
- ❌ Write to files directly (use FSWriteQueue)
- ❌ Create new state files without templates
- ❌ Ignore test failures
- ❌ Leave code undocumented

---

## DOCUMENTATION MAINTENANCE

### When Something Changes

If you modify documented behavior:

1. Update the documentation immediately
2. Update all affected documents
3. Update CHANGELOG
4. Make documentation and code change in same commit

### Keeping Docs Current

1. **Weekly**: Scan for outdated references
2. **Per Change**: Update docs with code
3. **Monthly**: Audit docs for accuracy
4. **Per Version**: Review complete changelog

---

## FILE LOCATIONS QUICK REFERENCE

### Documentation Files
```
RP_PROJECT/
├── CLAUDE.md                           ← THIS FILE
├── Working Guides/
│   ├── DOCUMENTATION_INDEX.md          ← Start here (navigation hub)
│   ├── AGENT_DOCUMENTATION.md          ← Agent reference
│   ├── SYSTEM_ARCHITECTURE.md          ← System design
│   ├── COMPONENT_DATA_FLOW.md          ← Quick reference
│   ├── SUPPORTING_COMPONENTS.md        ← Infrastructure
│   ├── AGENT_DEVELOPMENT_GUIDE.md      ← Build agents
│   ├── AUDIT_FINDINGS.md               ← Codebase health
│   ├── PROMPT_TEMPLATES_GUIDE.md       ← Genre templates
│   ├── RP_DIRECTORY_MAP.md             ← RP files/interactions
│   ├── LAUNCHER_DOCUMENTATION.md       ← Launcher system (NEW)
│   ├── TUI_BRIDGE_DOCUMENTATION.md     ← Bridge backend (NEW)
│   ├── SETUP_FOLDER_AUDIT.md           ← Setup audit (NEW)
│   └── RP_DIRECTORY_OBSOLESCENCE_AUDIT.md ← RP audit (NEW)
│
└── docs/changelogs/
    └── CHANGELOG_2025-10-16_1.0.1.md   ← Current version changelog
```

### Code Files
```
src/
├── automation/
│   ├── agents/
│   │   ├── background/                 ← Background agents
│   │   ├── immediate/                  ← Immediate agents
│   │   └── base_agent.py              ← Agent base class
│   ├── orchestrator.py                ← V1 (active)
│   ├── agent_coordinator.py           ← Agent orchestration
│   └── ... (other components)
├── file_manager.py                    ← File operations
├── entity_manager.py                  ← Entity management
└── ... (other core files)
```

### State Files
```
state/
├── automation_config.json             ← Agent configuration
├── response_counter.json              ← Response count
├── agent_analysis.json                ← Agent results cache
├── current_state.md                   ← Story state
├── relationships.json                 ← Character relationships
├── plot_threads_master.md             ← Plot threads
├── knowledge_base.md                  ← World facts
├── file_changes.json                  ← File tracking
└── hook.log                           ← Debug logs
```

### Changelogs
```
docs/changelogs
├── CHANGELOG_2025-10-16_1.0.1.md       ← Current changelog
```

---

## KEY PRINCIPLES

### 1. Documentation-Driven Development
- Read docs before coding
- Write code to match docs
- Update docs with code

### 2. Consistency
- Use established patterns
- Follow naming conventions
- Match existing style
- Consistent JSON schemas

### 3. Reliability
- Handle errors gracefully
- Log important operations
- Use FSWriteQueue for writes
- Test thoroughly

### 4. Clarity
- Clear docstrings
- Meaningful variable names
- Comprehensive comments
- Updated documentation

### 5. Maintainability
- Keep components independent
- Follow SOLID principles
- Reuse common patterns
- Document everything

---

## QUICK HELP

**"I need to add an agent"**
→ Read AGENT_DEVELOPMENT_GUIDE.md completely, then follow the step-by-step section

**"I need to understand the flow"**
→ Read SYSTEM_ARCHITECTURE.md#complete-request-response-cycle

**"I need to know who reads/writes X"**
→ Check COMPONENT_DATA_FLOW.md (quick reference tables)

**"I need to see an example"**
→ Real agents in src/automation/agents/[background|immediate]/

**"I need to know how something works"**
→ Check DOCUMENTATION_INDEX.md navigation guide

**"Something doesn't match the docs"**
→ Check AUDIT_FINDINGS.md for known issues

**"I need to start fresh on a component"**
→ Check AGENT_DEVELOPMENT_GUIDE.md#quick-reference-template

---

## THE ONE RULE

**Everything that's built must be documented.**

If it's not documented, it doesn't exist (from a maintenance perspective).

---

**Last Updated**: 2025-10-16 (Added CLAUDE CODE WORKING SESSION PROTOCOL)
**Documentation Version**: 1.0.1
**Status**: Complete and active

For questions, check the DOCUMENTATION_INDEX.md first.

---

## SESSION CONTEXT (Current Working Session)

**Current Session Started**: When continuing from previous conversation
**Last CLAUDE.md Read**: START OF SESSION (mandatory)
**Active Tasks**: See TodoWrite list
**Recent Work**: Template minimization and documentation updates
