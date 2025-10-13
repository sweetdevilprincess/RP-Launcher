# Automation Config - automation_config.json

This file controls automatic entity cards, story arcs, and memory updates during your RP sessions.

---

## Configuration Options

```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50,
  "auto_memory_update": true,
  "memory_frequency": 15
}
```

### `auto_entity_cards` (true/false)
**Default**: `true`

**What it does**: Automatically generates entity cards when entities are mentioned multiple times.

**How it works**:
- Hook tracks entity mentions in user messages
- When entity reaches threshold (see below), automatically calls DeepSeek
- Searches recent chapters for context
- Generates entity card and saves to `entities/[CHAR] Name.md`
- Marks entity as "card_created" in tracker

**Cost**: ~$0.001 per entity card (DeepSeek)

**Set to false if**: You want to manually create all entity cards using `/gencard`

---

### `entity_mention_threshold` (number)
**Default**: `2`

**What it does**: Sets how many mentions trigger automatic card generation.

**Recommended values**:
- `2`: Generate quickly (more cards, slightly higher cost)
- `3`: Generate for recurring entities only
- `5`: Generate only for frequently mentioned entities

**Example**:
- Threshold = 2
- User mentions "Marcus" once → Tracked, no card yet
- User mentions "Marcus" again → ✅ Auto-generates card

**Cost impact**:
- Lower threshold = More cards = Higher cost (but still cheap)
- Higher threshold = Fewer cards = Lower cost

---

### `auto_story_arc` (true/false)
**Default**: `true`

**What it does**: Automatically generates story arc updates at regular intervals.

**How it works**:
- Every X responses (see arc_frequency), hook triggers arc generation
- Claude reads Story Genome, recent chapters, current state
- Generates 11-beat future arc + full summary
- Saves to `state/story_arc.md`

**Cost**: **FREE** (uses Claude's main context during response generation)

**Set to false if**: You want to manually trigger arcs using `/arc` command

---

### `arc_frequency` (number)
**Default**: `50`

**What it does**: Sets how often (in responses) to auto-generate story arcs.

**Recommended values**:
- `25`: Frequent updates (good for fast-paced RPs)
- `50`: Standard (good balance)
- `100`: Infrequent (for slow-burn or long RPs)

**Example**:
- Frequency = 50
- At response 50, 100, 150, etc. → Auto-generates arc

**Note**: Even with auto-generation, you can manually trigger `/arc` anytime.

---

### `auto_memory_update` (true/false)
**Default**: `true`

**What it does**: Automatically updates {{user}}'s memory file at regular intervals.

**How it works**:
- Every X responses (see memory_frequency), hook triggers memory update
- Claude reviews recent RP exchanges (last 5-8)
- Calls DeepSeek to update `state/user_memory.md`
- Moves "Immediate Memory" to "Recent Memory"
- Adds new events to "Immediate Memory"
- Maintains character perspective

**Cost**: ~$0.001-0.002 per update (DeepSeek)

**Set to false if**:
- You don't use memory tracking
- You want to manually update via `/memory` command
- Memory file doesn't exist

**Note**: Memory file must exist (`state/user_memory.md`) for this to work. Use template from `templates/TEMPLATE_user_memory.md` to create one.

---

### `memory_frequency` (number)
**Default**: `15`

**What it does**: Sets how often (in responses) to auto-update memory.

**Recommended values**:
- `10`: Frequent updates (captures everything, higher cost)
- `15`: Standard (good balance)
- `20`: Less frequent (lower cost, may miss minor events)
- `30`: Infrequent (minimal cost, captures only major events)

**Example**:
- Frequency = 15
- At response 15, 30, 45, etc. → Auto-updates memory

**Cost impact**:
- Lower frequency = More updates = Higher cost
- Higher frequency = Fewer updates = Lower cost

**Note**: Even with auto-updates, `/endSession` performs a final comprehensive memory consolidation.

---

## How to Use

### Initial Setup (New RP)
1. Copy `TEMPLATE_automation_config.json` to your RP's `state/` folder
2. Rename to `automation_config.json`
3. Adjust settings if desired (defaults work well for most RPs)

### Adjusting Settings Mid-RP
1. Edit `state/automation_config.json` in your RP folder
2. Change values as needed
3. Save - settings apply immediately (next response)

### Disabling All Automation
Set all to false:
```json
{
  "auto_entity_cards": false,
  "entity_mention_threshold": 2,
  "auto_story_arc": false,
  "arc_frequency": 50,
  "auto_memory_update": false,
  "memory_frequency": 15
}
```

You can still use `/gencard`, `/arc`, and `/memory` commands manually.

---

## Cost Summary (OPTIMIZED PROMPTS)

**All DeepSeek prompts have been optimized to use 30-50% fewer tokens!**

**Typical RP session (30 responses, 3 new entities)**:
- Entity cards: 3 × $0.0006 = $0.0018 (40% savings)
- Story arc: (not reached) = $0.00
- Memory updates: 2 × $0.0006 = $0.0012 (35% savings)
- **Total**: ~$0.003

**At 50 responses (5 new entities)**:
- Entity cards: 5 × $0.0006 = $0.003 (40% savings)
- Story arc: 1 × FREE = $0.00
- Memory updates: 3 × $0.0006 = $0.0018 (35% savings)
- **Total**: ~$0.005

**Plus /endSession (chapter summary, character updates, final memory)**:
- Chapter summary: ~$0.0015-0.0025 (50% savings)
- Character updates: ~$0.0024-0.0048 (40% savings)
- Final memory consolidation: ~$0.0006-0.0012 (35% savings)
- **Session End Total**: ~$0.0045-0.0085

**Complete 50-response session with endSession**: ~$0.009-0.014

**~44% cost reduction vs. unoptimized prompts!**
**Still incredibly affordable for full automation!**

---

## Troubleshooting

### Entity cards not generating?
- Check if `jq` is installed (required for JSON manipulation)
- Check hook output in console for errors
- Verify `python -m work_in_progress.clients.deepseek` exists and is executable

### Story arc not generating?
- Check if you've reached the frequency threshold (default 50)
- Verify `STORY_GENOME.md` exists (arc compares to Genome)
- Check hook output for trigger message

### Want to regenerate a card?
1. Delete the card file from `entities/`
2. Edit `state/entity_tracker.json`, set `card_created` to `false` for that entity
3. Wait for next mention or use `/gencard` manually

### Want to force arc generation?
Use `/arc` command manually - works regardless of automation settings

---

## Default Behavior (No Config File)

If `automation_config.json` doesn't exist:
- Entity cards: **ENABLED** (threshold: 2)
- Story arcs: **ENABLED** (frequency: 50)

Automation works out of the box with sensible defaults!

---

## Best Practices

### For Most RPs:
Use defaults - they work well for typical roleplay pace.

### For Fast-Paced RPs:
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 3,
  "auto_story_arc": true,
  "arc_frequency": 25
}
```

### For Slow-Burn RPs:
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 100
}
```

### For Budget-Conscious:
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 5,
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

### For Manual Control:
```json
{
  "auto_entity_cards": false,
  "entity_mention_threshold": 2,
  "auto_story_arc": false,
  "arc_frequency": 50
}
```

---

**Remember**: You can always change these settings mid-RP. They take effect on the next response!

