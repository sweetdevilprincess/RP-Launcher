"""Plot Thread Extraction Agent - Extract relevant plot threads for context.

This immediate agent runs BEFORE Claude responds to identify and inject
relevant active plot threads into the prompt to maintain narrative continuity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class PlotThreadExtractionAgent(BaseAgent):
    """Extract relevant plot threads for prompt context.

    This immediate agent:
    1. Loads active plot threads from the thread file
    2. Uses LLM to rank threads by relevance to user's message
    3. Returns top 3-5 most relevant threads formatted for injection
    4. Provides narrative continuity and plot awareness to Claude
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "plot_thread_extraction"

    def execute(
        self,
        user_message: str,
        message_number: int,
        **kwargs
    ) -> str:
        """Extract relevant plot threads and format for prompt injection.

        Args:
            user_message: User's message to analyze
            message_number: Current message index
            **kwargs: Additional context

        Returns:
            Formatted plot thread context for prompt injection (empty string if none)
        """
        try:
            self.log(f"Extracting relevant plot threads for message #{message_number}")

            # Step 1: Load plot threads from session state
            threads_data = self._load_plot_threads()

            if not threads_data:
                self.log("No plot threads data available")
                return ""

            # Step 2: Filter for active threads only
            active_threads = [
                thread for thread in threads_data.get("threads", [])
                if thread.get("status") == "active"
            ]

            if not active_threads:
                self.log("No active plot threads found")
                return ""

            self.log(f"Found {len(active_threads)} active plot threads")

            # Step 3: Build LLM prompt for relevance ranking
            prompt = self._build_relevance_prompt(user_message, active_threads)

            # Step 4: Call LLM for relevance ranking (temperature=0.0 for consistency)
            self.log("Calling LLM for plot thread relevance ranking...")
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 5: Parse JSON response
            result = self.parse_json_response(response)

            if not result or "relevant_threads" not in result:
                self.log("Failed to parse relevant threads from LLM")
                return ""

            relevant_threads = result.get("relevant_threads", [])

            if not relevant_threads:
                self.log("No relevant plot threads identified")
                return ""

            self.log(f"Found {len(relevant_threads)} relevant plot threads")

            # Step 6: Format for prompt injection
            formatted = self._format_for_injection(relevant_threads, active_threads)

            self.log(f"Plot thread extraction complete ({len(formatted)} characters)")
            return formatted

        except Exception as e:
            self.log(f"Error in plot thread extraction: {e}")
            import traceback
            self.log(traceback.format_exc())
            return ""  # Fail gracefully, don't block main flow

    # ==========================================================================
    # Plot Thread Loading
    # ==========================================================================

    def _load_plot_threads(self) -> dict[str, Any] | None:
        """Load plot threads from timeline-specific file.

        Returns:
            Plot threads data dict, or None if not available
        """
        try:
            # Get current session state
            session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
            thread_file = session_state.get("plot_threads", {}).get("thread_file")

            if not thread_file:
                self.log("No plot_threads pointer in session state")
                return None

            # Construct full path
            thread_path = self.rp_dir / thread_file

            # Load if exists
            if not thread_path.exists():
                self.log(f"Plot threads file not found: {thread_path}")
                return None

            with open(thread_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.log(f"Loaded {len(data.get('threads', []))} plot threads")
            return data

        except Exception as e:
            self.log(f"Failed to load plot threads: {e}")
            return None

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_relevance_prompt(
        self,
        user_message: str,
        active_threads: list[dict[str, Any]]
    ) -> str:
        """Build LLM prompt for plot thread relevance ranking.

        Args:
            user_message: User's current message
            active_threads: List of active plot threads

        Returns:
            Formatted prompt string
        """
        # Build thread context (limit to prevent token overflow)
        threads_context = ""
        display_limit = min(len(active_threads), 20)  # Max 20 threads shown

        for i, thread in enumerate(active_threads[:display_limit], 1):
            thread_id = thread.get("id", "unknown")
            title = thread.get("title", "Untitled")
            description = thread.get("description", "")
            participants = ", ".join(thread.get("participants", []))
            locations = ", ".join(thread.get("locations", []))
            priority = thread.get("priority", 5)
            tags = ", ".join(thread.get("tags", []))
            time_sensitive = thread.get("time_sensitive", False)

            # Get latest update
            updates = thread.get("updates", [])
            latest_update = updates[-1].get("progress", "No recent updates") if updates else "No updates"

            threads_context += f"\n**Thread {i}** (ID: {thread_id})\n"
            threads_context += f"Title: {title}\n"
            threads_context += f"Description: {description}\n"
            threads_context += f"Participants: {participants}\n"
            threads_context += f"Locations: {locations}\n"
            threads_context += f"Priority: {priority}/10 | Tags: {tags}\n"
            threads_context += f"Time Sensitive: {time_sensitive}\n"
            threads_context += f"Latest: {latest_update}\n"

        if len(active_threads) > display_limit:
            threads_context += f"\n(... and {len(active_threads) - display_limit} more threads)\n"

        return f"""Find the most relevant plot threads for this conversation context.

USER MESSAGE:
{user_message}

ACTIVE PLOT THREADS:
{threads_context}

Select 3-5 plot threads that are most relevant to the current user message:

**Prioritization:**
1. **DIRECT RELEVANCE** - Threads directly mentioned or related to user's message
2. **PARTICIPANT OVERLAP** - Threads involving characters/entities in the message
3. **LOCATION MATCH** - Threads taking place where the current action is
4. **TIME SENSITIVITY** - Urgent threads that need attention
5. **HIGH PRIORITY** - Important storylines (priority 7-10)
6. **RECENT ACTIVITY** - Threads updated in the last few messages

Respond with JSON ONLY:
{{
  "relevant_threads": [
    {{
      "thread_id": "{thread_id}",
      "title": "Thread title",
      "relevance_reason": "Brief explanation of why this thread is relevant now"
    }}
  ]
}}

IMPORTANT:
- Select 3-5 threads maximum (quality over quantity)
- Prioritize threads the user might be directly engaging with
- If no threads are clearly relevant, return empty array: {{"relevant_threads": []}}
- thread_id must match an active thread's id field exactly"""

    # ==========================================================================
    # Output Formatting
    # ==========================================================================

    def _format_for_injection(
        self,
        relevant_threads: list[dict[str, Any]],
        all_active_threads: list[dict[str, Any]]
    ) -> str:
        """Format relevant plot threads for prompt injection.

        Args:
            relevant_threads: List of relevant thread dicts from LLM
            all_active_threads: Complete list of active threads for lookup

        Returns:
            Formatted text for prompt injection
        """
        if not relevant_threads:
            return ""

        # Create lookup dict for thread details
        thread_lookup = {t["id"]: t for t in all_active_threads}

        # Format as markdown
        lines = ["### ACTIVE PLOT THREADS\n"]

        for relevant in relevant_threads:
            thread_id = relevant.get("thread_id")
            relevance = relevant.get("relevance_reason", "")

            # Get full thread details
            thread = thread_lookup.get(thread_id)
            if not thread:
                self.log(f"Thread {thread_id} not found in active threads")
                continue

            title = thread.get("title", "Untitled")
            description = thread.get("description", "")
            participants = ", ".join(thread.get("participants", []))
            priority = thread.get("priority", 5)

            # Get latest progress
            updates = thread.get("updates", [])
            latest = updates[-1].get("progress", "No updates") if updates else "No updates"

            lines.append(f"**[{thread_id}] {title}** (Priority: {priority}/10)")
            lines.append(f"*{description}*")
            lines.append(f"Participants: {participants}")
            lines.append(f"Latest: {latest}")
            lines.append(f"Why relevant: {relevance}")
            lines.append("")  # Blank line between threads

        return "\n".join(lines)


__all__ = ["PlotThreadExtractionAgent"]
