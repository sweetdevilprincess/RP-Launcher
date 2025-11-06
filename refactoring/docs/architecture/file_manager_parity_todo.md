# FileManager Parity Checklist

This note tracks legacy `src/file_manager.py` functionality that still needs migration or confirmation in the refactored infrastructure layer.

## JSON & IPC
- [x] `read_json` / `write_json` -> `JsonStore` + FileManager wrappers
- [x] `update_json` -> `JsonStore.merge`
- [x] IPC write/read/migration -> `FileManager.write_ipc_input`, `read_ipc_input`, `ensure_ipc_migration`
- [x] IPC response read/write -> `FileManager.write_ipc_response`, `read_ipc_response`
- [x] Session triggers read/write -> `FileManager.read_session_triggers`, `.write_session_triggers`

## Counters & Queues
- [x] Response counter increment/read/write -> refactored FileManager + `FileAccessService`
- [x] Write queue facade -> `FileWriteQueue`

## Tiered Loading
- [x] Tiers powered by `TieredFileLoader` and `FileAccessService`
- [ ] Deeper entity metadata parsing deferred to domain services (captured in Workstream C plan)

## Markdown & Narrative Files
- [x] Markdown read/write/append -> `MarkdownStore`
- [x] Chapter/memory helper paths -> `StatePaths` helpers exposed via FileManager
- [x] Character/state file helpers -> `FileManager.character_file`, `.state_file`
- [ ] Template-backed helpers (e.g., story arc regeneration) to be evaluated during domain migration

## Backups & Metadata
- [x] `backup_file` -> refactored FileManager
- [x] Metadata/time change checks -> `FileManager.get_file_metadata`, `.has_file_changed`
- [x] Directory/file existence + listings -> `FileManager.directory_exists`, `.file_exists`, `.list_files`

## Copy/Directory Utilities
- [ ] Legacy cloning/copy helpers (`copy_directory`, `copy_entity_files`, if still used) pending evaluation
- [ ] Migration scripts (if any) for session/entity structures pending evaluation

## Notes
- Many legacy convenience functions were one-liners around `_resolve_path`; verify consumers and consider moving them to dedicated services instead of bloating FileManager.
- Tiered loader metadata (entity core detection) now surfaces entity file info; deep entity parsing will shift to the upcoming domain services.
