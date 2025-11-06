"""Contradiction Synthesis Agent - Detect and explain narrative inconsistencies.

This background agent runs during chapter compression to review the entire chapter
for contradictions, synthesize plausible explanations, and generate resolution actions
for other agents to apply.

Unlike traditional error detection, this agent turns apparent contradictions into
world-building opportunities by explaining WHY they happened.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class ContradictionSynthesisAgent(BaseAgent):
    """Analyze chapters for contradictions and synthesize explanations.

    This agent:
    1. Runs during chapter compression (async, no latency impact)
    2. Reviews entire chapter for narrative consistency
    3. Identifies apparent contradictions
    4. Generates 3-5 plausible explanations for each
    5. Recommends resolution actions for other agents
    6. Saves to contradictions tracking file

    Example contradiction:
    - Rule: "All magic requires verbal incantations"
    - Observation: "Alice cast spell silently"
    - Explanations: [powerful, mute, artifact, advanced skill]
    - Action: Add knowledge entry explaining chosen explanation
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "contradiction_synthesis"

    def execute(
        self,
        chapter_number: int,
        message_range: tuple[int, int],
        **kwargs
    ) -> str:
        """Analyze chapter for contradictions and synthesize explanations.

        Args:
            chapter_number: Chapter number being compressed
            message_range: (start_message, end_message) tuple
            **kwargs: Additional context (session_id, etc.)

        Returns:
            Summary of contradictions detected and actions generated
        """
        try:
            session_id = kwargs.get("session_id", "main")
            self.log(f"Analyzing chapter {chapter_number} for contradictions (messages {message_range[0]}-{message_range[1]})")

            # Step 1: Load chapter context
            chapter_context = self._load_chapter_context(
                chapter_number=chapter_number,
                message_range=message_range,
                session_id=session_id
            )

            if not chapter_context["chapter_content"]:
                self.log("No chapter content found, skipping analysis")
                return "No chapter content to analyze"

            # Step 2: Load supporting context
            supporting_context = self._load_supporting_context(
                characters=chapter_context.get("characters", []),
                session_id=session_id
            )

            # Step 3: Build LLM prompt for contradiction detection
            prompt = self._build_analysis_prompt(chapter_context, supporting_context)

            # Step 4: Call LLM for analysis (temperature=0.0 for consistency)
            self.log("Calling LLM for contradiction analysis...")
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 5: Parse JSON response
            result = self.parse_json_response(response)

            if not result or "contradictions" not in result:
                self.log("Failed to parse contradictions from LLM")
                return "Analysis complete, no contradictions detected"

            contradictions = result.get("contradictions", [])

            if not contradictions:
                self.log("No contradictions detected in chapter")
                return f"Chapter {chapter_number}: No contradictions detected (consistency score: {result.get('narrative_consistency_score', 'N/A')})"

            self.log(f"Detected {len(contradictions)} contradictions")

            # Step 6: Generate resolution actions
            enriched_contradictions = self._generate_resolution_actions(contradictions, chapter_number, message_range)

            # Step 7: Save to contradictions tracking file
            self._save_contradictions(
                contradictions=enriched_contradictions,
                chapter_number=chapter_number,
                session_id=session_id,
                consistency_score=result.get("narrative_consistency_score", 0),
                notes=result.get("notes", "")
            )

            summary = f"Chapter {chapter_number}: Detected {len(contradictions)} contradictions, generated {sum(len(c['resolution_actions']) for c in enriched_contradictions)} resolution actions"
            self.log(summary)
            return summary

        except Exception as e:
            self.log(f"Error in contradiction synthesis: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Error analyzing chapter: {e}"

    # ==========================================================================
    # Chapter Context Loading
    # ==========================================================================

    def _load_chapter_context(
        self,
        chapter_number: int,
        message_range: tuple[int, int],
        session_id: str
    ) -> dict[str, Any]:
        """Load full chapter content and metadata from session file.

        Args:
            chapter_number: Chapter number
            message_range: (start_message, end_message)
            session_id: Current session ID

        Returns:
            Dict with chapter_content, characters, locations, messages_data, etc.
        """
        self.log(f"Loading chapter {chapter_number} context (messages {message_range[0]}-{message_range[1]})")

        # Load session file
        session_file = self.rp_dir / "sessions" / f"session_{session_id}.json"

        if not session_file.exists():
            self.log(f"Session file not found: {session_file}")
            return {
                "chapter_number": chapter_number,
                "message_range": message_range,
                "chapter_title": f"Chapter {chapter_number}",
                "chapter_content": "",
                "characters": set(),
                "locations": set(),
                "messages_data": []
            }

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except Exception as e:
            self.log(f"Failed to load session file: {e}")
            return {
                "chapter_number": chapter_number,
                "message_range": message_range,
                "chapter_title": f"Chapter {chapter_number}",
                "chapter_content": "",
                "characters": set(),
                "locations": set(),
                "messages_data": []
            }

        # Filter messages by chapter or message range
        all_messages = session_data.get("messages", [])
        chapter_messages = []
        characters = set()
        locations = set()

        for msg in all_messages:
            msg_num = msg.get("response_num", msg.get("message_number", 0))
            msg_chapter = msg.get("chapter", 0)

            # Include if in chapter or message range
            if msg_chapter == chapter_number or (message_range[0] <= msg_num <= message_range[1]):
                chapter_messages.append(msg)

                # Extract characters and locations from scene context
                scene_ctx = msg.get("agent_data_background", {}).get("scene_context_snapshot", {})
                if not scene_ctx:
                    scene_ctx = msg.get("scene_context_snapshot", {})

                chars_in_scene = scene_ctx.get("characters_in_scene", [])
                location = scene_ctx.get("location", "")

                characters.update(chars_in_scene)
                if location and location != "Unknown":
                    locations.add(location)

        # Build chapter content text (for LLM analysis)
        chapter_content_parts = []
        for msg in chapter_messages:
            msg_num = msg.get("response_num", msg.get("message_number", 0))
            user_msg = msg.get("user_message", "")
            claude_response = msg.get("assistant_response", msg.get("claude_response", ""))

            chapter_content_parts.append(f"**Message {msg_num}:**")
            chapter_content_parts.append(f"User: {user_msg}")
            chapter_content_parts.append(f"Claude: {claude_response}")
            chapter_content_parts.append("")  # Blank line

        chapter_content = "\n".join(chapter_content_parts)

        self.log(f"Loaded {len(chapter_messages)} messages for chapter {chapter_number}")
        self.log(f"Found {len(characters)} characters, {len(locations)} locations")

        return {
            "chapter_number": chapter_number,
            "message_range": message_range,
            "chapter_title": f"Chapter {chapter_number}",
            "chapter_content": chapter_content,
            "characters": list(characters),
            "locations": list(locations),
            "messages_data": chapter_messages,  # Full message objects for detailed referencing
            "session_file": str(session_file)
        }

    def _load_supporting_context(
        self,
        characters: list[str],
        session_id: str
    ) -> dict[str, Any]:
        """Load knowledge base, memories, and entity profiles.

        Args:
            characters: List of character names in chapter
            session_id: Current session ID

        Returns:
            Dict with knowledge_base, character_profiles, etc.
        """
        supporting = {
            "knowledge_base": [],
            "character_profiles": {},
            "plot_threads": []
        }

        # Load knowledge base
        try:
            knowledge_file = self.rp_dir / f"state/knowledge_{session_id}.json"
            if knowledge_file.exists():
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    knowledge_data = json.load(f)
                    supporting["knowledge_base"] = knowledge_data.get("entries", [])
                    self.log(f"Loaded {len(supporting['knowledge_base'])} knowledge entries")
        except Exception as e:
            self.log(f"Failed to load knowledge base: {e}")

        # Load character profiles (basics + abilities)
        for character in characters:
            try:
                from src.domain.entities import FixtureEntityRepository
                repository = FixtureEntityRepository(
                    rp_dir=self.rp_dir,
                    session_state_service=self.bridge.session_state_service if self.bridge else None
                )
                character_entity = repository.get_character(character)
                supporting["character_profiles"][character] = {
                    "basics": dict(character_entity.basics),
                    "abilities": dict(character_entity.abilities),
                    "personality": dict(character_entity.personality)
                }
                self.log(f"Loaded profile for {character}")
            except Exception as e:
                self.log(f"Failed to load profile for {character}: {e}")

        # Load plot threads
        try:
            threads_file = self.rp_dir / f"state/plot_threads_{session_id}.json"
            if threads_file.exists():
                with open(threads_file, "r", encoding="utf-8") as f:
                    threads_data = json.load(f)
                    supporting["plot_threads"] = threads_data.get("threads", [])
                    self.log(f"Loaded {len(supporting['plot_threads'])} plot threads")
        except Exception as e:
            self.log(f"Failed to load plot threads: {e}")

        return supporting

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_analysis_prompt(
        self,
        chapter_context: dict[str, Any],
        supporting_context: dict[str, Any]
    ) -> str:
        """Build LLM prompt for contradiction detection and explanation synthesis.

        Args:
            chapter_context: Chapter content and metadata
            supporting_context: Knowledge base, profiles, etc.

        Returns:
            Formatted prompt string
        """
        # Format knowledge base
        knowledge_text = ""
        if supporting_context["knowledge_base"]:
            knowledge_text = "ESTABLISHED KNOWLEDGE:\n"
            for entry in supporting_context["knowledge_base"][:20]:  # Limit to recent 20
                category = entry.get("category", "general")
                fact = entry.get("fact", "")
                knowledge_text += f"- [{category}] {fact}\n"
        else:
            knowledge_text = "ESTABLISHED KNOWLEDGE:\nNo knowledge base entries yet.\n"

        # Format character profiles
        profiles_text = ""
        if supporting_context["character_profiles"]:
            profiles_text = "CHARACTER PROFILES:\n"
            for name, profile in supporting_context["character_profiles"].items():
                profiles_text += f"\n**{name}:**\n"
                basics = profile.get("basics", {})
                abilities = profile.get("abilities", {})
                if basics:
                    profiles_text += f"  Basics: {self._dict_preview(basics)}\n"
                if abilities:
                    profiles_text += f"  Abilities: {self._dict_preview(abilities)}\n"
        else:
            profiles_text = "CHARACTER PROFILES:\nNo character profiles loaded.\n"

        return f"""Review this chapter for narrative consistency and synthesize explanations for apparent contradictions.

CHAPTER SUMMARY:
Chapter {chapter_context['chapter_number']}: {chapter_context['chapter_title']}
Messages: {chapter_context['message_range'][0]} - {chapter_context['message_range'][1]}
Characters: {', '.join(chapter_context.get('characters', []))}

CHAPTER CONTENT:
{chapter_context['chapter_content']}

{knowledge_text}

{profiles_text}

TASK:
1. Identify any apparent contradictions:
   - World rules violated
   - Character behavior inconsistencies
   - Timeline issues
   - Contradictions with established facts

2. For each contradiction, generate 3-5 plausible explanations
   - Focus on narrative opportunities, not just "errors"
   - Consider character growth, hidden abilities, world complexity
   - Assess plausibility (high, medium, low)

3. Recommend resolution actions:
   - Should this be added to knowledge base?
   - Should character profile be updated?
   - Should this be left as intentional mystery?

IGNORE:
- Intentional character growth/development
- Deliberate plot mysteries/reveals
- Different character perspectives
- Minor stylistic inconsistencies

Respond with JSON ONLY:
{{
  "contradictions": [
    {{
      "type": "world_rule",
      "description": "Brief description of contradiction",
      "established_rule": "What was previously established",
      "contradicting_statement": "What contradicts it",
      "chapter_reference": "Where it appears",
      "explanations": [
        {{
          "explanation": "Plausible explanation text",
          "plausibility": "high",
          "narrative_impact": "How this enriches the story",
          "supporting_evidence": "Evidence from chapter/profiles"
        }}
      ],
      "recommended_action": "clarify_in_knowledge",
      "suggested_knowledge_entry": "Proposed knowledge base entry"
    }}
  ],
  "narrative_consistency_score": 8.5,
  "notes": "Overall assessment of chapter consistency"
}}

CONTRADICTION TYPES: "world_rule", "character_behavior", "timeline", "established_fact"
RECOMMENDED ACTIONS: "clarify_in_knowledge", "update_character_profile", "leave_as_mystery", "no_action_needed"
"""

    def _dict_preview(self, data: dict, max_items: int = 3) -> str:
        """Create brief preview of dict contents."""
        if not data:
            return "None"

        items = list(data.items())[:max_items]
        preview = ", ".join(f"{k}: {str(v)[:50]}" for k, v in items)

        if len(data) > max_items:
            preview += f", ... (+{len(data) - max_items} more)"

        return preview

    # ==========================================================================
    # Resolution Actions
    # ==========================================================================

    def _generate_resolution_actions(
        self,
        contradictions: list[dict[str, Any]],
        chapter_number: int,
        message_range: tuple[int, int]
    ) -> list[dict[str, Any]]:
        """Generate resolution actions for other agents to apply.

        Args:
            contradictions: List of contradiction dicts from LLM
            chapter_number: Chapter number
            message_range: Message range

        Returns:
            Enriched contradictions with resolution_actions field
        """
        enriched = []

        for contr in contradictions:
            # Generate unique ID
            contr_id = f"contr_{uuid4().hex[:8]}"

            # Choose first explanation as default (highest plausibility)
            explanations = contr.get("explanations", [])
            if explanations:
                explanations[0]["chosen"] = True
                for exp in explanations[1:]:
                    exp["chosen"] = False

            # Build resolution actions based on recommended_action
            actions = []
            recommended = contr.get("recommended_action", "no_action_needed")

            if recommended == "clarify_in_knowledge":
                actions.append({
                    "agent": "knowledge_extraction",
                    "action": "add_entry",
                    "target_file": "state/knowledge_{session_id}.json",
                    "data": {
                        "category": "world_rule",  # Will be determined by agent
                        "fact": contr.get("suggested_knowledge_entry", ""),
                        "details": "",
                        "confidence": 0.9,
                        "tags": ["contradiction_resolution"],
                        "source": "contradiction_synthesis",
                        "contradiction_id": contr_id,
                    },
                    "completed": False,
                    "pending": True
                })

            elif recommended == "update_character_profile":
                # TODO: Extract character name from contradiction
                actions.append({
                    "agent": "entity_update",
                    "action": "update_abilities",
                    "target": "entities/{character}.json",
                    "content": "Update based on contradiction explanation",
                    "completed": False,
                    "pending": True
                })

            # Build enriched contradiction
            enriched_contr = {
                "id": contr_id,
                "status": "pending",
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "chapter": chapter_number,
                "message_range": list(message_range),
                "type": contr.get("type", "unknown"),
                "description": contr.get("description", ""),
                "established_rule": contr.get("established_rule", ""),
                "contradicting_statement": contr.get("contradicting_statement", ""),
                "chapter_reference": contr.get("chapter_reference", ""),
                "explanations": explanations,
                "resolution_actions": actions,
                "resolved_at": None,
                "resolved_by": None
            }

            enriched.append(enriched_contr)

        return enriched

    # ==========================================================================
    # File Operations
    # ==========================================================================

    def _save_contradictions(
        self,
        contradictions: list[dict[str, Any]],
        chapter_number: int,
        session_id: str,
        consistency_score: float,
        notes: str
    ) -> None:
        """Save contradictions to tracking file in state/contradictions/ folder.

        Args:
            contradictions: List of enriched contradiction dicts
            chapter_number: Chapter number
            session_id: Session ID
            consistency_score: Narrative consistency score (0-10)
            notes: Overall assessment notes
        """
        # Use state/contradictions/ folder
        contradictions_file = self.rp_dir / "state" / "contradictions" / f"contradictions_{session_id}.json"

        # Load existing contradictions
        existing_data = {"contradictions": []}
        if contradictions_file.exists():
            try:
                with open(contradictions_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception as e:
                self.log(f"Failed to load existing contradictions: {e}")

        # Append new contradictions
        existing_data["contradictions"].extend(contradictions)

        # Update metadata
        existing_data["version"] = "1.0"
        existing_data["session_id"] = session_id
        existing_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Update stats
        all_contrs = existing_data["contradictions"]
        existing_data["stats"] = {
            "total": len(all_contrs),
            "pending": sum(1 for c in all_contrs if c["status"] == "pending"),
            "resolved": sum(1 for c in all_contrs if c["status"] == "resolved"),
            "dismissed": sum(1 for c in all_contrs if c["status"] == "dismissed")
        }

        # Save chapter analysis
        existing_data.setdefault("chapter_analyses", []).append({
            "chapter": chapter_number,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "contradictions_count": len(contradictions),
            "consistency_score": consistency_score,
            "notes": notes
        })

        # Write to file atomically
        temp_file = contradictions_file.with_suffix(".json.tmp")
        try:
            contradictions_file.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            temp_file.replace(contradictions_file)
            self.log(f"Saved {len(contradictions)} contradictions to {contradictions_file}")
        except Exception as e:
            self.log(f"Failed to save contradictions: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def archive_resolved_contradictions(self, session_id: str = "main") -> int:
        """Move resolved contradictions to resolved/ archive folder.

        This should be called periodically to clean up the active contradictions file.
        Resolved contradictions are moved to state/contradictions/resolved/ for historical reference.

        Args:
            session_id: Session ID to archive

        Returns:
            Number of contradictions archived
        """
        contradictions_file = self.rp_dir / "state" / "contradictions" / f"contradictions_{session_id}.json"
        resolved_archive_file = self.rp_dir / "state" / "contradictions" / "resolved" / f"resolved_{session_id}.json"

        if not contradictions_file.exists():
            self.log(f"No contradictions file to archive: {contradictions_file}")
            return 0

        # Load active contradictions
        try:
            with open(contradictions_file, "r", encoding="utf-8") as f:
                active_data = json.load(f)
        except Exception as e:
            self.log(f"Failed to load contradictions for archiving: {e}")
            return 0

        all_contradictions = active_data.get("contradictions", [])
        resolved = [c for c in all_contradictions if c["status"] == "resolved"]
        still_active = [c for c in all_contradictions if c["status"] != "resolved"]

        if not resolved:
            self.log("No resolved contradictions to archive")
            return 0

        # Load existing resolved archive
        resolved_data = {"contradictions": []}
        if resolved_archive_file.exists():
            try:
                with open(resolved_archive_file, "r", encoding="utf-8") as f:
                    resolved_data = json.load(f)
            except Exception as e:
                self.log(f"Failed to load resolved archive: {e}")

        # Append newly resolved contradictions
        resolved_data["contradictions"].extend(resolved)
        resolved_data["session_id"] = session_id
        resolved_data["last_archived"] = datetime.now(timezone.utc).isoformat()
        resolved_data["total_resolved"] = len(resolved_data["contradictions"])

        # Save resolved archive
        try:
            resolved_archive_file.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved_archive_file, "w", encoding="utf-8") as f:
                json.dump(resolved_data, f, indent=2, ensure_ascii=False)
            self.log(f"Archived {len(resolved)} resolved contradictions to {resolved_archive_file}")
        except Exception as e:
            self.log(f"Failed to save resolved archive: {e}")
            return 0

        # Update active file with only still-active contradictions
        active_data["contradictions"] = still_active
        active_data["stats"]["resolved"] = 0  # Reset resolved count
        active_data["stats"]["total"] = len(still_active)
        active_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(contradictions_file, "w", encoding="utf-8") as f:
                json.dump(active_data, f, indent=2, ensure_ascii=False)
            self.log(f"Updated active contradictions file, {len(still_active)} still pending")
        except Exception as e:
            self.log(f"Failed to update active contradictions: {e}")

        return len(resolved)


__all__ = ["ContradictionSynthesisAgent"]
