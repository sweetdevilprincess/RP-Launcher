"""Relationship Analysis Agent - Track character relationships and dynamics.

This agent analyzes Claude's responses to extract:
- Relationship changes between characters (-100 to 100 scale)
- Relationship types (romantic, friendship, rivalry, etc.)
- Temporary emotional modifiers (irritated, amused, etc.)
- Direction-specific values (Alice→Bob can differ from Bob→Alice)
- Automatic recovery logic based on relationship tier

Updates are saved to each character's relationships.json with change history.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


# Relationship value tiers (-100 to 100)
RELATIONSHIP_TIERS = {
    "mortal_enemies": (-100, -80),
    "rivals": (-79, -50),
    "dislike": (-49, -25),
    "mild_dislike": (-24, -5),
    "strangers": (-4, 4),
    "acquaintances": (5, 24),
    "loose_friends": (25, 35),
    "good_friends": (36, 50),
    "close_friends": (51, 70),
    "best_friends": (71, 85),
    "soulmates": (86, 100)
}

# Relationship types taxonomy
RELATIONSHIP_TYPES = [
    "romantic", "romantic_interest", "friendship", "family", "rivalry", "enemy",
    "mentor_student", "coworkers", "allies", "acquaintances", "strangers",
    "complicated", "former_relationship", "unrequited", "professional"
]

# Change types for relationship events
CHANGE_TYPES = [
    "first_meeting", "growing_closer", "growing_distant", "conflict",
    "reconciliation", "betrayal", "confession", "romantic_development",
    "trust_gained", "trust_lost", "bonding_moment", "tension_increase",
    "status_change", "major_revelation", "boundary_crossed"
]

# Temporary modifier states
TEMP_MODIFIER_STATES = {
    "negative": ["irritated", "annoyed", "frustrated", "angry", "offended", "hurt", "embarrassed"],
    "positive": ["pleased", "amused", "impressed", "touched", "grateful"]
}

# Intensity levels with default durations
INTENSITY_DURATIONS = {
    "mild": {"messages": 3, "minutes": 20},
    "moderate": {"messages": 5, "minutes": 50},
    "strong": {"messages": 10, "minutes": 120}
}


class RelationshipAnalysisAgent(BaseAgent):
    """Track and analyze character relationships with temporary modifiers.

    Uses -100 to 100 value scale with tier mapping.
    Tracks temporary emotional states with expiration logic.
    Implements recovery logic based on relationship tier and intensity.
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "relationship_analysis"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute relationship analysis with modifier tracking.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze
            **kwargs: Additional context

        Returns:
            Summary string of relationship updates
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping relationship analysis")
            return "No response to analyze"

        try:
            self.log(f"Analyzing relationships for message #{message_number}")

            # Step 1: Get scene context from session state
            scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

            # Step 2: Extract context
            characters_in_scene = scene_context.get("characters_in_scene", [])
            location = scene_context.get("location", "Unknown")
            chapter = scene_context.get("chapter", "")

            # Fallback: If no characters detected, try to extract from response
            if not characters_in_scene:
                self.log("No characters in scene_context, will extract from response")
                characters_in_scene = None

            # Step 3: Get timestamp from TimeTrackingAgent
            timestamp = self._get_timestamp_from_time_tracking(scene_context, message_number)

            # Step 4: Check for expired modifiers and apply recovery logic
            expired_count = self._process_expired_modifiers(scene_context, message_number, timestamp)
            if expired_count > 0:
                self.log(f"Processed {expired_count} expired modifiers")

            # Step 5: Load existing relationships for context
            existing_relationships = self._load_existing_relationships(characters_in_scene)

            # Step 6: Load recent memories for linking
            recent_memories = self._load_recent_memories(characters_in_scene, message_number)

            # Step 7: Build LLM prompt
            prompt = self._build_relationship_analysis_prompt(
                user_message,
                claude_response,
                characters_in_scene,
                location,
                chapter,
                existing_relationships
            )

            # Step 8: Call LLM (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 9: Parse JSON response
            relationships_data = self.parse_json_response(response)

            if not relationships_data or "relationship_updates" not in relationships_data:
                self.log("Failed to parse relationships from LLM response")
                return "Relationship analysis failed"

            # Step 10: Save relationship updates
            updated_count = self._save_relationship_updates(
                relationships_data["relationship_updates"],
                location,
                chapter,
                timestamp,
                message_number,
                recent_memories,
                scene_context
            )

            # Step 11: Return summary
            return self._format_summary(updated_count, relationships_data["relationship_updates"])

        except Exception as e:
            self.log(f"Error in relationship analysis: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Relationship analysis failed: {e}"

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_relationship_analysis_prompt(
        self,
        user_message: str,
        claude_response: str,
        characters_in_scene: list[str] | None,
        location: str,
        chapter: str,
        existing_relationships: dict
    ) -> str:
        """Build LLM prompt for relationship analysis."""
        # Build character context
        if characters_in_scene:
            char_context = f"CHARACTERS IN SCENE: {', '.join(characters_in_scene)}"
        else:
            char_context = "CHARACTERS IN SCENE: (extract from response)"

        # Build existing relationships context
        if existing_relationships:
            existing_str = self._format_existing_relationships(existing_relationships)
            existing_context = f"\nEXISTING RELATIONSHIPS:\n{existing_str}"
        else:
            existing_context = "\nEXISTING RELATIONSHIPS: None on record"

        # Build tier reference
        tier_guide = self._build_tier_guide()

        # Build taxonomy guidance
        rel_types_str = ", ".join(RELATIONSHIP_TYPES)
        change_types_str = ", ".join(CHANGE_TYPES)
        temp_states_str = ", ".join(TEMP_MODIFIER_STATES["negative"] + TEMP_MODIFIER_STATES["positive"])

        return f"""Analyze this roleplay response and identify relationship changes between characters.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}

{char_context}
LOCATION: {location}
CHAPTER: {chapter}
{existing_context}

{tier_guide}

Identify:
- NEW relationships formed (first meetings, introductions)
- CHANGED relationships (permanent value shifts)
- TEMPORARY emotional reactions (irritation, amusement, etc.)

For each relationship change, determine:
1. **Value** (-100 to 100) - Permanent relationship level
2. **Change intensity** (mild/moderate/strong) - How significant was the shift
3. **Interaction type** (negative/positive) - Nature of the interaction
4. **Temporary modifier** (if any) - Short-term emotional state

**Relationship Types**: {rel_types_str}
**Change Types**: {change_types_str}
**Temporary States**: {temp_states_str}

**Intensity Guidelines**:
- Mild: Minor interaction, small impact
- Moderate: Significant interaction, noticeable impact
- Strong: Major event, substantial impact

Respond with JSON ONLY:
{{
  "relationship_updates": [
    {{
      "character_a": "Alice",
      "character_b": "Bob",
      "relationship_type": "romantic_interest",
      "value": 28,
      "previous_value": 20,
      "direction": "Alice→Bob",
      "mutual": false,
      "change_type": "romantic_development",
      "change_summary": "Brief description of what changed",
      "intensity": "moderate",
      "interaction_type": "positive",
      "temporary_modifier": {{
        "state": "pleased",
        "reason": "Bob complimented her"
      }},
      "is_new_relationship": false
    }}
  ]
}}

IMPORTANT:
- value: Permanent relationship level (-100 to 100)
- intensity: mild/moderate/strong (affects recovery logic)
- interaction_type: negative/positive (affects recovery logic)
- temporary_modifier: Optional - only if there's a short-term emotional reaction
- Only report relationships that CHANGED in this response
- If no changes occurred, return empty array
- Each update is direction-specific (Alice→Bob can differ from Bob→Alice)
- If characters_in_scene was "(extract from response)", determine characters yourself"""

    def _build_tier_guide(self) -> str:
        """Build tier reference guide for LLM."""
        lines = ["**VALUE SCALE (-100 to 100)**:"]
        for tier, (min_val, max_val) in RELATIONSHIP_TIERS.items():
            lines.append(f"  {min_val} to {max_val}: {tier}")
        return "\n".join(lines)

    def _format_existing_relationships(self, existing: dict) -> str:
        """Format existing relationships for prompt context."""
        lines = []
        for (char_a, char_b), data in existing.items():
            value = data.get("value", 0)
            tier = data.get("tier", "unknown")
            lines.append(f"  {char_a}→{char_b}: {value} ({tier})")
        return "\n".join(lines) if lines else "  None"

    # ==========================================================================
    # Timestamp Handling
    # ==========================================================================

    def _get_timestamp_from_time_tracking(
        self,
        scene_context: dict,
        message_number: int
    ) -> str:
        """Get timestamp from TimeTrackingAgent's time_context."""
        time_ctx = scene_context.get("time_context", {})

        if not time_ctx:
            self.log("No time_context found, using current real-world time")
            return datetime.now().isoformat()

        current_datetime = time_ctx.get("current_datetime")

        if not current_datetime:
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

    # ==========================================================================
    # Tier Calculation
    # ==========================================================================

    def _value_to_tier(self, value: int) -> str:
        """Convert relationship value to tier name."""
        for tier, (min_val, max_val) in RELATIONSHIP_TIERS.items():
            if min_val <= value <= max_val:
                return tier
        return "strangers"  # Default fallback

    # ==========================================================================
    # Relationship Loading
    # ==========================================================================

    def _load_existing_relationships(
        self,
        characters_in_scene: list[str] | None
    ) -> dict:
        """Load existing relationships for characters in scene."""
        if not characters_in_scene:
            return {}

        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(
            rp_dir=self.rp_dir,
            session_state_service=self.bridge.session_state_service
        )

        existing = {}

        for character in characters_in_scene:
            try:
                # Load relationships file for this character
                char_slug = repository._slug(character)

                # Determine session ID
                timeline = self.bridge.session_state_service.get_current_timeline(self.rp_dir)
                session_id = timeline.get("current_session_id", "main")

                # Try to load relationships file
                if session_id == "main":
                    rel_file = repository.base_dir / f"{char_slug}_relationships.json"
                else:
                    rel_file = repository.base_dir / f"{char_slug}_relationships_{session_id}.json"

                if not rel_file.exists():
                    continue

                with open(rel_file, 'r', encoding='utf-8') as f:
                    rel_data = json.load(f)

                # Extract relationships
                for target, rel_info in rel_data.get("relationships", {}).items():
                    key = (character, target)
                    existing[key] = {
                        "value": rel_info.get("value", 0),
                        "tier": rel_info.get("tier", "strangers"),
                        "type": rel_info.get("relationship_type", "unknown")
                    }

            except Exception as e:
                self.log(f"Failed to load relationships for {character}: {e}")
                continue

        return existing

    def _load_recent_memories(
        self,
        characters_in_scene: list[str] | None,
        message_number: int
    ) -> dict:
        """Load recent memories for auto-linking (last 5 messages)."""
        if not characters_in_scene:
            return {}

        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(
            rp_dir=self.rp_dir,
            session_state_service=self.bridge.session_state_service
        )

        recent = {}

        for character in characters_in_scene:
            try:
                memory_log = repository.get_memory_log(character)

                # Get memories from last 5 messages
                recent_entries = [
                    e for e in memory_log.entries
                    if e.message_index >= message_number - 5
                ]

                for entry in recent_entries:
                    recent[entry.id] = {
                        "character": character,
                        "summary": entry.summary,
                        "message_index": entry.message_index
                    }

            except Exception as e:
                self.log(f"Failed to load memories for {character}: {e}")
                continue

        return recent

    # ==========================================================================
    # Modifier Expiration & Recovery
    # ==========================================================================

    def _process_expired_modifiers(
        self,
        scene_context: dict,
        current_message: int,
        current_timestamp: str
    ) -> int:
        """Check for expired modifiers and apply recovery logic.

        Returns:
            Number of expired modifiers processed
        """
        modifiers = scene_context.get("relationship_modifiers", {})

        if not modifiers:
            return 0

        expired_count = 0
        expired_keys = []

        for key, modifier in modifiers.items():
            if self._is_modifier_expired(modifier, current_message, current_timestamp):
                # Apply recovery logic
                self._apply_recovery_logic(key, modifier, scene_context)
                expired_keys.append(key)
                expired_count += 1

        # Remove expired modifiers
        for key in expired_keys:
            del modifiers[key]

        # Update scene context if any modifiers expired
        if expired_count > 0:
            self.bridge.session_state_service.update_scene_context(
                self.rp_dir,
                scene_context
            )

        return expired_count

    def _is_modifier_expired(
        self,
        modifier: dict,
        current_message: int,
        current_timestamp: str
    ) -> bool:
        """Check if a modifier has expired."""
        # Check message count
        started_message = modifier.get("started_message", 0)
        expires_after = modifier.get("expires_after_messages", 3)

        if current_message - started_message >= expires_after:
            return True

        # Check time elapsed
        try:
            started = datetime.fromisoformat(modifier.get("started_timestamp", current_timestamp))
            current = datetime.fromisoformat(current_timestamp)
            minutes_elapsed = (current - started).total_seconds() / 60

            expires_minutes = modifier.get("expires_after_minutes", 30)

            if minutes_elapsed >= expires_minutes:
                return True
        except Exception:
            pass

        return False

    def _apply_recovery_logic(
        self,
        relationship_key: str,
        modifier: dict,
        scene_context: dict
    ) -> None:
        """Apply recovery logic when modifier expires."""
        # Parse relationship key (e.g., "Alice_to_Bob")
        parts = relationship_key.split("_to_")
        if len(parts) != 2:
            return

        char_a, char_b = parts

        # Load current relationship
        try:
            from src.domain.entities import FixtureEntityRepository

            repository = FixtureEntityRepository(
                rp_dir=self.rp_dir,
                session_state_service=self.bridge.session_state_service
            )

            char_slug = repository._slug(char_a)
            timeline = self.bridge.session_state_service.get_current_timeline(self.rp_dir)
            session_id = timeline.get("current_session_id", "main")

            if session_id == "main":
                rel_file = repository.base_dir / f"{char_slug}_relationships.json"
            else:
                rel_file = repository.base_dir / f"{char_slug}_relationships_{session_id}.json"

            if not rel_file.exists():
                return

            with open(rel_file, 'r', encoding='utf-8') as f:
                rel_data = json.load(f)

            relationship = rel_data.get("relationships", {}).get(char_b)
            if not relationship:
                return

            current_value = relationship.get("value", 0)
            intensity = modifier.get("intensity", "mild")
            interaction_type = modifier.get("interaction_type", "negative")

            # Get original value from change history
            history = relationship.get("change_history", [])
            if not history:
                return

            # Last change entry has the original value
            last_change = history[-1]
            original_value = last_change.get("previous_value", current_value)

            # Determine if should recover
            should_recover = self._should_value_recover(
                original_value,
                current_value,
                intensity,
                interaction_type
            )

            if should_recover:
                # Calculate recovery value
                recovery_value = self._calculate_recovery_value(
                    original_value,
                    current_value,
                    intensity,
                    interaction_type
                )

                if recovery_value != current_value:
                    # Update relationship value
                    relationship["value"] = recovery_value
                    relationship["tier"] = self._value_to_tier(recovery_value)
                    relationship["last_updated"] = datetime.now().isoformat()

                    # Add recovery note to history
                    recovery_note = {
                        "change_id": f"rec_{uuid4().hex[:8]}",
                        "change_type": "modifier_recovery",
                        "value": recovery_value,
                        "previous_value": current_value,
                        "memory_id": None,
                        "message_index": modifier.get("started_message", 0),
                        "timestamp": datetime.now().isoformat(),
                        "note": f"Recovered from {modifier.get('state')} ({intensity})"
                    }
                    relationship["change_history"].append(recovery_note)

                    # Save updated relationship
                    with open(rel_file, 'w', encoding='utf-8') as f:
                        json.dump(rel_data, f, indent=2, ensure_ascii=False)

                    self.log(f"Recovered relationship {char_a}→{char_b}: {current_value}→{recovery_value}")

        except Exception as e:
            self.log(f"Failed to apply recovery logic: {e}")

    def _should_value_recover(
        self,
        original_value: int,
        current_value: int,
        intensity: str,
        interaction_type: str
    ) -> bool:
        """Determine if relationship value should recover after modifier expires."""
        # Strong intensity = never recover
        if intensity == "strong":
            return False

        # Neutral zone (-24 to 24) - fragile relationships
        if -24 <= original_value <= 24:
            return intensity == "mild"  # Only mild recovers

        # Good relationships (25+) - resilient to negativity
        if original_value >= 25:
            if interaction_type == "negative":
                return intensity in ["mild", "moderate"]  # Forgive easier
            else:
                return True  # Positive interactions always can improve

        # Bad relationships (-25 to -100) - resilient to positivity
        if original_value <= -25:
            if interaction_type == "negative":
                return False  # Permanent damage
            else:
                return intensity in ["mild", "moderate"]  # Slow trust building

        return False

    def _calculate_recovery_value(
        self,
        original_value: int,
        current_value: int,
        intensity: str,
        interaction_type: str
    ) -> int:
        """Calculate recovered relationship value."""
        # For good relationships with negative interactions, may improve after recovery
        if original_value >= 25 and interaction_type == "negative":
            # If it was playful teasing, relationship might improve
            if intensity == "mild" and current_value < original_value:
                # Small chance of improvement (playful interaction bonded them)
                return min(original_value + 2, 100)
            else:
                # Standard recovery
                return original_value

        # For bad relationships with positive interactions, partial recovery
        if original_value <= -25 and interaction_type == "positive":
            # Don't fully recover - they're still suspicious
            diff = current_value - original_value
            partial_recovery = original_value + (diff // 2)
            return partial_recovery

        # Default: return to original
        return original_value

    # ==========================================================================
    # Relationship Saving
    # ==========================================================================

    def _save_relationship_updates(
        self,
        updates: list[dict],
        location: str,
        chapter: str,
        timestamp: str,
        message_number: int,
        recent_memories: dict,
        scene_context: dict
    ) -> int:
        """Save relationship updates bidirectionally with modifier tracking."""
        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(
            rp_dir=self.rp_dir,
            session_state_service=self.bridge.session_state_service
        )

        updated_count = 0
        relationships_for_state = {}
        modifiers_for_state = {}

        for update in updates:
            character_a = update.get("character_a")
            character_b = update.get("character_b")

            if not character_a or not character_b:
                self.log("Relationship update missing character fields, skipping")
                continue

            # Find linked memory ID (from same message)
            memory_id = self._find_linked_memory(
                recent_memories,
                character_a,
                character_b,
                message_number
            )

            # Create change entry
            value = update.get("value", 0)
            previous_value = update.get("previous_value", 0)

            change_entry = {
                "change_id": f"rel_{uuid4().hex[:8]}",
                "change_type": update.get("change_type", "status_change"),
                "value": value,
                "previous_value": previous_value,
                "memory_id": memory_id,
                "message_index": message_number,
                "timestamp": timestamp
            }

            # Build relationship data
            tier = self._value_to_tier(value)
            relationship_data = {
                "relationship_type": update.get("relationship_type", "acquaintances"),
                "value": value,
                "tier": tier,
                "direction": update.get("direction", f"{character_a}→{character_b}"),
                "mutual": update.get("mutual", False),
                "is_new": update.get("is_new_relationship", False)
            }

            try:
                # Update relationship for character_a → character_b
                self._update_character_relationship(
                    repository,
                    character_a,
                    character_b,
                    relationship_data,
                    change_entry
                )

                # Update relationship for character_b → character_a (bidirectional)
                # Note: Use same value unless specified differently
                self._update_character_relationship(
                    repository,
                    character_b,
                    character_a,
                    relationship_data,
                    change_entry
                )

                # Track for session state update
                relationships_for_state[f"{character_a}_to_{character_b}"] = tier
                relationships_for_state[f"{character_b}_to_{character_a}"] = tier

                # Handle temporary modifier
                temp_mod = update.get("temporary_modifier")
                if temp_mod:
                    intensity = update.get("intensity", "mild")
                    interaction_type = update.get("interaction_type", "neutral")

                    modifier_data = {
                        "state": temp_mod.get("state"),
                        "intensity": intensity,
                        "reason": temp_mod.get("reason", ""),
                        "interaction_type": interaction_type,
                        "started_message": message_number,
                        "started_timestamp": timestamp,
                        "expires_after_messages": INTENSITY_DURATIONS[intensity]["messages"],
                        "expires_after_minutes": INTENSITY_DURATIONS[intensity]["minutes"]
                    }

                    modifiers_for_state[f"{character_a}_to_{character_b}"] = modifier_data

                updated_count += 1
                self.log(f"Updated relationship: {character_a} <-> {character_b}")

            except Exception as e:
                self.log(f"Failed to save relationship update: {e}")
                import traceback
                self.log(traceback.format_exc())
                continue

        # Update session state with relationship tiers and modifiers
        if relationships_for_state or modifiers_for_state:
            scene_context["relationships"] = scene_context.get("relationships", {})
            scene_context["relationships"].update(relationships_for_state)

            if modifiers_for_state:
                scene_context["relationship_modifiers"] = scene_context.get("relationship_modifiers", {})
                scene_context["relationship_modifiers"].update(modifiers_for_state)

            self.bridge.session_state_service.update_scene_context(
                self.rp_dir,
                scene_context
            )

        return updated_count

    def _find_linked_memory(
        self,
        recent_memories: dict,
        char_a: str,
        char_b: str,
        message_number: int
    ) -> str | None:
        """Find memory ID from same message that involves both characters."""
        for memory_id, memory_info in recent_memories.items():
            # Must be from same message
            if memory_info.get("message_index") != message_number:
                continue

            # Check if memory mentions both characters
            summary = memory_info.get("summary", "").lower()
            if char_a.lower() in summary and char_b.lower() in summary:
                return memory_id

        return None

    def _update_character_relationship(
        self,
        repository,
        from_character: str,
        to_character: str,
        relationship_data: dict,
        change_entry: dict
    ) -> None:
        """Update a single character's relationship record."""
        char_slug = repository._slug(from_character)

        # Determine session ID
        timeline = self.bridge.session_state_service.get_current_timeline(self.rp_dir)
        session_id = timeline.get("current_session_id", "main")

        # Determine file path
        if session_id == "main":
            rel_file = repository.base_dir / f"{char_slug}_relationships.json"
        else:
            rel_file = repository.base_dir / f"{char_slug}_relationships_{session_id}.json"

        # Load or create relationships file
        if rel_file.exists():
            with open(rel_file, 'r', encoding='utf-8') as f:
                rel_data = json.load(f)
        else:
            rel_data = {
                "character": from_character,
                "session_id": session_id,
                "relationships": {}
            }

        # Get or create relationship entry
        relationships = rel_data.get("relationships", {})
        existing_rel = relationships.get(to_character)

        if existing_rel:
            # Update existing relationship
            existing_rel["relationship_type"] = relationship_data["relationship_type"]
            existing_rel["value"] = relationship_data["value"]
            existing_rel["tier"] = relationship_data["tier"]
            existing_rel["direction"] = relationship_data["direction"]
            existing_rel["mutual"] = relationship_data["mutual"]
            existing_rel["last_updated"] = change_entry["timestamp"]
            existing_rel["last_message_index"] = change_entry["message_index"]

            # Append to change history
            if "change_history" not in existing_rel:
                existing_rel["change_history"] = []
            existing_rel["change_history"].append(change_entry)

            relationships[to_character] = existing_rel
        else:
            # Create new relationship
            relationships[to_character] = {
                "target_character": to_character,
                "relationship_type": relationship_data["relationship_type"],
                "value": relationship_data["value"],
                "tier": relationship_data["tier"],
                "direction": relationship_data["direction"],
                "mutual": relationship_data["mutual"],
                "first_established": change_entry["timestamp"],
                "last_updated": change_entry["timestamp"],
                "first_message_index": change_entry["message_index"],
                "last_message_index": change_entry["message_index"],
                "change_history": [change_entry]
            }

        rel_data["relationships"] = relationships

        # Save relationships file
        rel_file.parent.mkdir(parents=True, exist_ok=True)
        with open(rel_file, 'w', encoding='utf-8') as f:
            json.dump(rel_data, f, indent=2, ensure_ascii=False)

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def _format_summary(self, updated_count: int, updates: list[dict]) -> str:
        """Format relationship analysis result as summary string."""
        if updated_count == 0:
            return "No relationship changes detected"

        if updated_count == 1:
            update = updates[0]
            char_a = update.get("character_a", "unknown")
            char_b = update.get("character_b", "unknown")
            return f"Updated 1 relationship: {char_a} <-> {char_b}"

        # Count unique relationship pairs
        pairs = set()
        for u in updates:
            char_a = u.get("character_a")
            char_b = u.get("character_b")
            if char_a and char_b:
                pairs.add(tuple(sorted([char_a, char_b])))

        return f"Updated {len(pairs)} relationships"


__all__ = ["RelationshipAnalysisAgent"]
