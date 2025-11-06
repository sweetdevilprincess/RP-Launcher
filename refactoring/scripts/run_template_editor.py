"""
Runner script for the Template Editor mockup.

This script sets up the Python path and runs the template editor mockup.
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def main():
    print("=" * 70)
    print("Template Editor UI Mockup - Three-Panel Layout")
    print("=" * 70)
    print()
    print("This mockup demonstrates the template management interface:")
    print()
    print("Layout:")
    print("  +-------------+------------------+------------------+")
    print("  | Template    |  Template        |  Template        |")
    print("  | List        |  Preview         |  Editor          |")
    print("  | (sidebar)   |  (content)       |  (form)          |")
    print("  +-------------+------------------+------------------+")
    print()
    print("Features:")
    print("  * Organized template library with categories")
    print("  * Live preview of template content and variables")
    print("  * Full-featured editor with variable support")
    print("  * Create, edit, and delete templates")
    print("  * Tabbed interface (Templates, Settings, Import/Export)")
    print()
    print("Controls:")
    print("  - Click templates in left panel to select")
    print("  - View template details in middle panel")
    print("  - Edit template in right panel")
    print("  - Use 'New' button to create new templates")
    print("  - Ctrl+N for new template")
    print("  - Ctrl+S to save (mockup)")
    print("  - Ctrl+Q to quit")
    print()
    print("=" * 70)
    print()

    # Import and run the app directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "template_editor_mockup",
        src_path / "presentation" / "tui" / "components" / "template_editor_mockup.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.main()


if __name__ == "__main__":
    main()
