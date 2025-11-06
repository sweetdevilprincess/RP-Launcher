"""High-level entity operations built on JSON fixtures."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...infrastructure.templates.state_service import StateTemplateService
from ...shared.interfaces import LoggingService  # type: ignore[attr-defined]
from ...shared.models import EntityType

if TYPE_CHECKING:
    from ...automation.contracts import AutomationContext
from .entity_parser import (
    CharacterEntity,
    ItemEntity,
    LocationEntity,
    MemoryLog,
    OrganizationEntity,
)
from .entity_repository import FixtureEntityRepository
from .preference_generator import PreferenceGenerator, PreferenceResult


@dataclass
class EntityStats:
    total_characters: int
    total_locations: int
    total_organizations: int
    total_items: int
    total_memory_logs: int


class EntityService:
    """Coordinates repository access, templates, and cross-entity queries."""

    def __init__(
        self,
        *,
        repository: FixtureEntityRepository | None = None,
        templates: StateTemplateService | None = None,
        preference_generator: PreferenceGenerator | None = None,
        logger: LoggingService | None = None,
        session_state: Any | None = None,
        rp_dir: Any | None = None,
    ) -> None:
        self._repository = repository or FixtureEntityRepository()
        self._templates = templates or StateTemplateService()
        self._preference_generator = preference_generator
        self._logger = logger
        self._session_state = session_state
        self._rp_dir = rp_dir

    # ------------------------------------------------------------------
    # Accessors

    def list_characters(self) -> list[CharacterEntity]:
        return self._repository.list_characters()

    def list_locations(self) -> list[LocationEntity]:
        return self._repository.list_locations()

    def list_organizations(self) -> list[OrganizationEntity]:
        return self._repository.list_organizations()

    def list_items(self) -> list[ItemEntity]:
        return self._repository.list_items()

    def list_memory_logs(self) -> list[MemoryLog]:
        return self._repository.list_memory_logs()

    def get_character(self, name: str) -> CharacterEntity | None:
        try:
            return self._repository.get_character(name)
        except KeyError:
            return None

    # ------------------------------------------------------------------
    # Aggregation & queries

    def stats(self) -> EntityStats:
        return EntityStats(
            total_characters=len(self._repository.list_characters()),
            total_locations=len(self._repository.list_locations()),
            total_organizations=len(self._repository.list_organizations()),
            total_items=len(self._repository.list_items()),
            total_memory_logs=len(self._repository.list_memory_logs()),
        )

    def detect_mentions(self, text: str) -> set[str]:
        lowered = text.lower()
        matches: set[str] = set()

        def _matches(entity_name: str, triggers: Iterable[str]) -> bool:
            if entity_name.lower() in lowered:
                return True
            return any(trigger and trigger.lower() in lowered for trigger in triggers)

        for character in self._repository.list_characters():
            triggers = character.metadata.get("tags", [])
            if _matches(character.name, triggers):
                matches.add(character.name)

        for location in self._repository.list_locations():
            triggers = location.metadata.get("tags", [])
            if _matches(location.name, triggers):
                matches.add(location.name)

        for organization in self._repository.list_organizations():
            triggers = organization.metadata.get("tags", [])
            if _matches(organization.name, triggers):
                matches.add(organization.name)

        return matches

    def _get_scene_context(self) -> dict[str, Any]:
        """Get scene context from SessionStateService.

        Returns:
            Scene context dict with characters_in_scene, location, etc.
            Returns default empty context if SessionStateService not configured.
        """
        if not self._session_state or not self._rp_dir:
            # No session state service - return default empty context
            return {
                "chapter": "",
                "location": "Unknown",
                "characters_in_scene": [],
                "last_updated_message": 0,
                "scene_analysis": {},
                "time_context": {}
            }

        return self._session_state.get_scene_context(self._rp_dir)

    def _entity_names_to_paths(self, entity_names: list[str]) -> list[Any]:
        """Convert entity names to file paths.

        Checks multiple locations for entity files:
        - characters/{name}.md (markdown character cards)
        - entities/character_{name_lower}.json (JSON character cards)
        - entities/location_{name_lower}.json (JSON locations)
        - entities/organization_{name_lower}.json (JSON organizations)
        - entities/item_{name_lower}.json (JSON items)

        Args:
            entity_names: List of entity names to convert

        Returns:
            List of Path objects for existing entity files
        """
        from pathlib import Path

        if not self._rp_dir:
            return []

        paths = []
        for name in entity_names:
            name_lower = name.lower().replace(" ", "_")

            # Try characters/ directory (markdown)
            char_md = self._rp_dir / "characters" / f"{name}.md"
            if char_md.exists():
                paths.append(char_md)
                continue

            # Try entities/ directory (JSON) - try all entity types
            entity_patterns = [
                f"character_{name_lower}.json",
                f"location_{name_lower}.json",
                f"organization_{name_lower}.json",
                f"item_{name_lower}.json",
            ]

            found = False
            for pattern in entity_patterns:
                entity_path = self._rp_dir / "entities" / pattern
                if entity_path.exists():
                    paths.append(entity_path)
                    found = True
                    break

            if not found and self._logger:
                self._logger.debug(
                    "entity_service.path_not_found",
                    context={"entity_name": name, "tried_patterns": entity_patterns}
                )

        return paths

    def prepare_entities(self, context: AutomationContext) -> AutomationContext:
        """Prepare entity information for automation context with two-tier loading.

        Detects entities mentioned in the user message and splits them into:
        - IN SCENE: Characters in scene, current location, active items → Full cards
        - REFERENCED: Mentioned but not in scene → Basics only

        Args:
            context: The automation context to enrich

        Returns:
            The context with entity information:
            - loaded_entities: All detected entities
            - entities_with_cores: Entities with personality cores
            - in_scene_entities: Entities actively in scene (full cards)
            - referenced_entities: Entities mentioned but not in scene (basics only)
            - tier3_files: File paths for in-scene entities (full cards)
            - tier3_referenced_files: File paths for referenced entities (basics only)
        """
        # Detect entities mentioned in message
        mentioned = self.detect_mentions(context.message)

        if self._logger:
            self._logger.debug(
                "entity_service.detect_mentions",
                context={"mentioned_count": len(mentioned), "entities": list(mentioned)},
            )

        # Get scene context to determine in-scene vs referenced
        scene_context = self._get_scene_context()
        characters_in_scene = set(scene_context.get("characters_in_scene", []))
        current_location = scene_context.get("location", "Unknown")

        if self._logger:
            self._logger.debug(
                "entity_service.scene_context",
                context={
                    "characters_in_scene": list(characters_in_scene),
                    "current_location": current_location,
                },
            )

        # Split entities into in-scene vs referenced
        in_scene_entities = []
        referenced_entities = []
        loaded_entities = []
        entities_with_cores = []
        entities_with_archetypes = []
        archetype_categories = {
            "authority_figures": [],
            "merchants_traders": [],
            "commoners_laborers": [],
            "antagonists_rivals": [],
            "hybrid_npcs": []
        }
        entities_with_modifiers = []

        for entity_name in mentioned:
            try:
                # Try to load as character first
                character = self.get_character(entity_name)
                if character:
                    loaded_entities.append(entity_name)

                    # Check if has personality core
                    if character.core_mandate:
                        entities_with_cores.append(entity_name)

                    # Check for behavioral archetype
                    archetype = character.personality.get("behavioral_archetype")
                    if archetype:
                        entities_with_archetypes.append(entity_name)
                        # Categorize by archetype type
                        archetype_key = archetype.lower().replace("-", "_")
                        if archetype_key in archetype_categories:
                            archetype_categories[archetype_key].append(entity_name)
                        # Check for hybrid archetypes
                        hybrid_archetypes = character.metadata.get("hybrid_archetypes")
                        if hybrid_archetypes:
                            archetype_categories["hybrid_npcs"].append(entity_name)

                    # Check for contextual modifiers
                    if character.metadata.get("contextual_modifiers"):
                        entities_with_modifiers.append(entity_name)

                    # Determine if in-scene or referenced
                    if entity_name in characters_in_scene:
                        in_scene_entities.append(entity_name)
                        if self._logger:
                            self._logger.debug(
                                "entity_service.in_scene_character",
                                context={"name": entity_name},
                            )
                    else:
                        referenced_entities.append(entity_name)
                        if self._logger:
                            self._logger.debug(
                                "entity_service.referenced_character",
                                context={"name": entity_name},
                            )
                    continue

            except (KeyError, AttributeError):
                pass  # Not a character, check other entity types

            # Check if it's the current location (in-scene)
            if entity_name == current_location:
                in_scene_entities.append(entity_name)
                loaded_entities.append(entity_name)
                if self._logger:
                    self._logger.debug(
                        "entity_service.in_scene_location",
                        context={"name": entity_name},
                    )
                continue

            # Check if it's a location, organization, or item (all referenced by default)
            # Try loading from repository to confirm entity exists
            try:
                # Try location
                location = self._repository.get_location(entity_name)
                if location:
                    referenced_entities.append(entity_name)
                    loaded_entities.append(entity_name)
                    if self._logger:
                        self._logger.debug(
                            "entity_service.referenced_location",
                            context={"name": entity_name},
                        )
                    continue
            except (KeyError, AttributeError):
                pass

            try:
                # Try organization
                org = self._repository.get_organization(entity_name)
                if org:
                    referenced_entities.append(entity_name)
                    loaded_entities.append(entity_name)
                    if self._logger:
                        self._logger.debug(
                            "entity_service.referenced_organization",
                            context={"name": entity_name},
                        )
                    continue
            except (KeyError, AttributeError):
                pass

            try:
                # Try item
                item = self._repository.get_item(entity_name)
                if item:
                    # TODO: Track "active items" (being used) similar to characters_in_scene
                    # For now, all items are referenced
                    referenced_entities.append(entity_name)
                    loaded_entities.append(entity_name)
                    if self._logger:
                        self._logger.debug(
                            "entity_service.referenced_item",
                            context={"name": entity_name},
                        )
                    continue
            except (KeyError, AttributeError):
                pass

            # Entity mentioned but not found in repository
            if self._logger:
                self._logger.debug(
                    "entity_service.not_found",
                    context={"name": entity_name},
                )

        # Convert entity names to file paths
        tier3_files = self._entity_names_to_paths(in_scene_entities)
        tier3_referenced_files = self._entity_names_to_paths(referenced_entities)

        if self._logger:
            self._logger.info(
                "entity_service.prepare_complete",
                context={
                    "loaded": len(loaded_entities),
                    "with_cores": len(entities_with_cores),
                    "with_archetypes": len(entities_with_archetypes),
                    "with_modifiers": len(entities_with_modifiers),
                    "in_scene": len(in_scene_entities),
                    "referenced": len(referenced_entities),
                    "tier3_paths": len(tier3_files),
                    "tier3_ref_paths": len(tier3_referenced_files),
                },
            )

        return context.with_update(
            loaded_entities=loaded_entities,
            entities_with_cores=entities_with_cores,
            entities_with_archetypes=entities_with_archetypes,
            archetype_categories=archetype_categories,
            entities_with_modifiers=entities_with_modifiers,
            in_scene_entities=in_scene_entities,
            referenced_entities=referenced_entities,
            tier3_files=tier3_files,
            tier3_referenced_files=tier3_referenced_files,
        )

    # ------------------------------------------------------------------
    # Template helpers

    def generate_entity_card_template(self, name: str, entity_type: EntityType) -> str:
        return self._templates.render_entity_card(name, entity_type)

    def generate_character_preferences_template(self, name: str) -> dict[str, Any]:
        return self._templates.render_character_preferences(name)

    # ------------------------------------------------------------------
    # Preference generation

    def generate_character_preferences(self, character_name: str) -> PreferenceResult:
        """Generate AI-powered relationship preferences for a character.

        Uses the PreferenceGenerator to analyze a character's personality core
        and generate structured preferences (likes, dislikes, hates).

        Args:
            character_name: Name of the character entity

        Returns:
            PreferenceResult with generated preferences

        Raises:
            ValueError: If preference generator not configured or character not found
            LLMAuthError: If LLM authentication fails
            LLMError: If LLM request fails
        """
        if self._preference_generator is None:
            raise ValueError(
                "Preference generator not configured. Pass preference_generator to EntityService.__init__."
            )

        character = self.get_character(character_name)
        if character is None:
            raise ValueError(f"Character '{character_name}' not found")

        # Convert CharacterEntity to EntityCard
        from pathlib import Path

        from .models import EntityCard

        # Extract personality core from personality section (first try core_mandate, then full section)
        personality_core = character.core_mandate
        if not personality_core and character.personality:
            # If no core_mandate, use full personality as fallback
            personality_core = str(character.personality)

        entity_card = EntityCard(
            name=character.name,
            entity_type=EntityType.CHARACTER,
            file_path=Path(
                f"/entities/character_{character.name.lower()}.json"
            ),  # Placeholder path
            triggers=character.metadata.get("tags", []),
            full_content="",  # Not needed for preference generation
            personality_core=personality_core,
            metadata=dict(character.metadata),
            sections={
                "basics": character.basics,
                "appearance": character.appearance,
                "personality": character.personality,
                "preferences": character.preferences,
                "abilities": character.abilities,
                "background": character.background,
            },
        )

        result = self._preference_generator.generate(entity_card)
        self._log_debug(
            "entity.generate_preferences",
            {"character": character_name, "source": result.source},
        )
        return result

    # ------------------------------------------------------------------
    # Mutating helpers (delegate to repository)

    def save_character(self, character: CharacterEntity) -> CharacterEntity:
        saved = self._repository.save_character(character)
        self._log_debug("entity.save_character", {"name": character.name})
        return saved

    def append_memory_entry(self, character_name: str, entry: dict[str, object]) -> MemoryLog:
        log = self._repository.append_memory_entry(character_name, entry)
        self._log_debug(
            "entity.append_memory", {"character": character_name, "entry_id": entry.get("id")}
        )
        return log

    # ------------------------------------------------------------------

    def _log_debug(self, message: str, context: dict[str, object]) -> None:
        if self._logger is not None:
            self._logger.debug(message, context=context)
