"""Time Tracking Agent - Two-stage time tracking with recommendation + LLM review.

This agent tracks time passage using a two-stage approach:
1. Stage 1 (Recommendation): Generate time estimate using timing_reference.json
2. Stage 2 (LLM Review): LLM reviews recommendation and makes final decision

This provides structured guidance while allowing context-aware adjustments.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class TimeTrackingAgent(BaseAgent):
    """Track time passage with two-stage recommendation + review system.

    Fixes the "days until" calculation bug (Saturday to Tuesday = 2 days, not 3).
    Provides accurate timestamps for memories and events.
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "time_tracking"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute two-stage time tracking.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze
            **kwargs: Additional context

        Returns:
            Summary string of time tracking result
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping time tracking")
            return "No response to analyze"

        try:
            self.log(f"Tracking time for message #{message_number}")

            # Step 1: Load timing reference data
            timing_ref = self._load_timing_reference()

            # Step 2: Get current time state from session
            current_time = self._get_current_time_state()

            # Step 3: STAGE 1 - Generate recommendation using timing reference
            recommendation = self._generate_time_recommendation(
                claude_response,
                timing_ref
            )

            # Step 4: STAGE 2 - LLM reviews and makes final decision
            final_decision = self._llm_review_recommendation(
                claude_response,
                recommendation,
                current_time
            )

            # Step 5: Calculate new datetime
            new_datetime = self._add_time(
                current_time.get('current_datetime', current_time.get('start_datetime', {})),
                final_decision['final_minutes']
            )

            # Step 6: Calculate total elapsed
            start_datetime = current_time.get('start_datetime', new_datetime)
            total_elapsed = self._calculate_total_elapsed(new_datetime, start_datetime)

            # Step 7: Build time_context
            time_context = self._build_time_context(
                new_datetime,
                final_decision,
                recommendation,
                total_elapsed,
                message_number,
                start_datetime
            )

            # Step 8: Update session state
            self._update_time_context(time_context)

            # Step 9: Return summary
            return self._format_summary(final_decision, new_datetime)

        except Exception as e:
            self.log(f"Error in time tracking: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Time tracking failed: {e}"

    # ==========================================================================
    # Stage 1: Generate Recommendation
    # ==========================================================================

    def _generate_time_recommendation(
        self,
        claude_response: str,
        timing_ref: dict
    ) -> dict:
        """Generate time recommendation using timing reference as guidance.

        Args:
            claude_response: Claude's response to analyze
            timing_ref: Timing reference data from JSON

        Returns:
            Recommendation dict with activities and estimated duration
        """
        prompt = self._build_recommendation_prompt(claude_response, timing_ref)

        # Call LLM for recommendation (temperature=0.0 for consistency)
        response = self.call_llm(user_message=prompt, temperature=0.0)

        # Parse JSON response
        recommendation = self.parse_json_response(response)

        if not recommendation:
            self.log("Failed to parse recommendation from LLM")
            # Return default recommendation
            return {
                "activities_detected": [],
                "unknown_activities": [],
                "parallel": False,
                "recommended_minutes": 10,  # Default minimal passage
                "reasoning": "Failed to parse LLM response, using default",
                "explicit_time_mentioned": None
            }

        return recommendation

    def _build_recommendation_prompt(
        self,
        claude_response: str,
        timing_ref: dict
    ) -> str:
        """Build LLM prompt for Stage 1 recommendation generation."""

        activities_json = json.dumps(timing_ref.get('activities', {}), indent=2)
        modifiers_json = json.dumps(timing_ref.get('modifiers', {}), indent=2)

        return f"""Analyze this roleplay response and identify activities with time estimates.

CLAUDE'S RESPONSE:
{claude_response}

TIMING REFERENCE (base durations in minutes):
{activities_json}

MODIFIERS:
{modifiers_json}

Tasks:
1. Identify all activities in the response
2. Match activities to timing reference (use closest match if not exact)
3. Detect modifiers (fast, slow, quick, leisurely, etc.)
4. Determine if activities are parallel or sequential
5. Note any unknown activities not in reference (e.g., making out, cuddling)
6. Check for explicit time mentions ("30 minutes later", "hours passed")

Respond with JSON ONLY:
{{
  "activities_detected": [
    {{
      "activity": "conversation",
      "base_duration": 20,
      "modifier": null,
      "confidence": "high"
    }}
  ],
  "unknown_activities": [],
  "parallel": false,
  "recommended_minutes": 20,
  "reasoning": "One standard conversation detected",
  "explicit_time_mentioned": null
}}

IMPORTANT:
- Use "unknown" for activities not in timing reference (list them in unknown_activities)
- confidence: "high" (clear match), "medium" (implied), "low" (guess)
- If explicit time mentioned ("2 hours later"), note it in explicit_time_mentioned
- For parallel activities (e.g., "while eating, they talked"), set parallel=true
- If parallel, recommended_minutes should be MAX duration, not SUM"""

    # ==========================================================================
    # Stage 2: LLM Review & Final Decision
    # ==========================================================================

    def _llm_review_recommendation(
        self,
        claude_response: str,
        recommendation: dict,
        current_time: dict
    ) -> dict:
        """LLM reviews recommendation and makes final decision with reasoning.

        Args:
            claude_response: Claude's response (full context)
            recommendation: Stage 1 recommendation
            current_time: Current time state

        Returns:
            Final decision dict with accepted/adjusted time and reasoning
        """
        prompt = self._build_review_prompt(claude_response, recommendation, current_time)

        # Call LLM for review (temperature=0.3 for context-aware but consistent decisions)
        response = self.call_llm(user_message=prompt, temperature=0.3)

        # Parse JSON response
        final_decision = self.parse_json_response(response)

        if not final_decision:
            self.log("Failed to parse final decision from LLM")
            # Fall back to recommendation
            return {
                "accepted": True,
                "final_minutes": recommendation.get('recommended_minutes', 10),
                "reasoning": "Failed to parse LLM review, using recommendation as-is",
                "adjustments": None
            }

        return final_decision

    def _build_review_prompt(
        self,
        claude_response: str,
        recommendation: dict,
        current_time: dict
    ) -> str:
        """Build LLM prompt for Stage 2 review."""

        recommendation_json = json.dumps(recommendation, indent=2)
        current_dt = current_time.get('current_datetime', current_time.get('start_datetime', {}))
        current_formatted = current_dt.get('formatted', 'Unknown')

        return f"""Review this time recommendation and make the final decision.

CLAUDE'S RESPONSE:
{claude_response}

RECOMMENDATION (Stage 1):
{recommendation_json}

CURRENT IN-WORLD TIME:
{current_formatted}

Your task:
1. Review the recommendation and its reasoning
2. Decide whether to ACCEPT or ADJUST the timing
3. If UNKNOWN activities detected, estimate duration by combining similar activities from the reference
4. Consider scene context:
   - Emotional intensity (argument = longer than casual chat)
   - Time hints ("for hours", "briefly", "all night")
   - Activity combinations (making out = intimacy similar to brief date/sex)
5. Provide clear reasoning for your decision

Examples of adjustments:
- Unknown activity "making out" → estimate 15-30 min (brief intimacy)
- "talked for hours" → adjust from 20 min to 120+ min
- Parallel activities incorrectly summed → use MAX not SUM
- Explicit time mentioned ("3 hours later") → use that as authoritative

Respond with JSON ONLY:
{{
  "accepted": true,
  "final_minutes": 30,
  "reasoning": "Accepted - recommendation appropriate. Two sequential activities with realistic durations.",
  "adjustments": null
}}

OR (if adjusting):
{{
  "accepted": false,
  "final_minutes": 120,
  "reasoning": "Adjusted - scene indicates extended conversation ('talked for hours'), not brief chat",
  "adjustments": "Increased from 20 minutes to 120 minutes based on contextual clues"
}}

IMPORTANT:
- Always provide clear reasoning
- If explicit_time_mentioned in recommendation, use that as authoritative
- Be conservative - prefer shorter durations unless clear evidence for longer
- Unknown activities: estimate based on similar activities in reference"""

    # ==========================================================================
    # Time Calculations
    # ==========================================================================

    def _add_time(self, current_datetime: dict, minutes: int) -> dict:
        """Add minutes to current datetime and return new datetime.

        Uses Python datetime for accurate arithmetic (handles month/year boundaries).

        Args:
            current_datetime: Current datetime dict
            minutes: Minutes to add

        Returns:
            New datetime dict
        """
        if not current_datetime:
            # Fallback to current real-world time if no datetime provided
            now = datetime.now()
            current_datetime = {
                'year': now.year,
                'month': now.month,
                'day': now.day,
                'hour': 9,
                'minute': 0
            }

        dt = datetime(
            current_datetime['year'],
            current_datetime['month'],
            current_datetime['day'],
            current_datetime['hour'],
            current_datetime['minute']
        )

        new_dt = dt + timedelta(minutes=minutes)

        return {
            'year': new_dt.year,
            'month': new_dt.month,
            'day': new_dt.day,
            'hour': new_dt.hour,
            'minute': new_dt.minute,
            'day_of_week': new_dt.strftime('%A'),
            'formatted': new_dt.strftime('%A, %B %d, %Y %I:%M %p')
        }

    def _calculate_total_elapsed(
        self,
        current_datetime: dict,
        start_datetime: dict
    ) -> dict:
        """Calculate total elapsed time since RP start.

        This is ELAPSED days (different from "days until").

        Args:
            current_datetime: Current date/time
            start_datetime: RP start date/time

        Returns:
            Dict with days, hours, minutes, formatted
        """
        current = datetime(
            current_datetime['year'],
            current_datetime['month'],
            current_datetime['day'],
            current_datetime['hour'],
            current_datetime['minute']
        )

        start = datetime(
            start_datetime['year'],
            start_datetime['month'],
            start_datetime['day'],
            start_datetime['hour'],
            start_datetime['minute']
        )

        delta = current - start

        total_minutes = int(delta.total_seconds() / 60)
        total_hours = total_minutes // 60
        total_days = total_hours // 24

        return {
            'days': total_days,
            'hours': total_hours,
            'minutes': total_minutes,
            'formatted': f"{total_days} days, {total_hours % 24} hours elapsed since RP start"
        }

    def days_until(self, current_date: dict, future_date: dict) -> int:
        """Calculate intermediate days (not counting today or arrival day).

        CRITICAL FIX for "Saturday to Tuesday = 3 days" bug.

        Correct calculation:
        - Saturday: day 0 (NOT counted)
        - Sunday: day 1
        - Monday: day 2
        - Tuesday: arrival (NOT counted)
        Result: 2 days

        Args:
            current_date: Current date dict
            future_date: Future date dict

        Returns:
            Number of intermediate days
        """
        current = date(
            current_date['year'],
            current_date['month'],
            current_date['day']
        )
        future = date(
            future_date['year'],
            future_date['month'],
            future_date['day']
        )

        elapsed = (future - current).days
        intermediate = elapsed - 1  # Subtract 1 to exclude arrival day

        return max(0, intermediate)

    # ==========================================================================
    # State Management
    # ==========================================================================

    def _get_current_time_state(self) -> dict:
        """Get current time state from scene_context or initialize default.

        Returns:
            Time state dict with current_datetime and start_datetime
        """
        scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)
        time_ctx = scene_context.get('time_context', {})

        # If no time_context or missing current_datetime, initialize
        if not time_ctx or 'current_datetime' not in time_ctx:
            return self._initialize_time_state()

        return time_ctx

    def _initialize_time_state(self) -> dict:
        """Initialize time state from session config or default.

        Checks session.json for time_config.start_datetime.
        Falls back to current real-world date if not configured.

        Returns:
            Initial time state dict
        """
        # Try to load from session.json
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
        time_config = session_state.get('time_config', {})
        start_dt_config = time_config.get('start_datetime')

        if start_dt_config:
            # Use configured start date
            self.log("Using configured start_datetime from session.json")
            start_dt = start_dt_config
        else:
            # Default to current date/time
            self.log("No start_datetime configured, using current date as default")
            now = datetime.now()
            start_dt = {
                'year': now.year,
                'month': now.month,
                'day': now.day,
                'hour': 9,  # Default to 9 AM
                'minute': 0,
                'day_of_week': now.strftime('%A'),
                'formatted': now.strftime('%A, %B %d, %Y 9:00 AM')
            }

        return {
            'current_datetime': start_dt.copy(),
            'start_datetime': start_dt
        }

    def _build_time_context(
        self,
        new_datetime: dict,
        final_decision: dict,
        recommendation: dict,
        total_elapsed: dict,
        message_number: int,
        start_datetime: dict
    ) -> dict:
        """Build time_context dict for session state.

        Args:
            new_datetime: New current datetime
            final_decision: Final decision from Stage 2
            recommendation: Recommendation from Stage 1
            total_elapsed: Total elapsed time dict
            message_number: Current message number
            start_datetime: RP start datetime

        Returns:
            time_context dict
        """
        return {
            'current_datetime': new_datetime,
            'elapsed_this_scene': {
                'minutes': final_decision['final_minutes'],
                'formatted': self._format_minutes(final_decision['final_minutes'])
            },
            'total_elapsed': total_elapsed,
            'last_decision': {
                'recommendation': recommendation,
                'final': final_decision,
                'message_number': message_number
            },
            'start_datetime': start_datetime,
            'last_updated_message': message_number
        }

    def _update_time_context(self, time_context: dict) -> None:
        """Update time_context in scene_context (merge, don't replace).

        Args:
            time_context: New time_context dict
        """
        # Get current scene_context
        scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

        # Update only time_context section
        scene_context['time_context'] = time_context

        # Write back to file
        self.bridge.session_state_service.update_scene_context(
            self.rp_dir,
            scene_context
        )

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def _load_timing_reference(self) -> dict:
        """Load timing_reference.json from config folder.

        Returns:
            Timing reference dict with activities and modifiers
        """
        timing_ref_path = self.rp_dir / "config" / "timing_reference.json"

        if not timing_ref_path.exists():
            self.log("timing_reference.json not found, using empty reference")
            return {"activities": {}, "modifiers": {}}

        try:
            with open(timing_ref_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.log(f"Loaded timing reference with {len(data.get('activities', {}))} activities")
                return data
        except Exception as e:
            self.log(f"Failed to load timing reference: {e}")
            return {"activities": {}, "modifiers": {}}

    def _format_minutes(self, minutes: int) -> str:
        """Format minutes into human-readable string.

        Args:
            minutes: Total minutes

        Returns:
            Formatted string (e.g., "2 hours, 30 minutes")
        """
        if minutes < 60:
            return f"{minutes} minutes"

        hours = minutes // 60
        remaining_mins = minutes % 60

        if remaining_mins == 0:
            return f"{hours} hours"

        return f"{hours} hours, {remaining_mins} minutes"

    def _format_summary(self, final_decision: dict, new_datetime: dict) -> str:
        """Format time tracking result as summary string.

        Args:
            final_decision: Final decision from Stage 2
            new_datetime: New current datetime

        Returns:
            Summary string
        """
        accepted = final_decision.get('accepted', True)
        final_minutes = final_decision.get('final_minutes', 0)
        reasoning = final_decision.get('reasoning', 'No reasoning provided')

        status = "Accepted" if accepted else "Adjusted"
        time_formatted = self._format_minutes(final_minutes)
        new_time = new_datetime.get('formatted', 'Unknown')

        return f"Time tracking: {status} - {time_formatted} elapsed. New time: {new_time}. {reasoning}"


__all__ = ["TimeTrackingAgent"]
