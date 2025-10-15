#!/usr/bin/env python3
"""
Plot Thread Detection Agent

Detects new plot threads, tracks mentions of existing threads,
and identifies resolved threads.

Part of Phase 2.1 (Plot Thread Tracker)
Runs after Response N while user types Message N+1 (~5 seconds, hidden)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class PlotThreadDetectionAgent(BaseAgent):
    """Detects and tracks plot threads

    This agent:
    - Identifies new plot threads introduced in the response
    - Tracks mentions of existing threads
    - Detects resolved threads
    - Updates consequence countdowns
    - Assigns priority (High/Medium/Low)
    - Determines time sensitivity

    Plot Thread Types:
    - Character development (personal growth, backstory revelation)
    - Relationship arcs (romantic, friendship, rivalry)
    - Career/life goals (job interviews, projects, ambitions)
    - Conflicts (interpersonal, internal, external)
    - Mysteries (questions to be answered)
    - Future events (planned meetings, deadlines)
    """

    def get_agent_id(self) -> str:
        return "plot_thread_detection"

    def get_description(self) -> str:
        return "Detect new, mentioned, and resolved plot threads"

    def gather_data(self, response_text: str, response_number: int,
                    chapter: Optional[str] = None) -> dict:
        """Gather data for plot thread detection

        Args:
            response_text: The Claude response to analyze
            response_number: Current response number
            chapter: Optional chapter identifier

        Returns:
            Dict with response_text, response_number, existing_threads
        """
        # Read existing plot threads
        threads_file = self.rp_dir / "state" / "plot_threads_master.md"
        existing_threads = self._read_file_safe(threads_file, "No existing threads")

        return {
            "response_text": response_text,
            "response_number": response_number,
            "chapter": chapter or "Unknown",
            "existing_threads": existing_threads,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for plot thread detection

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        prompt = f"""Analyze this response for plot thread activity (new, mentioned, resolved).

RESPONSE TEXT:
{data['response_text']}

CONTEXT:
- Response Number: {data['response_number']}
- Chapter: {data['chapter']}

EXISTING PLOT THREADS:
{data['existing_threads']}

Guidelines:
- NEW: Only threads explicitly introduced or set up in this response
- MENTIONED: Existing threads that were referenced or advanced
- RESOLVED: Threads that reached a conclusion or were dropped
- Priority: high (immediate), medium (important), low (background)
- Time Sensitive = has deadline or consequence if ignored
- Be specific about thread titles (not generic like "Character Development")

Return your analysis as a JSON object:

{{
  "threads": {{
    "new": [
      {{
        "id": "THREAD-XXX",
        "title": "<specific thread title>",
        "priority": "<high|medium|low>",
        "time_sensitive": <true|false>,
        "chars": ["char1", "char2"],
        "tags": ["#tag1", "#tag2"],
        "desc": "<2-3 sentence description>"
      }}
    ],
    "mentioned": [
      {{
        "id": "THREAD-XXX",
        "update": "<what was said about this thread>"
      }}
    ],
    "resolved": [
      {{
        "id": "THREAD-XXX",
        "resolution": "<how it was resolved>"
      }}
    ]
  }}
}}

If no thread activity in a category, use empty arrays: "new": [], "mentioned": [], "resolved": []

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format plot thread detection result for JSON cache

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
                "threads": analysis.get("threads", {
                    "new": [],
                    "mentioned": [],
                    "resolved": []
                })
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
def detect_plot_threads(
    rp_dir: Path,
    response_text: str,
    response_number: int,
    chapter: Optional[str] = None,
    log_file: Optional[Path] = None
) -> str:
    """Detect plot thread activity in response

    Args:
        rp_dir: RP directory path
        response_text: Claude's response to analyze
        response_number: Current response number
        chapter: Optional chapter identifier
        log_file: Optional log file

    Returns:
        Formatted plot thread detection string
    """
    agent = PlotThreadDetectionAgent(rp_dir, log_file)
    return agent.execute(response_text, response_number, chapter)
