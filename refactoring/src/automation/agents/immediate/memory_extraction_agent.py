"""Memory Extraction Agent - Find relevant memories for context injection.

This immediate agent runs BEFORE Claude responds to extract relevant
memories from character memory logs and inject them into the prompt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class MemoryExtractionAgent(BaseAgent):
    """Extract relevant memories for characters in the scene.

    This immediate agent:
    1. Gets characters from session state (scene context)
    2. Loads recent memories for each character (last 50)
    3. Uses LLM to rank memories by relevance
    4. Returns formatted text for prompt injection
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "memory_extraction"

    def execute(
        self,
        user_message: str,
        message_number: int,
        **kwargs
    ) -> str:
        """Extract relevant memories and format for prompt injection.

        Args:
            user_message: User's message to analyze
            message_number: Current message index
            **kwargs: Additional context

        Returns:
            Formatted memory context for prompt injection (empty string if none)
        """
        try:
            self.log(f"Extracting relevant memories for message #{message_number}")

            # Step 1: Get characters from session state
            scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)
            characters = scene_context.get("characters_in_scene", [])

            if not characters:
                self.log("No characters in scene, skipping memory extraction")
                return ""  # No characters to extract memories for

            self.log(f"Found {len(characters)} characters: {', '.join(characters)}")

            # Step 2: Load recent memories from repository
            memories_by_character = self._load_recent_memories(characters, limit=50)

            if not memories_by_character:
                self.log("No memories available for any character")
                return ""  # No memories available

            # Count total memories
            total_memories = sum(len(mems) for mems in memories_by_character.values())
            self.log(f"Loaded {total_memories} total memories")

            # Step 3: Build LLM prompt for relevance ranking
            prompt = self._build_relevance_prompt(
                user_message,
                characters,
                memories_by_character
            )

            # Step 4: Call LLM for relevance ranking (temperature=0.0 for consistency)
            self.log("Calling LLM for memory relevance ranking...")
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 5: Parse JSON response
            result = self.parse_json_response(response)

            if not result or "relevant_memories" not in result:
                self.log("Failed to parse relevant memories from LLM")
                return ""

            relevant_memories = result.get("relevant_memories", [])

            if not relevant_memories:
                self.log("No relevant memories found")
                return ""

            self.log(f"Found {len(relevant_memories)} relevant memories")

            # Step 6: Format for prompt injection
            formatted = self._format_for_injection(relevant_memories)

            self.log(f"Memory extraction complete ({len(formatted)} characters)")
            return formatted

        except Exception as e:
            self.log(f"Error in memory extraction: {e}")
            import traceback
            self.log(traceback.format_exc())
            return ""  # Fail gracefully, don't block main flow

    # ==========================================================================
    # Memory Loading
    # ==========================================================================

    def _load_recent_memories(
        self,
        characters: list[str],
        limit: int = 50
    ) -> dict[str, list[dict[str, Any]]]:
        """Load recent memories for characters.

        Args:
            characters: List of character names
            limit: Maximum memories per character

        Returns:
            Dict mapping character to list of memory dicts
        """
        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(rp_dir=self.rp_dir)
        memories_by_character = {}

        for character in characters:
            try:
                # Load memory log (repository handles timeline automatically)
                memory_log = repository.get_memory_log(character)

                # Get last N memories (most recent)
                recent = list(memory_log.entries[-limit:])

                if not recent:
                    self.log(f"No memories found for {character}")
                    continue

                # Convert to dicts for LLM prompt
                memories_by_character[character] = [
                    {
                        "id": m.id,
                        "summary": m.summary,
                        "details": m.details,
                        "tags": list(m.tags) if m.tags else [],
                        "location": m.location or "Unknown",
                        "chapter": m.chapter or "Unknown",
                        "message_index": getattr(m, "message_index", 0)  # Handle old memories
                    }
                    for m in recent
                ]

                self.log(f"Loaded {len(recent)} memories for {character}")

            except KeyError:
                # Character has no memory log yet
                self.log(f"No memory log exists for {character}")
                continue
            except Exception as e:
                self.log(f"Could not load memories for {character}: {e}")
                continue

        return memories_by_character

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_relevance_prompt(
        self,
        user_message: str,
        characters: list[str],
        memories_by_character: dict[str, list[dict[str, Any]]]
    ) -> str:
        """Build LLM prompt for memory relevance ranking.

        Args:
            user_message: User's current message
            characters: List of characters in scene
            memories_by_character: Dict of character -> memories

        Returns:
            Formatted prompt string
        """
        # Build memory context
        memories_context = ""
        for character, memories in memories_by_character.items():
            memories_context += f"\n\n### {character} ({len(memories)} memories)\n"

            # Limit to prevent token overflow (show summaries only)
            display_limit = min(len(memories), 30)  # Max 30 per character

            for i, mem in enumerate(memories[-display_limit:], 1):  # Most recent
                memories_context += f"\n**Memory {i}** (ID: {mem['id']})\n"
                memories_context += f"Summary: {mem['summary']}\n"
                memories_context += f"Location: {mem['location']} | Chapter: {mem['chapter']}\n"

            if len(memories) > display_limit:
                memories_context += f"\n(... and {len(memories) - display_limit} older memories)\n"

        return f"""Find the most relevant memories for this conversation context.

USER MESSAGE:
{user_message}

CHARACTERS IN SCENE: {', '.join(characters)}

AVAILABLE MEMORIES:
{memories_context}

Select 5-10 memories that are most relevant to the current conversation:

**Prioritization:**
1. **RECENT** - Memories from the last few responses (high priority)
2. **TOPIC MATCH** - Memories directly related to what user is asking/doing
3. **EMOTIONAL SIGNIFICANCE** - Important moments that inform character responses
4. **PLOT THREADS** - Unresolved storylines that might be relevant
5. **AVOID REDUNDANCY** - Don't select similar memories

Respond with JSON ONLY:
{{
  "relevant_memories": [
    {{
      "character": "Alice",
      "memory_id": "mem_abc123",
      "summary": "Brief summary of the memory",
      "relevance": "Why this memory is relevant now"
    }}
  ]
}}

IMPORTANT:
- Select 5-10 memories total across all characters
- Prioritize quality over quantity
- If no memories are relevant, return empty array: {{"relevant_memories": []}}"""

    # ==========================================================================
    # Output Formatting
    # ==========================================================================

    def _format_for_injection(self, relevant_memories: list[dict[str, Any]]) -> str:
        """Format relevant memories for prompt injection.

        Args:
            relevant_memories: List of relevant memory dicts from LLM

        Returns:
            Formatted text for prompt injection
        """
        if not relevant_memories:
            return ""

        # Group by character
        by_character: dict[str, list[dict[str, Any]]] = {}
        for mem in relevant_memories:
            char = mem.get("character", "Unknown")
            if char not in by_character:
                by_character[char] = []
            by_character[char].append(mem)

        # Format as markdown
        lines = ["### RELEVANT MEMORIES\n"]

        for character, memories in by_character.items():
            lines.append(f"**{character}:**")
            for mem in memories:
                mem_id = mem.get("memory_id", "???")
                summary = mem.get("summary", "")
                lines.append(f"- [{mem_id}] {summary}")
            lines.append("")  # Blank line between characters

        return "\n".join(lines)


__all__ = ["MemoryExtractionAgent"]
