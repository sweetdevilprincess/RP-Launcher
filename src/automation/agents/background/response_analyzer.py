#!/usr/bin/env python3
"""
Response Analyzer Agent

Analyzes Claude's response to extract structured information about:
- Scene classification (type, pacing, tension)
- Characters (in scene vs mentioned)
- Location tracking
- Timeline extraction
- Variety and pacing alerts

Part of Phase 0.4 (Background Analysis System)
Runs after Response N while user types Message N+1 (~15 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class ResponseAnalyzerAgent(BaseAgent):
    """Analyzes roleplay responses for scene classification and pacing

    This agent extracts structured information from Claude's response:
    - Scene type (dialogue, action, introspection, transition, world_building)
    - Pacing (fast, medium, slow)
    - Tension level (1-10)
    - Characters in scene
    - Characters mentioned but absent
    - Current location
    - Time passed
    - Variety alerts (too many similar scenes)
    """

    def get_agent_id(self) -> str:
        return "response_analyzer"

    def get_description(self) -> str:
        return "Scene classification, character identification, pacing analysis"

    def gather_data(self, response_text: str, response_number: int,
                    previous_scenes: Optional[list] = None) -> dict:
        """Gather data for response analysis

        Args:
            response_text: The Claude response to analyze
            response_number: Current response number
            previous_scenes: Optional list of previous scene types for variety check

        Returns:
            Dict with response_text, response_number, previous_scenes, timestamp
        """
        return {
            "response_text": response_text,
            "response_number": response_number,
            "previous_scenes": previous_scenes or [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for response analysis

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        # Build previous scenes context if available
        prev_scenes_text = ""
        if data["previous_scenes"]:
            prev_scenes_text = f"\n\nPREVIOUS SCENES (last 5): {', '.join(data['previous_scenes'])}"

        prompt = f"""Analyze this roleplay response and extract structured information.

RESPONSE TEXT:
{data['response_text']}
{prev_scenes_text}

Return your analysis as a JSON object with the following structure:

{{
  "scene": {{
    "type": "<dialogue|action|introspection|transition|world_building>",
    "pace": "<fast|medium|slow>",
    "tension": <1-10>,
    "words": <approximate word count>
  }},
  "chars": {{
    "in_scene": ["character1", "character2"],
    "mentioned": ["character3"],
    "new": ["new_character"] or []
  }},
  "loc": "<current location description>",
  "loc_changed": <true|false>,
  "prev_loc": "<previous location if changed, otherwise null>",
  "time": {{
    "elapsed": "<e.g. '30 minutes', '2 hours', 'unknown'>",
    "timestamp": "<e.g. 'Tuesday 3:00 PM', 'Evening', 'unknown'>",
    "day_chapter": "<if mentioned, otherwise null>"
  }},
  "alerts": {{
    "variety": "<good|warning|critical>",
    "variety_msg": "<warning message if applicable, otherwise null>",
    "tension_flat": <true|false>,
    "recommendation": "<recommendation for variety if needed, otherwise null>"
  }}
}}

Return ONLY the JSON object, no additional text. Use null for unknown/missing values."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format analysis result for JSON cache

        Args:
            result: DeepSeek JSON analysis
            data: Original data dict (may include 'duration_ms')

        Returns:
            JSON string for agent cache
        """
        try:
            # Parse DeepSeek JSON output
            analysis = json.loads(result.strip())

            # Build output dict with duration if available
            output = {
                "scene": analysis.get("scene", {}),
                "chars": analysis.get("chars", {}),
                "loc": analysis.get("loc", "unknown"),
                "loc_changed": analysis.get("loc_changed", False),
                "time": analysis.get("time", {}),
                "alerts": analysis.get("alerts", {})
            }

            # Add previous location if changed
            if analysis.get("prev_loc"):
                output["prev_loc"] = analysis["prev_loc"]

            # Add duration if tracked by base agent
            if "duration_ms" in data:
                output["dur"] = data["duration_ms"]

            return json.dumps(output)

        except json.JSONDecodeError as e:
            # Fallback: return error info as JSON
            return json.dumps({
                "error": "Failed to parse DeepSeek output",
                "raw_output": result[:500],  # First 500 chars
                "exception": str(e)
            })


# Convenience function for standalone use
def analyze_response(
    rp_dir: Path,
    response_text: str,
    response_number: int,
    previous_scenes: Optional[list] = None,
    log_file: Optional[Path] = None
) -> str:
    """Analyze a roleplay response

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to analyze
        response_number: Current response number
        previous_scenes: Optional list of previous scene types
        log_file: Optional log file

    Returns:
        Formatted analysis string
    """
    agent = ResponseAnalyzerAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number, previous_scenes)
