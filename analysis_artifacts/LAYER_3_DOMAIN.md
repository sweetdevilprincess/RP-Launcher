# Domain Layer Analysis

**Layer:** Domain (`refactoring/src/domain/`)
**Purpose:** Business logic and domain models (entities, sessions)
**File Count:** 14 Python files
**Total Lines:** 3,155 lines
**Analysis Date:** Phase 2.2

---

## Layer Organization

### Subsystems (2 total)

1. **entities/** - Entity management (characters, locations, items, orgs)
2. **sessions/** - Session and chat history management

---

## Complete File Inventory

### 1. Entities Subsystem (7 files, ~1,400 lines)

| File | Lines | Purpose | Used By |
|------|-------|---------|---------|
| `entities/__init__.py` | 51 | Exports | All |
| `entities/models.py` | 23 | EntityCard data model | Parser, Service |
| `entities/entity_parser.py` | 191 | Parse entity markdown files | Repository |
| `entities/entity_repository.py` | 481 | Entity persistence (fixture-based) | Service |
| `entities/entity_service.py` | 490 | High-level entity operations | BridgeService, Automation |
| `entities/fixtures.py` | 50 | Fixture entity repository impl | Repository |
| `entities/preference_generator.py` | 165 | Generate entity preferences | Service (optional) |

#### Key Classes:

**Models (entity_parser.py):**
- `CharacterEntity` - Character data with personality, relationships
- `LocationEntity` - Location/setting information
- `OrganizationEntity` - Faction/group data
- `ItemEntity` - Object/artifact information
- `MemoryLog` - Character memory storage

**EntityCard (models.py):**
```python
@dataclass
class EntityCard:
    name: str
    entity_type: EntityType
    file_path: Path
    triggers: list[str]
    full_content: str
    personality_core: str | None
    metadata: dict[str, Any]
    sections: dict[str, str]
```

**FixtureEntityRepository (entity_repository.py):**
- Loads entities from JSON fixtures
- Provides CRUD operations
- Used instead of direct markdown parsing (performance)

**EntityService (entity_service.py):**
- **Purpose:** High-level entity API for automation
- **Key Methods:**
  - `list_characters()`, `list_locations()`, etc.
  - `get_character(name)` - Retrieve single character
  - `detect_mentions(text)` - Find entities mentioned in text
  - `get_characters_in_scene()` - Characters currently active
  - `stats()` - Entity statistics
  - `generate_preferences(context)` - Create entity preferences

**PreferenceGenerator (preference_generator.py):**
- Generates scene preferences based on entities
- Used by automation for context

#### Dependencies:
- `infrastructure.templates.StateTemplateService` - Entity templates
- `shared.models.EntityType` - Entity type enum
- `infrastructure.filesystem` - File I/O

#### Used By:
- `BridgeService._initialize_services()` - Creates EntityService
- `create_automation_service()` - Injects into automation
- Agents - Access entity data

---

### 2. Sessions Subsystem (7 files, ~1,755 lines)

| File | Lines | Purpose | Used By |
|------|-------|---------|---------|
| `sessions/__init__.py` | 18 | Exports | All |
| `sessions/models.py` | 220 | Session data models | All session code |
| `sessions/repository.py` | 671 | Session persistence (filesystem) | Service, Bridge, TUI |
| `sessions/service.py` | 153 | High-level session operations | Bridge, Automation |
| `sessions/write_back.py` | 254 | Session write operations | Bridge |
| `sessions/chatlog_organizer.py` | 387 | Chatlog file organization | Bridge |

#### Key Classes:

**Models (models.py):**

**SessionMessage:**
```python
@dataclass
class SessionMessage:
    response_num: int
    timestamp: str
    chapter: int
    user_message: str
    assistant_response: str
    agent_data_background: dict[str, Any]
    agent_data_immediate: dict[str, Any]
    model_info: dict[str, Any]
    status: str | None
```

**SessionCheckpoint:**
```python
@dataclass
class SessionCheckpoint:
    checkpoint_id: str
    message_index: int
    timestamp: str
    description: str
    metadata: dict[str, Any]
```

**SessionData:**
```python
@dataclass
class SessionData:
    session_id: str
    session_type: str
    parent_session: str | None
    branch_point: int | None
    created: str
    last_modified: str
    current_response: int
    tags: list[str]
    description: str
    rp_metadata: dict[str, Any]
    messages: list[SessionMessage]
    total_duration_seconds: float
    checkpoints: list[SessionCheckpoint]
```

**SessionRepository (repository.py):**
- **Purpose:** Persist/load session documents
- **Storage:** JSON files in `{rp_dir}/sessions/`
- **Key Methods:**
  - `load_active_session()` - Load current session
  - `save_session(session)` - Persist session
  - `append_message(message)` - Add message to session
  - `list_all_sessions()` - Get all sessions
  - `create_branch(from_message, description)` - Branch timeline
  - `switch_to_branch(session_id)` - Change active session
  - `archive_session(session_id)` - Move to archive

**Active Session Tracking:**
- File: `{rp_dir}/sessions/.active` (symlink or pointer)
- Points to current session (main or branch)

**SessionService (service.py):**
- **Purpose:** High-level session business logic
- **Key Methods:**
  - `get_current_session()` - Get active session
  - `add_exchange(user_msg, assistant_msg)` - Add conversation
  - `update_timeline(...)` - Update session metadata

**SessionWriteBack (write_back.py):**
- **Purpose:** Deferred session writes
- **Pattern:** Batch writes to avoid file thrashing
- **Key Methods:**
  - `schedule_write(session)` - Queue write
  - `flush()` - Force write

**ChatlogOrganizer (chatlog_organizer.py):**
- **Purpose:** Organize chat logs by chapter/scene
- **Output:** Markdown files in `{rp_dir}/logs/chatlogs/`
- **Key Methods:**
  - `organize_by_chapter()` - Split into chapter files
  - `organize_by_scene()` - Split into scene files
  - `export_markdown(session)` - Generate readable chatlog

#### Dependencies:
- `infrastructure.filesystem.JsonStore` - JSON persistence
- `infrastructure.filesystem.StatePaths` - Path utilities
- `infrastructure.sessions.SessionStateService` - Session state

#### Used By:
- `BridgeService._initialize_services()` - Creates SessionRepository, WriteBack, Organizer
- `RPClientApp.__init__()` - Creates SessionRepository for chat history
- `create_automation_service()` - Injects SessionService
- TUI - Loads chat history on startup

---

## Domain Layer Dependencies Graph

```
DOMAIN LAYER

entities/
  ├─> models.py (leaf - data structures)
  ├─> entity_parser.py → models
  ├─> entity_repository.py → parser, fixtures
  ├─> fixtures.py (implementation)
  ├─> preference_generator.py → parser
  └─> entity_service.py → all above + templates

sessions/
  ├─> models.py (leaf - data structures)
  ├─> repository.py → models, JsonStore, StatePaths
  ├─> service.py → repository, models
  ├─> write_back.py → repository
  └─> chatlog_organizer.py → repository, models

External Dependencies:
  ├─> infrastructure.filesystem (StatePaths, JsonStore, MarkdownStore)
  ├─> infrastructure.templates (StateTemplateService)
  ├─> infrastructure.sessions (SessionStateService)
  └─> shared.models (EntityType, etc.)
```

---

## Runtime Usage Analysis

### Entities Subsystem Usage

**Instantiated By:**
- `create_automation_service()` (factory.py:224):
  ```python
  entity_repository = FixtureEntityRepository(
      rp_dir=rp_dir,
      session_state_service=session_state_service,
  )
  entity_service = EntityService(
      repository=entity_repository,
      templates=template_service,
      logger=logger,
      session_state=session_state_service,
      rp_dir=rp_dir,
  )
  ```

**Used By:**
- Automation agents (via AutomationContext)
- Prompt builder (entity mentions, in-scene characters)
- TUI entity manager

### Sessions Subsystem Usage

**Instantiated By (Multiple Locations):**

1. **BridgeService** (bridge_service.py:136-150):
   ```python
   paths = StatePaths(rp_dir=self.rp_dir)
   self.session_repository = SessionRepository(
       paths=paths,
       logger=self.logger,
       session_state_service=self.session_state_service
   )
   self.session_writeback = SessionWriteBack(
       repository=self.session_repository,
       logger=self.logger
   )
   self.chatlog_organizer = ChatlogOrganizer(
       paths=paths,
       logger=self.logger,
       repository=self.session_repository
   )
   ```

2. **RPClientApp** (app.py:115-119):
   ```python
   self.session_repository = SessionRepository(
       paths=paths,
       logger=logger,
       session_state_service=session_state_service
   )
   ```

3. **Automation Factory** (factory.py:237-247):
   ```python
   session_repository = SessionRepository(
       paths=paths,
       logger=logger,
       session_state_service=session_state_service,
   )
   session_service = SessionService(
       repository=session_repository,
       logger=logger,
       session_state_service=session_state_service,
   )
   ```

**Used By:**
- TUI - Load chat history (`_load_chat_history()`)
- Bridge - Persist messages after LLM response
- Agents - Access conversation history
- Chatlog export - Generate markdown logs

---

## Key Data Flows

### Entity Loading Flow

```
User Message
  │
  ├─> EntityService.detect_mentions(message)
  │    └─> Scans all entities for name/trigger matches
  │         └─> Returns: set[entity_name]
  │
  └─> EntityService.get_characters_in_scene(...)
       └─> Loads full entity data for mentioned entities
            └─> Returns: list[CharacterEntity]
```

### Session Persistence Flow

```
LLM Response Received
  │
  ├─> Create SessionMessage(user_msg, assistant_response, ...)
  │
  ├─> SessionRepository.append_message(message)
  │    │
  │    ├─> Load active session
  │    ├─> Append message to session.messages
  │    ├─> session.sync_response_count()
  │    ├─> session.touch() (update timestamp)
  │    ├─> session.validate()
  │    └─> JsonStore.write(session.to_dict())
  │
  └─> ChatlogOrganizer.organize_by_chapter(session)
       └─> Generate markdown chatlog files
```

### Branching Flow

```
User Creates Branch
  │
  ├─> SessionRepository.create_branch(
  │        from_message_index=50,
  │        description="Alternate path"
  │    )
  │    │
  │    ├─> Load parent session
  │    ├─> Create new SessionData(
  │    │        session_id=generate_uuid(),
  │    │        parent_session="main",
  │    │        branch_point=50,
  │    │        messages=parent.messages[:50]
  │    │   )
  │    ├─> Save branch session to sessions/branches/{id}.json
  │    └─> Update .active pointer
  │
  └─> Future messages append to branch session
```

---

## File-Level Analysis

### Critical Files (Tier 1)

1. **sessions/models.py** - Core data structures
   - SessionData, SessionMessage, SessionCheckpoint
   - Used by all session code
   - No dependencies (pure data)

2. **sessions/repository.py** - Session persistence
   - 671 lines
   - CRUD operations
   - Branching support
   - Used by: Bridge, TUI, Automation

3. **entities/entity_service.py** - Entity API
   - 490 lines
   - High-level entity operations
   - Used by: Automation, Agents

### Important Files (Tier 2)

4. **entities/entity_repository.py** - Entity storage
   - 481 lines
   - Fixture-based loading
   - Used by: EntityService

5. **sessions/chatlog_organizer.py** - Export functionality
   - 387 lines
   - Markdown generation
   - Used by: Bridge (post-response)

6. **sessions/write_back.py** - Deferred writes
   - 254 lines
   - Prevents file thrashing
   - Used by: Bridge

### Supporting Files (Tier 3)

7. **entities/entity_parser.py** - Parse entity markdown
8. **entities/preference_generator.py** - Generate preferences
9. **sessions/service.py** - High-level session API
10. **entities/models.py** - Entity data models
11. **entities/fixtures.py** - Fixture repository impl

---

## Dead Code Analysis (Preliminary)

### Potentially Unused Components

**Need Verification in Phase 3:**

1. **preference_generator.py** (165 lines)
   - Purpose: Generate entity preferences
   - Usage: Not found in Phase 1 traces
   - **Verification needed:** Grep for PreferenceGenerator usage

2. **SessionCheckpoint** (in sessions/models.py)
   - Purpose: Branching save points
   - Usage: Model exists but unclear if checkpoints are created
   - **Verification needed:** Search for SessionCheckpoint.create() calls

3. **SessionService** (service.py)
   - Purpose: High-level session operations
   - Usage: Created in factory but unclear usage
   - **Verification needed:** Trace SessionService method calls

4. **ChatlogOrganizer.organize_by_scene()** (chatlog_organizer.py)
   - Purpose: Scene-based chat organization
   - Usage: organize_by_chapter() found, but by_scene() not traced
   - **Verification needed:** Search for organize_by_scene calls

### Files With Clear Usage (Verified in Phase 1):

✅ **entities/entity_service.py** - Used by BridgeService, automation factory
✅ **sessions/repository.py** - Used by Bridge, TUI, automation
✅ **sessions/models.py** - Used everywhere
✅ **sessions/write_back.py** - Used by BridgeService
✅ **sessions/chatlog_organizer.py** - Used by BridgeService

---

## Duplication Analysis (Preliminary)

### Potential Duplications:

1. **SessionRepository instantiated 3 times**
   - Bridge creates one
   - TUI creates one
   - Automation factory creates one
   - **Issue:** Same service created multiple times
   - **Recommendation:** Consider singleton or dependency injection

2. **SessionStateService instantiated 3 times**
   - Bridge creates one
   - TUI creates one
   - Automation factory creates one
   - **Issue:** Potential state inconsistency
   - **Recommendation:** Share single instance

3. **Entity detection logic**
   - EntityService.detect_mentions() (entity_service.py)
   - Potentially duplicated in tier loading (need verification)
   - **Verification needed:** Check tier_loader.py for similar logic

---

## Architecture Observations

### Good Patterns:

✅ **Clear separation of concerns**
   - Models (pure data) separate from services (logic)
   - Repository pattern for persistence
   - Service layer for business logic

✅ **Dataclass usage**
   - Immutable data structures
   - Type hints throughout
   - from_dict/to_dict for serialization

✅ **Branching support**
   - Timeline branching via parent_session + branch_point
   - Checkpoint system for save points

✅ **Validation**
   - SessionData.validate() ensures consistency
   - Response count syncing

### Potential Issues:

⚠️ **Service duplication**
   - Multiple instances of same services
   - No clear service lifetime management

⚠️ **Fixture-based entities**
   - Uses JSON fixtures instead of parsing markdown
   - Potential sync issues between markdown and fixtures
   - **Question:** When/how are fixtures updated?

⚠️ **Mixed responsibilities**
   - ChatlogOrganizer in domain layer (could be presentation)
   - EntityService has too many responsibilities

⚠️ **Type hints incomplete**
   - Many `Any` types
   - session_state_service: Any | None (should be typed)

---

## Next Steps for Phase 3 Verification

### Dead Code Verification (3+ methods):

1. **Grep for imports:**
   ```bash
   grep -r "PreferenceGenerator" refactoring/
   grep -r "SessionCheckpoint.create" refactoring/
   grep -r "organize_by_scene" refactoring/
   ```

2. **Trace from entry points:**
   - Follow execution from launch.py → bridge → TUI
   - Track all service method calls

3. **Check test files:**
   ```bash
   find refactoring/tests -name "*.py" -exec grep -l "PreferenceGenerator" {} \;
   ```

### Duplication Verification:
   - Map all service instantiations
   - Check for duplicated business logic
   - Compare entity detection implementations

---

## Summary Statistics

**Domain Layer:**
- **Files:** 14 (7 entities + 7 sessions)
- **Lines:** 3,155
- **Classes:** ~15 major classes
- **Services:** 3 (EntityService, SessionService, SessionRepository)
- **Models:** 6 dataclasses (SessionData, SessionMessage, SessionCheckpoint, EntityCard, + entity types)

**Key Responsibilities:**
- Entity management (characters, locations, items, orgs)
- Session persistence and branching
- Chat history management
- Chatlog export

**Dependencies:**
- Infrastructure: filesystem, templates, sessions
- Shared: models, interfaces

**Used By:**
- BridgeService (creates 3 session services, 1 entity service)
- TUI App (creates session repository)
- Automation (uses entity service, session service)

---

**Analysis Status:** Domain layer complete
**Next Step:** Phase 2.3 - Automation layer analysis (44 files)
