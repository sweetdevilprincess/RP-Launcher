# Bridge Critical Issues - Complete Trace

**Date:** 2025-10-27
**Status:** MULTIPLE CRITICAL BUGS FOUND

---

## Critical Issue #1: Missing `rp_dir` in Factory Call

**Location:** `bridge_service.py:180`

**Problem:**
```python
self.llm_client = provider_spec.factory(config)  # ❌ config doesn't have 'rp_dir'
```

**Root Cause:**
- Factory functions expect `config.get("rp_dir")` (see registry.py lines 53, 65, 76, 87)
- But `config` is the loaded JSON config from `config_loader.load()`
- `rp_dir` is NOT in the JSON config - it's a BridgeService attribute!
- All factories will get `rp_dir=None`

**Impact:** LLM clients won't have access to RP directory path

**Fix:**
```python
# Line 180 - Add rp_dir to config before passing to factory
config_with_metadata = {
    **config,
    "rp_dir": self.rp_dir,
    "project_root": self.rp_dir,  # Some factories might expect this
}
self.llm_client = provider_spec.factory(config_with_metadata)
```

---

## Critical Issue #2: Config Structure Mismatch

**Location:** `bridge_service.py:180` + `registry.py:58-88` + `claude_api_client.py:60-94`

**Problem:**

**What's being passed:**
```python
config = {
    "version": "1.0",
    "modules": {
        "claude_api_client": {
            "enabled": true,
            "config": {
                "api_key": "sk-...",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7
            }
        }
    }
}
# Full config dict passed to factory
provider_spec.factory(config)
```

**What `load_claude_settings` expects:**
```python
config_override = {
    "anthropic_api_key": "sk-...",  # ❌ Looking at root level
    "model": "claude-3-5-sonnet-20241022",
    etc.
}
```

**Root Cause:**
- `bridge_service.py:180` passes the FULL config tree
- But `load_claude_settings()` at line 83-85 looks for `config_data.get("anthropic_api_key")` at ROOT level
- The actual path is: `config["modules"]["claude_api_client"]["config"]["api_key"]`

**Impact:**
- Settings never loaded from config
- API keys not found
- LLM initialization fails or uses wrong settings

**Fix Option 1 (Simple):**
```python
# Line 180 in bridge_service.py
# Extract module-specific config before passing to factory
module_config = config.get("modules", {}).get(provider_name, {}).get("config", {})
config_with_metadata = {
    **module_config,  # ✓ Now has keys at root level
    "rp_dir": self.rp_dir,
    "project_root": self.rp_dir,
}
self.llm_client = provider_spec.factory(config_with_metadata)
```

**Fix Option 2 (Better - update factories):**
```python
# In registry.py, update all factory signatures to extract module config:
def _api_factory(config: dict[str, Any]) -> LLMClient:
    # Extract module-specific config
    provider_config = config.get("modules", {}).get("claude_api_client", {}).get("config", {})

    # Merge with metadata
    full_config = {
        **provider_config,
        "rp_dir": config.get("rp_dir"),
        "project_root": config.get("project_root"),
    }

    settings: ClaudeAPISettings = load_claude_settings(config_override=full_config)
    # ...
```

---

## Critical Issue #3: Claude SDK Client Missing Implementation

**Location:** `claude_sdk_client.py:19-22,37`

**Problem:**
```python
try:
    from src.clients.claude_sdk import ClaudeSDKClient as LegacyClaudeSDKClient
except ImportError:
    LegacyClaudeSDKClient = None  # ❌ Import fails

# Later at line 37:
self._client = LegacyClaudeSDKClient(cwd=working_dir)  # ❌ None(cwd=...) → TypeError
```

**Root Cause:**
- File `src/clients/claude_sdk.py` doesn't exist
- Import fails silently
- When user selects Claude SDK provider, initialization calls `None(...)`
- Error: "'NoneType' object is not callable"

**Impact:**
- Cannot use Claude SDK provider
- Crashes with confusing error message
- User stuck unable to configure LLM

**Fix Options:**

**Option A: Implement stub/error handling:**
```python
# Line 30-43 in claude_sdk_client.py
def __init__(self, *, rp_dir: Path | None = None, project_root: Path | None = None) -> None:
    if LegacyClaudeSDKClient is None:
        raise NotImplementedError(
            "Claude SDK client is not yet implemented. "
            "Please use 'Anthropic Claude (API)' provider instead. "
            "SDK support is coming soon."
        )
    working_dir = rp_dir or project_root or Path.cwd()
    self._client = LegacyClaudeSDKClient(cwd=working_dir)
    # ...
```

**Option B: Remove from registry temporarily:**
```python
# In registry.py - comment out SDK provider registration:
# register_provider(
#     ProviderSpec(
#         provider_id="claude_sdk_client",
#         label="Claude SDK",
#         supports_streaming=True,
#         factory=_sdk_factory,
#         description="High-performance Claude SDK bridge (Node) - Coming Soon",
#     )
# )
```

**Option C: Find the actual SDK implementation:**
- Search entire codebase for existing SDK client code
- May be in different repo or legacy folder
- User mentioned "We have an SDK client" so it exists somewhere

---

## Critical Issue #4: Settings Handler Unknown Fields Warnings

**Location:** `settings_handler.py:93-104` + Config structure

**Problem (from screenshot):**
```
[CONFIG] [WARNING] Unknown field 'claude_sdk_client.config.secondary_api_key' (will be ignored)
[CONFIG] [WARNING] Unknown field 'claude_sdk_client.config.secondary_model' (will be ignored)
[CONFIG] [WARNING] Unknown field 'claude_sdk_client.config.system_prompt' (will be ignored)
[CONFIG] [WARNING] Unknown field 'claude_sdk_client.config.context_window' (will be ignored)
[CONFIG] [WARNING] Unknown field 'claude_sdk_client.config.response_format' (will be ignored)
```

**Root Cause:**
- TUI Settings page (llm_settings_page.py:394-405) collects these fields:
  ```python
  self.settings = {
      "provider": provider,
      "use_sdk": ...,
      "primary_api_key": ...,
      "secondary_api_key": ...,      # ❌ Not in defaults
      "secondary_model": ...,         # ❌ Not in defaults
      "system_prompt": ...,          # ❌ Not in defaults
      "context_window": ...,         # ❌ Not in defaults
      "response_format": ...,        # ❌ Not in defaults
      "temperature": ...,
      "max_tokens": ...,
  }
  ```
- Settings handler saves these to config at line 93-104
- ConfigLoader validation (config_loader.py:686-732) detects unknown fields
- Fields don't exist in `defaults.py` for this provider

**Impact:**
- Settings get saved but trigger warnings
- Some settings might be ignored
- Validation spam in logs

**Fix:**

**Option A: Update defaults.py to include these fields:**
```python
# In defaults.py, add to claude_sdk_client config:
"claude_sdk_client": {
    "enabled": False,
    "config": {
        "api_key": "",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 4096,
        "use_prompt_caching": True,
        "use_sdk": False,
        # Add these:
        "secondary_api_key": "",
        "secondary_model": "",
        "system_prompt": "",
        "context_window": 8192,
        "response_format": "text",
    }
}
```

**Option B: Remove unused fields from TUI:**
```python
# In llm_settings_page.py:394-405
# Only collect fields that are actually used:
self.settings = {
    "provider": provider,
    "use_sdk": use_sdk_switch.value,
    "primary_api_key": primary_key.value,
    "temperature": temperature.value,
    "max_tokens": max_tokens.value,
    # Remove: secondary_api_key, secondary_model, system_prompt, context_window, response_format
}
```

---

## Critical Issue #5: Streaming Bug (Already Fixed)

**Location:** `message_handler.py:116, 126`

**Status:** ✅ ALREADY FIXED in previous session

**Was:**
```python
self.bridge.server.send_push_message(chunk_msg)  # ❌ AttributeError
```

**Fixed to:**
```python
self.bridge.socket_server.send_push_message(chunk_msg)  # ✓ Correct
```

---

## Summary of Critical Paths to Fix

### Path 1: Fix LLM Initialization (Issues #1, #2)

**Priority:** CRITICAL - blocks all LLM usage

**File:** `bridge_service.py:174-183`

**Current code:**
```python
# Get provider from registry
provider_spec = get_provider(provider_name)
if not provider_spec:
    raise RuntimeError(f"Provider not found: {provider_name}")

# Create client using factory
self.llm_client = provider_spec.factory(config)  # ❌ WRONG
self.current_provider = provider_name
```

**Fixed code:**
```python
# Get provider from registry
provider_spec = get_provider(provider_name)
if not provider_spec:
    raise RuntimeError(f"Provider not found: {provider_name}")

# Extract module-specific config
module_config = config.get("modules", {}).get(provider_name, {}).get("config", {})

# Add metadata
factory_config = {
    **module_config,  # Provider-specific settings at root level
    "rp_dir": self.rp_dir,  # Add RP directory path
    "project_root": self.rp_dir,  # Add project root
    "modules": config.get("modules", {}),  # Keep full modules for reference
}

# Create client using factory
print(f"[DEBUG] Factory config keys: {list(factory_config.keys())}")
self.llm_client = provider_spec.factory(factory_config)
self.current_provider = provider_name
```

---

### Path 2: Fix Claude SDK (Issue #3)

**Priority:** HIGH - blocks SDK provider

**Option A (Quick Fix):** Add error handling in `claude_sdk_client.py:30-43`

**Option B (Remove):** Comment out SDK provider in `registry.py:91-99`

**Option C (Find Implementation):** Locate existing SDK client code

---

### Path 3: Fix Settings Warnings (Issue #4)

**Priority:** MEDIUM - causes log spam but not blocking

**Choose one:**
- Update `defaults.py` to include all fields
- Remove unused fields from TUI settings page

---

## Testing Checklist After Fixes

1. **Test LLM Initialization:**
   ```bash
   # Restart bridge
   # Should see: [OK] LLM client initialized: claude_api_client
   # Should NOT see: AttributeError or KeyError
   ```

2. **Test Settings Save:**
   ```bash
   # In TUI: Press F8, change temperature, click Save
   # Should see: "Settings updated successfully"
   # Should NOT see: 'NoneType' object is not callable
   ```

3. **Test Message Sending:**
   ```bash
   # In TUI: Type message, press Ctrl+Enter
   # Should receive response (mock or real)
   # Should NOT crash
   ```

4. **Test Provider Switching:**
   ```bash
   # In TUI: F8, change provider dropdown, click Save
   # Should reinitialize LLM client
   # Should NOT see config mismatch errors
   ```

---

## Files That Need Changes

1. **`src/presentation/bridge/bridge_service.py`** (Lines 174-183)
   - Fix config structure passed to factory
   - Add rp_dir to factory config

2. **`src/infrastructure/llm/claude_sdk_client.py`** (Lines 30-43)
   - Add NotImplementedError if LegacyClaudeSDKClient is None
   - OR find actual SDK implementation

3. **`src/infrastructure/llm/registry.py`** (Optional - Lines 91-99)
   - Temporarily remove SDK provider registration
   - OR update all factories to handle new config structure

4. **`src/infrastructure/config/defaults.py`** (Optional)
   - Add missing fields to provider configs
   - OR remove unused fields from TUI

5. **`src/presentation/tui/components/llm_settings_page.py`** (Optional - Lines 394-405)
   - Remove unused fields from settings collection
   - OR keep fields and update defaults.py

---

**Next Steps:**
1. Apply fix to bridge_service.py (Issue #1 + #2)
2. Test LLM initialization
3. Apply fix to claude_sdk_client.py (Issue #3)
4. Test settings save
5. Clean up warnings (Issue #4)
