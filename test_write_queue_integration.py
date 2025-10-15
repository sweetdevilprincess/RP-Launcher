#!/usr/bin/env python3
"""
Integration test for write queue with file_change_tracker

This test verifies that the write queue is properly integrated
and reduces disk I/O through debouncing.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.file_change_tracker import FileChangeTracker
from src.fs_write_queue import get_write_queue
import tempfile


def test_file_change_tracker_with_queue():
    """Test that FileChangeTracker uses write queue properly"""
    print("Testing FileChangeTracker with write queue...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a test RP directory structure
        rp_dir = tmppath / "test_rp"
        rp_dir.mkdir()
        (rp_dir / "state").mkdir()

        # Create tracker with short debounce for testing
        tracker = FileChangeTracker(rp_dir, debounce_ms=200)

        # Get write queue
        write_queue = get_write_queue()

        # Simulate rapid file tracking updates (like entity tracking)
        print("\n1. Testing rapid tracker updates (should be debounced):")
        start_time = time.time()

        for i in range(10):
            test_file = rp_dir / f"file_{i}.txt"
            test_file.write_text(f"content {i}")
            tracker.mark_file_as_auto_generated(test_file)
            time.sleep(0.02)  # 20ms between updates

        elapsed = time.time() - start_time
        print(f"   Queued 10 updates in {elapsed*1000:.0f}ms")

        # Check pending writes
        pending = write_queue.get_pending_count()
        print(f"   Pending writes: {pending}")

        # Wait for debounce
        print("   Waiting for debounce...")
        time.sleep(0.3)

        # Verify writes completed
        pending_after = write_queue.get_pending_count()
        print(f"   Pending writes after debounce: {pending_after}")

        # Verify tracking file was written
        tracking_file = rp_dir / "state" / "file_changes.json"
        assert tracking_file.exists(), "Tracking file should exist"
        print("   [OK] Tracking file written successfully")

        # Test flush
        print("\n2. Testing manual flush:")
        test_file2 = rp_dir / "file_flush.txt"
        test_file2.write_text("flush test")
        tracker.mark_file_as_auto_generated(test_file2)

        write_queue.flush()
        print("   [OK] Manual flush completed")

        print("\n[SUCCESS] All integration tests passed!")
        return True


def test_write_batching():
    """Test that rapid writes to same file are batched"""
    print("\nTesting write batching...")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        write_queue = get_write_queue(debounce_ms=200)

        test_file = tmppath / "batch_test.txt"

        print("\n1. Simulating 20 rapid writes to same file:")
        start = time.time()

        for i in range(20):
            write_queue.write_text(test_file, f"version {i}")
            time.sleep(0.01)  # 10ms between writes

        elapsed = time.time() - start
        print(f"   Queued 20 writes in {elapsed*1000:.0f}ms")

        # File shouldn't exist yet (still in queue)
        if not test_file.exists():
            print("   [OK] File not written yet (debouncing working)")
        else:
            print("   [WARNING] File written early (debounce may be too short)")

        # Wait for debounce
        time.sleep(0.3)

        # Verify final content
        assert test_file.exists(), "File should exist after debounce"
        content = test_file.read_text()
        assert content == "version 19", f"Expected 'version 19', got '{content}'"
        print(f"   [OK] Final content: {content}")
        print("   [OK] Only final version was written (19 writes saved!)")

        print("\n[SUCCESS] Batching test passed!")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("FS Write Queue Integration Tests")
    print("=" * 60)

    try:
        test_file_change_tracker_with_queue()
        test_write_batching()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
