"""Response Analyzer Agent - Scene analysis and metadata extraction.

This agent analyzes Claude's responses to extract:
- Scene classification (type, pacing, tension)
- Characters in scene
- Location and chapter context
- Narrative variety alerts

Results are saved to timeline-specific scene_context_{session_id}.json
for other background agents to use.

Note: Time tracking is handled by TimeTrackingAgent (separate agent).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class ResponseAnalyzerAgent(BaseAgent):
    """Analyze Claude's response for scene metadata and narrative characteristics."""

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "response_analyzer"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute response analysis and update scene context.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze (from kwargs)
            **kwargs: Additional context

        Returns:
            Summary string of analysis
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping analysis")
            return "No response to analyze"

        try:
            self.log(f"Analyzing response for message #{message_number}")

            # Step 1: Get previous scene context for continuity
            previous_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

            # Step 2: Build LLM prompt with previous context
            prompt = self._build_analysis_prompt(
                user_message,
                claude_response,
                previous_context
            )

            # Step 3: Call LLM for analysis (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 4: Parse JSON response
            analysis = self.parse_json_response(response)

            if not analysis:
                self.log("Failed to parse analysis from LLM response")
                return "Analysis parsing failed"

            # Step 5: Build scene_context dict
            scene_context = self._build_scene_context(analysis, message_number)

            # Step 6: Update session state (writes to timeline-specific file)
            self.bridge.session_state_service.update_scene_context(
                self.rp_dir,
                scene_context
            )

            # Step 7: Check if response addresses any pending contradictions
            resolved_count = self._check_contradiction_resolutions(
                claude_response,
                message_number
            )

            # Step 8: Return summary
            summary = self._format_summary(analysis)
            if resolved_count > 0:
                summary += f" | Resolved {resolved_count} contradictions"
            return summary

        except Exception as e:
            self.log(f"Error in response analysis: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Analysis failed: {e}"

    def _build_analysis_prompt(
        self,
        user_message: str,
        claude_response: str,
        previous_context: dict
    ) -> str:
        """Build LLM prompt for scene analysis."""

        # Extract previous context for continuity
        prev_chapter = previous_context.get("chapter", "")
        prev_location = previous_context.get("location", "")
        prev_scenes = self._get_previous_scene_types(previous_context)

        prev_context_text = ""
        if prev_chapter or prev_location:
            prev_context_text = f"""
PREVIOUS SCENE CONTEXT:
- Chapter: {prev_chapter or "Unknown"}
- Location: {prev_location or "Unknown"}
- Recent Scene Types: {', '.join(prev_scenes) if prev_scenes else "None"}
"""

        return f"""Analyze this roleplay response and extract scene metadata and narrative characteristics.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}
{prev_context_text}

Extract the following information:

1. **Scene Classification:**
   - Type: dialogue, action, introspection, transition, world_building
   - Pacing: fast, medium, slow
   - Tension level: 1-10 (rate emotional intensity)
   - Approximate word count

2. **Characters:**
   - in_scene: Characters actively participating (speaking/acting in THIS scene)
   - mentioned: Characters referenced but not physically present
   - new_characters: Any new characters introduced

3. **Location & Chapter:**
   - Current location (be specific if mentioned, e.g., "The Rusty Anchor Tavern")
   - Has location changed from previous? (true/false)
   - Current chapter/arc (if continuing previous chapter, use same name; if new arc begins, provide descriptive name)

4. **Narrative Alerts:**
   - Scene variety: good/warning/critical (check if too many similar scene types in a row)
   - Tension flatness: true/false (is tension consistently low?)
   - Recommendations for improving variety if needed

Respond with JSON ONLY, no additional text:
{{
  "scene": {{
    "type": "dialogue",
    "pace": "medium",
    "tension": 6,
    "words": 450
  }},
  "chars": {{
    "in_scene": ["Alice", "Bob"],
    "mentioned": ["Carol"],
    "new": []
  }},
  "location": "The Rusty Anchor Tavern",
  "location_changed": true,
  "previous_location": "City Streets",
  "chapter": "Chapter 2: Secrets Revealed",
  "alerts": {{
    "variety": "good",
    "variety_msg": null,
    "tension_flat": false,
    "recommendation": null
  }}
}}

IMPORTANT:
- If chapter/location continues from previous, use the EXACT previous values
- Only mark location_changed=true if the scene clearly moves to a new place
- Only include characters who are actively in THIS scene, not just mentioned
- Use null for unknown/missing values"""

    def _get_previous_scene_types(self, previous_context: dict) -> list[str]:
        """Extract recent scene types for variety checking."""
        # Could be enhanced to track last N scene types
        # For now, just return the current scene type if available
        scene_analysis = previous_context.get("scene_analysis", {})
        scene_type = scene_analysis.get("type")
        return [scene_type] if scene_type else []

    def _build_scene_context(self, analysis: dict, message_number: int) -> dict:
        """Build scene_context dict from LLM analysis.

        Note: Time tracking is handled by TimeTrackingAgent, not here.
        This prevents race conditions when both agents update scene_context.
        """
        return {
            "chapter": analysis.get("chapter", ""),
            "location": analysis.get("location", "Unknown"),
            "characters_in_scene": analysis.get("chars", {}).get("in_scene", []),
            "last_updated_message": message_number,
            "scene_analysis": {
                "type": analysis.get("scene", {}).get("type", "unknown"),
                "pace": analysis.get("scene", {}).get("pace", "medium"),
                "tension": analysis.get("scene", {}).get("tension", 5),
                "word_count": analysis.get("scene", {}).get("words", 0)
            },
            "previous_location": analysis.get("previous_location"),
            "alerts": analysis.get("alerts", {})
        }

    def _format_summary(self, analysis: dict) -> str:
        """Format analysis result as summary string."""
        scene_type = analysis.get("scene", {}).get("type", "unknown")
        location = analysis.get("location", "unknown")
        char_count = len(analysis.get("chars", {}).get("in_scene", []))
        tension = analysis.get("scene", {}).get("tension", "?")

        return f"Scene: {scene_type} at {location} ({char_count} chars, tension {tension}/10)"

    # ==========================================================================
    # Contradiction Resolution Checking
    # ==========================================================================

    def _check_contradiction_resolutions(
        self,
        claude_response: str,
        message_number: int
    ) -> int:
        """Check if Claude's response addresses any pending contradictions.

        If a contradiction is narratively resolved (Claude explains or clarifies),
        mark it as resolved in the contradictions file.

        Args:
            claude_response: Claude's response text
            message_number: Current message number

        Returns:
            Number of contradictions marked as resolved
        """
        import json
        from datetime import datetime

        # Get session ID
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
        session_id = session_state.get("timeline", {}).get("current_session_id", "main")

        # Load contradictions file
        contradictions_file = self.rp_dir / "state" / "contradictions" / f"contradictions_{session_id}.json"

        if not contradictions_file.exists():
            return 0  # No contradictions file yet

        try:
            with open(contradictions_file, "r", encoding="utf-8") as f:
                contradictions_data = json.load(f)
        except Exception as e:
            self.log(f"Failed to load contradictions file: {e}")
            return 0

        all_contradictions = contradictions_data.get("contradictions", [])
        resolved_count = 0
        file_modified = False

        for contradiction in all_contradictions:
            if contradiction["status"] != "pending":
                continue  # Skip already resolved/dismissed

            # Check if this contradiction was addressed in the response
            if self._contradiction_addressed(contradiction, claude_response):
                # Mark as resolved
                contradiction["status"] = "resolved"
                contradiction["resolved_at"] = datetime.now().isoformat()
                contradiction["resolved_by"] = "response_analyzer"
                contradiction["resolved_reason"] = f"Addressed in Claude's response (message {message_number})"
                resolved_count += 1
                file_modified = True

                self.log(f"Marked contradiction as resolved: {contradiction['id']}")

        # Save updated contradictions file if modified
        if file_modified:
            # Update stats
            contradictions_data["stats"]["pending"] = sum(
                1 for c in all_contradictions if c["status"] == "pending"
            )
            contradictions_data["stats"]["resolved"] = sum(
                1 for c in all_contradictions if c["status"] == "resolved"
            )
            contradictions_data["last_updated"] = datetime.now().isoformat()

            try:
                with open(contradictions_file, "w", encoding="utf-8") as f:
                    json.dump(contradictions_data, f, indent=2, ensure_ascii=False)
                self.log(f"Updated contradictions file: {resolved_count} marked as resolved")
            except Exception as e:
                self.log(f"Failed to save updated contradictions file: {e}")

        return resolved_count

    def _contradiction_addressed(
        self,
        contradiction: dict,
        claude_response: str
    ) -> bool:
        """Check if a contradiction was addressed in Claude's response.

        Simple keyword matching for now. Could be enhanced with LLM analysis.

        Args:
            contradiction: Contradiction dict
            claude_response: Claude's response text

        Returns:
            True if contradiction appears to be addressed
        """
        # Get key terms from contradiction
        description = contradiction.get("description", "").lower()
        contradicting_statement = contradiction.get("contradicting_statement", "").lower()

        # Extract key phrases (simple approach)
        # Look for key words from the contradiction in Claude's response
        response_lower = claude_response.lower()

        # If the chosen explanation is mentioned in the response, consider it addressed
        explanations = contradiction.get("explanations", [])
        for exp in explanations:
            if exp.get("chosen", False):
                explanation_text = exp.get("explanation", "").lower()
                # Check if significant words from explanation appear in response
                explanation_words = set(explanation_text.split())
                # Filter out common words
                meaningful_words = {
                    w for w in explanation_words
                    if len(w) > 4 and w not in {"about", "could", "would", "should", "might", "because", "therefore"}
                }

                # Check if at least 2 meaningful words from explanation appear in response
                matches = sum(1 for word in meaningful_words if word in response_lower)
                if matches >= 2:
                    return True

        return False


__all__ = ["ResponseAnalyzerAgent"]
