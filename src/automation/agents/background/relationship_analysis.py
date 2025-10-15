#!/usr/bin/env python3
"""
Relationship Analysis Agent

Analyzes character interactions against their personality preferences.
Tracks relationship score changes and tier transitions.

Part of Phase 1.2 (Dynamic Relationship System)
Runs after Response N while user types Message N+1 (~5 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class RelationshipAnalysisAgent(BaseAgent):
    """Analyzes character interactions for relationship changes

    This agent:
    - Matches interactions against character preferences
    - Calculates relationship score changes
    - Detects tier transitions (Enemy → Hostile → Stranger → Friend, etc.)
    - Identifies what triggered the change

    Relationship Tiers:
    - Enemy (-100 to -30)
    - Hostile (-29 to -10)
    - Stranger (-9 to 10)
    - Acquaintance (11 to 30)
    - Friend (31 to 60)
    - Close Friend (61 to 80)
    - Best Friend (81 to 100)
    """

    def get_agent_id(self) -> str:
        return "relationship_analysis"

    def get_description(self) -> str:
        return "Preference matching and relationship tier tracking"

    def gather_data(self, response_text: str, response_number: int,
                    characters_in_scene: Optional[list] = None) -> dict:
        """Gather data for relationship analysis

        Args:
            response_text: The Claude response to analyze
            response_number: Current response number
            characters_in_scene: List of characters that interacted

        Returns:
            Dict with response_text, response_number, characters, preferences
        """
        # Read relationship preferences if they exist
        preferences = {}
        if characters_in_scene:
            for character in characters_in_scene:
                pref_file = self.rp_dir / "relationships" / f"{character}_preferences.json"
                preferences[character] = self._read_file_safe(pref_file, "{}")

        # Read current relationship states
        relationship_states = {}
        state_file = self.rp_dir / "state" / "relationships.json"
        current_states = self._read_file_safe(state_file, "{}")

        return {
            "response_text": response_text,
            "response_number": response_number,
            "characters_in_scene": characters_in_scene or [],
            "preferences": preferences,
            "current_states": current_states,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for relationship analysis

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        # Build character context
        char_context = ""
        if data["characters_in_scene"]:
            char_context = f"Characters interacting: {', '.join(data['characters_in_scene'])}"
        else:
            char_context = "No specific characters identified for analysis"

        # Build preferences context
        pref_context = ""
        if data["preferences"]:
            pref_context = "\nCHARACTER PREFERENCES:\n"
            for char, prefs in data["preferences"].items():
                pref_context += f"\n{char}:\n{prefs}\n"

        prompt = f"""Analyze character interactions in this response for relationship changes.

RESPONSE TEXT:
{data['response_text']}

CONTEXT:
{char_context}
{pref_context}

CURRENT RELATIONSHIP STATES:
{data['current_states'] if data['current_states'] != '{}' else 'No existing states'}

Relationship Tiers:
- enemy (-100 to -30)
- hostile (-29 to -10)
- stranger (-9 to 10)
- acquaintance (11 to 30)
- friend (31 to 60)
- close_friend (61 to 80)
- best_friend (81 to 100)

Guidelines:
- Only analyze characters that actually interacted in this response
- Be specific about what triggered score changes
- Note if preferences are not available (will need to create them)
- If no significant interactions occurred, return empty rels array

Return your analysis as a JSON object:

{{
  "rels": [
    {{
      "pair": "CharA_CharB",
      "tier": "<enemy|hostile|stranger|acquaintance|friend|close_friend|best_friend>",
      "score": <current score 0-100>,
      "prev": <previous score>,
      "change": <+/- points>,
      "trigger": "<what caused the change>",
      "tier_change": <true|false>,
      "prev_tier": "<previous tier if changed, otherwise null>",
      "notes": "<brief analysis>"
    }}
  ]
}}

If no relationship changes occurred, return: {{"rels": []}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format relationship analysis result for JSON cache

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
                "rels": analysis.get("rels", [])
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
def analyze_relationships(
    rp_dir: Path,
    response_text: str,
    response_number: int,
    characters_in_scene: Optional[list] = None,
    log_file: Optional[Path] = None
) -> str:
    """Analyze relationship changes in response

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to analyze
        response_number: Current response number
        characters_in_scene: List of characters that interacted
        log_file: Optional log file

    Returns:
        Formatted relationship analysis string
    """
    agent = RelationshipAnalysisAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number, characters_in_scene)
