"""
Configuration Loader for RP System

Handles loading, validation, and access to system configuration.
Provides centralized configuration management for all modules.

Configuration Precedence (highest to lowest):
1. Environment variables (e.g., RP_SYSTEM_LOG_LEVEL)
2. config.json file in RP directory
3. .env file in RP directory
4. Default values from defaults.py
"""

import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from .defaults import get_default_config


def _read_env_file(path: Path) -> dict[str, str]:
    """Read and parse an environment file.

    Args:
        path: Path to .env file

    Returns:
        Dict of environment variables, or empty dict if file doesn't exist or parsing fails
    """
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    except Exception:
        # Silently ignore errors, return empty dict
        pass

    return values


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

    # Environment variable prefixes for configuration
    ENV_PREFIX = "RP_"

    # Mapping of environment variables to config paths
    ENV_VAR_MAPPING = {
        # System config
        "RP_SYSTEM_LOG_LEVEL": "system.log_level",
        "RP_SYSTEM_AUTO_SAVE": "system.auto_save",
        "RP_SYSTEM_BACKUP_FREQUENCY": "system.backup_frequency",
        # LLM API keys (common convention)
        "ANTHROPIC_API_KEY": "modules.claude_api_client.config.api_key",
        "OPENAI_API_KEY": "modules.openai_client.config.api_key",
        "OPENROUTER_API_KEY": "modules.openrouter_client.config.api_key",
        # Claude config
        "RP_CLAUDE_MODEL": "modules.claude_api_client.config.model",
        "RP_CLAUDE_TEMPERATURE": "modules.claude_api_client.config.temperature",
        "RP_CLAUDE_MAX_TOKENS": "modules.claude_api_client.config.max_tokens",
        # OpenAI config
        "RP_OPENAI_MODEL": "modules.openai_client.config.model",
        "RP_OPENAI_TEMPERATURE": "modules.openai_client.config.temperature",
        # Proxy config
        "RP_PROXY_URL": "modules.proxy_client.config.proxy_url",
        "RP_PROXY_TIMEOUT": "modules.proxy_client.config.timeout",
    }

    def __init__(self, rp_dir: Path):
        """Initialize config loader.

        Args:
            rp_dir: Path to RP directory
        """
        self.rp_dir = Path(rp_dir)
        self.config_file = self.rp_dir / "config" / "config.json"
        self.env_file = self.rp_dir / ".env"
        self.config: dict[str, Any] = {}
        self._validation_warnings: list[str] = []

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
                "[%(asctime)s] [CONFIG] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    # ==================== Configuration Loading ====================

    def load(self, create_if_missing: bool = True) -> dict[str, Any]:
        """Load configuration from all sources with precedence.

        Configuration layers (lowest to highest priority):
        1. defaults.py (base)
        2. .env file (if exists)
        3. config.json (if exists)
        4. environment variables (highest)

        Args:
            create_if_missing: Create default config.json if missing

        Returns:
            Merged configuration dictionary

        Raises:
            FileNotFoundError: If config file missing and create_if_missing=False
            ValueError: If configuration is invalid
        """
        self._validation_warnings = []

        # Layer 1: Start with defaults
        self.config = get_default_config()
        self.logger.info("Loaded base configuration from defaults.py")

        # Layer 2: Overlay .env file
        if self.env_file.exists():
            env_dict = _read_env_file(self.env_file)
            if env_dict:
                self._apply_env_dict(env_dict)
                self.logger.info(f"Applied {len(env_dict)} settings from .env file")

        # Layer 3: Overlay config.json
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    loaded_config = json.load(f)

                self.config = self._merge_dicts(self.config, loaded_config)
                self.logger.info(f"Merged configuration from {self.config_file}")

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file: {e}")
            except Exception as e:
                raise ValueError(f"Failed to load config.json: {e}")
        elif create_if_missing:
            # Create default config.json for user customization
            self.logger.info(f"Config file not found, creating default: {self.config_file}")
            self.save()
        else:
            raise FileNotFoundError(f"Config file not found: {self.config_file}")

        # Layer 4: Overlay environment variables (highest priority)
        env_overrides = self._load_env_overrides()
        if env_overrides:
            for path, value in env_overrides.items():
                self._set_by_path(self.config, path, value)
            self.logger.info(f"Applied {len(env_overrides)} environment variable overrides")

        # Validate the final configuration
        self.validate()

        # Report any warnings
        if self._validation_warnings:
            for warning in self._validation_warnings:
                self.logger.warning(warning)

        return self.config

    def save(self) -> None:
        """Save current configuration to file.

        Raises:
            IOError: If unable to write config file
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Write config with pretty formatting
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration saved to {self.config_file}")

        except Exception as e:
            raise OSError(f"Failed to save config: {e}")

    def reload(self) -> dict[str, Any]:
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
        keys = key.split(".")
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
        keys = key.split(".")
        target = self.config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value

        # Redact sensitive values in logs (API keys, tokens, passwords, secrets)
        sensitive_keywords = ["key", "token", "password", "secret", "api_key", "auth"]
        is_sensitive = any(keyword in key.lower() for keyword in sensitive_keywords)
        log_value = "[REDACTED]" if is_sensitive else value
        self.logger.info(f"Configuration updated: {key} = {log_value}")

    # ==================== Module Configuration ====================

    def get_module_config(self, module_name: str) -> dict[str, Any]:
        """Get configuration for a specific module.

        Args:
            module_name: Name of module

        Returns:
            Module configuration dict (empty if not found)
        """
        if not self.config:
            self.load()

        modules_config = self.config.get("modules", {})
        module_config = modules_config.get(module_name, {})

        # Return the 'config' sub-dict, or empty dict if not present
        return module_config.get("config", {})

    def is_module_enabled(self, module_name: str) -> bool:
        """Check if module is enabled in configuration.

        Args:
            module_name: Name of module

        Returns:
            True if enabled (or not specified), False if explicitly disabled
        """
        if not self.config:
            self.load()

        modules_config = self.config.get("modules", {})
        module_config = modules_config.get(module_name, {})

        # Default to enabled if not specified
        return module_config.get("enabled", True)

    def set_module_enabled(self, module_name: str, enabled: bool) -> None:
        """Enable or disable a module.

        Args:
            module_name: Name of module
            enabled: True to enable, False to disable
        """
        if not self.config:
            self.load()

        # Ensure modules dict exists
        if "modules" not in self.config:
            self.config["modules"] = {}

        # Ensure module dict exists
        if module_name not in self.config["modules"]:
            self.config["modules"][module_name] = {}

        # Set enabled flag
        self.config["modules"][module_name]["enabled"] = enabled
        self.logger.info(f"Module '{module_name}' {'enabled' if enabled else 'disabled'}")

    def list_enabled_modules(self) -> list[str]:
        """List all enabled module names.

        Returns:
            List of enabled module names
        """
        if not self.config:
            self.load()

        modules_config = self.config.get("modules", {})
        return [name for name, config in modules_config.items() if config.get("enabled", True)]

    def list_disabled_modules(self) -> list[str]:
        """List all disabled module names.

        Returns:
            List of disabled module names
        """
        if not self.config:
            self.load()

        modules_config = self.config.get("modules", {})
        return [name for name, config in modules_config.items() if not config.get("enabled", True)]

    # ==================== Validation ====================

    def validate(self) -> bool:
        """Validate configuration structure, types, and values.

        Performs comprehensive validation:
        - Structure validation (required keys present)
        - Type validation (against TypedDict schemas)
        - Field-level validation (log levels, temperature ranges, etc.)
        - Unknown field detection (warnings)

        Returns:
            True if valid, False otherwise
        """
        if not self.config:
            self.load()

        valid = True

        # 1. Check required top-level keys
        required_keys = ["version", "system", "modules"]
        for key in required_keys:
            if key not in self.config:
                self.logger.error(f"Missing required config key: {key}")
                return False

        # 2. Validate system config
        if not self._validate_system_config():
            valid = False

        # 2.5. Validate LLM routing config (if present, not required for backwards compat)
        if "llm" in self.config:
            if not self._validate_llm_routing_config():
                valid = False

        # 3. Validate modules section
        modules = self.config.get("modules", {})
        if not isinstance(modules, dict):
            self.logger.error("'modules' must be a dictionary")
            return False

        # 4. Validate each module config
        for module_name, module_config in modules.items():
            if not isinstance(module_config, dict):
                self.logger.error(f"Module '{module_name}' config must be a dictionary")
                valid = False
                continue

            # Check module structure
            if "enabled" in module_config and not isinstance(module_config["enabled"], bool):
                self.logger.error(f"Module '{module_name}' 'enabled' must be boolean")
                valid = False

            if "config" in module_config:
                if not isinstance(module_config["config"], dict):
                    self.logger.error(f"Module '{module_name}' 'config' must be a dictionary")
                    valid = False
                # Validate module-specific config
                elif not self._validate_module_config(module_name, module_config["config"]):
                    valid = False

        # 5. Detect unknown fields (warnings only, doesn't affect validity)
        self._detect_unknown_fields()

        if valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error("Configuration validation failed")

        return valid

    def _validate_system_config(self) -> bool:
        """Validate system-level configuration.

        Returns:
            True if valid, False otherwise
        """
        system = self.config.get("system", {})
        valid = True

        # Validate log_level
        if "log_level" in system:
            log_level = system["log_level"]
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if log_level not in valid_levels:
                self.logger.error(
                    f"Invalid log_level '{log_level}'. Must be one of: {', '.join(valid_levels)}"
                )
                valid = False

        # Validate auto_save
        if "auto_save" in system and not isinstance(system["auto_save"], bool):
            self.logger.error("system.auto_save must be a boolean")
            valid = False

        # Validate backup_frequency
        if "backup_frequency" in system:
            freq = system["backup_frequency"]
            if not isinstance(freq, int) or freq < 0:
                self.logger.error("system.backup_frequency must be a non-negative integer")
                valid = False

        # Validate max_backups
        if "max_backups" in system:
            max_b = system["max_backups"]
            if not isinstance(max_b, int) or max_b < 0:
                self.logger.error("system.max_backups must be a non-negative integer")
                valid = False

        # Validate performance_tracking
        if "performance_tracking" in system and not isinstance(
            system["performance_tracking"], bool
        ):
            self.logger.error("system.performance_tracking must be a boolean")
            valid = False

        return valid

    def _validate_llm_routing_config(self) -> bool:
        """Validate LLM routing configuration.

        Returns:
            True if valid, False otherwise
        """
        llm_config = self.config.get("llm", {})
        valid = True

        # Known LLM provider names
        known_providers = [
            "claude_api_client",
            "claude_sdk_client",
            "openai_client",
            "openrouter_client",
        ]

        # Validate primary_provider
        if "primary_provider" in llm_config:
            primary = llm_config["primary_provider"]
            if not isinstance(primary, str):
                self.logger.error("llm.primary_provider must be a string")
                valid = False
            elif primary and primary not in known_providers:
                self.logger.warning(
                    f"llm.primary_provider '{primary}' is not a known provider. "
                    f"Known providers: {', '.join(known_providers)}"
                )

        # Validate secondary_provider
        if "secondary_provider" in llm_config:
            secondary = llm_config["secondary_provider"]
            if not isinstance(secondary, str):
                self.logger.error("llm.secondary_provider must be a string")
                valid = False
            elif secondary and secondary not in known_providers:
                self.logger.warning(
                    f"llm.secondary_provider '{secondary}' is not a known provider. "
                    f"Known providers: {', '.join(known_providers)}"
                )

        # Validate use_secondary_for_automation
        if "use_secondary_for_automation" in llm_config:
            use_secondary = llm_config["use_secondary_for_automation"]
            if not isinstance(use_secondary, bool):
                self.logger.error("llm.use_secondary_for_automation must be a boolean")
                valid = False

        return valid

    def _validate_module_config(self, module_name: str, config: dict[str, Any]) -> bool:
        """Validate module-specific configuration.

        Args:
            module_name: Name of the module
            config: Module configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # LLM client validations
        if module_name in [
            "claude_api_client",
            "openai_client",
            "openrouter_client",
        ]:
            valid = self._validate_llm_config(module_name, config) and valid

        # Agent coordinator validation
        elif module_name == "agent_coordinator":
            valid = self._validate_agent_coordinator_config(config) and valid

        # Proxy client validation
        elif module_name == "proxy_client":
            valid = self._validate_proxy_config(config) and valid

        # Session manager validation
        elif module_name == "session_manager":
            valid = self._validate_session_manager_config(config) and valid

        return valid

    def _validate_llm_config(self, module_name: str, config: dict[str, Any]) -> bool:
        """Validate LLM client configuration.

        Args:
            module_name: Name of LLM module
            config: LLM configuration

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # Validate temperature
        if "temperature" in config:
            temp = config["temperature"]
            # Allow empty string or None (means "use default")
            if temp not in ("", None):
                if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 1.0):
                    self.logger.error(
                        f"{module_name}.temperature must be a number between 0.0 and 1.0, got: {temp}"
                    )
                    valid = False

        # Validate max_tokens
        if "max_tokens" in config:
            max_tok = config["max_tokens"]
            # Allow empty string or None (means "use default")
            if max_tok not in ("", None):
                if not isinstance(max_tok, int) or max_tok <= 0:
                    self.logger.error(
                        f"{module_name}.max_tokens must be a positive integer, got: {max_tok}"
                    )
                    valid = False

        # Validate model (warn if unknown)
        if "model" in config:
            model = config["model"]
            if not isinstance(model, str):
                self.logger.error(f"{module_name}.model must be a string, got: {type(model)}")
                valid = False

        return valid

    def _validate_agent_coordinator_config(self, config: dict[str, Any]) -> bool:
        """Validate agent coordinator configuration.

        Args:
            config: Agent coordinator configuration

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # Validate max_concurrent_agents
        if "max_concurrent_agents" in config:
            max_agents = config["max_concurrent_agents"]
            if not isinstance(max_agents, int) or max_agents <= 0:
                self.logger.error(
                    f"agent_coordinator.max_concurrent_agents must be a positive integer, got: {max_agents}"
                )
                valid = False

        # Validate timeout
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, int) or timeout <= 0:
                self.logger.error(
                    f"agent_coordinator.timeout must be a positive integer, got: {timeout}"
                )
                valid = False

        # Validate worker counts
        for field in ["immediate_workers", "background_workers"]:
            if field in config:
                workers = config[field]
                if not isinstance(workers, int) or workers <= 0:
                    self.logger.error(
                        f"agent_coordinator.{field} must be a positive integer, got: {workers}"
                    )
                    valid = False

        # Validate max_retries
        if "max_retries" in config:
            retries = config["max_retries"]
            if not isinstance(retries, int) or retries < 0:
                self.logger.error(
                    f"agent_coordinator.max_retries must be a non-negative integer, got: {retries}"
                )
                valid = False

        return valid

    def _validate_proxy_config(self, config: dict[str, Any]) -> bool:
        """Validate proxy configuration.

        Args:
            config: Proxy configuration

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # Validate timeout
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, int) or timeout <= 0:
                self.logger.error(
                    f"proxy_client.timeout must be a positive integer, got: {timeout}"
                )
                valid = False

        # Validate retry_attempts
        if "retry_attempts" in config:
            retries = config["retry_attempts"]
            if not isinstance(retries, int) or retries < 0:
                self.logger.error(
                    f"proxy_client.retry_attempts must be a non-negative integer, got: {retries}"
                )
                valid = False

        return valid

    def _validate_session_manager_config(self, config: dict[str, Any]) -> bool:
        """Validate session manager configuration.

        Args:
            config: Session manager configuration

        Returns:
            True if valid, False otherwise
        """
        valid = True

        # Validate auto_checkpoint_frequency
        if "auto_checkpoint_frequency" in config:
            freq = config["auto_checkpoint_frequency"]
            if not isinstance(freq, int) or freq < 0:
                self.logger.error(
                    f"session_manager.auto_checkpoint_frequency must be a non-negative integer, got: {freq}"
                )
                valid = False

        # Validate keep_archived
        if "keep_archived" in config:
            keep = config["keep_archived"]
            if not isinstance(keep, int) or keep < 0:
                self.logger.error(
                    f"session_manager.keep_archived must be a non-negative integer, got: {keep}"
                )
                valid = False

        # Validate compression
        if "compression" in config and not isinstance(config["compression"], bool):
            self.logger.error("session_manager.compression must be a boolean")
            valid = False

        return valid

    def _detect_unknown_fields(self) -> None:
        """Detect unknown fields in configuration and add warnings.

        Compares current config against defaults to find extra fields.
        Warnings are added to self._validation_warnings.
        """
        defaults = get_default_config()

        # Check system section for unknown fields
        system = self.config.get("system", {})
        default_system = defaults.get("system", {})
        for key in system:
            if key not in default_system:
                self._validation_warnings.append(
                    f"Unknown field in system config: '{key}' (will be ignored)"
                )

        # Check modules for unknown fields
        modules = self.config.get("modules", {})
        default_modules = defaults.get("modules", {})

        for module_name, module_config in modules.items():
            # Check if module exists in defaults
            if module_name not in default_modules:
                self._validation_warnings.append(
                    f"Unknown module '{module_name}' (will be ignored)"
                )
                continue

            # Check module config fields
            if "config" in module_config and isinstance(module_config["config"], dict):
                user_config = module_config["config"]
                default_config = default_modules[module_name].get("config", {})

                for key in user_config:
                    if key not in default_config:
                        # Provide suggestion if there's a similar field
                        suggestion = self._suggest_similar_field(key, default_config.keys())
                        if suggestion:
                            self._validation_warnings.append(
                                f"Unknown field '{module_name}.config.{key}'. Did you mean '{suggestion}'?"
                            )
                        else:
                            self._validation_warnings.append(
                                f"Unknown field '{module_name}.config.{key}' (will be ignored)"
                            )

    def _suggest_similar_field(self, field: str, valid_fields) -> str | None:
        """Suggest a similar valid field name if one exists.

        Uses simple string similarity logic.

        Args:
            field: The unknown field name
            valid_fields: Iterable of valid field names

        Returns:
            Suggested field name or None
        """
        field_lower = field.lower()
        valid_fields_list = list(valid_fields)

        # Look for exact case-insensitive match
        for valid_field in valid_fields_list:
            if valid_field.lower() == field_lower:
                return valid_field

        # Look for prefix match (at least 3 chars)
        if len(field) >= 3:
            field_prefix = field_lower[:3]
            for valid_field in valid_fields_list:
                if valid_field.lower().startswith(field_prefix):
                    return valid_field

        return None

    # ==================== Utilities ====================

    def _merge_dicts(self, base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries.

        Recursively merges overlay into base, preserving nested structures.

        Args:
            base: Base dictionary
            overlay: Dictionary to merge on top

        Returns:
            Merged dictionary
        """
        result = deepcopy(base)

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_env_dict(self, env_dict: dict[str, str]) -> None:
        """Apply .env file variables to configuration.

        Maps environment variable names to config paths and applies them.

        Args:
            env_dict: Dictionary of environment variables from .env file
        """
        for env_key, env_value in env_dict.items():
            if env_key in self.ENV_VAR_MAPPING:
                path = self.ENV_VAR_MAPPING[env_key]
                typed_value = self._parse_env_value(env_value)
                self._set_by_path(self.config, path, typed_value)

    def _load_env_overrides(self) -> dict[str, Any]:
        """Load configuration overrides from environment variables.

        Returns:
            Dictionary mapping config paths to values
        """
        overrides: dict[str, Any] = {}

        for env_key, config_path in self.ENV_VAR_MAPPING.items():
            if env_key in os.environ:
                raw_value = os.environ[env_key]
                typed_value = self._parse_env_value(raw_value)
                overrides[config_path] = typed_value

        return overrides

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable string to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Boolean values
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        if value.lower() in ("false", "no", "0", "off"):
            return False

        # Numeric values
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String value
        return value

    def _set_by_path(self, config: dict[str, Any], path: str, value: Any) -> None:
        """Set a configuration value using dot-notation path.

        Args:
            config: Configuration dictionary to modify
            path: Dot-separated path (e.g., "system.log_level")
            value: Value to set
        """
        keys = path.split(".")
        target = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Set the value
        target[keys[-1]] = value

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults and save."""
        self.logger.warning("Resetting configuration to defaults")
        self.config = get_default_config()
        self.save()

    def export(self, output_file: Path) -> None:
        """Export current configuration to a file.

        Args:
            output_file: Path to output file
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration exported to {output_file}")

        except Exception as e:
            raise OSError(f"Failed to export config: {e}")

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
            with open(input_file, encoding="utf-8") as f:
                imported_config = json.load(f)

            # Merge with defaults
            defaults = get_default_config()
            self.config = self._merge_dicts(defaults, imported_config)

            # Save to current config file
            self.save()

            self.logger.info(f"Configuration imported from {input_file}")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to import config: {e}")

    def validate_rp_directory(self) -> list[str]:
        """Validate RP directory structure and return actionable error messages.

        Checks for common misconfiguration issues and provides helpful suggestions.

        Returns:
            List of error/warning messages (empty if all OK)
        """
        issues: list[str] = []

        # Check if RP directory exists
        if not self.rp_dir.exists():
            issues.append(
                f"ERROR: RP directory does not exist: {self.rp_dir}\n"
                f"  -> Create the directory or provide a valid path"
            )
            return issues  # Can't continue validation

        if not self.rp_dir.is_dir():
            issues.append(
                f"ERROR: RP path is not a directory: {self.rp_dir}\n"
                f"  -> Provide a path to a directory, not a file"
            )
            return issues

        # Check for config.json
        if not self.config_file.exists():
            issues.append(
                f"WARNING: config.json not found at: {self.config_file}\n"
                f"  -> Run ConfigLoader.load(create_if_missing=True) to generate default config"
            )

        # Check common subdirectories that might be expected
        expected_dirs = {
            "state": "Session state and game progress files",
            "entities": "Character and world entity files",
            "templates": "Prompt templates and narrative guides",
        }

        for dirname, description in expected_dirs.items():
            dirpath = self.rp_dir / dirname
            if not dirpath.exists():
                issues.append(
                    f"INFO: Optional directory missing: {dirpath}\n" f"  -> {description}"
                )

        # Check for common entity fixture locations
        fixture_candidates = [
            self.rp_dir / "entities" / "characters",
            self.rp_dir / "entities" / "locations",
            self.rp_dir / "fixtures" / "characters",
            self.rp_dir / "fixtures" / "locations",
        ]

        entity_dirs_found = any(d.exists() for d in fixture_candidates)
        if not entity_dirs_found:
            issues.append(
                "INFO: No entity directories found\n"
                "  -> Create entities/characters/ and entities/locations/ for entity fixtures"
            )

        # Validate config.json if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(
                    f"ERROR: config.json has invalid JSON syntax:\n"
                    f"  -> {e}\n"
                    f"  -> Fix JSON syntax or delete file to regenerate"
                )
            except Exception as e:
                issues.append(
                    f"ERROR: Cannot read config.json: {e}\n" f"  -> Check file permissions"
                )

        # Check .env file if it exists
        if self.env_file.exists():
            env_dict = _read_env_file(self.env_file)
            if not env_dict:
                issues.append(
                    f"WARNING: .env file exists but contains no valid entries: {self.env_file}\n"
                    f"  -> Check .env file format (KEY=value)"
                )

        return issues

    def __repr__(self) -> str:
        """String representation of config loader.

        Returns:
            String representation
        """
        num_modules = len(self.config.get("modules", {})) if self.config else 0
        num_enabled = len(self.list_enabled_modules()) if self.config else 0

        return (
            f"<ConfigLoader(rp_dir='{self.rp_dir}', "
            f"modules={num_modules}, enabled={num_enabled})>"
        )
