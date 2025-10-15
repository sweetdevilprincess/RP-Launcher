#!/usr/bin/env python3
"""
Memory Extraction Agent

Extracts 2-5 relevant memories per character from their memory banks.
Achieves 96% token reduction vs loading all memories.

Part of Phase 1.1 (Memory Extraction System)
Runs before Response N+1 (parallel execution, user sees latency)
"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class MemoryExtractionAgent(BaseAgent):
    """Extracts relevant memories for scene participants

    This agent takes the list of scene participants and extracts
    only 2-5 relevant memories from each character's memory bank.

    Example: Instead of loading 8,500 tokens (45 memories for Marcus),
    we extract 3 relevant memories totaling ~320 tokens (96% reduction).

    Master File + Extraction Pattern:
    - Store 100+ memories in character memory files
    - Extract only 2-5 relevant memories per response
    - Scales infinitely (doesn't matter if you have 50 or 500 memories)
    """

    def get_agent_id(self) -> str:
        return "memory_extraction"

    def get_description(self) -> str:
        return "Extract relevant memories for scene participants"

    def gather_data(self, user_message: str, scene_participants: List[str]) -> dict:
        """Gather data for memory extraction

        Args:
            user_message: User's message (for relevance context)
            scene_participants: List of characters in scene

        Returns:
            Dict with user_message, scene_participants, memory_files
        """
        # Read memory files for each participant
        memory_summaries = {}
        for character in scene_participants:
            memories_dir = self.rp_dir / "memories" / character
            if memories_dir.exists():
                # Get list of memory files
                memory_files = list(memories_dir.glob("*.md"))
                # Read all memories (will ask DeepSeek to select relevant ones)
                memories = []
                for mf in memory_files:
                    memories.append({
                        "file": mf.name,
                        "content": self._read_file_safe(mf, "")[:500]  # Preview
                    })
                memory_summaries[character] = {
                    "count": len(memory_files),
                    "memories": memories
                }
            else:
                memory_summaries[character] = {
                    "count": 0,
                    "memories": []
                }

        return {
            "user_message": user_message,
            "scene_participants": scene_participants,
            "memory_summaries": memory_summaries,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for memory extraction

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        # Build memory context for each character
        memories_context = ""
        for character, mem_data in data["memory_summaries"].items():
            memories_context += f"\n\n### {character} ({mem_data['count']} total memories)\n"
            if mem_data["memories"]:
                for i, mem in enumerate(mem_data["memories"][:20], 1):  # Limit to 20
                    memories_context += f"\n**Memory {i}** ({mem['file']}):\n{mem['content'][:300]}...\n"
            else:
                memories_context += "No memories found\n"

        prompt = f"""Extract 2-5 relevant memories for each scene participant.

USER MESSAGE (for context):
{data['user_message']}

SCENE PARTICIPANTS: {', '.join(data['scene_participants'])}

AVAILABLE MEMORIES:
{memories_context}

For each character, select 2-5 memories most relevant to the current conversation:
- Prioritize recent memories (just happened)
- Include foundational memories (first meeting, major events)
- Include memories relevant to current topic
- Skip irrelevant backstory

Guidelines:
- Extract 2-5 memories per character
- JUST HAPPENED (last response) = highest priority
- FOUNDATIONAL (first meetings, major revelations) = high priority
- RELEVANT TO TOPIC = medium priority
- DISTANT/UNRELATED = skip
- If character has no memories, return empty array
- Each memory summary should be 1-2 sentences max

Return your analysis as a JSON object:

{{
  "chars": {{
    "CharacterName": {{
      "total": <total memories available>,
      "mems": [
        {{
          "id": "MEM-###",
          "title": "Memory title",
          "when": "Chapter X, Response Y",
          "loc": "location",
          "sig": <1-10>,
          "why": "why this memory matters now",
          "summary": "1-2 sentence summary"
        }}
      ]
    }}
  }}
}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format memory extraction result for JSON cache

        Args:
            result: DeepSeek JSON analysis
            data: Original data dict (may include 'duration_ms')

        Returns:
            JSON string for agent cache
        """
        try:
            # Parse DeepSeek JSON output
            analysis = json.loads(result.strip())

            # Build output dict
            output = {
                "chars": analysis.get("chars", {})
            }

            # Add duration if tracked by base agent
            if "duration_ms" in data:
                output["dur"] = data["duration_ms"]

            return json.dumps(output)

        except json.JSONDecodeError as e:
            # Fallback: return error info as JSON
            return json.dumps({
                "error": "Failed to parse DeepSeek output",
                "raw_output": result[:500],
                "exception": str(e)
            })


# Convenience function for standalone use
def extract_memories(
    rp_dir: Path,
    user_message: str,
    scene_participants: List[str],
    log_file: Optional[Path] = None
) -> str:
    """Extract relevant memories for scene participants

    Args:
        rp_dir: RP directory path
        user_message: User's message for context
        scene_participants: List of characters in scene
        log_file: Optional log file

    Returns:
        Formatted memory extraction string
    """
    agent = MemoryExtractionAgent(rp_dir, log_file)
    return agent.execute(user_message, scene_participants)
