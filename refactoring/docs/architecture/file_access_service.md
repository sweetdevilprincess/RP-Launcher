# FileAccessService Overview

The `FileAccessService` coordinates higher-level filesystem workflows by composing the low-level `FileManager` with the data-driven `TieredFileLoader`.

## Responsibilities
- Provide tiered bundle loading APIs (`load_tiered_context`, `load_all_bundles`) for automation/domain layers.
- Delegate counter/IPC/backup operations to the underlying `FileManager` without exposing raw filesystem details.
- Centralise logging for complex file workflows.

## Construction
```python
from refactoring.src.infrastructure.filesystem import (
    FileAccessService,
    FileManager,
    TieredFileLoader,
    FileWriteQueue,
    JsonStore,
    MarkdownStore,
    StatePaths,
)

paths = StatePaths(rp_dir=rp_path)
json_store = JsonStore(root=paths.state_dir, logger=logger)
markdown_store = MarkdownStore(root=paths.rp_dir, logger=logger)
write_queue = FileWriteQueue(queue=get_write_queue(), logger=logger)
file_manager = FileManager(
    paths=paths,
    json_store=json_store,
    markdown_store=markdown_store,
    write_queue=write_queue,
    logger=logger,
)
tier_loader = TieredFileLoader.from_default_config(
    paths=paths,
    markdown_store=markdown_store,
    logger=logger,
)
file_access = FileAccessService(
    file_manager=file_manager,
    tier_loader=tier_loader,
    logger=logger,
)
```

## Typical Usage
```python
context = file_access.load_tiered_context(
    response_count=42,
    triggered_files=[pathlib.Path("state/triggers/alert.md")],
)
for result in context.tier1.values():
    render(result.files)
```

## Future Work
- Extend `TieredContext` with richer metadata (entity cues, story arc summaries).
- Add helpers for state snapshots or archived backups.
- Expose async/queued variants if the automation pipeline adopts concurrency.
