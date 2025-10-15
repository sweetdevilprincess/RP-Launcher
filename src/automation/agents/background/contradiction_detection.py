#!/usr/bin/env python3
"""
Contradiction Detection Agent

Detects contradictions between new response and established facts.
Optional agent for quality assurance (Phase 2.3).

Part of Phase 2.3 (Contradiction Detection - Optional)
Runs after Response N while user types Message N+1 (~2 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class ContradictionDetectionAgent(BaseAgent):
    """Detects contradictions in responses

    This agent checks new responses against established facts:
    - Character traits and background
    - Location details
    - Timeline events
    - World rules and mechanics
    - Previously stated facts

    Note: This is an OPTIONAL agent for quality assurance.
    The Knowledge Base (Phase 2.2) may be sufficient for most cases.
    """

    def get_agent_id(self) -> str:
        return "contradiction_detection"

    def get_description(self) -> str:
        return "Optional fact-checking against established canon"

    def gather_data(self, response_text: str, response_number: int) -> dict:
        """Gather data for contradiction detection

        Args:
            response_text: The Claude response to check
            response_number: Current response number

        Returns:
            Dict with response_text, response_number, established_facts
        """
        # Read established facts
        kb_file = self.rp_dir / "state" / "knowledge_base.md"
        knowledge_base = self._read_file_safe(kb_file, "")

        facts_file = self.rp_dir / "state" / "story_facts.json"
        story_facts = self._read_file_safe(facts_file, "{}")

        # Read entity cards for character facts
        entities_dir = self.rp_dir / "entities"
        entity_files = list(entities_dir.glob("*.md")) if entities_dir.exists() else []
        entity_summaries = []
        for ef in entity_files[:10]:  # Limit to first 10 to keep prompt manageable
            entity_summaries.append(f"{ef.stem}: {self._read_file_safe(ef, '')[:200]}...")

        return {
            "response_text": response_text,
            "response_number": response_number,
            "knowledge_base": knowledge_base,
            "story_facts": story_facts,
            "entity_summaries": entity_summaries,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for contradiction detection

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        # Build entity context
        entity_context = ""
        if data["entity_summaries"]:
            entity_context = "\n\nENTITY SUMMARIES:\n" + "\n".join(data["entity_summaries"])

        prompt = f"""Check this response for contradictions against established facts.

RESPONSE TEXT:
{data['response_text']}

ESTABLISHED KNOWLEDGE BASE:
{data['knowledge_base'][:1500] if data['knowledge_base'] else 'No knowledge base yet'}

STORY FACTS:
{data['story_facts']}
{entity_context}

Check for contradictions in these categories:
- Character Facts (age, appearance, background, personality, relationships, skills)
- Location Details (physical descriptions, geography, features)
- Timeline (event ordering, time elapsed, dates)
- World Rules (technology, magic/supernatural, social norms, physical laws)
- Previously Stated Facts (plot details, historical events, established canon)

Guidelines:
- Be selective: Only flag clear contradictions, not ambiguities
- Severity: minor (small detail), moderate (noticeable but workable), major (breaks canon)
- Don't flag reasonable character development as contradiction
- Don't flag elaboration/addition of details (only direct conflicts)
- If unsure, don't flag (false positives are worse than misses)

Return your analysis as a JSON object:

{{
  "contradictions": [
    {{
      "cat": "<character|location|timeline|world_rules|facts>",
      "subj": "<what is contradicted>",
      "established": "<what was previously established>",
      "new": "<what the response says now>",
      "severity": "<minor|moderate|major>"
    }}
  ],
  "verified": <count of facts checked and found consistent>
}}

If no contradictions found, return: {{"contradictions": [], "verified": 5}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format contradiction detection result for JSON cache

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
                "contradictions": analysis.get("contradictions", []),
                "verified": analysis.get("verified", 0)
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
def detect_contradictions(
    rp_dir: Path,
    response_text: str,
    response_number: int,
    log_file: Optional[Path] = None
) -> str:
    """Check response for contradictions

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to check
        response_number: Current response number
        log_file: Optional log file

    Returns:
        Formatted contradiction detection string
    """
    agent = ContradictionDetectionAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number)
