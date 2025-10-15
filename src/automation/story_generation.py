#!/usr/bin/env python3
"""
Story Generation Module

Handles DeepSeek API calls for:
- Story arc generation
- Chapter summaries
- Entity card generation (text generation part)
"""

import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from src.clients import deepseek as deepseek_client
from src.automation.core import log_to_file
from src.fs_write_queue import get_write_queue


# Get write queue instance
_write_queue = get_write_queue()


class StoryGenerator:
    """Handles story generation via DeepSeek API"""

    def __init__(self, rp_dir: Path, log_file: Path):
        """Initialize story generator

        Args:
            rp_dir: RP directory path
            log_file: Path to log file
        """
        self.rp_dir = rp_dir
        self.log_file = log_file

    def _call_deepseek_api(self, prompt: str) -> str:
        """Call DeepSeek API via OpenRouter

        Args:
            prompt: Prompt to send

        Returns:
            Generated content or empty string on error
        """
        try:
            log_to_file(
                self.log_file,
                f"Calling DeepSeek API (model: {deepseek_client.DEFAULT_MODEL})",
            )
            content = deepseek_client.call_deepseek(prompt, rp_dir=self.rp_dir)
            log_to_file(self.log_file, f"DeepSeek API call successful ({len(content)} chars)")
            return content
        except deepseek_client.MissingAPIKeyError as exc:
            log_to_file(self.log_file, f"ERROR: DeepSeek API key missing: {exc}")
        except requests.exceptions.Timeout:
            log_to_file(self.log_file, "ERROR: DeepSeek API timeout (60s)")
        except requests.exceptions.RequestException as exc:
            log_to_file(self.log_file, f"ERROR: DeepSeek API request failed: {exc}")
        except deepseek_client.DeepSeekError as exc:
            log_to_file(self.log_file, f"ERROR: DeepSeek API error: {exc}")
        except Exception as exc:
            log_to_file(self.log_file, f"ERROR: Unexpected DeepSeek error: {exc}")

        return ""

    def generate_story_arc_instructions(self, response_count: int) -> str:
        """Generate story arc injection instructions for Claude

        Args:
            response_count: Current response count

        Returns:
            Arc generation instructions (markdown)
        """
        log_to_file(self.log_file, f"[AUTO-GEN] Generating story arc update at response {response_count}")

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

    def generate_chapter_summary(self, chapter_number: int, recent_responses: List[str]) -> Optional[str]:
        """Generate chapter summary using DeepSeek

        Args:
            chapter_number: Chapter number to summarize
            recent_responses: List of recent RP responses from this chapter

        Returns:
            Chapter summary text or None on error
        """
        log_to_file(self.log_file, f"[AUTO-GEN] Generating chapter {chapter_number} summary with DeepSeek")

        # Read current state for context
        state_file = self.rp_dir / "state" / "current_state.md"
        current_state = ""
        if state_file.exists():
            try:
                current_state = state_file.read_text(encoding='utf-8')
            except Exception as e:
                log_to_file(self.log_file, f"WARNING: Could not read current_state.md: {e}")

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
        summary = self._call_deepseek_api(prompt)

        if summary:
            # Save summary
            chapters_dir = self.rp_dir / "chapters"
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
            log_to_file(self.log_file, f"[SUCCESS] Chapter {chapter_number} summary saved to chapters/Chapter {chapter_number}.txt")
            return summary
        else:
            log_to_file(self.log_file, f"[ERROR] Failed to generate chapter {chapter_number} summary")
            return None


# Convenience functions for backward compatibility
def call_deepseek_api(prompt: str, log_file: Path, rp_dir: Optional[Path] = None) -> str:
    """Call DeepSeek API (convenience function)

    Args:
        prompt: Prompt to send
        log_file: Path to log file
        rp_dir: Optional RP directory path

    Returns:
        Generated content or empty string on error
    """
    if rp_dir is None:
        # Just call the API directly without story generator
        try:
            log_to_file(log_file, f"Calling DeepSeek API (model: {deepseek_client.DEFAULT_MODEL})")
            content = deepseek_client.call_deepseek(prompt, rp_dir=rp_dir)
            log_to_file(log_file, f"DeepSeek API call successful ({len(content)} chars)")
            return content
        except Exception as exc:
            log_to_file(log_file, f"ERROR: DeepSeek API error: {exc}")
            return ""

    generator = StoryGenerator(rp_dir, log_file)
    return generator._call_deepseek_api(prompt)


def auto_generate_story_arc(rp_dir: Path, response_count: int, log_file: Path) -> str:
    """Generate story arc injection (convenience function)

    Args:
        rp_dir: RP directory path
        response_count: Current response count
        log_file: Path to log file

    Returns:
        Arc generation instructions
    """
    generator = StoryGenerator(rp_dir, log_file)
    return generator.generate_story_arc_instructions(response_count)


def auto_generate_chapter_summary(rp_dir: Path, chapter_number: int, recent_responses: List[str], log_file: Path) -> Optional[str]:
    """Generate chapter summary (convenience function)

    Args:
        rp_dir: RP directory path
        chapter_number: Chapter number
        recent_responses: Recent RP responses
        log_file: Path to log file

    Returns:
        Chapter summary or None on error
    """
    generator = StoryGenerator(rp_dir, log_file)
    return generator.generate_chapter_summary(chapter_number, recent_responses)
