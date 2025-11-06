# Trigger System LLM Usage Documentation

**Date:** 2025-10-24
**Question:** Does the trigger system use Claude or just Node/Python logic?

---

## Quick Answer

**Mostly just Node/Python logic** (string matching), with **optional LLM use** for semantic triggers.

The trigger system has **3 types of evaluators**:

1. **KeywordEvaluator** ❌ NO LLM - Pure string matching
2. **RegexEvaluator** ❌ NO LLM - Pattern matching
3. **SemanticEvaluator** ⚠️ OPTIONAL LLM - AI-powered semantic matching

---

## How It Works

### Execution Order (Performance Optimized)

```
User sends message
    ↓
TriggerCoordinator evaluates in order:
    ↓
1. KeywordEvaluator tries first (fastest)
   ├─ Matches? → DONE, skip other evaluators ✅
   └─ No match? → Try next evaluator
    ↓
2. RegexEvaluator tries second (medium speed)
   ├─ Matches? → DONE, skip semantic ✅
   └─ No match? → Try semantic (if enabled)
    ↓
3. SemanticEvaluator tries last (slowest, optional)
   ├─ Has AI client? → Call LLM
   ├─ No AI client? → Skip, return no match
   └─ Result returned
```

**Key point**: For each entity file, the coordinator stops at the **first match**. So if keyword matches, regex and semantic are never tried.

---

## Evaluator Details

### 1. KeywordEvaluator (NO LLM)

**File**: `src/automation/triggers/keyword_evaluator.py`

**What it does**:
- Simple string matching
- Case-insensitive (configurable)
- Word boundary checking (configurable)

**Example**:
```python
# Entity file has: keywords: ["alice", "allie"]
# User message: "Alice walked into the room"
# Result: MATCH (found "alice")
```

**Cost**: FREE - No API calls
**Speed**: ~0.1ms per entity
**When used**: ALWAYS (tried first for every entity)

---

### 2. RegexEvaluator (NO LLM)

**File**: `src/automation/triggers/regex_evaluator.py`

**What it does**:
- Pattern matching with regex
- Supports complex patterns
- More flexible than keywords

**Example**:
```python
# Entity file has: regex: ["alice('s)?", "mention(s|ed)? alice"]
# User message: "I mentioned Alice's sister"
# Result: MATCH (pattern "mention(s|ed)? alice" matches)
```

**Cost**: FREE - No API calls
**Speed**: ~0.5ms per entity (depends on pattern complexity)
**When used**: ALWAYS (tried second if keyword doesn't match)

---

### 3. SemanticEvaluator (OPTIONAL LLM)

**File**: `src/automation/triggers/semantic_evaluator.py`

**What it does**:
- AI-powered semantic understanding
- Matches on meaning, not exact words
- Most flexible but slowest/expensive

**Example**:
```python
# Entity file has: semantic: ["References to Alice", "Alice's family"]
# User message: "I was talking to my sister yesterday"
# LLM analyzes: "sister" semantically relates to "Alice's family"
# Result: MATCH with confidence 0.85
```

**Cost**: ~$0.0001-0.001 per evaluation (if enabled)
**Speed**: ~100-500ms per entity (network call)
**When used**: ONLY IF:
  1. AI client is provided to TriggerRegistry
  2. `triggers.semantic.enabled = true` in config
  3. Keyword and regex both failed to match
  4. Entity has `semantic_descriptions` defined

**Graceful degradation**: If no AI client provided, semantic evaluation is silently skipped.

---

## Configuration

### Registry Creation

**File**: `src/automation/triggers/registry.py`

```python
class TriggerRegistry:
    def __init__(
        self,
        config_service: ConfigService,
        ai_client: AiClient | None = None,  # ← Optional!
    ):
```

**With AI Client** (Semantic enabled):
```python
# Create AI client (e.g., Claude, GPT-4)
ai_client = SemanticAiClient(llm_client=claude_client)

# Create registry with AI
registry = TriggerRegistry(
    config_service=config,
    ai_client=ai_client  # ← Enables semantic
)

evaluators = registry.create_evaluators()
# Returns: [KeywordEvaluator, RegexEvaluator, SemanticEvaluator]
```

**Without AI Client** (Semantic disabled):
```python
# Create registry without AI
registry = TriggerRegistry(
    config_service=config,
    ai_client=None  # ← No semantic evaluation
)

evaluators = registry.create_evaluators()
# Returns: [KeywordEvaluator, RegexEvaluator]
# SemanticEvaluator is NOT created
```

---

## Which LLM Does Semantic Use?

### Current Architecture

**File**: `src/infrastructure/llm/semantic_ai_client.py`

```python
class SemanticAiClient:
    def __init__(
        self,
        llm_client: LLMClient,  # ← Uses your LLMClient interface
        model: str | None = None,
        max_tokens: int = 100,
    ):
```

**The semantic evaluator uses whatever LLMClient you pass to it:**

- Could be Claude (primary conversation LLM)
- Could be OpenAI/GPT-4
- Could be DeepSeek (via OpenRouter)
- Could be mock client (for testing)

### Current Status

**NOT CONFIGURED IN PRODUCTION YET**

The semantic evaluator infrastructure exists, but:
- ❌ No AI client is passed to TriggerRegistry currently
- ❌ No configuration for which LLM to use for semantic
- ❌ UI exists but not wired up

So semantic evaluation is **effectively disabled** right now.

---

## Cost Analysis

### Scenario 1: Pure Keyword/Regex (Current State)

User message triggers 5 entities:
- 5 × Keyword evaluation: FREE
- 2 × Regex evaluation (keyword missed): FREE
- **Total: $0** ✅

### Scenario 2: With Semantic Enabled

User message triggers 5 entities:
- 5 × Keyword evaluation: FREE
- 3 × Regex evaluation: FREE
- 2 × Semantic evaluation: ~$0.002
- **Total: ~$0.002 per message**

### Cost per Month (Semantic Enabled)

Assumptions:
- 100 messages/day
- 2 semantic evaluations per message (avg)
- $0.001 per semantic evaluation

**Monthly cost**: 100 msg × 30 days × 2 evals × $0.001 = **$6/month**

---

## Recommendation

### For Cost Efficiency

**Disable semantic triggers entirely:**
- Keyword + Regex covers 95% of use cases
- Free and fast
- Reliable

**Current state**: Already disabled (no ai_client configured)

### For Advanced Matching

**Enable semantic triggers with cheap LLM:**
- Use DeepSeek via OpenRouter (~$0.0001 per call)
- Only for entities that need semantic understanding
- Configure `semantic_descriptions` only where necessary

---

## Summary

### What Uses LLM?

| Component | Uses LLM? | Which LLM? | Cost | Currently Active? |
|-----------|-----------|------------|------|-------------------|
| **KeywordEvaluator** | ❌ No | N/A | FREE | ✅ Yes |
| **RegexEvaluator** | ❌ No | N/A | FREE | ✅ Yes |
| **SemanticEvaluator** | ⚠️ Optional | Configurable (Claude/GPT/DeepSeek) | ~$0.001/eval | ❌ No (no ai_client) |

### Configuration Files

**Enable/Disable Semantic**:
```yaml
# config/config.json
{
  "triggers": {
    "semantic": {
      "enabled": true,  # Set to false to disable
      "confidence_threshold": 0.7,
      "model": "gpt-4-mini",  # Or "deepseek/deepseek-chat-v3"
      "max_tokens": 100
    }
  }
}
```

**Entity File with Semantic Triggers**:
```yaml
# entities/Alice.md
---
name: Alice
triggers:
  keywords: ["alice", "allie"]  # FREE, fast
  regex: ["alice('s)?"]  # FREE, medium
  semantic:  # OPTIONAL LLM, slow/expensive
    - "References to Alice"
    - "Alice's family or friends"
    - "Discussions about sisters"
---
```

---

## Conclusion

**To directly answer your question:**

The trigger system for "going through all the tags and such" is **mostly just Node/Python logic** (string/pattern matching).

**No LLM is used** unless:
1. You explicitly provide an AI client to TriggerRegistry
2. Enable semantic evaluation in config
3. Define semantic_descriptions in entity files

**Currently**: Semantic evaluation is disabled (no ai_client configured), so everything is FREE string/pattern matching. ✅
