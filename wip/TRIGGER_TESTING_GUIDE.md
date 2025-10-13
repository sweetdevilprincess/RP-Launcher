# Enhanced Trigger System - Testing Guide

## What's New in WIP Bridge

The WIP bridge (`wip/tui_bridge.py`) now uses the **Enhanced Multi-Tier Trigger System** with:

1. **Keyword Matching** (Enhanced)
   - Word boundary protection (no more "Marcusian" false matches!)
   - Case-insensitive matching
   - Fast and reliable

2. **Regex Matching** (New)
   - Pattern matching for possessives: "Marcus's", "Marcus'"
   - Variant matching: "Marc" or "Mark" → triggers Marcus
   - Complex patterns: "Bruno's Restaurant" or "Brunos Cafe"

3. **Semantic Matching** (Optional)
   - AI-powered concept matching
   - "My bodyguard arrived" → triggers Marcus (if he has `protective friend` semantic trigger)
   - Requires: `pip install sentence-transformers`

---

## How to Test

### 1. Update Your Character/Entity Files

Add the new trigger formats to your existing RP character/entity files:

```markdown
# [CHAR] Marcus Thompson

[Triggers:Marcus,Marc,Thompson']
[RegexTriggers:\bMarcus'?s?\b,\b(Marc|Mark)\b']
[SemanticTriggers:protective friend,loyal companion']

**Type**: Character
...
```

**Example files already created in `wip/trigger_system/test_data/`**:
- `characters/Marcus.md` - All three trigger types
- `characters/Sarah.md` - Simple keyword triggers
- `entities/[LOC] Bruno's Restaurant.md` - All three trigger types

### 2. Test Messages to Try

Copy test data to your RP folder or try these messages:

**Keyword Tests:**
- "Marcus is here" → Should trigger Marcus
- "marc said hello" → Should trigger Marcus (case-insensitive)
- "Marcusian empire" → Should NOT trigger (word boundary protection)

**Regex Tests:**
- "Marcus's car is red" → Should trigger (possessive pattern)
- "Mark is here too" → Should trigger (variant pattern)
- "Bruno's Restaurant downtown" → Should trigger location

**Semantic Tests** (if sentence-transformers installed):
- "My bodyguard arrived" → Should trigger Marcus (protective friend)
- "My loyal buddy helped" → Should trigger Marcus (loyal companion)
- "The pasta place downtown" → Should trigger Bruno's (Italian restaurant)

### 3. Check the Logs

Trigger matches are logged to `state/hook.log`:

```
[2025-10-13 12:45:23] --- Using Enhanced Trigger System ---
[2025-10-13 12:45:23] Keyword: True, Regex: True, Semantic: False
[2025-10-13 12:45:23] KEYWORD MATCH: Marcus.md ('Marcus')
[2025-10-13 12:45:23] TRIGGER: Marcus (keyword, pattern: 'Marcus')
[2025-10-13 12:45:23] Conditional files loaded: 1
```

---

## Configuration

The trigger system can be configured in your RP's `state/automation_config.json`:

```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50,

  "trigger_system": {
    "keyword_matching": {
      "enabled": true,
      "case_sensitive": false,
      "use_word_boundaries": true
    },
    "regex_matching": {
      "enabled": true,
      "max_patterns_per_file": 10
    },
    "semantic_matching": {
      "enabled": false,
      "model": "all-MiniLM-L6-v2",
      "similarity_threshold": 0.7
    }
  }
}
```

**Default Config** (if not specified):
- Keyword: ✅ Enabled (case-insensitive, word boundaries)
- Regex: ✅ Enabled (up to 10 patterns per file)
- Semantic: ❌ Disabled (optional, requires sentence-transformers)

---

## Performance

**Speed Ranking:**
1. Keyword: ~0.001ms per file ⚡
2. Regex: ~0.01ms per file ⚡⚡
3. Semantic: ~1-5ms per file ⚡⚡⚡ (with caching)

**Order of Operations:**
- System tries keyword first (fastest)
- Then regex (fast)
- Then semantic (slowest but most intelligent)
- Returns immediately on first match

---

## Enabling Semantic Matching (Optional)

Semantic matching uses AI embeddings to match concepts, not just words.

**Installation:**
```bash
pip install sentence-transformers
```

**First run downloads ~80MB model** (one-time, cached afterward)

**Enable in config:**
```json
"semantic_matching": {
  "enabled": true,
  "model": "all-MiniLM-L6-v2",
  "similarity_threshold": 0.7
}
```

**Example semantic triggers:**
- `protective friend` matches: bodyguard, guardian, protector
- `Italian restaurant` matches: pasta place, trattoria, pizzeria
- `loyal companion` matches: faithful friend, devoted buddy

---

## Troubleshooting

### Triggers Not Working

1. **Check file format:**
   - Must be `[Triggers:word1,word2']` format
   - Must be `[RegexTriggers:pattern1,pattern2']` format
   - Must be `[SemanticTriggers:concept1,concept2']` format

2. **Check logs:**
   - Look in `state/hook.log` for trigger processing
   - Should see "Using Enhanced Trigger System" message

3. **Test with standalone script:**
   ```bash
   cd wip/trigger_system
   python test_triggers.py
   ```

### False Negatives (Should trigger but doesn't)

- For keywords: Try adding more variations to `[Triggers:...]`
- For possessives: Use regex patterns like `\bName'?s?\b`
- For concepts: Try semantic triggers with broader concepts

### False Positives (Triggers when it shouldn't)

- Keyword word boundaries should prevent this (e.g., "Marcusian" won't match "Marcus")
- If still happening, check your trigger list for overly broad terms
- For regex, make sure patterns use `\b` word boundaries

---

## What's Next

1. **Test thoroughly** with your actual RP sessions
2. **Tune the configuration** if needed (thresholds, patterns)
3. **Add semantic triggers** if you want concept-based matching
4. **Report any issues** so we can refine before integrating into main system

When everything works well, we'll integrate this into the main `src/tui_bridge.py`!

---

## Files Modified

- `wip/tui_bridge.py` - Updated to use TriggerMatcher
- `wip/trigger_system/trigger_system.py` - Core trigger matching logic
- `wip/trigger_system/test_triggers.py` - Standalone test suite
- `wip/trigger_system/README.md` - Complete technical documentation

---

**Happy testing!** 🎯
