"""Tests for session migration from legacy formats.

Tests migration scripts and validation.
"""

import json

# Import migrator directly from scripts
import sys
import tempfile
from pathlib import Path

import pytest

scripts_path = Path(__file__).parent.parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from migrate_sessions import MigrationReport, SessionMigrator


class TestLegacyConversationMigration:
    """Test migration from legacy conversation.json format."""

    def test_migrate_simple_conversation(self):
        """Test migrating simple conversation format."""
        migrator = SessionMigrator()

        legacy_data = {
            "messages": [
                {
                    "user": "Hello",
                    "assistant": "Hi there",
                    "timestamp": "2025-01-01T10:00:00Z",
                },
                {
                    "user": "How are you?",
                    "assistant": "I'm doing well!",
                    "timestamp": "2025-01-01T10:01:00Z",
                },
            ],
            "metadata": {
                "rp_name": "Test RP",
                "chapter": 1,
            },
        }

        migrated = migrator.migrate_v1_conversation(legacy_data)

        # Verify structure
        assert migrated["session_id"] == "main"
        assert migrated["session_type"] == "active"
        assert len(migrated["messages"]) == 2
        assert migrated["current_response"] == 2

        # Verify messages
        msg1 = migrated["messages"][0]
        assert msg1["response_num"] == 1
        assert msg1["user_message"] == "Hello"
        assert msg1["assistant_response"] == "Hi there"
        assert msg1["timestamp"] == "2025-01-01T10:00:00Z"

        # Verify metadata
        assert migrated["rp_metadata"]["rp_name"] == "Test RP"
        assert migrated["rp_metadata"]["chapter"] == 1

        # Verify new fields
        assert "total_duration_seconds" in migrated
        assert "checkpoints" in migrated
        assert migrated["total_duration_seconds"] == 0.0
        assert migrated["checkpoints"] == []

    def test_migrate_conversation_with_chapters(self):
        """Test migration with chapter information in messages."""
        migrator = SessionMigrator()

        legacy_data = {
            "messages": [
                {
                    "user": "Message 1",
                    "assistant": "Response 1",
                    "timestamp": "2025-01-01T10:00:00Z",
                    "chapter": 1,
                },
                {
                    "user": "Message 2",
                    "assistant": "Response 2",
                    "timestamp": "2025-01-01T10:01:00Z",
                    "chapter": 2,
                },
            ],
            "metadata": {
                "rp_name": "Multi-Chapter RP",
            },
        }

        migrated = migrator.migrate_v1_conversation(legacy_data)

        assert migrated["messages"][0]["chapter"] == 1
        assert migrated["messages"][1]["chapter"] == 2


class TestLegacySessionStateMigration:
    """Test migration from legacy session_state.json format."""

    def test_migrate_session_state(self):
        """Test migrating session state format."""
        migrator = SessionMigrator()

        legacy_data = {
            "session_id": "test_session",
            "conversation_history": [
                {
                    "user": "User message 1",
                    "assistant": "Assistant response 1",
                    "timestamp": "2025-01-01T10:00:00Z",
                },
                {
                    "user": "User message 2",
                    "assistant": "Assistant response 2",
                    "timestamp": "2025-01-01T10:01:00Z",
                },
            ],
            "current_chapter": 3,
            "rp_name": "State Test RP",
            "current_scene": "Forest clearing",
            "created_at": "2025-01-01T09:00:00Z",
        }

        migrated = migrator.migrate_v1_session_state(legacy_data)

        # Verify structure
        assert migrated["session_id"] == "test_session"
        assert migrated["session_type"] == "active"
        assert len(migrated["messages"]) == 2
        assert migrated["current_response"] == 2

        # Verify metadata
        assert migrated["rp_metadata"]["rp_name"] == "State Test RP"
        assert migrated["rp_metadata"]["chapter"] == 3
        assert migrated["rp_metadata"]["scene"] == "Forest clearing"

        # Verify timestamps
        assert migrated["created"] == "2025-01-01T09:00:00Z"

        # Verify new fields
        assert "total_duration_seconds" in migrated
        assert "checkpoints" in migrated


class TestFormatDetection:
    """Test legacy format detection."""

    def test_detect_v1_conversation(self):
        """Test detecting v1 conversation format."""
        migrator = SessionMigrator()

        data = {
            "messages": [
                {"user": "Hello", "assistant": "Hi"},
            ],
            "metadata": {},
        }

        assert migrator.detect_format(data) == "v1_conversation"

    def test_detect_v1_session_state(self):
        """Test detecting v1 session state format."""
        migrator = SessionMigrator()

        data = {
            "session_id": "test",
            "conversation_history": [
                {"user": "Hello", "assistant": "Hi"},
            ],
        }

        assert migrator.detect_format(data) == "v1_session_state"

    def test_detect_v2_format(self):
        """Test detecting v2 format (already migrated)."""
        migrator = SessionMigrator()

        data = {
            "session_id": "main",
            "messages": [],
            "total_duration_seconds": 0.0,
            "checkpoints": [],
        }

        assert migrator.detect_format(data) == "v2"

    def test_detect_v2_partial(self):
        """Test detecting partial v2 format (missing new fields)."""
        migrator = SessionMigrator()

        data = {
            "session_id": "main",
            "messages": [],
            "current_response": 0,
            # Missing total_duration_seconds and checkpoints
        }

        assert migrator.detect_format(data) == "v2_partial"

    def test_detect_unknown_format(self):
        """Test detecting unknown format."""
        migrator = SessionMigrator()

        data = {
            "random_field": "value",
        }

        assert migrator.detect_format(data) == "unknown"


class TestFileMigration:
    """Test file-based migration."""

    def test_migrate_single_file(self):
        """Test migrating a single file."""
        migrator = SessionMigrator(verbose=False)

        legacy_data = {
            "messages": [
                {"user": "Test", "assistant": "Response", "timestamp": "2025-01-01T10:00:00Z"},
            ],
            "metadata": {"rp_name": "File Test"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write legacy file
            legacy_file = tmpdir_path / "legacy.json"
            with open(legacy_file, "w", encoding="utf-8") as f:
                json.dump(legacy_data, f)

            # Migrate
            output_file = tmpdir_path / "migrated.json"
            success = migrator.migrate_file(legacy_file, output_file)

            assert success
            assert output_file.exists()

            # Verify migrated content
            with open(output_file, encoding="utf-8") as f:
                migrated = json.load(f)

            assert "total_duration_seconds" in migrated
            assert "checkpoints" in migrated
            assert migrated["current_response"] == 1

    def test_skip_already_migrated(self):
        """Test that v2 files are skipped."""
        migrator = SessionMigrator(verbose=False)

        v2_data = {
            "session_id": "main",
            "messages": [],
            "total_duration_seconds": 0.0,
            "checkpoints": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write v2 file
            v2_file = tmpdir_path / "v2.json"
            with open(v2_file, "w", encoding="utf-8") as f:
                json.dump(v2_data, f)

            # Try to migrate (should skip)
            success = migrator.migrate_file(v2_file)

            assert not success  # Returns False for skipped files


class TestBatchMigration:
    """Test batch migration functionality."""

    def test_batch_migrate_directory(self):
        """Test batch migrating multiple files."""
        migrator = SessionMigrator(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_dir = tmpdir_path / "input"
            output_dir = tmpdir_path / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            # Create 3 legacy files
            for i in range(1, 4):
                legacy_data = {
                    "messages": [
                        {
                            "user": f"Test {i}",
                            "assistant": f"Response {i}",
                            "timestamp": "2025-01-01T10:00:00Z",
                        },
                    ],
                    "metadata": {"rp_name": f"RP {i}"},
                }
                with open(input_dir / f"session_{i}.json", "w", encoding="utf-8") as f:
                    json.dump(legacy_data, f)

            # Batch migrate
            report = migrator.batch_migrate(input_dir, output_dir)

            # Verify report
            assert report.total_files == 3
            assert report.successful == 3
            assert report.failed == 0
            assert report.skipped == 0

            # Verify output files exist
            for i in range(1, 4):
                output_file = output_dir / f"session_{i}.json"
                assert output_file.exists()

    def test_batch_migration_skips_existing(self):
        """Test that batch migration skips existing output files."""
        migrator = SessionMigrator(verbose=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_dir = tmpdir_path / "input"
            output_dir = tmpdir_path / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            # Create legacy file
            legacy_data = {
                "messages": [
                    {"user": "Test", "assistant": "Response", "timestamp": "2025-01-01T10:00:00Z"},
                ],
                "metadata": {},
            }
            with open(input_dir / "session.json", "w", encoding="utf-8") as f:
                json.dump(legacy_data, f)

            # Create existing output file
            with open(output_dir / "session.json", "w", encoding="utf-8") as f:
                json.dump({}, f)

            # Batch migrate
            report = migrator.batch_migrate(input_dir, output_dir)

            # Should skip existing file
            assert report.skipped == 1
            assert report.successful == 0


class TestMigrationValidation:
    """Test migration validation."""

    def test_validate_successful_migration(self):
        """Test validation of a successful migration."""
        migrator = SessionMigrator(verbose=False)

        legacy_data = {
            "messages": [
                {"user": "Test 1", "assistant": "Response 1", "timestamp": "2025-01-01T10:00:00Z"},
                {"user": "Test 2", "assistant": "Response 2", "timestamp": "2025-01-01T10:01:00Z"},
            ],
            "metadata": {"rp_name": "Validation Test"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write legacy file
            legacy_file = tmpdir_path / "legacy.json"
            with open(legacy_file, "w", encoding="utf-8") as f:
                json.dump(legacy_data, f)

            # Migrate
            migrated_file = tmpdir_path / "migrated.json"
            migrator.migrate_file(legacy_file, migrated_file)

            # Validate
            valid = migrator.validate_migration(legacy_file, migrated_file)

            assert valid


class TestMigrationReport:
    """Test MigrationReport functionality."""

    def test_report_tracking(self):
        """Test that report tracks results correctly."""
        report = MigrationReport()

        assert report.total_files == 0
        assert report.successful == 0
        assert report.failed == 0

        report.add_success()
        assert report.successful == 1

        report.add_failure("test.json", "Test error")
        assert report.failed == 1
        assert len(report.errors) == 1
        assert report.errors[0]["file"] == "test.json"

        report.add_skip()
        assert report.skipped == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
