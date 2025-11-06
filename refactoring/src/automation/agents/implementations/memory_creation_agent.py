"""Memory Creation Agent - Extract memorable moments for character memory logs.

This agent analyzes Claude's responses to extract:
- Important events characters experienced
- Significant dialogue
- Emotional moments
- Decisions made
- Character development

Memories are saved with accurate timestamps from TimeTrackingAgent.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


# Standardized tag taxonomy to prevent tag sprawl
EMOTION_TAGS = [
    "happy", "sad", "angry", "fearful", "surprised", "disgusted", "anxious",
    "excited", "disappointed", "relieved", "guilty", "ashamed", "proud",
    "jealous", "confused", "bored", "content", "lonely", "nostalgic"
]

ACTION_TAGS = [
    "combat", "dialogue", "decision", "discovery", "revelation", "confession",
    "argument", "reconciliation", "betrayal", "sacrifice", "victory", "defeat",
    "escape", "capture", "rescue", "death", "injury", "healing"
]

DESCRIPTOR_TAGS = [
    "milestone", "turning_point", "character_growth", "relationship_change",
    "secret_learned", "promise_made", "promise_broken", "first_time",
    "last_time", "regret", "triumph", "trauma", "bonding_moment"
]


class MemoryCreationAgent(BaseAgent):
    """Extract memorable moments and save to character memory logs.

    Uses session state from ResponseAnalyzerAgent and TimeTrackingAgent for context.
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "memory_creation"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute memory extraction and save to memory logs.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze
            **kwargs: Additional context

        Returns:
            Summary string of memories created
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping memory creation")
            return "No response to analyze"

        try:
            self.log(f"Creating memories for message #{message_number}")

            # Step 1: Get scene context from session state
            scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

            # Step 2: Extract context (with fallbacks)
            characters_in_scene = scene_context.get("characters_in_scene", [])
            location = scene_context.get("location", "Unknown")
            chapter = scene_context.get("chapter", "")

            # Fallback: If no characters detected, try to extract from response
            if not characters_in_scene:
                self.log("No characters in scene_context, will extract from response")
                characters_in_scene = None  # Signal to LLM to extract

            # Step 3: Get timestamp from TimeTrackingAgent's time_context
            timestamp = self._get_timestamp_from_time_tracking(scene_context, message_number)

            # Step 4: Build LLM prompt
            prompt = self._build_memory_extraction_prompt(
                user_message,
                claude_response,
                characters_in_scene,
                location,
                chapter
            )

            # Step 5: Call LLM for memory extraction (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 6: Parse JSON response
            memories_data = self.parse_json_response(response)

            if not memories_data or "memories" not in memories_data:
                self.log("Failed to parse memories from LLM response")
                return "Memory extraction failed"

            # Step 7: Save memories using repository
            saved_count = self._save_memories(
                memories_data["memories"],
                location,
                chapter,
                timestamp,
                message_number
            )

            # Step 8: Return summary
            return self._format_summary(saved_count, memories_data["memories"])

        except Exception as e:
            self.log(f"Error in memory creation: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Memory creation failed: {e}"

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_memory_extraction_prompt(
        self,
        user_message: str,
        claude_response: str,
        characters_in_scene: list[str] | None,
        location: str,
        chapter: str
    ) -> str:
        """Build LLM prompt for memory extraction.

        Args:
            user_message: User's message
            claude_response: Claude's response
            characters_in_scene: Characters detected (None = extract from response)
            location: Current location
            chapter: Current chapter

        Returns:
            LLM prompt string
        """
        # Build character context
        if characters_in_scene:
            char_context = f"CHARACTERS IN SCENE: {', '.join(characters_in_scene)}"
        else:
            char_context = "CHARACTERS IN SCENE: (extract from response)"

        # Build tag guidance
        emotion_tags_str = ", ".join(EMOTION_TAGS[:10]) + ", ..."
        action_tags_str = ", ".join(ACTION_TAGS[:10]) + ", ..."
        descriptor_tags_str = ", ".join(DESCRIPTOR_TAGS[:10]) + ", ..."

        return f"""Analyze this roleplay response and extract memorable moments for each character.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}

{char_context}
LOCATION: {location}
CHAPTER: {chapter}

For each character, identify:
- Important events they experienced
- Significant dialogue they said or heard
- Emotional moments (joy, sadness, anger, fear, surprise, etc.)
- Decisions they made
- Character development or growth
- Memorable interactions

DO NOT include relationship changes here - those are tracked separately.

**Tag Guidance** (use these as reference, but not exclusively):
- Emotions: {emotion_tags_str}
- Actions: {action_tags_str}
- Descriptors: {descriptor_tags_str}

Tags should include:
1. Character names mentioned in the memory
2. Relevant emotion/action/descriptor tags from above
3. Custom tags if none of the above fit

Respond with JSON ONLY:
{{
  "memories": [
    {{
      "character": "Alice",
      "summary": "Brief 1-sentence summary of the memorable moment",
      "details": "More detailed description of what happened and why it's memorable",
      "tags": ["Alice", "Bob", "happy", "dialogue", "bonding_moment"],
      "quoted_dialogue": ["\\"Exact quote with escaped quotes\\"", "\\"Another quote\\""]
    }}
  ]
}}

IMPORTANT:
- Only create memories for moments that are truly memorable (don't extract every mundane detail)
- Each memory should focus on one specific moment or event
- quoted_dialogue should contain EXACT quotes from the response (with escaped quotes)
- If no memorable moments for a character, don't create an entry for them
- If characters_in_scene was "(extract from response)", determine characters yourself"""

    # ==========================================================================
    # Timestamp Handling
    # ==========================================================================

    def _get_timestamp_from_time_tracking(
        self,
        scene_context: dict,
        message_number: int
    ) -> str:
        """Get timestamp from TimeTrackingAgent's time_context.

        Args:
            scene_context: Scene context from session state
            message_number: Current message number

        Returns:
            ISO 8601 formatted timestamp
        """
        time_ctx = scene_context.get("time_context", {})

        if not time_ctx:
            # No time tracking data - use current real-world time as fallback
            self.log("No time_context found, using current real-world time")
            return datetime.now().isoformat()

        current_datetime = time_ctx.get("current_datetime")

        if not current_datetime:
            # Time tracking exists but no current_datetime
            self.log("time_context exists but no current_datetime, using current time")
            return datetime.now().isoformat()

        # Convert time_context datetime to ISO 8601
        try:
            dt = datetime(
                current_datetime.get("year", 2024),
                current_datetime.get("month", 1),
                current_datetime.get("day", 1),
                current_datetime.get("hour", 0),
                current_datetime.get("minute", 0)
            )
            return dt.isoformat()
        except Exception as e:
            self.log(f"Failed to convert time_context to ISO: {e}")
            return datetime.now().isoformat()

    # ==========================================================================
    # Memory Saving
    # ==========================================================================

    def _save_memories(
        self,
        memories: list[dict],
        location: str,
        chapter: str,
        timestamp: str,
        message_number: int
    ) -> int:
        """Save memories using FixtureEntityRepository.

        Args:
            memories: List of memory dicts from LLM
            location: Current location
            chapter: Current chapter
            timestamp: ISO 8601 timestamp
            message_number: Current message number

        Returns:
            Number of memories saved
        """
        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(rp_dir=self.rp_dir)

        saved_count = 0

        for memory in memories:
            character = memory.get("character")

            if not character:
                self.log("Memory missing character field, skipping")
                continue

            # Build memory entry matching MemoryEntry dataclass structure
            memory_entry = {
                "id": f"mem_{uuid4().hex[:8]}",
                "summary": memory.get("summary", ""),
                "details": memory.get("details", ""),
                "tags": memory.get("tags", []),
                "quoted_dialogue": memory.get("quoted_dialogue", []),
                "relationships": {},  # Empty - tracked by RelationshipAnalysisAgent
                "location": location,
                "chapter": chapter,
                "timestamp": timestamp,
                "message_index": message_number
            }

            try:
                # Save using repository (handles timeline branching)
                repository.append_memory_entry(character, memory_entry)
                saved_count += 1
                self.log(f"Saved memory for {character}: {memory_entry['id']}")
            except Exception as e:
                self.log(f"Failed to save memory for {character}: {e}")
                # Continue with other memories even if one fails

        return saved_count

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def _format_summary(self, saved_count: int, memories: list[dict]) -> str:
        """Format memory creation result as summary string.

        Args:
            saved_count: Number of memories successfully saved
            memories: List of memory dicts

        Returns:
            Summary string
        """
        # Count unique characters
        characters = set(m.get("character") for m in memories if m.get("character"))
        num_characters = len(characters)

        if saved_count == 0:
            return "No memories created"

        if saved_count == 1:
            char_name = memories[0].get("character", "unknown")
            return f"Created 1 memory for {char_name}"

        return f"Created {saved_count} memories for {num_characters} characters"


__all__ = ["MemoryCreationAgent"]
