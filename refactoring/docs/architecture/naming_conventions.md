# Naming Conventions

To keep the refactored codebase consistent, we adopt the following naming scheme:

## Packages & Directories
- All top-level packages under `refactoring/src/` use lowercase snake_case (e.g., `automation`, `domain`, `infrastructure`, `shared`).
- Subpackages group by responsibility: `infrastructure/filesystem`, `infrastructure/transports`, `domain/entities`, etc.
- Tests for refactored code live under `refactoring/tests/<package>` mirroring the package path (to be added when tests are ported).

## Modules & Files
- Modules are lowercase snake_case describing their role (`file_manager.py`, `json_store.py`, `write_queue.py`).
- Façade or service wrappers use `_service.py` suffix (`automation_service.py`, `entity_service.py`).
- Protocol/interface definitions live in files ending with `_protocol.py` or `_interface.py` when multiple contracts coexist; single-class modules can retain the class name (`logging_service.py`).

## Classes & Types
- Classes and dataclasses use PascalCase (`FileManager`, `JsonStore`, `TransportResponse`).
- Protocols end with the suffix `Protocol` when a generic marker is helpful (e.g., `LoggingService` already conveys intent; no suffix needed).
- Exceptions end with `Error` (`TransportError`).

## Functions & Methods
- Functions and methods use snake_case, favouring verbs (`read_json`, `flush_queue`).
- Asynchronous utilities will use `async_` prefixes only when necessary to avoid keyword clashes.

## Constants & Enums
- Constants use UPPER_SNAKE_CASE (`DEFAULT_DEBOUNCE_MS`).
- Enum members use UPPER_SNAKE_CASE unless mirroring external values.

## File Paths & Namespaces
- Import paths should follow the layer boundaries defined in `architecture/README.md`.
- Shared code intended for multiple layers belongs in `refactoring/src/shared/`.

Keep this document updated as we introduce new patterns or folder groups.
