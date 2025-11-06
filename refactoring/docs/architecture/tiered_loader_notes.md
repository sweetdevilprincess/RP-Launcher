# Tiered Loader Notes

- Configuration lives in `refactoring/config/tiered_bundles.json` and defines bundles with `id`, `label`, `trigger`, and `entries`.
- `Trigger.type` values currently supported: `always`, `every_n_responses` (with `interval`), and `triggered` (requires caller-supplied file list).
- Entry types:
  - `path`: loads markdown/text from the specified `value`, scoped by `base` (`rp`, `state`, `config`).
  - `main_character`: loads the first character card that is not `{{user}}.md`.
  - `rp_overview`: loads the RP overview file (`<rp-name>.md`).
  - `triggered_paths`: loads caller-provided file paths.
- Loader returns `TieredLoadResult` objects with `files` (content keyed by relative path) and metadata, including:
  - `loaded_paths`: absolute path strings for each file.
  - `entry_count`: number of loaded files in the bundle.
  - `entities_with_cores`: list of entity names whose markdown contains “Personality Core”.
  - `entity_files`: list of entity file paths loaded during the bundle.
- Future enhancements:
  - Expand metadata with richer entity parsing once domain services migrate.
  - Support additional entry types (glob patterns, JSON payloads) and bundle-level limits.
  - Allow markdown-to-JSON transformations for structured prompts if needed.
