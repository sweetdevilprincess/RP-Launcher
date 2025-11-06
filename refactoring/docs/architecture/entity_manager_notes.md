# Legacy Entity Manager Notes

Key responsibilities identified in `src/entity_manager.py`:

- **File scanning/indexing**: `scan_and_index`, `_parse_entity_file`, `_index_entity` build in-memory maps of entity cards across characters/locations/organizations.
- **Parsing helpers**: `_extract_name_and_type`, `_extract_triggers`, `_extract_personality_core`, `_extract_metadata`, `_parse_sections` – these will move into `entity_parser.py`.
- **Retrieval APIs**: `get_entity`, `get_entities_by_type`, `detect_mentioned_entities`, `load_entity_card`, `load_multiple_entities`, `get_entity_summary`.
- **Creation/update flows**: `create_entity_card`, `reload_entity`, `create_preference_file`, `auto_generate_preferences`.
- **Dependencies**: relies on filesystem reads, manual regex parsing, DeepSeek preference generator, highlight logic for Personality Core.

Baseline fixture targets:
- At least one character card with Personality Core.
- One location/organization card.
- Sample DeepSeek response to drive preference generation.
- Text sample exercising `detect_mentioned_entities` trigger extraction.

These notes guide Phase 1 fixture capture and the parsing/repository refactor.
