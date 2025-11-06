# RP Claude Code - Project Instructions

This file contains project-wide guidelines for working on this codebase. It's automatically loaded and read by Claude Code to understand the system architecture and development standards.

**See also:** Full documentation structure at @Claude Instructions/DOCUMENTATION.md

---

## Getting Started (First Time?)

1. **Understand the project**: @Claude Instructions/PROJECT_STRUCTURE.md
2. **Read the guidelines**: @Claude Instructions/GUIDELINES.md
3. **Learn the workflows**: @Claude Instructions/WORKFLOWS.md
4. **Understand documentation**: @Claude Instructions/DOCUMENTATION.md
5. **For detailed reference**: @Claude Instructions/FILE_REFERENCE.md

---

## The Foundation: Documentation First

This project is **comprehensively documented**. Before making ANY changes:

1. **Read** the relevant documentation
2. **Understand** existing patterns
3. **Follow** the format of similar components
4. **Update** documentation as part of your change

**All changes MUST update documentation** - this is not optional.

**See @Claude Instructions/GUIDELINES.md for critical guidelines.**

---

## Quick Navigation

| Need | Read |
|------|------|
| **Project structure** | @Claude Instructions/PROJECT_STRUCTURE.md |
| **Documentation index** | @Claude Instructions/DOCUMENTATION.md |
| **Critical guidelines** | @Claude Instructions/GUIDELINES.md |
| **Development workflows** | @Claude Instructions/WORKFLOWS.md |
| **Session protocol** | @Claude Instructions/SESSION_PROTOCOL.md |
| **File locations** | @Claude Instructions/FILE_REFERENCE.md |
| **All working guides** | `Working Guides/` folder |

---

## For Specific Tasks

### Adding an Agent

See @Claude Instructions/WORKFLOWS.md#adding-an-agent-complete-workflow

**Quick checklist:**
1. Read `AGENT_DEVELOPMENT_GUIDE.md`
2. Create agent file with 5 required methods
3. Register in `agent_factory.py`
4. Update documentation
5. Update CHANGELOG

### Understanding the System

See @Claude Instructions/DOCUMENTATION.md#primary-documents

**Read in this order:**
1. @Claude Instructions/PROJECT_STRUCTURE.md
2. Working Guides/SYSTEM_ARCHITECTURE.md
3. Working Guides/COMPONENT_DATA_FLOW.md

### Fixing a Bug

See @Claude Instructions/WORKFLOWS.md#fixing-a-bug-complete-workflow

**Quick steps:**
1. Locate the bug
2. Fix it
3. Test thoroughly
4. Update CHANGELOG

### Adding a Component

See @Claude Instructions/WORKFLOWS.md#adding-a-core-component-complete-workflow

**Quick checklist:**
1. Check existing patterns
2. Write component with docstrings
3. Add comprehensive documentation
4. Update affected docs
5. Update CHANGELOG

---

## Working Session Protocol

**See @Claude Instructions/SESSION_PROTOCOL.md for full details**

### At Session Start (MANDATORY)

- [ ] Read CLAUDE.md (key sections)
- [ ] Read @Claude Instructions/SESSION_PROTOCOL.md
- [ ] Check todo list status
- [ ] Understand current task/context

### During Work

- [ ] Update todo list as progress is made
- [ ] Mark tasks completed immediately
- [ ] Signal context concerns early
- [ ] Reference documentation instead of re-explaining

### When Context Approaches Limit

- [ ] Create comprehensive summary
- [ ] Save critical context to files
- [ ] Ask user to start new session with context
- [ ] Provide explicit resume command

---

## Critical Guidelines

**See @Claude Instructions/GUIDELINES.md for complete details**

### DO's

✅ Read existing documentation before coding
✅ Follow established patterns and conventions
✅ Update documentation as part of your change
✅ Handle errors gracefully
✅ Use FSWriteQueue for file writes
✅ Include comprehensive docstrings
✅ Test before considering done
✅ Update CHANGELOG for every significant change

### DON'Ts

❌ Add code without updating docs
❌ Create new patterns when existing ones work
❌ Change documented behavior without updating docs
❌ Raise exceptions in pipeline code (handle gracefully)
❌ Write to files directly (use FSWriteQueue)
❌ Leave code undocumented

---

## The One Rule

**Everything that's built must be documented.**

If it's not documented, it doesn't exist (from a maintenance perspective).

---

## Primary Documentation Files

**See @Claude Instructions/DOCUMENTATION.md for complete structure**

### Must-Read Documents

1. **@Claude Instructions/PROJECT_STRUCTURE.md** - Directory tree and structure
2. **Working Guides/DOCUMENTATION_INDEX.md** - Navigation hub (in Working Guides/)
3. **Working Guides/SYSTEM_ARCHITECTURE.md** - System design
4. **Working Guides/COMPONENT_DATA_FLOW.md** - Data flow reference
5. **Working Guides/AGENT_DOCUMENTATION.md** - All 10 agents
6. **Working Guides/AGENT_DEVELOPMENT_GUIDE.md** - Build agents (5-method template)
7. **Working Guides/SUPPORTING_COMPONENTS.md** - Infrastructure

### Reference Documents

- **Working Guides/AUDIT_FINDINGS.md** - Codebase health and issues
- **Working Guides/PROMPT_TEMPLATES_GUIDE.md** - Genre template system
- **Working Guides/RP_DIRECTORY_MAP.md** - RP file structure

### Current Version

**Version**: 1.1.0
**Date**: 2025-10-17
**Changelog**: `docs/changelogs/CHANGELOG_2025-10-17_1.1.0.md`

---

## File Organization Quick Reference

**See @Claude Instructions/FILE_REFERENCE.md for complete details**

```
Project Root/
├── CLAUDE.md                          ← YOU ARE HERE (imports from Claude Instructions/)
│
├── Claude Instructions/               ← Modular project instructions
│   ├── GUIDELINES.md                  ← Guidelines
│   ├── DOCUMENTATION.md               ← Doc structure
│   ├── WORKFLOWS.md                   ← Development workflows
│   ├── SESSION_PROTOCOL.md            ← Session protocol
│   ├── FILE_REFERENCE.md              ← File locations
│   └── PROJECT_STRUCTURE.md           ← Directory tree
│
├── Working Guides/                    ← All main documentation
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── COMPONENT_DATA_FLOW.md
│   ├── AGENT_DOCUMENTATION.md
│   ├── AGENT_DEVELOPMENT_GUIDE.md
│   └── [10+ more guides]
│
├── src/                               ← Source code
│   ├── automation/                    ← Automation system
│   ├── clients/                       ← API clients
│   └── [core modules]
│
├── config/                            ← Configuration
│   ├── templates/
│   └── guidelines/
│
├── RPs/                               ← Roleplay projects
│   ├── Example RP/
│   ├── Lilith and Silas/
│   └── [other RPs]
│
└── docs/                              ← Documentation
    ├── guides/
    ├── changelogs/
    └── reference/
```

---

## Common Questions

### "Where do I start?"

1. Read @PROJECT_STRUCTURE.md
2. Read @DOCUMENTATION.md
3. For your specific task, check @WORKFLOWS.md

### "What's the system architecture?"

Read Working Guides/SYSTEM_ARCHITECTURE.md

### "How do I add an agent?"

1. Read @WORKFLOWS.md#adding-an-agent-complete-workflow
2. Follow Working Guides/AGENT_DEVELOPMENT_GUIDE.md
3. Use the 5-method template provided

### "Who reads/writes what?"

Check Working Guides/COMPONENT_DATA_FLOW.md

### "I need to understand RP structure"

Read Working Guides/RP_DIRECTORY_MAP.md and @PROJECT_STRUCTURE.md#roleplay-projects-rps

### "Something doesn't match the docs"

Check Working Guides/AUDIT_FINDINGS.md for known issues

### "I'm running low on context"

See @SESSION_PROTOCOL.md#if-context-gets-too-full

---

## Development Standards

**See @GUIDELINES.md for complete standards**

### Code Standards

- Comprehensive docstrings required
- Type hints in function signatures
- Graceful error handling (never raise in pipeline)
- Use FSWriteQueue for file writes
- Log important operations

### Documentation Standards

- Markdown format with proper headers
- File paths and line numbers in references
- Code examples for complex features
- Tables for comparisons
- Consistent terminology

### Changelog Standards

- Version format: YYYY-MM-DD_X.X.X
- Categories: Added, Fixed, Changed, Improved, Removed
- Reference updated documentation
- Flag breaking changes

---

## Where to Find Things

| Question | Answer |
|----------|--------|
| **How do I...?** | See @Claude Instructions/WORKFLOWS.md |
| **Where is...?** | See @Claude Instructions/FILE_REFERENCE.md |
| **How does...work?** | See Working Guides/SYSTEM_ARCHITECTURE.md |
| **What are the rules?** | See @Claude Instructions/GUIDELINES.md |
| **What's the structure?** | See @Claude Instructions/PROJECT_STRUCTURE.md |
| **How do sessions work?** | See @Claude Instructions/SESSION_PROTOCOL.md |

---

## For Help

- **Questions about workflow**: Check @Claude Instructions/WORKFLOWS.md
- **Questions about guidelines**: Check @Claude Instructions/GUIDELINES.md
- **Questions about docs**: Check @Claude Instructions/DOCUMENTATION.md
- **Questions about sessions**: Check @Claude Instructions/SESSION_PROTOCOL.md
- **Questions about files**: Check @Claude Instructions/FILE_REFERENCE.md
- **Questions about structure**: Check @Claude Instructions/PROJECT_STRUCTURE.md

---

## Version & Changelog

**Current Version**: 1.1.0
**Current Date**: 2025-10-17

**To create a new version:**
1. Create new file: `docs/changelogs/CHANGELOG_[DATE_VERSION].md`
2. Update version numbers in relevant files
3. Document all changes using standard format
4. Link to previous changelog

**Version History**:
- 1.0.0 - Previous launcher version
- 1.0.1 - Comprehensive documentation suite
- 1.0.2 - Launcher setup integration
- 1.1.0 - Unified proxy infrastructure and multi-LLM readiness (current)

---

## Key Principles

See @GUIDELINES.md#key-principles for complete details

1. **Documentation-Driven Development** - Read docs before coding
2. **Consistency** - Use established patterns
3. **Reliability** - Handle errors gracefully
4. **Clarity** - Clear docstrings and comments
5. **Maintainability** - Keep components independent

---

## Quick Help

**"I want to add an agent"**
→ @Claude Instructions/WORKFLOWS.md#adding-an-agent-complete-workflow

**"I need to understand the flow"**
→ Working Guides/SYSTEM_ARCHITECTURE.md

**"I need to know who reads/writes X"**
→ Working Guides/COMPONENT_DATA_FLOW.md

**"I need to see an example"**
→ Real agents in `src/automation/agents/`

**"I need to start fresh"**
→ Working Guides/AGENT_DEVELOPMENT_GUIDE.md

**"Something is wrong/unclear"**
→ Working Guides/AUDIT_FINDINGS.md

---

## All Modular Documentation Files

These are organized in the `Claude Instructions/` folder:

- **@Claude Instructions/PROJECT_STRUCTURE.md** - Complete directory tree
- **@Claude Instructions/GUIDELINES.md** - Critical guidelines and principles
- **@Claude Instructions/DOCUMENTATION.md** - Documentation structure and standards
- **@Claude Instructions/WORKFLOWS.md** - Development workflows
- **@Claude Instructions/SESSION_PROTOCOL.md** - Working session protocol
- **@Claude Instructions/FILE_REFERENCE.md** - File locations quick reference

Plus 10+ comprehensive guides in the `Working Guides/` folder.

---

**Last Updated**: 2025-10-17
**Version**: 1.1.0
**Status**: Complete and using modular documentation with imports
**Maintenance**: All changes reference modular docs using @ import syntax

For detailed information on any topic, use the import references above (e.g., @GUIDELINES.md).
