# Complete Secondary LLM Automation List

**Date:** 2025-10-24
**Purpose:** COMPREHENSIVE list of ALL automation tasks that should use secondary LLM
**Status:** CORRECTED based on legacy code + user clarifications + reference repos

---

## Key Discovery: Legacy Agent Implementations Found!

**Location:** `C:\Users\green\Desktop\RP Claude Code\src\automation\agents\`

Many agents already implemented in legacy code - can PORT instead of building from scratch!

---

## N vs N+1 Timing (Critical)

From legacy code comments: **"Runs after Response N while user types Message N+1 (~5 seconds, hidden)"**

- **N agents (Background)**: Run after Claude responds, analyze Response N
- **N+1 agents (Immediate)**: Run before Claude responds, prepare context for Response N+1
- **Timing**: ~5 seconds while user types = "free" background processing time

---

## Overview

This document lists EVERY automation task that should use the secondary (cheap) LLM, organized by:
1. **When** it runs (N background, N+1 immediate, periodic, on-demand)
2. **What system** it belongs to (triggers, templates, entities, memories, etc.)
3. **Status** (✅ exists in legacy, ❌ needs building)

---

## 1. TRIGGER SYSTEM Automation

### 1.1 Semantic Trigger Evaluation (EXISTING, needs wiring)

**Status:** ✅ Implementation exists, ❌ Not wired to secondary LLM

**File:** `src/automation/triggers/semantic_evaluator.py`

**What:** Determine if user message semantically matches trigger descriptions

**Why LLM:** Understand meaning beyond keywords
- "I talked to my sister" → Matches "Alice's family" if context suggests sister = Alice

**Input:**
```python
{
    "user_message": str,
    "semantic_descriptions": list[str],  # From entity trigger metadata
    "entity_name": str,
}
```

**Output:**
```python
{
    "matched": bool,
    "confidence": float,  # 0.0-1.0
}
```

**Current State:**
- Has `SemanticAiClient` wrapper (semantic_ai_client.py)
- Takes any `LLMClient`
- NOT currently initialized with secondary LLM
- Falls back gracefully if no client

**Action Needed:**
- Wire `SemanticEvaluator` to secondary LLM client
- Pass via `TriggerRegistry.__init__(ai_client=agent_llm_client)`

**Estimated:** 0.5 hours (already implemented, just wiring)

---

## 2. TEMPLATE SYSTEM Automation

### 2.1 Template Adherence Validation ❌ NEW

**What:** Check if Claude's response follows the active template guidelines (thriller, dark_romance, etc.)

**Why LLM:** Understand nuanced writing guidelines and evaluate adherence

**User Clarification:** NOT automatic selection - validate adherence to templates you already have (thriller.json, dark_romance.json)

**Template Structure** (from config/templates/prompts/):
```json
{
  "genre": "thriller",
  "sections": {
    "tone_and_atmosphere": ["Suspense and mounting dread", ...],
    "pacing": ["Alternating between slow builds and sharp action", ...],
    "dialogue_style": [...],
    "scene_construction": [...],
    "descriptive_focus": [...],
    "common_pitfalls": [...]
  }
}
```

**Input:**
```python
{
    "response_text": str,
    "active_template": dict,  # The template JSON (thriller.json, etc.)
    "template_name": str,  # "thriller", "dark_romance"
}
```

**LLM Prompt:**
```
Evaluate how well this response adheres to the {template_name} template guidelines.

RESPONSE: {response_text}

TEMPLATE GUIDELINES:
Tone & Atmosphere: {tone_guidelines}
Pacing: {pacing_guidelines}
Dialogue Style: {dialogue_guidelines}
Scene Construction: {scene_guidelines}
Descriptive Focus: {descriptive_guidelines}
Common Pitfalls: {pitfalls_to_avoid}

Evaluate each section:
- FOLLOWED (2 pts): Guidelines clearly followed
- PARTIAL (1 pt): Some adherence but could be stronger
- MISSED (0 pts): Guidelines not followed or violated

Respond with JSON:
{
  "adherence_score": 0.85,
  "section_scores": {
    "tone_and_atmosphere": 2,
    "pacing": 1,
    "dialogue_style": 2,
    "scene_construction": 2,
    "descriptive_focus": 1
  },
  "strengths": ["Suspense well-maintained", "Time pressure clear"],
  "weaknesses": ["Dialogue could be more strategic"],
  "pitfalls_violated": [],
  "recommendation": "good"
}
```

**Output:** Validation report with score and feedback

**File:** `src/automation/agents/background/template_validation_agent.py`

**Priority:** 🟢 MEDIUM (quality control)

**Estimated:** 5-6 hours

---

## 3. ENTITY SYSTEM Automation

### 3.1 Entity Sheet Generation & Updates ❌ NEW (Inspired by Auto-Cards)

**What:** Like Auto-Cards - BOTH generate new entity sheets AND update existing ones

**Why LLM:**
- **Create**: Extract information to build complete character card for new NPCs
- **Update**: Add new information to existing entity sheets as it's revealed

**Reference:** https://github.com/LewdLeah/Auto-Cards (detects entities, creates new cards, provides smart long-term memory updates for existing cards)

**Two Operations:**

#### A. Auto-Generate NEW Entity Sheets
**Example:**
- Response 1: "A bartender served drinks"
- Response 3: "The same bartender asked about Alice"
- Response 5: "The bartender mentioned his name is James, he's from Boston"
- **TRIGGER**: 3 mentions → Generate full entity sheet for "James"

**LLM Prompt (Create):**
```
Extract all information about "{unnamed_npc}" from the conversation context.

CONTEXT: {conversation_history}

Create a complete character profile including:
- Full name (if mentioned)
- Physical description
- Personality traits
- Background/history
- Relationships to other characters
- Notable behaviors/quirks
- Relevant facts

Generate appropriate trigger keywords for future detection.

Respond with JSON character card format.
```

#### B. Update EXISTING Entity Sheets
**Example:**
- James's card exists with: "Bartender, from Boston"
- New response: "James mentioned he has a sister in Chicago and loves jazz"
- **TRIGGER**: New information detected → Update James's card

**LLM Prompt (Update):**
```
New information revealed about "{entity_name}":

CURRENT CARD: {existing_entity_card}
NEW CONTEXT: {new_information}

Identify:
1. What new facts were revealed?
2. Does any information contradict the existing card?
3. What fields should be updated?

Respond with JSON:
{
  "updates": {
    "field_name": "new_value",
    ...
  },
  "new_facts": [...],
  "contradictions": [...]
}
```

**Input:**
```python
{
    "conversation_context": list[dict],
    "existing_entities": dict[str, EntityCard],
    "unnamed_npc_mentions": dict[str, int],  # Track mention counts
}
```

**Output:**
```python
{
    "new_entities_to_create": list[dict],  # Full card data
    "entities_to_update": list[dict],  # entity_id + updates
    "mention_counts": dict[str, int],  # Updated counts
}
```

**File:** `src/automation/agents/background/entity_management_agent.py`

**Priority:** 🟡 HIGH (very useful feature)

**Estimated:** 8-10 hours (two-part system: creation + updates)

---

---

## 4. MEMORY SYSTEM Automation - Dual Layer

**User Clarification:** Two types of memories, not consolidation!

### 4.1 Specific Memories (FROM LEGACY) ✅ EXISTS

**Status:** ✅ Implementation exists in legacy code

**File:** `src/automation/agents/background/memory_creation.py` (LEGACY - port to refactored)

**What:** Individual memorable moments (MemoryEntry dataclass)

**Memory Types** (from legacy):
- revelation
- conflict
- first_meeting
- character_moment
- relationship_development
- plot_event

**From legacy code:**
```python
{
  "mems": [
    {
      "title": str,
      "chars": list[str],
      "loc": str,
      "type": str,
      "sig": int,  # 1-10 significance
      "tone": str,  # emotional tone
      "summary": str,
      "quote": str,
      "tags": list[str]
    }
  ]
}
```

**Priority:** 🔴 CRITICAL

**Estimated:** 4-6 hours (port from legacy)

---

### 4.2 General/Overall Memories ❌ NEW

**What:** Broader patterns and summaries that NPC "generally remembers"

**User Clarification:** Different from specific memories - tracks general patterns

**Difference:**
- **Specific**: "Alice confessed feelings on May 5th in the garden" (can recall this exact moment)
- **General**: "Alice has romantic feelings for Bob that she's expressed" (overall pattern)

**Why:** Dual-layer system - specific for detail, general for quick context

**Priority:** 🟢 MEDIUM

**Estimated:** 5-6 hours

---

### 4.3 Relationship Analysis (FROM LEGACY) ✅ EXISTS

**Status:** ✅ Implementation exists in legacy code

**File:** `src/automation/agents/background/relationship_analysis.py` (LEGACY - port to refactored)

**What:** Track Player-NPC relationships based on interactions and preferences

**Why LLM:** Analyze player actions/dialogue against NPC preferences to update relationship tiers

**User Clarification:** "Relationships are supposed to look through how a player (or another NPC) is acting or talking about or to or whatever and that would look through NPC (and character preferences) and have that change the relationship between the player and the NPCs."

**Relationship Tiers** (from legacy):
- Enemy (-100 to -30)
- Hostile (-29 to -10)
- Stranger (-9 to 10)
- Acquaintance (11 to 30)
- Friend (31 to 60)
- Close Friend (61 to 80)
- Best Friend (81 to 100)

**Input:**
```python
{
    "player_actions": list[str],  # What player said/did
    "npc_name": str,
    "npc_preferences": dict,  # From entity card
    "current_relationship_score": int,
    "conversation_context": str,
}
```

**Output:**
```python
{
    "relationship_delta": int,  # +/- change to score
    "new_relationship_score": int,
    "new_tier": str,
    "reasoning": str,
    "preference_matches": list[str],  # Which preferences were matched
}
```

**Priority:** 🔴 CRITICAL (core feature)

**Estimated:** 4-6 hours (port from legacy)

---

## 5. PLOT SYSTEM Automation

### 5.1 Plot Thread Detection & Outcome Tracking (FROM LEGACY) ✅ EXISTS

**Status:** ✅ Implementation exists in legacy code - needs enhancement

**File:** `src/automation/agents/background/plot_thread_detection.py` (LEGACY - port + enhance)

**What:** Detect new plot threads, track mentioned threads, and TRACK OUTCOMES when resolved

**Why LLM:** Understand narrative threads and their impact on the story

**User Clarification:** "Plot threads kept track of open threads, closed threads, and kept them as part of the RP. It would keep the outcomes from the thread being resolved successfully or unsuccessfully and would change the story based on that."

**Example:**
- **Fake date scenario**: Player and fake SO fight in public
- **Outcome**: Unsuccessful/Conflict
- **Long-term effect**: Reputation damage, relationship changes

**From Legacy Code:**
```python
{
  "threads": {
    "new": [
      {
        "id": "THREAD-001",
        "title": "Search for missing artifact",
        "priority": "high",
        "time_sensitive": true,
        "description": "..."
      }
    ],
    "mentioned": [
      {
        "id": "THREAD-002",
        "update": "Found new clue about sister's location"
      }
    ],
    "resolved": [
      {
        "id": "THREAD-003",
        "resolution": "Successfully rescued hostages",
        "outcome": "successful"  # ← NEW: track outcome type
      }
    ]
  }
}
```

**Enhancement Needed:** Add outcome tracking
- `outcome`: "successful", "unsuccessful", "abandoned", "complicated"
- `long_term_effects`: list[str] - How this resolution affects future story
- `affected_relationships`: dict[str, str] - Which relationships changed
- `consequences`: str - Narrative consequences

**Priority:** 🔴 CRITICAL (core narrative tracking)

**Estimated:** 4-6 hours (port + enhance with outcomes)

---

### 5.2 Chapter/Arc Detection ❌ NEW

**What:** Detect when a narrative chapter or story arc completes

**Why LLM:** Understand story structure and pacing

**Example:**
- Major plot thread resolves → Suggest chapter break
- Location changes + time skip → Suggest chapter break
- Major character development moment → Arc milestone

**Input:**
```python
{
    "recent_responses": list[str],  # Last 10-20 responses
    "plot_threads": list[PlotThread],
    "chapter_history": list[dict],  # Previous chapters
    "current_chapter": dict,
}
```

**LLM Prompt:**
```
Analyze if a natural chapter break or story arc has occurred.

RECENT NARRATIVE:
{recent_responses}

PLOT THREADS:
{plot_threads}

CURRENT CHAPTER: {current_chapter}

Detect:
- Natural stopping points (quest complete, location change, time skip)
- Story arcs completing (character development, plot resolution)
- Pacing milestones (climax, resolution, transition)

Respond with JSON:
{
  "chapter_break_detected": true,
  "arc_milestone": "resolution",
  "reasoning": "Major plot thread resolved, characters moving to new location",
  "suggested_chapter_title": "The Revelation",
  "confidence": 0.85
}
```

**Output:**
```python
{
    "chapter_break_detected": bool,
    "arc_milestone": str | None,  # "inciting_incident", "rising_action", "climax", "resolution"
    "suggested_chapter_title": str | None,
    "reasoning": str,
    "confidence": float,
}
```

**File:** `src/automation/agents/background/chapter_detection_agent.py`

**Priority:** MEDIUM (useful for long sessions)

**Estimated:** 5-6 hours

---

## 6. KNOWLEDGE/LORE Automation

### 6.1 Knowledge Extraction ❌ NEW
**Estimated:** 4-6 hours (already documented)

### 6.2 Contradiction Detection ❌ NEW
**Estimated:** 6-8 hours (already documented)

### 6.3 Lore Categorization ⚪ OPTIONAL

**What:** Auto-categorize knowledge entries into taxonomy

**Why LLM:** Understand content and assign categories

**Input:**
```python
{
    "knowledge_entry": KnowledgeEntry,
    "available_categories": list[str],
}
```

**Output:**
```python
{
    "categories": list[str],
    "confidence": float,
}
```

**Priority:** LOW (can assign manually)

**Estimated:** 2-3 hours

---

## 7. SESSION MANAGEMENT Automation

### 7.1 Session Summary Generation ❌ NEW

**What:** Generate summary of session for user

**Why LLM:** Synthesize narrative into coherent summary

**Example:** After 50 responses, generate:
- What happened in this session
- Key moments
- Character developments
- Plot progress

**Input:**
```python
{
    "session_messages": list[dict],  # All messages in session
    "memories_created": list[MemoryEntry],
    "plot_threads_updated": list[PlotThread],
    "session_metadata": dict,
}
```

**LLM Prompt:**
```
Create a narrative summary of this roleplay session.

SESSION MESSAGES: {session_messages}
KEY MEMORIES: {memories_created}
PLOT DEVELOPMENTS: {plot_threads_updated}

Generate:
1. Brief overview (2-3 sentences)
2. Key moments (bullet points)
3. Character development highlights
4. Plot progress summary
5. Notable quotes/dialogue

Style: Engaging third-person narrative summary

Respond with JSON:
{
  "overview": "Alice and Bob explored the mysterious ruins...",
  "key_moments": [...],
  "character_developments": {...},
  "plot_progress": {...},
  "notable_quotes": [...]
}
```

**Output:**
```python
{
    "overview": str,
    "key_moments": list[str],
    "character_developments": dict[str, str],
    "plot_progress": dict[str, str],
    "notable_quotes": list[str],
}
```

**File:** `src/automation/agents/on_demand/session_summary_agent.py`

**Triggered:**
- User requests summary
- End of session
- After N responses (configurable)

**Priority:** HIGH (very useful feature)

**Estimated:** 4-5 hours

---

### 7.2 Session Title Generation ⚪ OPTIONAL

**What:** Generate title for session based on content

**Why LLM:** Understand narrative themes

**Input:**
```python
{
    "session_summary": str,
    "key_moments": list[str],
}
```

**Output:**
```python
{
    "suggested_titles": list[str],  # 3-5 options
}
```

**Priority:** LOW

**Estimated:** 2 hours

---

## 8. RESPONSE ANALYSIS Automation (Already covered)

### 8.1 Response Classification ❌ NEW
**Estimated:** 3-4 hours (already documented)

### 8.2 Quality Scoring ⚪ OPTIONAL

**What:** Score Claude's response quality

**Why LLM:** Meta-analysis of response

**Input:**
```python
{
    "user_message": str,
    "response_text": str,
    "character_cards": list[CharacterEntity],
}
```

**Output:**
```python
{
    "quality_score": float,  # 0.0-1.0
    "strengths": list[str],
    "weaknesses": list[str],
    "suggestions": list[str],
}
```

**Priority:** LOW (interesting but not critical)

**Estimated:** 4-5 hours

---

### 8.3 Pacing Analysis ❌ NEW

**What:** Analyze narrative pacing over time

**Why LLM:** Understand story rhythm

**Input:**
```python
{
    "recent_classifications": list[ResponseClassification],  # Last 20
    "session_length": int,
}
```

**Output:**
```python
{
    "pacing_assessment": str,  # "too_fast", "good", "too_slow", "uneven"
    "action_dialogue_ratio": float,
    "scene_variety_score": float,
    "recommendations": list[str],
}
```

**Priority:** MEDIUM (helpful for long sessions)

**Estimated:** 3-4 hours

---

## 9. CONTEXT ENHANCEMENT Automation

### 9.1 Fact Extraction (Immediate) ❌ NEW
**Estimated:** 4-5 hours (already documented)

### 9.2 Memory Extraction (Immediate) ❌ NEW
**Estimated:** 4-5 hours (already documented)

### 9.3 Plot Thread Extraction (Immediate) ❌ NEW
**Estimated:** 4-5 hours (already documented)

### 9.4 Context Summarization ❌ NEW

**What:** Summarize long conversation history for Claude

**Why LLM:** Condense information while preserving important details

**Problem:** Conversation history grows too long for token limits

**Solution:** Summarize older messages, keep recent ones verbatim

**Input:**
```python
{
    "conversation_history": list[dict],  # All messages
    "current_message_index": int,
    "max_tokens": int,  # Token budget
}
```

**LLM Prompt:**
```
Summarize the older portion of this conversation history.

CONVERSATION HISTORY (messages 1-30):
{conversation_history}

Create a concise summary that:
- Preserves key plot developments
- Maintains character dynamics
- Includes important decisions/revelations
- Removes redundant dialogue
- Fits within {max_tokens} tokens

Respond with JSON:
{
  "summary": "Alice and Bob met at the cafe, where Alice revealed...",
  "key_moments_preserved": [...],
  "estimated_tokens": 500
}
```

**Output:**
```python
{
    "summary": str,
    "key_moments_preserved": list[str],
    "compression_ratio": float,  # original_tokens / summary_tokens
}
```

**File:** `src/automation/agents/immediate/context_summarization_agent.py`

**Priority:** HIGH (essential for long conversations)

**Estimated:** 5-6 hours

---

### 9.5 Prompt Enhancement/Rewriting ⚪ OPTIONAL

**What:** Rewrite user message to be more detailed/clear

**Why LLM:** Expand terse messages into rich prompts

**Example:**
- User: "Alice talks"
- Enhanced: "Alice engages in a conversation, expressing her thoughts about..."

**Priority:** LOW (might annoy users)

**Estimated:** 3-4 hours

---

## 10. TAGGING & CATEGORIZATION Automation

### 10.1 Automatic Memory Tagging ❌ NEW

**What:** Auto-generate tags for memories

**Why LLM:** Understand content and assign semantic tags

**Input:**
```python
{
    "memory_entry": MemoryEntry,
    "available_tags": list[str],
}
```

**Output:**
```python
{
    "tags": list[str],
    "new_tag_suggestions": list[str],  # If no existing tags fit
}
```

**Priority:** MEDIUM (part of memory creation)

**Estimated:** Included in MemoryCreationAgent (add to prompt)

---

### 10.2 Entity Relationship Classification ⚪ OPTIONAL

**What:** Classify relationship types between entities

**Why LLM:** Understand nuanced relationship dynamics

**Input:**
```python
{
    "entity_a": str,
    "entity_b": str,
    "relationship_history": list[dict],
}
```

**Output:**
```python
{
    "relationship_type": str,  # "friendship", "romance", "rivalry", etc.
    "intensity": int,  # 1-10
    "dynamics": list[str],  # ["power_imbalance", "mutual_respect"]
}
```

**Priority:** LOW (part of relationship analysis)

**Estimated:** Included in RelationshipAnalysisAgent

---

## 11. TESTING & DEBUGGING Automation ⚪ OPTIONAL

### 11.1 Regression Testing ⚪ OPTIONAL

**What:** Test if changes break existing narrative consistency

**Why LLM:** Understand if story still makes sense

**Priority:** LOW

**Estimated:** 6-8 hours

---

### 11.2 Constraint Checking ⚪ OPTIONAL

**What:** Verify responses follow user-defined rules/constraints

**Why LLM:** Understand and evaluate against rules

**Example:** User rule: "Bob never swears" → Check if Bob swore

**Priority:** LOW

**Estimated:** 4-5 hours

---

## 12. USER ASSISTANCE Automation

### 12.1 Suggestion Generation ❌ NEW

**What:** Suggest what user could say next

**Why LLM:** Generate contextually appropriate suggestions

**Input:**
```python
{
    "response_text": str,
    "user_message": str,
    "conversation_context": list[dict],
}
```

**Output:**
```python
{
    "suggestions": list[str],  # 3-5 suggested user responses
}
```

**Priority:** MEDIUM (helpful for users)

**Estimated:** 3-4 hours

---

### 12.2 World Building Assistant ⚪ OPTIONAL

**What:** Help user build out world details

**Why LLM:** Generate ideas and expand on concepts

**Priority:** LOW (user can do this manually)

**Estimated:** 4-6 hours

---

## 13. ANALYTICS & METRICS Automation

### 13.1 Character Development Tracking ❌ NEW

**What:** Track how characters change over time

**Why LLM:** Understand character arcs

**Input:**
```python
{
    "character_name": str,
    "memories": list[MemoryEntry],
    "time_span": str,  # "session", "chapter", "all_time"
}
```

**Output:**
```python
{
    "development_summary": str,
    "key_changes": list[dict],  # What changed + when + why
    "arc_progress": str,  # "beginning", "development", "climax", "resolution"
}
```

**Priority:** MEDIUM

**Estimated:** 4-5 hours

---

### 13.2 Engagement Metrics ⚪ OPTIONAL

**What:** Analyze user engagement patterns

**Why LLM:** Understand what types of scenes work best

**Priority:** LOW

**Estimated:** 3-4 hours

---

## COMPLETE LIST SUMMARY

### By Category (Agent Work Only)

| Category | Tasks | Status | Est. Hours |
|----------|-------|--------|------------|
| **Trigger System** | 1 | ✅ Exists, needs wiring | 0.5 |
| **Template System** | 1 | ❌ Validation only | 5-6 |
| **Entity System** | 1 | ❌ Create + Update (Auto-Cards style) | 8-10 |
| **Memory System** | 3 | ❌ Specific + General + Relationships | 13-17 (1 exists in legacy) |
| **Plot System** | 3 | ❌ Detection + Resolution + Chapter | 11-14 |
| **Knowledge System** | 2 | ❌ Extraction + Contradiction | 10-14 |
| **Session Management** | 2 | ❌ Summary + Title | 6-7 |
| **Response Analysis** | 3 | ❌ Classification + Quality + Pacing | 10-13 |
| **Context Enhancement** | 4 | ❌ Need to build | 17-20 |
| **Tagging** | 0 | ⚪ Part of other agents | 0 (included) |
| **Testing** | 2 | ⚪ Optional | 10-13 |
| **User Assistance** | 2 | ⚪ Optional | 7-10 |
| **Analytics** | 2 | ⚪ Optional | 7-9 |
| **TOTAL AGENTS** | **26 tasks** | | **95-130 hours** |

**Note:** Add 24-37 hours for infrastructure, data structures, testing, and integration (see Revised Total Estimate)

### By Priority

#### 🔴 CRITICAL (Must Have) - 30-40 hours
1. ✅ Semantic Trigger Evaluation (wiring) - 0.5h
2. ❌ MemoryCreationAgent - 4-6h
3. ❌ RelationshipAnalysisAgent - 4-6h
4. ❌ FactExtractionAgent - 4-5h
5. ❌ MemoryExtractionAgent - 4-5h
6. ❌ Context Summarization - 5-6h
7. ❌ Session Summary - 4-5h

#### 🟡 HIGH PRIORITY (Core Features) - 40-55 hours
8. ❌ Entity Management (Create + Update) - 8-10h
9. ❌ PlotThreadDetectionAgent - 6-8h
10. ❌ PlotThreadExtractionAgent - 4-5h
11. ❌ KnowledgeExtractionAgent - 4-6h
12. ❌ ContradictionDetectionAgent - 6-8h
13. ❌ ResponseAnalyzerAgent - 3-4h
14. ❌ Chapter Detection - 5-6h
15. ❌ Pacing Analysis - 3-4h
16. ❌ Character Development Tracking - 4-5h

#### 🟢 MEDIUM PRIORITY (Nice to Have) - 10-15 hours
17. ⚪ Template Validation - 5-6h
18. ⚪ Suggestion Generation - 3-4h
19. ⚪ Session Title Generation - 2h

#### ⚪ LOW PRIORITY (Optional) - 15-20 hours
20. ⚪ Quality Scoring - 4-5h
21. ⚪ Prompt Enhancement - 3-4h
22. ⚪ Lore Categorization - 2-3h
23. ⚪ Regression Testing - 6-8h
24. ⚪ Constraint Checking - 4-5h
25. ⚪ World Building Assistant - 4-6h
26. ⚪ Engagement Metrics - 3-4h

---

## What Was Missing From Original Document

From the original `AGENT_SYSTEM_BUILD_SCOPE.md`, I missed:

### Added Now:
1. **Semantic Trigger Evaluation** (already implemented!)
2. **Template Validation** - Quality control for narrative adherence
3. **Context Summarization** - Essential for long conversations
4. **Session Summary** - Very useful user feature (command-triggered)
5. **Chapter Detection** - Natural story structure
6. **Character Development Tracking** - Analytics
7. **Pacing Analysis** - Quality control
8. **Entity Updates** - Keep entity sheets current with new info (Auto-Cards style)
9. **Suggestion Generation** - User assistance

### Key Additions:
- **7 critical priority tasks** that should be implemented first
- **9 high priority tasks** that are core features
- **3 medium priority tasks** that add value
- **7 optional tasks** for completeness

---

## Revised Total Estimate

**Previously:** 122-160 hours (35 tasks - had duplicates/outdated items)

**Now (CORRECTED):** 119-167 hours (26 automation tasks + infrastructure)

**Breakdown:**
- Infrastructure: 4-6h
- Data structures: 4-6h
- **Agent work: 95-130h total:**
  - Critical agents (7): 30-40h (mostly porting from legacy)
  - High priority agents (9): 40-55h (includes Entity Management 8-10h)
  - Medium priority (3): 10-15h
  - Low priority (7): 15-20h
- Testing: 10-15h
- Integration: 6-10h

**Grand Total: 119-167 hours**

---

## Recommended Phased Approach

### Phase 1: Foundation (2-3 weeks)
- Infrastructure + data structures (8-12h)
- Critical 7 agents - port from legacy (30-40h)
- Basic testing (4-6h)
**Total:** 42-58 hours

### Phase 2: Core Features (3-4 weeks)
- High priority 9 agents (40-55h)
  - Entity Management (Create + Update) - 8-10h
  - Plot Thread Detection/Extraction - 10-13h
  - Knowledge + Contradiction - 10-14h
  - Response Analysis + Chapter + Pacing - 13-15h
  - Character Development - 4-5h
- Integration refinement (4-6h)
**Total:** 44-61 hours

### Phase 3: Polish & Optional (2-3 weeks)
- Medium priority (10-15h)
  - Template Validation - 5-6h
  - Suggestion Generation - 3-4h
  - Session Title - 2h
- Testing & integration (6-9h)
**Total:** 16-24 hours

### Phase 4: Optional Enhancements (as time permits)
- Low priority 7 tasks (15-20h)
- Advanced testing (10-13h)
**Total:** 25-33 hours

---

## Next Steps

Want to:
1. **Prioritize which tasks to implement first?**
2. **Deep dive into one of the newly identified agents?** (e.g., Context Summarization, Entity Management, Story Arc)
3. **Start implementing Phase 1?**
4. **Make architectural decisions first?** (agent grouping, when to run, etc.)

---

# 🔴 MAJOR CORRECTIONS FROM INITIAL ANALYSIS

## What Changed After Finding Legacy Code & User Clarifications

### 1. **Entity System** - AUTO-GENERATION not updates
- ❌ OLD: Update existing character/location cards
- ✅ NEW: Auto-generate NEW entity sheets after X mentions (like Auto-Cards)
- Reference: https://github.com/LewdLeah/Auto-Cards

### 2. **Template System** - VALIDATION not selection
- ❌ OLD: Auto-select which template to use
- ✅ NEW: Validate Claude follows active template (thriller.json, dark_romance.json)

### 3. **Relationship System** - Player-NPC with PREFERENCES
- ✅ FOUND in legacy: `relationship_analysis.py`
- Matches player actions against NPC preferences  
- Tracks tiers (Enemy → Hostile → Stranger → Friend → Best Friend)
- ✅ Can PORT from legacy

### 4. **Memory System** - DUAL LAYER not consolidation
- ❌ OLD: Consolidate similar memories
- ✅ NEW: Two types:
  - **Specific**: "Alice confessed on May 5th" (exact moment)
  - **General**: "Alice has romantic feelings" (overall pattern)
- ✅ Specific memories exist in legacy: `memory_creation.py`

### 5. **Plot Threads** - Track OUTCOMES
- ✅ FOUND in legacy: `plot_thread_detection.py`
- ✅ NEW ADDITION: Track successful/unsuccessful/abandoned outcomes
- Example: Fake date fight → Unsuccessful → Long-term reputation damage
- ✅ Can PORT + ENHANCE from legacy

### 6. **Story Arc System** - NEW ENTIRE SYSTEM
- ❌ NOT in initial analysis
- ✅ NEW: Story Genome/Arc generation system
- Reference: https://github.com/Yi1i1i/Story-Arc-Engine
- Generates chapter arcs from past + planned path
- Detects divergence, can regenerate
- Influences pacing and story direction

### 7. **Session Summary** - USER COMMAND not automatic
- ❌ OLD: Automatic periodic summaries
- ✅ NEW: User-triggered command (like `/summary`)
- Forces all agents to update
- Generates chapter summary

### 8. **N vs N+1 Agents** - TIMING CLARIFICATION
- **N agents (Background)**: Run after Response N while user types (~5 seconds)
- **N+1 agents (Immediate)**: Run before Response N+1 to prepare context
- From legacy code comments: "hidden background processing"

### 9. **Tagging** - Already included
- Part of memory creation and entity generation
- Not separate system

### 10. **Legacy Code Found!**
- 7 agents already implemented
- Can PORT instead of building from scratch
- Located in: `C:\Users\green\Desktop\RP Claude Code\src\automation/agents/`

---

## CORRECTED PRIORITY LIST

### 🔴 CRITICAL - Port from Legacy (22-32 hours)
1. ✅ Semantic Triggers - 0.5h (wire existing)
2. ✅ Memory Creation - 4-6h (port)
3. ✅ Relationship Analysis - 4-6h (port)
4. ✅ Fact Extraction - 4-5h (port)
5. ✅ Memory Extraction - 4-5h (port)
6. ✅ Plot Thread Extraction - 4-5h (port)
7. ✅ Plot Thread Detection - 4-6h (port + enhance)

### 🟡 HIGH - New Features (31-40 hours)
8. ❌ Auto-Generate Entity Sheets - 6-8h (Auto-Cards style)
9. ❌ Story Arc Generation - 8-10h (Story Genome system)
10. ❌ Session Summary Command - 6-8h (user-triggered)
11. ❌ General Memory Synthesis - 5-6h (dual-layer)

### 🟢 MEDIUM (16-20 hours)
12. ⚪ Template Validation - 5-6h
13. ⚪ Knowledge Extraction - 4-5h (port from legacy)
14. ⚪ Contradiction Detection - 4-5h (port from legacy)
15. ⚪ Pacing Analysis - 3-4h

---

## REVISED TOTAL: 119-167 hours total (corrected from 122-160)

**Why similar but more accurate?**
- Removed duplicates and outdated items (Template Selection, Memory Consolidation, separate Character/Location updates)
- Combined Entity system into single Create+Update agent (Auto-Cards style)
- Adjusted estimates for dual-layer memory system and Story Arc
- Found legacy implementations to port (saves time!)

**Breakdown:**
- Infrastructure: 4-6h
- Data structures: 4-6h
- Port from legacy: 22-32h (7 agents exist!)
- New features to build: 73-98h
  - Entity Management (both create + update): 8-10h
  - Story Arc/Genome system: (not yet estimated - need user input on structure)
  - General Memory layer: 5-6h
  - Template Validation: 5-6h
  - And more...
- Testing: 10-15h
- Integration: 6-10h

---

## Questions for You

1. **Story Genome structure** - What should this JSON look like?
2. **Auto-entity threshold** - Generate after how many mentions? (3? 5?)
3. **Priority order** - Port legacy first or build new Story Arc system?
4. **Is "N/N+1" understanding correct?**

