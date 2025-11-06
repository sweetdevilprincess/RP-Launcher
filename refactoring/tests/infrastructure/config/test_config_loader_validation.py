"""Tests for ConfigLoader validation functionality."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.config.config_loader import ConfigLoader


@pytest.fixture
def temp_rp_dir():
    """Create a temporary RP directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_loader(temp_rp_dir):
    """Create a ConfigLoader instance for testing."""
    return ConfigLoader(temp_rp_dir)


# ==============================================================================
# Configuration Loading Tests
# ==============================================================================


def test_load_creates_default_config(temp_rp_dir):
    """Test that load() creates default config.json if missing."""
    loader = ConfigLoader(temp_rp_dir)
    config = loader.load(create_if_missing=True)

    # Should have created config.json
    assert (temp_rp_dir / "config.json").exists()

    # Should have all required keys
    assert "version" in config
    assert "system" in config
    assert "modules" in config


def test_load_fails_if_missing_and_not_create(temp_rp_dir):
    """Test that load() raises error if config missing and create_if_missing=False."""
    loader = ConfigLoader(temp_rp_dir)

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        loader.load(create_if_missing=False)


def test_load_from_config_json(temp_rp_dir):
    """Test loading configuration from config.json."""
    # Create a config.json with custom values
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "version": "2.0.0",
        "system": {"log_level": "DEBUG", "auto_save": False},
        "modules": {},
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    # Load config
    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have merged with defaults
    assert config["system"]["log_level"] == "DEBUG"
    assert config["system"]["auto_save"] is False
    assert "backup_frequency" in config["system"]  # From defaults


def test_load_from_env_file(temp_rp_dir):
    """Test loading configuration from .env file."""
    # Create .env file
    env_file = temp_rp_dir / ".env"
    env_content = """
# System config
RP_SYSTEM_LOG_LEVEL=WARNING
RP_SYSTEM_AUTO_SAVE=false

# API keys
ANTHROPIC_API_KEY=test_key_123
"""
    env_file.write_text(env_content)

    # Load config
    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have applied .env values
    assert config["system"]["log_level"] == "WARNING"
    assert config["system"]["auto_save"] is False
    assert config["modules"]["claude_api_client"]["config"]["api_key"] == "test_key_123"


def test_env_variable_precedence(temp_rp_dir):
    """Test that environment variables override config.json and .env."""
    # Create config.json
    config_file = temp_rp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump({"system": {"log_level": "INFO"}}, f)

    # Create .env
    env_file = temp_rp_dir / ".env"
    env_file.write_text("RP_SYSTEM_LOG_LEVEL=WARNING")

    # Set environment variable (highest priority)
    with patch.dict(os.environ, {"RP_SYSTEM_LOG_LEVEL": "ERROR"}):
        loader = ConfigLoader(temp_rp_dir)
        config = loader.load()

        # ENV var should win
        assert config["system"]["log_level"] == "ERROR"


def test_deep_merge_preserves_nested_structure(temp_rp_dir):
    """Test that deep merge preserves nested structure."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "modules": {
            "claude_api_client": {
                "enabled": True,
                "config": {"temperature": 0.9},  # Only override temperature
            }
        }
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Temperature should be overridden
    assert config["modules"]["claude_api_client"]["config"]["temperature"] == 0.9

    # But other defaults should be preserved
    assert "model" in config["modules"]["claude_api_client"]["config"]
    assert "max_tokens" in config["modules"]["claude_api_client"]["config"]


# ==============================================================================
# Type Validation Tests
# ==============================================================================


def test_validate_invalid_log_level(temp_rp_dir):
    """Test validation catches invalid log level."""
    config_file = temp_rp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump({"system": {"log_level": "INVALID"}}, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Validation should fail
    assert not loader.validate()


def test_validate_invalid_auto_save_type(temp_rp_dir):
    """Test validation catches wrong type for auto_save."""
    config_file = temp_rp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump({"system": {"auto_save": "yes"}}, f)  # Should be bool

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Validation should fail
    assert not loader.validate()


def test_validate_invalid_temperature(temp_rp_dir):
    """Test validation catches temperature out of range."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "modules": {"claude_api_client": {"config": {"temperature": 1.5}}}  # Out of range (0.0-1.0)
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Validation should fail
    assert not loader.validate()


def test_validate_invalid_max_tokens(temp_rp_dir):
    """Test validation catches negative max_tokens."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "modules": {"claude_api_client": {"config": {"max_tokens": -100}}}  # Must be positive
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Validation should fail
    assert not loader.validate()


def test_validate_invalid_timeout(temp_rp_dir):
    """Test validation catches invalid timeout value."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "modules": {"agent_coordinator": {"config": {"timeout": 0}}}  # Must be positive
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Validation should fail
    assert not loader.validate()


def test_validate_valid_configuration(temp_rp_dir):
    """Test that validation passes for valid configuration."""
    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Default config should be valid
    assert loader.validate()


# ==============================================================================
# Unknown Field Warning Tests
# ==============================================================================


def test_warn_unknown_system_field(temp_rp_dir):
    """Test that unknown system fields generate warnings."""
    config_file = temp_rp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump({"system": {"unknown_field": "value"}}, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have warning
    assert len(loader._validation_warnings) > 0
    assert any("unknown_field" in w for w in loader._validation_warnings)


def test_warn_unknown_module(temp_rp_dir):
    """Test that unknown modules generate warnings."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {"modules": {"nonexistent_module": {"enabled": True, "config": {}}}}

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have warning
    assert len(loader._validation_warnings) > 0
    assert any("nonexistent_module" in w for w in loader._validation_warnings)


def test_warn_unknown_module_config_field(temp_rp_dir):
    """Test that unknown module config fields generate warnings."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {"modules": {"claude_api_client": {"config": {"unknown_setting": "value"}}}}

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have warning
    assert len(loader._validation_warnings) > 0
    assert any("unknown_setting" in w for w in loader._validation_warnings)


def test_suggest_similar_field(temp_rp_dir):
    """Test that typos in field names get suggestions."""
    config_file = temp_rp_dir / "config.json"
    custom_config = {
        "modules": {
            "claude_api_client": {"config": {"max_token": 8000}}  # Typo: should be max_tokens
        }
    }

    with open(config_file, "w") as f:
        json.dump(custom_config, f)

    loader = ConfigLoader(temp_rp_dir)
    config = loader.load()

    # Should have warning with suggestion
    assert len(loader._validation_warnings) > 0
    warnings_text = " ".join(loader._validation_warnings)
    assert "max_token" in warnings_text
    assert "max_tokens" in warnings_text  # Suggestion


# ==============================================================================
# Environment Variable Parsing Tests
# ==============================================================================


def test_parse_env_boolean_true(config_loader):
    """Test parsing boolean true values from environment."""
    assert config_loader._parse_env_value("true") is True
    assert config_loader._parse_env_value("True") is True
    assert config_loader._parse_env_value("yes") is True
    assert config_loader._parse_env_value("1") is True
    assert config_loader._parse_env_value("on") is True


def test_parse_env_boolean_false(config_loader):
    """Test parsing boolean false values from environment."""
    assert config_loader._parse_env_value("false") is False
    assert config_loader._parse_env_value("False") is False
    assert config_loader._parse_env_value("no") is False
    assert config_loader._parse_env_value("0") is False
    assert config_loader._parse_env_value("off") is False


def test_parse_env_integer(config_loader):
    """Test parsing integer values from environment."""
    assert config_loader._parse_env_value("42") == 42
    assert config_loader._parse_env_value("0") == 0
    assert config_loader._parse_env_value("-10") == -10


def test_parse_env_float(config_loader):
    """Test parsing float values from environment."""
    assert config_loader._parse_env_value("0.7") == 0.7
    assert config_loader._parse_env_value("1.0") == 1.0
    assert config_loader._parse_env_value("-3.14") == -3.14


def test_parse_env_string(config_loader):
    """Test parsing string values from environment."""
    assert config_loader._parse_env_value("hello") == "hello"
    assert config_loader._parse_env_value("api_key_123") == "api_key_123"
    assert config_loader._parse_env_value("") == ""


# ==============================================================================
# Module Access Tests
# ==============================================================================


def test_get_module_config(temp_rp_dir):
    """Test getting module configuration."""
    loader = ConfigLoader(temp_rp_dir)
    loader.load()

    session_config = loader.get_module_config("session_manager")

    assert isinstance(session_config, dict)
    assert "auto_checkpoint_frequency" in session_config


def test_is_module_enabled(temp_rp_dir):
    """Test checking if module is enabled."""
    loader = ConfigLoader(temp_rp_dir)
    loader.load()

    # Session manager should be enabled by default
    assert loader.is_module_enabled("session_manager")


def test_set_module_enabled(temp_rp_dir):
    """Test enabling/disabling modules."""
    loader = ConfigLoader(temp_rp_dir)
    loader.load()

    # Disable a module
    loader.set_module_enabled("update_checker", False)
    assert not loader.is_module_enabled("update_checker")

    # Enable it again
    loader.set_module_enabled("update_checker", True)
    assert loader.is_module_enabled("update_checker")


def test_list_enabled_modules(temp_rp_dir):
    """Test listing enabled modules."""
    loader = ConfigLoader(temp_rp_dir)
    loader.load()

    enabled = loader.list_enabled_modules()

    assert isinstance(enabled, list)
    assert "file_manager" in enabled  # Should be enabled by default


# ==============================================================================
# Precedence Integration Tests
# ==============================================================================


def test_full_precedence_chain(temp_rp_dir):
    """Test complete precedence: defaults < .env < config.json < ENV."""
    # Layer 1: defaults.py (log_level = INFO)

    # Layer 2: .env file
    env_file = temp_rp_dir / ".env"
    env_file.write_text("RP_SYSTEM_AUTO_SAVE=false")

    # Layer 3: config.json
    config_file = temp_rp_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(
            {
                "system": {
                    "log_level": "WARNING",  # Overrides default
                    "backup_frequency": 5,  # Overrides default
                }
            },
            f,
        )

    # Layer 4: Environment variable (highest)
    with patch.dict(os.environ, {"RP_SYSTEM_LOG_LEVEL": "ERROR"}):
        loader = ConfigLoader(temp_rp_dir)
        config = loader.load()

        # Check precedence
        assert config["system"]["log_level"] == "ERROR"  # From ENV
        assert config["system"]["backup_frequency"] == 5  # From config.json
        assert config["system"]["auto_save"] is False  # From .env
        assert config["system"]["max_backups"] == 20  # From defaults


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
