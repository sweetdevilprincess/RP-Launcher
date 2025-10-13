# Status Command

Display comprehensive RP system status.

---

## Instructions

Read and display the following information:

### 1. Current State
Read: `state/current_state.md`

Display:
- Current chapter
- Current timestamp
- Current location
- Active plot threads

### 2. Response Counter
Read: `state/response_counter.txt`

Display:
- Total responses this story
- Responses until next arc generation (counter % 50)

### 3. Entity Tracking
Read: `state/entity_tracker.json`

Display:
- Total entities tracked
- List entities with 2+ mentions (show mention count)
- List entities with cards created

### 4. Automation Status
Read: `state/automation_config.json`

Display:
- Entity card auto-generation: ON/OFF (threshold)
- Story arc auto-generation: ON/OFF (frequency)

### 5. Recent Activity
Read: `state/hook.log` (last 20 lines)

Display recent automation activity:
- Entity cards generated
- Story arcs created
- Triggers matched
- Errors (if any)

### 6. Available Files
Display counts:
- Character files in `characters/` (list them)
- Entity files in `entities/` (count only)
- Chapter summaries in `chapters/` (count only)

### 7. Memory Status
Check if `state/user_memory.md` exists

Display:
- Memory file exists: YES/NO
- If yes, show last updated timestamp

---

## Format Output

Format the status report clearly with sections:

```
# 🎭 RP System Status

**Generated**: [Current date/time]

---

## 📍 Current State

**Chapter**: [X]
**Timestamp**: [Story time]
**Location**: [Where]

**Active Plot Threads**:
- [Thread 1]
- [Thread 2]

---

## 📊 Progress

**Total Responses**: [X]
**Next Arc Generation**: [Y] responses away

---

## 🎭 Entities

**Tracked**: [X] entities
**Cards Created**: [Y] cards

**Entities with 2+ mentions**:
- [Entity 1]: [N] mentions [✅ Card Created / ⏳ Pending]
- [Entity 2]: [N] mentions [✅ Card Created / ⏳ Pending]

---

## ⚙️ Automation

✅/❌ **Entity Card Generation**: [ON/OFF] (Threshold: [X] mentions)
✅/❌ **Story Arc Generation**: [ON/OFF] (Every [X] responses)

---

## 🔍 Recent Activity

[Last 5-10 notable events from hook.log]

---

## 📁 Available Files

**Characters**: [X] files
- [Character 1]
- [Character 2]

**Entity Cards**: [X] files
**Chapter Summaries**: [X] files

**Memory**: [✅ Active / ❌ Not created]

---

**Tip**: Keep `CURRENT_STATUS.md` open in a second pane for live updates!
```

---

## Notes

- This command provides a comprehensive snapshot of the RP system
- Use this to understand current state, progress, and configuration
- The `CURRENT_STATUS.md` file is auto-updated every response (lighter version)
- This `/status` command is more detailed (run on-demand)
