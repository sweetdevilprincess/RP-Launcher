# Checkpoint & Retry System - Technical Architecture
## Session Log Approach

**Document Version**: 2.0
**Last Updated**: 2025-10-17
**Status**: Design (Revised)

---

## Executive Summary

**Key Insight**: Retry, checkpoints, and branching are **the same operation** - copying a session log up to a specific response number. Using session logs as the single source of truth dramatically simplifies the architecture and enables all features from day one.

**Architecture Change**: Instead of modifying chapter markdown files, we use JSON session logs that contain:
- Full conversation history
- All agent analyses (embedded)
- Complete context for each response
- Metadata for tagging and searching

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         TUI (Textual)                        │
│  User types: /retry                                          │
│  User types: /branch "romance path"                          │
│  User types: /switch "action path"                           │
└──────────────────────────┬───────────────────────────────────┘
                           │ IPC (JSON files)
┌──────────────────────────▼───────────────────────────────────┐
│                      TUI Bridge                               │
│  All commands use same core operation:                       │
│  SessionManager.copy_session(up_to_response, name, tags)    │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              SessionManager (Core Class)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  copy_session(response_num, name, tags) ← CORE      │   │
│  │  retry() → copy without last response                │   │
│  │  branch(response_num, name, tags) → named copy      │   │
│  │  checkpoint(response_num, name, tags) → saved copy  │   │
│  │  switch(session_name) → load different session      │   │
│  │  list_sessions() → show all available               │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    Session Storage                            │
│  <RP_DIR>/sessions/                                          │
│  ├── session_main.json        ← Active session (PRIMARY)    │
│  ├── branches/                                               │
│  │   ├── session_romance.json  ← Named branch              │
│  │   └── session_action.json   ← Named branch              │
│  └── archived/                                               │
│      ├── retry_20251017_103500.json                         │
│      └── checkpoint_before_choice.json                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Session Log Format

### Complete Session Structure

```json
{
  "session_id": "main",
  "session_type": "active",
  "parent_session": null,
  "branch_point": null,
  "created": "2025-10-15T14:57:25",
  "last_modified": "2025-10-17T10:30:00",
  "current_response": 45,
  "tags": ["main-timeline"],

  "rp_metadata": {
    "rp_name": "Lilith and Silas",
    "chapter": 1,
    "scene": "The Crimson Hour bar"
  },

  "messages": [
    {
      "response_num": 1,
      "timestamp": "2025-10-15T15:00:00",
      "chapter": 1,

      "user_message": "I approach the tattooed stranger at the bar...",

      "assistant_response": "Silas looked up as you approached, his dark eyes meeting yours...",

      "agent_data_background": {
        "scene_analysis": {
          "scene_type": "dialogue",
          "pacing": "medium",
          "tension": 6,
          "variety_score": 8
        },
        "characters_in_scene": ["Lilith", "Silas"],
        "characters_mentioned": [],
        "location": "The Crimson Hour bar",
        "time_passed": "5 minutes",
        "plot_threads": {
          "new": ["First meeting between Lilith and Silas"],
          "mentioned": [],
          "resolved": []
        },
        "memories_created": [
          {
            "character": "Lilith",
            "memory_id": "MEM-001",
            "type": "first_meeting",
            "significance": 8,
            "content": "First approached Silas at The Crimson Hour"
          }
        ],
        "relationship_changes": {
          "Lilith-Silas": {
            "score_change": 5,
            "new_score": 5,
            "tier": "Stranger"
          }
        },
        "knowledge_extracted": [
          "The Crimson Hour has red lighting",
          "Silas has tattoos on his arms and throat"
        ]
      },

      "agent_data_immediate": {
        "entities_to_load": ["Lilith", "Silas"],
        "relevant_memories": [],
        "relevant_plot_threads": ["First meeting between Lilith and Silas"],
        "tier_2_facts": {},
        "tier_3_entities": []
      },

      "model_info": {
        "model": "claude-sonnet-4",
        "temperature": 0.85,
        "tokens_input": 5234,
        "tokens_output": 432,
        "cache_hit": false
      }
    },
    {
      "response_num": 2,
      // ... same structure
    }
  ]
}
```

### Why This Format?

**Single Source of Truth**:
- ✅ LLM reads ONE file for full context
- ✅ Agent data embedded (no separate cache file)
- ✅ Complete history always available
- ✅ Self-contained for archiving

**Perfect for Operations**:
- ✅ Retry = copy messages[:-1]
- ✅ Branch = copy messages[:N]
- ✅ Rollback = load archived session
- ✅ Switch = load different session file

---

## Core Operation: copy_session()

**The ONE operation that powers everything:**

```python
class SessionManager:
    def copy_session(
        self,
        up_to_response: int,
        new_session_name: str,
        session_type: str = "branch",
        tags: List[str] = None,
        description: str = ""
    ) -> Path:
        """Core operation: copy session up to specific response

        Args:
            up_to_response: Last response to include
            new_session_name: Name for new session
            session_type: "branch", "archived", "checkpoint"
            tags: Optional tags for finding later
            description: Optional description

        Returns:
            Path to new session file
        """
        # 1. Load active session
        active = self.load_session("session_main.json")

        # 2. Create new session with messages up to response N
        new_session = {
            "session_id": new_session_name,
            "session_type": session_type,
            "parent_session": "main",
            "branch_point": up_to_response,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "current_response": up_to_response,
            "tags": tags or [],
            "description": description,
            "rp_metadata": active["rp_metadata"].copy(),
            "messages": active["messages"][:up_to_response].copy()
        }

        # 3. Save to appropriate location
        if session_type == "branch":
            path = self.sessions_dir / "branches" / f"session_{new_session_name}.json"
        elif session_type == "archived":
            path = self.sessions_dir / "archived" / f"{new_session_name}.json"
        elif session_type == "checkpoint":
            path = self.sessions_dir / "archived" / f"checkpoint_{new_session_name}.json"

        self.save_session(new_session, path)
        return path
```

**All features use this:**

```python
def retry(self, tags: List[str] = None) -> Path:
    """Retry = branch back 1 response"""
    current = self.get_current_response()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return self.copy_session(
        up_to_response=current - 1,
        new_session_name=f"retry_{timestamp}",
        session_type="archived",
        tags=tags or ["retry"],
        description="Retried response"
    )

def branch(self, response_num: int, branch_name: str,
           tags: List[str] = None, description: str = "") -> Path:
    """Create named branch from specific point"""
    return self.copy_session(
        up_to_response=response_num,
        new_session_name=branch_name,
        session_type="branch",
        tags=tags or [],
        description=description
    )

def checkpoint(self, checkpoint_name: str,
               tags: List[str] = None, description: str = "") -> Path:
    """Save checkpoint at current point"""
    current = self.get_current_response()
    return self.copy_session(
        up_to_response=current,
        new_session_name=checkpoint_name,
        session_type="checkpoint",
        tags=tags or ["checkpoint"],
        description=description
    )
```

---

## Tagging System

### Tag Structure

Each session has optional tags for easy finding:

```json
{
  "session_id": "romance_path",
  "tags": [
    "branch",
    "romance",
    "chapter-2",
    "important-choice"
  ],
  "description": "Exploring romantic relationship with Silas"
}
```

### Tag Commands

```bash
# Create with tags
/retry #rewrite #better-dialogue
/branch "romance" #romance #silas #chapter-2
/checkpoint "before-choice" #important #turning-point

# Search by tags
/sessions tag:romance
/sessions tag:chapter-2
/sessions tag:important

# List all tags
/sessions tags
```

### Auto-Tags

System automatically adds contextual tags:

- `retry` - All retry operations
- `checkpoint` - All manual checkpoints
- `branch` - All named branches
- `chapter-N` - Chapter number at branch point
- `response-N` - Response number at branch point
- `date-YYYYMMDD` - Date created

---

## User Workflows

### Retry Last Response

```
User: /retry
Bridge: Creating retry archive...
Bridge: ✅ Retry ready!
        Response 45 removed.
        Archived to: retry_20251017_103500.json
TUI: [Reloads session_main.json, response 45 gone]

User: [Sends message again]
Bridge: [Generates new response 45]
```

**With Tags**:
```
User: /retry #better-dialogue #rewrite
Bridge: ✅ Retry ready! Tags: better-dialogue, rewrite
```

### Create Named Branch

```
User: /branch "romance path" #romance #exploring-options
Bridge: Creating branch...
Bridge: ✅ Branch created!
        Name: romance_path
        Branched from: Response 45
        Location: sessions/branches/session_romance_path.json
        Tags: romance, exploring-options

        Continue here, or /switch main to return.
TUI: [Still on main session]

User: [Continues on main timeline]

# Later...
User: /switch "romance path"
Bridge: Loading branch...
Bridge: ✅ Switched to: romance_path
        At response 45
TUI: [Reloads session_romance_path.json]

User: [Continues from response 45 on romance branch]
```

### List and Search Sessions

```
User: /sessions
Bridge:
📁 Available Sessions:

  ● session_main.json (Response 50) [active]
    └─ Tags: main-timeline

  Branches:
    session_romance_path.json (Response 48)
    └─ Tags: romance, exploring-options
    └─ "Exploring romantic relationship with Silas"

    session_action_path.json (Response 47)
    └─ Tags: action, high-stakes

  Archived:
    retry_20251017_103500.json (Response 44)
    └─ Tags: retry, better-dialogue

    checkpoint_before_choice.json (Response 40)
    └─ Tags: checkpoint, important, turning-point

---
User: /sessions tag:romance
Bridge:
📁 Sessions tagged "romance":
  session_romance_path.json (Response 48)
```

---

## Integration with Existing Systems

### TUI Display

**Current**: TUI likely displays chat from memory or temp storage

**New**: TUI loads from active session file

```python
# In TUI
class RPClientApp:
    def load_chat_history(self):
        """Load messages from active session"""
        session_file = self.rp_dir / "sessions" / "session_main.json"
        session = json.load(session_file.open())

        for msg in session["messages"]:
            self.add_message_to_chat(
                user=msg["user_message"],
                assistant=msg["assistant_response"],
                response_num=msg["response_num"]
            )
```

### Bridge Response Flow

**Current**: Bridge generates response, sends to TUI

**New**: Bridge appends to session log, TUI reloads

```python
# In bridge
def handle_user_message(message: str):
    # Generate response
    response = orchestrator.run_automation(message)

    # Append to session
    session_manager.append_message(
        user_message=message,
        assistant_response=response,
        agent_data_background=background_results,
        agent_data_immediate=immediate_results
    )

    # TUI automatically reloads session_main.json
```

### Agent System

**Before**: Agents write to separate cache file

**After**: Agents write to session log

```python
# After background agents run
session_manager.update_message_agent_data(
    response_num=current_response,
    field="agent_data_background",
    data=agent_results
)

# Before next response (immediate agents)
session_manager.update_message_agent_data(
    response_num=current_response,
    field="agent_data_immediate",
    data=immediate_results
)
```

---

## File Structure

```
<RP_DIR>/
├── sessions/                       ← PRIMARY DATA STORE
│   ├── session_main.json           ← Active session (source of truth)
│   ├── branches/
│   │   ├── session_romance_path.json
│   │   └── session_action_path.json
│   └── archived/
│       ├── retry_20251017_103500.json
│       ├── retry_20251017_110000.json
│       └── checkpoint_before_choice.json
│
├── chapters/                       ← OPTIONAL (generated for humans)
│   └── chapter_001.md              ← Generated from session periodically
│
└── state/                          ← DERIVED STATE
    ├── response_counter.json       ← Derived from session.current_response
    └── current_state.md             ← Derived from last message
```

**Session log = source of truth**
**Everything else = derived or optional**

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Load session | O(n) JSON parse | <50ms for 100 responses |
| Copy session | O(n) message copy | <100ms for 100 responses |
| Append message | O(1) + write | <50ms |
| Search by tags | O(m) files × O(1) tag check | <100ms for 50 sessions |
| Switch session | O(n) load + UI update | <200ms |

### Space Complexity

**Per Session**:
- Average message: ~5KB (user + response + agent data)
- 100 responses: ~500KB
- 1000 responses: ~5MB

**Storage Growth**:
- Main session: Grows continuously
- Branches: Fixed size at branch point
- Archives: Keep last N (configurable)

**Cleanup Strategy**:
- Delete old retry archives (keep last 10)
- Keep all named branches (user decides)
- Keep all manual checkpoints (user decides)

---

## Migration from Current System

### What Exists Now

- Chapter files with markdown responses
- State files (response_counter.json, current_state.md)
- Agent cache (agent_analysis.json)

### Migration Strategy

**Create session log from existing data**:

```python
def migrate_to_session_log(rp_dir: Path):
    """One-time migration to session log format"""

    # 1. Parse all chapter files
    messages = []
    for chapter_file in (rp_dir / "chapters").glob("*.md"):
        chapter_messages = parse_chapter_markdown(chapter_file)
        messages.extend(chapter_messages)

    # 2. Create initial session
    session = {
        "session_id": "main",
        "session_type": "active",
        "created": datetime.now().isoformat(),
        "current_response": len(messages),
        "tags": ["main-timeline"],
        "messages": messages
    }

    # 3. Save as session_main.json
    save_session(session, rp_dir / "sessions" / "session_main.json")

    # 4. Keep old chapter files as backup
    # (Don't delete - just stop using as primary)
```

---

## Design Decisions

### Why JSON Over Other Formats?

**Options Considered**:
1. JSON
2. SQLite database
3. MessagePack
4. Custom binary format

**Decision**: JSON

**Rationale**:
- ✅ Human-readable (easy debugging)
- ✅ Universal support (Python, JS, etc.)
- ✅ Git-friendly (text diffs work)
- ✅ No dependencies (built-in)
- ✅ Fast enough for typical use (<1000 responses)

**When to Reconsider**: If sessions exceed 10,000 responses, consider SQLite

### Why Embed Agent Data in Session?

**Options Considered**:
1. Separate agent cache file (current)
2. Embed in session log
3. Separate agent database

**Decision**: Embed in session log

**Rationale**:
- ✅ Single file = single source of truth
- ✅ Retry/branch copies everything atomically
- ✅ No synchronization issues
- ✅ Self-contained archives
- ✅ Simpler rollback logic

### Why Single Active Session?

**Options Considered**:
1. Single active session (session_main.json)
2. Multiple active sessions
3. Auto-switching between sessions

**Decision**: Single active session

**Rationale**:
- ✅ Clear which session is "now"
- ✅ Simpler TUI integration
- ✅ Explicit switching (/switch command)
- ✅ Prevents accidental branches

---

## Testing Strategy

**See**: `TESTING.md` for complete test plan

**Key Tests**:
- Session log CRUD operations
- Copy session at various response numbers
- Tag filtering and search
- Session switching with TUI reload
- Agent data preservation
- Large session performance (1000+ responses)

---

## Future Enhancements

### Phase 2 Features (Built-in Already!)

Since core operation handles everything, these are trivial:

- ✅ `/rollback N` - Just load archived session from N responses ago
- ✅ `/branch` - Already implemented
- ✅ `/checkpoint` - Already implemented
- ✅ `/switch` - Already implemented

### Phase 3: UI Integration

- Session list screen in TUI
- Visual branch tree
- Tag management UI
- Session comparison view

### Phase 4+: Advanced Features

- Session diff (compare two sessions)
- Merge sessions (combine branches)
- Session search (full-text)
- Session export (share with others)
- Session analytics (track branches over time)

---

## References

- **Implementation Guide**: `PHASE_1_SESSION_LOGS.md` (to be created)
- **Testing Plan**: `TESTING.md`
- **Main Roadmap**: `ROADMAP.md`

---

**Last Updated**: 2025-10-17
**Version**: 2.0 (Redesigned for session log approach)
**Status**: Design complete, ready for implementation
