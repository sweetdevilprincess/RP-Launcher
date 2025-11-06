"""
Configuration Loader for RP System

Handles loading, validation, and access to system configuration.
Provides centralized configuration management for all modules.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from copy import deepcopy


class ConfigLoader:
    """Manages configuration loading and access for RP system.

    The config loader handles:
    - Loading configuration from JSON files
    - Providing default configurations
    - Validating configuration structure
    - Module-specific configuration access
    - Configuration updates and reloading

    Usage:
        config_loader = ConfigLoader(rp_dir)
        config = config_loader.load()

        # Access module config
        session_config = config_loader.get_module_config('session_manager')

        # Check if module enabled
        if config_loader.is_module_enabled('session_manager'):
            # Initialize module
    """

    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "system": {
            "log_level": "INFO",
            "auto_save": True,
            "backup_frequency": 10
        },
        "modules": {
            # Core modules (always enabled)
            "file_manager": {
                "enabled": True,
                "config": {}
            },

            # Session management
            "session_manager": {
                "enabled": True,
                "config": {
                    "auto_checkpoint_frequency": 10,
                    "keep_archived": 20,
                    "compression": False
                }
            },

            # File system write queue
            "fs_write_queue": {
                "enabled": True,
                "config": {
                    "flush_interval": 5,
                    "max_queue_size": 100
                }
            },

            # Background task queue
            "background_task_queue": {
                "enabled": True,
                "config": {
                    "max_workers": 4,
                    "shutdown_timeout": 30
                }
            },

            # Agent coordination
            "agent_coordinator": {
                "enabled": True,
                "config": {
                    "max_concurrent_agents": 3,
                    "timeout": 60,
                    "cache_enabled": True
                }
            },

            # Entity management
            "entity_manager": {
                "enabled": True,
                "config": {
                    "auto_generate_threshold": 3,
                    "track_mentions": True
                }
            },

            # Automation orchestrator
            "automation_orchestrator": {
                "enabled": True,
                "config": {
                    "auto_start": False
                }
            },

            # Update checker (optional)
            "update_checker": {
                "enabled": False,
                "config": {
                    "check_interval": 86400,
                    "auto_check": False
                }
            },

            # Proxy client
            "proxy_client": {
                "enabled": True,
                "config": {
                    "timeout": 30,
                    "retry_attempts": 3
                }
            },

            # LLM clients
            "claude_api_client": {
                "enabled": True,
                "config": {
                    "model": "claude-3-opus-20240229",
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            },

            "deepseek_client": {
                "enabled": True,
                "config": {
                    "model": "deepseek-chat",
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            }
        }
    }

    def __init__(self, rp_dir: Path):
        """Initialize config loader.

        Args:
            rp_dir: Path to RP directory
        """
        self.rp_dir = Path(rp_dir)
        self.config_file = self.rp_dir / "config.json"
        self.config: Dict[str, Any] = {}

        # Setup logger
        self.logger = self._setup_logger()

        self.logger.info(f"Config loader created for RP: {rp_dir}")

    def _setup_logger(self) -> logging.Logger:
        """Setup config loader logger.

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger("rp.config")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [CONFIG] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    # ==================== Configuration Loading ====================

    def load(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            create_if_missing: Create default config if file doesn't exist

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file missing and create_if_missing=False
            ValueError: If config file is invalid JSON
        """
        # Check if config file exists
        if not self.config_file.exists():
            if create_if_missing:
                self.logger.info(f"Config file not found, creating default: {self.config_file}")
                self.config = deepcopy(self.DEFAULT_CONFIG)
                self.save()
                return self.config
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_file}")

        # Load config file
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # Merge with defaults (to add any missing keys)
            self.config = self._merge_with_defaults(loaded_config)

            self.logger.info(f"Configuration loaded from {self.config_file}")
            return self.config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")

    def save(self) -> None:
        """Save current configuration to file.

        Raises:
            IOError: If unable to write config file
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write config with pretty formatting
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            raise IOError(f"Failed to save config: {e}")

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file.

        Returns:
            Updated configuration dictionary
        """
        self.logger.info("Reloading configuration...")
        return self.load(create_if_missing=False)

    # ==================== Configuration Access ====================

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Supports dot notation for nested keys.
        Example: get('system.log_level') returns config['system']['log_level']

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if not self.config:
            self.load()

        # Handle dot notation
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Supports dot notation for nested keys.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        if not self.config:
            self.load()

        # Handle dot notation
        keys = key.split('.')
        target = self.config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value
        self.logger.info(f"Configuration updated: {key} = {value}")

    # ==================== Module Configuration ====================

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module.

        Args:
            module_name: Name of module

        Returns:
            Module configuration dict (empty if not found)
        """
        if not self.config:
            self.load()

        modules_config = self.config.get('modules', {})
        module_config = modules_config.get(module_name, {})

        # Return the 'config' sub-dict, or empty dict if not present
        return module_config.get('config', {})

    def is_module_enabled(self, module_name: str) -> bool:
        """Check if module is enabled in configuration.

        Args:
            module_name: Name of module

        Returns:
            True if enabled (or not specified), False if explicitly disabled
        """
        if not self.config:
            self.load()

        modules_config = self.config.get('modules', {})
        module_config = modules_config.get(module_name, {})

        # Default to enabled if not specified
        return module_config.get('enabled', True)

    def set_module_enabled(self, module_name: str, enabled: bool) -> None:
        """Enable or disable a module.

        Args:
            module_name: Name of module
            enabled: True to enable, False to disable
        """
        if not self.config:
            self.load()

        # Ensure modules dict exists
        if 'modules' not in self.config:
            self.config['modules'] = {}

        # Ensure module dict exists
        if module_name not in self.config['modules']:
            self.config['modules'][module_name] = {}

        # Set enabled flag
        self.config['modules'][module_name]['enabled'] = enabled
        self.logger.info(f"Module '{module_name}' {'enabled' if enabled else 'disabled'}")

    def list_enabled_modules(self) -> List[str]:
        """List all enabled module names.

        Returns:
            List of enabled module names
        """
        if not self.config:
            self.load()

        modules_config = self.config.get('modules', {})
        return [
            name for name, config in modules_config.items()
            if config.get('enabled', True)
        ]

    def list_disabled_modules(self) -> List[str]:
        """List all disabled module names.

        Returns:
            List of disabled module names
        """
        if not self.config:
            self.load()

        modules_config = self.config.get('modules', {})
        return [
            name for name, config in modules_config.items()
            if not config.get('enabled', True)
        ]

    # ==================== Validation ====================

    def validate(self) -> bool:
        """Validate configuration structure.

        Returns:
            True if valid, False otherwise
        """
        if not self.config:
            self.load()

        # Check required top-level keys
        required_keys = ['version', 'system', 'modules']
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Missing required config key: {key}")
                return False

        # Validate modules section
        modules = self.config.get('modules', {})
        if not isinstance(modules, dict):
            self.logger.error("'modules' must be a dictionary")
            return False

        # Validate each module config
        for module_name, module_config in modules.items():
            if not isinstance(module_config, dict):
                self.logger.error(f"Module '{module_name}' config must be a dictionary")
                return False

            # Check for 'enabled' and 'config' keys
            if 'enabled' in module_config and not isinstance(module_config['enabled'], bool):
                self.logger.error(f"Module '{module_name}' 'enabled' must be boolean")
                return False

            if 'config' in module_config and not isinstance(module_config['config'], dict):
                self.logger.error(f"Module '{module_name}' 'config' must be a dictionary")
                return False

        self.logger.info("Configuration validation passed")
        return True

    # ==================== Utilities ====================

    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults.

        Ensures all default keys exist, but preserves user values.

        Args:
            loaded_config: Configuration loaded from file

        Returns:
            Merged configuration
        """
        def merge_dicts(default: Dict, loaded: Dict) -> Dict:
            """Recursively merge dictionaries."""
            result = deepcopy(default)

            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value

            return result

        merged = merge_dicts(self.DEFAULT_CONFIG, loaded_config)
        return merged

    def get_default_config(self) -> Dict[str, Any]:
        """Get a copy of the default configuration.

        Returns:
            Default configuration dictionary
        """
        return deepcopy(self.DEFAULT_CONFIG)

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults and save."""
        self.logger.warning("Resetting configuration to defaults")
        self.config = deepcopy(self.DEFAULT_CONFIG)
        self.save()

    def export(self, output_file: Path) -> None:
        """Export current configuration to a file.

        Args:
            output_file: Path to output file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration exported to {output_file}")

        except Exception as e:
            raise IOError(f"Failed to export config: {e}")

    def import_config(self, input_file: Path) -> None:
        """Import configuration from a file.

        Args:
            input_file: Path to input file

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If input file is invalid
        """
        if not input_file.exists():
            raise FileNotFoundError(f"Config file not found: {input_file}")

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            # Merge with defaults
            self.config = self._merge_with_defaults(imported_config)

            # Save to current config file
            self.save()

            self.logger.info(f"Configuration imported from {input_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to import config: {e}")

    def __repr__(self) -> str:
        """String representation of config loader.

        Returns:
            String representation
        """
        num_modules = len(self.config.get('modules', {})) if self.config else 0
        num_enabled = len(self.list_enabled_modules()) if self.config else 0

        return (
            f"<ConfigLoader(rp_dir='{self.rp_dir}', "
            f"modules={num_modules}, enabled={num_enabled})>"
        )
