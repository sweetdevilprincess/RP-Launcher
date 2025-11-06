# Session State Architecture & Timeline Branching

**Date:** 2025-10-30
**Purpose:** Document session.json structure, identify timeline conflicts, establish best practices

---

## Overview

`state/session.json` serves as the **central registry** for the current RP session. It tracks which timeline is active and provides **pointers** to timeline-specific data files.

**Critical Rule:** Timeline-specific data should NEVER be stored directly in session.json. Instead, session.json should store **file pointers** that change when switching timelines.

---

## Current session.json Structure

```json
{
  "session_id": "main",
  "timeline": {
    "current_session_id": "main",
    "session_type": "active",
    "is_branch": false,
    "parent_session": null,
    "branch_point": null
  },
  "arc_tracking": {
    "arc_file": "state/arc_main.md",
    "arc_session_id": "main"
  },
  "relationship_tracking": {
    "relationship_file": "state/relationships_main.json"
  },
  "plot_threads": {
    "thread_file": "state/plot_threads_main.json"
  },
  "rp_metadata": {
    "rp_title": "test_rp",
    "response_count": 0,
    "total_messages": 0,
    "migrated_at": "2025-10-22T19:48:37.761235+00:00"
  }
}
```

---

## Field-by-Field Analysis

### ✅ CORRECT: Timeline-Agnostic (Shared Across All Timelines)

#### 1. `timeline` (object)
**Purpose:** Tracks which timeline is currently active
**Why Shared:** This is meta-state that tells us WHICH timeline we're viewing

**Fields:**
- `current_session_id` - Which timeline is active
- `session_type` - "active" or "branch"
- `is_branch` - Boolean flag
- `parent_session` - Parent timeline ID (if branch)
- `branch_point` - Message index where branch diverged

**Behavior on Timeline Switch:**
- Entire object gets rewritten with new timeline info

---

#### 2. `rp_metadata.rp_title` (string)
**Purpose:** Name of the RP
**Why Shared:** The RP title is the same across all timelines

---

#### 3. `rp_metadata.migrated_at` (string)
**Purpose:** Timestamp of migration from legacy structure
**Why Shared:** Migration happened once, applies to all timelines

---

### ✅ CORRECT: Timeline-Specific (Pointer Pattern)

#### 4. `arc_tracking` (object)
**Purpose:** Points to timeline-specific arc file
**Pattern:** CORRECT ✅

**Fields:**
- `arc_file`: "state/arc_main.md" → "state/arc_branch_a.md"
- `arc_session_id`: "main" → "branch_a"

**Behavior on Timeline Switch:**
```python
state["arc_tracking"]["arc_file"] = f"state/arc_{session_id}.md"
state["arc_tracking"]["arc_session_id"] = session_id
```

**Files:**
- `state/arc_main.md`
- `state/arc_branch_a.md`
- `state/arc_branch_b.md`

---

#### 5. `relationship_tracking` (object)
**Purpose:** Points to timeline-specific relationship file
**Pattern:** CORRECT ✅

**Fields:**
- `relationship_file`: "state/relationships_main.json" → "state/relationships_branch_a.json"

**Behavior on Timeline Switch:**
```python
state["relationship_tracking"]["relationship_file"] = f"state/relationships_{session_id}.json"
```

**Files:**
- `state/relationships_main.json`
- `state/relationships_branch_a.json`

---

#### 6. `plot_threads` (object)
**Purpose:** Points to timeline-specific plot thread file
**Pattern:** CORRECT ✅

**Fields:**
- `thread_file`: "state/plot_threads_main.json" → "state/plot_threads_branch_a.json"

**Behavior on Timeline Switch:**
```python
state["plot_threads"]["thread_file"] = f"state/plot_threads_{session_id}.json"
```

**Files:**
- `state/plot_threads_main.json`
- `state/plot_threads_branch_a.json`

---

### ⚠️ CONFLICTS IDENTIFIED: Timeline-Specific Data Stored Globally

#### 7. `rp_metadata.response_count` ❌ CONFLICT
**Current Storage:** Directly in session.json
**Problem:** Each timeline has a different response count!

**Example Scenario:**
- Main timeline: 50 responses
- Branch A (created at response 30): 25 responses
- Branch B (created at response 40): 15 responses

**Current Behavior (BROKEN):**
- Switch to Branch A → response_count shows 50 (wrong! should be 25)
- Switch to Branch B → response_count shows 50 (wrong! should be 15)
- Data gets overwritten and lost

**Solution:** Move to timeline-specific file

---

#### 8. `rp_metadata.total_messages` ❌ CONFLICT
**Current Storage:** Directly in session.json
**Problem:** Same issue as response_count - each timeline has different message counts

**Solution:** Move to timeline-specific file

---

#### 9. `session_id` ❓ REDUNDANT
**Current Storage:** Top-level field
**Problem:** Redundant with `timeline.current_session_id`

**Solution:** Remove top-level `session_id`, use `timeline.current_session_id` consistently

---

### ⚠️ MISSING: New Timeline-Specific Data

#### 10. `scene_context` (NEEDS TO BE ADDED)
**Purpose:** Track current scene metadata (chapter, location, characters)
**Why Timeline-Specific:** Branch A might be at Chapter 3 in a Tavern, Branch B might be at Chapter 2 in a Forest

**Recommended Pattern:** Follow existing pointer pattern

```json
{
  "scene_context": {
    "scene_file": "state/scene_context_main.json"
  }
}
```

**Files:**
- `state/scene_context_main.json`
- `state/scene_context_branch_a.json`

**Content of scene_context_{session_id}.json:**
```json
{
  "chapter": "Chapter 3: Secrets Revealed",
  "location": "The Rusty Anchor Tavern",
  "characters_in_scene": ["Alice", "Bob"],
  "last_updated_message": 42,
  "scene_analysis": {
    "type": "dialogue",
    "pace": "medium",
    "tension": 6,
    "word_count": 450
  },
  "time_context": {
    "elapsed": "30 minutes",
    "timestamp": "Tuesday 3:00 PM"
  }
}
```

---

## Recommended Fixes

### Priority 1: Fix response_count and total_messages

**Create new file:** `state/timeline_metadata_{session_id}.json`

```json
{
  "session_id": "main",
  "response_count": 50,
  "total_messages": 100,
  "created_at": "2025-01-15T10:00:00Z",
  "last_updated": "2025-01-20T15:30:00Z"
}
```

**Update session.json:**
```json
{
  "timeline_metadata": {
    "metadata_file": "state/timeline_metadata_main.json"
  }
}
```

**Update SessionStateService:**
```python
def get_response_count(self, rp_dir: Path) -> int:
    """Get response count for current timeline."""
    state = self.load_session_state(rp_dir)
    metadata_file = state.get("timeline_metadata", {}).get(
        "metadata_file",
        "state/timeline_metadata_main.json"
    )
    metadata_path = rp_dir / metadata_file
    if not metadata_path.exists():
        return 0

    with open(metadata_path) as f:
        metadata = json.load(f)

    return metadata.get("response_count", 0)

def increment_response_count(self, rp_dir: Path) -> int:
    """Increment response count for current timeline."""
    state = self.load_session_state(rp_dir)
    metadata_file = state.get("timeline_metadata", {}).get(
        "metadata_file",
        "state/timeline_metadata_main.json"
    )
    metadata_path = rp_dir / metadata_file

    # Load current metadata
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
    else:
        metadata = {
            "session_id": state["timeline"]["current_session_id"],
            "response_count": 0,
            "total_messages": 0
        }

    # Increment
    metadata["response_count"] += 1
    metadata["last_updated"] = datetime.now().isoformat()

    # Save
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata["response_count"]
```

**Update switch_timeline():**
```python
def switch_timeline(self, rp_dir, session_id, *, parent_session=None, branch_point=None):
    # ... existing code ...

    state["timeline_metadata"]["metadata_file"] = f"state/timeline_metadata_{session_id}.json"

    self.save_session_state(rp_dir, state)
```

---

### Priority 2: Add scene_context

**Update session.json schema:**
```json
{
  "scene_context": {
    "scene_file": "state/scene_context_main.json"
  }
}
```

**Update switch_timeline():**
```python
state["scene_context"]["scene_file"] = f"state/scene_context_{session_id}.json"
```

**Add SessionStateService methods:**
```python
def get_scene_context(self, rp_dir: Path) -> dict:
    """Get scene context for current timeline."""
    state = self.load_session_state(rp_dir)
    scene_file = state.get("scene_context", {}).get(
        "scene_file",
        "state/scene_context_main.json"
    )
    scene_path = rp_dir / scene_file

    if not scene_path.exists():
        return {
            "chapter": "",
            "location": "Unknown",
            "characters_in_scene": [],
            "last_updated_message": 0
        }

    with open(scene_path) as f:
        return json.load(f)

def update_scene_context(self, rp_dir: Path, scene_data: dict) -> None:
    """Update scene context for current timeline."""
    state = self.load_session_state(rp_dir)
    scene_file = state.get("scene_context", {}).get(
        "scene_file",
        "state/scene_context_main.json"
    )
    scene_path = rp_dir / scene_file
    scene_path.parent.mkdir(parents=True, exist_ok=True)

    with open(scene_path, 'w') as f:
        json.dump(scene_data, f, indent=2, ensure_ascii=False)
```

---

### Priority 3: Remove redundant session_id

**Before:**
```json
{
  "session_id": "main",
  "timeline": {
    "current_session_id": "main",
    ...
  }
}
```

**After:**
```json
{
  "timeline": {
    "current_session_id": "main",
    ...
  }
}
```

**Migration:** Update any code referencing top-level `session_id` to use `timeline.current_session_id` instead.

---

## Best Practices for Future Fields

### Rule 1: Is this data timeline-specific?

**Ask:** "Could this data be different in Branch A vs. Branch B?"

**Examples:**
- ✅ Timeline-Specific: response_count, current_chapter, current_location, scene_analysis
- ❌ Shared: rp_title, user_preferences, llm_provider_settings

### Rule 2: Store timeline-specific data in separate files

**Pattern:**
```json
{
  "new_feature": {
    "feature_file": "state/new_feature_{session_id}.json"
  }
}
```

**NOT:**
```json
{
  "new_feature": {
    "some_data": "value that changes per timeline"
  }
}
```

### Rule 3: Update switch_timeline() for all timeline-specific pointers

When adding new timeline-specific data:

```python
def switch_timeline(self, rp_dir, session_id, **kwargs):
    state = self.load_session_state(rp_dir)

    # Update timeline metadata
    state["timeline"] = {...}

    # Update ALL timeline-specific file pointers
    state["arc_tracking"]["arc_file"] = f"state/arc_{session_id}.md"
    state["relationship_tracking"]["relationship_file"] = f"state/relationships_{session_id}.json"
    state["plot_threads"]["thread_file"] = f"state/plot_threads_{session_id}.json"
    state["timeline_metadata"]["metadata_file"] = f"state/timeline_metadata_{session_id}.json"
    state["scene_context"]["scene_file"] = f"state/scene_context_{session_id}.json"
    # ↑ ADD NEW POINTERS HERE

    self.save_session_state(rp_dir, state)
```

---

## Summary of Identified Issues

| Field | Current Location | Issue | Priority | Solution |
|-------|-----------------|-------|----------|----------|
| `response_count` | `rp_metadata` | Timeline-specific data in shared location | **HIGH** | Move to `timeline_metadata_{session_id}.json` |
| `total_messages` | `rp_metadata` | Timeline-specific data in shared location | **HIGH** | Move to `timeline_metadata_{session_id}.json` |
| `session_id` | Top-level | Redundant with `timeline.current_session_id` | MEDIUM | Remove, use `timeline.current_session_id` |
| `scene_context` | Missing | Needed for ResponseAnalyzerAgent | **HIGH** | Add as `scene_context_{session_id}.json` pointer |

---

## Migration Strategy

### Phase 1: Add new pointer fields (backwards compatible)
1. Add `timeline_metadata` pointer to session.json
2. Add `scene_context` pointer to session.json
3. Update `switch_timeline()` to update new pointers
4. Create timeline-specific files when switching

### Phase 2: Migrate existing data
1. Read `rp_metadata.response_count` and `rp_metadata.total_messages`
2. Create `timeline_metadata_main.json` with these values
3. Update session.json to point to new file
4. Keep old fields for backwards compatibility (mark deprecated)

### Phase 3: Remove deprecated fields
1. Remove `rp_metadata.response_count` from session.json
2. Remove `rp_metadata.total_messages` from session.json
3. Remove top-level `session_id` field

---

**Status:** Analysis Complete - Ready for Implementation
**Next Steps:** Fix response_count/total_messages conflict, add scene_context support
