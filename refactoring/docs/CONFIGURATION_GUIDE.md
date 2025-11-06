# Configuration Guide - RP Launcher

**Version:** 2.0.0
**Last Updated:** 2025-10-21

---

## Overview

The RP Launcher uses a **4-layer configuration system** with clear precedence rules, comprehensive validation, and flexible override options.

### Configuration Layers (Lowest to Highest Priority)

1. **defaults.py** - Base configuration with TypedDict schemas
2. **.env file** - Local environment variables (gitignored secrets)
3. **config.json** - Per-RP customizations (committed to repo)
4. **ENV variables** - Runtime overrides (Docker/production)

```
┌─────────────────────────────────────────┐
│  Environment Variables (Highest)        │ ← RP_SYSTEM_LOG_LEVEL=ERROR
├─────────────────────────────────────────┤
│  config.json                            │ ← { "system": { "log_level": "INFO" } }
├─────────────────────────────────────────┤
│  .env file                              │ ← RP_SYSTEM_AUTO_SAVE=true
├─────────────────────────────────────────┤
│  defaults.py (Lowest)                   │ ← Built-in defaults
└─────────────────────────────────────────┘
```

---

## Quick Start

### Basic Setup

```python
from pathlib import Path
from src.infrastructure.config import ConfigLoader

# Initialize config loader for your RP directory
rp_dir = Path("/path/to/my/rp")
loader = ConfigLoader(rp_dir)

# Load configuration (creates default config.json if missing)
config = loader.load()

# Access configuration values
log_level = config["system"]["log_level"]
claude_model = config["modules"]["claude_api_client"]["config"]["model"]
```

### Check for Misconfigurations

```python
# Validate directory structure
issues = loader.validate_rp_directory()

if issues:
    for issue in issues:
        print(issue)
else:
    print("✓ Directory structure is valid")

# Validate configuration values
if loader.validate():
    print("✓ Configuration is valid")
else:
    print("✗ Configuration has errors (see logs)")
```

---

## Configuration Files

### 1. defaults.py (Read-Only)

**Location:** `src/infrastructure/config/defaults.py`

Contains all default configuration values with TypedDict schemas for validation.

**Do NOT modify this file** - It's the source of truth for defaults.

```python
# Example from defaults.py
SYSTEM_DEFAULTS: SystemConfig = {
    "log_level": "INFO",
    "auto_save": True,
    "backup_frequency": 10,
    "max_backups": 20,
    "performance_tracking": False,
}
```

### 2. .env File (Local Overrides)

**Location:** `<rp_dir>/.env`
**Purpose:** Local secrets and overrides (gitignored)

Format:
```bash
# System configuration
RP_SYSTEM_LOG_LEVEL=DEBUG
RP_SYSTEM_AUTO_SAVE=false

# API Keys (never commit to git!)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...

# LLM Configuration
RP_CLAUDE_MODEL=claude-3-5-sonnet-20241022
RP_CLAUDE_TEMPERATURE=0.8
```

**Supported Environment Variables:**

| Variable | Maps To | Example |
|----------|---------|---------|
| `RP_SYSTEM_LOG_LEVEL` | `system.log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `RP_SYSTEM_AUTO_SAVE` | `system.auto_save` | `true`, `false` |
| `RP_SYSTEM_BACKUP_FREQUENCY` | `system.backup_frequency` | `10` |
| `ANTHROPIC_API_KEY` | `modules.claude_api_client.config.api_key` | `sk-ant-...` |
| `OPENAI_API_KEY` | `modules.openai_client.config.api_key` | `sk-...` |
| `DEEPSEEK_API_KEY` | `modules.deepseek_client.config.api_key` | `sk-...` |
| `OPENROUTER_API_KEY` | `modules.openrouter_client.config.api_key` | `sk-...` |
| `RP_CLAUDE_MODEL` | `modules.claude_api_client.config.model` | `claude-3-5-sonnet-20241022` |
| `RP_CLAUDE_TEMPERATURE` | `modules.claude_api_client.config.temperature` | `0.7` |
| `RP_CLAUDE_MAX_TOKENS` | `modules.claude_api_client.config.max_tokens` | `8192` |
| `RP_PROXY_URL` | `modules.proxy_client.config.proxy_url` | `http://proxy:8080` |

### 3. config.json (Per-RP Config)

**Location:** `<rp_dir>/config.json`
**Purpose:** Per-RP customizations (committed to git)

Auto-generated with defaults if missing. Edit to customize:

```json
{
  "version": "2.0.0",
  "system": {
    "log_level": "INFO",
    "auto_save": true,
    "backup_frequency": 10,
    "max_backups": 20,
    "performance_tracking": false
  },
  "modules": {
    "claude_api_client": {
      "enabled": true,
      "config": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 8192,
        "use_prompt_caching": true
      }
    },
    "session_manager": {
      "enabled": true,
      "config": {
        "auto_checkpoint_frequency": 10,
        "keep_archived": 20,
        "compression": false
      }
    }
  }
}
```

### 4. Environment Variables (Runtime)

Set in shell or Docker/systemd config:

```bash
# Linux/macOS
export RP_SYSTEM_LOG_LEVEL=DEBUG
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:RP_SYSTEM_LOG_LEVEL="DEBUG"
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Docker Compose
environment:
  - RP_SYSTEM_LOG_LEVEL=ERROR
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

---

## Configuration Schema

### System Configuration

```python
class SystemConfig(TypedDict):
    log_level: str              # DEBUG, INFO, WARNING, ERROR, CRITICAL
    auto_save: bool             # Auto-save state changes
    backup_frequency: int       # Responses between backups (≥0)
    max_backups: int            # Max backup files to keep (≥0)
    performance_tracking: bool  # Enable performance profiling
```

### Module Configuration

Each module has this structure:

```json
{
  "module_name": {
    "enabled": true,  // Boolean: enable/disable module
    "config": {       // Dict: module-specific config
      // ... module settings
    }
  }
}
```

**Available Modules:**

- `file_manager` - File I/O and backups
- `session_manager` - Session state and checkpoints
- `fs_write_queue` - Async file write queue
- `background_task_queue` - Background task processing
- `agent_coordinator` - Agent execution and orchestration
- `entity_manager` - Character/world entity management
- `automation_orchestrator` - Automation pipeline
- `update_checker` - Update notifications
- `proxy_client` - HTTP proxy configuration
- `claude_api_client` - Claude LLM client
- `openai_client` - OpenAI LLM client
- `deepseek_client` - DeepSeek LLM client
- `openrouter_client` - OpenRouter LLM client

### LLM Client Configuration

All LLM clients follow this pattern:

```python
class LLMConfig(TypedDict):
    enabled: bool
    model: str            # Model identifier
    temperature: float    # 0.0-1.0 sampling temperature
    max_tokens: int       # Max tokens in response (>0)
    api_key: str          # Optional: API key (prefer .env)
```

**Validation Rules:**
- `temperature` must be between 0.0 and 1.0
- `max_tokens` must be a positive integer
- `model` must be a non-empty string

---

## Precedence Examples

### Example 1: Simple Override

```json
// defaults.py
{ "system": { "log_level": "INFO" } }

// config.json
{ "system": { "log_level": "DEBUG" } }

// Result
{ "system": { "log_level": "DEBUG" } }  ← config.json wins
```

### Example 2: Deep Merge

```json
// defaults.py
{
  "modules": {
    "claude_api_client": {
      "config": {
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 4000
      }
    }
  }
}

// config.json (only override temperature)
{
  "modules": {
    "claude_api_client": {
      "config": {
        "temperature": 0.9
      }
    }
  }
}

// Result (deep merge preserves other fields)
{
  "modules": {
    "claude_api_client": {
      "config": {
        "model": "claude-3-opus-20240229",    ← from defaults
        "temperature": 0.9,                    ← from config.json
        "max_tokens": 4000                     ← from defaults
      }
    }
  }
}
```

### Example 3: Full Precedence Chain

```bash
# Layer 1: defaults.py
system.log_level = "INFO"

# Layer 2: .env file
RP_SYSTEM_LOG_LEVEL=WARNING

# Layer 3: config.json
{ "system": { "log_level": "DEBUG" } }

# Layer 4: Environment variable
export RP_SYSTEM_LOG_LEVEL=ERROR

# Final Result
system.log_level = "ERROR"  ← ENV variable wins (highest priority)
```

---

## Validation

### Automatic Validation

Configuration is validated automatically during `load()`:

```python
loader = ConfigLoader(rp_dir)
config = loader.load()  # Validation happens here

# Check for warnings
if loader._validation_warnings:
    for warning in loader._validation_warnings:
        print(f"⚠ {warning}")
```

### Manual Validation

```python
# Validate configuration values
is_valid = loader.validate()

if not is_valid:
    print("Configuration has errors - check logs")

# Validate directory structure
issues = loader.validate_rp_directory()
for issue in issues:
    print(issue)
```

### Validation Rules

**System Config:**
- `log_level` must be one of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `auto_save` must be boolean
- `backup_frequency` must be non-negative integer
- `max_backups` must be non-negative integer
- `performance_tracking` must be boolean

**LLM Clients:**
- `temperature` must be float between 0.0 and 1.0
- `max_tokens` must be positive integer
- `model` must be non-empty string

**Agent Coordinator:**
- `max_concurrent_agents` must be positive integer
- `timeout` must be positive integer
- `immediate_workers` must be positive integer
- `background_workers` must be positive integer
- `max_retries` must be non-negative integer

**Session Manager:**
- `auto_checkpoint_frequency` must be non-negative integer
- `keep_archived` must be non-negative integer
- `compression` must be boolean

### Unknown Field Warnings

Unknown fields generate warnings (not errors):

```python
# config.json
{
  "system": {
    "log_level": "INFO",
    "unknwon_field": "typo here"  ← typo
  }
}

# Warning generated:
⚠ Unknown field in system config: 'unknwon_field' (will be ignored)
```

**Field Suggestions:**

If the unknown field is similar to a valid field, a suggestion is provided:

```json
{
  "modules": {
    "claude_api_client": {
      "config": {
        "max_token": 8000  ← typo (should be max_tokens)
      }
    }
  }
}

# Warning generated:
⚠ Unknown field 'claude_api_client.config.max_token'. Did you mean 'max_tokens'?
```

---

## Common Use Cases

### Use Case 1: Local Development

**Setup:**
1. Clone repo
2. Create `.env` with API keys
3. Run with default `config.json`

```bash
# .env (gitignored)
ANTHROPIC_API_KEY=sk-ant-...
RP_SYSTEM_LOG_LEVEL=DEBUG  # Verbose logging for development
```

### Use Case 2: Production Deployment

**Setup:**
1. Use default config.json
2. Override via environment variables

```bash
# systemd service or Docker
Environment="RP_SYSTEM_LOG_LEVEL=ERROR"
Environment="ANTHROPIC_API_KEY=sk-ant-..."
Environment="RP_SYSTEM_AUTO_SAVE=true"
```

### Use Case 3: Multiple RPs with Different Settings

**Setup:**
Each RP directory has its own `config.json`:

```
/my-rps/
  ├── fantasy-rp/
  │   └── config.json  ← temperature=0.7, model=claude-3-opus
  ├── scifi-rp/
  │   └── config.json  ← temperature=0.9, model=claude-3-5-sonnet
  └── mystery-rp/
      └── config.json  ← temperature=0.5, model=gpt-4
```

### Use Case 4: CI/CD Testing

**Setup:**
Override everything via ENV for reproducible tests:

```bash
export RP_SYSTEM_LOG_LEVEL=ERROR
export RP_CLAUDE_TEMPERATURE=0.0  # Deterministic
export RP_CLAUDE_MAX_TOKENS=100   # Fast tests
```

---

## Programmatic Usage

### Basic Access

```python
from src.infrastructure.config import ConfigLoader

loader = ConfigLoader(rp_dir)
config = loader.load()

# Dot-notation access
log_level = loader.get("system.log_level", default="INFO")

# Direct dict access
claude_config = config["modules"]["claude_api_client"]["config"]
```

### Module Configuration

```python
# Get module config
session_config = loader.get_module_config("session_manager")

# Check if module enabled
if loader.is_module_enabled("claude_api_client"):
    # Use Claude client
    pass

# Enable/disable modules
loader.set_module_enabled("update_checker", False)
loader.save()  # Persist changes
```

### Dynamic Updates

```python
# Update configuration
loader.set("system.log_level", "DEBUG")
loader.save()  # Write to config.json

# Reload from disk
loader.reload()
```

### Export/Import

```python
# Export configuration to file
loader.export(Path("backup_config.json"))

# Import configuration from file
loader.import_config(Path("custom_config.json"))
```

---

## Troubleshooting

### Problem: Configuration not loading

**Solution:** Check directory structure

```python
loader = ConfigLoader(rp_dir)
issues = loader.validate_rp_directory()

for issue in issues:
    print(issue)
```

### Problem: Unknown field warnings

**Cause:** Typos or deprecated fields in config.json

**Solution:** Check warnings, fix typos

```python
loader.load()

if loader._validation_warnings:
    for warning in loader._validation_warnings:
        print(warning)
```

### Problem: Validation errors

**Cause:** Invalid values (wrong types, out of range)

**Solution:** Check logs, fix invalid values

```python
if not loader.validate():
    # Check logs for specific errors
    # Fix config.json and reload
    pass
```

### Problem: Environment variables not working

**Cause:** Wrong variable name or not exported

**Solution:** Check variable name mapping

```python
# Verify ENV vars are set
import os
print(os.environ.get("RP_SYSTEM_LOG_LEVEL"))

# Check mapping in ConfigLoader.ENV_VAR_MAPPING
from src.infrastructure.config.config_loader import ConfigLoader
print(ConfigLoader.ENV_VAR_MAPPING)
```

---

## Migration from Legacy

### Old System (Before v2.0.0)

- Hardcoded defaults scattered across files
- No .env support
- No environment variable overrides
- Limited validation

### New System (v2.0.0+)

- Centralized defaults in defaults.py with TypedDict schemas
- Full .env file support
- Environment variable overrides
- Comprehensive validation with helpful error messages
- 4-layer precedence system

### Migration Steps

1. **Read existing config:**
   ```python
   # Old way
   config = json.load(open("config.json"))

   # New way
   loader = ConfigLoader(rp_dir)
   config = loader.load()
   ```

2. **Move secrets to .env:**
   ```bash
   # Remove from config.json:
   # { "api_key": "sk-ant-..." }

   # Add to .env:
   ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Update module references:**
   ```python
   # Old way
   if config.get("use_claude", True):
       ...

   # New way
   if loader.is_module_enabled("claude_api_client"):
       ...
   ```

---

## Best Practices

### Security

1. **Never commit API keys** - Use .env file (gitignored)
2. **Use environment variables in production** - Avoid secrets in config.json
3. **Rotate keys regularly** - Update .env and restart

### Organization

1. **Use config.json for RP-specific settings** - Models, temperatures, etc.
2. **Use .env for local overrides** - Development logging, test keys
3. **Use ENV vars for deployment** - Docker, systemd, CI/CD

### Validation

1. **Always validate after loading**:
   ```python
   config = loader.load()
   assert loader.validate(), "Invalid configuration"
   ```

2. **Check directory structure on first run**:
   ```python
   issues = loader.validate_rp_directory()
   if any("ERROR" in i for i in issues):
       print("Critical issues found!")
   ```

3. **Monitor validation warnings** - Fix typos and unknown fields

---

## API Reference

### ConfigLoader Class

```python
class ConfigLoader:
    def __init__(self, rp_dir: Path)
    def load(self, create_if_missing: bool = True) -> Dict[str, Any]
    def save(self) -> None
    def reload(self) -> Dict[str, Any]
    def validate(self) -> bool
    def validate_rp_directory(self) -> List[str]

    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None

    def get_module_config(self, module_name: str) -> Dict[str, Any]
    def is_module_enabled(self, module_name: str) -> bool
    def set_module_enabled(self, module_name: str, enabled: bool) -> None

    def list_enabled_modules(self) -> List[str]
    def list_disabled_modules(self) -> List[str]

    def reset_to_defaults(self) -> None
    def export(self, output_file: Path) -> None
    def import_config(self, input_file: Path) -> None
```

---

## See Also

- `docs/architecture/README.md` - System architecture
- `src/infrastructure/config/defaults.py` - Default values and schemas
- `tests/infrastructure/config/test_config_loader_validation.py` - Test examples

---

**Version:** 2.0.0
**Workstream:** J (Configuration & Defaults)
**Date:** 2025-10-21
