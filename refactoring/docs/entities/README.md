# Entity Domain Documentation

**Workstream:** C (Entity Domain)
**Status:** ✅ Complete
**Tests:** 78 passing (100% coverage)

---

## Overview

The entity domain provides a clean, testable architecture for managing all RP entities (characters, locations, organizations, items, memories). It replaces the monolithic `entity_manager.py` with a modular, protocol-based design.

---

## Architecture

```
EntityService (orchestrator)
├── EntityRepository (storage abstraction)
│   └── FixtureEntityRepository (JSON file implementation)
├── Parser layer (entity_parser.py)
│   ├── parse_character()
│   ├── parse_location()
│   ├── parse_organization()
│   ├── parse_item()
│   └── parse_memories()
├── PreferenceGenerator (protocol-based)
│   └── LLMPreferenceGenerator (uses any LLMClient)
└── StateTemplateService (template generation)
```

---

## Components

### EntityService (`src/domain/entities/entity_service.py`)

Main orchestration service that coordinates entity operations.

**Responsibilities**:
- Load and save entities via repository
- Detect entity mentions in text
- Generate character preferences
- Coordinate state templates

**Usage**:
```python
from refactoring.src.domain.entities import EntityService, FixtureEntityRepository

repository = FixtureEntityRepository(base_dir=rp_dir)
service = EntityService(repository=repository)

# Load character
character = service.get_character("Alice")

# Detect mentions
mentioned = service.detect_mentions("Alice met Bob in Tavern")
# Returns: ["Alice", "Bob", "Tavern"]
```

### EntityRepository (`src/domain/entities/entity_repository.py`)

Storage abstraction for entity persistence.

**Implementations**:
- **FixtureEntityRepository**: JSON file-based storage (production)
- **InMemoryEntityRepository**: In-memory storage (testing)

**API**:
```python
# Characters
character = repository.get_character("Alice")
repository.save_character(character_data)
all_characters = repository.list_characters()

# Locations
location = repository.get_location("Tavern")
repository.save_location(location_data)

# Organizations
org = repository.get_organization("Guild")
repository.save_organization(org_data)

# Items
item = repository.get_item("Sword")
repository.save_item(item_data)

# Memories
memories = repository.get_memory_log("Alice")
repository.append_memory_entry("Alice", memory_entry)
```

### EntityParser (`src/domain/entities/entity_parser.py`)

Parsing functions for converting raw data to structured entities.

**Functions**:
```python
from refactoring.src.domain.entities.entity_parser import (
    parse_character,
    parse_location,
    parse_organization,
    parse_item,
    parse_memories,
)

# Parse character data
character_data = {"name": "Alice", "basics": {...}, ...}
parsed = parse_character(character_data)

# Parse memory log
memories_data = [{"tags": ["meeting"], "summary": "...", ...}]
parsed_memories = parse_memories(memories_data)
```

**Validation**: Each parser validates required fields and structure.

### PreferenceGenerator (`src/domain/entities/preference_generator.py`)

Multi-provider preference generation for characters.

**Implementations**:
- **LLMPreferenceGenerator**: Uses any LLMClient (Claude, OpenAI, etc.)
- **CachedPreferenceGenerator**: Caching wrapper (future)

**Usage**:
```python
from refactoring.src.infrastructure.llm.registry import get_provider
from refactoring.src.domain.entities import LLMPreferenceGenerator

# Create LLM client (any provider)
provider_spec = get_provider("anthropic_api")
llm_client = provider_spec.factory(config)

# Create generator
generator = LLMPreferenceGenerator(client=llm_client)

# Generate preferences
entity_card = EntityCard(
    name="Alice",
    entity_type=EntityType.CHARACTER,
    data=character_data,
)
result = generator.generate(entity_card)

# Access preferences
print(result.preferences)  # Dict of entity -> preference score
print(result.metadata)     # Generation metadata
```

---

## Entity Data Models

### CharacterEntity

```python
from refactoring.src.domain.entities.models import CharacterEntity

character = CharacterEntity(
    name="Alice",
    basics={
        "age": "25",
        "gender": "female",
        "species": "human",
    },
    appearance={
        "height": "5'6\"",
        "build": "athletic",
        "features": ["blue eyes", "blonde hair"],
    },
    personality={
        "core_mandate": "Alice is brave and curious",
        "traits": ["brave", "curious", "kind"],
        "likes": ["adventure", "books"],
        "dislikes": ["injustice", "boredom"],
    },
    preferences={
        "Bob": 0.8,
        "Charlie": -0.2,
    },
    abilities=["swordsmanship", "magic"],
    background="Alice grew up in...",
    metadata={
        "related_locations": ["Hometown", "Academy"],
        "related_organizations": ["Guild"],
        "related_items": ["Sword"],
    },
)
```

### LocationEntity

```python
from refactoring.src.domain.entities.models import LocationEntity

location = LocationEntity(
    name="Tavern",
    basics={
        "type": "building",
        "region": "City Center",
    },
    geography={
        "climate": "temperate",
        "terrain": "urban",
    },
    facilities=["bar", "rooms", "kitchen"],
    culture={
        "customs": ["no fighting"],
        "notable_residents": ["Bartender"],
    },
    hooks=["mysterious stranger appears"],
    metadata={
        "related_characters": ["Bartender", "Alice"],
        "related_organizations": ["Tavern Guild"],
    },
)
```

### OrganizationEntity

```python
from refactoring.src.domain.entities.models import OrganizationEntity

org = OrganizationEntity(
    name="Guild",
    basics={
        "type": "professional",
        "size": "large",
    },
    structure={
        "leadership": ["Guildmaster"],
        "ranks": ["Initiate", "Member", "Master"],
    },
    resources={"funds": 10000, "facilities": ["Guildhall"]},
    relations={
        "allies": ["City Council"],
        "rivals": ["Thieves Guild"],
    },
    metadata={
        "related_characters": ["Guildmaster", "Alice"],
        "related_locations": ["Guildhall"],
    },
)
```

### ItemEntity

```python
from refactoring.src.domain.entities.models import ItemEntity

item = ItemEntity(
    name="Sword",
    basics={
        "type": "weapon",
        "rarity": "uncommon",
    },
    properties={
        "damage": "1d8",
        "material": "steel",
    },
    owner="Alice",
    metadata={
        "related_characters": ["Alice"],
        "related_locations": ["Armory"],
    },
)
```

---

## Fixtures for Testing

Test fixtures are located in `refactoring/tests/entities/fixtures/`.

### Available Fixtures

- **`character_aurora.json`**: Detailed character profile
- **`Aurora_Lys_memories.json`**: Memory log for Aurora & Lys
- **`location_celestia.json`**: Location profile
- **`organization_elysian_alliance.json`**: Organization profile
- **`item_harmonic_resonator.json`**: Item profile
- **`deepseek_preference_response.json`**: Mocked LLM response

### Using Fixtures in Tests

```python
from refactoring.src.domain.entities.fixtures import load_character_fixture

def test_character_loading():
    character_data = load_character_fixture("aurora")
    assert character_data["name"] == "Aurora Lys"
    assert "personality" in character_data
```

---

## Testing

**Test Organization**:
```
tests/domain/entities/
├── test_entity_parser.py (22 tests)
├── test_entity_repository.py (31 tests)
├── test_entity_service.py (8 tests)
└── test_preference_generator.py (17 tests)
```

**Total**: 78 tests, 100% passing

**Coverage**: 100% of entity domain code

**Running Tests**:
```bash
# All entity tests
python -m pytest tests/domain/entities/

# Specific test file
python -m pytest tests/domain/entities/test_entity_service.py

# With coverage
python -m pytest tests/domain/entities/ --cov=src/domain/entities --cov-report=html
```

---

## Migration from Legacy

For migrating from legacy `entity_manager.py`, see:
- **Migration Guide**: `docs/ENTITY_MANAGER_MIGRATION.md`
- **API Equivalence**: Entity domain provides drop-in replacements for all entity_manager functions
- **Timeline**: Gradual migration, legacy code continues working during transition

---

## Extension Points

### Adding a New Entity Type

1. **Define dataclass** in `src/domain/entities/models.py`:
   ```python
   @dataclass(frozen=True)
   class SpellEntity:
       name: str
       school: str
       level: int
       effects: list
       metadata: dict
   ```

2. **Add parser** in `src/domain/entities/entity_parser.py`:
   ```python
   def parse_spell(data: Dict[str, Any]) -> SpellEntity:
       # Validation and parsing
       return SpellEntity(
           name=data["name"],
           school=data["school"],
           level=data["level"],
           effects=data.get("effects", []),
           metadata=data.get("metadata", {}),
       )
   ```

3. **Add repository methods** in `src/domain/entities/entity_repository.py`:
   ```python
   def get_spell(self, name: str) -> SpellEntity:
       # Load from file system
       data = self._load_entity_file("spells", name)
       return parse_spell(data)

   def save_spell(self, spell: SpellEntity) -> None:
       # Save to file system
       self._save_entity_file("spells", spell.name, asdict(spell))
   ```

4. **Add tests** for parser and repository

5. **Update `EntityType` enum** in `src/shared/models.py`

### Adding a New Preference Generator

Implement the `PreferenceGenerator` protocol:

```python
from refactoring.src.domain.entities.preference_generator import PreferenceGenerator

class CustomPreferenceGenerator(PreferenceGenerator):
    def generate(self, entity: EntityCard) -> PreferenceResult:
        # Your custom logic
        preferences = {...}
        return PreferenceResult(
            preferences=preferences,
            metadata={"method": "custom"},
        )
```

---

## Dependencies

### Domain → Infrastructure

The entity domain depends on infrastructure for:
- **LLMClient**: For preference generation
- **LoggingService**: For logging (optional)

These are injected via constructor, keeping domain testable.

### Domain → Shared

Uses shared types:
- **EntityType** enum (`src/shared/models.py`)
- **Protocols** (`src/shared/interfaces/`)

---

## Performance Considerations

### Lazy Loading

Entities are loaded on-demand, not all at once:
```python
# Only loads when accessed
character = repository.get_character("Alice")
```

### Caching (Future)

Future enhancement: `CachedEntityRepository` wrapper
```python
repository = CachedEntityRepository(
    base_repository=FixtureEntityRepository(base_dir),
    cache_size=100,
)
```

### Preference Generation

LLM-based preference generation can be slow. Consider:
- Pre-generating preferences for main characters
- Caching preference results
- Using faster/cheaper LLM providers for preferences

---

## Troubleshooting

### Entity Not Found

**Error**: `EntityNotFoundError: Character 'Alice' not found`

**Solutions**:
- Check entity file exists: `entities/characters/alice.json`
- Verify entity name matches file name (case-insensitive)
- Check file is valid JSON

### Invalid Entity Structure

**Error**: `KeyError: 'personality'` when parsing character

**Solutions**:
- Ensure all required fields present in JSON
- Use `parse_character()` to validate structure
- Check fixture examples for correct format

### Preference Generation Fails

**Error**: LLM client timeout or error

**Solutions**:
- Check LLM client configuration
- Verify API key is valid
- Try different provider
- Check entity card has all required data

---

## Related Documentation

- **Architecture**: `docs/architecture/README.md`
- **Migration Guide**: `docs/ENTITY_MANAGER_MIGRATION.md`
- **Configuration**: `docs/CONFIGURATION_GUIDE.md`
- **Testing**: `docs/TOOLING.md`
- **Workstream C**: `docs/WORKSTREAM_C_COMPLETE.md`

---

## API Reference

### EntityService

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_character(name)` | `name: str` | `CharacterEntity` | Load character by name |
| `get_location(name)` | `name: str` | `LocationEntity` | Load location by name |
| `list_characters()` | - | `List[str]` | List all character names |
| `detect_mentions(text)` | `text: str` | `List[str]` | Find entity mentions in text |
| `generate_character_preferences(name)` | `name: str` | `PreferenceResult` | Generate preferences for character |

### EntityRepository

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_character(name)` | `name: str` | `Dict` | Load character data |
| `save_character(data)` | `data: Dict` | `None` | Save character data |
| `list_characters()` | - | `List[str]` | List character names |
| `get_memory_log(name)` | `name: str` | `List[Dict]` | Load memory log |
| `append_memory_entry(name, entry)` | `name: str, entry: Dict` | `None` | Add memory entry |

---

**Last Updated**: 2025-10-21
**Version**: 2.0.0
**Status**: Production Ready
