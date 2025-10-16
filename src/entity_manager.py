"""
Entity Card Management System
Handles loading, parsing, and indexing of entity cards (characters, locations, organizations).
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.file_manager import FileManager
from src.state_templates import StateTemplates
from src.clients.deepseek import call_deepseek, MissingAPIKeyError


class EntityType(Enum):
    """Entity type enumeration."""
    CHARACTER = "character"
    LOCATION = "location"
    ORGANIZATION = "organization"
    UNKNOWN = "unknown"


@dataclass
class EntityCard:
    """
    Represents a parsed entity card.
    """
    name: str
    entity_type: EntityType
    file_path: Path
    triggers: List[str]  # Keywords that trigger this entity
    full_content: str  # Complete markdown content
    personality_core: Optional[str]  # Extracted Personality Core section
    metadata: Dict[str, Any]  # Parsed metadata fields
    sections: Dict[str, str]  # Parsed sections (Description, Personality, etc.)


class EntityManager:
    """
    Manages entity cards: loading, parsing, indexing, and retrieval.
    """

    def __init__(self, rp_dir: Path):
        """
        Initialize EntityManager.

        Args:
            rp_dir: Path to RP directory
        """
        self.rp_dir = Path(rp_dir)
        self.fm = FileManager(rp_dir)

        # Entity storage
        self.entities: Dict[str, EntityCard] = {}  # name -> EntityCard
        self.entities_by_type: Dict[EntityType, List[str]] = {
            EntityType.CHARACTER: [],
            EntityType.LOCATION: [],
            EntityType.ORGANIZATION: [],
            EntityType.UNKNOWN: []
        }
        self.trigger_map: Dict[str, str] = {}  # trigger -> entity name

        # Entity directories
        self.entity_dirs = [
            self.rp_dir / "entities",
            self.rp_dir / "characters"  # Legacy support
        ]

    def scan_and_index(self) -> None:
        """
        Scan entity directories and index all entity cards.
        """
        for entity_dir in self.entity_dirs:
            if not entity_dir.exists():
                continue

            # Find all markdown files
            entity_files = self.fm.list_files(entity_dir, pattern="*.md")

            for entity_file in entity_files:
                try:
                    entity_card = self._parse_entity_file(entity_file)
                    self._index_entity(entity_card)
                except Exception as e:
                    print(f"⚠️  Error parsing entity file {entity_file.name}: {e}")

    def _parse_entity_file(self, file_path: Path) -> EntityCard:
        """
        Parse an entity card file.

        Args:
            file_path: Path to entity file

        Returns:
            Parsed EntityCard
        """
        content = self.fm.read_markdown(file_path)

        # Extract entity name and type from filename or content
        name, entity_type = self._extract_name_and_type(file_path, content)

        # Extract triggers
        triggers = self._extract_triggers(content)

        # Extract personality core (if exists)
        personality_core = self._extract_personality_core(content)

        # Extract metadata fields
        metadata = self._extract_metadata(content)

        # Parse sections
        sections = self._parse_sections(content)

        return EntityCard(
            name=name,
            entity_type=entity_type,
            file_path=file_path,
            triggers=triggers,
            full_content=content,
            personality_core=personality_core,
            metadata=metadata,
            sections=sections
        )

    def _extract_name_and_type(self, file_path: Path, content: str) -> Tuple[str, EntityType]:
        """
        Extract entity name and type from filename or content.

        Args:
            file_path: Path to entity file
            content: File content

        Returns:
            Tuple of (name, entity_type)
        """
        filename = file_path.stem  # Without .md extension

        # Check for [CHAR], [LOC], [ORG] tags in filename
        tag_pattern = r'^\[(CHAR|LOC|ORG)\]\s*(.+)$'
        match = re.match(tag_pattern, filename)

        if match:
            tag, name = match.groups()
            entity_type_map = {
                'CHAR': EntityType.CHARACTER,
                'LOC': EntityType.LOCATION,
                'ORG': EntityType.ORGANIZATION
            }
            return name.strip(), entity_type_map[tag]

        # Check for [CHAR], [LOC], [ORG] tags in content
        content_tag_pattern = r'^\s*#\s*\[(CHAR|LOC|ORG)\]\s*(.+)$'
        match = re.search(content_tag_pattern, content, re.MULTILINE)

        if match:
            tag, name = match.groups()
            entity_type_map = {
                'CHAR': EntityType.CHARACTER,
                'LOC': EntityType.LOCATION,
                'ORG': EntityType.ORGANIZATION
            }
            return name.strip(), entity_type_map[tag]

        # Check for **Type**: in metadata
        type_pattern = r'\*\*Type\*\*:\s*(\w+)'
        match = re.search(type_pattern, content, re.IGNORECASE)

        if match:
            type_value = match.group(1).lower()
            if 'char' in type_value or 'npc' in type_value:
                entity_type = EntityType.CHARACTER
            elif 'loc' in type_value:
                entity_type = EntityType.LOCATION
            elif 'org' in type_value:
                entity_type = EntityType.ORGANIZATION
            else:
                entity_type = EntityType.UNKNOWN
        else:
            entity_type = EntityType.UNKNOWN

        # Extract name from first heading
        heading_pattern = r'^#\s+(.+)$'
        match = re.search(heading_pattern, content, re.MULTILINE)

        if match:
            name = match.group(1).strip()
            # Remove [CHAR], [LOC], [ORG] tags if present
            name = re.sub(r'^\[(CHAR|LOC|ORG)\]\s*', '', name).strip()
        else:
            # Use filename as fallback
            name = filename

        return name, entity_type

    def _extract_triggers(self, content: str) -> List[str]:
        """
        Extract trigger keywords from [Triggers:...] line.

        Args:
            content: File content

        Returns:
            List of trigger keywords
        """
        # Pattern: [Triggers:keyword1,keyword2,keyword3]
        pattern = r'\[Triggers:([^\]]+)\]'
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            triggers_str = match.group(1)
            # Split by comma and clean
            triggers = [t.strip().strip("'\"") for t in triggers_str.split(',')]
            return [t for t in triggers if t]  # Remove empty strings

        return []

    def _extract_personality_core(self, content: str) -> Optional[str]:
        """
        Extract Personality Core section (if exists).

        Args:
            content: File content

        Returns:
            Personality Core section content or None
        """
        # Pattern: ## PERSONALITY CORE ... (everything until next ## heading or end)
        pattern = r'##\s+PERSONALITY CORE.*?\n(.*?)(?=\n##\s+[A-Z]|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(0).strip()  # Include the heading

        return None

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata fields like **Type**: character, **Age**: 25, etc.

        Args:
            content: File content

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Pattern: **Field**: Value
        pattern = r'\*\*([^*]+)\*\*:\s*([^\n]+)'
        matches = re.finditer(pattern, content)

        for match in matches:
            field = match.group(1).strip().lower().replace(' ', '_')
            value = match.group(2).strip()
            metadata[field] = value

        return metadata

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse markdown sections (## Heading).

        Args:
            content: File content

        Returns:
            Dictionary of section_name -> section_content
        """
        sections = {}

        # Split by ## headings
        section_pattern = r'##\s+([^\n]+)\n(.*?)(?=\n##\s+|\Z)'
        matches = re.finditer(section_pattern, content, re.DOTALL)

        for match in matches:
            section_name = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[section_name] = section_content

        return sections

    def _index_entity(self, entity_card: EntityCard) -> None:
        """
        Add entity to indexes.

        Args:
            entity_card: EntityCard to index
        """
        # Store entity
        self.entities[entity_card.name] = entity_card

        # Index by type
        if entity_card.entity_type in self.entities_by_type:
            self.entities_by_type[entity_card.entity_type].append(entity_card.name)

        # Index triggers
        for trigger in entity_card.triggers:
            trigger_lower = trigger.lower()
            self.trigger_map[trigger_lower] = entity_card.name

        # Also index entity name itself as a trigger
        self.trigger_map[entity_card.name.lower()] = entity_card.name

    def get_entity(self, name: str) -> Optional[EntityCard]:
        """
        Get entity by name.

        Args:
            name: Entity name

        Returns:
            EntityCard or None
        """
        return self.entities.get(name)

    def get_entities_by_type(self, entity_type: EntityType) -> List[EntityCard]:
        """
        Get all entities of a specific type.

        Args:
            entity_type: Entity type to filter by

        Returns:
            List of EntityCards
        """
        names = self.entities_by_type.get(entity_type, [])
        return [self.entities[name] for name in names if name in self.entities]

    def detect_mentioned_entities(self, text: str) -> Set[str]:
        """
        Detect which entities are mentioned in text based on triggers.

        Args:
            text: Text to analyze

        Returns:
            Set of entity names mentioned
        """
        text_lower = text.lower()
        mentioned = set()

        for trigger, entity_name in self.trigger_map.items():
            if trigger in text_lower:
                mentioned.add(entity_name)

        return mentioned

    def load_entity_card(self, name: str, highlight_core: bool = True) -> Optional[str]:
        """
        Load entity card content for inclusion in prompt.

        Args:
            name: Entity name
            highlight_core: If True, highlight Personality Core section

        Returns:
            Formatted entity card content or None
        """
        entity = self.get_entity(name)

        if not entity:
            return None

        if not entity.personality_core or not highlight_core:
            # No personality core or highlighting disabled, return full content
            return entity.full_content

        # Highlight personality core
        highlighted = f"""## {entity.name} - ENTITY CARD

### ⚠️ PERSONALITY CORE (LOCKED - MUST FOLLOW)
{entity.personality_core}

---

### Full Character Details
{self._get_non_core_content(entity)}
"""
        return highlighted

    def _get_non_core_content(self, entity: EntityCard) -> str:
        """
        Get entity content excluding Personality Core section.

        Args:
            entity: EntityCard

        Returns:
            Content without Personality Core
        """
        content = entity.full_content

        if entity.personality_core:
            # Remove personality core section
            core_pattern = r'##\s+PERSONALITY CORE.*?\n.*?(?=\n##\s+[A-Z]|\Z)'
            content = re.sub(core_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)

        return content.strip()

    def load_multiple_entities(
        self,
        entity_names: List[str],
        highlight_cores: bool = True
    ) -> str:
        """
        Load multiple entity cards for inclusion in prompt.

        Args:
            entity_names: List of entity names to load
            highlight_cores: If True, highlight Personality Core sections

        Returns:
            Combined entity card content
        """
        cards = []

        for name in entity_names:
            card = self.load_entity_card(name, highlight_core=highlight_cores)
            if card:
                cards.append(card)

        return "\n\n---\n\n".join(cards)

    def get_characters(self) -> List[EntityCard]:
        """Get all character entities."""
        return self.get_entities_by_type(EntityType.CHARACTER)

    def get_locations(self) -> List[EntityCard]:
        """Get all location entities."""
        return self.get_entities_by_type(EntityType.LOCATION)

    def get_organizations(self) -> List[EntityCard]:
        """Get all organization entities."""
        return self.get_entities_by_type(EntityType.ORGANIZATION)

    def get_entity_summary(self) -> Dict[str, Any]:
        """
        Get summary of all indexed entities.

        Returns:
            Summary dictionary
        """
        return {
            "total_entities": len(self.entities),
            "by_type": {
                "characters": len(self.entities_by_type[EntityType.CHARACTER]),
                "locations": len(self.entities_by_type[EntityType.LOCATION]),
                "organizations": len(self.entities_by_type[EntityType.ORGANIZATION]),
                "unknown": len(self.entities_by_type[EntityType.UNKNOWN])
            },
            "total_triggers": len(self.trigger_map),
            "entities_with_personality_core": sum(
                1 for e in self.entities.values() if e.personality_core
            )
        }

    def create_entity_card(
        self,
        name: str,
        entity_type: EntityType,
        content: Optional[str] = None
    ) -> Path:
        """
        Create a new entity card file.

        Args:
            name: Entity name
            entity_type: Entity type
            content: Optional custom content (uses template if not provided)

        Returns:
            Path to created file
        """
        from state_templates import StateTemplates

        # Determine filename
        type_tags = {
            EntityType.CHARACTER: "CHAR",
            EntityType.LOCATION: "LOC",
            EntityType.ORGANIZATION: "ORG"
        }
        tag = type_tags.get(entity_type, "ENTITY")
        filename = f"[{tag}] {name}.md"
        file_path = self.rp_dir / "entities" / filename

        # Generate content if not provided
        if content is None:
            type_map = {
                EntityType.CHARACTER: "character",
                EntityType.LOCATION: "location",
                EntityType.ORGANIZATION: "organization"
            }
            content = StateTemplates.entity_card_template(
                name,
                type_map.get(entity_type, "character")
            )

        # Write file
        self.fm.write_markdown(file_path, content)

        # Re-index to include new entity
        entity_card = self._parse_entity_file(file_path)
        self._index_entity(entity_card)

        return file_path

    def reload_entity(self, name: str) -> bool:
        """
        Reload an entity card from disk (if it was modified).

        Args:
            name: Entity name

        Returns:
            True if reloaded successfully
        """
        entity = self.get_entity(name)

        if not entity:
            return False

        try:
            # Re-parse file
            updated_entity = self._parse_entity_file(entity.file_path)

            # Update in storage
            self.entities[name] = updated_entity

            # Re-index triggers
            for trigger in entity.triggers:
                trigger_lower = trigger.lower()
                if trigger_lower in self.trigger_map:
                    del self.trigger_map[trigger_lower]

            for trigger in updated_entity.triggers:
                trigger_lower = trigger.lower()
                self.trigger_map[trigger_lower] = updated_entity.name

            return True

        except Exception as e:
            print(f"⚠️  Error reloading entity {name}: {e}")
            return False

    def create_preference_file(self, character_name: str) -> bool:
        """
        Create a relationship preference file for a character.

        This generates a preferences JSON template file that defines what traits
        the character likes, dislikes, and hates. Works for ANY character,
        regardless of whether they have a Personality Core.

        Args:
            character_name: Name of the character

        Returns:
            True if preference file created successfully, False otherwise
        """
        # Ensure relationships directory exists
        relationships_dir = self.rp_dir / "relationships"
        relationships_dir.mkdir(exist_ok=True)

        # Check if file already exists
        preference_file = relationships_dir / f"{character_name}_preferences.json"
        if preference_file.exists():
            print(f"ℹ️  Preference file already exists for {character_name}")
            return True

        # Generate preference file using template
        preference_data = StateTemplates.character_preferences(character_name)

        # Save to file
        try:
            self.fm.write_json(preference_file, preference_data)
            print(f"✅ Created preference file for {character_name}: {preference_file.name}")
            print(f"   📝 Edit this file to define what {character_name} likes/dislikes/hates")
            return True
        except Exception as e:
            print(f"❌ Error creating preference file for {character_name}: {e}")
            return False

    def auto_generate_preferences(self, character_name: str) -> bool:
        """
        Auto-generate relationship preferences using DeepSeek analysis of Personality Core.

        This uses DeepSeek to analyze a character's Personality Core and automatically
        generate appropriate likes, dislikes, and hates based on their personality.

        Args:
            character_name: Name of the character

        Returns:
            True if preferences generated successfully, False otherwise
        """
        # Get character entity
        entity = self.get_entity(character_name)
        if not entity:
            print(f"❌ Character '{character_name}' not found")
            return False

        if not entity.personality_core:
            print(f"⚠️  Character '{character_name}' has no Personality Core - cannot auto-generate preferences")
            print(f"   Add a Personality Core section to the entity card first")
            return False

        # Ensure relationships directory exists
        relationships_dir = self.rp_dir / "relationships"
        relationships_dir.mkdir(exist_ok=True)

        preference_file = relationships_dir / f"{character_name}_preferences.json"

        print(f"🤖 Analyzing {character_name}'s personality to generate preferences...")

        # Create prompt for DeepSeek
        prompt = f"""Analyze this character's Personality Core and generate relationship preferences.

**Character Name**: {character_name}

**Personality Core**:
{entity.personality_core}

**Task**: Based on this personality, generate a list of traits this character would like, dislike, and hate in relationships with others.

**Guidelines**:
- Be specific to THIS character's personality (not generic traits)
- Consider their core values, flaws, speaking style, and behaviors
- Likes should have +5 to +15 points (most important values get higher points)
- Dislikes should have -5 to -10 points
- Hates should have -20 to -30 points (dealbreakers only)
- Include 3-5 items in each category
- Each item should have a "trait" and a "reason" explaining why based on personality

Return ONLY valid JSON in this exact format:
{{
  "likes": [
    {{"trait": "trait_name", "points": 10, "reason": "why this character values this"}},
    ...
  ],
  "dislikes": [
    {{"trait": "trait_name", "points": -5, "reason": "why this bothers this character"}},
    ...
  ],
  "hates": [
    {{"trait": "trait_name", "points": -25, "reason": "why this is a dealbreaker"}},
    ...
  ]
}}"""

        try:
            # Query DeepSeek
            response = call_deepseek(
                prompt=prompt,
                rp_dir=self.rp_dir,
                max_tokens=2000,
                temperature=0.3
            )

            # Parse JSON response
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                print(f"❌ DeepSeek response was not valid JSON")
                return False

            preferences_data = json.loads(json_match.group())

            # Validate structure
            required_keys = ["likes", "dislikes", "hates"]
            if not all(key in preferences_data for key in required_keys):
                print(f"❌ Generated preferences missing required keys")
                return False

            # Build full preference file
            full_preferences = {
                "character_name": character_name,
                "preferences": preferences_data,
                "baseline_disposition": 0,
                "notes": f"Auto-generated from Personality Core using DeepSeek analysis",
                "generated_at": json.dumps({"timestamp": "auto-generated"})
            }

            # Save to file
            self.fm.write_json(preference_file, full_preferences)
            print(f"✅ Auto-generated preferences for {character_name}!")
            print(f"   📝 Saved to: {preference_file.name}")
            print(f"   Likes: {len(preferences_data['likes'])} traits")
            print(f"   Dislikes: {len(preferences_data['dislikes'])} traits")
            print(f"   Hates: {len(preferences_data['hates'])} traits")
            print(f"   💡 Review and adjust the file as needed")

            return True

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse DeepSeek response as JSON: {e}")
            print(f"   Response: {response[:200]}...")
            return False
        except MissingAPIKeyError as e:
            print(f"❌ {e}")
            print(f"   Set OPENROUTER_API_KEY environment variable or add to config.json")
            return False
        except Exception as e:
            print(f"❌ Error generating preferences: {e}")
            import traceback
            traceback.print_exc()
            return False
