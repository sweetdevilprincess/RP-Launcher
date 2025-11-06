"""Migration script for legacy session formats to SessionData v2.

Supports migration from:
- Legacy conversation.json (flat message array)
- Old session_state.json (mixed state format)
- Custom session exports

Usage:
    python migrate_sessions.py <legacy_file> [--output <output_file>]
    python migrate_sessions.py --batch <legacy_dir> --output-dir <output_dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MigrationReport:
    """Report of migration results."""

    total_files: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[Dict[str, str]] = field(default_factory=list)

    def add_success(self) -> None:
        """Record successful migration."""
        self.successful += 1

    def add_failure(self, file_path: str, error: str) -> None:
        """Record failed migration."""
        self.failed += 1
        self.errors.append({"file": file_path, "error": error})

    def add_skip(self) -> None:
        """Record skipped file."""
        self.skipped += 1

    def print_summary(self) -> None:
        """Print migration summary."""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Total files processed: {self.total_files}")
        print(f"Successful migrations: {self.successful}")
        print(f"Failed migrations: {self.failed}")
        print(f"Skipped files: {self.skipped}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error['file']}: {error['error']}")
        print("=" * 60 + "\n")


class SessionMigrator:
    """Migrate legacy session formats to SessionData v2."""

    def __init__(self, *, verbose: bool = False) -> None:
        """Initialize migrator.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose

    def migrate_v1_conversation(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy conversation.json format.

        Legacy format:
        {
            "messages": [
                {"user": "...", "assistant": "...", "timestamp": "..."},
                ...
            ],
            "metadata": {"rp_name": "...", "chapter": 1}
        }

        Args:
            legacy_data: Legacy conversation data

        Returns:
            SessionData v2 dict
        """
        now_iso = datetime.now(tz=UTC).isoformat()

        # Extract messages
        legacy_messages = legacy_data.get("messages", [])
        new_messages = []

        for idx, msg in enumerate(legacy_messages, start=1):
            new_messages.append({
                "response_num": idx,
                "timestamp": msg.get("timestamp", now_iso),
                "chapter": msg.get("chapter", 1),
                "user_message": msg.get("user", ""),
                "assistant_response": msg.get("assistant", ""),
                "agent_data_background": {},
                "agent_data_immediate": {},
                "model_info": {},
                "status": None,
            })

        # Extract metadata
        metadata = legacy_data.get("metadata", {})
        rp_name = metadata.get("rp_name", "Migrated RP")
        chapter = metadata.get("chapter", 1)

        # Build v2 session
        return {
            "session_id": "main",
            "session_type": "active",
            "parent_session": None,
            "branch_point": None,
            "created": now_iso,
            "last_modified": now_iso,
            "current_response": len(new_messages),
            "tags": ["migrated-v1", f"chapter-{chapter}"],
            "description": f"Migrated from legacy conversation.json",
            "rp_metadata": {
                "rp_name": rp_name,
                "chapter": chapter,
                "scene": "",
            },
            "messages": new_messages,
            "total_duration_seconds": 0.0,
            "checkpoints": [],
        }

    def migrate_v1_session_state(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy session_state.json format.

        Legacy format:
        {
            "session_id": "...",
            "conversation_history": [...],
            "current_chapter": 1,
            "rp_name": "..."
        }

        Args:
            legacy_data: Legacy session state data

        Returns:
            SessionData v2 dict
        """
        now_iso = datetime.now(tz=UTC).isoformat()

        # Extract conversation history
        history = legacy_data.get("conversation_history", [])
        new_messages = []

        for idx, entry in enumerate(history, start=1):
            # Handle different legacy formats
            if isinstance(entry, dict):
                user_msg = entry.get("user", entry.get("user_message", ""))
                assistant_msg = entry.get("assistant", entry.get("assistant_response", ""))
                timestamp = entry.get("timestamp", now_iso)
                chapter = entry.get("chapter", legacy_data.get("current_chapter", 1))
            else:
                # Skip malformed entries
                continue

            new_messages.append({
                "response_num": idx,
                "timestamp": timestamp,
                "chapter": chapter,
                "user_message": user_msg,
                "assistant_response": assistant_msg,
                "agent_data_background": {},
                "agent_data_immediate": {},
                "model_info": {},
                "status": None,
            })

        session_id = legacy_data.get("session_id", "main")
        rp_name = legacy_data.get("rp_name", "Migrated RP")
        chapter = legacy_data.get("current_chapter", 1)

        return {
            "session_id": session_id,
            "session_type": "active",
            "parent_session": None,
            "branch_point": None,
            "created": legacy_data.get("created_at", now_iso),
            "last_modified": now_iso,
            "current_response": len(new_messages),
            "tags": ["migrated-session-state", f"chapter-{chapter}"],
            "description": f"Migrated from legacy session_state.json",
            "rp_metadata": {
                "rp_name": rp_name,
                "chapter": chapter,
                "scene": legacy_data.get("current_scene", ""),
            },
            "messages": new_messages,
            "total_duration_seconds": 0.0,
            "checkpoints": [],
        }

    def detect_format(self, data: Dict[str, Any]) -> str:
        """Detect legacy session format.

        Args:
            data: Legacy session data

        Returns:
            Format identifier: "v1_conversation", "v1_session_state", "v2", or "unknown"
        """
        # Check if already v2
        if "total_duration_seconds" in data and "checkpoints" in data:
            return "v2"

        # Check for conversation.json format
        if "messages" in data and isinstance(data["messages"], list):
            # Check message structure
            if data["messages"] and "user" in data["messages"][0]:
                return "v1_conversation"

        # Check for session_state.json format
        if "conversation_history" in data:
            return "v1_session_state"

        # Check if it's already close to v2 (just missing new fields)
        if "session_id" in data and "messages" in data and "current_response" in data:
            return "v2_partial"

        return "unknown"

    def migrate_file(self, legacy_file: Path, output_file: Optional[Path] = None) -> bool:
        """Migrate a single legacy session file.

        Args:
            legacy_file: Path to legacy session file
            output_file: Optional output path (defaults to <legacy_file>_v2.json)

        Returns:
            True if migration succeeded, False otherwise
        """
        if self.verbose:
            print(f"Migrating: {legacy_file}")

        try:
            # Load legacy data
            with open(legacy_file, "r", encoding="utf-8") as f:
                legacy_data = json.load(f)

            # Detect format
            format_type = self.detect_format(legacy_data)
            if self.verbose:
                print(f"  Detected format: {format_type}")

            # Migrate based on format
            if format_type == "v2":
                if self.verbose:
                    print("  Already v2 format, skipping")
                return False
            elif format_type == "v1_conversation":
                migrated_data = self.migrate_v1_conversation(legacy_data)
            elif format_type == "v1_session_state":
                migrated_data = self.migrate_v1_session_state(legacy_data)
            elif format_type == "v2_partial":
                # Just add missing fields
                migrated_data = legacy_data.copy()
                migrated_data.setdefault("total_duration_seconds", 0.0)
                migrated_data.setdefault("checkpoints", [])
                if "tags" not in migrated_data:
                    migrated_data["tags"] = ["migrated-partial"]
            else:
                raise ValueError(f"Unknown session format: {legacy_file}")

            # Determine output path
            if output_file is None:
                output_file = legacy_file.parent / f"{legacy_file.stem}_v2.json"

            # Write migrated data
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(migrated_data, f, indent=2)

            if self.verbose:
                print(f"  Migrated to: {output_file}")

            return True

        except Exception as exc:
            if self.verbose:
                print(f"  ERROR: {exc}")
            raise

    def batch_migrate(
        self,
        legacy_dir: Path,
        output_dir: Path,
        *,
        pattern: str = "*.json",
    ) -> MigrationReport:
        """Batch migrate all sessions in a directory.

        Args:
            legacy_dir: Directory containing legacy session files
            output_dir: Output directory for migrated sessions
            pattern: File glob pattern (default: *.json)

        Returns:
            MigrationReport with results
        """
        report = MigrationReport()

        # Find all matching files
        files = list(legacy_dir.glob(pattern))
        report.total_files = len(files)

        if self.verbose:
            print(f"Found {report.total_files} files to migrate")

        for legacy_file in files:
            try:
                # Determine output path (preserve filename)
                output_file = output_dir / legacy_file.name

                # Skip if output already exists
                if output_file.exists():
                    if self.verbose:
                        print(f"Skipping {legacy_file.name} (output exists)")
                    report.add_skip()
                    continue

                # Migrate
                success = self.migrate_file(legacy_file, output_file)
                if success:
                    report.add_success()
                else:
                    report.add_skip()

            except Exception as exc:
                report.add_failure(str(legacy_file), str(exc))

        return report

    def validate_migration(
        self,
        legacy_file: Path,
        migrated_file: Path,
    ) -> bool:
        """Verify migration correctness.

        Args:
            legacy_file: Original legacy file
            migrated_file: Migrated v2 file

        Returns:
            True if migration is valid, False otherwise
        """
        try:
            # Load both files
            with open(legacy_file, "r", encoding="utf-8") as f:
                legacy_data = json.load(f)

            with open(migrated_file, "r", encoding="utf-8") as f:
                migrated_data = json.load(f)

            # Basic checks
            if "messages" not in migrated_data:
                print("ERROR: Missing 'messages' field")
                return False

            if "current_response" not in migrated_data:
                print("ERROR: Missing 'current_response' field")
                return False

            if migrated_data["current_response"] != len(migrated_data["messages"]):
                print("ERROR: current_response doesn't match message count")
                return False

            # Validate message sequence
            for idx, msg in enumerate(migrated_data["messages"], start=1):
                if msg["response_num"] != idx:
                    print(f"ERROR: Message {idx} has wrong response_num: {msg['response_num']}")
                    return False

            # Check new fields exist
            if "total_duration_seconds" not in migrated_data:
                print("ERROR: Missing 'total_duration_seconds' field")
                return False

            if "checkpoints" not in migrated_data:
                print("ERROR: Missing 'checkpoints' field")
                return False

            print(f"✓ Migration validation passed: {migrated_file.name}")
            return True

        except Exception as exc:
            print(f"ERROR during validation: {exc}")
            return False


def main() -> int:
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate legacy session formats to SessionData v2"
    )

    # Single file migration
    parser.add_argument("legacy_file", nargs="?", type=Path, help="Legacy session file to migrate")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")

    # Batch migration
    parser.add_argument("--batch", "-b", type=Path, help="Batch migrate directory")
    parser.add_argument("--output-dir", type=Path, help="Output directory for batch migration")
    parser.add_argument("--pattern", default="*.json", help="File pattern for batch (default: *.json)")

    # Validation
    parser.add_argument("--validate", action="store_true", help="Validate migration after completion")

    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    migrator = SessionMigrator(verbose=args.verbose)

    # Batch migration
    if args.batch:
        if not args.output_dir:
            print("ERROR: --output-dir required for batch migration")
            return 1

        print(f"Batch migrating: {args.batch} → {args.output_dir}")
        report = migrator.batch_migrate(args.batch, args.output_dir, pattern=args.pattern)
        report.print_summary()
        return 0 if report.failed == 0 else 1

    # Single file migration
    if not args.legacy_file:
        parser.print_help()
        return 1

    try:
        success = migrator.migrate_file(args.legacy_file, args.output)

        if success:
            print(f"✓ Migration successful")

            # Validate if requested
            if args.validate:
                output_file = args.output or args.legacy_file.parent / f"{args.legacy_file.stem}_v2.json"
                migrator.validate_migration(args.legacy_file, output_file)

            return 0
        else:
            print("Migration skipped (already v2 format)")
            return 0

    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
