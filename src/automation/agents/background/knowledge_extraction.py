#!/usr/bin/env python3
"""
Knowledge Extraction Agent

Extracts world-building facts from responses and adds them to the knowledge base.
Tracks setting details, cultural information, organizations, locations, and important items.

Part of Phase 2.2 (Knowledge Base System)
Runs after Response N while user types Message N+1 (~3 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class KnowledgeExtractionAgent(BaseAgent):
    """Extracts world-building knowledge from responses

    This agent identifies and extracts:
    - Setting details (genre, time period, technology level)
    - Geography (neighborhoods, landmarks, regions)
    - Organizations (companies, institutions, groups)
    - Locations (specific places with features)
    - Cultural details (customs, practices, norms)
    - Important items (story-significant objects)
    - Historical events (backstory, world events)

    Each fact includes:
    - Category (setting, geography, organizations, etc.)
    - Subject (what it's about)
    - Fact statement
    - Source (chapter, response number)
    - Confidence level (high, medium, low)
    """

    def get_agent_id(self) -> str:
        return "knowledge_extraction"

    def get_description(self) -> str:
        return "Extract world-building facts from response"

    def gather_data(self, response_text: str, response_number: int,
                    chapter: Optional[str] = None) -> dict:
        """Gather data for knowledge extraction

        Args:
            response_text: The Claude response to analyze
            response_number: Current response number
            chapter: Optional chapter identifier

        Returns:
            Dict with response_text, response_number, chapter, existing_kb
        """
        # Read existing knowledge base
        kb_file = self.rp_dir / "state" / "knowledge_base.md"
        existing_kb = self._read_file_safe(kb_file, "No existing knowledge base")

        return {
            "response_text": response_text,
            "response_number": response_number,
            "chapter": chapter or "Unknown",
            "existing_kb": existing_kb,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for knowledge extraction

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        prompt = f"""Extract world-building facts from this response for the knowledge base.

RESPONSE TEXT:
{data['response_text']}

CONTEXT:
- Response Number: {data['response_number']}
- Chapter: {data['chapter']}

EXISTING KNOWLEDGE BASE:
{data['existing_kb'][:1000]}... [truncated]

Extract 0-5 new facts about the world. Focus on:
- Setting details (time period, genre, technology)
- Locations (specific places, features, atmosphere)
- Organizations (companies, groups, institutions)
- Cultural details (customs, norms, practices)
- Geography (neighborhoods, landmarks, regions)
- Important items (significant objects, artifacts)
- Historical events (backstory, world history)

Guidelines:
- Only extract NEW facts not already in the knowledge base
- Be factual, not interpretive (state what IS, not what MIGHT be)
- Skip character-specific information (handled by entity cards)
- Skip temporary plot details (handled by plot threads)
- Focus on WORLD information that's generally applicable
- Confidence: high (explicitly stated), medium (strongly implied), low (weak inference)

Return your analysis as a JSON object:

{{
  "facts": [
    {{
      "cat": "<setting|locations|organizations|cultural|geography|items|history>",
      "subj": "<what this fact is about>",
      "fact": "<the actual factual statement>",
      "conf": "<high|medium|low>"
    }}
  ]
}}

If no new world-building facts, return: {{"facts": []}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format knowledge extraction result for JSON cache

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
                "facts": analysis.get("facts", [])
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
def extract_knowledge(
    rp_dir: Path,
    response_text: str,
    response_number: int,
    chapter: Optional[str] = None,
    log_file: Optional[Path] = None
) -> str:
    """Extract world-building knowledge from response

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to analyze
        response_number: Current response number
        chapter: Optional chapter identifier
        log_file: Optional log file

    Returns:
        Formatted knowledge extraction string
    """
    agent = KnowledgeExtractionAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number, chapter)
