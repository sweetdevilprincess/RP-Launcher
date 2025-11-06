# Workstream B Remaining Tasks

- [x] Snapshot legacy FileManager behaviours with integration tests (counter, IPC, backups).
- [x] Introduce `IpcChannel` abstraction with schema validation around IPC payloads.
- [x] Inventory legacy copy/migration helpers (no additional helpers beyond backup identified).
- [x] Introduce TemplateRenderer/StateTemplateService and begin migrating story arc & entity card helpers.
- [x] Update automation/domain call sites to rely on `FileAccessService` and tiered loaders (automation service consumes tiered context; session service provides cached agent data).
- [x] Confirm whether additional filesystem migrations (session/entity scripts) are required once Workstream C session layer is drafted (no further migrations identified; tracked via session/domain plans).
