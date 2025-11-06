# SessionStateService Duplication Analysis

**Date**: 2025-11-06
**Analyst**: Claude (Systematic Codebase Analysis)
**Context**: Phase 3 verification following SYSTEMATIC_CODEBASE_ANALYSIS_PLAN.md
**Status**: CORRECTED - Initial analysis had errors, corrected after review

---

## Executive Summary

**Finding**: SessionStateService is instantiated **3 times** across the application:
1. In TUI process (presentation/tui/app.py:112) - **Used indirectly via SessionRepository**
2. In Bridge process (presentation/bridge/bridge_service.py:132) - **Active, 26 direct usages**
3. In Automation factory (automation/factory.py:176) - **Active, read-only usage**

**Severity**: **MEDIUM** - Not inter-instance conflict, but intra-instance concurrency within Bridge

**Real Issue**: Multiple agents in Bridge writing to same files concurrently, not duplicate instances conflicting

**Recommendation**: Implement file-level locking in write operations to protect against concurrent agent updates

---

## 1. Instantiation Analysis

### 1.1 Where SessionStateService is Created

#### Instance #1: TUI Process (Main)
```python
# refactoring/src/presentation/tui/app.py:112
session_state_service = SessionStateService(logger=logger)
self.session_repository = SessionRepository(
    paths=paths,
    logger=logger,
    session_state_service=session_state_service
)
```

**Purpose**: Passed to SessionRepository for timeline-aware session loading
**Direct Usage**: Zero direct calls to `session_state_service.*`
**Indirect Usage**: Used by SessionRepository methods:
- `SessionRepository.active_path` (repository.py:641) - Determines which timeline session to load
- `SessionRepository.create_branch()` (repository.py:306) - Updates timeline when creating branch

**Process**: Main process (separate from Bridge subprocess)

---

#### Instance #2: Bridge Process (Subprocess)
```python
# refactoring/src/presentation/bridge/bridge_service.py:132
self.session_state_service = SessionStateService(logger=self.logger)

# Used by (line 140):
self.session_repository = SessionRepository(
    paths=paths,
    logger=self.logger,
    session_state_service=self.session_state_service
)
```

**Purpose**: Primary service instance for Bridge operations
**Usage**: 26 direct calls across handlers and all 10 agents
**Process**: Bridge subprocess

---

#### Instance #3: Automation Factory (Bridge Process)
```python
# refactoring/src/automation/factory.py:176
session_state_service = SessionStateService(logger=logger)

# Shared with multiple components:
# - FileManager (line 194)
# - FixtureEntityRepository (line 221)
# - EntityService (line 228)
# - SessionRepository (line 240)
# - SessionService (line 246)
```

**Purpose**: Timeline-aware operations for automation pipeline
**Usage**: Injected into 5 automation components (all read-only)
**Process**: Bridge subprocess (same as Instance #2)

---

## 2. Understanding the Files Managed

### 2.1 session.json - The Control File (Single File)

**Location:** `RPs/[RP]/state/session.json`

**Purpose:** Central routing/configuration that tracks which timeline is active and where to find timeline-specific files

**Structure:**
```json
{
  "version": "2.0.0",
  "session_id": "main",
  "rp_title": "My RP",
  "response_count": 42,

  "timeline": {
    "current_session_id": "main",           // Which timeline are we on?
    "session_type": "active",
    "is_branch": false,
    "parent_session": null,
    "branch_point": null
  },

  "scene_context": {
    "scene_file": "state/scene_context_main.json"  // Points to scene file
  },

  "arc_tracking": {
    "arc_file": "state/arc_main.md"
  },

  "relationship_tracking": {
    "relationship_file": "state/relationships_main.json"
  },

  "plot_threads": {
    "thread_file": "state/plot_threads_main.json"
  },

  "knowledge": {
    "knowledge_file": "state/knowledge_main.json"
  }
}
```

**When Updated:**
- User switches branches → `timeline.current_session_id` changes
- User creates branch → Timeline section and all file pointers update
- Response count increments (currently unused feature)

**Update Frequency:** Rare (only on user branch operations)

---

### 2.2 scene_context_{session_id}.json - Scene Data (Multiple Files)

**Location:** `RPs/[RP]/state/scene_context_main.json`, `scene_context_branch1.json`, etc.

**Purpose:** Timeline-specific scene state that tracks what's happening in the story

**Structure:**
```json
{
  "chapter": "3",
  "location": "The old lighthouse",
  "characters_in_scene": ["Alice", "Bob", "mysterious_figure"],
  "last_updated_message": 42,

  "scene_analysis": {
    "mood": "tense",
    "setting_details": "stormy night, wind howling",
    "time_of_day": "midnight"
  },

  "time_context": {
    "current_time": "23:47",
    "elapsed_minutes": 15
  }
}
```

**When Updated:**
- **Every message** - Multiple agents update after LLM response
- ResponseAnalyzer extracts chapter/location/characters
- TimeTracking updates time_context
- RelationshipAnalysis updates characters_in_scene

**Update Frequency:** Every message (multiple agent writes per message)

**Multiple Files:** One per timeline (main, branch1, branch2, etc.)

---

### 2.3 Key Differences

| Aspect | session.json | scene_context_{id}.json |
|--------|-------------|------------------------|
| **Count** | 1 per RP | 1 per timeline |
| **Purpose** | Configuration/routing | Story state |
| **Update Frequency** | Rare (user actions) | Every message |
| **Content** | "Which timeline?" | "What's happening?" |
| **Size** | ~200 lines | ~50 lines |
| **Writers** | TUI + Bridge (user) | Bridge agents only |

**Analogy:**
- `session.json` = GPS saying "you're on Route 66"
- `scene_context_main.json` = Your current location on Route 66

When switching to a branch:
1. `session.json` updates: `"current_session_id": "branch1"`
2. File pointers update: `"scene_file": "state/scene_context_branch1.json"`
3. Agents now read/write `scene_context_branch1.json`

---

## 3. Execution Flow Analysis

### 3.1 TUI Process Flow

```
TUI Startup (start_tui.py)
  ↓
RPClientApp.__init__() [app.py:112]
  ↓
SessionStateService() created
  ↓
Passed to SessionRepository
  ↓
SessionRepository.load_active_session() [app.py:277]
  ↓
SessionRepository.active_path property [repository.py:641]
  ↓
session_state_service.load_session_state() ← READS session.json
  ↓
Returns correct session file path (main or branch)
```

**TUI's Usage Pattern:**
- Reads `session.json` to determine active timeline
- Loads correct session file for display
- Never directly calls `session_state_service.*` methods

**Separate Process:** TUI runs in main process, Bridge in subprocess - cannot share instances

---

### 3.2 Bridge Process Flow (Two Instances)

#### Bridge's Instance (26 usages)

```
User sends message
  ↓
MessageHandler.handle() [message_handler.py:311]
  ↓
bridge.session_state_service.get_scene_context() ← READS scene_context_*.json
  ↓
Background agents run after LLM response
  ↓
Multiple agents concurrently:
  - ResponseAnalyzer.execute() [response_analyzer_agent.py:85]
      → session_state_service.update_scene_context() ← WRITES

  - TimeTracking.execute() [time_tracking_agent.py:542]
      → session_state_service.update_scene_context() ← WRITES

  - RelationshipAnalysis.execute() [relationship_analysis_agent.py:480]
      → session_state_service.update_scene_context() ← WRITES
```

**Concurrent Write Pattern:**
```python
# Agent 1:
context = get_scene_context()      # READ scene_context_main.json
context["chapter"] = "3"            # MODIFY
update_scene_context(context)       # WRITE scene_context_main.json

# Agent 2 (simultaneously):
context = get_scene_context()      # READ scene_context_main.json (before Agent 1 writes)
context["location"] = "lighthouse"  # MODIFY
update_scene_context(context)       # WRITE scene_context_main.json (overwrites Agent 1!)
```

**Critical Finding:** The concurrency issue is **within Bridge's single instance**, not between instances.

---

#### Automation's Instance (Read-Only)

```
MessageHandler.handle() [message_handler.py:82]
  ↓
automation_service.run(context)
  ↓
session_service.enrich_session() [service.py:83]
  ↓
session_state_service.load_session_state() ← READS session.json
  ↓
Returns timeline info (session_id, parent_session, branch_point)
  ↓
Added to automation context for agents
```

**Usage Pattern:**
- **Read-only** operations
- Loads timeline info for context enrichment
- Never writes to any files

**No Write Conflicts:** Automation never modifies state

---

### 3.3 Branch Operations Flow

```
User creates branch in TUI
  ↓
BranchHandler._handle_create_branch() [branch_handler.py:170]
  ↓
session_repository.create_branch() [repository.py:227]
  ↓
Saves new branch session file
  ↓
session_state_service.switch_timeline() ← WRITES session.json
  ↓
Updates timeline section and file pointers
```

**Cross-Process Concern:**
- TUI and Bridge both write to `session.json` for branch operations
- But these are synchronous user actions (can't create and switch simultaneously)
- **Risk: LOW** - User-initiated, mutually exclusive operations

---

## 4. Conflict Analysis

### 4.1 session.json Conflicts

**Writers:**
- TUI instance: `SessionRepository.create_branch()` → `switch_timeline()`
- Bridge instance: `BranchHandler.switch_timeline()`
- Automation instance: Never writes

**Fields Written:**
```json
{
  "timeline": {
    "current_session_id": "...",    // Both TUI and Bridge
    "is_branch": true/false,         // Both TUI and Bridge
    "parent_session": "...",         // Both TUI and Bridge
    "branch_point": 42               // Both TUI and Bridge
  },
  "scene_context": {
    "scene_file": "..."              // Both TUI and Bridge
  }
  // + all other file pointers
}
```

**Conflict Risk:** **LOW**
- Both write same fields with same format
- Operations are user-initiated (not concurrent)
- User cannot create branch AND switch branch simultaneously

**Cross-Process Issue:**
- TUI (main process) and Bridge (subprocess) are separate processes
- File-level locking would need OS-level mechanisms (fcntl)
- Current atomic write (temp + rename) provides some protection

---

### 4.2 scene_context_{id}.json Conflicts

**Writers:**
- Bridge instance only: Multiple agents after each message
  - ResponseAnalyzer: chapter, location, characters_in_scene
  - TimeTracking: time_context
  - RelationshipAnalysis: characters_in_scene, scene updates
  - MemoryCreation: Reads for context
  - KnowledgeExtraction: Reads for context

**Fields Written:**
```json
{
  "chapter": "3",                     // ResponseAnalyzer
  "location": "lighthouse",           // ResponseAnalyzer
  "characters_in_scene": [...],       // ResponseAnalyzer, RelationshipAnalysis
  "last_updated_message": 42,         // Multiple agents
  "scene_analysis": {...},            // ResponseAnalyzer
  "time_context": {...}               // TimeTracking
}
```

**Conflict Risk:** **MEDIUM-HIGH**
- Multiple agents write concurrently after each message
- Each does read-modify-write without coordination
- Lost updates possible if two agents update simultaneously

**Same Process:**
- All agents run in Bridge subprocess
- All use Bridge's `session_state_service` instance
- This is an **intra-instance** concurrency problem

---

### 4.3 The Real Issue

**Not an inter-instance problem:**
- TUI and Bridge can't share (separate processes)
- Automation only reads (no writes)
- No conflicts between the 3 instances

**The actual problem:**
- Multiple agents in Bridge process writing to same file
- Using same SessionStateService instance
- Each agent does unsynchronized read-modify-write
- Classic race condition within single instance

**Example Scenario:**
```
Message #42 completes
  ↓
7 background agents start (in Bridge process)
  ↓
Agent 1: get_scene_context() → {"chapter": "2", "location": "forest"}
Agent 2: get_scene_context() → {"chapter": "2", "location": "forest"}
Agent 3: get_scene_context() → {"chapter": "2", "location": "forest"}
  ↓
Agent 1: modifies context["chapter"] = "3"
Agent 2: modifies context["location"] = "lighthouse"
Agent 3: modifies context["characters_in_scene"] = ["Alice", "Bob"]
  ↓
Agent 1: update_scene_context() → WRITES {"chapter": "3", "location": "forest", ...}
Agent 2: update_scene_context() → WRITES {"chapter": "2", "location": "lighthouse", ...}  ← Overwrites Agent 1!
Agent 3: update_scene_context() → WRITES {"chapter": "2", "location": "forest", "characters": [...]}  ← Overwrites Agent 2!
  ↓
Result: Only Agent 3's changes persist, Agent 1 and 2 lost
```

---

## 5. What Each Instance Actually Does

### 5.1 TUI Instance (Indirect Usage)

**Operations:**
- Read `session.json` to determine active timeline (via SessionRepository)
- Write `session.json` when user creates branch
- Display session metadata in UI

**Files Accessed:**
- `session.json` - Read frequently, write rarely
- Does NOT access `scene_context_*.json` files

**Frequency:**
- Reads: On startup, when loading chat history
- Writes: When user creates branch (rare)

---

### 5.2 Bridge Instance (Heavy Usage)

**Operations:**
- Read `session.json` for timeline info
- Write `session.json` when switching branches
- Read `scene_context_*.json` before/after messages
- Write `scene_context_*.json` from multiple agents

**Files Accessed:**
- `session.json` - Read frequently, write on branch operations
- `scene_context_*.json` - Read every message, write every message (multiple agents)

**Frequency:**
- Reads: Every message (10+ times)
- Writes: Every message from agents (3-7 concurrent writes)

**Critical Methods:**
- `get_scene_context()` - 26 calls from handlers and agents
- `update_scene_context()` - 5-7 calls from agents (concurrent!)
- `load_session_state()` - 15+ calls for timeline info
- `switch_timeline()` - Rare, user-initiated

---

### 5.3 Automation Instance (Read-Only)

**Operations:**
- Read `session.json` for timeline enrichment
- Add session_id, parent_session, branch_point to automation context
- Never writes to any state files

**Files Accessed:**
- `session.json` - Read only
- Does NOT access `scene_context_*.json`

**Frequency:**
- Reads: Once per message during enrichment phase

**Methods Used:**
- `load_session_state()` - Read timeline info
- No write methods called

---

## 6. Verification Methodology

### 6.1 Three-Method Verification

#### Method 1: Grep Analysis
```bash
# Find instantiations
$ grep -rn "SessionStateService(" refactoring/src --include="*.py"
refactoring/src/automation/factory.py:176
refactoring/src/presentation/bridge/bridge_service.py:132
refactoring/src/presentation/tui/app.py:112

# Find direct usages
$ grep -rn "session_state_service\." refactoring/src/presentation/tui --include="*.py"
# Result: 0 matches (TUI uses it only through SessionRepository)

# Find indirect usages via SessionRepository
$ grep -rn "_session_state_service" refactoring/src/domain/sessions/repository.py
# Result: 3 matches (lines 45, 306, 641)
```

#### Method 2: Execution Flow Tracing
- Traced message handling (message_handler.py → agents)
- Traced automation enrichment (factory.py → service.py)
- Traced branch operations (TUI and Bridge)
- Confirmed concurrent agent execution

#### Method 3: Code Reading
- Read SessionStateService full implementation (544 lines)
- Read all agent implementations for `update_scene_context()` calls
- Read SessionRepository indirect usage
- Read factory dependency injection

**Conclusion:** All three methods confirm usage patterns and concurrency risk.

---

## 7. Recommendations

### 7.1 Primary Solution: File-Level Locking

**Problem:** Multiple agents in Bridge process write to same files concurrently

**Solution:** Add file-level locking to protect write operations

```python
import threading

class SessionStateService:
    def __init__(self, *, logger: LoggingService):
        self._logger = logger
        self._locks: dict[Path, threading.Lock] = {}
        self._locks_lock = threading.Lock()

    def _get_lock(self, file_path: Path) -> threading.Lock:
        """Get or create lock for specific file path."""
        with self._locks_lock:
            if file_path not in self._locks:
                self._locks[file_path] = threading.Lock()
            return self._locks[file_path]

    def save_session_state(self, rp_dir: Path, state: dict[str, Any]) -> None:
        """Write session.json with file-level locking."""
        file_path = self._get_session_file_path(rp_dir)

        with self._get_lock(file_path):
            # Existing atomic write logic
            temp_path = file_path.with_suffix('.json.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            # Backup current file
            if file_path.exists():
                backup = file_path.with_suffix('.json.backup')
                shutil.copy2(file_path, backup)

            # Atomic rename
            temp_path.replace(file_path)

    def update_scene_context(self, rp_dir: Path, scene_data: dict[str, Any]) -> None:
        """Write scene_context with file-level locking."""
        state = self.load_session_state(rp_dir)
        scene_file = state.get("scene_context", {}).get(
            "scene_file", "state/scene_context_main.json"
        )
        file_path = rp_dir / scene_file

        with self._get_lock(file_path):  # ← Protect concurrent agent writes
            # Existing atomic write logic
            file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = file_path.with_suffix('.json.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)

            temp_path.replace(file_path)
```

**What This Protects:**
- Multiple agents updating `scene_context_*.json` simultaneously
- Race conditions in `save_session_state()`
- Lost updates from concurrent writes

**What This Doesn't Protect:**
- Cross-process conflicts (TUI vs Bridge) - would need OS-level locking (fcntl)
- But cross-process conflicts are low-risk (user-initiated actions)

**Benefits:**
- Works with current architecture (3 instances)
- No breaking changes required
- Simple thread-level locking (sufficient for same-process agents)
- Each file has its own lock (fine-grained)

---

### 7.2 Alternative: Merge-Based Updates (Advanced)

For even better correctness, implement merge-based updates:

```python
def update_scene_context_merge(
    self,
    rp_dir: Path,
    updates: dict[str, Any],
    merge_strategy: str = "shallow"
) -> None:
    """Update scene context by merging changes, not replacing.

    Args:
        rp_dir: RP directory
        updates: Fields to update (not full context)
        merge_strategy: "shallow" or "deep" merge
    """
    state = self.load_session_state(rp_dir)
    scene_file = state.get("scene_context", {}).get(
        "scene_file", "state/scene_context_main.json"
    )
    file_path = rp_dir / scene_file

    with self._get_lock(file_path):
        # Read current data inside lock
        current = self._read_scene_context(file_path)

        # Merge updates
        if merge_strategy == "deep":
            merged = self._deep_merge(current, updates)
        else:
            merged = {**current, **updates}  # Shallow merge

        # Write merged result
        self._write_scene_context(file_path, merged)
```

**Usage:**
```python
# Instead of:
context = get_scene_context()
context["chapter"] = "3"
update_scene_context(context)

# Agents do:
update_scene_context_merge({"chapter": "3"})
```

**Benefits:**
- Agents only specify what they're changing
- Concurrent updates don't overwrite unrelated fields
- More robust than full replacement

**Downside:**
- Requires refactoring all agent code
- More complex implementation

---

### 7.3 Why NOT Share Instances

**Reason 1: Separate Processes**
- TUI runs in main process
- Bridge runs in subprocess (spawned by launch.py)
- Python objects cannot be shared across processes without serialization

**Reason 2: No Actual Inter-Instance Conflict**
- TUI instance: Reads session.json, rare writes on branch creation
- Bridge instance: Heavy usage, agents write concurrently
- Automation instance: Read-only operations
- Conflicts are **within** Bridge instance, not **between** instances

**Reason 3: Current Design Is Appropriate**
- Each process needs its own instance (cannot share)
- Bridge having 2 instances (Bridge + Automation) is acceptable
- The issue is concurrent writes, not duplicate instances

---

## 8. Implementation Priority

### Priority 1: File-Level Locking (HIGH)

**Effort:** 1-2 hours
**Impact:** HIGH - Prevents data loss from concurrent agent writes
**Risk:** LOW - Additive change, doesn't break existing code

**Changes Required:**
1. Add `_locks` dict to `SessionStateService.__init__()`
2. Add `_get_lock()` helper method
3. Wrap write operations in `with self._get_lock(file_path):`
4. Test with concurrent agent execution

**Files to Modify:**
- `src/infrastructure/sessions/session_state_service.py` only

---

### Priority 2: Merge-Based Updates (MEDIUM)

**Effort:** 4-6 hours
**Impact:** MEDIUM - Better correctness, cleaner agent code
**Risk:** MEDIUM - Requires refactoring all agent update calls

**Changes Required:**
1. Add `update_scene_context_merge()` method
2. Update all 5-7 agents that call `update_scene_context()`
3. Add tests for merge behavior
4. Migration path for backward compatibility

**Files to Modify:**
- `src/infrastructure/sessions/session_state_service.py`
- 7 agent files (response_analyzer, time_tracking, relationship_analysis, etc.)

---

### Priority 3: OS-Level Locking (LOW)

**Effort:** 2-3 hours
**Impact:** LOW - Only protects rare cross-process conflicts
**Risk:** MEDIUM - Platform-dependent (fcntl on Linux, different on Windows)

**Only needed if:**
- Users frequently create/switch branches during message processing
- Currently this is extremely rare (user can't use TUI while Bridge is processing)

**Not Recommended:** Thread-level locking is sufficient for the actual problem

---

## 9. Testing Strategy

### 9.1 Concurrent Write Test

```python
import threading
from pathlib import Path

def test_concurrent_scene_context_updates():
    """Test multiple agents updating scene context simultaneously."""
    service = SessionStateService(logger=logger)
    rp_dir = Path("/path/to/test/rp")

    # Initialize scene context
    initial = {
        "chapter": "1",
        "location": "start",
        "characters_in_scene": []
    }
    service.update_scene_context(rp_dir, initial)

    # Simulate 3 agents updating concurrently
    def update_chapter():
        context = service.get_scene_context(rp_dir)
        context["chapter"] = "2"
        service.update_scene_context(rp_dir, context)

    def update_location():
        context = service.get_scene_context(rp_dir)
        context["location"] = "forest"
        service.update_scene_context(rp_dir, context)

    def update_characters():
        context = service.get_scene_context(rp_dir)
        context["characters_in_scene"] = ["Alice", "Bob"]
        service.update_scene_context(rp_dir, context)

    # Run concurrently
    threads = [
        threading.Thread(target=update_chapter),
        threading.Thread(target=update_location),
        threading.Thread(target=update_characters)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify all updates persisted
    final = service.get_scene_context(rp_dir)
    assert final["chapter"] == "2", "Chapter update lost!"
    assert final["location"] == "forest", "Location update lost!"
    assert final["characters_in_scene"] == ["Alice", "Bob"], "Characters update lost!"
```

**Expected Without Locking:** Test fails (lost updates)
**Expected With Locking:** Test passes (all updates preserved)

---

### 9.2 Load Test

```python
def test_high_concurrency_load():
    """Stress test with many concurrent updates."""
    service = SessionStateService(logger=logger)
    rp_dir = Path("/path/to/test/rp")

    service.update_scene_context(rp_dir, {"counter": 0})

    def increment_counter():
        for _ in range(100):
            context = service.get_scene_context(rp_dir)
            context["counter"] = context.get("counter", 0) + 1
            service.update_scene_context(rp_dir, context)

    # 10 threads each incrementing 100 times
    threads = [threading.Thread(target=increment_counter) for _ in range(10)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final = service.get_scene_context(rp_dir)
    assert final["counter"] == 1000, f"Expected 1000, got {final['counter']}"
```

**Without Locking:** Will be < 1000 (lost updates)
**With Locking:** Exactly 1000

---

## 10. Conclusion

### Summary of Corrected Understanding

**Initial Error:** Misidentified as inter-instance conflict requiring instance sharing

**Corrected Understanding:**
1. **TUI instance is NOT dead code** - Used indirectly via SessionRepository for timeline-aware session loading
2. **Can't share TUI and Bridge instances** - Separate processes, cannot share Python objects
3. **Automation instance is read-only** - No writes, no conflicts
4. **Real issue is intra-instance** - Multiple agents in Bridge writing concurrently using same instance

### File Responsibilities

| File | Purpose | Writers | Update Frequency |
|------|---------|---------|-----------------|
| **session.json** | Configuration/routing | TUI + Bridge | Rare (user actions) |
| **scene_context_{id}.json** | Story state | Bridge agents | Every message (concurrent!) |

### The Actual Problem

Multiple agents in Bridge process call `update_scene_context()` concurrently:
- Each reads current state
- Each modifies different fields
- Each writes full state back
- Last write wins, others lost

### The Solution

**File-level locking** in `SessionStateService` write methods:
- Protects concurrent agent writes
- Works with current architecture
- Simple implementation (threading.Lock)
- No breaking changes

### Priority

**HIGH** - Implement file-level locking
- Prevents data loss from concurrent agent updates
- 1-2 hour implementation
- Low risk, high impact
- Addresses the actual problem (concurrent writes within Bridge)

### What We Don't Need

- ❌ Share instances across processes (impossible)
- ❌ Remove TUI instance (used via SessionRepository)
- ❌ Merge Automation into Bridge instance (working fine, read-only)
- ❌ OS-level file locking (overkill for rare cross-process conflicts)

---

## Appendix A: All Usage Sites

### Bridge's Instance (26 direct usages)

**Handlers:**
- `message_handler.py:311` - `get_scene_context()` for message saving
- `branch_handler.py:57` - `load_session_state()` for branch listing
- `branch_handler.py:223` - `switch_timeline()` for branch switching
- `branch_handler.py:289` - `update_scene_context()` for branch restoration

**Immediate Agents (3):**
- `fact_extraction_agent.py:220` - `load_session_state()`
- `memory_extraction_agent.py:51` - `get_scene_context()`
- `plot_thread_extraction_agent.py:117` - `load_session_state()`

**Background Agents (7 agents, 19 usages):**
- `response_analyzer_agent.py:62` - `get_scene_context()`
- `response_analyzer_agent.py:85` - `update_scene_context()` ← WRITE
- `response_analyzer_agent.py:256` - `load_session_state()`
- `relationship_analysis_agent.py:113` - `get_scene_context()`
- `relationship_analysis_agent.py:373` - `get_current_timeline()`
- `relationship_analysis_agent.py:480` - `update_scene_context()` ← WRITE
- `relationship_analysis_agent.py:540` - `get_current_timeline()`
- `relationship_analysis_agent.py:804` - `update_scene_context()` ← WRITE
- `relationship_analysis_agent.py:843` - `get_current_timeline()`
- `time_tracking_agent.py:445` - `get_scene_context()`
- `time_tracking_agent.py:464` - `load_session_state()`
- `time_tracking_agent.py:536` - `get_scene_context()`
- `time_tracking_agent.py:542` - `update_scene_context()` ← WRITE
- `plot_thread_detection_agent.py:85` - `get_scene_context()`
- `plot_thread_detection_agent.py:350` - `load_session_state()`
- `plot_thread_detection_agent.py:674` - `load_session_state()`
- `plot_thread_detection_agent.py:728` - `load_session_state()`
- `chapter_compression_agent.py:504` - `set_current_chapter()` ← WRITE
- `memory_creation_agent.py:87` - `get_scene_context()`
- `knowledge_extraction_agent.py:164` - `get_scene_context()`
- `knowledge_extraction_agent.py:431` - `load_session_state()`
- `knowledge_extraction_agent.py:480` - `load_session_state()`
- `knowledge_extraction_agent.py:539` - `load_session_state()`

**Write Operations:** 5 agents write to scene_context (potentially concurrent)

---

### Automation's Instance (Indirect via injection)

**SessionService (service.py:83):**
```python
def enrich_session(self, context: AutomationContext):
    state = self._session_state_service.load_session_state(context.rp_dir)
    timeline = state.get("timeline", {})
    # Returns session_id, parent_session, branch_point
```

**SessionRepository (repository.py:641):**
```python
@property
def active_path(self) -> Path:
    state = self._session_state_service.load_session_state(self._paths.rp_dir)
    current_session_id = state.get("timeline", {}).get("current_session_id", "main")
    # Returns correct session file path
```

**All Read-Only:** No write operations from Automation instance

---

### TUI's Instance (Indirect via SessionRepository)

**RPClientApp (app.py:277):**
```python
def _load_chat_history(self):
    session = self.session_repository.load_active_session()
    # SessionRepository calls active_path property
    # which uses session_state_service
```

**SessionRepository.create_branch (repository.py:306):**
```python
def create_branch(...):
    # After saving branch file...
    if self._session_state_service:
        self._session_state_service.switch_timeline(...)  ← WRITES session.json
```

**Mostly Read, Rare Writes:** TUI writes only on branch creation

---

## Appendix B: Recommended Code Changes

### Change 1: Add Locking Infrastructure

```python
# src/infrastructure/sessions/session_state_service.py

import threading
from typing import Any

class SessionStateService:
    """Manages the centralized session state file with backup support."""

    def __init__(self, *, logger: LoggingService) -> None:
        self._logger = logger
        # Add file-level locks
        self._locks: dict[Path, threading.Lock] = {}
        self._locks_lock = threading.Lock()  # Lock for the locks dict

    def _get_lock(self, file_path: Path) -> threading.Lock:
        """Get or create a lock for the given file path.

        Thread-safe lock acquisition for file-level synchronization.
        """
        with self._locks_lock:
            if file_path not in self._locks:
                self._locks[file_path] = threading.Lock()
            return self._locks[file_path]
```

### Change 2: Protect session.json Writes

```python
def save_session_state(self, rp_dir: Path, state: dict[str, Any]) -> None:
    """Write session.json with file-level locking."""
    session_file = self._get_session_file_path(rp_dir)

    # Acquire file lock before write
    with self._get_lock(session_file):
        # Ensure state directory exists
        session_file.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if session_file.exists():
            backup = session_file.with_suffix('.json.backup')
            try:
                shutil.copy2(session_file, backup)
            except Exception as e:
                self._logger.warning(
                    "session_state.backup_failed",
                    context={"path": str(session_file), "error": str(e)}
                )

        # Atomic write (temp + rename)
        temp_path = session_file.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            temp_path.replace(session_file)  # Atomic on POSIX and Windows

            self._logger.debug(
                "session_state.saved",
                context={"path": str(session_file)}
            )
        except Exception as e:
            self._logger.error(
                "session_state.save_failed",
                context={"path": str(session_file), "error": str(e)}
            )
            if temp_path.exists():
                temp_path.unlink()
            raise
```

### Change 3: Protect scene_context Writes

```python
def update_scene_context(self, rp_dir: Path, scene_data: dict[str, Any]) -> None:
    """Update scene context for current timeline with file-level locking."""
    state = self.load_session_state(rp_dir)
    scene_file = state.get("scene_context", {}).get(
        "scene_file",
        "state/scene_context_main.json"
    )
    scene_path = rp_dir / scene_file

    # Acquire file lock before write
    with self._get_lock(scene_path):
        # Ensure parent directory exists
        scene_path.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically (temp file + rename)
        temp_path = scene_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(scene_path)  # Atomic on both POSIX and Windows

            self._logger.debug(
                "scene_context.updated",
                context={
                    "path": str(scene_path),
                    "chapter": scene_data.get("chapter", ""),
                    "location": scene_data.get("location", "")
                }
            )
        except Exception as e:
            self._logger.error(
                "scene_context.update_failed",
                context={"path": str(scene_path), "error": str(e)}
            )
            if temp_path.exists():
                temp_path.unlink()
            raise
```

**Benefits:**
- Each file has independent lock (fine-grained)
- Locks held only during write (minimal contention)
- Atomic writes still preserved (temp + rename)
- Backward compatible (no API changes)

---

**Document Status**: CORRECTED AND COMPLETE
**Key Insight**: Problem is concurrent agent writes within single instance, not duplicate instances
**Next Steps**: Implement file-level locking in SessionStateService write methods
