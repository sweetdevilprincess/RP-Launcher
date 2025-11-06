"""Migration script for Memory-Session Consistency implementation.

This script migrates existing RPs to the new session state structure:
1. Creates state/session.json with proper timeline structure
2. Merges response_counter.json into session.json
3. Adds message_index to existing memory entries
4. Backs up original files before modification

Usage:
    python scripts/migrate_session_state.py <rp_directory>
    python scripts/migrate_session_state.py --all  # Migrate all RPs in parent directory
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


def backup_file(file_path: Path) -> Path:
    """Create timestamped backup of file.

    Args:
        file_path: File to backup

    Returns:
        Path to backup file
    """
    if not file_path.exists():
        return file_path

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
    shutil.copy2(file_path, backup_path)
    print(f"  [OK] Backed up {file_path.name} → {backup_path.name}")
    return backup_path


def create_session_state(rp_dir: Path, response_count: int = 0) -> dict:
    """Create initial session state structure.

    Args:
        rp_dir: RP directory path
        response_count: Current response count (from response_counter.json)

    Returns:
        Session state dictionary
    """
    return {
        "session_id": "main",
        "timeline": {
            "current_session_id": "main",
            "session_type": "active",
            "is_branch": False,
            "parent_session": None,
            "branch_point": None,
        },
        "arc_tracking": {
            "arc_file": "state/arc_main.md",
            "arc_session_id": "main",
        },
        "relationship_tracking": {
            "relationship_file": "state/relationships_main.json",
        },
        "plot_threads": {
            "thread_file": "state/plot_threads_main.json",
        },
        "rp_metadata": {
            "rp_title": rp_dir.name,
            "response_count": response_count,
            "total_messages": response_count * 2,  # Estimate: 1 user + 1 assistant per response
            "migrated_at": datetime.now(tz=UTC).isoformat(),
        },
    }


def migrate_response_counter(rp_dir: Path) -> int:
    """Read response counter from legacy file.

    Args:
        rp_dir: RP directory path

    Returns:
        Response count (0 if file doesn't exist)
    """
    counter_file = rp_dir / "state" / "response_counter.json"
    if not counter_file.exists():
        return 0

    try:
        with counter_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return int(data.get("count", 0))
    except (json.JSONDecodeError, ValueError, KeyError):
        print(f"  [WARN] Warning: Could not read {counter_file}, defaulting to count=0")
        return 0


def migrate_memory_files(rp_dir: Path, dry_run: bool = False) -> int:
    """Add message_index to memory entries in all memory files.

    Args:
        rp_dir: RP directory path
        dry_run: If True, don't actually modify files

    Returns:
        Number of memory files migrated
    """
    entities_dir = rp_dir / "entities"
    characters_dir = rp_dir / "characters"  # Legacy location

    # Check which directory exists
    base_dir = entities_dir if entities_dir.exists() else characters_dir
    if not base_dir.exists():
        print(f"  [INFO] No entities/characters directory found, skipping memory migration")
        return 0

    memory_files = list(base_dir.glob("*_memories.json"))
    if not memory_files:
        print(f"  [INFO] No memory files found in {base_dir}")
        return 0

    migrated_count = 0
    for memory_file in memory_files:
        try:
            with memory_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if "entries" not in data or not isinstance(data["entries"], list):
                continue

            # Check if already migrated
            if data["entries"] and "message_index" in data["entries"][0]:
                print(f"  [SKIP]  {memory_file.name} already has message_index, skipping")
                continue

            # Backup before modifying
            if not dry_run:
                backup_file(memory_file)

            # Add message_index to entries (assign sequentially based on position)
            modified = False
            for idx, entry in enumerate(data["entries"]):
                if "message_index" not in entry:
                    entry["message_index"] = idx
                    modified = True

            # Add session_id if not present
            if "session_id" not in data:
                data["session_id"] = "main"
                modified = True

            if modified and not dry_run:
                with memory_file.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  [OK] Migrated {memory_file.name} ({len(data['entries'])} entries)")
                migrated_count += 1
            elif modified:
                print(f"  [DRY RUN] Would migrate {memory_file.name} ({len(data['entries'])} entries)")
                migrated_count += 1

        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            print(f"  [WARN] Warning: Could not migrate {memory_file.name}: {exc}")

    return migrated_count


def migrate_rp(rp_dir: Path, dry_run: bool = False) -> bool:
    """Migrate a single RP to new session state structure.

    Args:
        rp_dir: RP directory path
        dry_run: If True, don't actually modify files

    Returns:
        True if migration was successful
    """
    print(f"\n[DIR] Migrating: {rp_dir.name}")
    print(f"   Path: {rp_dir}")

    # Ensure state directory exists
    state_dir = rp_dir / "state"
    if not dry_run:
        state_dir.mkdir(parents=True, exist_ok=True)

    session_file = state_dir / "session.json"

    # Check if already migrated
    if session_file.exists():
        try:
            with session_file.open("r", encoding="utf-8") as f:
                existing = json.load(f)
            if "migrated_at" in existing.get("rp_metadata", {}):
                print(f"  [SKIP]  Already migrated at {existing['rp_metadata']['migrated_at']}")
                return True
        except (json.JSONDecodeError, ValueError):
            pass  # File exists but corrupt, proceed with migration

    # Step 1: Read response counter
    response_count = migrate_response_counter(rp_dir)
    if response_count > 0:
        print(f"  [OK] Found response counter: {response_count}")

    # Step 2: Create session state
    session_state = create_session_state(rp_dir, response_count)

    if not dry_run:
        # Backup existing session.json if it exists
        if session_file.exists():
            backup_file(session_file)

        # Write new session state
        with session_file.open("w", encoding="utf-8") as f:
            json.dump(session_state, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Created state/session.json")
    else:
        print(f"  [DRY RUN] Would create state/session.json")

    # Step 3: Migrate memory files
    memory_count = migrate_memory_files(rp_dir, dry_run=dry_run)
    if memory_count > 0:
        print(f"  [OK] Migrated {memory_count} memory file(s)")

    print(f"  [DONE] Migration complete!")
    return True


def main():
    """Main entry point for migration script."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("[DRY RUN] DRY RUN MODE - No files will be modified\n")

    if arg == "--all":
        # Migrate all RPs in parent directory
        # Assuming script is in refactoring/scripts, RPs are in refactoring/..
        script_dir = Path(__file__).parent
        rp_parent = script_dir.parent.parent

        print(f"Searching for RPs in: {rp_parent}")
        rp_dirs = [d for d in rp_parent.iterdir() if d.is_dir() and (d / "state").exists()]

        if not rp_dirs:
            print("No RP directories found (looking for directories with 'state' subdirectory)")
            sys.exit(1)

        print(f"Found {len(rp_dirs)} RP(s) to migrate\n")

        success_count = 0
        for rp_dir in sorted(rp_dirs):
            try:
                if migrate_rp(rp_dir, dry_run=dry_run):
                    success_count += 1
            except Exception as exc:
                print(f"  [ERROR] Error migrating {rp_dir.name}: {exc}")

        print(f"\n{'[DRY RUN] ' if dry_run else ''}[DONE] Successfully migrated {success_count}/{len(rp_dirs)} RP(s)")

    else:
        # Migrate single RP
        rp_dir = Path(arg).resolve()
        if not rp_dir.exists():
            print(f"Error: Directory not found: {rp_dir}")
            sys.exit(1)

        try:
            migrate_rp(rp_dir, dry_run=dry_run)
        except Exception as exc:
            print(f"[ERROR] Error: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    main()
