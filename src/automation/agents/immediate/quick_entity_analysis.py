#!/usr/bin/env python3
"""
Quick Entity Analysis Agent

Quickly identifies entities mentioned in user's message to determine:
- Scene participants (Tier 1 - load full cards)
- Mentioned but absent (Tier 2 - extract facts)
- Locations mentioned

Part of Phase 0.5 (Context Intelligence - Three-Tier Loading)
Runs before Response N+1 (~3 seconds, user sees this latency)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class QuickEntityAnalysisAgent(BaseAgent):
    """Identifies entities mentioned in user message

    This agent quickly determines:
    - Which characters are in the scene (Tier 1)
    - Which characters are mentioned but absent (Tier 2)
    - Which locations are relevant
    - New entities that might need cards

    Three-Tier Loading Strategy:
    - Tier 1: Scene participants → Load FULL entity cards
    - Tier 2: Mentioned but absent → Extract 5 key facts
    - Tier 3: Not mentioned → Skip entirely
    """

    def get_agent_id(self) -> str:
        return "quick_entity_analysis"

    def get_description(self) -> str:
        return "Identify entities mentioned in user message"

    def gather_data(self, user_message: str, message_number: int) -> dict:
        """Gather data for entity analysis

        Args:
            user_message: The user's message
            message_number: Current message number

        Returns:
            Dict with user_message, message_number, available_entities
        """
        # Get list of available entity cards
        entities_dir = self.rp_dir / "entities"
        available_entities = []
        if entities_dir.exists():
            available_entities = [f.stem for f in entities_dir.glob("*.md")]

        # Get list of available locations
        locations_dir = self.rp_dir / "locations"
        available_locations = []
        if locations_dir.exists():
            available_locations = [f.stem.replace("_", " ") for f in locations_dir.glob("*.md")]

        return {
            "user_message": user_message,
            "message_number": message_number,
            "available_entities": available_entities,
            "available_locations": available_locations,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for entity analysis

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        prompt = f"""Analyze this user message to identify which entities are relevant.

USER MESSAGE:
{data['user_message']}

AVAILABLE ENTITIES:
{', '.join(data['available_entities']) if data['available_entities'] else 'No existing entity cards'}

AVAILABLE LOCATIONS:
{', '.join(data['available_locations']) if data['available_locations'] else 'No existing location cards'}

Classify entities into three tiers:
- **TIER 1**: Scene participants (will load FULL cards - high token cost)
- **TIER 2**: Mentioned but absent (will extract 5 facts - 97% reduction)
- **TIER 3**: Irrelevant (will skip entirely - 100% reduction)

Guidelines:
- Tier 1 = ONLY characters actively in the scene right now
- Tier 2 = mentioned by name but not present
- Tier 3 = everything else (just count them)
- Be conservative with Tier 1 (full cards are expensive)
- If user message is just continuing conversation, keep existing scene participants

Return your analysis as a JSON object:

{{
  "tier1": ["Character1", "Character2"],
  "tier2": ["Character3"],
  "tier3_count": <number of entities being skipped>,
  "locs": ["Location1"],
  "new_entities": [
    {{
      "name": "NewCharacter",
      "note": "mentioned character, may need card"
    }}
  ]
}}

If no entities in a tier, use empty arrays: "tier1": [], "tier2": [], etc.
If no new entities mentioned, use: "new_entities": []

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format entity analysis result for JSON cache

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
                "tier1": analysis.get("tier1", []),
                "tier2": analysis.get("tier2", []),
                "tier3_count": analysis.get("tier3_count", 0),
                "locs": analysis.get("locs", []),
                "new_entities": analysis.get("new_entities", [])
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
def analyze_entities(
    rp_dir: Path,
    user_message: str,
    message_number: int,
    log_file: Optional[Path] = None
) -> str:
    """Analyze entities mentioned in user message

    Args:
        rp_dir: RP directory path
        user_message: User's message to analyze
        message_number: Current message number
        log_file: Optional log file

    Returns:
        Formatted entity analysis string
    """
    agent = QuickEntityAnalysisAgent(rp_dir, log_file)
    return agent.execute(user_message, message_number)
