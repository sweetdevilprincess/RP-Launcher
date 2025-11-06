"""
Common Utilities Module

Shared utilities to eliminate code duplication across agents and modules.

Provides:
- file_utils: Safe file operations and directory walking
- json_utils: JSON parsing with fallbacks and validation
- agent_result: Standardized agent result format
- agent_logger: Consistent logging with emoji and timing
- time_utils: Timestamp and timing utilities
"""

# File utilities
from .file_utils import (
    read_file_safe,
    load_directory_map,
    ensure_directory,
    write_file_safe,
    file_exists,
    get_file_age_seconds,
    list_files_by_pattern
)

# JSON utilities
from .json_utils import (
    parse_json_safe,
    extract_json_from_text,
    build_error_payload,
    merge_json_objects,
    validate_json_schema,
    sanitize_json_string
)

# Agent result
from .agent_result import (
    AgentResult,
    CachedAgentResult,
    combine_agent_results
)

# Agent logger
from .agent_logger import (
    AgentLogger,
    AgentCoordinatorLogger,
    log_to_file
)

# Time utilities
from .time_utils import (
    now_iso,
    now_formatted,
    now_timestamp,
    now_timestamp_ms,
    elapsed_ms,
    parse_iso,
    format_duration,
    time_ago,
    is_expired,
    Timer
)

__all__ = [
    # File utilities
    'read_file_safe',
    'load_directory_map',
    'ensure_directory',
    'write_file_safe',
    'file_exists',
    'get_file_age_seconds',
    'list_files_by_pattern',

    # JSON utilities
    'parse_json_safe',
    'extract_json_from_text',
    'build_error_payload',
    'merge_json_objects',
    'validate_json_schema',
    'sanitize_json_string',

    # Agent result
    'AgentResult',
    'CachedAgentResult',
    'combine_agent_results',

    # Agent logger
    'AgentLogger',
    'AgentCoordinatorLogger',
    'log_to_file',

    # Time utilities
    'now_iso',
    'now_formatted',
    'now_timestamp',
    'now_timestamp_ms',
    'elapsed_ms',
    'parse_iso',
    'format_duration',
    'time_ago',
    'is_expired',
    'Timer',
]
