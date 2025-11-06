"""Fact Extraction Agent - Extract relevant entity facts for context injection.

This immediate agent runs BEFORE Claude responds to extract the most relevant
facts about entities mentioned in the user's message. This prevents context bloat
by injecting only relevant sections instead of entire entity card files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class FactExtractionAgent(BaseAgent):
    """Extract relevant facts from entity cards and knowledge base.

    This immediate agent:
    1. Loads entity data for entities mentioned in message
    2. Loads knowledge base entries
    3. Uses LLM to select 5-10 most relevant facts
    4. Returns concise, contextual information for prompt injection
    5. Reduces context usage by 10x compared to loading full entity cards
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "fact_extraction"

    def execute(
        self,
        user_message: str,
        message_number: int,
        **kwargs
    ) -> str:
        """Extract relevant facts and format for prompt injection.

        Args:
            user_message: User's message to analyze
            message_number: Current message index
            **kwargs: Additional context (loaded_entities, in_scene_entities, referenced_entities)

        Returns:
            Formatted fact context for prompt injection (empty string if none)
        """
        try:
            self.log(f"Extracting relevant facts for message #{message_number}")

            # Step 1: Get entity lists from automation context
            # IMPORTANT: Only process referenced entities (in_scene entities already fully loaded)
            in_scene_entities = kwargs.get("in_scene_entities", [])
            referenced_entities = kwargs.get("referenced_entities", [])

            # Fallback to loaded_entities if new fields not populated yet
            if not referenced_entities:
                loaded_entities = kwargs.get("loaded_entities", [])
                # Filter out in-scene entities
                referenced_entities = [e for e in loaded_entities if e not in in_scene_entities]

            if not referenced_entities:
                self.log("No referenced entities to extract facts for (all entities in-scene or none detected)")
                return ""

            self.log(f"Processing {len(referenced_entities)} referenced entities: {', '.join(referenced_entities)}")
            if in_scene_entities:
                self.log(f"Skipping {len(in_scene_entities)} in-scene entities (already fully loaded): {', '.join(in_scene_entities)}")

            # Step 2: Load entity data from repository (only for referenced entities)
            entity_data = self._load_entity_data(referenced_entities)

            if not entity_data:
                self.log("No entity data available")
                return ""

            # Step 3: Load knowledge base
            knowledge_data = self._load_knowledge_base()

            # Step 4: Build LLM prompt
            prompt = self._build_relevance_prompt(
                user_message,
                referenced_entities,
                entity_data,
                knowledge_data
            )

            # Step 5: Call LLM for fact selection (temperature=0.0 for consistency)
            self.log("Calling LLM for fact relevance selection...")
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 6: Parse JSON response
            result = self.parse_json_response(response)

            if not result or "relevant_facts" not in result:
                self.log("Failed to parse relevant facts from LLM")
                return ""

            relevant_facts = result.get("relevant_facts", [])

            if not relevant_facts:
                self.log("No relevant facts identified")
                return ""

            self.log(f"Found {len(relevant_facts)} relevant facts")

            # Step 7: Format for prompt injection
            formatted = self._format_for_injection(relevant_facts)

            self.log(f"Fact extraction complete ({len(formatted)} characters)")
            return formatted

        except Exception as e:
            self.log(f"Error in fact extraction: {e}")
            import traceback
            self.log(traceback.format_exc())
            return ""  # Fail gracefully, don't block main flow

    # ==========================================================================
    # Entity Data Loading
    # ==========================================================================

    def _load_entity_data(self, entity_names: list[str]) -> dict[str, dict[str, Any]]:
        """Load entity data from repository.

        Args:
            entity_names: List of entity names to load

        Returns:
            Dict mapping entity name to entity data
        """
        from src.domain.entities import FixtureEntityRepository

        repository = FixtureEntityRepository(rp_dir=self.rp_dir)
        entity_data = {}

        for name in entity_names:
            try:
                # Try loading as character first
                character = repository.get_character(name)
                entity_data[name] = {
                    "type": "character",
                    "basics": dict(character.basics),
                    "appearance": dict(character.appearance),
                    "personality": dict(character.personality),
                    "preferences": dict(character.preferences),
                    "abilities": dict(character.abilities),
                    "background": dict(character.background),
                    "metadata": dict(character.metadata),
                }
                self.log(f"Loaded character: {name}")
                continue
            except KeyError:
                pass

            try:
                # Try loading as location
                location = repository.get_location(name)
                entity_data[name] = {
                    "type": "location",
                    "basics": dict(location.basics),
                    "geography": dict(location.geography),
                    "facilities": dict(location.facilities),
                    "culture": dict(location.culture),
                    "hooks": dict(location.hooks),
                    "metadata": dict(location.metadata),
                }
                self.log(f"Loaded location: {name}")
                continue
            except KeyError:
                pass

            try:
                # Try loading as organization
                organization = repository.get_organization(name)
                entity_data[name] = {
                    "type": "organization",
                    "basics": dict(organization.basics),
                    "structure": dict(organization.structure),
                    "resources": dict(organization.resources),
                    "relations": dict(organization.relations),
                    "operations": dict(organization.operations),
                    "metadata": dict(organization.metadata),
                }
                self.log(f"Loaded organization: {name}")
                continue
            except KeyError:
                pass

            try:
                # Try loading as item
                item = repository.get_item(name)
                entity_data[name] = {
                    "type": "item",
                    "basics": dict(item.basics),
                    "attributes": dict(item.attributes),
                    "usage": dict(item.usage),
                    "metadata": dict(item.metadata),
                }
                self.log(f"Loaded item: {name}")
                continue
            except KeyError:
                pass

            self.log(f"Could not load entity: {name}")

        return entity_data

    def _load_knowledge_base(self) -> dict[str, Any] | None:
        """Load knowledge base from timeline-specific file.

        Returns:
            Knowledge data dict, or None if not available
        """
        try:
            # Get current session state
            session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
            knowledge_file = session_state.get("knowledge", {}).get("knowledge_file")

            if not knowledge_file:
                self.log("No knowledge pointer in session state")
                return None

            # Construct full path
            knowledge_path = self.rp_dir / knowledge_file

            # Load if exists
            if not knowledge_path.exists():
                self.log(f"Knowledge file not found: {knowledge_path}")
                return None

            with open(knowledge_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.log(f"Loaded {len(data.get('entries', []))} knowledge entries")
            return data

        except Exception as e:
            self.log(f"Failed to load knowledge base: {e}")
            return None

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_relevance_prompt(
        self,
        user_message: str,
        entity_names: list[str],
        entity_data: dict[str, dict[str, Any]],
        knowledge_data: dict[str, Any] | None
    ) -> str:
        """Build LLM prompt for fact selection.

        Args:
            user_message: User's current message
            entity_names: List of entity names
            entity_data: Entity data dicts
            knowledge_data: Knowledge base data (optional)

        Returns:
            Formatted prompt string
        """
        # Build entity context
        entities_context = ""
        for name in entity_names:
            if name not in entity_data:
                continue

            entity = entity_data[name]
            entity_type = entity.get("type", "unknown")

            entities_context += f"\n**{name}** ({entity_type}):\n"

            # Format based on entity type
            if entity_type == "character":
                entities_context += self._format_character_summary(entity)
            elif entity_type == "location":
                entities_context += self._format_location_summary(entity)
            elif entity_type == "organization":
                entities_context += self._format_organization_summary(entity)
            elif entity_type == "item":
                entities_context += self._format_item_summary(entity)

        # Build knowledge context (limit to prevent token overflow)
        knowledge_context = ""
        if knowledge_data and knowledge_data.get("entries"):
            entries = knowledge_data["entries"]
            display_limit = min(len(entries), 20)  # Max 20 entries

            knowledge_context = "\n**Knowledge Base Entries:**\n"
            for entry in entries[-display_limit:]:  # Most recent
                category = entry.get("category", "general")
                fact = entry.get("fact", "")
                knowledge_context += f"- [{category}] {fact}\n"

            if len(entries) > display_limit:
                knowledge_context += f"\n(... and {len(entries) - display_limit} more entries)\n"

        return f"""Extract the most relevant facts to include in Claude's context.

USER MESSAGE:
{user_message}

ENTITIES IN SCENE:
{entities_context}

{knowledge_context}

Select 5-10 most relevant facts focusing on:
1. **DIRECT RELEVANCE** - Information directly related to user's message
2. **CHARACTER TRAITS** - Personality/behavior that informs how they'd respond
3. **CONTEXTUAL INFO** - Details that apply to the current situation
4. **WORLD RULES** - Knowledge/facts that affect what can happen
5. **PRACTICAL INFO** - Hours, location, availability, etc.

Respond with JSON ONLY:
{{
  "relevant_facts": [
    {{
      "entity": "Golden Sun Bar",
      "fact_type": "facilities",
      "fact": "Open Fri-Sun 6pm-2am",
      "relevance": "User asking about going there on Saturday"
    }}
  ]
}}

IMPORTANT:
- Select 5-10 facts maximum (quality over quantity)
- Focus on what Claude needs to respond appropriately
- Include practical info when user asks about actions (hours, location, etc.)
- If no facts are clearly relevant, return empty array: {{"relevant_facts": []}}
- fact_type should be the section name (personality, facilities, abilities, etc.)"""

    def _format_character_summary(self, character: dict[str, Any]) -> str:
        """Format character data summary."""
        lines = []

        basics = character.get("basics", {})
        if basics:
            lines.append(f"  Basics: {self._dict_preview(basics)}")

        personality = character.get("personality", {})
        if personality:
            lines.append(f"  Personality: {self._dict_preview(personality)}")

        abilities = character.get("abilities", {})
        if abilities:
            lines.append(f"  Abilities: {self._dict_preview(abilities)}")

        return "\n".join(lines)

    def _format_location_summary(self, location: dict[str, Any]) -> str:
        """Format location data summary."""
        lines = []

        basics = location.get("basics", {})
        if basics:
            lines.append(f"  Basics: {self._dict_preview(basics)}")

        facilities = location.get("facilities", {})
        if facilities:
            lines.append(f"  Facilities: {self._dict_preview(facilities)}")

        geography = location.get("geography", {})
        if geography:
            lines.append(f"  Geography: {self._dict_preview(geography)}")

        return "\n".join(lines)

    def _format_organization_summary(self, org: dict[str, Any]) -> str:
        """Format organization data summary."""
        lines = []

        basics = org.get("basics", {})
        if basics:
            lines.append(f"  Basics: {self._dict_preview(basics)}")

        structure = org.get("structure", {})
        if structure:
            lines.append(f"  Structure: {self._dict_preview(structure)}")

        operations = org.get("operations", {})
        if operations:
            lines.append(f"  Operations: {self._dict_preview(operations)}")

        return "\n".join(lines)

    def _format_item_summary(self, item: dict[str, Any]) -> str:
        """Format item data summary."""
        lines = []

        basics = item.get("basics", {})
        if basics:
            lines.append(f"  Basics: {self._dict_preview(basics)}")

        attributes = item.get("attributes", {})
        if attributes:
            lines.append(f"  Attributes: {self._dict_preview(attributes)}")

        usage = item.get("usage", {})
        if usage:
            lines.append(f"  Usage: {self._dict_preview(usage)}")

        return "\n".join(lines)

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
    # Output Formatting
    # ==========================================================================

    def _format_for_injection(self, relevant_facts: list[dict[str, Any]]) -> str:
        """Format relevant facts for prompt injection.

        Args:
            relevant_facts: List of relevant fact dicts from LLM

        Returns:
            Formatted text for prompt injection
        """
        if not relevant_facts:
            return ""

        # Group by entity
        by_entity: dict[str, list[dict[str, Any]]] = {}
        for fact in relevant_facts:
            entity = fact.get("entity", "Unknown")
            if entity not in by_entity:
                by_entity[entity] = []
            by_entity[entity].append(fact)

        # Format as markdown
        lines = ["### RELEVANT FACTS\n"]

        for entity, facts in by_entity.items():
            lines.append(f"**{entity}:**")
            for fact_data in facts:
                fact_type = fact_data.get("fact_type", "general")
                fact = fact_data.get("fact", "")
                lines.append(f"- [{fact_type}] {fact}")
            lines.append("")  # Blank line between entities

        return "\n".join(lines)


__all__ = ["FactExtractionAgent"]
