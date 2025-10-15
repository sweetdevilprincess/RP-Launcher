#!/usr/bin/env python3
"""
Plot Thread Extraction Agent

Extracts 2-5 relevant plot threads from the master plot threads file.
Achieves 85% token reduction vs loading all threads.

Part of Phase 2.1 (Plot Thread Tracker)
Runs before Response N+1 (parallel execution, user sees latency)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class PlotThreadExtractionAgent(BaseAgent):
    """Extracts relevant plot threads from master file

    This agent takes the master plot threads file (50+ threads)
    and extracts only 2-5 threads relevant to the current conversation.

    Example: Instead of loading 5,500 tokens (25 active threads),
    we extract 3 relevant threads totaling ~800 tokens (85% reduction).

    Master File + Extraction Pattern:
    - Store 50+ plot threads in plot_threads_master.md
    - Extract only 2-5 relevant threads per response
    - Prioritize: CRITICAL (consequence triggered) > RELEVANT (natural to mention) > MONITORING

    Thread Priority Levels:
    - CRITICAL: Consequence triggered, must address immediately
    - HIGH: Time-sensitive, approaching deadline
    - MEDIUM: Important but no immediate urgency
    - LOW: Background tracking
    """

    def get_agent_id(self) -> str:
        return "plot_thread_extraction"

    def get_description(self) -> str:
        return "Extract 2-5 relevant plot threads from master"

    def gather_data(self, user_message: str, message_number: int) -> dict:
        """Gather data for plot thread extraction

        Args:
            user_message: User's message (for relevance context)
            message_number: Current message number

        Returns:
            Dict with user_message, message_number, plot_threads_master
        """
        # Read master plot threads file
        threads_file = self.rp_dir / "state" / "plot_threads_master.md"
        plot_threads_master = self._read_file_safe(threads_file, "No plot threads file found")

        return {
            "user_message": user_message,
            "message_number": message_number,
            "plot_threads_master": plot_threads_master,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt for plot thread extraction

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt for DeepSeek
        """
        prompt = f"""Extract 2-5 relevant plot threads from the master file.

USER MESSAGE (for context):
{data['user_message']}

MASTER PLOT THREADS FILE:
{data['plot_threads_master']}

Select 2-5 threads most relevant to current conversation using this priority:

1. **CRITICAL** - Consequence triggered, must address NOW
2. **HIGH** - Time-sensitive, mentioned in conversation
3. **MEDIUM** - Relevant to current topic
4. **LOW** - Monitoring but not urgent

Guidelines:
- ALWAYS load threads with consequence imminent (countdown < 10)
- Load threads mentioned in user message
- Load threads relevant to current characters/location
- Skip distant future threads (50+ responses away)
- Skip threads unrelated to current conversation
- LIMIT to 2-5 threads (be selective!)
- Note monitored threads so user knows they're tracked

Return your analysis as a JSON object:

{{
  "total_active": <total active threads>,
  "loaded": [
    {{
      "id": "THREAD-###",
      "title": "Thread title",
      "priority": "<critical|high|medium|low>",
      "last_mentioned": <response number>,
      "countdown": <responses until consequence, or null>,
      "time_sensitive": <true|false>,
      "why": "why this thread is relevant now",
      "rec": "what should happen next (if critical)"
    }}
  ],
  "monitored": [
    {{
      "id": "THREAD-###",
      "title": "brief title",
      "note": "X responses away"
    }}
  ]
}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format plot thread extraction result for JSON cache

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
                "total_active": analysis.get("total_active", 0),
                "loaded": analysis.get("loaded", []),
                "monitored": analysis.get("monitored", [])
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
def extract_plot_threads(
    rp_dir: Path,
    user_message: str,
    message_number: int,
    log_file: Optional[Path] = None
) -> str:
    """Extract relevant plot threads from master file

    Args:
        rp_dir: RP directory path
        user_message: User's message for context
        message_number: Current message number
        log_file: Optional log file

    Returns:
        Formatted plot thread extraction string
    """
    agent = PlotThreadExtractionAgent(rp_dir, log_file)
    return agent.execute(user_message, message_number)
