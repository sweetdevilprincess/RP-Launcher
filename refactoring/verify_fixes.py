"""Verify all fixes are working."""

from pathlib import Path
from src.infrastructure.config.config_loader import ConfigLoader
from src.infrastructure.config.defaults import get_default_config

print("=" * 60)
print("Verification Script")
print("=" * 60)

# 1. Check default config has modules
print("\n1. Checking default config...")
default_config = get_default_config()
modules = default_config.get("modules", {})
print(f"   Default config has {len(modules)} modules")
if modules:
    print("   Module names:")
    for i, module_id in enumerate(list(modules.keys())[:5], 1):
        enabled = modules[module_id].get("enabled", False)
        print(f"     {i}. {module_id}: {'[ON]' if enabled else '[OFF]'}")
    if len(modules) > 5:
        print(f"     ... and {len(modules) - 5} more")
else:
    print("   [WARN] WARNING: No modules in default config!")

# 2. Check if config.json exists
print("\n2. Checking if config.json exists...")
rp_dir = Path("test_rps_output/Test Adventure")
config_file = rp_dir / "config.json"

if config_file.exists():
    print(f"   [OK] config.json exists at {config_file}")

    # Load it and check modules
    config_loader = ConfigLoader(rp_dir)
    config = config_loader.load()
    loaded_modules = config.get("modules", {})
    print(f"   Loaded config has {len(loaded_modules)} modules")
else:
    print(f"   [X] config.json does NOT exist at {config_file}")
    print("   --> Bridge will create it on first run")

# 3. Check settings handler changes
print("\n3. Checking settings handler...")
with open("src/presentation/bridge/handlers/settings_handler.py", "r") as f:
    content = f.read()
    if '"primary_provider"' in content:
        print("   [OK] Settings handler uses 'primary_provider'")
    else:
        print("   [X] Settings handler missing 'primary_provider'")

    if 'excluded_fields' in content:
        print("   [OK] Settings handler has excluded_fields filter")
    else:
        print("   [X] Settings handler missing excluded_fields")

# 4. Check modules page changes
print("\n4. Checking modules page...")
with open("src/presentation/tui/components/modules_page.py", "r") as f:
    content = f.read()
    if '_show_empty_state' in content:
        print("   [OK] Modules page has _show_empty_state method")
    else:
        print("   [X] Modules page missing _show_empty_state")

# 5. Check LLM settings page CSS
print("\n5. Checking LLM settings page CSS...")
with open("src/presentation/tui/components/llm_settings_page.py", "r") as f:
    content = f.read()
    # Count how many times "color:" appears in Select CSS
    select_section = content[content.find("LLMSettingsPage Select"):content.find("#primary-provider")]
    color_count = select_section.count("color:")
    print(f"   Select CSS has {color_count} color: declarations")
    if color_count >= 4:  # SelectCurrent, OptionList, option, option-highlighted
        print("   [OK] Select CSS properly defines colors")
    else:
        print("   [WARN] Select CSS may be missing color declarations")

print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)
print("\nNext Steps:")
print("1. Run: python start_bridge.py")
print("2. Wait for '[OK] Bridge Service ready'")
print("3. Check that config.json was created")
print("4. In new terminal: python start_tui.py")
print("5. Navigate to Modules tab - should see modules")
print("6. Navigate to Settings tab - dropdown should be readable")
print("7. Toggle SDK switch - should work without error")
