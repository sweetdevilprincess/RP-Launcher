# Setup Folder Audit

Comprehensive analysis of outdated, missing, or no longer needed content in the `setup/` folder.

**Date**: 2025-10-16
**Status**: Documentation needs cleanup to match current system

---

## Executive Summary

The setup folder documentation promises several features and guides that don't actually exist, creating a gap between documentation and implementation. Additionally, some sections reference systems or configurations that may be outdated or no longer in use.

**Issues Found**: 12 major documentation/implementation gaps

---

## 1. MISSING GUIDES (Critical)

### Promised But Not Built

| Guide | Status | Referenced In | Impact |
|-------|--------|--------------|--------|
| **01_FIRST_TIME_SETUP.md** | ❌ Missing | README.md line 46 | Users can't find system installation guide |
| **03_UNDERSTANDING_STRUCTURE.md** | ❌ Missing | README.md line 48 | Users can't understand RP folder structure |
| **04_WRITING_YOUR_STORY.md** | ❌ Missing | README.md line 49, template README line 344 | Users lack writing guidance |
| **05_ADVANCED_FEATURES.md** | ❌ Missing | README.md line 50 | Advanced users can't find power user features |
| **99_TROUBLESHOOTING.md** | ❌ Missing | README.md line 51, CHECKLIST.md line 214, template README line 418 | No troubleshooting guide |

**Impact**: README and templates reference these guides but they don't exist. Users following documentation will hit broken links and get frustrated.

**Recommendation**:
- Either build these guides
- Or remove references from README and templates
- Prefer: Build them since they're needed

---

## 2. MISSING TEMPLATES (Medium Priority)

### Promised But Not Built

| Template | Status | Mentioned In | Impact |
|----------|--------|-------------|--------|
| **fantasy_adventure** | ❌ Missing | README.md line 116 (marked "coming soon") | Not blocking - marked as coming soon |
| **modern_romance** | ❌ Missing | README.md line 117 (marked "coming soon") | Not blocking - marked as coming soon |
| **scifi_exploration** | ❌ Missing | README.md line 118 (marked "coming soon") | Not blocking - marked as coming soon |

**Status**: All three are marked "*(coming soon)*" in README, so users aren't expecting them. This is documented correctly.

**However**: The quick_setup.py script only supports "minimal" template (line 137):
```python
choices=["minimal"],  # Add more as they become available
```

**Recommendation**:
- Leave as "coming soon" in README (correct)
- When built, update quick_setup.py to include them

---

## 3. MISSING SCRIPTS/TOOLS (Medium Priority)

### Promised But Not Built

| Script | Status | Mentioned In | Impact |
|--------|--------|-------------|--------|
| **new_rp_wizard.py** | ❌ Missing | README.md line 89 (marked "coming soon") | Not blocking - marked coming soon |
| **validate_rp.py** | ❌ Missing | README.md line 97 (marked "coming soon"), CHECKLIST.md line 216, template README line 381 | Not blocking - marked coming soon |
| **fix_structure.py** | ❌ Missing | README.md line 103 (marked "coming soon") | Not blocking - marked coming soon |
| **migrate_existing.py** | ❌ Missing | Not mentioned, but scripts/ folder is empty | Not mentioned, no broken links |

**Status**: All marked "coming soon" so users aren't expecting them. Scripts/ folder is empty but doesn't break anything.

**Recommendation**:
- These are correctly marked "coming soon"
- Priority order if building: validate_rp.py > fix_structure.py > new_rp_wizard.py > migrate_existing.py

---

## 4. POTENTIALLY OUTDATED REFERENCES

### Technology Stack References

#### A. Node.js / SDK Mode
**Location**: CHECKLIST.md lines 14-20

```markdown
- [ ] Node.js 18+ installed (for SDK mode)
- [ ] Node.js packages installed: `cd src && npm install`
```

**Question**: Is SDK mode still used/maintained?
**Research Needed**: Verify if:
- SDK mode is still part of the system
- Node.js dependencies are still required
- This is still an active code path

**Action**:
- If SDK mode is deprecated: Remove these lines
- If SDK mode is active: Keep as-is
- If unclear: Add note that this is optional

---

#### B. Model Selection Reference
**Location**: CHECKLIST.md line 26, template README.md line 26

```markdown
- Model selected (default: deepseek/deepseek-chat-v3.1)
```

**Question**: Is DeepSeek still the default? Is this model string current?
**Research Needed**: Verify:
- What is the current default model
- What models are available
- Whether OpenRouter or Anthropic API is primary

**Action**: Update to current default model or leave generic

---

### API Configuration References

**Location**: CHECKLIST.md lines 24-26

```markdown
- [ ] OpenRouter API key configured (Press F9 → Settings)
  - Or: Anthropic API key if using API mode
- [ ] Model selected (default: deepseek/deepseek-chat-v3.1)
```

**Question**: Which API is primary? What's the current setup?
**Research Needed**: Verify current API setup in actual launcher

**Action**: Document which API is recommended

---

## 5. F-KEY COMMAND REFERENCES

**Location**: CHECKLIST.md lines 147-156, template README.md lines 322

```markdown
- F1: Help
- F2: Memory
- F3: Arc
- F4: Characters
- F5: Notes
- F6: Entities
- F7: Genome
- F8: Status
- F9: Settings
```

**Question**: Do all these F-key overlays actually exist?
**Research Needed**: Verify these are implemented in TUI

**Action**:
- Verify each F-key actually works
- Update if any are missing or different
- Verify they do what's described

---

## 6. AUTOMATION FEATURES REFERENCES

**Location**: Template README.md lines 196-216, CHECKLIST.md lines 113-120

References to:
- Auto entity cards
- Auto story arc generation
- Auto memory creation
- Entity mention threshold
- Memory frequency tracking

**Question**: How current are these automation features?
**Research Needed**: Verify with current agent system documentation

**Status**: The RP_DIRECTORY_MAP.md we just created documents this - these should be verified against that documentation

**Action**: Cross-reference with actual agent system capabilities

---

## 7. STATE FILE REFERENCES

**Location**: CHECKLIST.md lines 52-57, template README.md lines 232-239

Lists required state files:
- plot_threads_master.md
- current_state.md
- automation_config.json
- entity_tracker.json
- file_tracking.json
- response_counter.json

**Status Check**: According to RP_DIRECTORY_MAP.md, we now have:
- plot_threads_master.md ✅
- plot_threads_archive.md (not mentioned in setup docs)
- knowledge_base.md (not mentioned in setup docs)
- current_state.md ✅
- automation_config.json ✅
- entity_tracker.json ✅
- relationship_tracker.json (not mentioned in setup docs)
- memory_index.json (not mentioned in setup docs)
- file_tracking.json ✅
- response_counter.json ✅
- And many IPC/flag files

**Action**: Update state file list in setup docs to match RP_DIRECTORY_MAP.md

---

## 8. RELATIONSHIP TRACKING SYSTEM

**Location**: Template README.md lines 196-216, CHECKLIST.md line 70

```markdown
**Relationship Tracking** - Automatic relationship tracking (likes/dislikes/hates system)
```

**Question**: Is this system currently active?
**Details**: Mentions:
- Automatic relationship tracking based on personality
- Tier changes (Stranger → Friend → Close Friend)
- Point values for likes/dislikes/hates

**Research Needed**: Verify with current agent system if this is:
- Fully implemented
- Partially implemented
- Still being developed

**Action**: Either document fully or mark as "experimental"

---

## 9. DIRECTORY STRUCTURE DIFFERENCES

**Template Says Should Have** (template README.md line 72):
```
├── state/
│   ├── plot_threads_master.md
│   ├── current_state.md
│   ├── automation_config.json
│   ├── entity_tracker.json
│   ├── file_tracking.json
│   └── response_counter.json
```

**RP_DIRECTORY_MAP.md Shows Should Have**:
- Plus: plot_threads_archive.md
- Plus: knowledge_base.md
- Plus: memory_index.json
- Plus: relationship_tracker.json
- Plus: IPC files (rp_client_input.json, etc.)
- Plus: Flag files
- Plus: hook.log

**Gap**: Setup documentation is incomplete about full state file set

**Action**: Update template and CHECKLIST to include all state files

---

## Conclusion

The setup folder has good structure and mostly complete core functionality (quick_setup.py, minimal template), but documentation makes promises about guides and tools that don't exist yet. This creates a gap between what users are directed to and what actually exists.

**Recommendation**: Before building new features, clean up documentation to match current reality. Then decide what's actually needed and build it systematically.

---

**Last Updated**: 2025-10-16
**Reviewer**: Codebase audit

Related documents:
- RP_DIRECTORY_MAP.md - What actually exists in RPs/
- RP_DIRECTORY_OBSOLESCENCE_AUDIT.md - What's outdated in RPs/
