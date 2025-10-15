#!/usr/bin/env python3
"""
TUI Bridge Script - Connects TUI to Claude Code

This script monitors for TUI input and sends it to Claude Code,
then captures the response and sends it back to the TUI.

Includes Python-based automation that replicates the bash hook functionality:
- Response counter increment
- Entity tracking (JSON)
- Time calculation from activities
- Conditional file loading (triggers)
- Status file generation
- Logging system

Usage:
    python tui_bridge.py "Example RP"

Run this in a separate terminal alongside the TUI.
"""

# ============================================================================
# ⚠️  CRITICAL: DO NOT MOVE THIS CODE BELOW - MUST BE FIRST! ⚠️
# ============================================================================
# This Python path fix MUST be the very first code that runs, before ANY
# other imports. If you move this down or import anything before it, you'll
# get Unicode encoding errors (emojis failing) which indicates the wrong
# Python (conda pkgs cache) is being used.
#
# This code detects if we're using the wrong Python and relaunches with the
# correct one BEFORE any imports that would fail.
# ============================================================================

import sys
from pathlib import Path

# Check if we're using the wrong Python (pkgs cache) and relaunch if needed
current_python = Path(sys.executable)
if "\\pkgs\\" in str(current_python) or "/pkgs/" in str(current_python):
    # We're using pkgs cache Python - find the correct one
    import subprocess
    conda_root = None
    for parent in current_python.parents:
        if parent.name in ["miniconda3", "anaconda3", "miniforge3"]:
            conda_root = parent
            break

    if conda_root:
        correct_python = conda_root / "python.exe"
        if correct_python.exists():
            # Relaunch with correct Python
            result = subprocess.run(
                [str(correct_python), sys.argv[0]] + sys.argv[1:],
                cwd=str(Path.cwd())
            )
            sys.exit(result.returncode)

# Now add project root to Python path
# Bridge is in src/, so go up one level to project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now safe to import everything else
import time
import json
import re
import subprocess
import requests
from datetime import datetime
from typing import Optional

from src.clients import deepseek as deepseek_client
from src.clients.claude_api import ClaudeAPIClient, ConversationManager, load_api_key
from src.clients.claude_sdk import ClaudeSDKClient

# Import enhanced trigger system
from src.trigger_system.trigger_system import TriggerMatcher

# Import file change tracker
from src.file_change_tracker import FileChangeTracker

# Import write queue
from src.fs_write_queue import get_write_queue, flush_all_writes, shutdown_write_queue


# =============================================================================
# WRITE QUEUE INITIALIZATION
# =============================================================================

# Initialize global write queue with 500ms debounce
# This reduces disk I/O by batching rapid writes
_write_queue = get_write_queue(debounce_ms=500, verbose=False)


# =============================================================================
# AUTOMATION MODULE - Replaces bash hook functionality
# =============================================================================

def log_to_file(log_file: Path, message: str) -> None:
    """Log message to hook.log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"WARNING: Could not write to log: {e}")


def load_config(config_file: Path) -> dict:
    """Load automation configuration from JSON"""
    defaults = {
        "auto_entity_cards": True,
        "entity_mention_threshold": 2,
        "auto_story_arc": True,
        "arc_frequency": 50
    }

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults
                return {**defaults, **config}
        except Exception:
            pass

    return defaults


def increment_counter(counter_file: Path, config: dict, log_file: Path) -> int:
    """Increment response counter and return new count"""
    count = 0

    if counter_file.exists():
        try:
            count = int(counter_file.read_text(encoding='utf-8').strip())
        except Exception:
            count = 0

    count += 1
    _write_queue.write_text(counter_file, str(count), encoding='utf-8')

    log_to_file(log_file, f"Response counter: {count}")

    # Check if arc generation needed (Phase 3: returns True if arc should be generated)
    arc_frequency = config.get('arc_frequency', 50)
    should_generate_arc = (count % arc_frequency == 0 and config.get('auto_story_arc', True))

    if should_generate_arc:
        log_to_file(log_file, f"Arc generation threshold reached at response {count}")

    return count, should_generate_arc


def calculate_time(message: str, timing_file: Path, state_file: Path, log_file: Path) -> tuple[int, str]:
    """Calculate elapsed time from activities mentioned in message

    Returns: (total_minutes, activities_description)
    """
    if not timing_file.exists():
        log_to_file(log_file, f"WARNING: Timing.txt not found at {timing_file}")
        return 0, ""

    # Read timing file
    try:
        timing_content = timing_file.read_text(encoding='utf-8')
    except Exception as e:
        log_to_file(log_file, f"ERROR: Could not read Timing.txt: {e}")
        return 0, ""

    # Parse activities (format: "activity: minutes")
    activities = {}
    for line in timing_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse comma-separated format: eat: 10, drink: 3, ...
        pairs = line.split(',')
        for pair in pairs:
            if ':' in pair:
                parts = pair.split(':', 1)
                activity = parts[0].strip().lower()
                try:
                    minutes = int(parts[1].strip())
                    activities[activity] = minutes
                except ValueError:
                    continue

    # Find activities in message
    total_minutes = 0
    activities_found = []
    message_lower = message.lower()

    for activity, minutes in activities.items():
        # Word boundary matching
        if re.search(r'\b' + re.escape(activity) + r'\b', message_lower):
            total_minutes += minutes
            activities_found.append(f"{activity} ({minutes} min)")

    # Log results
    if activities_found:
        activities_desc = ", ".join(activities_found)
        log_to_file(log_file, f"Time tracking: {activities_desc} = {total_minutes} minutes")

        # Update current_state.md with suggestion
        if state_file.exists():
            try:
                current_content = state_file.read_text(encoding='utf-8')

                # Remove any existing time suggestion
                lines = current_content.split('\n')
                filtered_lines = []
                skip_section = False
                for line in lines:
                    if line.startswith('## Time Calculation Suggestion'):
                        skip_section = True
                    elif line.startswith('##') and skip_section:
                        skip_section = False

                    if not skip_section:
                        filtered_lines.append(line)

                # Add new suggestion
                suggestion = f"""
## Time Calculation Suggestion (Latest)
**Activities detected**: {activities_desc}
**Suggested time elapsed**: {total_minutes} minutes
**Note**: Review and adjust for modifiers (fast/slow) or unknown activities
"""
                updated_content = '\n'.join(filtered_lines).rstrip() + '\n' + suggestion
                _write_queue.write_text(state_file, updated_content, encoding='utf-8')

            except Exception as e:
                log_to_file(log_file, f"WARNING: Could not update current_state.md: {e}")

        return total_minutes, activities_desc
    else:
        log_to_file(log_file, "No standard activities detected")
        return 0, ""


def track_entities(message: str, tracker_file: Path, counter_file: Path, config: dict, log_file: Path, file_tracker: Optional['FileChangeTracker'] = None) -> dict:
    """Track entity mentions in JSON

    Args:
        message: User message
        tracker_file: Entity tracker JSON file
        counter_file: Response counter file
        config: Configuration dict
        log_file: Log file
        file_tracker: Optional FileChangeTracker for marking auto-generated files

    Returns: dict of entities found in this message
    """
    # Initialize tracker if doesn't exist
    if not tracker_file.exists():
        tracker = {"entities": {}}
        _write_queue.write_json(tracker_file, tracker, encoding='utf-8', indent=2)
    else:
        try:
            tracker = json.loads(tracker_file.read_text(encoding='utf-8'))
        except Exception:
            tracker = {"entities": {}}

    # Extract capitalized words (potential entity names)
    potential_entities = re.findall(r'\b[A-Z][a-z]+\b', message)
    potential_entities = list(set(potential_entities))  # Remove duplicates

    # Common words to skip
    skip_words = {
        'The', 'A', 'An', 'I', 'You', 'He', 'She', 'It', 'They', 'We',
        'Is', 'Was', 'Are', 'Were', 'Be', 'Been', 'Have', 'Has', 'Had',
        'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should', 'May',
        'Might', 'Must', 'Can', 'My', 'Your', 'His', 'Her', 'Their', 'Our'
    }

    # Calculate current chapter (rough estimate: 10 responses per chapter)
    current_chapter = 1
    if counter_file.exists():
        try:
            responses = int(counter_file.read_text(encoding='utf-8').strip())
            current_chapter = (responses // 10) + 1
        except Exception:
            pass

    entities_this_message = {}

    # Track each entity
    for entity in potential_entities:
        if entity in skip_words:
            continue

        log_to_file(log_file, f"Entity mentioned: {entity}")

        # Get or create entity entry
        if entity not in tracker['entities']:
            tracker['entities'][entity] = {
                'mentions': 0,
                'first_chapter': current_chapter,
                'last_chapter': current_chapter,
                'card_created': False
            }

        # Update mentions
        entity_data = tracker['entities'][entity]
        entity_data['mentions'] += 1
        entity_data['last_chapter'] = current_chapter

        log_to_file(log_file, f"Entity '{entity}': {entity_data['mentions']} mentions")

        entities_this_message[entity] = entity_data

        # Check if card generation threshold reached
        threshold = config.get('entity_mention_threshold', 2)
        if (config.get('auto_entity_cards', True) and
            not entity_data['card_created'] and
            entity_data['mentions'] >= threshold):
            log_to_file(log_file, f"TRIGGERING AUTO-GENERATION: {entity} reached {threshold} mentions")

            # PHASE 3: Auto-generate entity card
            rp_dir_path = tracker_file.parent.parent  # Go up from state/ to RP root
            card_generated = auto_generate_entity_card(entity, entity_data, rp_dir_path, log_file, file_tracker)

            if card_generated:
                # Mark as created in tracker
                entity_data['card_created'] = True

    # Save updated tracker (queued with debouncing)
    try:
        _write_queue.write_json(tracker_file, tracker, encoding='utf-8', indent=2)
    except Exception as e:
        log_to_file(log_file, f"ERROR: Could not queue entity tracker: {e}")

    return entities_this_message


def identify_triggers(message: str, rp_dir: Path, log_file: Path, config: dict = None) -> tuple[list, list]:
    """Identify conditional files to load based on trigger words using enhanced trigger system

    Returns: (files_to_load, entity_names_loaded)
    """
    files_to_load = []
    entity_names = []

    # Build trigger system configuration
    if config is None:
        config = {}

    # Get trigger system config or use defaults
    trigger_config = config.get('trigger_system', {})

    # Default configuration: keyword + regex enabled, semantic optional
    full_config = {
        'trigger_system': {
            'keyword_matching': trigger_config.get('keyword_matching', {
                'enabled': True,
                'case_sensitive': False,
                'use_word_boundaries': True
            }),
            'regex_matching': trigger_config.get('regex_matching', {
                'enabled': True,
                'max_patterns_per_file': 10
            }),
            'semantic_matching': trigger_config.get('semantic_matching', {
                'enabled': False,  # Optional, requires sentence-transformers
                'model': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.7
            })
        }
    }

    log_to_file(log_file, "--- Using Enhanced Trigger System ---")
    log_to_file(log_file, f"Keyword: {full_config['trigger_system']['keyword_matching']['enabled']}, "
                          f"Regex: {full_config['trigger_system']['regex_matching']['enabled']}, "
                          f"Semantic: {full_config['trigger_system']['semantic_matching']['enabled']}")

    # Create TriggerMatcher
    try:
        matcher = TriggerMatcher(full_config)

        # Find triggered files
        matches = matcher.find_triggered_files(
            message,
            rp_dir,
            log_callback=lambda msg: log_to_file(log_file, msg)
        )

        # Convert matches to file paths and entity names
        for match in matches:
            files_to_load.append(match.file_path)
            entity_names.append(match.entity_name)

            # Log match details
            if match.trigger_type == 'semantic':
                log_to_file(log_file,
                    f"TRIGGER: {match.entity_name} ({match.trigger_type}, "
                    f"pattern: '{match.matched_pattern}', confidence: {match.confidence:.3f})")
            else:
                log_to_file(log_file,
                    f"TRIGGER: {match.entity_name} ({match.trigger_type}, "
                    f"pattern: '{match.matched_pattern}')")

        if files_to_load:
            log_to_file(log_file, f"Conditional files loaded: {len(files_to_load)}")

    except Exception as e:
        log_to_file(log_file, f"ERROR in enhanced trigger system: {e}")
        log_to_file(log_file, "Falling back to no triggers")
        import traceback
        log_to_file(log_file, traceback.format_exc())

    return files_to_load, entity_names


def update_status_file(status_file: Path, state_file: Path, counter_file: Path,
                       tracker_file: Path, config: dict, loaded_entities: list) -> None:
    """Generate/update CURRENT_STATUS.md with system status"""
    # Get response count
    response_count = 0
    if counter_file.exists():
        try:
            response_count = int(counter_file.read_text(encoding='utf-8').strip())
        except Exception:
            pass

    # Get timestamp and location from current_state.md
    timestamp = "Unknown"
    location = "Unknown"
    chapter = "[Check current_state.md]"
    if state_file.exists():
        try:
            content = state_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('**Timestamp'):
                    timestamp = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
                elif line.startswith('**Location'):
                    location = line.split(':', 1)[1].strip() if ':' in line else "Unknown"
                elif line.startswith('**Chapter'):
                    chapter = line.split(':', 1)[1].strip() if ':' in line else chapter
        except Exception:
            pass

    # Count tracked entities
    entity_count = 0
    if tracker_file.exists():
        try:
            tracker = json.loads(tracker_file.read_text(encoding='utf-8'))
            entity_count = len(tracker.get('entities', {}))
        except Exception:
            pass

    # Calculate arc progress
    arc_frequency = config.get('arc_frequency', 50)
    arc_progress = response_count % arc_frequency
    arc_next = arc_frequency - arc_progress

    # Build progress bar
    bar_filled = (arc_progress * 10) // arc_frequency
    bar_empty = 10 - bar_filled
    progress_bar = '█' * bar_filled + '░' * bar_empty

    # Loaded entities string
    loaded_str = ', '.join(loaded_entities) if loaded_entities else "None"

    # Automation status
    auto_cards = "✅ ON" if config.get('auto_entity_cards', True) else "❌ OFF"
    auto_arc = "✅ ON" if config.get('auto_story_arc', True) else "❌ OFF"
    card_threshold = config.get('entity_mention_threshold', 2)

    # Write status file
    status_content = f"""# Current RP Status

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📍 Current State

- **Timestamp**: {timestamp}
- **Location**: {location}
- **Chapter**: {chapter}
- **Response Count**: {response_count}

---

## 📊 Progress

**Story Arc**: {arc_progress} / {arc_frequency} responses
- Next arc generation in: **{arc_next} responses**
- Progress: {progress_bar}

---

## 🎭 Entities

**Tracked**: {entity_count} entities in entity_tracker.json
**Loaded This Response**: {loaded_str}

---

## ⚙️ Automation

**Entity Cards**: {auto_cards} (Threshold: {card_threshold} mentions)
**Story Arcs**: {auto_arc} (Every {arc_frequency} responses)

---

## 📝 Quick Commands

- `/status` - Detailed status report
- `/continue` - Load session context
- `/endSession` - End session protocol
- `/arc` - Generate story arc
- `/gencard [type], [name]` - Create entity card
- `/note [text]` - Add quick note
- `/memory` - Update memory

---

*Keep this file open in a second pane for live status updates*
"""

    try:
        _write_queue.write_text(status_file, status_content, encoding='utf-8')
    except Exception as e:
        print(f"WARNING: Could not queue status file: {e}")


def call_deepseek_api(prompt: str, log_file: Path, rp_dir: Optional[Path] = None) -> str:
    """Call DeepSeek API via OpenRouter using the new Python helper.

    Returns: Generated content or empty string on error
    """
    try:
        log_to_file(
            log_file,
            f"Calling DeepSeek API (model: {deepseek_client.DEFAULT_MODEL})",
        )
        content = deepseek_client.call_deepseek(prompt, rp_dir=rp_dir)
        log_to_file(log_file, f"DeepSeek API call successful ({len(content)} chars)")
        return content
    except deepseek_client.MissingAPIKeyError as exc:
        log_to_file(log_file, f"ERROR: DeepSeek API key missing: {exc}")
    except requests.exceptions.Timeout:
        log_to_file(log_file, "ERROR: DeepSeek API timeout (60s)")
    except requests.exceptions.RequestException as exc:
        log_to_file(log_file, f"ERROR: DeepSeek API request failed: {exc}")
    except deepseek_client.DeepSeekError as exc:
        log_to_file(log_file, f"ERROR: DeepSeek API error: {exc}")
    except Exception as exc:  # noqa: BLE001 - want to log unexpected issues
        log_to_file(log_file, f"ERROR: Unexpected DeepSeek error: {exc}")

    return ""


def auto_generate_entity_card(entity_name: str, entity_data: dict, rp_dir: Path, log_file: Path, file_tracker: Optional['FileChangeTracker'] = None) -> bool:
    """Auto-generate entity card using DeepSeek API

    If card already exists, updates it with strikethrough formatting for changes.
    If card is new, creates fresh card without strikethrough.

    Args:
        entity_name: Name of entity
        entity_data: Entity tracking data
        rp_dir: RP directory path
        log_file: Log file path
        file_tracker: Optional FileChangeTracker to mark file as auto-generated

    Returns: True if card generated successfully, False otherwise
    """
    log_to_file(log_file, f"[AUTO-GEN] Generating entity card for: {entity_name}")

    # Check if card already exists
    entities_dir = rp_dir / "entities"
    card_file = entities_dir / f"[CHAR] {entity_name}.md"
    existing_card = None
    is_update = False

    if card_file.exists():
        try:
            existing_card = card_file.read_text(encoding='utf-8')
            is_update = True
            log_to_file(log_file, f"[AUTO-GEN] Existing card found - will UPDATE with strikethrough formatting")
        except Exception as e:
            log_to_file(log_file, f"WARNING: Could not read existing card: {e}")

    # Search recent chapters for context
    context = ""
    chapters_dir = rp_dir / "chapters"
    if chapters_dir.exists():
        chapter_files = sorted(chapters_dir.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        for chapter_file in chapter_files:
            try:
                chapter_content = chapter_file.read_text(encoding='utf-8')
                # Find lines mentioning the entity
                matching_lines = [line for line in chapter_content.split('\n')
                                if entity_name.lower() in line.lower()]
                if matching_lines:
                    context += f"\n\nFrom {chapter_file.name}:\n" + '\n'.join(matching_lines[:5])
            except Exception as e:
                log_to_file(log_file, f"WARNING: Could not read {chapter_file.name}: {e}")

    # If no context found, use generic
    if not context:
        context = f"Entity '{entity_name}' has been mentioned {entity_data['mentions']} times starting from chapter {entity_data['first_chapter']}. Generate a card based on typical story context."

    # Build prompt based on whether this is an update or new card
    first_chapter = entity_data.get('first_chapter', 1)
    mentions = entity_data.get('mentions', 0)

    if is_update and existing_card:
        # UPDATE EXISTING CARD - Use strikethrough formatting
        prompt = f"""UPDATE an existing entity card for a roleplay story.

Entity Name: {entity_name}
Current Mentions: {mentions} (first in chapter {first_chapter})

New Context from recent story:{context}

EXISTING CARD TO UPDATE:
---
{existing_card}
---

CRITICAL FORMATTING RULES - STRIKETHROUGH FOR CHANGES:

When information has CHANGED, you MUST preserve the old information with strikethrough:
- Use ~~old information~~ -> new information (ASCII arrow: dash greater-than)
- NEVER delete old information
- Keep all chapter appearances (never remove them)
- IMPORTANT: Use ASCII arrow (->) NOT Unicode arrow, for compatibility

Examples of CORRECT updates:
- ~~Lives alone~~ -> Lives with boyfriend
- ~~Works as barista~~ -> Works as legal assistant
- ~~Single~~ -> Dating Marcus (Chapter 3+)
- **Job**: ~~Coffee Corner Cafe (Ch. 1-3)~~ -> Morrison Law Firm (Ch. 4+)

When information is completely NEW (not replacing anything), add it normally without strikethrough.

REQUIRED UPDATES:
1. Update **Mention Count** to: {mentions}
2. Update **Last Updated** date to: {datetime.now().strftime("%B %d, %Y")}
3. Add any new Appearances sections for new chapters (keep all old chapters)
4. Add a change log entry at the top if significant changes occurred:
   ## Change Log
   - **{datetime.now().strftime("%B %d, %Y")}**: [Brief description of what changed]

5. Update any information that has changed based on the new context:
   - If living situation changed: ~~old~~ -> new
   - If job changed: ~~old~~ -> new
   - If relationships changed: ~~old~~ -> new
   - If appearance changed: ~~old~~ -> new
   - If personality evolved: ~~old~~ -> new with note about growth

OUTPUT REQUIREMENTS:
- Output the COMPLETE updated card in markdown format
- Include ALL sections from the original card
- Apply strikethrough formatting to ALL changed information
- Keep the same structure and heading format
- Use AI Dungeon trigger format: [Triggers:name,variations']

Output ONLY the completed updated entity card."""

    else:
        # CREATE NEW CARD - No strikethrough needed
        prompt = f"""Create an entity card for a roleplay story.

Entity Name: {entity_name}
Mentions: {mentions} (first in chapter {first_chapter})

Context from story:{context}

Generate a detailed entity card. Since we don't know the exact type yet, create a CHARACTER card with this structure:

# [CHAR] {entity_name}

[Triggers:{entity_name}']
**Type**: Character
**First Mentioned**: Chapter {first_chapter}
**Mention Count**: {mentions}

## Description
[Based on context, describe this character]

## Role in Story
[What function they seem to serve]

## Significance
[Why this character matters]

## Appearances
### Chapter {first_chapter}
- [Context of first appearance based on story info]

## Notes
[Additional relevant information]

---

**Last Updated**: {datetime.now().strftime("%B %d, %Y")}

Use AI Dungeon trigger format: [Triggers:name,variations']
Output ONLY the completed entity card in markdown format."""

    # Call DeepSeek API
    card_content = call_deepseek_api(prompt, log_file, rp_dir=rp_dir)

    if card_content:
        # Save card (queued)
        entities_dir.mkdir(exist_ok=True)
        _write_queue.write_text(card_file, card_content, encoding='utf-8')

        # Mark file as auto-generated for change tracking
        if file_tracker:
            file_tracker.mark_file_as_auto_generated(card_file)

        if is_update:
            log_to_file(log_file, f"[SUCCESS] Updated entity card with strikethrough formatting: entities/[CHAR] {entity_name}.md")
        else:
            log_to_file(log_file, f"[SUCCESS] Auto-generated new entity card: entities/[CHAR] {entity_name}.md")
        return True
    else:
        log_to_file(log_file, f"[ERROR] Failed to generate card for {entity_name}")
        return False


def auto_generate_chapter_summary(rp_dir: Path, chapter_number: int, recent_responses: list[str], log_file: Path) -> Optional[str]:
    """Generate chapter summary using DeepSeek

    Args:
        rp_dir: RP directory path
        chapter_number: Chapter number to summarize
        recent_responses: List of recent RP responses from this chapter
        log_file: Log file path

    Returns: Chapter summary text or None on error
    """
    log_to_file(log_file, f"[AUTO-GEN] Generating chapter {chapter_number} summary with DeepSeek")

    # Read current state for context
    state_file = rp_dir / "state" / "current_state.md"
    current_state = ""
    if state_file.exists():
        try:
            current_state = state_file.read_text(encoding='utf-8')
        except Exception as e:
            log_to_file(log_file, f"WARNING: Could not read current_state.md: {e}")

    # Build context from recent responses
    responses_text = "\n\n---\n\n".join(recent_responses)

    # Build prompt for DeepSeek
    prompt = f"""You are summarizing Chapter {chapter_number} of a roleplay story.

CURRENT STATE:
{current_state}

RECENT RP EXCHANGES (last {len(recent_responses)} responses):
{responses_text}

Create a detailed chapter summary focusing on:
1. **Major Plot Events**: What happened in this chapter? Key actions, decisions, conflicts.
2. **Character Actions and Decisions**: What did characters do? What choices were made?
3. **Emotional Moments**: Significant emotional beats, reactions, revelations.
4. **Relationship Dynamics**: How did relationships change or develop?
5. **Important Dialogue**: Quote key lines that reveal character or advance plot.
6. **Unresolved Tensions**: What questions or conflicts remain open?
7. **Setup for Future**: What threads or hooks were planted for future chapters?

Weight important story beats heavily. Include specific details that may be referenced later.

Use markdown with clear sections. Be thorough but concise (aim for 300-500 words).

Output ONLY the chapter summary."""

    # Call DeepSeek
    summary = call_deepseek_api(prompt, log_file, rp_dir=rp_dir)

    if summary:
        # Save summary
        chapters_dir = rp_dir / "chapters"
        chapters_dir.mkdir(exist_ok=True)

        summary_file = chapters_dir / f"Chapter {chapter_number}.txt"

        # Add header with metadata
        full_summary = f"""# Chapter {chapter_number} Summary

**Generated**: {datetime.now().strftime("%B %d, %Y %H:%M")}
**Responses**: {len(recent_responses)}

---

{summary}
"""

        _write_queue.write_text(summary_file, full_summary, encoding='utf-8')
        log_to_file(log_file, f"[SUCCESS] Chapter {chapter_number} summary saved to chapters/Chapter {chapter_number}.txt")
        return summary
    else:
        log_to_file(log_file, f"[ERROR] Failed to generate chapter {chapter_number} summary")
        return None


def auto_generate_story_arc(rp_dir: Path, response_count: int, log_file: Path) -> str:
    """Generate story arc injection for Claude to process

    Returns: Arc generation instructions for Claude
    """
    log_to_file(log_file, f"[AUTO-GEN] Generating story arc update at response {response_count}")

    # Build injection instructions for Claude
    arc_injection = f"""
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
"✅ Story arc auto-updated at response {response_count}"

<!-- ======================================== -->
"""

    return arc_injection


def load_tier1_files(rp_dir: Path, log_file: Path) -> dict[str, str]:
    """Load TIER_1 files (core RP files loaded every response)

    Returns: dict of {filename: content}
    """
    tier1_files = {}

    # Core RP files (always load)
    files_to_load = [
        rp_dir / "AUTHOR'S_NOTES.md",
        rp_dir / "STORY_GENOME.md",
        rp_dir / "SCENE_NOTES.md",
        rp_dir / "state" / "current_state.md",
        rp_dir / "state" / "story_arc.md",
        rp_dir / "characters" / "{{user}}.md",
    ]

    # Find main character ({{char}}) - first character file that's not {{user}}
    chars_dir = rp_dir / "characters"
    if chars_dir.exists():
        for char_file in chars_dir.glob("*.md"):
            if char_file.name != "{{user}}.md":
                files_to_load.append(char_file)
                break  # Only load the first main character

    # Load all files
    for file_path in files_to_load:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                tier1_files[file_path.name] = content
                log_to_file(log_file, f"TIER_1: Loaded {file_path.name}")
            except Exception as e:
                log_to_file(log_file, f"WARNING: Could not load TIER_1 file {file_path.name}: {e}")
        else:
            log_to_file(log_file, f"TIER_1: File not found: {file_path.name}")

    return tier1_files


def load_tier2_files(rp_dir: Path, response_count: int, log_file: Path) -> dict[str, str]:
    """Load TIER_2 files (guidelines loaded every 4th response)

    Returns: dict of {filename: content}
    """
    tier2_files = {}

    # Only load on 4th responses
    if response_count % 4 != 0:
        return tier2_files

    log_to_file(log_file, f"TIER_2: Loading (response {response_count} is divisible by 4)")

    # Guidelines and reference files
    files_to_load = [
        rp_dir.parent / "config" / "guidelines" / "Timing.txt",
        rp_dir.parent / "config" / "guidelines" / "Writing_Style_Guide.md",
        rp_dir.parent / "config" / "guidelines" / "NPC_Interaction_Rules.md",
        rp_dir.parent / "config" / "guidelines" / "POV_and_Writing_Checklist.md",
        rp_dir.parent / "config" / "guidelines" / "Time_Tracking_Guide.md",
        rp_dir.parent / "config" / "guidelines" / "Story Guidelines.md",
    ]

    # Also load RP overview
    rp_name = rp_dir.name
    overview_file = rp_dir / f"{rp_name}.md"
    if overview_file.exists():
        files_to_load.append(overview_file)

    # Load all files
    for file_path in files_to_load:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                tier2_files[file_path.name] = content
                log_to_file(log_file, f"TIER_2: Loaded {file_path.name}")
            except Exception as e:
                log_to_file(log_file, f"WARNING: Could not load TIER_2 file {file_path.name}: {e}")

    return tier2_files


def track_tier3_triggers(triggered_files: list, tracker_file: Path, log_file: Path) -> list:
    """Track TIER_3 trigger frequency and identify escalated files

    Files triggered 3+ times in last 10 responses get escalated to TIER_2

    Returns: list of files to escalate to TIER_2
    """
    if not triggered_files:
        return []

    # Load or initialize trigger history
    if tracker_file.exists():
        try:
            history = json.loads(tracker_file.read_text(encoding='utf-8'))
        except Exception:
            history = {"trigger_history": []}
    else:
        history = {"trigger_history": []}

    # Add current triggers to history
    current_triggers = [str(f) for f in triggered_files]
    history["trigger_history"].append(current_triggers)

    # Keep only last 10 responses
    history["trigger_history"] = history["trigger_history"][-10:]

    # Save updated history (queued)
    try:
        _write_queue.write_json(tracker_file, history, encoding='utf-8', indent=2)
    except Exception as e:
        log_to_file(log_file, f"WARNING: Could not queue trigger history: {e}")

    # Find files that should be escalated (3+ triggers in last 10)
    trigger_counts = {}
    for response_triggers in history["trigger_history"]:
        for file_path in response_triggers:
            trigger_counts[file_path] = trigger_counts.get(file_path, 0) + 1

    escalated = []
    for file_path, count in trigger_counts.items():
        if count >= 3:
            escalated.append(Path(file_path))
            log_to_file(log_file, f"TIER_3 ESCALATION: {Path(file_path).name} triggered {count}/10 times")

    return escalated


def run_automation(message: str, rp_dir: Path) -> tuple[str, list]:
    """Run all automation tasks and return enhanced prompt + loaded files

    Returns: (enhanced_prompt, loaded_entity_names)
    """
    # Setup paths
    state_dir = rp_dir / "state"
    counter_file = state_dir / "response_counter.txt"
    tracker_file = state_dir / "entity_tracker.json"
    config_file = state_dir / "automation_config.json"
    state_file = state_dir / "current_state.md"
    status_file = rp_dir / "CURRENT_STATUS.md"
    log_file = state_dir / "hook.log"
    timing_file = rp_dir.parent / "config" / "guidelines" / "Timing.txt"
    trigger_history_file = state_dir / "trigger_history.json"

    # Ensure state directory exists
    state_dir.mkdir(exist_ok=True)

    # Initialize tracking
    loaded_entities = []
    all_loaded_files = []

    # Initialize file change tracker
    file_tracker = FileChangeTracker(rp_dir)

    log_to_file(log_file, "========== RP Automation Starting (Phases 1-3: Full System) ==========")

    # 1. Load config
    config = load_config(config_file)

    # 2. Increment counter (Phase 3: also returns if arc should be generated)
    response_count, should_generate_arc = increment_counter(counter_file, config, log_file)

    # 3. Calculate time
    total_minutes, activities_desc = calculate_time(message, timing_file, state_file, log_file)

    # 4. Track entities (Phase 3: now auto-generates cards when threshold reached)
    entities_found = track_entities(message, tracker_file, counter_file, config, log_file, file_tracker)

    # 5. PHASE 2: Load TIER_1 files (core RP files - every response)
    log_to_file(log_file, "--- TIER_1 Loading (Core Files) ---")
    tier1_files = load_tier1_files(rp_dir, log_file)

    # 6. PHASE 2: Load TIER_2 files (guidelines - every 4th response)
    log_to_file(log_file, "--- TIER_2 Loading (Guidelines) ---")
    tier2_files = load_tier2_files(rp_dir, response_count, log_file)

    # 7. PHASE 2: Identify TIER_3 triggers (conditional entity/character files)
    log_to_file(log_file, "--- TIER_3 Loading (Conditional) ---")
    tier3_files, loaded_entities = identify_triggers(message, rp_dir, log_file, config)

    # 8. PHASE 2: Track trigger frequency and escalate if needed
    escalated_files = track_tier3_triggers(tier3_files, trigger_history_file, log_file)

    # 9. Update status file
    update_status_file(status_file, state_file, counter_file, tracker_file, config, loaded_entities)

    # Build enhanced prompt with tiered structure
    prompt_sections = []

    # PHASE 3: Story arc generation (if threshold reached)
    if should_generate_arc:
        arc_instructions = auto_generate_story_arc(rp_dir, response_count, log_file)
        prompt_sections.append(arc_instructions)

    # Time suggestion (if any)
    if total_minutes > 0:
        prompt_sections.append(f"⏱️ Time suggestion: {total_minutes} minutes ({activities_desc})")

    # TIER_1: Core RP files (always included)
    if tier1_files:
        tier1_section = "<!-- ========== TIER_1: CORE RP FILES (ALWAYS LOADED) ========== -->\n"
        for filename, content in tier1_files.items():
            tier1_section += f"\n<!-- FILE: {filename} -->\n{content}\n"
        prompt_sections.append(tier1_section)

    # TIER_2: Guidelines (every 4th response)
    if tier2_files:
        tier2_section = "<!-- ========== TIER_2: GUIDELINES (PERIODIC) ========== -->\n"
        for filename, content in tier2_files.items():
            tier2_section += f"\n<!-- FILE: {filename} -->\n{content}\n"
        prompt_sections.append(tier2_section)

    # TIER_3: Triggered files (conditional)
    if tier3_files:
        tier3_section = "<!-- ========== TIER_3: TRIGGERED FILES (CONDITIONAL) ========== -->\n"
        for file_path in tier3_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tier3_section += f"\n<!-- FILE: {file_path.name} -->\n{content}\n"
            except Exception as e:
                log_to_file(log_file, f"ERROR: Could not read {file_path.name}: {e}")
        prompt_sections.append(tier3_section)

    # TIER_3 ESCALATED: Frequently triggered files (treated like TIER_2)
    if escalated_files:
        escalated_section = "<!-- ========== TIER_3 ESCALATED: FREQUENTLY USED FILES ========== -->\n"
        for file_path in escalated_files:
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    escalated_section += f"\n<!-- FILE: {file_path.name} (ESCALATED) -->\n{content}\n"
                except Exception as e:
                    log_to_file(log_file, f"ERROR: Could not read escalated file {file_path.name}: {e}")
        prompt_sections.append(escalated_section)

    # User message
    prompt_sections.append(f"<!-- ========== USER MESSAGE ========== -->\n{message}")

    # Build final enhanced prompt
    enhanced_prompt = '\n\n'.join(prompt_sections)

    # Log summary
    arc_status = "YES (injected)" if should_generate_arc else "NO"
    log_to_file(log_file, f"Prompt built: TIER_1={len(tier1_files)} files, TIER_2={len(tier2_files)} files, TIER_3={len(tier3_files)} files, Escalated={len(escalated_files)} files")
    log_to_file(log_file, f"Phase 3: Arc generation={arc_status}, Entity cards auto-generated (see above)")
    log_to_file(log_file, "========== Automation Complete ==========")

    return enhanced_prompt, loaded_entities


def load_proxy_prompt(base_dir: Path) -> Optional[str]:
    """Load proxy prompt from proxy_prompt.txt.

    Args:
        base_dir: Base directory (RP Claude Code root)

    Returns:
        Proxy prompt text or None if not found or empty
    """
    proxy_file = base_dir / "config" / "proxy_prompt.txt"
    if not proxy_file.exists():
        return None

    try:
        content = proxy_file.read_text(encoding='utf-8').strip()
        # Filter out comment lines and empty lines
        lines = [line for line in content.split('\n')
                if line.strip() and not line.strip().startswith('#')]
        filtered_content = '\n'.join(lines).strip()

        return filtered_content if filtered_content else None
    except Exception as e:
        print(f"⚠️  Error loading proxy prompt: {e}")
        return None


def run_automation_with_caching(message: str, rp_dir: Path) -> tuple[str, str, list]:
    """Run automation and return cached context + dynamic prompt separately.

    This version separates TIER_1 files (which should be cached) from the
    rest of the content for use with the Claude API's prompt caching feature.

    Args:
        message: User's input message
        rp_dir: Path to the RP folder

    Returns:
        Tuple of (cached_context, dynamic_prompt, loaded_entities)
        - cached_context: TIER_1 files that should be cached in system prompt
        - dynamic_prompt: Everything else (TIER_2, TIER_3, user message)
        - loaded_entities: List of entity names that were loaded
    """
    config_file = rp_dir / "state" / "config.json"
    counter_file = rp_dir / "state" / "counter.txt"
    tracker_file = rp_dir / "state" / "entity_tracker.json"
    state_dir = rp_dir / "state"
    state_file = state_dir / "current_state.md"
    status_file = rp_dir / "CURRENT_STATUS.md"
    log_file = state_dir / "hook.log"
    timing_file = rp_dir.parent / "config" / "guidelines" / "Timing.txt"
    trigger_history_file = state_dir / "trigger_history.json"

    # Ensure state directory exists
    state_dir.mkdir(exist_ok=True)

    # Initialize tracking
    loaded_entities = []

    # Initialize file change tracker
    file_tracker = FileChangeTracker(rp_dir)

    log_to_file(log_file, "========== RP Automation Starting (API Mode with Caching) ==========")

    # 1. Load config
    config = load_config(config_file)

    # 2. Increment counter
    response_count, should_generate_arc = increment_counter(counter_file, config, log_file)

    # 3. Calculate time
    total_minutes, activities_desc = calculate_time(message, timing_file, state_file, log_file)

    # 4. Track entities
    entities_found = track_entities(message, tracker_file, counter_file, config, log_file, file_tracker)

    # 5. Load TIER_1 files (these will be cached!)
    log_to_file(log_file, "--- TIER_1 Loading (Core Files - FOR CACHING) ---")
    tier1_files = load_tier1_files(rp_dir, log_file)

    # 6. Load TIER_2 files
    log_to_file(log_file, "--- TIER_2 Loading (Guidelines) ---")
    tier2_files = load_tier2_files(rp_dir, response_count, log_file)

    # 7. Identify TIER_3 triggers
    log_to_file(log_file, "--- TIER_3 Loading (Conditional) ---")
    tier3_files, loaded_entities = identify_triggers(message, rp_dir, log_file, config)

    # 8. Track trigger frequency
    escalated_files = track_tier3_triggers(tier3_files, trigger_history_file, log_file)

    # 9. Check for file updates and generate notifications
    log_to_file(log_file, "--- Checking for file updates ---")
    all_loaded_files = []
    # Collect all files that will be in the context
    all_loaded_files.extend([rp_dir / name for name in tier1_files.keys() if (rp_dir / name).exists()])
    all_loaded_files.extend(tier3_files)
    all_loaded_files.extend(escalated_files)

    file_updates, updated_files = file_tracker.check_files_for_updates(all_loaded_files)
    update_notification = ""
    if file_updates:
        update_notification = file_tracker.generate_update_notification(file_updates)
        log_to_file(log_file, f"File updates detected: {len(file_updates)} files")
        for update in file_updates:
            log_to_file(log_file, f"  - {update['file_name']} ({update['category']})")

    # 10. Update status file
    update_status_file(status_file, state_file, counter_file, tracker_file, config, loaded_entities)

    # Build CACHED CONTEXT (TIER_1 only)
    cached_sections = []

    if tier1_files:
        tier1_section = "<!-- ========== TIER_1: CORE RP FILES (CACHED) ========== -->\n"
        for filename, content in tier1_files.items():
            tier1_section += f"\n<!-- FILE: {filename} -->\n{content}\n"
        cached_sections.append(tier1_section)

    cached_context = '\n\n'.join(cached_sections) if cached_sections else ""

    # Build DYNAMIC PROMPT (everything else)
    dynamic_sections = []

    # FILE UPDATE NOTIFICATIONS (highest priority - Claude needs to see these first!)
    if update_notification:
        dynamic_sections.append(update_notification)

    # Story arc generation (if threshold reached)
    if should_generate_arc:
        arc_instructions = auto_generate_story_arc(rp_dir, response_count, log_file)
        dynamic_sections.append(arc_instructions)

    # Time suggestion
    if total_minutes > 0:
        dynamic_sections.append(f"⏱️ Time suggestion: {total_minutes} minutes ({activities_desc})")

    # TIER_2: Guidelines (every 4th response)
    if tier2_files:
        tier2_section = "<!-- ========== TIER_2: GUIDELINES (PERIODIC) ========== -->\n"
        for filename, content in tier2_files.items():
            tier2_section += f"\n<!-- FILE: {filename} -->\n{content}\n"
        dynamic_sections.append(tier2_section)

    # TIER_3: Triggered files
    if tier3_files:
        tier3_section = "<!-- ========== TIER_3: TRIGGERED FILES (CONDITIONAL) ========== -->\n"
        for file_path in tier3_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                tier3_section += f"\n<!-- FILE: {file_path.name} -->\n{content}\n"
            except Exception as e:
                log_to_file(log_file, f"ERROR: Could not read {file_path.name}: {e}")
        dynamic_sections.append(tier3_section)

    # TIER_3 ESCALATED: Frequently triggered files
    if escalated_files:
        escalated_section = "<!-- ========== TIER_3 ESCALATED: FREQUENTLY USED FILES ========== -->\n"
        for file_path in escalated_files:
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    escalated_section += f"\n<!-- FILE: {file_path.name} (ESCALATED) -->\n{content}\n"
                except Exception as e:
                    log_to_file(log_file, f"ERROR: Could not read escalated file {file_path.name}: {e}")
        dynamic_sections.append(escalated_section)

    # User message
    dynamic_sections.append(f"<!-- ========== USER MESSAGE ========== -->\n{message}")

    # Build final dynamic prompt
    dynamic_prompt = '\n\n'.join(dynamic_sections)

    # Log summary
    arc_status = "YES (injected)" if should_generate_arc else "NO"
    log_to_file(log_file, f"Prompt built: TIER_1={len(tier1_files)} files (CACHED), TIER_2={len(tier2_files)} files, TIER_3={len(tier3_files)} files, Escalated={len(escalated_files)} files")
    log_to_file(log_file, f"Arc generation={arc_status}")
    log_to_file(log_file, "========== Automation Complete (Caching Mode) ==========")

    return cached_context, dynamic_prompt, loaded_entities


# =============================================================================
# MAIN BRIDGE LOOP
# =============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python tui_bridge.py <RP_FOLDER_NAME>")
        print("Example: python tui_bridge.py \"Example RP\"")
        sys.exit(1)

    # Get RP directory
    # Bridge is in src/, so go up one level to project root
    base_dir = Path(__file__).parent.parent
    rp_folder = sys.argv[1]
    rp_dir = base_dir / rp_folder

    if not rp_dir.exists():
        print(f"Error: RP folder not found: {rp_dir}")
        sys.exit(1)

    state_dir = rp_dir / "state"
    input_file = state_dir / "rp_client_input.txt"
    response_file = state_dir / "rp_client_response.txt"
    ready_flag = state_dir / "rp_client_ready.flag"
    done_flag = state_dir / "rp_client_done.flag"

    # Check for mode configuration (global config first, then per-RP)
    # Modes: SDK (default), API (alternative)
    use_api_mode = False
    use_sdk_mode = True  # SDK is now the default!
    api_client = None
    conversation_manager = None
    sdk_client = None

    try:
        # Check global config.json (created by TUI settings)
        global_config_file = base_dir / "config" / "config.json"
        local_config_file = state_dir / "config.json"

        config = {}

        # Load global config first
        if global_config_file.exists():
            with open(global_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # Override with local config if it exists
        if local_config_file.exists():
            with open(local_config_file, 'r', encoding='utf-8') as f:
                local_config = json.load(f)
                config.update(local_config)

        # Check if user wants API mode (alternative to SDK)
        use_api_mode = config.get("use_api_mode", False)

        if use_api_mode:
            # API mode requested - use direct API calls
            use_sdk_mode = False
            api_key = load_api_key()
            if api_key:
                api_client = ClaudeAPIClient(api_key)
                conversation_manager = ConversationManager(state_dir)
                print("🌉 TUI Bridge started (API MODE with Prompt Caching + Extended Thinking)")
                print("💾 TIER_1 files will be cached for maximum efficiency!")
                print("🧠 Extended thinking enabled for better context and fewer corrections!")
            else:
                print("⚠️  API mode enabled but no API key found. Falling back to SDK mode.")
                print("   Set ANTHROPIC_API_KEY environment variable or add to config.json")
                use_api_mode = False
                use_sdk_mode = True
    except Exception as e:
        print(f"⚠️  Error initializing API mode: {e}. Falling back to SDK mode.")
        use_api_mode = False
        use_sdk_mode = True

    # Initialize SDK mode (default)
    if use_sdk_mode and not use_api_mode:
        try:
            sdk_client = ClaudeSDKClient(cwd=rp_dir)
            print("🚀 TUI Bridge started (SDK MODE - High Performance)")
            print("💾 TIER_1 files will be cached for maximum efficiency!")
            print("⚡ Real-time streaming enabled!")
            print("🧠 Extended thinking enabled for better context and fewer corrections!")
        except Exception as e:
            print(f"❌ Error initializing SDK: {e}")
            print("   Make sure Node.js is installed and run: npm install")
            print("   Check work_in_progress/QUICKSTART_SDK.md for setup")
            sys.exit(1)

    print(f"📁 Monitoring: {rp_dir}")
    print("⏳ Waiting for TUI input...")
    print("(Press Ctrl+C to stop)")
    print()

    try:
        while True:
            # Check for ready flag
            if ready_flag.exists() and input_file.exists():
                print("📨 Received input from TUI")

                # Read user message
                try:
                    message = input_file.read_text(encoding='utf-8').strip()
                    print(f"📝 Message: {message[:50]}..." if len(message) > 50 else f"📝 Message: {message}")
                except Exception as e:
                    print(f"❌ Error reading input: {e}")
                    ready_flag.unlink(missing_ok=True)
                    continue

                # Check for /new command first
                session_flag = state_dir / "claude_session_active.flag"
                if message.strip().lower() == "/new":
                    # Start fresh conversation
                    if session_flag.exists():
                        session_flag.unlink()
                        print("🔄 Session reset - next message will start fresh conversation")
                    if use_api_mode and conversation_manager:
                        conversation_manager.clear_history()
                        print("🗑️  Conversation history cleared (API)")
                    if use_sdk_mode and sdk_client:
                        sdk_client.clear_session()
                        print("🗑️  Conversation history cleared (SDK)")
                    response = "Session reset. Your next message will start a new conversation."
                    # Write response and continue to next message
                    try:
                        response_file.write_text(response, encoding='utf-8')
                        done_flag.touch()
                        print("📤 Response sent to TUI")
                        print()
                        print("⏳ Waiting for next input...")
                    except Exception as e:
                        print(f"❌ Error writing response: {e}")
                    ready_flag.unlink(missing_ok=True)
                    continue

                # ===== API MODE =====
                if use_api_mode and api_client:
                    print("⚙️ Running automation (API Mode with Caching)...")
                    try:
                        cached_context, dynamic_prompt, loaded_entities = run_automation_with_caching(message, rp_dir)
                        if loaded_entities:
                            print(f"📚 TIER_3 entities loaded: {', '.join(loaded_entities)}")
                        print(f"✅ Automation complete - TIER_1 will be cached!")
                    except Exception as e:
                        print(f"⚠️ Automation error: {e}")
                        import traceback
                        traceback.print_exc()
                        cached_context = ""
                        dynamic_prompt = message

                    # Apply proxy prompt if enabled
                    if config.get("use_proxy", False):
                        proxy_prompt = load_proxy_prompt(base_dir)
                        if proxy_prompt:
                            print("🔀 Proxy mode active - injecting custom prompt")
                            dynamic_prompt = f"{proxy_prompt}\n\n---\n\n{dynamic_prompt}"

                    print("🤖 Sending to Claude API...")
                    try:
                        result = api_client.send_message(
                            user_message=dynamic_prompt,
                            cached_context=cached_context if cached_context else None,
                            conversation_history=conversation_manager.get_history(),
                            max_tokens=8192
                        )

                        response = result["content"]
                        print("✓ Response received")

                        # Add to conversation history
                        conversation_manager.add_user_message(dynamic_prompt)
                        conversation_manager.add_assistant_message(response)

                        # Print cache stats
                        print(api_client.format_cache_stats(result["usage"]))

                        # Create session flag after successful response
                        if not session_flag.exists():
                            session_flag.touch()
                            print("📝 Session flag created")

                    except Exception as e:
                        response = f"Error calling Claude API: {e}"
                        print(f"❌ {response}")
                        import traceback
                        traceback.print_exc()

                # ===== SDK MODE (default) =====
                elif use_sdk_mode and sdk_client:
                    print("⚙️ Running automation (SDK Mode with Caching)...")
                    try:
                        cached_context, dynamic_prompt, loaded_entities = run_automation_with_caching(message, rp_dir)
                        if loaded_entities:
                            print(f"📚 TIER_3 entities loaded: {', '.join(loaded_entities)}")
                        print(f"✅ Automation complete - TIER_1 will be cached!")
                    except Exception as e:
                        print(f"⚠️ Automation error: {e}")
                        import traceback
                        traceback.print_exc()
                        cached_context = ""
                        dynamic_prompt = message

                    # Apply proxy prompt if enabled
                    if config.get("use_proxy", False):
                        proxy_prompt = load_proxy_prompt(base_dir)
                        if proxy_prompt:
                            print("🔀 Proxy mode active - injecting custom prompt")
                            dynamic_prompt = f"{proxy_prompt}\n\n---\n\n{dynamic_prompt}"

                    # Call Claude Code SDK
                    print("🚀 Sending to Claude Code SDK...")
                    try:
                        response = ""
                        # Stream the response
                        for chunk in sdk_client.query(
                            message=dynamic_prompt,
                            cached_context=cached_context if cached_context else None
                        ):
                            response += chunk
                            # Could optionally stream to TUI here in the future

                        print("✓ Response received")

                        # Get and display cache stats
                        stats = sdk_client.get_cache_stats()
                        if stats:
                            print(stats)

                        # Get metadata
                        metadata = sdk_client.get_metadata()
                        if metadata and metadata.session_id:
                            print(f"📝 Session: {metadata.session_id[:8]}...")

                        # Create session flag after successful response
                        if not session_flag.exists():
                            session_flag.touch()
                            print("📝 Session flag created")

                    except Exception as e:
                        response = f"Error calling Claude Code SDK: {e}"
                        print(f"❌ {response}")
                        import traceback
                        traceback.print_exc()

                # Write response
                try:
                    response_file.write_text(response, encoding='utf-8')
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    print("⏳ Waiting for next input...")
                except Exception as e:
                    print(f"❌ Error writing response: {e}")

                # Clean up ready flag
                ready_flag.unlink(missing_ok=True)

            # Sleep briefly
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Bridge stopped")

        # Flush pending writes before shutdown
        print("💾 Flushing pending writes...")
        flush_all_writes()
        print("✓ All writes complete")

        # Clean up SDK client
        if sdk_client:
            sdk_client.close()
            print("🔒 SDK client closed")

        # Clean up flags
        ready_flag.unlink(missing_ok=True)
        done_flag.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
