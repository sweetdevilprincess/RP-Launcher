#!/bin/bash

# Time Tracking & Reference Management Hook
# Runs before each user message is processed by Claude
# Purpose: Calculate time, track entities, manage conditional references

# Get the user's message from stdin or command line
USER_MESSAGE="${1:-$(cat)}"

# Get current working directory (should be RP folder)
RP_DIR="${CLAUDE_WORKING_DIR:-$(pwd)}"

# Path to state files
STATE_DIR="$RP_DIR/state"
CURRENT_STATE="$STATE_DIR/current_state.md"
RESPONSE_COUNTER="$STATE_DIR/response_counter.txt"
ENTITY_TRACKER="$STATE_DIR/entity_tracker.json"
STATUS_FILE="$RP_DIR/CURRENT_STATUS.md"
HOOK_LOG="$STATE_DIR/hook.log"

# Path to shared files
TIMING_FILE="$RP_DIR/../guidelines/Timing.txt"

# Verbose mode (set to false for cleaner output)
VERBOSE=false

# ====================
# FUNCTION: Log to File
# ====================
log_to_file() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$HOOK_LOG"
}

# ====================
# FUNCTION: Update Status File
# ====================
update_status_file() {
    # Get current data
    local response_count=0
    if [ -f "$RESPONSE_COUNTER" ]; then
        response_count=$(cat "$RESPONSE_COUNTER")
    fi

    # Get timestamp and location from current_state.md
    local timestamp="Unknown"
    local location="Unknown"
    if [ -f "$CURRENT_STATE" ]; then
        timestamp=$(grep -m 1 "Timestamp" "$CURRENT_STATE" | sed 's/.*: //' || echo "Unknown")
        location=$(grep -m 1 "Location" "$CURRENT_STATE" | sed 's/.*: //' || echo "Unknown")
    fi

    # Count tracked entities
    local entity_count=0
    if [ -f "$ENTITY_TRACKER" ] && command -v jq &> /dev/null; then
        entity_count=$(jq '.entities | length' "$ENTITY_TRACKER" 2>/dev/null || echo 0)
    fi

    # Get loaded entities from last run (track in temp variable)
    local loaded_entities="${LOADED_ENTITIES:-None}"

    # Calculate arc progress
    local arc_progress=$((response_count % ARC_FREQUENCY))
    local arc_next=$((ARC_FREQUENCY - arc_progress))

    # Write status file
    cat > "$STATUS_FILE" <<EOF
# Current RP Status

**Last Updated**: $(date '+%Y-%m-%d %H:%M:%S')

---

## 📍 Current State

- **Timestamp**: $timestamp
- **Location**: $location
- **Chapter**: [Check current_state.md]
- **Response Count**: $response_count

---

## 📊 Progress

**Story Arc**: $arc_progress / $ARC_FREQUENCY responses
- Next arc generation in: **$arc_next responses**
- Progress: $(printf '█%.0s' $(seq 1 $((arc_progress * 10 / ARC_FREQUENCY))))$(printf '░%.0s' $(seq 1 $((10 - arc_progress * 10 / ARC_FREQUENCY))))

---

## 🎭 Entities

**Tracked**: $entity_count entities in entity_tracker.json
**Loaded This Response**: $loaded_entities

---

## ⚙️ Automation

**Entity Cards**: $([ "$AUTO_ENTITY_CARDS" = "true" ] && echo "✅ ON" || echo "❌ OFF") (Threshold: $ENTITY_THRESHOLD mentions)
**Story Arcs**: $([ "$AUTO_STORY_ARC" = "true" ] && echo "✅ ON" || echo "❌ OFF") (Every $ARC_FREQUENCY responses)
**Memory Updates**: $([ "$AUTO_MEMORY_UPDATE" = "true" ] && echo "✅ ON" || echo "❌ OFF") (Every $MEMORY_FREQUENCY responses)

---

## 📝 Quick Commands

- \`/status\` - Detailed status report
- \`/continue\` - Load session context
- \`/endSession\` - End session protocol
- \`/arc\` - Generate story arc
- \`/gencard [type], [name]\` - Create entity card
- \`/note [text]\` - Add quick note
- \`/memory\` - Update memory

---

*Keep this file open in a second pane for live status updates*
EOF
}

# ====================
# FUNCTION: Load Automation Config
# ====================
load_config() {
    CONFIG_FILE="$STATE_DIR/automation_config.json"

    # Default values
    AUTO_ENTITY_CARDS=true
    ENTITY_THRESHOLD=2
    AUTO_STORY_ARC=true
    ARC_FREQUENCY=50
    AUTO_MEMORY_UPDATE=true
    MEMORY_FREQUENCY=15

    # Load from config if exists
    if [ -f "$CONFIG_FILE" ] && command -v jq &> /dev/null; then
        AUTO_ENTITY_CARDS=$(jq -r '.auto_entity_cards // true' "$CONFIG_FILE")
        ENTITY_THRESHOLD=$(jq -r '.entity_mention_threshold // 2' "$CONFIG_FILE")
        AUTO_STORY_ARC=$(jq -r '.auto_story_arc // true' "$CONFIG_FILE")
        ARC_FREQUENCY=$(jq -r '.arc_frequency // 50' "$CONFIG_FILE")
        AUTO_MEMORY_UPDATE=$(jq -r '.auto_memory_update // true' "$CONFIG_FILE")
        MEMORY_FREQUENCY=$(jq -r '.memory_frequency // 15' "$CONFIG_FILE")
    fi
}

# ====================
# FUNCTION: Increment Response Counter
# ====================
increment_counter() {
    if [ -f "$RESPONSE_COUNTER" ]; then
        COUNT=$(cat "$RESPONSE_COUNTER")
        NEW_COUNT=$((COUNT + 1))
        echo "$NEW_COUNT" > "$RESPONSE_COUNTER"

        # Check if we've hit arc generation threshold (every 50 responses)
        if [ $((NEW_COUNT % ARC_FREQUENCY)) -eq 0 ] && [ "$AUTO_STORY_ARC" = "true" ]; then
            log_to_file "Auto-generating story arc at response $NEW_COUNT"
            [ "$VERBOSE" = "true" ] && echo "<!-- AUTO-GENERATING STORY ARC (Response $NEW_COUNT) -->" >&2
            auto_generate_arc "$NEW_COUNT"
        fi

        # Check if we've hit memory update threshold (every 15 responses)
        if [ $((NEW_COUNT % MEMORY_FREQUENCY)) -eq 0 ] && [ "$AUTO_MEMORY_UPDATE" = "true" ]; then
            log_to_file "Auto-updating memory at response $NEW_COUNT"
            [ "$VERBOSE" = "true" ] && echo "<!-- AUTO-UPDATING MEMORY (Response $NEW_COUNT) -->" >&2
            auto_update_memory "$NEW_COUNT"
        fi
    fi
}

# ====================
# FUNCTION: Calculate Time from Activities
# ====================
calculate_time() {
    local message="$1"

    # Check if Timing.txt exists
    if [ ! -f "$TIMING_FILE" ]; then
        log_to_file "WARNING: Timing.txt not found at $TIMING_FILE"
        [ "$VERBOSE" = "true" ] && echo "<!-- WARNING: Timing.txt not found at $TIMING_FILE -->" >&2
        return
    fi

    # Extract activity keywords from user message (simple matching)
    # This looks for common activity words in the message

    local total_minutes=0
    local activities_found=""

    # Read Timing.txt and search for matches in user message
    while IFS=':' read -r activity minutes; do
        # Remove whitespace
        activity=$(echo "$activity" | xargs)
        minutes=$(echo "$minutes" | xargs)

        # Skip empty lines or comments
        [ -z "$activity" ] && continue
        [[ "$activity" =~ ^# ]] && continue

        # Check if activity word appears in message (case-insensitive)
        if echo "$message" | grep -qi "\b$activity\b"; then
            total_minutes=$((total_minutes + minutes))
            if [ -z "$activities_found" ]; then
                activities_found="$activity ($minutes min)"
            else
                activities_found="$activities_found, $activity ($minutes min)"
            fi
        fi
    done < "$TIMING_FILE"

    # If activities found, output suggestion
    if [ $total_minutes -gt 0 ]; then
        log_to_file "Time tracking: $activities_found = $total_minutes minutes"

        # Update current_state.md with suggestion
        if [ -f "$CURRENT_STATE" ]; then
            # Add suggestion to current state (Claude will see this)
            echo "" >> "$CURRENT_STATE"
            echo "## Time Calculation Suggestion (Latest)" >> "$CURRENT_STATE"
            echo "**Activities detected**: $activities_found" >> "$CURRENT_STATE"
            echo "**Suggested time elapsed**: $total_minutes minutes" >> "$CURRENT_STATE"
            echo "**Note**: Review and adjust for modifiers (fast/slow) or unknown activities" >> "$CURRENT_STATE"
        fi

        TIME_SUGGESTION="⏱️ $total_minutes min"
    else
        log_to_file "No standard activities detected"
        TIME_SUGGESTION=""
    fi
}

# ====================
# FUNCTION: Track Entity Mentions
# ====================
track_entities() {
    local message="$1"

    # Check if entity_tracker.json exists
    if [ ! -f "$ENTITY_TRACKER" ]; then
        echo '{"entities": {}}' > "$ENTITY_TRACKER"
    fi

    # Extract potential entity names (capitalized words)
    potential_entities=$(echo "$message" | grep -oE '\b[A-Z][a-z]+\b' | sort -u)

    # Get current chapter from response counter (approximate)
    local current_chapter=1
    if [ -f "$RESPONSE_COUNTER" ]; then
        local responses=$(cat "$RESPONSE_COUNTER")
        current_chapter=$(( (responses / 10) + 1 ))  # Rough estimate: 10 responses per chapter
    fi

    # For each potential entity, increment mention count
    for entity in $potential_entities; do
        # Skip common words that aren't entities
        case "$entity" in
            The|A|An|I|You|He|She|It|They|We|Is|Was|Are|Were|Be|Been|Have|Has|Had|Do|Does|Did|Will|Would|Could|Should|May|Might|Must|Can) continue ;;
        esac

        log_to_file "Entity mentioned: $entity"

        # Update JSON using jq if available, otherwise manual
        if command -v jq &> /dev/null; then
            # Get current mentions
            local mentions=$(jq -r ".entities.\"$entity\".mentions // 0" "$ENTITY_TRACKER")
            local first_chapter=$(jq -r ".entities.\"$entity\".first_chapter // $current_chapter" "$ENTITY_TRACKER")
            local card_created=$(jq -r ".entities.\"$entity\".card_created // false" "$ENTITY_TRACKER")

            # Increment mentions
            mentions=$((mentions + 1))

            # Update JSON
            jq ".entities.\"$entity\" = {\"mentions\": $mentions, \"first_chapter\": $first_chapter, \"last_chapter\": $current_chapter, \"card_created\": $card_created}" "$ENTITY_TRACKER" > "$ENTITY_TRACKER.tmp"
            mv "$ENTITY_TRACKER.tmp" "$ENTITY_TRACKER"

            log_to_file "Entity '$entity': $mentions mentions"

            # Check if we should auto-generate card
            if [ "$AUTO_ENTITY_CARDS" = "true" ] && [ "$card_created" = "false" ] && [ $mentions -ge $ENTITY_THRESHOLD ]; then
                log_to_file "TRIGGERING AUTO-GENERATION: $entity reached $ENTITY_THRESHOLD mentions"
                auto_generate_entity_card "$entity" "$mentions" "$first_chapter"
            fi
        fi
    done
}

# ====================
# FUNCTION: Identify Conditional File Triggers
# ====================
identify_triggers() {
    local message="$1"
    local chars_dir="$RP_DIR/characters"
    local entities_dir="$RP_DIR/entities"

    local files_to_inject=""
    LOADED_ENTITIES=""  # Track for status badge

    # Search for character triggers
    if [ -d "$chars_dir" ]; then
        for char_file in "$chars_dir"/*.md; do
            [ -f "$char_file" ] || continue

            # Extract triggers - Support both formats:
            # Format 1: **Triggers**: word1, word2, word3
            # Format 2 (AI Dungeon): [Triggers:word1,word2,word3']

            # Try Format 1 first
            triggers=$(grep -i "^\*\*Triggers\*\*:" "$char_file" | sed 's/^\*\*Triggers\*\*://I')

            # If not found, try Format 2
            if [ -z "$triggers" ]; then
                triggers=$(grep -i "^\[Triggers:" "$char_file" | sed 's/^\[Triggers://I' | sed 's/\]$//')
            fi

            # Skip if no triggers found
            [ -z "$triggers" ] && continue

            # Split by comma and check each trigger
            IFS=',' read -ra trigger_array <<< "$triggers"
            for trigger in "${trigger_array[@]}"; do
                # Trim whitespace (but preserve internal punctuation like apostrophes)
                trigger=$(echo "$trigger" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                [ -z "$trigger" ] && continue

                # Exact match including punctuation (AI Dungeon style)
                if echo "$message" | grep -qF "$trigger"; then
                    files_to_inject="$files_to_inject
Read: $char_file"
                    local entity_name=$(basename "$char_file" .md)
                    entity_name=$(echo "$entity_name" | sed 's/^\[CHAR\] //')
                    if [ -z "$LOADED_ENTITIES" ]; then
                        LOADED_ENTITIES="$entity_name"
                    else
                        LOADED_ENTITIES="$LOADED_ENTITIES, $entity_name"
                    fi
                    log_to_file "Trigger match: Loading $char_file (matched: $trigger)"
                    [ "$VERBOSE" = "true" ] && echo "<!-- TRIGGER MATCH: Loading $char_file (matched: $trigger) -->" >&2
                    break  # Only inject once per file
                fi
            done
        done
    fi

    # Search for entity triggers
    if [ -d "$entities_dir" ]; then
        for entity_file in "$entities_dir"/*.md; do
            [ -f "$entity_file" ] || continue

            # Extract triggers - Support both formats:
            # Format 1: **Triggers**: word1, word2, word3
            # Format 2 (AI Dungeon): [Triggers:word1,word2,word3']

            # Try Format 1 first
            triggers=$(grep -i "^\*\*Triggers\*\*:" "$entity_file" | sed 's/^\*\*Triggers\*\*://I')

            # If not found, try Format 2
            if [ -z "$triggers" ]; then
                triggers=$(grep -i "^\[Triggers:" "$entity_file" | sed 's/^\[Triggers://I' | sed 's/\]$//')
            fi

            # Skip if no triggers found
            [ -z "$triggers" ] && continue

            # Split by comma and check each trigger
            IFS=',' read -ra trigger_array <<< "$triggers"
            for trigger in "${trigger_array[@]}"; do
                # Trim whitespace (but preserve internal punctuation like apostrophes)
                trigger=$(echo "$trigger" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                [ -z "$trigger" ] && continue

                # Exact match including punctuation (AI Dungeon style)
                if echo "$message" | grep -qF "$trigger"; then
                    files_to_inject="$files_to_inject
Read: $entity_file"
                    local entity_name=$(basename "$entity_file" .md)
                    entity_name=$(echo "$entity_name" | sed 's/^\[[A-Z]*\] //')
                    if [ -z "$LOADED_ENTITIES" ]; then
                        LOADED_ENTITIES="$entity_name"
                    else
                        LOADED_ENTITIES="$LOADED_ENTITIES, $entity_name"
                    fi
                    log_to_file "Trigger match: Loading $entity_file (matched: $trigger)"
                    [ "$VERBOSE" = "true" ] && echo "<!-- TRIGGER MATCH: Loading $entity_file (matched: $trigger) -->" >&2
                    break  # Only inject once per file
                fi
            done
        done
    fi

    # Output files to inject (Claude will see these)
    if [ -n "$files_to_inject" ]; then
        log_to_file "Conditional files loaded: $(echo "$files_to_inject" | grep -c 'Read:')"
        [ "$VERBOSE" = "true" ] && echo "<!-- CONDITIONAL FILES TO REFERENCE: -->" >&2
        echo "$files_to_inject" >&2
    fi

    # If no entities loaded, set to "None"
    [ -z "$LOADED_ENTITIES" ] && LOADED_ENTITIES="None"
}

# ====================
# FUNCTION: Auto-Generate Entity Card
# ====================
auto_generate_entity_card() {
    local entity_name="$1"
    local mentions="$2"
    local first_chapter="$3"

    log_to_file "[AUTO-GEN] Generating entity card for: $entity_name"

    # Path to deepseek script
    local deepseek_script="$RP_DIR/../scripts/deepseek_call.sh"

    if [ ! -f "$deepseek_script" ]; then
        log_to_file "[ERROR] DeepSeek script not found at $deepseek_script"
        [ "$VERBOSE" = "true" ] && echo "<!-- [ERROR] DeepSeek script not found at $deepseek_script -->" >&2
        return
    fi

    # Search recent chapters for context about this entity
    local context=""
    if [ -d "$RP_DIR/chapters" ]; then
        # Get last 2-3 chapter files
        local chapter_files=$(ls -t "$RP_DIR/chapters"/*.txt 2>/dev/null | head -3)
        for chapter in $chapter_files; do
            # Search for entity mentions in chapter
            local mentions_in_chapter=$(grep -i "$entity_name" "$chapter" 2>/dev/null || true)
            if [ -n "$mentions_in_chapter" ]; then
                context="$context\n\nFrom $(basename \"$chapter\"):\n$mentions_in_chapter"
            fi
        done
    fi

    # If no context found, use generic
    if [ -z "$context" ]; then
        context="Entity '$entity_name' has been mentioned $mentions times starting from chapter $first_chapter. Generate a card based on typical story context."
    fi

    # Build optimized prompt (compact format)
    # Extract key info from context instead of sending full text
    local context_summary=$(echo "$context" | head -c 200 | tr '\n' ' ' | sed 's/  */ /g')

    local prompt="{
  \"entity\": \"$entity_name\",
  \"type\": \"character\",
  \"mentions\": $mentions,
  \"first_chapter\": $first_chapter,
  \"context_brief\": \"$context_summary\"
}

Task: Generate entity card in markdown format.

Structure:
# [CHAR] $entity_name

[Triggers:$entity_name']
**Type**: Character
**First Mentioned**: Chapter $first_chapter
**Mention Count**: $mentions

## Description
[Deduce from context_brief - expand with typical character details]

## Role in Story
[Infer function from limited context]

## Significance
[Deduce why entity matters]

## Appearances
### Chapter $first_chapter
- [Expand from context_brief]

## Notes
[Additional inferred information]

---
**Last Updated**: $(date +"%B %d, %Y")

Output ONLY the completed entity card in markdown format."

    # Call DeepSeek
    local card_content=$("$deepseek_script" "$prompt" 2>/dev/null)

    if [ -n "$card_content" ]; then
        # Save card
        local entities_dir="$RP_DIR/entities"
        mkdir -p "$entities_dir"

        local card_file="$entities_dir/[CHAR] $entity_name.md"
        echo "$card_content" > "$card_file"

        # Mark as created in tracker
        if command -v jq &> /dev/null; then
            jq ".entities.\"$entity_name\".card_created = true" "$ENTITY_TRACKER" > "$ENTITY_TRACKER.tmp"
            mv "$ENTITY_TRACKER.tmp" "$ENTITY_TRACKER"
        fi

        log_to_file "[SUCCESS] Auto-generated entity card: entities/[CHAR] $entity_name.md"
        CARD_GENERATED="✨ $entity_name"
    else
        log_to_file "[ERROR] Failed to generate card for $entity_name"
        [ "$VERBOSE" = "true" ] && echo "<!-- [ERROR] Failed to generate card for $entity_name -->" >&2
    fi
}

# ====================
# FUNCTION: Auto-Generate Story Arc
# ====================
auto_generate_arc() {
    local response_count="$1"

    log_to_file "[AUTO-GEN] Generating story arc update at response $response_count"

    # This injects instructions for Claude to generate the arc
    # Claude will see this and execute during normal response generation

    cat >&2 <<'EOF'
<!-- ========================================
AUTOMATIC STORY ARC GENERATION TRIGGERED
======================================== -->

Read: STORY_GENOME.md (intended plot beats)
Read: Last 2-3 chapter summaries from chapters/ folder
Read: state/current_state.md (current position)
Read: state/story_arc.md (existing arc if present)

GENERATE UPDATED STORY ARC:

## Step 1: Compare to Genome
- Are we on track with STORY_GENOME.md?
- Any divergences? Note them.

## Step 2: Generate 11-Beat Future Arc (AI Dungeon Format)
Write numbered list of 11 major future events:
- Each event UNDER 7 words
- Chronological order
- Build on each other
- Turning points, conflicts, discoveries
- No clichés, dialogue, or prose
- Don't write "protagonist" or "main character"

## Step 3: Create Full Arc Summary

### Current Story Arc

**Arc Title**: [Name]
**Current Phase**: [Beginning/Rising/Climax/Falling/Resolution]

**Where We Are in Genome**:
- Genome Beat: [Which beat from STORY_GENOME.md]
- Status: [On track / Diverged / Modified]
- Notes: [Explanation]

**Future Story Arc (Next 11 Major Beats)**:
1. [Event <7 words]
2. [Event <7 words]
[...continue through 11]

**Key Recent Events**:
- [Recent event 1]
- [Recent event 2]

**Active Plot Threads**:
- [Thread 1]: Status
- [Thread 2]: Status

**Character Developments**:
- [Character]: Recent development

**Relationship Dynamics**:
- [A & B]: Current dynamic

**Themes**:
- [Theme]: How manifesting

**Next Direction**:
[Where story seems headed next - 1-2 paragraphs]

## Step 4: Save Arc
Save the complete arc summary to: state/story_arc.md

After saving, notify:
"✅ Story arc auto-updated at response $response_count"

<!-- ======================================== -->
EOF
}

# ====================
# FUNCTION: Auto Update Memory
# ====================
auto_update_memory() {
    local response_count="$1"

    log_to_file "[AUTO-MEM] Triggering memory update at response $response_count"

    # Check if memory file exists
    local memory_file="$STATE_DIR/user_memory.md"
    if [ ! -f "$memory_file" ]; then
        log_to_file "[AUTO-MEM] No memory file found, skipping"
        return
    fi

    # Inject instructions for Claude to update memory using DeepSeek (OPTIMIZED)
    cat >&2 <<'EOF'
<!-- ========================================
AUTOMATIC MEMORY UPDATE TRIGGERED (OPTIMIZED)
======================================== -->

**Task**: Update {{user}}'s memory using compact event extraction

## Instructions:

1. **Extract Recent Events**: Look back at last 5-8 RP exchanges and extract to compact JSON:
   ```json
   [
     {"ts": "timestamp", "event": "brief event summary", "sig": "high/medium/low", "emotion": "emotion"},
     {"ts": "timestamp", "event": "brief event summary", "sig": "high/medium/low", "emotion": "emotion"}
   ]
   ```

2. **Read Current Memory**: Read state/user_memory.md and summarize current structure:
   - Immediate: [list]
   - Recent: [list]
   - Significant: [list]

3. **Call DeepSeek** with OPTIMIZED prompt using `python -m work_in_progress.clients.deepseek`:

```
Consolidate memory for {{user}} using structured event data.

**Current Memory** (brief):
Immediate: [list current immediate memories]
Recent: [list current recent memories]
Significant: [list current significant memories]

**New Events** (JSON):
[paste JSON array from step 1]

**Task**:
1. Expand new events into "Immediate Memory" (2-3 sentences each, vivid detail)
2. Move old immediate → "Recent Memory" (compress to 1 sentence each)
3. Promote high-sig events to "Significant Memories" if warranted
4. Maintain character perspective

Output complete updated state/user_memory.md in markdown format.
```

4. **Save Result**: Write DeepSeek output to state/user_memory.md

5. **Notify**: Output "✅ Memory auto-updated at response [count]"

<!-- ======================================== -->
EOF
}

# ====================
# MAIN EXECUTION
# ====================

# Only run if we're in an RP directory (has state folder)
if [ ! -d "$STATE_DIR" ]; then
    log_to_file "Not in RP directory (no state/ folder found)"
    [ "$VERBOSE" = "true" ] && echo "<!-- Not in RP directory (no state/ folder found) -->" >&2
    exit 0
fi

# Initialize tracking variables
TIME_SUGGESTION=""
LOADED_ENTITIES="None"
CARD_GENERATED=""

log_to_file "========== RP Automation Hook Starting =========="

# 0. Load automation configuration
load_config

# 1. Increment response counter
increment_counter

# 2. Calculate time from activities
calculate_time "$USER_MESSAGE"

# 3. Track entity mentions
track_entities "$USER_MESSAGE"

# 4. Identify conditional file triggers
identify_triggers "$USER_MESSAGE"

# 5. Update status file
update_status_file

# 6. Display consolidated status badge (quiet mode)
if [ "$VERBOSE" = "false" ]; then
    # Build status badge with only important info
    local status_parts=""

    # Add time suggestion if present
    [ -n "$TIME_SUGGESTION" ] && status_parts="$status_parts $TIME_SUGGESTION"

    # Add card generation if occurred
    [ -n "$CARD_GENERATED" ] && status_parts="$status_parts $CARD_GENERATED"

    # Display badge if we have anything to show
    if [ -n "$status_parts" ]; then
        echo "<!-- 🤖$status_parts -->" >&2
    fi
fi

log_to_file "========== Hook Complete =========="

# Exit successfully
exit 0
