# Documentation Structure and Standards

**Last Updated**: 2025-10-17
**Purpose**: Documentation organization, structure, and navigation guide

---

## Before Making ANY Changes

**DOCUMENTATION FIRST**

This project is **comprehensively documented**. Before making ANY changes, modifications, or additions:

1. **Read the relevant documentation** from the list below
2. **Understand the existing patterns** in the code
3. **Follow the format** used by similar components
4. **Update documentation** as part of your change

**All changes MUST update documentation** - this is not optional.

---

## Primary Documents (Read in This Order)

### 0. @Claude Instructions/PROJECT_STRUCTURE.md
Project Reference
- Complete directory tree and structure
- File organization and purposes
- Component locations
- Quick navigation guide

### 1. [DOCUMENTATION_INDEX.md](Working%20Guides/DOCUMENTATION_INDEX.md)
START HERE - Navigation hub for all docs
- Navigation hub for all docs
- Quick lookup tables
- Task-based navigation
- "I want to..." guides

### 2. [AGENT_DOCUMENTATION.md](Working%20Guides/AGENT_DOCUMENTATION.md)
Agent Reference
- All 10 agents and what they do
- Agent system behavior (caching, write queue, timeouts, priorities)
- Orchestration and coordination
- New agent behavior guidelines

### 3. [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md)
System Design
- Core components and their purposes
- Complete request/response flow with timeline
- Data flow diagrams
- Design patterns used
- Performance optimization strategies
- Error handling approaches

### 4. [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md)
Quick Reference
- One-page matrix: who reads/writes what
- State file R/W tracking
- Entity system tracking
- IPC communication format
- Debugging tips
- Component modification checklist

### 5. [SUPPORTING_COMPONENTS.md](Working%20Guides/SUPPORTING_COMPONENTS.md)
Infrastructure
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

### 6. [AGENT_DEVELOPMENT_GUIDE.md](Working%20Guides/AGENT_DEVELOPMENT_GUIDE.md)
Build Agents
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

### 7. [AUDIT_FINDINGS.md](Working%20Guides/AUDIT_FINDINGS.md)
Codebase Health
- Audit results and findings
- Legacy code locations
- Cleanup recommendations
- Current issues needing decisions

### 8. [PROMPT_TEMPLATES_GUIDE.md](Working%20Guides/PROMPT_TEMPLATES_GUIDE.md)
Genre Templates
- 11 built-in genre templates
- Template structure and JSON format
- 4 configuration modes
- How template injection works
- Creating custom templates
- Integration with automation system
- Debugging template issues

---

## What Docs Get Updated When?

### Adding an Agent

**Before writing code:**
1. Read: @Claude Instructions/DOCUMENTATION.md#agent-documentation
2. Read: [AGENT_DEVELOPMENT_GUIDE.md](Working%20Guides/AGENT_DEVELOPMENT_GUIDE.md) (all sections)
3. Reference: Real agent examples in `src/automation/agents/`

**While writing code:**
- Use the template from AGENT_DEVELOPMENT_GUIDE.md
- Follow the 5-method pattern (get_agent_id, get_description, gather_data, build_prompt, format_output)
- Use JSON output schemas from AGENT_DEVELOPMENT_GUIDE.md
- Follow naming conventions
- Include comprehensive docstrings

**After writing code:**
- Complete the integration checklist in AGENT_DEVELOPMENT_GUIDE.md
- Update [AGENT_DOCUMENTATION.md](Working%20Guides/AGENT_DOCUMENTATION.md) with new agent entry
- Update [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md) if data sources/destinations changed
- Update [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md) if it affects request/response flow
- Register in AgentFactory
- Add to automation_config.json
- Update CHANGELOG_[DATE_VERSION].md in `/docs/changelogs`

### Adding a Core Component (State File, Manager, System)

**Before writing code:**
1. Read: [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md) - relevant section
2. Read: [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md) - see what reads/writes what
3. Check: [AUDIT_FINDINGS.md](Working%20Guides/AUDIT_FINDINGS.md) - verify not duplicate of something removed

**While writing code:**
- Follow patterns from similar components
- Include comprehensive docstrings
- Handle errors gracefully (never raise exceptions in production pipeline)
- Use FSWriteQueue for file writes (not direct writes)
- Log important operations to hook.log
- Use TypeHints in function signatures

**After writing code:**
- Add documentation entry to [SUPPORTING_COMPONENTS.md](Working%20Guides/SUPPORTING_COMPONENTS.md)
- Update [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md) if adds/changes core flow
- Update [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md) to show R/W
- Create example in [AGENT_DEVELOPMENT_GUIDE.md](Working%20Guides/AGENT_DEVELOPMENT_GUIDE.md) common patterns if useful
- Update CHANGELOG_[DATE_VERSION].md

### Adding a State File

**Before:**
1. Check: [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md#state-management) - existing state files
2. Check: [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md#state-files---who-reads-and-writes) - who reads/writes

**While:**
- Create template in StateTemplates class
- Document structure with comments
- Plan who will read/write it

**After:**
- Add to StateTemplates documentation
- Add to [SYSTEM_ARCHITECTURE.md](Working%20Guides/SYSTEM_ARCHITECTURE.md) state management section
- Add to [COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md) state files matrix
- Update CHANGELOG_[DATE_VERSION].md

### Modifying Existing Code

**Before:**
1. Check where it's documented in the docs
2. Understand impact on data flow
3. Check what depends on this component ([COMPONENT_DATA_FLOW.md](Working%20Guides/COMPONENT_DATA_FLOW.md))

**While:**
- Update docstrings if behavior changes
- Update related comments
- Don't change documented behavior without updating docs

**After:**
- Update affected documentation
- Update CHANGELOG_[DATE_VERSION].md with "Fixed", "Changed", or "Improved"

---

## VERSION & CHANGELOG

**Current Version**: 1.0.2
**Current Date**: 2025-10-16

**Changelog File**: [CHANGELOG_2025-10-16_1.0.2.md](docs/changelogs/CHANGELOG_2025-10-16_1.0.2.md)

When creating a new version:
1. Create new CHANGELOG_[DATE_VERSION].md file
2. Update version in CLAUDE.md and this file
3. Document all changes
4. Link previous changelog

**Version History**:
- 1.0.0 - Previous launcher version
- 1.0.1 - Comprehensive documentation suite
- 1.0.2 - Launcher setup integration (current)

---

**Last Updated**: 2025-10-17
**Status**: Active documentation standards
