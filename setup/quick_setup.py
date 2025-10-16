#!/usr/bin/env python3
"""
Quick Setup - Fast RP Creation Script
Creates a complete RP folder structure with all required files.

Usage:
    python setup/quick_setup.py "My RP Name"
    python setup/quick_setup.py "My RP Name" --template minimal
    python setup/quick_setup.py "My RP Name" --path /custom/path
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from initialize_rp import RPInitializer


def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print(" " * 20 + "RP QUICK SETUP" + " " * 36)
    print("=" * 70)
    print()


def print_success(rp_dir: Path, rp_name: str):
    """Print success message with next steps."""
    print()
    print("=" * 70)
    print(" " * 24 + "SUCCESS!" + " " * 39)
    print("=" * 70)
    print()
    print(f"✅ RP Created: {rp_name}")
    print(f"📁 Location: {rp_dir}")
    print()
    print("Next steps:")
    print()
    print("  1. (Optional) Customize your RP:")
    print(f"     - Edit: {rp_dir}/AUTHOR'S_NOTES.md")
    print(f"     - Edit: {rp_dir}/STORY_GENOME.md")
    print(f"     - Edit: {rp_dir}/characters/{{{{user}}}}.md")
    print()
    print("  2. Launch your RP:")
    print(f'     python launch_rp_tui.py "{rp_name}"')
    print()
    print("  3. Start writing!")
    print("     - Type your message")
    print("     - Press Ctrl+Enter to send")
    print("     - Get Claude's response")
    print("     - Continue your story!")
    print()
    print("=" * 70)
    print()
    print("📖 For help and guides, see: setup/README.md")
    print("✅ To verify setup, use: setup/CHECKLIST.md")
    print()


def copy_template(template_name: str, dest_dir: Path, rp_name: str) -> bool:
    """
    Copy template files from starter pack to destination.

    Args:
        template_name: Name of template (e.g., 'minimal')
        dest_dir: Destination RP directory
        rp_name: Name of the RP (for renaming RP_NAME.md)

    Returns:
        True if template was copied, False if not found
    """
    import shutil

    base_dir = Path(__file__).parent
    template_dir = base_dir / "templates" / "starter_packs" / template_name

    if not template_dir.exists():
        return False

    print(f"📦 Using template: {template_name}")
    print(f"   Copying from: {template_dir}")
    print()

    # Create destination if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy all template files and directories
    copied_count = 0
    for item in template_dir.iterdir():
        # Skip README.md from template (it's template documentation)
        if item.name == "README.md":
            continue

        dest_item = dest_dir / item.name

        # Handle RP_NAME.md renaming
        if item.name == "RP_NAME.md":
            dest_item = dest_dir / f"{rp_name}.md"

        try:
            if item.is_file():
                shutil.copy2(item, dest_item)
                print(f"  ✓ Copied: {item.name}")
                copied_count += 1
            elif item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
                print(f"  ✓ Copied directory: {item.name}/")
                copied_count += 1
        except Exception as e:
            print(f"  ⚠️  Warning: Could not copy {item.name}: {e}")

    print(f"\n  📄 Copied {copied_count} items from template")
    print()
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Quick setup for new RP - creates complete structure",
        epilog="Example: python setup/quick_setup.py \"Epic Fantasy Quest\""
    )

    parser.add_argument(
        "rp_name",
        type=str,
        help="Name of your RP (e.g., \"My Amazing Story\")"
    )

    parser.add_argument(
        "--template",
        type=str,
        default="minimal",
        choices=["minimal", "fantasy_adventure"],  # Add more as they become available
        help="Template to use (default: minimal)"
    )

    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom path for RP folder (default: project root)"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files (use with caution!)"
    )

    args = parser.parse_args()

    # Determine RP directory location
    if args.path:
        rp_dir = Path(args.path) / args.rp_name
    else:
        # Default: RPs folder in project root
        project_root = Path(__file__).parent.parent
        rps_dir = project_root / "RPs"
        # Ensure RPs directory exists
        rps_dir.mkdir(parents=True, exist_ok=True)
        rp_dir = rps_dir / args.rp_name

    # Print banner
    print_banner()

    # Check if RP already exists
    if rp_dir.exists() and not args.overwrite:
        print(f"⚠️  RP folder already exists: {rp_dir}")
        print()
        print("Options:")
        print(f"  1. Use a different name")
        print(f"  2. Delete the existing folder")
        print(f"  3. Run with --overwrite flag (will skip existing files)")
        print()
        sys.exit(1)

    # Step 1: Initialize directory structure first
    print(f"Creating RP: {args.rp_name}")
    print(f"Location: {rp_dir}")
    print()

    initializer = RPInitializer(rp_dir)
    initializer.initialize(
        rp_name=args.rp_name,
        skip_existing=True  # Always skip when using template
    )

    # Step 2: Copy template files (will add to or override structure)
    if args.template:
        template_found = copy_template(args.template, rp_dir, args.rp_name)
        if not template_found:
            print(f"⚠️  Template not found: {args.template}")
            print(f"   Using basic structure instead.")
            print()

    # Print success message
    print_success(rp_dir, args.rp_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
