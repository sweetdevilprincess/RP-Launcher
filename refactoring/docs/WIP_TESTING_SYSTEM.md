# WIP (Work In Progress) Testing System

**Status:** ✅ Implemented and Tested
**Version:** 1.0
**Date:** 2025-10-21

## Overview

The WIP Testing System is a dynamic, self-discovering framework for testing new code implementations alongside production code **without modifying the Bridge for each new module**. It provides safe, side-by-side comparison of production and WIP code to detect bugs and conflicts before deployment.

### Key Benefits

✅ **No Bridge edits per module** - Bridge modified once, never touched again
✅ **Automatic discovery** - Scans src/wip/ folder for available modules
✅ **Safe testing** - Both versions run, production always works
✅ **Error recovery** - WIP crashes don't affect production
✅ **Easy workflow** - Copy file, edit, test, move to production
✅ **Comparison mode** - See exactly what changed
✅ **Hot reload** - Reload WIP modules without restarting Bridge

---

## Architecture

### Components

1. **WIP Registry** (`src/wip/registry.py`)
   - Defines which components CAN be swapped (explicit whitelist)
   - Provides safety by preventing arbitrary code injection
   - Currently supports 10+ components across automation, infrastructure, and domain layers

2. **WIP Scanner** (`src/wip/scanner.py`)
   - Auto-discovers available WIP modules by scanning filesystem
   - Checks against registry (only registered components allowed)
   - Reads optional `wip_manifest.json` for metadata

3. **WIP Loader** (`src/wip/loader.py`)
   - Dynamically imports WIP modules using `importlib`
   - Handles import errors gracefully
   - Caches loaded modules for performance

4. **WIP Executor** (`src/wip/executor.py`)
   - Runs operations through BOTH production and WIP code
   - Catches WIP errors without affecting production
   - Compares results and detects differences

5. **Bridge Integration** (`src/presentation/bridge/bridge_service.py`)
   - Extended `TEST_MODE` handler supports WIP commands
   - Single modification enables entire WIP system
   - No further Bridge edits needed for new WIP modules

### File Structure

```
src/
├── wip/                              # WIP system core
│   ├── __init__.py                   # Public API
│   ├── registry.py                   # Component registry
│   ├── scanner.py                    # Module discovery
│   ├── loader.py                     # Dynamic import
│   ├── executor.py                   # Comparison execution
│   ├── wip_manifest_template.json    # Optional metadata template
│   └── automation/                   # WIP implementations (example)
│       └── services/
│           └── prompt_builder.py     # Your WIP code here
├── automation/
│   └── services/
│       └── prompt_builder.py         # Production code
└── presentation/
    └── bridge/
        └── bridge_service.py         # Modified ONCE

tests/
└── wip/
    └── test_wip_system.py            # 25 tests, all passing
```

---

## User Workflow

### 1. Create WIP Module

Copy production file to WIP directory:

```bash
# Example: Testing new PromptBuilder implementation
cp src/automation/services/prompt_builder.py src/wip/automation/services/prompt_builder.py

# Edit the WIP version
# Make your changes to src/wip/automation/services/prompt_builder.py
```

### 2. Enable WIP Mode via TUI

Send TEST_MODE request with WIP action:

```python
# Enable WIP mode for prompt_builder
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="enable",
    wip_component="prompt_builder"
)

# Response:
{
    "wip_enabled": true,
    "component": "prompt_builder",
    "message": "WIP mode enabled for prompt_builder"
}
```

### 3. Test with Comparison

When WIP mode is enabled, operations run through both versions:

```python
# Send message (uses both prod and WIP)
client.send_request(
    IPCMessageType.SEND_MESSAGE,
    user_message="Test my prompt builder"
)

# Response includes comparison:
{
    "production_result": "...",
    "wip_result": "...",
    "differences": [
        "Prompt length: 1500 chars (prod) vs 1800 chars (WIP)",
        "New section: 'ENTITY HIGHLIGHTS' (only in WIP)"
    ],
    "wip_error": null  # Or error message if WIP crashed
}
```

### 4. Handle WIP Errors

If WIP code crashes, production still works:

```python
# Response when WIP has error:
{
    "production_result": "...",  # Production works fine
    "wip_result": null,
    "wip_error": "KeyError: 'template_dir'",
    "wip_traceback": "Traceback (most recent call last):\\n  ...",
    "fallback": "Using production version"
}
```

### 5. Disable WIP Mode

```python
# Disable specific component
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="disable",
    wip_component="prompt_builder"
)

# Or disable all WIP modules
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="disable"
)
```

### 6. Move to Production

When WIP is tested and ready:

```bash
# Move WIP to production
mv src/wip/automation/services/prompt_builder.py src/automation/services/prompt_builder.py

# Done! No Bridge changes needed.
```

---

## TUI Commands

### List Available WIP Modules

```python
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="list"
)

# Response:
{
    "available_wip_modules": [
        "prompt_builder",
        "trigger_evaluator"
    ],
    "summary": {
        "total_swappable": 10,
        "available_wip": 2,
        "by_category": {
            "automation": 2,
            "infrastructure": 0
        }
    }
}
```

### Get WIP Status

```python
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="status"
)

# Response:
{
    "wip_status": {
        "enabled_components": ["prompt_builder"],
        "available_wip_modules": ["prompt_builder", "trigger_evaluator"],
        "loaded_wip_modules": ["prompt_builder"]
    }
}
```

### Reload WIP Module

Useful during development when WIP code changes:

```python
client.send_request(
    IPCMessageType.TEST_MODE,
    wip_action="reload",
    wip_component="prompt_builder"
)

# Response:
{
    "reloaded": true,
    "component": "prompt_builder",
    "message": "WIP module reloaded: prompt_builder"
}
```

---

## Optional Manifest File

Create `src/wip/wip_manifest.json` for metadata:

```json
{
  "prompt_builder": {
    "description": "Testing new tiered template system",
    "author": "Your Name",
    "status": "in_progress",
    "created": "2025-10-21",
    "notes": "Refactoring to support dynamic template loading",
    "changes": [
      "Added lazy initialization for template manager",
      "Fixed template path resolution bug",
      "Improved caching strategy"
    ],
    "tests_passing": true,
    "ready_for_production": false
  }
}
```

The manifest is **optional** - WIP system works without it.

---

## Registered Swappable Components

Currently, 10 components can be replaced with WIP versions:

### Automation Services
- `prompt_builder` - PromptBuilder (builds prompts from context)
- `file_loader` - FileLoader (loads RP files)

### Trigger System
- `trigger_evaluator` - TriggerEvaluator (evaluates semantic triggers)
- `semantic_evaluator` - SemanticEvaluator (semantic matching)

### Template System
- `narrative_template_manager` - NarrativeTemplateManager
- `template_loader` - TemplateLoader

### LLM Clients
- `claude_client` - ClaudeAPIClient
- `openai_client` - OpenAIChatClient

### Configuration & Session
- `config_loader` - ConfigLoader
- `session_manager` - SessionManager

### Adding New Swappable Components

Edit `src/wip/registry.py`:

```python
SWAPPABLE_COMPONENTS = {
    # ... existing components ...

    "my_new_component": ComponentInfo(
        component_id="my_new_component",
        production_module="src.my_module.my_component",
        class_name="MyComponent",
        category="automation",
        description="Description of what this does",
    ),
}
```

That's it! No Bridge changes needed.

---

## Comparison Engine

The WIP Executor automatically compares results:

### String Comparison
```python
# Detected:
- Length difference: 1500 chars (prod) vs 1800 chars (WIP)
- Content preview if strings are short
```

### Numeric Comparison
```python
# Detected:
- Value: 42 (prod) vs 50 (WIP)
```

### List/Tuple Comparison
```python
# Detected:
- Length: 5 items (prod) vs 6 items (WIP)
- Element 2: "foo" (prod) vs "bar" (WIP)
```

### Dict Comparison
```python
# Detected:
- Missing keys in WIP: {'old_field'}
- Extra keys in WIP: {'new_field'}
- Key 'name': "Alice" (prod) vs "Bob" (WIP)
```

---

## Implementation Details

### How Dynamic Loading Works

1. **Registry Check**: Is this component allowed to be swapped?
2. **Path Resolution**: Convert `src.automation.services.prompt_builder` to `src/wip/automation/services/prompt_builder.py`
3. **File Check**: Does the WIP file exist?
4. **Dynamic Import**: Use `importlib.util.spec_from_file_location()` to load module
5. **Class Extraction**: Get class by name from module
6. **Caching**: Cache loaded classes for performance
7. **Instance Creation**: Instantiate with same arguments as production

### How Comparison Works

1. **Check if Enabled**: Is WIP mode on for this component?
2. **Create Instances**: Instantiate both production and WIP versions
3. **Execute Production**: Call method on production instance
4. **Execute WIP**: Try to call method on WIP instance (catch errors)
5. **Compare Results**: Use comparison engine to detect differences
6. **Return ComparisonResult**: Include both results, errors, and differences

### Error Handling

WIP errors are caught and reported without affecting production:

```python
try:
    wip_result = wip_instance.method(*args, **kwargs)
    wip_error = None
except Exception as e:
    wip_result = None
    wip_error = str(e)
    wip_traceback = traceback.format_exc()
```

Production result is always returned, even if WIP fails.

---

## Testing

### Test Coverage

25 tests covering all components:

```bash
pytest tests/wip/test_wip_system.py -v

# Results: 25 passed in 0.74s ✅
```

### Test Categories

1. **Registry Tests** (7 tests)
   - Component registration
   - Validation
   - Categories

2. **Scanner Tests** (7 tests)
   - File discovery
   - Manifest loading
   - Availability checking

3. **Loader Tests** (6 tests)
   - Dynamic import
   - Caching
   - Error handling

4. **Executor Tests** (5 tests)
   - Enable/disable
   - Status reporting

---

## Best Practices

### ✅ DO:
- Use WIP for major refactors and experiments
- Test thoroughly before moving to production
- Keep WIP lifetime short (days, not weeks)
- Use manifest for tracking status
- Disable WIP when not actively testing
- Delete WIP files after promoting to production

### ❌ DON'T:
- Let WIP diverge too far from production
- Commit WIP files to main branch
- Use WIP in production deployments
- Forget to test edge cases
- Skip comparison analysis

---

## Troubleshooting

### WIP Module Not Found

**Problem:** `WIP module not available for: component_id`

**Solutions:**
1. Check file exists: `src/wip/automation/services/component.py`
2. Check component is registered in `registry.py`
3. Check file has correct class name

### Import Errors

**Problem:** `Failed to load module`

**Solutions:**
1. Check Python syntax in WIP file
2. Check imports in WIP file are correct
3. Use relative imports (not absolute to `src.wip`)
4. Check for circular dependencies

### WIP Always Uses Old Version

**Problem:** Changes to WIP file not reflected

**Solutions:**
1. Use reload command: `wip_action="reload"`
2. Restart Bridge
3. Check you're editing the right file

### Comparison Shows No Differences But Results Differ

**Problem:** Visual inspection shows differences but comparison doesn't detect them

**Solutions:**
1. Check if objects have custom `__eq__` methods
2. Add specific comparison logic to executor
3. Manually inspect `production_result` vs `wip_result`

---

## Future Enhancements

Potential improvements (not yet implemented):

1. **Visual Diff Tool**: Side-by-side code comparison in TUI
2. **Performance Comparison**: Track execution time differences
3. **Automated Testing**: Run WIP through test suite automatically
4. **CI Integration**: Gate production merges on WIP tests passing
5. **Version Tracking**: Track WIP module versions and changes
6. **A/B Testing**: Route % of requests to WIP version

---

## Examples

### Example 1: Testing New PromptBuilder

```bash
# 1. Copy to WIP
cp src/automation/services/prompt_builder.py src/wip/automation/services/

# 2. Edit WIP version
# ... make changes ...

# 3. Enable via TUI
TEST_MODE(wip_action="enable", wip_component="prompt_builder")

# 4. Send test message
SEND_MESSAGE(user_message="Test prompt")

# Response shows both versions!

# 5. Disable when done
TEST_MODE(wip_action="disable", wip_component="prompt_builder")

# 6. Move to production when ready
mv src/wip/automation/services/prompt_builder.py src/automation/services/
```

### Example 2: Multiple WIP Modules

```bash
# Enable multiple components
TEST_MODE(wip_action="enable", wip_component="prompt_builder")
TEST_MODE(wip_action="enable", wip_component="trigger_evaluator")

# Check status
TEST_MODE(wip_action="status")
# Returns: {"enabled_components": ["prompt_builder", "trigger_evaluator"]}

# Disable all at once
TEST_MODE(wip_action="disable")
```

---

## Conclusion

The WIP Testing System provides a **production-safe** way to test new implementations without:
- Modifying the Bridge repeatedly
- Risking production stability
- Losing comparison data
- Complex setup procedures

**Result:** Faster development, safer testing, easier debugging! 🚀

For questions or issues, see the test suite in `tests/wip/test_wip_system.py` for working examples.
