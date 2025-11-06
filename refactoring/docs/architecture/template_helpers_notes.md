# Template-Driven Helpers Inventory

Legacy modules relying on hard-coded templates:

- `src/state_templates.py`: generates markdown templates for plot threads, knowledge base, entities, relationships, etc. Heavy string formatting with timestamps and manual sections.
- `src/automation/story_generation.py`: orchestrates story arc regeneration and chapter summaries using template snippets and file writes.
- `src/automation/helpers/prompt_builder.py`: inlines instructions for story arc updates when building prompts.

## Refactor Approach (Workstream B follow-up)
1. Extract template definitions into structured JSON/markdown assets inside `refactoring/templates/` (or similar) so they can be versioned/edited independently.
2. Create a `TemplateRenderer` service (located at `refactoring/src/infrastructure/templates/template_renderer.py`) that loads templates, fills context (timestamps, names), and returns strings.
3. Update FileManager/Automation code to request templates via the new service instead of direct string-building functions.
4. Preserve legacy behaviour by snapshotting a few generated outputs (plot threads, story arc) before migration.
5. Apply the same renderer for entity card creation to align with the JSON fixtures.

This note will guide the template helper work once repository/service layers are ready.
