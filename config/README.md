# Configuration Folder

⚠️ **IMPORTANT: DO NOT MODIFY FILES IN THIS FOLDER UNLESS YOU KNOW WHAT YOU'RE DOING**

This folder contains critical system configuration files. Modifying or moving these files may break the launcher and automation system.

---

## Critical Files

### `CLAUDE.md`
**DO NOT MOVE OR RENAME** - Referenced by slash commands and automation hooks.

This file contains instructions for Claude Code on how to handle RP sessions. It defines:
- File reference priority
- Reading order for RP files
- Session workflow
- Story continuity rules

**Referenced by:**
- `.claude/commands/continue.md` - Session start command
- `.claude/commands/` - Multiple slash commands
- `config/guidelines/SESSION_INSTRUCTIONS.md` - Session workflow
- Background automation hooks

### `config.json`
Your personal configuration including:
- API keys (OpenRouter, Anthropic)
- Thinking mode preferences
- Automation settings
- Model selection

**This file is gitignored** - Never committed to version control.

### `config.json.template`
Template for creating new config files. Copy this to `config.json` and add your API keys.

### `automation_config.json.template`
Template for RP-specific automation settings (used when creating new RPs).

---

## Folders

### `guidelines/`
Shared writing guidelines and session instructions used across all RPs:
- `SESSION_INSTRUCTIONS.md` - How to start/end sessions
- Custom writing guides
- Style templates

### `templates/`
Template files for creating new RP content:
- Entity card templates
- Chapter templates
- State file templates

### `proxy_prompt.txt`
System prompt for API proxy mode (if using custom proxy setup).

---

## For Developers

If you need to modify these files for development:

1. **CLAUDE.md**: Update all references in:
   - `.claude/commands/continue.md`
   - `.claude/commands/COMMANDS_README.md`
   - `config/guidelines/SESSION_INSTRUCTIONS.md`
   - `docs/reference/RP_FOLDER_STRUCTURE.md`
   - `docs/guides/SYSTEM_OVERVIEW.md`

2. **config.json**: Never commit with real API keys. Always use `config.json.template` for repository.

3. **Templates**: Test changes with `python setup/quick_setup.py` before committing.

---

**When in doubt, don't change it!** Most user-facing settings can be changed via the Settings screen (F9) in the launcher.
