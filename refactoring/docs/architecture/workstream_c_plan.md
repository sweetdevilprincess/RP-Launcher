# Workstream C Plan (Entity Domain)

## Objectives
- Preserve current entity/session behaviour while introducing clearer boundaries and testable abstractions.
- Move parsing and repository logic out of monolithic `entity_manager.py` into dedicated modules.
- Provide fixtures/tests to lock in behaviour before major migrations.

## Phases

1. **Baseline & Fixtures**
   - [x] Snapshot key entity cards and DeepSeek responses for fixture-based tests (`tests/entities/fixtures`).
   - [x] Identify critical behaviours in `entity_manager.py` (parsing, caching, preference generation).

2. **Parsing Layer**
   - [x] Extract parsing logic into `refactoring/src/domain/entities/entity_parser.py` with unit tests (triggers, metadata, sections).
   - [x] Define data classes/models representing entity structure.

3. **Repository Layer**
   - [x] Implement `EntityRepository` (fixture-backed version for testing).
   - [x] Provide methods for listing entities, loading by name, writing updates.

4. **Service Layer**
   - [x] Introduce `EntityService` orchestrating parser + repository (initial fixture-backed version).
   - [x] Integrate preference generation behind `PreferenceGenerator` interface.

5. **Integration & Tests**
   - [x] Update automation/domain call sites to use new service stack (already integrated via factory).
   - [x] Add fixture-based tests verifying preference generation (25 tests passing).
   - [x] Add fixture-based tests for entity parsing (22 tests passing).
   - [x] Add fixture-based tests for repository operations (31 tests passing).
   - [x] Document deprecation plan for legacy `entity_manager.py`.

## Dependencies & Notes
- Coordinate with Workstream B for any remaining filesystem needs (e.g., entity copy helpers).
- Ensure tests run against refactoring namespace without touching legacy code.
- Document new module layout in `refactoring/docs/entities/README.md` once implemented.
