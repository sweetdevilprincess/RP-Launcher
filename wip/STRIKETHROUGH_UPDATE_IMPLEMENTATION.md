# Strikethrough Update Implementation - Summary

**Date**: January 2025
**Status**: ✅ Ready for Testing

---

## Overview

Implemented strikethrough formatting for DeepSeek auto-generated entity cards to preserve character history. When entity information changes (job, living situation, relationships, etc.), the old information is preserved with strikethrough and the new information is added.

**Example**: `~~Barista~~ → Legal Assistant` shows career progression over time.

---

## Files Modified

### 1. Created: `config/guidelines/DeepSeek_Update_Format_Guide.md`
**Status**: ✅ Complete (Production-ready)

Comprehensive guide for DeepSeek with:
- Strikethrough formatting rules
- Examples for all update scenarios (job, living situation, relationships, appearance, personality)
- Good vs bad examples
- Update checklist
- 500+ lines of detailed guidance

**Location**: Already in production folder

---

### 2. Updated: `wip/tui_bridge.py`
**Status**: ✅ Ready for deployment

**Function Modified**: `auto_generate_entity_card()` (lines 539-696)

**Key Changes**:
```python
# 1. Check if entity card already exists
if card_file.exists():
    existing_card = card_file.read_text()
    is_update = True

# 2. Two different prompts:
if is_update:
    # UPDATE prompt with strikethrough instructions
    prompt = """UPDATE existing card...
    CRITICAL: Use ~~old~~ → new for all changes
    NEVER delete old information
    ...detailed instructions..."""
else:
    # CREATE prompt (original, no strikethrough)
    prompt = """Create new card..."""

# 3. Better logging
if is_update:
    log("[SUCCESS] Updated entity card with strikethrough formatting")
else:
    log("[SUCCESS] Auto-generated new entity card")
```

**Benefits**:
- ✅ Detects existing cards automatically
- ✅ Preserves all historical information
- ✅ Uses different prompts for create vs update
- ✅ Clear logging to distinguish updates from new cards
- ✅ No breaking changes - creates work exactly as before

---

### 3. Updated: `wip/TEMPLATE_ENTITY_CHARACTER.md`
**Status**: ✅ Ready for deployment

**Added**:
- Strikethrough format guide comment at top
- Change Log section for tracking updates
- Living Situation section (new)
- Employment section with strikethrough examples
- Example updates in every section
- HTML comments explaining never to delete appearances

**New Sections**:
```markdown
## Change Log
- Track significant changes with dates

## Living Situation
- ~~old~~ → new format

## Employment
- Job history with strikethrough

[All other sections have example updates]
```

**Example snippets throughout**:
- `~~24~~ 25-year-old` (age change)
- `~~Lives alone~~ → Lives with boyfriend` (living situation)
- `~~Barista~~ → Legal assistant` (job change)
- `~~Single~~ → Dating Marcus (Ch. 3+)` (relationship)

---

## How It Works

### New Entity Card Creation
**Trigger**: Entity mentioned 2+ times (threshold), no existing card

**Process**:
1. DeepSeek creates NEW card using original prompt
2. No strikethrough formatting (nothing to update)
3. Standard format with all sections
4. Saves to `entities/[CHAR] Name.md`

**Log**: `[SUCCESS] Auto-generated new entity card: entities/[CHAR] Name.md`

---

### Existing Entity Card Update
**Trigger**: Entity mentioned again, card already exists

**Process**:
1. System detects existing card file
2. Reads current card content
3. Sends to DeepSeek with UPDATE prompt including:
   - Existing card content
   - New context from recent chapters
   - Strikethrough formatting rules
   - Examples of correct updates
4. DeepSeek updates card with `~~old~~ → new` format
5. Overwrites existing file with updated version

**Log**: `[SUCCESS] Updated entity card with strikethrough formatting: entities/[CHAR] Name.md`

---

## Example Scenario

### Response 1-2: Character First Appears
```
Sarah mentioned → Entity tracker: 1 mention
Sarah mentioned again → Entity tracker: 2 mentions → THRESHOLD REACHED
```

**Auto-generation triggers**:
```markdown
# [CHAR] Sarah

[Triggers:Sarah']
**Type**: Character
**Mention Count**: 2

## Living Situation
- Lives alone in downtown apartment

## Employment
- Barista at Coffee Corner Cafe
```

---

### Response 10: Character's Life Changes
Story context: "Sarah quit the cafe and moved in with Marcus"

```
Sarah mentioned → Entity tracker: 10 mentions
Card already exists → UPDATE MODE
```

**Auto-generation triggers UPDATE**:
```markdown
# [CHAR] Sarah

[Triggers:Sarah']
**Type**: Character
**Mention Count**: 10

## Change Log
- **January 2025**: Updated living situation (moved in with partner), job change

## Living Situation
- ~~Lives alone in downtown apartment~~ → Lives with boyfriend Marcus in his house (Chapter 5+)

## Employment
- ~~Barista at Coffee Corner Cafe (Ch. 1-4)~~ → Looking for new job (Chapter 5+)
```

---

### Response 15: Gets New Job
Story context: "Sarah started her new job at Morrison Law"

```
Sarah mentioned → Entity tracker: 15 mentions
Card exists → UPDATE MODE again
```

**Auto-generation updates AGAIN**:
```markdown
## Employment
- ~~Barista at Coffee Corner Cafe (Ch. 1-4)~~ → ~~Looking for new job (Chapter 5)~~ → Legal Assistant at Morrison & Associates (Chapter 6+)
```

**Result**: Full career progression visible at a glance!

---

## Testing Plan

### Test 1: New Entity Creation
1. Start fresh RP or use test RP
2. Mention new character "TestChar" 2 times
3. Verify auto-generation creates NEW card
4. Check format is standard (no strikethrough)
5. **Expected log**: `[SUCCESS] Auto-generated new entity card`

### Test 2: Entity Update - Job Change
1. Use card from Test 1
2. Edit card: Add "Job: Barista"
3. Mention TestChar 3 more times with new context: "TestChar the lawyer"
4. Verify auto-generation UPDATES card
5. Check strikethrough: `~~Barista~~ → Lawyer`
6. **Expected log**: `[SUCCESS] Updated entity card with strikethrough formatting`

### Test 3: Entity Update - Multiple Changes
1. Edit card: Add living situation, relationship status
2. Mention character with context showing changes
3. Verify multiple sections updated with strikethrough
4. Check all old information preserved

### Test 4: Verify No Breaking Changes
1. Delete entity card
2. Trigger auto-generation
3. Verify creates new card (original behavior still works)

---

## Deployment Steps

### Option 1: Quick Deploy (Replace files)
```bash
# Backup originals
cp src/tui_bridge.py src/tui_bridge.py.backup
cp config/templates/TEMPLATE_ENTITY_CHARACTER.md config/templates/TEMPLATE_ENTITY_CHARACTER.md.backup

# Deploy from wip
cp wip/tui_bridge.py src/tui_bridge.py
cp wip/TEMPLATE_ENTITY_CHARACTER.md config/templates/TEMPLATE_ENTITY_CHARACTER.md

# Note: DeepSeek_Update_Format_Guide.md already in production
```

### Option 2: Gradual Deploy (Test first)
1. Copy wip/tui_bridge.py to test RP folder
2. Test with that RP only
3. Verify strikethrough updates work
4. Deploy to main src/ when confident

### Option 3: Keep Both (Feature Flag)
Add config option to toggle strikethrough updates:
```json
{
  "use_strikethrough_updates": true
}
```

---

## Benefits

### For Users
- ✅ Never lose character history
- ✅ See character evolution at a glance
- ✅ Understand when changes happened
- ✅ Track relationship progression
- ✅ Career history visible

### For Story Continuity
- ✅ Easy to reference past states
- ✅ Clear timeline of character development
- ✅ Prevents contradictions
- ✅ Shows character growth

### Technical
- ✅ No breaking changes
- ✅ Backward compatible
- ✅ Automatic (no manual work)
- ✅ Well-documented
- ✅ Easy to test

---

## Potential Issues & Solutions

### Issue 1: DeepSeek doesn't follow strikethrough format
**Solution**: The prompt is very detailed with examples. If it still doesn't work:
- Make examples even more explicit
- Add "YOU WILL BE PENALIZED FOR DELETING INFORMATION" warning
- Use few-shot examples in prompt

### Issue 2: Card gets too cluttered with updates
**Solution**:
- Natural - shows realistic character evolution
- Could add "History" section to move old strikethrough data
- Could summarize very old changes

### Issue 3: Update prompt too long
**Current size**: ~50 lines for update prompt
**Token count**: ~400 tokens
**Solution**: Should be fine, but can optimize if needed

### Issue 4: Accidentally updates when shouldn't
**Solution**: System only updates when:
- Card file already exists
- File is readable
- Still creates new card if any issues

---

## Future Enhancements

### 1. Update Story Arcs with Strikethrough
Apply same logic to `auto_generate_story_arc()`:
- Track plot direction changes
- Show when story diverged from genome
- Preserve old arc beats with strikethrough

### 2. Change Summaries
Add section showing all changes in one place:
```markdown
## Change Summary
- **Chapter 3**: ~~Single~~ → Dating Marcus
- **Chapter 5**: ~~Barista~~ → Looking for job, ~~Lives alone~~ → Lives with Marcus
- **Chapter 6**: ~~Looking for job~~ → Legal assistant
```

### 3. Visual Timeline
Generate visual timeline of character evolution

### 4. Diff View
Allow viewing card with/without strikethrough for clean reading

---

## File Locations

```
Production (Current):
├── src/tui_bridge.py (unchanged, original version)
├── config/templates/TEMPLATE_ENTITY_CHARACTER.md (unchanged)
└── config/guidelines/DeepSeek_Update_Format_Guide.md ✅ (NEW, already deployed)

WIP (Ready for deployment):
├── wip/tui_bridge.py ✅ (updated with strikethrough logic)
├── wip/TEMPLATE_ENTITY_CHARACTER.md ✅ (updated with examples)
└── wip/DeepSeek_Update_Format_Guide.md (copy of production)
```

---

## Rollback Plan

If issues occur after deployment:

```bash
# Restore from backups
cp src/tui_bridge.py.backup src/tui_bridge.py
cp config/templates/TEMPLATE_ENTITY_CHARACTER.md.backup config/templates/TEMPLATE_ENTITY_CHARACTER.md

# Or keep using wip folder
python launch_rp_tui.py  # will use production files
# vs
python wip/tui_bridge.py  # test mode
```

---

## Summary

✅ **Strikethrough update system is ready for deployment**

**What's done**:
- Comprehensive formatting guide (production-ready)
- Updated entity card generation logic (WIP)
- Updated template with examples (WIP)
- Full documentation

**Next steps**:
1. Test in WIP folder with test RP
2. Verify strikethrough updates work correctly
3. Deploy to production when confident
4. Monitor entity card updates in active RPs

**Impact**: Minimal risk, significant benefit. System falls back gracefully if any issues.

---

## Questions?

- Check `config/guidelines/DeepSeek_Update_Format_Guide.md` for formatting rules
- See examples in `wip/TEMPLATE_ENTITY_CHARACTER.md`
- Review `wip/tui_bridge.py` lines 539-696 for implementation details

---

**Ready to test and deploy!** 🚀
