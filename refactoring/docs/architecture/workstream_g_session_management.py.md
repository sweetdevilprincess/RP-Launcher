# Workstream G: State & Session Management

**Status:** ✅ Complete
**Version:** 2.0
**Location:** `refactoring/src/domain/sessions/`

## Overview

Workstream G provides comprehensive session management with support for:
- Session lifecycle (create, load, save, archive)
- Message management and updates
- Branching and checkpointing
- Time-tracking and metadata
- Legacy format migration
- Automation write-back integration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Domain Layer                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐   │
│  │   Models     │────→│  Repository  │────→│   Service  │   │
│  │              │     │              │     │            │   │
│  │ SessionData  │     │  CRUD ops    │     │  Enrich    │   │
│  │ SessionMsg   │     │  Branching   │     │  Context   │   │
│  │ Checkpoint   │     │  Archival    │     │            │   │
│  └──────────────┘     └──────────────┘     └────────────┘   │
│                              │                       │        │
│                              │                       │        │
│                       ┌──────┴────────┐            │        │
│                       │  Write-Back   │←───────────┘        │
│                       │               │                      │
│                       │  Agent        │                      │
│                       │  Integration  │                      │
│                       └───────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                        │
                        ↓
            ┌───────────────────────┐
            │  Infrastructure       │
            │  - JsonStore          │
            │  - StatePaths         │
            └───────────────────────┘
```

## Core Components

### 1. Models (`models.py`)

#### SessionMessage
Represents a single conversation turn.

```python
@dataclass
class SessionMessage:
    response_num: int
    timestamp: str
    chapter: int
    user_message: str
    assistant_response: str
    agent_data_background: Dict[str, Any]
    agent_data_immediate: Dict[str, Any]
    model_info: Dict[str, Any]
    status: Optional[str]
```

**Fields:**
- `response_num`: Sequential message number (1-indexed)
- `timestamp`: ISO timestamp of message creation
- `chapter`: Chapter number for RP context
- `user_message`: User's input
- `assistant_response`: AI's response
- `agent_data_background`: Background agent analysis (post-response)
- `agent_data_immediate`: Immediate agent context (pre-response)
- `model_info`: Model metadata (name, tokens, etc.)
- `status`: Optional status indicator

#### SessionCheckpoint
Represents a save-point for branching/restoration.

```python
@dataclass
class SessionCheckpoint:
    checkpoint_id: str
    message_index: int
    timestamp: str
    description: str
    metadata: Dict[str, Any]
```

**Creation:**
```python
checkpoint = SessionCheckpoint.create(
    message_index=42,
    description="Before major decision",
    metadata={"scene": "throne room"}
)
```

#### SessionData
Aggregate session document.

```python
@dataclass
class SessionData:
    session_id: str
    session_type: str  # "active", "branch", "archived"
    parent_session: Optional[str]
    branch_point: Optional[int]
    created: str
    last_modified: str
    current_response: int
    tags: List[str]
    description: str
    rp_metadata: Dict[str, Any]
    messages: List[SessionMessage]
    total_duration_seconds: float  # ✨ NEW in v2
    checkpoints: List[SessionCheckpoint]  # ✨ NEW in v2
```

**Key Methods:**
- `touch()`: Update last_modified timestamp
- `sync_response_count()`: Ensure current_response matches message count
- `validate()`: Enforce invariants

---

### 2. Repository (`repository.py`)

#### SessionRepository
Filesystem-backed session persistence.

**Core Operations:**
```python
def ensure_active_session(rp_name: str, chapter: int) -> SessionData
def load_active_session() -> SessionData
def save_session(session: SessionData) -> None
def append_message(message: SessionMessage) -> SessionData
```

**Discovery:**
```python
def list_sessions(archived: bool, include_branches: bool) -> List[SessionMetadata]
def get_session_metadata(session_id: str) -> Optional[SessionMetadata]
def session_exists(session_id: str) -> bool
```

**Branching:**
```python
def create_branch(
    source_session_id: str,
    branch_name: str,
    branch_point: Optional[int],
    description: str
) -> SessionData

def list_branches(base_session_id: Optional[str]) -> List[SessionMetadata]
```

**Archival:**
```python
def archive_session(session_id: str) -> None
def unarchive_session(session_id: str) -> None
def delete_session(session_id: str, permanent: bool) -> None
```

**Checkpoints:**
```python
def create_checkpoint(
    session_id: str,
    message_index: int,
    description: str,
    metadata: Optional[Dict]
) -> SessionCheckpoint

def restore_checkpoint(session_id: str, checkpoint_id: str) -> SessionData
def list_checkpoints(session_id: str) -> List[SessionCheckpoint]
```

**Directory Structure:**
```
rp_dir/
├── sessions/
│   ├── session_main.json          # Active session
│   └── session_alternate.json     # Other active sessions
├── sessions/branches/
│   ├── session_main_branch_explore_forest.json
│   └── session_main_branch_restore_cp_abc123.json
└── sessions/archived/
    └── session_old_attempt.json
```

---

### 3. Service (`service.py`)

#### SessionService
Enriches AutomationContext with session data.

```python
class SessionService:
    def enrich_session(self, context: AutomationContext) -> AutomationContext:
        """Enrich context with recent session history for prompt."""
```

**Integration with Workstream D:**
- Called by `AutomationService` before prompt assembly
- Adds recent messages to context for Claude
- Maintains separation of concerns (session ↔ automation)

---

### 4. Write-Back (`write_back.py`)

#### SessionWriteBack
Automation-driven session updates.

**Append Messages:**
```python
def append_message(
    user_message: str,
    assistant_response: str,
    chapter: int,
    agent_data_background: Optional[Dict],
    agent_data_immediate: Optional[Dict],
    model_info: Optional[Dict],
    status: Optional[str]
) -> int  # Returns response_num
```

**Update Existing Messages:**
```python
def update_message_content(
    response_num: int,
    updated_user_message: Optional[str],
    updated_assistant_response: Optional[str]
) -> None

def add_agent_data(
    response_num: int,
    background_data: Optional[Dict],
    immediate_data: Optional[Dict],
    merge: bool = True
) -> None

def update_message_status(response_num: int, status: str) -> None
def update_model_info(response_num: int, model_info: Dict) -> None
```

**Usage Example (AgentCoordinator):**
```python
# After background agents complete
write_back.add_agent_data(
    response_num=42,
    background_data={
        "scene_type": "action",
        "pacing": "fast",
        "narrative_analysis": {...}
    },
    merge=True  # Merge with existing data
)
```

---

## Migration from Legacy Formats

### Migration Script (`scripts/migrate_sessions.py`)

**Supported Formats:**

1. **Legacy conversation.json**
   ```json
   {
     "messages": [
       {"user": "...", "assistant": "...", "timestamp": "..."},
       ...
     ],
     "metadata": {"rp_name": "...", "chapter": 1}
   }
   ```

2. **Legacy session_state.json**
   ```json
   {
     "session_id": "...",
     "conversation_history": [...],
     "current_chapter": 1,
     "rp_name": "..."
   }
   ```

3. **Partial v2** (missing `total_duration_seconds`, `checkpoints`)

**Usage:**
```bash
# Single file migration
python scripts/migrate_sessions.py legacy.json --output migrated.json

# Batch migration
python scripts/migrate_sessions.py --batch legacy_dir/ --output-dir sessions/

# With validation
python scripts/migrate_sessions.py legacy.json --validate
```

**Migration Report:**
```
============================================================
MIGRATION SUMMARY
============================================================
Total files processed: 15
Successful migrations: 14
Failed migrations: 1
Skipped files: 0

Errors:
  - corrupt_session.json: Invalid JSON format
============================================================
```

---

## Workflows

### Workflow 1: Basic Session Lifecycle

```python
from refactoring.src.domain.sessions import (
    SessionRepository,
    SessionWriteBack,
)
from refactoring.src.infrastructure.filesystem import StatePaths
from refactoring.src.shared.interfaces import LoggingService

# Setup
paths = StatePaths(rp_dir=Path("/path/to/rp"))
logger = LoggingService()
repo = SessionRepository(paths=paths, logger=logger)
write_back = SessionWriteBack(repository=repo, logger=logger)

# 1. Create session
session = repo.ensure_active_session(rp_name="My RP", chapter=1)

# 2. Append messages
write_back.append_message(
    user_message="You enter the dark forest...",
    assistant_response="The trees loom overhead, their branches...",
    chapter=1,
    agent_data_immediate={"entities": ["Alice"], "scene": "forest"},
)

# 3. Later: add background analysis
write_back.add_agent_data(
    response_num=1,
    background_data={"scene_type": "exploration", "mood": "tense"},
)

# 4. Load for display
session = repo.load_active_session()
for msg in session.messages:
    print(f"[{msg.response_num}] {msg.user_message[:50]}...")
```

### Workflow 2: Branching for "What If" Scenarios

```python
# User at message 10, wants to try different choice

# 1. Create checkpoint
checkpoint = repo.create_checkpoint(
    session_id="main",
    message_index=10,
    description="Before entering the cave",
)

# 2. Continue main timeline
write_back.append_message(
    user_message="I enter the cave cautiously...",
    assistant_response="...",
    chapter=1,
)

# 3. Later: explore alternate choice
branch = repo.create_branch(
    source_session_id="main",
    branch_name="flee_instead",
    branch_point=10,
    description="What if I fled instead?",
)

# Branch is now in sessions/branches/session_main_branch_flee_instead.json
# Can continue adding messages to branch independently
```

### Workflow 3: Checkpoint Restoration

```python
# User wants to go back to checkpoint

# 1. List checkpoints
checkpoints = repo.list_checkpoints("main")
for cp in checkpoints:
    print(f"{cp.checkpoint_id}: {cp.description} (msg {cp.message_index})")

# 2. Restore checkpoint (creates branch)
restored_branch = repo.restore_checkpoint("main", checkpoint.checkpoint_id)

# restored_branch.session_id == "main_branch_restore_cp_abc123"
# restored_branch has messages up to checkpoint only
```

### Workflow 4: Session Archival

```python
# Archive old attempt
repo.archive_session("main_branch_old_attempt")

# List archived sessions
archived = repo.list_sessions(archived=True)
for session_meta in archived:
    print(f"Archived: {session_meta.session_id} ({session_meta.message_count} messages)")

# Restore if needed
repo.unarchive_session("main_branch_old_attempt")

# Permanent deletion
repo.delete_session("main_branch_failed", permanent=True)
```

---

## Integration with Workstream D

### AutomationService Integration

```python
class AutomationService:
    def __init__(
        self,
        *,
        session_service: SessionService,
        session_write_back: SessionWriteBack,
        agent_coordinator: AgentCoordinator,
        ...
    ):
        self.session_service = session_service
        self.write_back = session_write_back
        self.agent_coordinator = agent_coordinator

    def process_turn(self, user_message: str, response_number: int):
        # 1. Load context (includes session history)
        context = self.automation_context.load_context(response_number)
        context = self.session_service.enrich_session(context)

        # 2. Run immediate agents (pre-response)
        prompt_context = self.agent_coordinator.run_immediate_agents(
            message=user_message,
            response_number=response_number,
            ...
        )

        # 3. Generate response (with Claude)
        assistant_response = self.generate_response(user_message, prompt_context)

        # 4. Append to session
        self.write_back.append_message(
            user_message=user_message,
            assistant_response=assistant_response,
            chapter=context.current_chapter,
            agent_data_immediate=json.loads(prompt_context),  # Parse formatted data
        )

        # 5. Run background agents (post-response)
        cache_data = self.agent_coordinator.run_background_agents(
            response_text=assistant_response,
            response_number=response_number,
            ...
        )

        # 6. Update session with background analysis
        self.write_back.add_agent_data(
            response_num=response_number,
            background_data=cache_data,
            merge=True,
        )
```

---

## Testing

### Test Coverage

**Lifecycle Tests** (`test_session_lifecycle.py`):
- Create session end-to-end
- Append messages with write-back
- Checkpoint and restore
- Branch from checkpoint
- Archive and unarchive
- Full lifecycle workflow
- Message updates and agent data

**Branching Tests** (`test_session_branching.py`):
- Create branch at specific point
- Create branch at latest message
- Branch from empty session
- List branches for session
- Branch preserves metadata
- Branch from archived session
- Invalid branch point handling

**Migration Tests** (`test_session_migration.py`):
- Migrate v1 conversation format
- Migrate v1 session state format
- Detect legacy formats
- Batch migration
- Migration validation
- Skip already migrated files

**Run Tests:**
```bash
# All session tests
pytest tests/domain/sessions/ -v

# Specific test file
pytest tests/domain/sessions/test_session_lifecycle.py -v

# Specific test
pytest tests/domain/sessions/test_session_lifecycle.py::TestSessionLifecycle::test_create_session_end_to_end -v
```

---

## Performance Considerations

### Lazy Loading
- `SessionMetadata` provides lightweight queries without loading messages
- Use `list_sessions()` for browsing instead of loading full sessions

### Caching Strategy
- Active session cached in memory by `AutomationService`
- Branches/archived sessions loaded on-demand

### Large Sessions
- Consider splitting into chapters (separate sessions per chapter)
- Archive old chapters when inactive
- Use checkpoints to mark chapter boundaries

---

## API Reference

### SessionData

| Method | Description |
|--------|-------------|
| `from_dict(data)` | Deserialize from JSON |
| `to_dict()` | Serialize to JSON |
| `touch()` | Update last_modified timestamp |
| `sync_response_count()` | Sync current_response with message count |
| `validate()` | Validate invariants |

### SessionRepository

| Method | Description |
|--------|-------------|
| **Core** | |
| `ensure_active_session(rp_name, chapter)` | Get or create active session |
| `load_active_session()` | Load active session |
| `save_session(session)` | Save session to disk |
| `append_message(message)` | Append message to active session |
| **Discovery** | |
| `list_sessions(archived, include_branches)` | List sessions with metadata |
| `get_session_metadata(session_id)` | Get lightweight metadata |
| `session_exists(session_id)` | Check if session exists |
| **Branching** | |
| `create_branch(source, name, point, desc)` | Create branch from session |
| `list_branches(base_session_id)` | List branch sessions |
| **Archival** | |
| `archive_session(session_id)` | Move to archived/ |
| `unarchive_session(session_id)` | Restore from archived/ |
| `delete_session(session_id, permanent)` | Archive or permanently delete |
| **Checkpoints** | |
| `create_checkpoint(session_id, index, desc)` | Create checkpoint |
| `restore_checkpoint(session_id, checkpoint_id)` | Restore as branch |
| `list_checkpoints(session_id)` | List checkpoints |

### SessionWriteBack

| Method | Description |
|--------|-------------|
| `append_message(...)` | Append new message to active session |
| `update_message_content(num, user, assistant)` | Update message text |
| `add_agent_data(num, bg_data, im_data, merge)` | Update agent analysis |
| `update_message_status(num, status)` | Set message status |
| `update_model_info(num, model_info)` | Update model metadata |

---

## Troubleshooting

### Issue: Session validation failed

**Symptom:** `ValueError: Session current_response must match message count`

**Solution:**
```python
session.sync_response_count()
session.save()
```

### Issue: Checkpoint not found

**Symptom:** `ValueError: Checkpoint 'cp_abc123' not found`

**Solution:** List checkpoints to verify ID:
```python
checkpoints = repo.list_checkpoints("main")
for cp in checkpoints:
    print(cp.checkpoint_id, cp.description)
```

### Issue: Cannot archive main session

**Symptom:** `ValueError: Cannot archive the main session`

**Reason:** Main session is special and cannot be archived.

**Solution:** Create a branch and archive the branch instead:
```python
branch = repo.create_branch(source_session_id="main", branch_name="old_main", branch_point=None)
repo.archive_session(branch.session_id)
```

---

## Migration from Existing System

### Step 1: Identify Legacy Sessions

```bash
# Find legacy session files
find /path/to/rp -name "conversation.json" -o -name "session_state.json"
```

### Step 2: Batch Migrate

```bash
python scripts/migrate_sessions.py \
    --batch /path/to/legacy/sessions \
    --output-dir /path/to/rp/sessions \
    --verbose
```

### Step 3: Validate

```bash
# Run validation on migrated files
for file in /path/to/rp/sessions/*.json; do
    python scripts/migrate_sessions.py \
        /path/to/legacy/$(basename $file) \
        --output $file \
        --validate
done
```

### Step 4: Update Application

Update `AutomationService` to use new `SessionWriteBack`:

```python
# Old
self.session_dict["messages"].append({...})

# New
self.write_back.append_message(
    user_message=user_msg,
    assistant_response=ai_resp,
    ...
)
```

---

## Future Enhancements

### Potential Additions

1. **Session Merging**: Merge two branches back into one
2. **Checkpoint Metadata**: Add tags, categories to checkpoints
3. **Session Templates**: Create sessions from templates
4. **Export Formats**: Export to PDF, Markdown, HTML
5. **Search/Filter**: Full-text search across sessions
6. **Session Analytics**: Token usage, duration tracking per session

---

## Summary

Workstream G provides a **robust, production-ready session management system** with:

✅ Complete lifecycle management
✅ Branching and checkpointing for alternate timelines
✅ Time-tracking and metadata support
✅ Legacy format migration
✅ Automation write-back integration
✅ Comprehensive test coverage

**Dependencies:**
- Infrastructure: `JsonStore`, `StatePaths`
- Shared: `LoggingService`

**Integration Points:**
- Workstream D: `SessionService.enrich_session()`, `SessionWriteBack` for agent updates

**File Locations:**
- Source: `refactoring/src/domain/sessions/`
- Tests: `refactoring/tests/domain/sessions/`
- Scripts: `refactoring/scripts/migrate_sessions.py`
- Docs: `refactoring/docs/architecture/workstream_g_session_management.md`
