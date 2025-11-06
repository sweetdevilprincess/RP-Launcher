"""Tests for security and bug fixes in ConfigLoader.

Tests verify:
1. Mutable defaults bug is fixed (deepcopy protection)
2. Secret logging is redacted
3. Unicode arrows are replaced with ASCII
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.config.config_loader import ConfigLoader
from src.infrastructure.config.defaults import get_default_config


def test_mutable_defaults_fix():
    """Verify that get_default_config() returns a deep copy, not references.

    Bug: Previously, get_default_config() returned dict references to global
    constants. Any mutation via ConfigLoader.set() would modify the global
    defaults, affecting all future loads.

    Fix: Now uses deepcopy to return isolated copies.
    """
    # Get first config
    config1 = get_default_config()

    # Mutate it
    config1["system"]["log_level"] = "MUTATED"
    config1["modules"]["claude_api_client"]["config"]["model"] = "MUTATED"

    # Get second config - should be clean, not mutated
    config2 = get_default_config()

    # Verify second config has original defaults, not mutations
    assert config2["system"]["log_level"] == "INFO", "System defaults were mutated!"
    assert (
        config2["modules"]["claude_api_client"]["config"]["model"] == "claude-3-5-sonnet-20241022"
    ), "Module defaults were mutated!"


def test_config_loader_isolation():
    """Verify that ConfigLoader instances don't share mutable state.

    Bug: If defaults were shared by reference, changing config in one loader
    would affect other loaders.

    Fix: Each loader gets its own deep copy of defaults.
    """
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:

        dir1 = Path(tmpdir1)
        dir2 = Path(tmpdir2)

        # Create two loaders
        loader1 = ConfigLoader(dir1)
        loader2 = ConfigLoader(dir2)

        # Load configs
        config1 = loader1.load(create_if_missing=True)
        config2 = loader2.load(create_if_missing=True)

        # Mutate loader1's config
        loader1.set("system.log_level", "ERROR")

        # Verify loader2's config is unchanged
        assert (
            loader2.config["system"]["log_level"] == "INFO"
        ), "Mutation in loader1 affected loader2!"


def test_secret_logging_redaction():
    """Verify that ConfigLoader.set() redacts sensitive values in logs.

    Security Issue: Previously, set() logged the value directly, exposing
    API keys and other secrets in log files.

    Fix: Now redacts values if key contains sensitive keywords.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir)

        # Create mock logger to capture log calls
        mock_logger = MagicMock()

        loader = ConfigLoader(rp_dir)
        loader.logger = mock_logger
        loader.load(create_if_missing=True)

        # Test sensitive keys - should be redacted
        sensitive_keys = [
            ("modules.claude_api_client.config.api_key", "sk-ant-secret123"),
            ("modules.openai_client.config.api_key", "sk-openai-secret456"),
            ("auth.token", "bearer-token-789"),
            ("system.password", "super-secret"),
            ("proxy.secret", "proxy-secret"),
        ]

        for key, value in sensitive_keys:
            mock_logger.reset_mock()
            loader.set(key, value)

            # Check that logger.info was called
            assert mock_logger.info.called, f"Logger not called for {key}"

            # Get the log message
            log_message = mock_logger.info.call_args[0][0]

            # Verify secret is NOT in the log message
            assert (
                value not in log_message
            ), f"Secret value '{value}' leaked in log for key '{key}': {log_message}"

            # Verify [REDACTED] is in the log message
            assert (
                "[REDACTED]" in log_message
            ), f"Expected [REDACTED] in log for key '{key}': {log_message}"

        # Test non-sensitive keys - should NOT be redacted
        non_sensitive_keys = [
            ("system.log_level", "DEBUG"),
            ("system.auto_save", True),
            ("system.backup_frequency", 10),
        ]

        for key, value in non_sensitive_keys:
            mock_logger.reset_mock()
            loader.set(key, value)

            # Get the log message
            log_message = mock_logger.info.call_args[0][0]

            # Verify value IS in the log message (not redacted)
            assert (
                str(value) in log_message
            ), f"Non-sensitive value should be logged for key '{key}': {log_message}"

            # Verify [REDACTED] is NOT in the log message
            assert (
                "[REDACTED]" not in log_message
            ), f"Non-sensitive value should not be redacted for key '{key}': {log_message}"


def test_ascii_arrows_in_validation_messages():
    """Verify that validation messages use ASCII arrows, not Unicode.

    UX Issue: Previously used Unicode arrow (→) which doesn't render on
    Windows default console, showing as replacement glyph.

    Fix: Now uses ASCII arrow (->) for portability.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_dir = Path(tmpdir)
        loader = ConfigLoader(rp_dir)

        # Get validation issues
        issues = loader.validate_rp_directory()

        # Should have issues (directory is empty)
        assert len(issues) > 0, "Expected validation issues for empty directory"

        # Verify all issues use ASCII arrows, not Unicode
        for issue in issues:
            assert "→" not in issue, f"Unicode arrow found in validation message: {issue}"
            assert (
                "\u2192" not in issue
            ), f"Unicode arrow (escaped) found in validation message: {issue}"

            # If issue has suggestions, they should use ASCII arrows
            if ":" in issue and "\n" in issue:
                assert (
                    "->" in issue or "  " in issue
                ), f"Expected ASCII arrow in multi-line message: {issue}"


if __name__ == "__main__":
    # Run tests manually
    print("Testing mutable defaults fix...")
    test_mutable_defaults_fix()
    print("✅ PASS: Mutable defaults fix verified")

    print("\nTesting config loader isolation...")
    test_config_loader_isolation()
    print("✅ PASS: Config loader isolation verified")

    print("\nTesting secret logging redaction...")
    test_secret_logging_redaction()
    print("✅ PASS: Secret logging redaction verified")

    print("\nTesting ASCII arrows in validation...")
    test_ascii_arrows_in_validation_messages()
    print("✅ PASS: ASCII arrows verified")

    print("\n" + "=" * 60)
    print("ALL SECURITY FIXES VERIFIED ✅")
    print("=" * 60)
