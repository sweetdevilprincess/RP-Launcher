"""
Entity Manager Module

Wraps EntityManager for the module management system.
Handles entity card loading, parsing, indexing, and retrieval.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from entity_manager import EntityManager, EntityCard, EntityType


class EntityManagerModule(RPModule):
    """Module wrapper for EntityManager.

    Manages entity cards (characters, locations, organizations):
    - Loading and parsing markdown entity files
    - Indexing by name, type, and triggers
    - Detecting entity mentions in text
    - Creating and updating entity cards
    - Preference file management

    Dependencies: file_manager
    """

    # Module metadata
    name = "entity_manager"
    version = "1.0.0"
    description = "Entity card management for characters, locations, and organizations"
    dependencies: List[str] = ["file_manager"]  # Needs FileManager
    optional = False  # Core module for entity tracking

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize entity manager module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # Entity manager instance (created during initialize)
        self.entity_manager: Optional[EntityManager] = None

        # Configuration
        self.auto_scan = config.get('auto_scan', True)
        self.auto_generate_threshold = config.get('auto_generate_threshold', 3)

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize entity manager.

        Creates EntityManager and optionally scans entity directories.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create entity manager
            self.entity_manager = EntityManager(self.rp_dir)

            # Auto-scan if configured
            if self.auto_scan:
                self.entity_manager.scan_and_index()
                entity_count = len(self.entity_manager.entities)
                self.log_info(f"Indexed {entity_count} entities")

            self.log_info("Entity manager initialized successfully")
            return True

        except Exception as e:
            self.log_error("Failed to initialize entity manager", e)
            return False

    def start(self) -> bool:
        """Start entity manager.

        Entity manager is passive (no background tasks).

        Returns:
            True (always succeeds)
        """
        self.log_info("Entity manager started (passive module)")
        return True

    def stop(self) -> bool:
        """Stop entity manager.

        Entity manager is passive (nothing to stop).

        Returns:
            True (always succeeds)
        """
        self.log_info("Entity manager stopped")
        return True

    def cleanup(self) -> None:
        """Cleanup entity manager resources.

        Entity manager has no persistent resources to cleanup.
        """
        self.log_info("Entity manager cleanup complete")
        self.entity_manager = None

    # ==================== Entity Operations ====================

    def scan_and_index(self) -> None:
        """Scan entity directories and index all entity cards.

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        self.entity_manager.scan_and_index()

    def get_entity(self, name: str) -> Optional[EntityCard]:
        """Get entity by name.

        Args:
            name: Entity name

        Returns:
            EntityCard or None if not found

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_entity(name)

    def get_entities_by_type(self, entity_type: EntityType) -> List[EntityCard]:
        """Get all entities of a specific type.

        Args:
            entity_type: Type of entity

        Returns:
            List of EntityCards

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_entities_by_type(entity_type)

    def detect_mentioned_entities(self, text: str) -> Set[str]:
        """Detect entities mentioned in text.

        Args:
            text: Text to analyze

        Returns:
            Set of entity names mentioned

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.detect_mentioned_entities(text)

    def load_entity_card(self, name: str, highlight_core: bool = True) -> Optional[str]:
        """Load entity card content.

        Args:
            name: Entity name
            highlight_core: Highlight personality core section

        Returns:
            Entity card content or None

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.load_entity_card(name, highlight_core)

    def load_multiple_entities(
        self,
        entity_names: List[str],
        highlight_core: bool = True,
        join_separator: str = "\n\n---\n\n"
    ) -> str:
        """Load multiple entity cards.

        Args:
            entity_names: List of entity names
            highlight_core: Highlight personality cores
            join_separator: Separator between cards

        Returns:
            Joined entity cards content

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.load_multiple_entities(
            entity_names, highlight_core, join_separator
        )

    def get_characters(self) -> List[EntityCard]:
        """Get all character entities.

        Returns:
            List of character EntityCards

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_characters()

    def get_locations(self) -> List[EntityCard]:
        """Get all location entities.

        Returns:
            List of location EntityCards

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_locations()

    def get_organizations(self) -> List[EntityCard]:
        """Get all organization entities.

        Returns:
            List of organization EntityCards

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_organizations()

    def get_entity_summary(self) -> Dict[str, Any]:
        """Get summary of indexed entities.

        Returns:
            Summary dictionary

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.get_entity_summary()

    def create_entity_card(
        self,
        name: str,
        entity_type: EntityType,
        description: str,
        personality: Optional[str] = None,
        **additional_fields
    ) -> Path:
        """Create new entity card.

        Args:
            name: Entity name
            entity_type: Type of entity
            description: Entity description
            personality: Personality description (characters only)
            **additional_fields: Additional fields

        Returns:
            Path to created entity file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.create_entity_card(
            name, entity_type, description, personality, **additional_fields
        )

    def reload_entity(self, name: str) -> bool:
        """Reload entity from file.

        Args:
            name: Entity name

        Returns:
            True if reloaded successfully

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.reload_entity(name)

    def create_preference_file(self, character_name: str) -> bool:
        """Create preference file for character.

        Args:
            character_name: Character name

        Returns:
            True if created successfully

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.create_preference_file(character_name)

    def auto_generate_preferences(self, character_name: str) -> bool:
        """Auto-generate preferences using LLM.

        Args:
            character_name: Character name

        Returns:
            True if generated successfully

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")

        return self.entity_manager.auto_generate_preferences(character_name)

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle entity manager commands.

        Commands:
            status - Show entity manager status
            list - List all entities
            summary - Show entity summary
            scan - Rescan entity directories

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"Entity Manager v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")

            # Add entity counts if initialized
            if self.entity_manager:
                summary = self.get_entity_summary()
                lines.append(f"Total entities: {summary['total']}")
                lines.append(f"Characters: {summary['characters']}")
                lines.append(f"Locations: {summary['locations']}")
                lines.append(f"Organizations: {summary['organizations']}")

            return "\n".join(lines)

        elif command == "list":
            try:
                if not self.entity_manager:
                    return "Entity manager not initialized"

                lines = ["📋 Indexed Entities:"]
                for name, entity in self.entity_manager.entities.items():
                    type_icon = {
                        EntityType.CHARACTER: "👤",
                        EntityType.LOCATION: "📍",
                        EntityType.ORGANIZATION: "🏢",
                        EntityType.UNKNOWN: "❓"
                    }.get(entity.entity_type, "📄")

                    lines.append(f"  {type_icon} {name} ({entity.entity_type.value})")

                return "\n".join(lines)

            except Exception as e:
                return f"Error listing entities: {e}"

        elif command == "summary":
            try:
                if not self.entity_manager:
                    return "Entity manager not initialized"

                summary = self.get_entity_summary()
                lines = ["📊 Entity Summary:"]
                lines.append(f"  Total: {summary['total']}")
                lines.append(f"  Characters: {summary['characters']}")
                lines.append(f"  Locations: {summary['locations']}")
                lines.append(f"  Organizations: {summary['organizations']}")
                lines.append(f"  Triggers: {summary['total_triggers']}")

                return "\n".join(lines)

            except Exception as e:
                return f"Error getting summary: {e}"

        elif command == "scan":
            try:
                if not self.entity_manager:
                    return "Entity manager not initialized"

                before_count = len(self.entity_manager.entities)
                self.scan_and_index()
                after_count = len(self.entity_manager.entities)

                return f"✓ Rescanned entities (found {after_count}, {after_count - before_count:+d})"

            except Exception as e:
                return f"Error scanning entities: {e}"

        # Default to parent handler
        return super().handle_command(command, args)

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status with entity-specific info.

        Returns:
            Status dictionary
        """
        status = super().get_status()

        # Add entity-specific info
        if self.entity_manager:
            try:
                summary = self.get_entity_summary()
                status["entity_summary"] = summary
            except Exception:
                pass  # Ignore errors in status

        status["auto_scan"] = self.auto_scan
        status["auto_generate_threshold"] = self.auto_generate_threshold

        return status

    # ==================== Direct Access ====================

    def get_entity_manager(self) -> EntityManager:
        """Get the underlying EntityManager instance.

        For legacy code that needs direct access.

        Returns:
            EntityManager instance

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.entity_manager:
            raise RuntimeError("Entity manager not initialized")
        return self.entity_manager
