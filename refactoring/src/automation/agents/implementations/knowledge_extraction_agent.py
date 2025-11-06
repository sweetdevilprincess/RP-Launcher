"""Knowledge Extraction Agent - Extract world-building facts and lore.

This agent analyzes Claude's responses to extract:
- World rules (magic, physics, technology)
- History and timeline
- Culture and society
- Geography and locations
- Organizations and factions

Features:
- Multi-category support (each entry can belong to multiple categories)
- Intelligent contradiction synthesis (reconciles conflicting facts)
- Converts knowledge_base.md to JSON on first run
- Timeline-specific storage with branch inheritance
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


# =============================================================================
# Standardized Taxonomies
# =============================================================================

KNOWLEDGE_CATEGORIES = [
    # World Rules
    "magic_system",
    "technology",
    "supernatural",
    "physics_laws",

    # History & Time
    "history",
    "timeline",
    "past_events",
    "legends_myths",

    # Society & Culture
    "culture",
    "customs",
    "laws",
    "religion",
    "language",

    # Geography & Places
    "geography",
    "locations",
    "climate",

    # Organizations & Power
    "organizations",
    "factions",
    "government",
    "military",

    # Economy & Resources
    "economy",
    "trade",
    "resources",

    # Other
    "species_races",
    "lore",
    "prophecy",
    "secrets"
]

KNOWLEDGE_TAGS = [
    # Certainty
    "established_canon",
    "implied",
    "rumor",
    "uncertain",

    # Importance
    "critical",
    "important",
    "background",
    "flavor",

    # Type
    "rule",
    "fact",
    "limitation",
    "exception",
    "secret",

    # Scope
    "global",
    "regional",
    "local",
    "character_specific",

    # Story
    "plot_relevant",
    "worldbuilding",
    "backstory",
    "foreshadowing"
]


class KnowledgeExtractionAgent(BaseAgent):
    """Extract world-building facts and lore from Claude's responses.

    Uses session state from ResponseAnalyzerAgent and TimeTrackingAgent for context.
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "knowledge_extraction"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute knowledge extraction and save to knowledge file.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze
            **kwargs: Additional context

        Returns:
            Summary string of knowledge extracted
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping knowledge extraction")
            return "No response to analyze"

        try:
            self.log(f"Extracting knowledge from message #{message_number}")

            # Step 1: Convert knowledge_base.md if it exists (first run only)
            if self._should_convert_md():
                self.log("Found knowledge_base.md, converting to JSON...")
                conversion_count = self._convert_knowledge_base_md()
                self.log(f"Converted {conversion_count} entries from knowledge_base.md")

            # Step 2: Load existing knowledge
            knowledge_data = self._load_existing_knowledge()
            existing_entries = knowledge_data.get("entries", [])

            # Step 3: Get scene context from session state
            scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

            # Step 4: Extract context
            characters_in_scene = scene_context.get("characters_in_scene", [])
            location = scene_context.get("location", "Unknown")
            chapter = scene_context.get("chapter", "")

            # Step 5: Get timestamp from TimeTrackingAgent
            timestamp = self._get_timestamp_from_time_tracking(scene_context, message_number)

            # Step 6: Build LLM prompt
            prompt = self._build_knowledge_prompt(
                user_message,
                claude_response,
                existing_entries,
                characters_in_scene,
                location,
                chapter
            )

            # Step 7: Call LLM for knowledge extraction (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 8: Parse JSON response
            extraction_data = self.parse_json_response(response)

            if not extraction_data or "knowledge" not in extraction_data:
                self.log("Failed to parse knowledge from LLM response")
                return "Knowledge extraction failed"

            new_facts = extraction_data.get("knowledge", [])

            if not new_facts:
                self.log("No new knowledge found in response")
                return "No new knowledge extracted"

            # Step 9: Process each extracted fact (check contradictions, add to entries)
            added_count, updated_count = self._apply_knowledge_updates(
                knowledge_data,
                new_facts,
                location,
                chapter,
                timestamp,
                message_number,
                characters_in_scene
            )

            # Step 10: Save updated knowledge
            self._save_knowledge(knowledge_data)

            # Step 11: Check for and apply contradiction resolutions
            contradiction_resolutions = self._apply_contradiction_resolutions(
                knowledge_data,
                message_number
            )

            # Step 12: Return summary
            summary = self._format_summary(added_count, updated_count, new_facts)
            if contradiction_resolutions > 0:
                summary += f" | Applied {contradiction_resolutions} contradiction resolutions"
            return summary

        except Exception as e:
            self.log(f"Error in knowledge extraction: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Knowledge extraction failed: {e}"

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_knowledge_prompt(
        self,
        user_message: str,
        claude_response: str,
        existing_entries: list[dict],
        characters_in_scene: list[str],
        location: str,
        chapter: str
    ) -> str:
        """Build LLM prompt for knowledge extraction.

        Args:
            user_message: User's message
            claude_response: Claude's response
            existing_entries: Already extracted knowledge entries
            characters_in_scene: Characters detected in scene
            location: Current location
            chapter: Current chapter

        Returns:
            LLM prompt string
        """
        # Format existing knowledge (prevent duplicates)
        existing_text = self._format_existing_knowledge(existing_entries)

        # Build lists for prompt
        categories_str = ", ".join(KNOWLEDGE_CATEGORIES)
        tags_str = ", ".join(KNOWLEDGE_TAGS)
        characters_str = ", ".join(characters_in_scene) if characters_in_scene else "Unknown"

        return f"""Analyze this roleplay response for world-building facts and lore.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}

CURRENT SCENE:
- Chapter: {chapter if chapter else "None"}
- Location: {location}
- Characters: {characters_str}

EXISTING KNOWLEDGE (DO NOT DUPLICATE):
{existing_text}

Extract NEW world-building facts about:
1. **World Rules** - Magic, physics, technology, supernatural
2. **History** - Past events, timeline, legends
3. **Culture & Society** - Customs, laws, language, religion
4. **Geography** - Locations, terrain, climate
5. **Organizations** - Factions, governments, groups

IMPORTANT RULES:
- Only extract facts that are NEW (not already in existing knowledge)
- Facts must be explicitly stated or strongly implied
- Do NOT extract character feelings/actions (that's memories)
- Do NOT extract temporary scene details (weather, mood)
- Facts must be important for narrative consistency

**Confidence Scale:**
- 0.9-1.0: Explicitly stated as fact
- 0.7-0.9: Strongly implied
- 0.5-0.7: Inferred from context
- Below 0.5: Too uncertain, don't extract

**Categories (MUST use these):** {categories_str}
**Tags (MUST use these):** {tags_str}

**MULTIPLE CATEGORIES ALLOWED** - If fact touches multiple topics, include all relevant categories.

Example:
- "The Academy was founded after the war to regulate magic"
- Categories: ["organizations", "history", "magic_system"]

Respond with JSON ONLY:
{{
  "knowledge": [
    {{
      "categories": ["magic_system", "culture"],
      "fact": "Magic requires verbal incantations for most users",
      "details": "Standard teaching requires spoken words. Some advanced users can cast silently.",
      "confidence": 0.9,
      "tags": ["magic", "established_canon", "rule"],
      "mentioned_by": ["Professor Alice"]
    }}
  ]
}}

If no NEW knowledge found, return: {{"knowledge": []}}"""

    def _format_existing_knowledge(self, entries: list[dict]) -> str:
        """Format existing knowledge for prompt to prevent duplicates.

        Args:
            entries: List of existing knowledge entries

        Returns:
            Formatted string of existing facts
        """
        if not entries:
            return "(No existing knowledge)"

        # Show last 20 entries (most recent)
        recent_entries = entries[-20:] if len(entries) > 20 else entries

        lines = []
        for entry in recent_entries:
            categories = ", ".join(entry.get("categories", []))
            fact = entry.get("fact", "")
            lines.append(f"- [{categories}] {fact}")

        if len(entries) > 20:
            lines.insert(0, f"(Showing 20 most recent out of {len(entries)} total entries)")

        return "\n".join(lines)

    def _build_synthesis_prompt(
        self,
        existing_entry: dict,
        new_fact: str,
        new_details: str,
        new_confidence: float,
        new_message: int
    ) -> str:
        """Build LLM prompt for contradiction synthesis.

        Args:
            existing_entry: Existing knowledge entry
            new_fact: New conflicting fact
            new_details: Details of new fact
            new_confidence: Confidence of new fact
            new_message: Message number where new fact appeared

        Returns:
            LLM prompt string for synthesis
        """
        source_msg = existing_entry.get("source_message", "unknown")

        return f"""Two knowledge facts appear to contradict each other:

EXISTING FACT (Message {source_msg}, confidence {existing_entry['confidence']}):
"{existing_entry['fact']}"
Details: {existing_entry.get('details', '')}

NEW FACT (Message {new_message}, confidence {new_confidence}):
"{new_fact}"
Details: {new_details}

Reconcile these facts by finding an explanation that makes BOTH true:

Consider these possibilities:
- Different skill levels (basic vs advanced)
- Exceptions to the rule (rare cases)
- Special conditions (time, place, circumstances)
- Character-specific abilities (mutations, training)
- Context matters (different situations)
- Evolution of knowledge (old belief vs new discovery)

Examples of good synthesis:
- "Magic requires incantations normally, but advanced mages can cast silently"
- "Iron disrupts magic for most users, but doesn't affect Bob due to his unique bloodline"
- "The war happened 50 years ago according to common belief, but historical records show it was 60 years ago"

If they are TRULY irreconcilable with no reasonable explanation:
- Return can_reconcile: false
- Provide reason why they cannot be reconciled

Respond with JSON ONLY:
{{
  "can_reconcile": true,
  "synthesized_fact": "One sentence combining both facts with explanation",
  "synthesized_details": "2-3 sentences explaining how both are true",
  "synthesis_explanation": "Why this reconciliation makes sense",
  "confidence": 0.85,
  "revision_note": "Brief note about what changed"
}}

OR if irreconcilable:
{{
  "can_reconcile": false,
  "reason": "Why these facts cannot be reconciled",
  "recommendation": "mark_for_review"
}}"""

    # ==========================================================================
    # Knowledge Loading/Saving
    # ==========================================================================

    def _load_existing_knowledge(self) -> dict[str, Any]:
        """Load existing knowledge from timeline-specific file.

        Returns:
            Knowledge data dict with entries, metadata
        """
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)

        # Get knowledge file path from session state
        knowledge_file = session_state.get("knowledge", {}).get(
            "knowledge_file",
            "state/knowledge_main.json"
        )

        knowledge_path = self.rp_dir / knowledge_file

        if not knowledge_path.exists():
            # Initialize empty knowledge structure
            session_id = session_state.get("timeline", {}).get("current_session_id", "main")
            return {
                "session_id": session_id,
                "last_updated": datetime.now().isoformat(),
                "last_updated_message": 0,
                "total_entries": 0,
                "entries": [],
                "categories_index": {}
            }

        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.log(f"Loaded {len(data.get('entries', []))} knowledge entries from {knowledge_file}")
            return data
        except (json.JSONDecodeError, IOError) as e:
            self.log(f"Failed to load knowledge from {knowledge_path}: {e}")
            # Return empty structure
            session_id = session_state.get("timeline", {}).get("current_session_id", "main")
            return {
                "session_id": session_id,
                "last_updated": datetime.now().isoformat(),
                "last_updated_message": 0,
                "total_entries": 0,
                "entries": [],
                "categories_index": {}
            }

    def _save_knowledge(self, knowledge_data: dict[str, Any]) -> bool:
        """Save knowledge to timeline-specific file.

        Args:
            knowledge_data: Complete knowledge data structure

        Returns:
            True if saved successfully
        """
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)

        # Get knowledge file path from session state
        knowledge_file = session_state.get("knowledge", {}).get(
            "knowledge_file",
            "state/knowledge_main.json"
        )

        knowledge_path = self.rp_dir / knowledge_file

        # Ensure parent directory exists
        knowledge_path.parent.mkdir(parents=True, exist_ok=True)

        # Update metadata
        knowledge_data["total_entries"] = len(knowledge_data.get("entries", []))
        knowledge_data["last_updated"] = datetime.now().isoformat()

        # Rebuild category index
        knowledge_data["categories_index"] = self._build_category_index(
            knowledge_data.get("entries", [])
        )

        # Write atomically (temp file + rename)
        temp_path = knowledge_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(knowledge_path)  # Atomic on both POSIX and Windows

            self.log(f"Saved {knowledge_data['total_entries']} entries to {knowledge_file}")
            return True
        except Exception as e:
            self.log(f"Failed to save knowledge to {knowledge_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

    # ==========================================================================
    # Contradiction Resolution Integration
    # ==========================================================================

    def _apply_contradiction_resolutions(
        self,
        knowledge_data: dict[str, Any],
        message_number: int
    ) -> int:
        """Check for and apply pending contradiction resolutions.

        Reads the contradictions file and applies any pending knowledge_extraction
        actions, then marks them as completed.

        Args:
            knowledge_data: Current knowledge data (will be modified)
            message_number: Current message number

        Returns:
            Number of resolutions applied
        """
        # Get session ID from session state
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
        resolutions_applied = 0
        file_modified = False

        for contradiction in all_contradictions:
            if contradiction["status"] != "pending":
                continue  # Skip resolved/dismissed

            # Check for pending knowledge_extraction actions
            for action in contradiction.get("resolution_actions", []):
                if action.get("agent") != "knowledge_extraction":
                    continue
                if action.get("completed"):
                    continue  # Already applied

                # Apply the resolution
                if self._apply_knowledge_action(
                    knowledge_data,
                    action,
                    contradiction["id"],
                    message_number
                ):
                    action["completed"] = True
                    action["completed_at"] = datetime.now().isoformat()
                    action["completed_by_message"] = message_number
                    resolutions_applied += 1
                    file_modified = True

                    self.log(f"Applied contradiction resolution: {contradiction['id']}")

        # Save updated contradictions file if modified
        if file_modified:
            try:
                with open(contradictions_file, "w", encoding="utf-8") as f:
                    json.dump(contradictions_data, f, indent=2, ensure_ascii=False)
                self.log(f"Updated contradictions file with {resolutions_applied} completed actions")
            except Exception as e:
                self.log(f"Failed to save updated contradictions file: {e}")

            # Also save updated knowledge data
            self._save_knowledge(knowledge_data)

        return resolutions_applied

    def _apply_knowledge_action(
        self,
        knowledge_data: dict[str, Any],
        action: dict[str, Any],
        contradiction_id: str,
        message_number: int
    ) -> bool:
        """Apply a single knowledge resolution action.

        Args:
            knowledge_data: Knowledge data to modify
            action: Resolution action from contradiction
            contradiction_id: ID of the contradiction being resolved
            message_number: Current message number

        Returns:
            True if successfully applied
        """
        if action.get("action") != "add_entry":
            self.log(f"Unknown action type: {action.get('action')}")
            return False

        # Extract data from action
        action_data = action.get("data", {})
        if not action_data:
            self.log(f"No data in action for contradiction {contradiction_id}")
            return False

        # Create new knowledge entry
        new_entry = {
            "id": f"know_{uuid4().hex[:8]}",
            "category": action_data.get("category", "world_rule"),
            "fact": action_data.get("fact", ""),
            "details": action_data.get("details", ""),
            "confidence": action_data.get("confidence", 0.9),
            "tags": action_data.get("tags", []) + ["contradiction_resolution"],
            "source": "contradiction_synthesis",
            "contradiction_id": contradiction_id,
            "added_at": datetime.now().isoformat(),
            "added_by_message": message_number,
            "location": "",
            "chapter": "",
            "characters": []
        }

        # Add to entries
        knowledge_data.setdefault("entries", []).append(new_entry)

        self.log(f"Added knowledge entry from contradiction: {new_entry['fact'][:50]}...")
        return True

    # ==========================================================================
    # Knowledge Base Conversion (.md → JSON)
    # ==========================================================================

    def _should_convert_md(self) -> bool:
        """Check if knowledge_base.md exists and needs conversion.

        Returns:
            True if .md file exists and hasn't been converted yet
        """
        md_path = self.rp_dir / "state" / "knowledge_base.md"
        converted_path = self.rp_dir / "state" / "knowledge_base.md.converted"

        # Only convert if .md exists and .converted doesn't
        return md_path.exists() and not converted_path.exists()

    def _convert_knowledge_base_md(self) -> int:
        """Convert knowledge_base.md to JSON entries.

        Returns:
            Number of entries converted
        """
        md_path = self.rp_dir / "state" / "knowledge_base.md"

        if not md_path.exists():
            return 0

        try:
            content = md_path.read_text(encoding="utf-8")

            # Parse markdown sections
            entries = self._parse_knowledge_base_md(content)

            # Load existing knowledge (might already have some)
            knowledge_data = self._load_existing_knowledge()

            # Add converted entries to beginning (user-created should come first)
            knowledge_data["entries"] = entries + knowledge_data.get("entries", [])

            # Save
            self._save_knowledge(knowledge_data)

            # Rename .md to .md.converted (backup)
            converted_path = self.rp_dir / "state" / "knowledge_base.md.converted"
            md_path.rename(converted_path)

            self.log(f"Converted {len(entries)} entries from knowledge_base.md")
            return len(entries)

        except Exception as e:
            self.log(f"Failed to convert knowledge_base.md: {e}")
            import traceback
            self.log(traceback.format_exc())
            return 0

    def _parse_knowledge_base_md(self, content: str) -> list[dict]:
        """Parse knowledge_base.md into knowledge entries.

        Args:
            content: Markdown file content

        Returns:
            List of knowledge entry dicts
        """
        entries = []

        # Section → category mapping
        section_mapping = {
            "Geography": ["geography", "locations"],
            "Locations": ["locations"],
            "Organizations": ["organizations"],
            "World Rules": ["magic_system", "physics_laws"],
            "Cultural Details": ["culture", "customs"],
            "Historical Events": ["history", "past_events"],
            "Important Items": ["resources"],
            "Magic System": ["magic_system"],
            "History": ["history"],
            "Technology": ["technology"],
            "Religion": ["religion"],
            "Government": ["government"],
            "Economy": ["economy"],
            "Species": ["species_races"],
            "Lore": ["lore"],
        }

        # Extract all bullet points from each section
        for section_name, default_categories in section_mapping.items():
            facts = self._extract_bullets_from_section(content, section_name)

            for fact_text in facts:
                if not fact_text.strip():
                    continue

                entries.append({
                    "id": f"know_{uuid4().hex[:8]}",
                    "categories": default_categories,
                    "fact": fact_text.strip(),
                    "details": "",
                    "confidence": 1.0,  # User-created = certain
                    "tags": ["established_canon", "worldbuilding"],
                    "source": "user_created",
                    "source_message": None,
                    "source_timestamp": datetime.now().isoformat(),
                    "mentioned_by": [],
                    "location": None,
                    "chapter": None,
                    "revision_history": []
                })

        return entries

    def _extract_bullets_from_section(self, content: str, section_name: str) -> list[str]:
        """Extract bullet points from a markdown section.

        Args:
            content: Full markdown content
            section_name: Section header to find

        Returns:
            List of bullet point texts
        """
        facts = []

        # Find section (## Section Name or ### Section Name)
        pattern = rf"(?:^|\n)#{1,3}\s+{re.escape(section_name)}\s*\n(.*?)(?=\n#{1,3}\s+|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if not match:
            return facts

        section_content = match.group(1)

        # Extract bullet points (- item or * item)
        bullet_pattern = r"(?:^|\n)[-*]\s+(.+?)(?=\n[-*\#]|\Z)"
        bullets = re.findall(bullet_pattern, section_content, re.DOTALL)

        for bullet in bullets:
            # Clean up (remove extra whitespace, newlines)
            cleaned = bullet.strip().replace("\n", " ")
            if cleaned:
                facts.append(cleaned)

        return facts

    # ==========================================================================
    # Contradiction Handling
    # ==========================================================================

    def _check_for_contradictions(
        self,
        new_fact: str,
        existing_entries: list[dict]
    ) -> dict | None:
        """Check if new fact contradicts existing knowledge.

        Uses text similarity to detect potential contradictions.

        Args:
            new_fact: New fact text
            existing_entries: List of existing knowledge entries

        Returns:
            Existing entry that contradicts, or None
        """
        # Check similarity against existing facts
        for entry in existing_entries:
            existing_fact = entry.get("fact", "")

            # Calculate text similarity
            similarity = SequenceMatcher(None, new_fact.lower(), existing_fact.lower()).ratio()

            # If >80% similar, might be contradiction or duplicate
            if similarity > 0.8:
                # Check if it's a true duplicate (same meaning)
                if similarity > 0.95:
                    self.log(f"Detected duplicate fact (similarity: {similarity:.2f})")
                    return None  # Skip duplicate

                # Otherwise, potential contradiction
                self.log(f"Detected potential contradiction (similarity: {similarity:.2f})")
                return entry

        return None

    def _synthesize_contradiction(
        self,
        existing_entry: dict,
        new_fact: str,
        new_details: str,
        new_confidence: float,
        message_number: int
    ) -> dict | None:
        """Synthesize contradicting facts using LLM.

        Args:
            existing_entry: Existing knowledge entry
            new_fact: New conflicting fact
            new_details: Details of new fact
            new_confidence: Confidence of new fact
            message_number: Message number where new fact appeared

        Returns:
            Synthesis result dict or None if failed
        """
        try:
            # Build synthesis prompt
            prompt = self._build_synthesis_prompt(
                existing_entry,
                new_fact,
                new_details,
                new_confidence,
                message_number
            )

            # Call LLM (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Parse JSON response
            synthesis_data = self.parse_json_response(response)

            if not synthesis_data:
                self.log("Failed to parse synthesis response")
                return None

            return synthesis_data

        except Exception as e:
            self.log(f"Error during contradiction synthesis: {e}")
            return None

    # ==========================================================================
    # Entry Management
    # ==========================================================================

    def _apply_knowledge_updates(
        self,
        knowledge_data: dict,
        new_facts: list[dict],
        location: str,
        chapter: str,
        timestamp: str,
        message_number: int,
        mentioned_by: list[str]
    ) -> tuple[int, int]:
        """Apply knowledge updates (create new or synthesize contradictions).

        Args:
            knowledge_data: Full knowledge data structure
            new_facts: List of newly extracted facts
            location: Current location
            chapter: Current chapter
            timestamp: ISO timestamp
            message_number: Current message number
            mentioned_by: Characters who mentioned the facts

        Returns:
            Tuple of (added_count, updated_count)
        """
        entries = knowledge_data.get("entries", [])
        added_count = 0
        updated_count = 0

        for new_fact_data in new_facts:
            new_fact = new_fact_data.get("fact", "")
            new_details = new_fact_data.get("details", "")
            new_confidence = new_fact_data.get("confidence", 0.7)

            if not new_fact:
                continue

            # Check for contradictions
            contradicting_entry = self._check_for_contradictions(new_fact, entries)

            if contradicting_entry:
                # Synthesize contradiction
                self.log(f"Synthesizing contradiction for: {new_fact[:50]}...")
                synthesis = self._synthesize_contradiction(
                    contradicting_entry,
                    new_fact,
                    new_details,
                    new_confidence,
                    message_number
                )

                if synthesis and synthesis.get("can_reconcile"):
                    # Update existing entry with synthesis
                    contradicting_entry["fact"] = synthesis.get("synthesized_fact", new_fact)
                    contradicting_entry["details"] = synthesis.get("synthesized_details", new_details)
                    contradicting_entry["confidence"] = synthesis.get("confidence", new_confidence)

                    # Add to revision history
                    if "revision_history" not in contradicting_entry:
                        contradicting_entry["revision_history"] = []

                    contradicting_entry["revision_history"].append({
                        "message": message_number,
                        "fact": new_fact,
                        "confidence": new_confidence,
                        "synthesis": synthesis.get("revision_note", "Reconciled contradiction")
                    })

                    updated_count += 1
                    self.log(f"Updated entry {contradicting_entry['id']} with synthesis")
                else:
                    # Can't reconcile - add as new entry with note
                    self.log("Cannot reconcile contradiction, adding as separate entry")
                    entry = self._create_knowledge_entry(
                        new_fact_data,
                        location,
                        chapter,
                        timestamp,
                        message_number,
                        mentioned_by
                    )
                    entry["tags"].append("conflicting")
                    entries.append(entry)
                    added_count += 1
            else:
                # No contradiction - add new entry
                entry = self._create_knowledge_entry(
                    new_fact_data,
                    location,
                    chapter,
                    timestamp,
                    message_number,
                    mentioned_by
                )
                entries.append(entry)
                added_count += 1
                self.log(f"Added new entry: {entry['id']}")

        knowledge_data["entries"] = entries
        knowledge_data["last_updated_message"] = message_number

        return added_count, updated_count

    def _create_knowledge_entry(
        self,
        fact_data: dict,
        location: str,
        chapter: str,
        timestamp: str,
        message_number: int,
        mentioned_by: list[str]
    ) -> dict:
        """Create a new knowledge entry from extracted fact.

        Args:
            fact_data: Extracted fact dict from LLM
            location: Current location
            chapter: Current chapter
            timestamp: ISO timestamp
            message_number: Message number
            mentioned_by: Characters who mentioned this

        Returns:
            Complete knowledge entry dict
        """
        return {
            "id": self._generate_knowledge_id(),
            "categories": fact_data.get("categories", ["lore"]),
            "fact": fact_data.get("fact", ""),
            "details": fact_data.get("details", ""),
            "confidence": fact_data.get("confidence", 0.7),
            "tags": fact_data.get("tags", []),
            "source": "auto_extracted",
            "source_message": message_number,
            "source_timestamp": timestamp,
            "mentioned_by": fact_data.get("mentioned_by", mentioned_by),
            "location": location,
            "chapter": chapter,
            "revision_history": []
        }

    def _generate_knowledge_id(self) -> str:
        """Generate unique knowledge ID.

        Returns:
            ID string in format: know_{8_hex_chars}
        """
        return f"know_{uuid4().hex[:8]}"

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def _get_timestamp_from_time_tracking(
        self,
        scene_context: dict,
        message_number: int
    ) -> str:
        """Get timestamp from TimeTrackingAgent's time_context.

        Args:
            scene_context: Scene context from session state
            message_number: Current message number

        Returns:
            ISO 8601 formatted timestamp
        """
        time_ctx = scene_context.get("time_context", {})

        if not time_ctx:
            # No time tracking data - use current real-world time as fallback
            self.log("No time_context found, using current real-world time")
            return datetime.now().isoformat()

        current_datetime = time_ctx.get("current_datetime")

        if not current_datetime:
            # Time tracking exists but no current_datetime
            self.log("time_context exists but no current_datetime, using current time")
            return datetime.now().isoformat()

        # Convert time_context datetime to ISO 8601
        try:
            dt = datetime(
                current_datetime.get("year", 2024),
                current_datetime.get("month", 1),
                current_datetime.get("day", 1),
                current_datetime.get("hour", 0),
                current_datetime.get("minute", 0)
            )
            return dt.isoformat()
        except Exception as e:
            self.log(f"Failed to convert time_context to ISO: {e}")
            return datetime.now().isoformat()

    def _build_category_index(self, entries: list[dict]) -> dict[str, int]:
        """Build category count index.

        Args:
            entries: List of knowledge entries

        Returns:
            Dict mapping category to entry count
        """
        index = {}
        for entry in entries:
            for category in entry.get("categories", []):
                index[category] = index.get(category, 0) + 1
        return index

    def _format_summary(
        self,
        added_count: int,
        updated_count: int,
        new_facts: list[dict]
    ) -> str:
        """Format knowledge extraction result as summary string.

        Args:
            added_count: Number of new entries added
            updated_count: Number of entries updated (contradictions)
            new_facts: List of newly extracted facts

        Returns:
            Summary string
        """
        if added_count == 0 and updated_count == 0:
            return "No new knowledge extracted"

        parts = []

        if added_count > 0:
            parts.append(f"{added_count} new fact{'s' if added_count > 1 else ''}")

        if updated_count > 0:
            parts.append(f"{updated_count} updated (contradictions)")

        return f"Extracted: {', '.join(parts)}"


__all__ = ["KnowledgeExtractionAgent"]
