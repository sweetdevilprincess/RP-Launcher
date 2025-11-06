# Agent Priority Analysis

**Date:** 2025-10-30
**Purpose:** Identify core agents required for basic system functionality vs. optional enhancements

---

## Agent Categories

### ✅ TIER 1: CORE AGENTS (Essential for Basic Functionality)

These agents are fundamental to the RP system and should be implemented first.

#### 1. ResponseAnalyzerAgent ✅ IMPLEMENTED
**Type:** Background (N+1)
**Status:** COMPLETE
**Purpose:** Extract scene metadata (chapter, location, characters)
**Why Core:**
- Populates session state for all other agents
- Without it, other agents must do redundant LLM calls
- Foundation for timeline-specific scene tracking

#### 2. TimeTrackingAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Track time passage, calculate activity durations, fix date calculations
**Why Core:**
- **Fixes actual bug** ("Saturday to Tuesday" incorrectly calculated as "3 days")
- Provides accurate timestamps for memories and events
- Enables correct "days until" calculations
- Foundation for schedules, appointments, and time-based features
- User explicitly requested this feature

**Priority:** **HIGH - Implement Next**

**Key Features:**
- Calculate intermediate days correctly (Saturday to Tuesday = 2 days, not 3)
- Track activity durations using timing reference data
- Apply modifiers (fast, slow, relaxed) to activities
- Update structured in-world date/time
- Provide time context to Claude's prompt

#### 3. MemoryCreationAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Extract memorable moments for each character
**Why Core:**
- Core feature of RP system - players expect character memories
- Directly impacts narrative continuity
- Referenced by users frequently ("Does Alice remember X?")
- Provides context for future responses
- Needs accurate timestamps from TimeTrackingAgent

**Priority:** **HIGH - Implement After TimeTrackingAgent**

#### 4. RelationshipAnalysisAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Track relationship changes between characters
**Why Core:**
- Core feature of RP system - relationships drive narrative
- Players expect relationship progression to be tracked
- Critical for romantic RP scenarios
- Informs character behavior in future scenes

**Priority:** **HIGH - Implement After MemoryCreationAgent**

---

### ⚙️ TIER 2: IMPORTANT AGENTS (Enhance Core Functionality)

These agents significantly improve the experience but aren't required for basic operation.

#### 5. KnowledgeExtractionAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Extract world-building facts and lore
**Why Important:**
- Maintains narrative consistency
- Prevents contradictions in world rules
- Valuable for complex world-building settings
- Can be worked around manually (user notes)

**Priority:** MEDIUM - Implement after core agents

#### 6. PlotThreadDetectionAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Identify and track narrative threads/storylines
**Why Important:**
- Helps maintain long-running story arcs
- Prevents dropped plot threads
- Useful for complex multi-arc stories
- Less critical for simple/slice-of-life RPs

**Priority:** MEDIUM - Implement after core agents

---

### 🔍 TIER 3: OPTIONAL AGENTS (Nice-to-Have)

These agents provide additional value but aren't essential.

#### 7. ContradictionDetectionAgent
**Type:** Background (N+1)
**Status:** NOT IMPLEMENTED
**Purpose:** Detect narrative inconsistencies
**Why Optional:**
- Complex to implement well (lots of false positives)
- Can be handled by KnowledgeExtractionAgent + manual review
- Most valuable for very long RPs (100+ responses)
- Claude already does some consistency checking

**Priority:** LOW - Consider skipping or implementing much later

#### 8. QuickEntityAnalysisAgent
**Type:** Immediate (N)
**Status:** NOT IMPLEMENTED
**Purpose:** Identify entities mentioned in user message
**Why Optional:**
- Existing keyword-based detection already works
- May not need LLM at all
- Minor improvement over current system

**Priority:** VERY LOW - Likely skip entirely

#### 9. FactExtractionAgent
**Type:** Immediate (N)
**Status:** NOT IMPLEMENTED
**Purpose:** Pull relevant facts for Claude's context
**Why Optional:**
- Current tiered loading system already handles this
- Complex to implement (what's "relevant"?)
- May not provide enough value for effort

**Priority:** LOW - Consider for future enhancement

#### 10. MemoryExtractionAgent
**Type:** Immediate (N)
**Status:** NOT IMPLEMENTED
**Purpose:** Find relevant memories for current context
**Why Optional:**
- Similar to FactExtractionAgent
- Current system loads recent memories automatically
- Marginal improvement over current approach

**Priority:** LOW - Consider for future enhancement

#### 11. PlotThreadExtractionAgent
**Type:** Immediate (N)
**Status:** NOT IMPLEMENTED
**Purpose:** Identify relevant plot threads for current message
**Why Optional:**
- Depends on PlotThreadDetectionAgent existing first
- Complex to determine "relevance"
- Current system works without it

**Priority:** LOW - Implement only after PlotThreadDetectionAgent is proven valuable

---

## Recommended Implementation Order

### Phase 1: Core Functionality (REQUIRED)
1. ✅ **ResponseAnalyzerAgent** - COMPLETE
2. **TimeTrackingAgent** - START HERE (fixes date calculation bug)
3. **MemoryCreationAgent** - After time tracking (needs accurate timestamps)
4. **RelationshipAnalysisAgent**

**Result:** Basic RP system with time tracking, memory & relationship tracking

**Estimated Time:** ~16-20 hours (TimeTracking: 6-8h, MemoryCreation: 4-6h, Relationship: 4-6h)

---

### Phase 2: Enhanced Functionality (RECOMMENDED)
5. **KnowledgeExtractionAgent**
6. **PlotThreadDetectionAgent**

**Result:** Improved narrative consistency and plot tracking

**Estimated Time:** ~10-14 hours (Knowledge: 4-6h, PlotThread: 6-8h)

---

### Phase 3: Polish & Optimization (OPTIONAL)
7. **ContradictionDetectionAgent** (if needed)
8. Immediate agents (if proven valuable)

**Result:** Advanced features for power users

**Estimated Time:** ~12-16 hours (varies by agent)

---

## Core Agent Dependencies

### TimeTrackingAgent Dependencies:
- ✅ ResponseAnalyzerAgent (for scene context, optional)
- ✅ SessionStateService (for reading/writing time_context)
- ✅ BaseAgent (for LLM access)
- ✅ timing_reference.json (created in config/)

**Blockers:** NONE - Ready to implement

---

### MemoryCreationAgent Dependencies:
- ✅ ResponseAnalyzerAgent (for chapter/location/characters)
- ✅ SessionStateService (for reading scene context)
- ✅ FixtureEntityRepository (for saving memories)
- ✅ BaseAgent (for LLM access)

**Blockers:** NONE - Ready to implement

---

### RelationshipAnalysisAgent Dependencies:
- ✅ ResponseAnalyzerAgent (for characters_in_scene)
- ✅ SessionStateService (for reading scene context)
- ✅ BaseAgent (for LLM access)
- ⚠️ Need to design relationship file format

**Blockers:** Design relationship storage format

**Questions:**
1. Where do we store relationships?
   - Option A: `state/relationships_{session_id}.json` (timeline-specific)
   - Option B: Per-character files `entities/{char}_relationships.json`
2. What format do relationships use?
   - Bidirectional or unidirectional?
   - How to track relationship history/changes?

---

### KnowledgeExtractionAgent Dependencies:
- ✅ BaseAgent (for LLM access)
- ⚠️ Need knowledge base file structure

**Blockers:** Design knowledge storage format

**Questions:**
1. Where to store knowledge?
   - `state/knowledge_base_{session_id}.json` (timeline-specific)?
2. How to organize by category?
3. How to prevent duplicate facts?

---

### PlotThreadDetectionAgent Dependencies:
- ✅ ResponseAnalyzerAgent (for chapter context)
- ✅ SessionStateService (already has plot_threads pointer!)
- ✅ Timeline-specific storage already configured

**Blockers:** NONE - plot_threads file structure already exists in session.json

**Existing Infrastructure:**
```json
{
  "plot_threads": {
    "thread_file": "state/plot_threads_{session_id}.json"
  }
}
```

---

## Analysis Summary

### Ready to Implement Immediately:
1. ✅ **TimeTrackingAgent** - All dependencies met, timing_reference.json created
2. ✅ **MemoryCreationAgent** - All dependencies met (needs TimeTracking first for timestamps)
3. ⚙️ **PlotThreadDetectionAgent** - Infrastructure ready

### Needs Design Work First:
1. ⚠️ **RelationshipAnalysisAgent** - Design storage format
2. ⚠️ **KnowledgeExtractionAgent** - Design storage format

### Recommendation:

**Next Steps (Priority Order):**

1. **Implement TimeTrackingAgent** (~6-8 hours)
   - All dependencies ready
   - **Fixes actual bug** (incorrect "days until" calculations)
   - Provides accurate timestamps for memories
   - User explicitly requested this feature

2. **Implement MemoryCreationAgent** (~4-6 hours)
   - All dependencies ready
   - Core feature users expect
   - Needs accurate timestamps from TimeTrackingAgent
   - Builds on ResponseAnalyzerAgent foundation

3. **Design Relationship Storage Format** (~1-2 hours)
   - Define JSON schema
   - Decide on file location
   - Document in architecture docs

4. **Implement RelationshipAnalysisAgent** (~4-6 hours)
   - After storage format designed
   - Core feature for RP system

5. **Implement PlotThreadDetectionAgent** (~6-8 hours)
   - Infrastructure already exists
   - Enhances long-form narrative tracking

6. **Implement KnowledgeExtractionAgent** (~4-6 hours)
   - After relationship tracking proven
   - Valuable for world-building RPs

7. **Evaluate Optional Agents** (~research)
   - After core agents working well
   - Decide which (if any) immediate agents to build

---

## Why Skip/Defer Certain Agents?

### ContradictionDetectionAgent:
- High false-positive risk (character growth vs. inconsistency)
- Expensive (needs to load all knowledge + memories)
- Marginal value (Claude already self-corrects somewhat)
- Can be added later if users request it

### Immediate Agents (N):
- Current system already loads context well
- Tiered loading handles most use cases
- Complexity doesn't justify marginal improvement
- Can add later if testing shows gaps

### QuickEntityAnalysisAgent:
- Keyword detection already works
- LLM call overhead not worth minor improvement
- May not need at all

---

**Status:** Analysis Complete (Updated with TimeTrackingAgent)
**Next Action:** Implement TimeTrackingAgent (fixes "Saturday to Tuesday = 3 days" bug)
