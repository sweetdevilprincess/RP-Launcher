# RP System for Claude Code - Project Status & Roadmap

**Last Updated**: October 11th, 2025
**Project Status**: ✅ Core System Complete + Automation Implemented
**Next Phase**: Integration of Webapp Writing Quality Systems

---

## 📋 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [What We've Built](#what-weve-built)
3. [System Architecture](#system-architecture)
4. [Recent Additions](#recent-additions)
5. [What's Working Now](#whats-working-now)
6. [Costs & Performance](#costs--performance)
7. [Recent Discovery](#recent-discovery)
8. [Planned Improvements](#planned-improvements)
9. [File Structure](#file-structure)
10. [Quick Start Guide](#quick-start-guide)

---

## PROJECT OVERVIEW

### Goal
Create a comprehensive RP (roleplay) system for Claude Code that:
- Automates tracking and management
- Maintains story continuity
- Keeps costs very low
- Produces high-quality writing
- Works seamlessly with Claude Code's capabilities

### Background
- User previously used Claude webapp with extensive custom project instructions
- Wanted to migrate to Claude Code for better tooling
- Needed automation features like AI Dungeon (entity cards, story arcs)
- Required cost optimization (DeepSeek integration)

### Current Status
**✅ PHASE 1 COMPLETE**: Core system with full automation
**🔄 PHASE 2 STARTING**: Adding webapp's writing quality systems

---

## WHAT WE'VE BUILT

### ✅ Complete Features (Working Now)

#### 1. **Folder Structure & Organization**
- Clean, hierarchical RP project structure
- Separation of: guidelines, templates, commands, hooks, state
- Example RP folder fully populated with all necessary files

#### 2. **Automated Time Tracking**
- Hook calculates time from user activities
- References `guidelines/Timing.txt` (100+ activities)
- Suggests elapsed time with activity breakdown
- Claude decides final timestamp

#### 3. **Automated Entity Card Generation** 🆕
- Tracks entity mentions in `state/entity_tracker.json`
- When entity hits 2 mentions (configurable) → Auto-generates card
- Uses DeepSeek via OpenRouter (~$0.001 per card)
- Creates cards with AI Dungeon-style triggers
- Cards auto-load on future mentions

#### 4. **Automated Story Arc Generation** 🆕
- Every 50 responses (configurable) → Auto-generates arc
- 11-beat future arc (AI Dungeon format: <7 words each)
- Full arc summary with Genome comparison
- Uses Claude's main context (FREE)

#### 5. **Conditional File Loading**
- Trigger system loads relevant entity/character files
- AI Dungeon format: `[Triggers:word1,word2,word3']`
- Exact match including punctuation
- Hook scans user messages and injects matching files

#### 6. **Session Management Commands**
- `/continue` - Loads context and last RP response
- `/endSession` - Complete session end protocol
- `/arc` - Generate/update story arc
- `/gencard [type], [name]` - Create entity cards
- `/note [text]` - Quick notes with routing
- `/memory` - Update character memory

#### 7. **Cost Optimization**
- DeepSeek integration via OpenRouter API
- Reusable script: `scripts/deepseek_call.sh`
- Hybrid approach: Claude analyzes, DeepSeek updates
- Character updates, memory, entity cards use cheap DeepSeek

#### 8. **Comprehensive Documentation**
- `CLAUDE.md` - Main instructions
- `RP_FOLDER_STRUCTURE.md` - Folder guide
- `COMMANDS_README.md` - All commands documented
- `HOOKS_README.md` - Hook system explained
- `Session_End_Protocol.md` - Detailed protocol
- `AUTOMATION_CONFIG_README.md` - Configuration guide

#### 9. **Template System**
- 8 templates for all file types:
  - Entity templates (character, location, item, event)
  - Core RP templates (overview, Author's Notes, Genome, Scene Notes)
  - State templates (current state, story arc, entity tracker)
  - Automation config template

#### 10. **Example RP - "The Roommate"**
- Fully populated example RP folder
- Complete with all core files
- 3 character sheets ({{user}}, Alex, Sarah)
- Chapter 2 summary (full example)
- Demonstrates all features in action

---

## SYSTEM ARCHITECTURE

### Core Components

```
RP Claude Code/
├── .claude/
│   ├── commands/          # 7 slash commands
│   └── hooks/             # Automation hook
├── guidelines/            # Shared resources (Timing.txt, protocols)
├── templates/             # 8 reusable templates
├── scripts/               # DeepSeek API script
├── Example RP/            # Complete example
│   ├── Core Files:
│   │   ├── Example RP.md
│   │   ├── AUTHOR'S_NOTES.md
│   │   ├── STORY_GENOME.md
│   │   └── SCENE_NOTES.md
│   ├── characters/        # Character sheets
│   ├── entities/          # Entity cards (auto-generated)
│   ├── chapters/          # Chapter summaries
│   ├── sessions/          # Session chatlogs
│   └── state/             # Tracking files + automation config
├── CLAUDE.md              # Main instructions
└── [Documentation files]
```

### Data Flow

```
User types message
  ↓
Hook runs (user-prompt-submit.sh)
  ↓
Hook performs:
  - Increment response counter
  - Calculate time from activities
  - Track entity mentions (update JSON)
  - Check for entity threshold → Auto-generate card (DeepSeek)
  - Check for arc threshold → Trigger arc generation (Claude)
  - Scan for triggers → Inject matching files
  ↓
Claude receives:
  - User message
  - Hook suggestions (time, entities)
  - Injected files (triggered entities/characters)
  - Arc generation trigger (if threshold)
  ↓
Claude responds with:
  - Updated RP response
  - Accurate timestamp
  - References loaded entities
  - Generated arc (if triggered)
```

---

## RECENT ADDITIONS

### Last Session Accomplishments

#### 1. Automatic Entity Card Generation
**Problem**: User had to manually run `/gencard` for every entity
**Solution**: Hook tracks mentions, auto-generates at threshold
**Implementation**:
- Enhanced `track_entities()` function with jq JSON updates
- Added `auto_generate_entity_card()` function
- Searches recent chapters for context
- Calls `deepseek_call.sh` with prompt
- Saves to `entities/[CHAR] Name.md`
- Marks as "card_created" to avoid duplicates

**Testing**: Successfully generated Sarah Mitchell card in Example RP

#### 2. Automatic Story Arc Generation
**Problem**: User had to remember to run `/arc` every 50 responses
**Solution**: Hook auto-triggers arc generation at response threshold
**Implementation**:
- Modified `increment_counter()` to check frequency
- Added `auto_generate_arc()` function
- Injects instructions for Claude to generate arc
- Claude reads Genome + chapters + state
- Generates 11-beat arc + full summary
- Saves to `state/story_arc.md`

**Cost**: FREE (uses Claude's main context)

#### 3. Configuration System
**Created**: `state/automation_config.json`
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

**Features**:
- Toggle automation on/off
- Adjust thresholds
- Changes apply immediately (no restart)
- Template in `templates/` folder

#### 4. Reusable DeepSeek Script
**Created**: `scripts/deepseek_call.sh`
- Handles all DeepSeek API calls
- Takes prompt as input
- Returns generated content
- Used by entity cards, memory, character updates

**Testing**: Successfully called OpenRouter, verified in user's account

#### 5. Complete Documentation Update
- Updated `HOOKS_README.md` with automation features
- Updated `COMMANDS_README.md` with auto vs manual usage
- Created `AUTOMATION_CONFIG_README.md` for configuration
- Updated cost breakdowns

---

## WHAT'S WORKING NOW

### ✅ Fully Functional

1. **Manual Commands**: All 7 commands work
2. **Automation**: Entity cards + story arcs auto-generate
3. **Time Tracking**: Hook calculates and suggests time
4. **Trigger Loading**: Entity/character files auto-load
5. **Session Management**: /continue and /endSession work
6. **Cost Optimization**: DeepSeek integration operational
7. **Example RP**: Complete working example

### ✅ Tested & Verified

- DeepSeek API calls work (tested with Sarah Mitchell card)
- OpenRouter account charged correctly (~$0.001 per card)
- Hook executes without errors
- Configuration system loads properly
- JSON tracking updates correctly

### 📊 Performance Metrics

**Typical Session (30 responses, 3 new entities)**:
- Entity cards: 3 × $0.001 = $0.003
- Story arc: Not reached = $0.00
- Total automation: ~$0.003

**At 50 Responses (5 new entities)**:
- Entity cards: 5 × $0.001 = $0.005
- Story arc: 1 × FREE = $0.00
- Total automation: ~$0.005

**With /endSession**:
- Session end: ~$0.02-0.05
- Total session: ~$0.025-0.055

**Very affordable!**

---

## COSTS & PERFORMANCE

### Current Cost Structure

| Feature | Cost | Frequency | Method |
|---------|------|-----------|--------|
| Hook execution | $0 | Every response | Local bash |
| Entity tracking | $0 | Every response | Local JSON |
| Time calculation | $0 | Every response | Local lookup |
| Trigger detection | $0 | Every response | Local grep |
| **Entity card** | **~$0.001** | **2+ mentions** | **DeepSeek** |
| Story arc | $0 | Every 50 responses | Claude context |
| Memory update | ~$0.0005 | /endSession | DeepSeek |
| Character updates | ~$0.001 each | /endSession | DeepSeek |
| Session end | ~$0.02-0.05 | Manual | Claude + DeepSeek |

### Token Usage Estimates

**Without optimization** (loading everything every time):
- ~8,000-12,000 tokens per response
- Includes all files, all entities, all guidelines

**With current system** (selective loading):
- ~4,000-6,000 tokens per response (TIER_1 files + triggered entities)
- Saves ~40-50% tokens

**Potential with tiered system** (planned):
- TIER_1: ~3,000 tokens (core files)
- TIER_2 (every 4th): +2,000 tokens (references)
- TIER_3: +500-2,000 tokens (conditional)
- Average: ~3,500 tokens per response (30% additional savings)

---

## RECENT DISCOVERY

### Webapp System Analysis

**Found**: User's old Claude webapp project instructions in root folder
- `Claude Project instructions Webapp.md` (75KB)
- `NPC_Interaction_Rules.md`
- `POV_and_Writing_Checklist.md`
- `Writing_Style_Guide.md`
- `Time_Tracking_Guide.md`
- `Story Guidelines.md`

**Created**: `WEBAPP_VS_CLAUDECODE_ANALYSIS.md` - Complete comparison

### Key Findings

**Old System Had Excellent**:
1. ⭐⭐⭐ POV Enforcement (red flag checkers, translation guides)
2. ⭐⭐⭐ Writing Style Templates (scene-specific: suspense, intimate, dialogue)
3. ⭐⭐⭐ NPC Response Control (prevents monologues, maintains pacing)
4. ⭐⭐⭐ Tiered Document Loading (TIER_1, TIER_2, TIER_3 with modulo)
5. ⭐⭐⭐ Chapter Trigger System (dialogue triggers load past chapters)
6. ⭐⭐ NPC Reaction Protocol (6-step systematic reactions)
7. ⭐⭐ Information Revelation Protocol (tracks what NPCs know)
8. ⭐ Gate Quality Control (multi-gate verification system)

**New System Excels At**:
- ✅ Automation (hooks, auto-generation)
- ✅ Cost optimization (DeepSeek, selective loading)
- ✅ Session management (clean boundaries)
- ✅ Modern tooling (works with Claude Code)

**Best of Both Worlds**: Keep new automation, add old writing quality systems

---

## PLANNED IMPROVEMENTS

### Phase 1: Organize Existing Guides ⭐⭐⭐
**Priority**: HIGHEST
**Time**: 30 minutes
**Impact**: HIGH - Immediate writing quality improvement

**Tasks**:
1. Move existing guide files to `guidelines/` folder:
   - `NPC_Interaction_Rules.md`
   - `POV_and_Writing_Checklist.md`
   - `Writing_Style_Guide.md`
   - `Time_Tracking_Guide.md`
   - `Story Guidelines.md`

2. Update `CLAUDE.md` to reference them in priority order

3. Update Example RP's AUTHOR'S_NOTES to reference POV checklist

**Result**: Access to all writing quality systems immediately!

---

### Phase 2: Tiered Document Reference System ⭐⭐⭐
**Priority**: HIGH
**Time**: 2-3 hours
**Impact**: MEDIUM-HIGH - Reduces costs 20-30%

**Implementation**:

```markdown
## DOCUMENT_REFERENCE_MANAGEMENT

### TIER_1_MANDATORY_EVERY_RESPONSE
- AUTHOR'S_NOTES.md (story rules)
- STORY_GENOME.md (intended path)
- SCENE_NOTES.md (session guidance)
- state/current_state.md (timestamp/location)
- state/story_arc.md (current progress)
- characters/{{user}}.md
- characters/{{char}}.md

### TIER_2_PERIODIC_EVERY_4TH_RESPONSE
(Load when response_count % 4 == 0)
- guidelines/Timing.txt
- guidelines/Writing_Style_Guide.md
- guidelines/NPC_Interaction_Rules.md
- [RP_Name].md (overview)
- [Additional large reference files]

### TIER_3_CONDITIONAL_WITH_ESCALATION
(Load when triggered, escalate to TIER_2 if triggered 3+ times in 10 responses)
- Entity cards (triggered by mentions)
- Chapter summaries (triggered by dialogue)
- Scene-specific guidelines (triggered by scene type)
```

**Hook Changes**:
- Track response count for modulo calculation
- Track TIER_3 trigger frequency
- Implement escalation system

**Benefits**:
- Large files (Timing, Style Guide) only loaded every 4 responses
- Reduces token usage significantly
- Maintains quality with periodic refreshers

---

### Phase 3: Chapter Trigger System ⭐⭐⭐
**Priority**: HIGH
**Time**: 3-4 hours
**Impact**: HIGH - Creates story continuity

**Implementation**:

1. **Create Trigger Database** (`state/chapter_triggers.json`):
```json
{
  "chapter_2": {
    "emotional_triggers": ["first time", "when we met", "that night"],
    "dialogue_triggers": ["remember when", "you said"],
    "character_triggers": ["Sarah", "Marcus"],
    "location_triggers": ["coffee shop", "restaurant"],
    "event_triggers": ["first date", "moving in"]
  }
}
```

2. **Add Trigger Scanning to Hook**:
```bash
scan_chapter_triggers() {
  # Scan user message for trigger keywords
  # Weight by recency, relevance, relationship state
  # Select 1-3 most relevant chapters
  # Inject chapter content for Claude to reference
}
```

3. **Chapter Content Structure**:
- Full chapter summaries in `chapters/`
- Key quotes preserved
- Important events highlighted
- Emotional beats noted

**Example Flow**:
```
User: "Remember when we first met at the coffee shop?"
  ↓
Hook detects: "remember when", "first met", "coffee shop"
  ↓
Matches Chapter 1 (first meeting) + Chapter 2 (coffee shop date)
  ↓
Loads both chapters into context
  ↓
Claude weaves memory into response naturally
```

**Benefits**:
- Automatic story continuity
- References past events accurately
- Maintains relationship history
- User doesn't need to specify chapters manually

---

### Phase 4: POV Enforcement Enhancement ⭐⭐
**Priority**: MEDIUM
**Time**: 1-2 hours
**Impact**: MEDIUM - Improves POV consistency

**Implementation**:

1. Add POV checklist to AUTHOR'S_NOTES.md:
```markdown
## POV RED FLAGS - MANDATORY CHECK

Before every response, scan for violations:
🚩 "He felt..." → Change to physical observation
🚩 "He knew..." → Change to action/dialogue
🚩 "He wanted..." → Change to suggested behavior
🚩 Certainty about emotions → Add uncertainty language
🚩 Information {{user}} can't know → Remove
```

2. Add character-specific observable tells to character sheets

3. Create POV translation reference in guidelines

**Benefits**:
- Eliminates POV violations
- Maintains immersion
- Character thoughts stay private unless spoken

---

### Phase 5: NPC Management Systems ⭐
**Priority**: MEDIUM-LOW
**Time**: 3-4 hours
**Impact**: MEDIUM - Better NPC consistency

**Optional Features**:

1. **NPC Reaction Protocol**: 6-step systematic reactions
2. **Information Revelation Matrix**: Track what NPCs know
3. **Response Scope Enforcement**: Prevent monologues

**Implementation**:
- Add protocols to guidelines
- Create knowledge tracking in state/
- Add enforcement to AUTHOR'S_NOTES

**Benefits**:
- More consistent NPC behavior
- Prevents knowledge leaks
- Better interaction pacing

---

## FILE STRUCTURE

### Current Organization

```
RP Claude Code/
│
├── .claude/
│   ├── commands/
│   │   ├── continue.md
│   │   ├── endSession.md
│   │   ├── arc.md
│   │   ├── gencard.md
│   │   ├── note.md
│   │   ├── memory.md
│   │   └── COMMANDS_README.md
│   └── hooks/
│       ├── user-prompt-submit.sh
│       └── HOOKS_README.md
│
├── guidelines/
│   ├── Session_End_Protocol.md
│   └── Timing.txt
│
├── templates/
│   ├── TEMPLATE_ENTITY_CHARACTER.md
│   ├── TEMPLATE_ENTITY_LOCATION.md
│   ├── TEMPLATE_ENTITY_ITEM.md
│   ├── TEMPLATE_ENTITY_EVENT.md
│   ├── TEMPLATE_AUTHORS_NOTES.md (for new RPs)
│   ├── TEMPLATE_ROLEPLAY_OVERVIEW.md
│   ├── TEMPLATE_SCENE_NOTES.md
│   ├── TEMPLATE_STORY_GENOME.md
│   ├── TEMPLATE_automation_config.json
│   └── AUTOMATION_CONFIG_README.md
│
├── scripts/
│   ├── deepseek_call.sh
│   └── README.md
│
├── Example RP/
│   ├── Example RP.md
│   ├── AUTHOR'S_NOTES.md
│   ├── STORY_GENOME.md
│   ├── SCENE_NOTES.md
│   ├── characters/
│   │   ├── {{user}}.md
│   │   └── Alex.md
│   ├── entities/
│   │   └── [CHAR] Sarah Mitchell.md
│   ├── chapters/
│   │   └── Chapter 2.txt
│   ├── sessions/
│   └── state/
│       ├── current_state.md
│       ├── story_arc.md
│       ├── entity_tracker.json
│       ├── response_counter.txt
│       └── automation_config.json
│
├── CLAUDE.md (main instructions)
├── RP_FOLDER_STRUCTURE.md (folder guide)
├── WEBAPP_VS_CLAUDECODE_ANALYSIS.md (comparison)
├── PROJECT_STATUS_AND_ROADMAP.md (this file)
│
└── [Guide files to be moved to guidelines/]:
    ├── NPC_Interaction_Rules.md
    ├── POV_and_Writing_Checklist.md
    ├── Writing_Style_Guide.md
    ├── Time_Tracking_Guide.md
    └── Story Guidelines.md
```

---

## QUICK START GUIDE

### For User (Continuing This Project)

#### If Starting New Session:

1. **Read this file first**: `PROJECT_STATUS_AND_ROADMAP.md`
2. **Review current status**: See "What's Working Now" section
3. **Check planned work**: See "Planned Improvements" section
4. **Ask Claude**: "I'm continuing the RP system project. I've read the status document. Should we start with Phase 1 (organizing guides)?"

#### Next Steps (In Order):

**Phase 1** (Quick Win):
```
"Let's start Phase 1: Move the guide files to guidelines/ and update CLAUDE.md"
```

**Phase 2** (Cost Optimization):
```
"Let's implement the tiered document reference system"
```

**Phase 3** (Story Continuity):
```
"Let's create the chapter trigger system"
```

---

### For Using the System (Actual RP)

#### Starting a New RP:

1. **Copy Example RP folder** as template
2. **Rename to your RP name**
3. **Edit core files**:
   - `[Your RP].md` - Overview
   - `AUTHOR'S_NOTES.md` - Story rules
   - `STORY_GENOME.md` - Intended plot
   - `SCENE_NOTES.md` - Current session guidance

4. **Create character sheets** in `characters/`
5. **Configure automation** in `state/automation_config.json`
6. **Start session**: Use `/continue` command

#### During RP:

- **Just roleplay normally** - automation handles entity cards and arcs
- Use `/note` for quick reminders
- Use `/gencard` manually for specific entity types (location/item/event)
- Use `/arc` manually after major events

#### Ending Session:

- Use `/endSession` - handles everything automatically
- Creates summary, updates memory, updates character sheets
- Costs ~$0.02-0.05 per session

---

## KEY FILES TO REFERENCE

### For Development:

- **This file**: Overall project status
- **WEBAPP_VS_CLAUDECODE_ANALYSIS.md**: Feature comparison and recommendations
- **RP_FOLDER_STRUCTURE.md**: Complete folder organization guide
- **COMMANDS_README.md**: All commands documented
- **HOOKS_README.md**: Hook system explained

### For Using System:

- **CLAUDE.md**: Main instructions (Claude reads this)
- **Example RP/**: Working example of complete setup
- **templates/**: Copy these to start new RPs
- **AUTOMATION_CONFIG_README.md**: Configuration options

### For Writing Quality:

- **NPC_Interaction_Rules.md**: Response pacing, background NPCs
- **POV_and_Writing_Checklist.md**: POV enforcement, red flags
- **Writing_Style_Guide.md**: Scene-specific templates, prose quality
- **Time_Tracking_Guide.md**: Activity durations, modifiers

---

## TECHNICAL NOTES

### API Configuration

**OpenRouter (DeepSeek)**:
- API Key: `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`
- Model: `deepseek/deepseek-chat-v3.1`
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Cost: ~$0.14 per million tokens (very cheap)

**Script Location**: `scripts/deepseek_call.sh`

### Hook Location

**File**: `.claude/hooks/user-prompt-submit.sh`

**Functions**:
- `load_config()` - Loads automation settings
- `increment_counter()` - Tracks responses, triggers arc
- `calculate_time()` - Suggests elapsed time
- `track_entities()` - Tracks mentions, triggers card generation
- `identify_triggers()` - Loads triggered files
- `auto_generate_entity_card()` - Creates cards with DeepSeek
- `auto_generate_arc()` - Triggers arc generation

**Execution**: Runs before every user message (automatic)

### Configuration

**File**: `state/automation_config.json`

**Options**:
```json
{
  "auto_entity_cards": true,          // Enable/disable
  "entity_mention_threshold": 2,      // Mentions to trigger
  "auto_story_arc": true,             // Enable/disable
  "arc_frequency": 50                 // Responses between arcs
}
```

**Changes**: Apply immediately (no restart needed)

---

## SUMMARY

### ✅ What's Complete

1. **Core System**: Folder structure, templates, documentation
2. **Automation**: Entity cards + story arcs auto-generate
3. **Commands**: 7 slash commands for management
4. **Cost Optimization**: DeepSeek integration working
5. **Example**: Fully populated Example RP
6. **Testing**: Verified with OpenRouter API

### 🔄 What's Next

1. **Phase 1**: Move guide files to guidelines/ (30 min)
2. **Phase 2**: Implement tiered document loading (2-3 hours)
3. **Phase 3**: Create chapter trigger system (3-4 hours)
4. **Phase 4+**: Optional enhancements (NPC systems, POV enforcement)

### 💰 Current Costs

- **Automation**: ~$0.003-0.005 per session
- **Session end**: ~$0.02-0.05
- **Total**: ~$0.025-0.055 per complete session
- **Very affordable!**

### 🎯 Immediate Next Step

**Recommend starting Phase 1**: Move guide files to guidelines/ and update CLAUDE.md

This gives immediate access to all the writing quality systems from the webapp without any complex implementation.

---

## QUESTIONS TO ASK WHEN CONTINUING

1. "What phase should we work on next?"
2. "Should we start with the quick win (Phase 1)?"
3. "Do you want to test the current system first?"
4. "Any changes to the automation config you'd like?"
5. "Should we review the webapp analysis together?"

---

**End of Status Document**

*This document provides complete project context for continuing work in a new session. All key information about what's been built, what works, costs, and next steps is included.*
