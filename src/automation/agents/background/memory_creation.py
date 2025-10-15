#!/usr/bin/env python3
"""
Memory Creation Agent

Extracts memorable moments from Claude's response and creates memory cards.
Identifies significant events, revelations, character moments, and emotional beats.

Part of Phase 1.1 (Memory Extraction System)
Runs after Response N while user types Message N+1 (~5 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class MemoryCreationAgent(BaseAgent):
    """Extracts memorable moments from responses

    This agent identifies:
    - Significant events or revelations
    - Important character moments
    - Emotional beats worth remembering
    - First meetings or major relationship changes
    - Conflicts or resolutions

    Each memory includes:
    - Characters involved
    - Location
    - Memory type (revelation, conflict, first_meeting, etc.)
    - Significance score (1-10)
    - Emotional tone
    - Key quote
    - Tags for searching
    """

    def get_agent_id(self) -> str:
        return "memory_creation"

    def get_description(self) -> str:
        return "Extract memorable moments from response"

    def gather_data(self, response_text: str, response_number: int,
                    chapter: Optional[str] = None) -> dict:
        """Gather data for memory extraction

        Args:
            response_text: The Claude response to analyze
            response_number: Current response number
            chapter: Optional chapter identifier

        Returns:
            Dict with response_text, response_number, chapter, timestamp
        """
        return {
            "response_text": response_text,
            "response_number": response_number,
            "chapter": chapter or "Unknown",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for memory extraction

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        prompt = f"""Extract memorable moments from this roleplay response that should be saved as memories.

RESPONSE TEXT:
{data['response_text']}

CONTEXT:
- Response Number: {data['response_number']}
- Chapter: {data['chapter']}

Identify 0-3 memorable moments worth saving. Not every response has memorable moments - be selective.

Guidelines:
- Be selective: Only extract truly memorable moments (significance 6+)
- Prioritize revelations, character development, major plot events
- Skip routine dialogue or mundane actions
- Each memory should be specific and meaningful

Return your analysis as a JSON object:

{{
  "mems": [
    {{
      "title": "<brief title>",
      "chars": ["character1", "character2"],
      "loc": "<location>",
      "type": "<revelation|conflict|first_meeting|character_moment|relationship_development|plot_event>",
      "sig": <1-10 significance score>,
      "tone": "<emotional tone: vulnerable, tense, joyful, etc>",
      "summary": "<2-3 sentence summary>",
      "quote": "<most memorable line>",
      "tags": ["#tag1", "#tag2"]
    }}
  ]
}}

If there are no memorable moments, return: {{"mems": []}}

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
                "mems": analysis.get("mems", [])
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
    response_text: str,
    response_number: int,
    chapter: Optional[str] = None,
    log_file: Optional[Path] = None
) -> str:
    """Extract memorable moments from response

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to analyze
        response_number: Current response number
        chapter: Optional chapter identifier
        log_file: Optional log file

    Returns:
        Formatted memory extraction string
    """
    agent = MemoryCreationAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number, chapter)
