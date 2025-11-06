# Claude Code Working Session Protocol

**Last Updated**: 2025-10-17
**Purpose**: Ensure critical context is preserved during active working sessions

---

## Session Initialization (START OF EVERY SESSION)

When continuing from a previous conversation or starting new work:

### Mandatory First Actions

1. **IMMEDIATELY read CLAUDE.md** (or at least understand its sections)
2. **Skim this file** (SESSION_PROTOCOL.md) - you're reading it now
3. **Check for session state files**
4. **Load TodoWrite list** to understand current task state
5. **DO NOT** proceed with work until these are all reviewed

### Setting Context

- **Read project instructions first**: @CLAUDE.md (or key sections)
- **Check active tasks**: What was I working on?
- **Understand documentation structure**: Where are the docs?
- **Review recent changes**: What was just modified?

---

## Critical Information to Always Preserve

### High Priority - ALWAYS Keep in Context

These are the most important things to preserve:

- **Current task/goal** being worked on
- **CLAUDE.md** project instructions and guidelines
- **File paths** and recent modifications
- **Decisions** already made in this session
- **TIER_1 automation files**: AUTHOR'S_NOTES.md, STORY_GENOME.md, etc.
- **Active todo list** status

### Medium Priority - Preserve When Possible

These are valuable but can be sacrificed if needed:

- **Code snippets** from recent edits
- **Previous error messages** and debugging findings
- **Documentation references** made
- **Verification results**

### Can Sacrifice if Context Full

These can be dropped if absolutely necessary:

- **Early exploratory searches** (if documented in notes)
- **Redundant explanations** already given
- **Tool output** that's been summarized
- **Verbose command results**

---

## Context Management During Work

### Monitor Context Usage

**Periodically check context usage** (approximately every 30 messages or when feeling near limits):

1. **Be aware** of how much context you're using
2. **Signal early** if approaching limits
3. **Create summaries** proactively before crisis

### Proactive Context Signaling

When approaching limits:

1. **Inform user**: "Context approaching limit, let me create a summary"
2. **Create bullet-point summary** of:
   - Current task and progress
   - Key decisions made
   - Files modified
   - Next immediate steps
3. **Save summary** to user or file

### Create Hand-Offs Between Message Groups

**Before starting new work phase:**

1. **Recap** what was just done
2. **Explicitly state** what must be remembered
3. **Reference documentation** instead of re-explaining
4. **Update files** to capture important context

---

## If Context Gets Too Full

### When Approaching Limits

If you're running low on context:

1. **Create session summary** with:
   - Task completed
   - Task in progress
   - Task pending
   - Critical context (file paths, recent changes, decisions)
   - Command/reference to resume from

2. **Update project files** to reflect current state:
   - Update CHANGELOG for work done
   - Update relevant documentation
   - Commit important context to files user can reference

3. **Ask user to start new session** with explicit instructions:
   - "Please start a new Claude Code session and say: 'Continue session: [specific task]. Context: [key info].'"

---

## What To Include In Every Message

### At Start of Work Task

- Reference current task from todo list
- Acknowledge what was done previously
- Understand context and state

### At End of Work Phase

- Summary of what was completed
- What remains to be done
- Any blockers encountered

### On Context Signals

- Save information to files or explicit recaps
- Update documentation
- Create summaries

### Before Major Decisions

- Confirm understanding of requirements
- Ask for clarification if uncertain
- Document assumptions made

---

## Critical DO's

For working sessions to be effective:

✅ Read CLAUDE.md at session start
✅ Read any project CLAUDE.md files
✅ Check todo list status
✅ Proactively signal context concerns
✅ Create summaries before context gets critical
✅ Reference files instead of carrying all context
✅ Ask for clarification about session continuation
✅ Update files with session progress
✅ Create clear hand-offs between phases

---

## Critical DON'Ts

Avoid these mistakes:

❌ Assume manual `/compact` will work
❌ Wait for user to remind you about context
❌ Skip reading CLAUDE.md at session start
❌ Miss important context by not checking early
❌ Continue working when context is obviously full
❌ Lose decisions or progress by relying on conversation alone
❌ Forget to update todo list as progress is made
❌ Leave work in undocumented state

---

## Working with TodoWrite

### Use Todo List For

- **Tracking progress** on complex tasks
- **Breaking down** large work into steps
- **Maintaining state** between context limits
- **Communicating** what's done/pending to user
- **Resuming work** after context resets

### Todo Status States

- **pending**: Task not yet started
- **in_progress**: Currently working on (limit to ONE at a time)
- **completed**: Task finished successfully

### Best Practices

1. **Create todos at start** of complex work
2. **Mark in_progress** BEFORE starting a task
3. **Mark completed** IMMEDIATELY after finishing
4. **Never batch completions** - do it task by task
5. **Update with progress** - don't wait for end of session
6. **Use descriptive names** - make it clear what's being done

---

## Session Types and Contexts

### Starting Fresh (New Session)

```
1. Read CLAUDE.md (or key sections)
2. Understand @Claude Instructions/PROJECT_STRUCTURE.md
3. Review @Claude Instructions/DOCUMENTATION.md
4. Clarify task with user
5. Create todo list if needed
6. Begin work
```

### Continuing Work (Same Session)

```
1. Acknowledge what was done
2. Note current state
3. Check todo list
4. Continue from next task
5. Update progress
```

### Resuming After Context Limit (New Session, Same Task)

```
1. User provides: "Continue session: [task]. Context: [key info]."
2. Read session summary from previous context
3. Load or review any saved context files
4. Verify understanding
5. Create new todo list
6. Continue work
```

### Context Crisis (Run Out of Space)

```
1. Create comprehensive summary
2. Save to file or provide to user
3. Ask user to start new session
4. Provide explicit resume command
```

---

## Quick Reference Commands

### For User to Provide Context

Use this format when starting a new session or after context limit:

```
Continue session: [Task Name]
Context: [Key information like file paths, recent decisions, what's left to do]
```

### For Assistant (You) to Signal Context

Use this when approaching limit:

```
Context approaching limit. Creating summary:
- Completed: [what was done]
- In Progress: [current task]
- Remaining: [what's left]
- Critical Files: [paths modified]
- Resume Command: Please start new session and say: "Continue session: [task name]"
```

---

## Example: Good Session Flow

```
1. [User]: "Add authentication to the system"
2. [Assistant]: Reads CLAUDE.md, checks docs, creates todo list
3. [Assistant]: Works on task, updates todo list with progress
4. [Assistant after 45 messages]: "Context approaching limit. Summary:"
5. [Assistant]: Saves context to file
6. [User]: Starts new session, says "Continue: Add authentication"
7. [Assistant]: Reads saved context, continues work
8. [Assistant]: Completes all todos, updates CHANGELOG
9. [Assistant]: "Task complete. All changes documented."
```

---

## Documentation for Your Session

**Important files to reference:**
- @CLAUDE.md - Main project instructions
- @Claude Instructions/GUIDELINES.md - Critical guidelines
- @Claude Instructions/DOCUMENTATION.md - Doc structure
- @Claude Instructions/WORKFLOWS.md - Development workflows
- @Claude Instructions/FILE_REFERENCE.md - File locations
- @Claude Instructions/SESSION_PROTOCOL.md - This file

---

**Last Updated**: 2025-10-17
**Status**: Active session protocol
