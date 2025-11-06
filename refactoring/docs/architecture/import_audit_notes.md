# Import Audit Notes

This document tracks the dependency audit tooling introduced for Workstream A.

- `refactoring/src/tools/import_audit.py` scans Python files under a given root (defaults to `refactoring/src`).
- The script enforces the layer rules defined in `refactoring/docs/architecture/README.md` by flagging imports that cross boundaries.
- Run it manually: `python refactoring/src/tools/import_audit.py` (optionally provide a path argument).
- Extend `INTERNAL_LAYERS` and `LAYER_RULES` within the script as new packages are added.
- Future improvement ideas:
  - Integrate with CI once refactored modules are promoted.
  - Add allowlists for migration periods when temporary violations are accepted.
  - Emit machine-readable output (JSON) for tooling ingestion.
