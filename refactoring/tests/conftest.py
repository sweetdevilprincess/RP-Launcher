"""
Test configuration and shared fixtures for refactoring package.

This module provides:
- Path setup for importing src modules
- Common fixtures for temporary RP directories
- Factories for creating test entities and configurations
- Automatic test markers for organization
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

# ==============================================================================
# Path Setup
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ==============================================================================
# Temporary Directory Fixtures
# ==============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory that is cleaned up after the test.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_rp_dir(temp_dir: Path) -> Path:
    """Create a temporary RP directory with standard structure.

    Creates:
        - config/ (for configuration files)
        - state/ (for session state)
        - entities/ (for entity fixtures)
          - characters/
          - locations/
          - organizations/
          - items/
        - templates/ (for prompt templates)
        - logs/ (for log files)

    Args:
        temp_dir: Base temporary directory

    Returns:
        Path to configured RP directory
    """
    rp_dir = temp_dir / "test_rp"
    rp_dir.mkdir()

    # Create standard subdirectories
    (rp_dir / "config").mkdir()
    (rp_dir / "state").mkdir()
    (rp_dir / "logs").mkdir()
    (rp_dir / "templates").mkdir()

    # Create entity subdirectories
    entities_dir = rp_dir / "entities"
    entities_dir.mkdir()
    (entities_dir / "characters").mkdir()
    (entities_dir / "locations").mkdir()
    (entities_dir / "organizations").mkdir()
    (entities_dir / "items").mkdir()

    return rp_dir


@pytest.fixture
def temp_rp_with_config(temp_rp_dir: Path) -> Path:
    """Create a temporary RP directory with default config.json.

    Args:
        temp_rp_dir: Base RP directory

    Returns:
        Path to RP directory with config.json
    """
    config_file = temp_rp_dir / "config.json"

    default_config = {
        "version": "2.0.0",
        "system": {
            "log_level": "INFO",
            "auto_save": True,
            "backup_frequency": 10,
            "max_backups": 20,
        },
        "modules": {
            "session_manager": {
                "enabled": True,
                "config": {"auto_checkpoint_frequency": 10, "keep_archived": 20},
            }
        },
    }

    with open(config_file, "w") as f:
        json.dump(default_config, f, indent=2)

    return temp_rp_dir


# ==============================================================================
# Entity Fixture Factories
# ==============================================================================


@pytest.fixture
def character_factory() -> Callable[..., dict[str, Any]]:
    """Factory for creating test character entities.

    Returns:
        Function that creates character dict with given name
    """

    def _make_character(name: str, **overrides) -> dict[str, Any]:
        """Create a character entity dict.

        Args:
            name: Character name
            **overrides: Fields to override in character

        Returns:
            Character entity dictionary
        """
        character = {
            "name": name,
            "basics": {"age": "25", "gender": "female", "species": "human"},
            "appearance": {
                "height": "5'6\"",
                "build": "athletic",
                "hair": "brown",
                "eyes": "green",
            },
            "personality": {
                "traits": ["brave", "curious", "loyal"],
                "likes": ["adventure", "books"],
                "dislikes": ["dishonesty"],
            },
            "background": {"origin": "Small village", "occupation": "Adventurer"},
            "core_mandate": f"{name} is a brave adventurer who values honor above all",
        }

        # Apply overrides
        character.update(overrides)
        return character

    return _make_character


@pytest.fixture
def location_factory() -> Callable[..., dict[str, Any]]:
    """Factory for creating test location entities.

    Returns:
        Function that creates location dict with given name
    """

    def _make_location(name: str, **overrides) -> dict[str, Any]:
        """Create a location entity dict.

        Args:
            name: Location name
            **overrides: Fields to override

        Returns:
            Location entity dictionary
        """
        location = {
            "name": name,
            "type": "city",
            "description": f"A bustling {name}",
            "notable_features": ["marketplace", "town hall"],
            "inhabitants": [],
            "atmosphere": "lively",
        }

        location.update(overrides)
        return location

    return _make_location


@pytest.fixture
def create_character_file(
    temp_rp_dir: Path, character_factory: Callable[..., dict[str, Any]]
) -> Callable[..., Path]:
    """Factory for creating character JSON files.

    Args:
        temp_rp_dir: RP directory
        character_factory: Character factory fixture

    Returns:
        Function that creates character file
    """

    def _create_file(name: str, **overrides) -> Path:
        """Create a character JSON file.

        Args:
            name: Character name
            **overrides: Character field overrides

        Returns:
            Path to created character file
        """
        character = character_factory(name, **overrides)
        char_file = temp_rp_dir / "entities" / "characters" / f"{name.lower()}.json"

        with open(char_file, "w") as f:
            json.dump(character, f, indent=2)

        return char_file

    return _create_file


# ==============================================================================
# Session State Fixtures
# ==============================================================================


@pytest.fixture
def session_state_factory() -> Callable[..., dict[str, Any]]:
    """Factory for creating test session states.

    Returns:
        Function that creates session state dict
    """

    def _make_session_state(
        session_id: str = "test_session_001", response_count: int = 0, **overrides
    ) -> dict[str, Any]:
        """Create a session state dict.

        Args:
            session_id: Session identifier
            response_count: Number of responses in session
            **overrides: Fields to override

        Returns:
            Session state dictionary
        """
        state = {
            "session_id": session_id,
            "response_count": response_count,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "active_characters": [],
            "current_location": None,
            "metadata": {},
        }

        state.update(overrides)
        return state

    return _make_session_state


# ==============================================================================
# Configuration Fixtures
# ==============================================================================


@pytest.fixture
def minimal_config() -> dict[str, Any]:
    """Provide a minimal valid configuration.

    Returns:
        Minimal config dictionary
    """
    return {"version": "2.0.0", "system": {"log_level": "INFO"}, "modules": {}}


@pytest.fixture
def full_config() -> dict[str, Any]:
    """Provide a full configuration with all modules.

    Returns:
        Complete config dictionary
    """
    return {
        "version": "2.0.0",
        "system": {
            "log_level": "INFO",
            "auto_save": True,
            "backup_frequency": 10,
            "max_backups": 20,
            "performance_tracking": False,
        },
        "modules": {
            "session_manager": {
                "enabled": True,
                "config": {
                    "auto_checkpoint_frequency": 10,
                    "keep_archived": 20,
                    "compression": False,
                },
            },
            "agent_coordinator": {
                "enabled": True,
                "config": {"max_concurrent_agents": 3, "timeout": 60, "cache_enabled": True},
            },
            "claude_api_client": {
                "enabled": True,
                "config": {
                    "model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
            },
        },
    }


# ==============================================================================
# Test Markers Registration
# ==============================================================================


def pytest_configure(config):
    """Register custom pytest markers.

    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "smoke: mark test as a smoke test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically.

    Args:
        config: Pytest configuration
        items: List of collected test items
    """
    for item in items:
        # Auto-mark tests in integration/ as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-mark tests in unit/ as unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Auto-mark smoke tests
        if "smoke" in item.name or "test_smoke" in str(item.fspath):
            item.add_marker(pytest.mark.smoke)
