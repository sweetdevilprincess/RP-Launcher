# Narrative Template Issue - Root Cause Analysis

**Date:** 2025-10-20
**Status:** 🔍 ROOT CAUSE IDENTIFIED

---

## The Problem

Smoke tests fail with:
```
WARNING  narrative_template.auto_not_found | context={"primary": "fantasy"}
```

The narrative template system can't find templates even though the test creates them.

---

## Root Cause: Missing Templates Directory

### Discovery

**Main Refactoring Folder:**
```bash
$ ls "C:\Users\green\Desktop\RP Claude Code\refactoring\config\templates\prompts"
Directory does not exist  # ❌ MISSING!
```

**Worktree Folder (where templates actually exist):**
```bash
$ ls "C:\Users\green\Desktop\RP Claude Code\.worktrees\refactor-d\config\templates\prompts"
action.json
comedy.json
dark_romance.json
dark_romance_thriller.json
grimdark.json
grimdark_horror.json
horror.json
mystery.json
slice_of_life.json
slice_of_life_comedy.json
thriller.json
# ✅ 11 templates exist!
```

### The Mismatch

1. **Templates exist** in worktree but **NOT** in main refactoring folder
2. **No fantasy.json** in either location (test creates it, but it's not part of real templates)
3. **TemplateRegistry expects** templates at `{rp_dir}/config/templates/prompts/`
4. **Directory missing** → Registry returns empty list → Template load fails

---

## How the Template System Works

### Template Discovery Flow

```
1. NarrativeTemplateManager.__init__()
   ├─> Receives TemplateRegistry instance
   └─> TemplateRegistry scans {rp_dir}/config/templates/prompts/*.json

2. generate_narrative_instructions() called
   ├─> mode = "auto" (from config)
   └─> _auto_select_template()
       ├─> _parse_genre_from_overview()
       │   └─> Reads ROLEPLAY_OVERVIEW.md
       │       └─> Finds "**Genre**: Fantasy / Adventure"
       │           └─> Returns ("fantasy", "adventure")
       │
       ├─> _registry.find_composite_template("fantasy", "adventure")
       │   └─> Looks for "fantasy_adventure.json" or "adventure_fantasy.json"
       │       └─> Not found (doesn't exist)
       │
       ├─> _loader.load_template("fantasy")
       │   └─> Tries to load "fantasy.json"
       │       └─> TemplateLoader can't find it
       │           └─> Returns None
       │
       └─> WARNING logged: "narrative_template.auto_not_found"
```

### Template Registry Code

**File:** `src/automation/templates/template_registry.py:129-159`

```python
def _refresh_available_templates(self) -> None:
    """Scan template directory and update available templates list."""
    self._available_templates = []

    if not self._template_dir.exists():
        self._logger.warning(
            "template_registry.directory_not_found",
            context={"template_dir": str(self._template_dir)},
        )
        return  # ❌ Returns empty list if directory missing!

    for template_file in self._template_dir.glob("*.json"):
        template_name = template_file.stem
        self._available_templates.append(template_name)
```

**What Happens:**
1. Registry initialized with `{rp_dir}/config/templates/prompts/`
2. Directory doesn't exist → logs warning → returns empty list
3. Later, when auto mode tries to find "fantasy" template → not in list → fails

---

## Template File Structure

**From:** `config/templates/prompts/action.json`

```json
{
  "genre": "action",
  "display_name": "Action",
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "High energy and kinetic momentum",
        "Clear stakes and immediate danger",
        ...
      ]
    },
    "pacing": { ... },
    "dialogue_style": { ... },
    "scene_construction": { ... },
    "descriptive_focus": { ... },
    "common_pitfalls": { ... }
  },
  "highlights": [
    "High energy with clear choreography",
    "Competence on display",
    ...
  ]
}
```

**Available Templates (in worktree):**
- action
- comedy
- dark_romance
- dark_romance_thriller (composite)
- grimdark
- grimdark_horror (composite)
- horror
- mystery
- slice_of_life
- slice_of_life_comedy (composite)
- thriller

**Missing Templates:**
- fantasy ❌ (test creates it, but not in real collection)
- fantasy_adventure ❌
- adventure ❌
- Many other genres likely needed

---

## Why Tests Fail

### Smoke Test Scenario

**Test Creates:**
```python
# File: tests/automation/test_automation_smoke.py:92-119
fantasy_template = {
    "display_name": "Fantasy Adventure",
    "sections": { ... },
    "highlights": [ ... ]
}
(tmp_path / "config" / "templates" / "prompts" / "fantasy.json").write_text(
    json.dumps(fantasy_template, indent=2), encoding="utf-8"
)
```

**What Should Happen:**
1. Test creates `{tmp_path}/config/templates/prompts/fantasy.json` ✅
2. TemplateRegistry initialized with `{tmp_path}/config/templates/prompts/` ✅
3. Registry scans directory, finds fantasy.json ✅
4. Auto mode detects "fantasy" genre ✅
5. Loads fantasy.json and renders template ✅

**What Actually Happens:**
1. Test creates fantasy.json ✅
2. TemplateRegistry initialized... but with WHAT path? 🤔
3. Registry may be looking in wrong directory OR
4. Registry initialized before test creates file OR
5. Something else prevents discovery

### Investigation Needed

Need to add debug logging to see:
1. What path is TemplateRegistry actually using?
2. Does the directory exist when Registry scans?
3. What files does Registry find during scan?
4. Is Registry cached or refreshed?

---

## Solution Options

### Option 1: Copy Templates to Main Refactoring Folder (IMMEDIATE)

**Action:**
```bash
mkdir -p "C:\Users\green\Desktop\RP Claude Code\refactoring\config\templates\prompts"
cp "C:\Users\green\Desktop\RP Claude Code\.worktrees\refactor-d\config\templates\prompts"/*.json \
   "C:\Users\green\Desktop\RP Claude Code\refactoring\config\templates\prompts/"
```

**Pros:**
- Simple, immediate fix
- Matches expected structure
- Works for real RP directories

**Cons:**
- Doesn't fix the smoke test issue (tmp_path still different)
- Need to create missing templates (fantasy, adventure, etc.)

### Option 2: Create Missing Templates

**Templates to Create:**
- fantasy.json
- fantasy_adventure.json (composite)
- adventure.json
- sci_fi.json
- sci_fi_adventure.json
- romance.json
- ... and others as needed

**Pros:**
- Comprehensive template coverage
- Supports auto mode for common genres

**Cons:**
- More work
- Need to design content for each genre

### Option 3: Fix Test to Use Existing Templates

**Action:**
Change smoke test to use existing genre like "action" instead of "fantasy"

**Pros:**
- Quick test fix
- Uses real templates

**Cons:**
- Doesn't test auto mode properly
- Fantasy is common genre, should exist

### Option 4: Add Template Fallback Logic

**Action:**
If template not found, generate generic template or use empty placeholder

**Pros:**
- Graceful degradation
- Works even without templates

**Cons:**
- Masks the real issue
- Less helpful for users

---

## Recommended Approach

### Phase 1: Immediate Fixes

1. **Copy existing templates to main folder:**
   ```bash
   mkdir -p refactoring/config/templates/prompts
   cp .worktrees/refactor-d/config/templates/prompts/*.json refactoring/config/templates/prompts/
   ```

2. **Create fantasy.json template:**
   ```json
   {
     "genre": "fantasy",
     "display_name": "Fantasy",
     "sections": {
       "tone_and_atmosphere": {
         "title": "Tone & Atmosphere",
         "content": [
           "Epic and heroic storytelling",
           "Sense of wonder and discovery",
           "Magic woven into the world naturally",
           "Good vs evil themes with nuance"
         ]
       },
       ...
     },
     "highlights": [
       "Magic and mythical creatures",
       "Epic quests and world-building"
     ]
   }
   ```

3. **Add debug logging to TemplateRegistry:**
   ```python
   self._logger.debug(
       "template_registry.scan_complete",
       context={
           "directory": str(self._template_dir),
           "directory_exists": self._template_dir.exists(),
           "files_found": self._available_templates,
       }
   )
   ```

### Phase 2: Investigation

1. Run smoke test with verbose logging
2. Check what path is actually used
3. Verify file discovery logic
4. Fix any remaining issues

### Phase 3: Template Expansion

1. Create common genre templates:
   - fantasy, adventure, sci_fi
   - romance, urban_fantasy, historical
   - cyberpunk, steampunk, western

2. Create common composites:
   - fantasy_adventure
   - sci_fi_thriller
   - urban_fantasy_mystery

3. Test with various genres

---

## Related Files

**Template System:**
- `src/automation/templates/template_registry.py` - Discovery
- `src/automation/templates/template_loader.py` - Loading
- `src/automation/templates/narrative_template_manager.py` - Auto mode
- `src/automation/templates/template_cache.py` - Caching

**Tests:**
- `tests/automation/test_automation_smoke.py` - Creates fantasy.json
- `tests/automation/templates/test_template_loader.py` - Template loading tests
- `tests/automation/templates/test_template_cache.py` - Cache tests

**Existing Templates:**
- `.worktrees/refactor-d/config/templates/prompts/*.json` (11 templates)

---

## Next Steps

1. ✅ Document issue (this file)
2. ⏸️ Copy existing templates to main folder
3. ⏸️ Create fantasy.json template
4. ⏸️ Add debug logging to Registry
5. ⏸️ Run smoke tests with logging
6. ⏸️ Fix discovery issues if any
7. ⏸️ Create additional common templates
8. ⏸️ Test with real RP directory

---

*Created: 2025-10-20 23:30*
*Status: Ready for implementation*
*Priority: MEDIUM (tests work enough to proceed, but should fix for production)*
