# Critical Guidelines and Principles

**Last Updated**: 2025-10-17
**Purpose**: Core guidelines and key principles for all work on this project

---

## DO's and DON'Ts

### Critical DO's

✅ Read existing documentation before coding
✅ Follow established patterns and conventions
✅ Update documentation as part of your change
✅ Use consistent naming and formatting
✅ Include comprehensive docstrings
✅ Handle errors gracefully
✅ Log important operations
✅ Test before considering done
✅ Update CHANGELOG for every significant change
✅ Read CLAUDE.md at session start
✅ Read any project CLAUDE.md files
✅ Check todo list status
✅ Proactively signal context concerns
✅ Create summaries before context gets critical
✅ Reference files instead of carrying all context
✅ Ask for clarification about session continuation

### Critical DON'Ts

❌ Add code without updating docs
❌ Create new patterns when existing ones work
❌ Change documented behavior without updating docs
❌ Skip the documentation checklist
❌ Raise exceptions in pipeline code (handle gracefully)
❌ Write to files directly (use FSWriteQueue)
❌ Create new state files without templates
❌ Ignore test failures
❌ Leave code undocumented
❌ Assume manual `/compact` will work
❌ Wait for user to remind you about context
❌ Skip reading CLAUDE.md at session start
❌ Miss important context by not checking early
❌ Continue working when context is obviously full
❌ Lose decisions or progress by relying on conversation alone

---

## Key Principles

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

## The One Rule

**Everything that's built must be documented.**

If it's not documented, it doesn't exist (from a maintenance perspective).

---

## Documentation Standards

### Consistency Requirements

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

## When Documentation Changes

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

**Last Updated**: 2025-10-17
**Status**: Active guidelines
