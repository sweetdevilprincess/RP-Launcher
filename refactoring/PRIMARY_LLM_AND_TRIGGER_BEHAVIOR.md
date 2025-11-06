# Primary LLM Usage and Trigger System Behavior

**Date:** 2025-10-24
**Questions:**
1. Is the Primary LLM only used for roleplay?
2. Does the trigger system stop after finding one trigger or find multiple?

---

## Question 1: Primary LLM Usage

### ✅ YES - Primary LLM is ONLY used for roleplay

**Evidence:** `src/presentation/bridge/handlers/message_handler.py` (lines 103-147)

```python
# Step 2: Run automation pipeline to build enhanced prompt
automation_result = self.bridge.automation_service.run(context)

# Step 3: Call LLM with enhanced prompt
if capabilities.supports_streaming:
    for chunk in self.bridge.llm_client.stream_message(
        user_message=enhanced_prompt,  # ← ONLY CALL to primary LLM
        cached_context=cached_context
    ):
        # Send response to user
```

**What happens in order:**
1. User sends message
2. Automation pipeline runs (triggers, agents) - **NO LLM calls here**
3. Enhanced prompt is built
4. **Primary LLM is called ONCE** for roleplay response
5. Response is streamed back to user

**The primary LLM is NOT used for:**
- ❌ Trigger evaluation (pure keyword/regex)
- ❌ Agent analysis (not implemented yet)
- ❌ Memory creation (not implemented yet)
- ❌ Context gathering (done by pattern matching)

**Cost:** Only the roleplay response costs money (~$0.03/message)

---

## Question 2: Trigger System Behavior

### ✅ YES - Trigger system finds MULTIPLE entities!

**Evidence:** `src/automation/triggers/coordinator.py` (lines 53-113)

### How It Works

```python
def evaluate_triggers(self, patterns_list, context):
    all_results = []

    # Loop through ALL entity files
    for patterns in patterns_list:  # ← Does NOT stop after first!

        # For each entity, try evaluators in order
        for evaluator in self._evaluators:
            result = evaluator.evaluate(patterns, context)
            if result is not None:
                all_results.append(result)  # ← Adds to list
                break  # ← Only breaks inner loop (tries next entity)

    # Return up to max_results (default: 10)
    return all_results[:max_results]
```

### Behavior Breakdown

**Per Entity File:**
- Tries Keyword evaluator first (fastest)
- If keyword matches: DONE for this entity, move to next entity
- If no keyword match: Try Regex evaluator
- If regex matches: DONE for this entity, move to next entity
- If no regex match: Try Semantic evaluator (if enabled)
- If semantic matches: DONE for this entity
- Move to next entity

**Overall:**
- Evaluates ALL entity files (characters, locations, organizations, items)
- Collects ALL matches (up to 10 max)
- Returns multiple triggered entities

---

## Example Scenario

**User message:** "Alice walked into the garden with her sister to talk about Bob"

**Trigger evaluation:**

| Entity File | Evaluator | Pattern | Result |
|-------------|-----------|---------|--------|
| `characters/Alice.md` | Keyword | "alice" | ✅ MATCH |
| `characters/Bob.md` | Keyword | "bob" | ✅ MATCH |
| `locations/Garden.md` | Keyword | "garden" | ✅ MATCH |
| `characters/Sister.md` | Semantic | "family member" | ✅ MATCH (if semantic enabled) |
| `items/Sword.md` | Keyword | "sword" | ❌ No match |

**Total triggered:** 4 entities (Alice, Bob, Garden, Sister)

**All 4 entity files are loaded and injected into the prompt!**

---

## Configuration

### Max Results
**File:** `src/automation/triggers/coordinator.py:42`
```python
def __init__(self, evaluators, *, max_results: int = 10):
```
- Default: 10 entities max per message
- Configurable via coordinator initialization

### Filters
The system also:
1. **Filters recently triggered files** - Avoids loading same entity repeatedly
2. **Ranks by priority** - Keyword > Regex > Semantic
3. **Deduplicates** - Same entity can't trigger multiple times in one message

---

## Summary Table

| Component | Uses LLM? | Behavior |
|-----------|-----------|----------|
| **Primary LLM** | ✅ Yes | ONLY for roleplay response |
| **Trigger System** | ❌ No (keyword/regex only) | Finds ALL matching entities (up to 10) |
| **Agents** | ❌ Not implemented | Would use secondary LLM when built |

---

## Key Findings

### Primary LLM
- ✅ Used ONLY for roleplay
- ✅ No other calls in the system
- ✅ Cost-efficient design

### Trigger System
- ✅ Finds MULTIPLE entities per message
- ✅ Up to 10 entities max (configurable)
- ✅ Stops at first evaluator match PER entity (performance optimization)
- ✅ Collects ALL entity matches across the entire RP directory

**Your scenario is fully supported:**
- 3 characters in scene: ✅ All detected
- Location mentioned: ✅ Detected
- Nickname used: ✅ Detected (if in triggers)
- Person not in scene: ✅ Still detected and loaded

All triggered entities are loaded and injected into the enhanced prompt before the primary LLM generates the roleplay response.
