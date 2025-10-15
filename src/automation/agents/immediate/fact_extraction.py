#!/usr/bin/env python3
"""
Fact Extraction Agent

Extracts 5 key facts from entity cards for Tier 2 entities (mentioned but absent).
Achieves 97% token reduction vs loading full cards.

Part of Phase 0.5 (Context Intelligence - Three-Tier Loading)
Runs before Response N+1 (~2 seconds, user sees this latency)
"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class FactExtractionAgent(BaseAgent):
    """Extracts key facts for Tier 2 entities

    This agent takes a list of Tier 2 entities (mentioned but absent)
    and extracts only the 5 most important facts from their entity cards.

    Example: Instead of loading a 2,200 token entity card, we extract:
    1. Marcus's best friend since college
    2. Works as software engineer at TechCorp
    3. Known for being blunt and direct
    4. Doesn't like Lily (thinks she's "too flighty")
    5. Recently got engaged to Amy

    This achieves 97% token reduction (2,200 → 60 tokens).
    """

    def get_agent_id(self) -> str:
        return "fact_extraction"

    def get_description(self) -> str:
        return "Extract 5 key facts for Tier 2 entities"

    def gather_data(self, user_message: str, tier2_entities: List[str]) -> dict:
        """Gather data for fact extraction

        Args:
            user_message: User's message (for context)
            tier2_entities: List of Tier 2 entity names

        Returns:
            Dict with user_message, tier2_entities, entity_cards
        """
        # Read entity cards for Tier 2 entities
        entity_cards = {}
        for entity_name in tier2_entities:
            card_file = self.rp_dir / "entities" / f"{entity_name}.md"
            if card_file.exists():
                entity_cards[entity_name] = self._read_file_safe(card_file, "")
            else:
                entity_cards[entity_name] = f"[Entity card not found: {entity_name}]"

        return {
            "user_message": user_message,
            "tier2_entities": tier2_entities,
            "entity_cards": entity_cards,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for fact extraction

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        # Build entity card context
        cards_context = ""
        for entity_name, card_content in data["entity_cards"].items():
            cards_context += f"\n\n### {entity_name}\n{card_content[:2000]}"  # Limit per card

        prompt = f"""Extract 5 key facts for each Tier 2 entity (mentioned but not present in scene).

USER MESSAGE (for context):
{data['user_message']}

TIER 2 ENTITIES: {', '.join(data['tier2_entities'])}

ENTITY CARDS:
{cards_context}

For each entity, extract the 5 most important facts that Claude should know:
- Focus on facts relevant to current conversation
- Prioritize relationships, personality traits, current situation
- Skip detailed backstory unless directly relevant
- Keep each fact to one short sentence

Guidelines:
- Extract ONLY 5 facts per entity (no more, no less)
- Facts should be concise (one sentence each)
- Prioritize information relevant to the current conversation
- Focus on: relationships, personality, current situation, key traits
- Skip: detailed backstory, minor details, long descriptions
- If entity card doesn't exist, return empty facts array

Return your analysis as a JSON object:

{{
  "entities": {{
    "EntityName": {{
      "facts": [
        "First most important fact",
        "Second most important fact",
        "Third most important fact",
        "Fourth most important fact",
        "Fifth most important fact"
      ]
    }}
  }}
}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format fact extraction result for JSON cache

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
                "entities": analysis.get("entities", {})
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
def extract_facts(
    rp_dir: Path,
    user_message: str,
    tier2_entities: List[str],
    log_file: Optional[Path] = None
) -> str:
    """Extract key facts for Tier 2 entities

    Args:
        rp_dir: RP directory path
        user_message: User's message for context
        tier2_entities: List of Tier 2 entity names
        log_file: Optional log file

    Returns:
        Formatted fact extraction string
    """
    agent = FactExtractionAgent(rp_dir, log_file)
    return agent.execute(user_message, tier2_entities)
