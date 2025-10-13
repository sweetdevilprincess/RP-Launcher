# Enhanced Trigger System (WIP)

Work-in-progress implementation of the enhanced multi-tier trigger system.

## Status: In Development

This is a development version. Test here before integrating into the main system.

---

## Features

### 1. **Keyword Matching** (Enhanced)
- Word boundaries to avoid false positives
- Case-insensitive option
- Fast and reliable

### 2. **Regex Matching** (New)
- Powerful pattern matching
- Handles possessives, variants, complex patterns
- Pattern caching for performance

### 3. **Semantic Matching** (New)
- AI-powered semantic understanding
- Matches related concepts/synonyms
- Uses sentence-transformers (optional)

---

## Testing

### Quick Test

```bash
cd wip/trigger_system
python test_triggers.py
```

This will run all test suites:
1. Keyword matching tests
2. Regex matching tests
3. Semantic matching tests (if sentence-transformers installed)
4. Combined matching tests

### Test Data

Sample files in `test_data/`:
- `characters/Marcus.md` - All three trigger types
- `characters/Sarah.md` - Simple keyword triggers
- `entities/[LOC] Bruno's Restaurant.md` - All three trigger types

---

## Installation

### Basic (Keyword + Regex)

No additional dependencies needed!

### Semantic Matching (Optional)

For semantic matching, install sentence-transformers:

```bash
pip install sentence-transformers
```

**Note:** This downloads a ~80MB model on first use.

---

## Trigger Syntax

### In Character/Entity Files:

```markdown
# [CHAR] Marcus Thompson

# Keyword triggers (existing, enhanced)
[Triggers:Marcus,Marc,Thompson']

# Regex triggers (new)
[RegexTriggers:\bMarcus'?s?\b,\b(Marc|Mark)\b']

# Semantic triggers (new)
[SemanticTriggers:protective friend,loyal companion']
```

---

## Configuration

Example config dict:

```python
config = {
    'trigger_system': {
        'keyword_matching': {
            'enabled': True,
            'case_sensitive': False,          # Default: False
            'use_word_boundaries': True       # Default: True
        },
        'regex_matching': {
            'enabled': True,
            'max_patterns_per_file': 10       # Limit for safety
        },
        'semantic_matching': {
            'enabled': False,                 # Default: False (requires install)
            'model': 'all-MiniLM-L6-v2',     # Sentence-transformers model
            'similarity_threshold': 0.7,      # 0.0-1.0
            'cache_embeddings': True
        }
    }
}
```

---

## Usage Example

```python
from trigger_system import TriggerMatcher

# Create matcher with config
matcher = TriggerMatcher(config)

# Find triggered files
matches = matcher.find_triggered_files(
    message="Marcus is here",
    rp_dir=Path("test_data"),
    log_callback=print  # Optional logging
)

# Process matches
for match in matches:
    print(f"Triggered: {match.entity_name}")
    print(f"Type: {match.trigger_type}")
    print(f"Pattern: {match.matched_pattern}")
    if match.trigger_type == 'semantic':
        print(f"Confidence: {match.confidence:.2f}")
```

---

## Performance

**Speed Ranking:**
1. Keyword: ~0.001ms per file
2. Regex: ~0.01ms per file
3. Semantic: ~1-5ms per file (with caching)

**Matching Order:**
- Tries keyword first (fastest)
- Then regex (fast)
- Then semantic (slowest)
- Returns on first match

**Optimizations:**
- Regex pattern caching
- Embedding caching
- Early exit on match

---

## Test Results

Run `python test_triggers.py` to see:

### Keyword Tests
- Basic matching
- Case-insensitive
- Word boundaries
- Possessives

### Regex Tests
- Pattern matching
- Multiple variants
- Complex patterns

### Semantic Tests
- Synonym matching
- Concept similarity
- Confidence scores

---

## Next Steps

1. **Test thoroughly** with various messages
2. **Tune configuration** (thresholds, options)
3. **Add more test cases** as needed
4. **Benchmark performance** with large entity sets
5. **Integrate into main system** when ready

---

## Files in WIP

```
wip/trigger_system/
├── trigger_system.py          # Main module
├── test_triggers.py           # Test suite
├── README.md                  # This file
└── test_data/                 # Test files
    ├── characters/
    │   ├── Marcus.md          # All trigger types
    │   └── Sarah.md           # Simple triggers
    └── entities/
        └── [LOC] Bruno's Restaurant.md
```

---

## Questions?

This is WIP! Feel free to:
- Modify test data
- Add new test cases
- Tune configuration
- Experiment with patterns

Test everything here before integrating into the main system!
