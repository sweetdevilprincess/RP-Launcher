"""
Common File Utilities

Shared file reading/writing utilities to eliminate duplication across agents and modules.
Consolidates _read_file_safe, _load_file_safe, and directory walk patterns.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging


logger = logging.getLogger(__name__)


def read_file_safe(
    file_path: Union[str, Path],
    default: str = "",
    encoding: str = 'utf-8',
    log_errors: bool = True
) -> str:
    """Safely read a file with error handling.

    Unified implementation to replace BaseAgent._read_file_safe and FileLoader._load_file_safe.

    Args:
        file_path: Path to file
        default: Default value if file doesn't exist or can't be read
        encoding: File encoding
        log_errors: Whether to log errors

    Returns:
        File contents or default value
    """
    try:
        path = Path(file_path)
        if not path.exists():
            if log_errors:
                logger.debug(f"File not found: {file_path}")
            return default

        return path.read_text(encoding=encoding)

    except Exception as e:
        if log_errors:
            logger.error(f"Error reading file {file_path}: {e}")
        return default


def load_directory_map(
    directory: Union[str, Path],
    pattern: str = "*.md",
    name_key: Optional[str] = None,
    recursive: bool = False,
    encoding: str = 'utf-8'
) -> Dict[str, str]:
    """Load directory contents into a name->content map.

    Replaces repeated directory walk patterns for entity cards, memory banks, plot threads.

    Args:
        directory: Directory to scan
        pattern: Glob pattern for files
        name_key: If provided, use this as the key (e.g., "entity_name"). Otherwise use filename stem.
        recursive: Search recursively
        encoding: File encoding

    Returns:
        Dictionary mapping names to file contents

    Example:
        # Load all entity cards
        entities = load_directory_map(rp_dir / "entities", "*.md")
        # {'Character_A': 'content...', 'Character_B': 'content...'}
    """
    result = {}
    dir_path = Path(directory)

    if not dir_path.exists() or not dir_path.is_dir():
        logger.debug(f"Directory not found or not a directory: {directory}")
        return result

    try:
        # Get matching files
        if recursive:
            files = dir_path.rglob(pattern)
        else:
            files = dir_path.glob(pattern)

        # Load each file
        for file_path in files:
            if not file_path.is_file():
                continue

            # Determine key (filename stem by default)
            key = file_path.stem

            # Read content
            content = read_file_safe(file_path, default="", encoding=encoding, log_errors=False)

            if content:  # Only add non-empty files
                result[key] = content

    except Exception as e:
        logger.error(f"Error loading directory map from {directory}: {e}")

    return result


def ensure_directory(directory: Union[str, Path]) -> Path:
    """Ensure directory exists, create if needed.

    Args:
        directory: Path to directory

    Returns:
        Path object

    Raises:
        OSError: If directory can't be created
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def write_file_safe(
    file_path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True,
    log_errors: bool = True
) -> bool:
    """Safely write a file with error handling.

    Args:
        file_path: Path to write to
        content: Content to write
        encoding: File encoding
        create_dirs: Create parent directories if needed
        log_errors: Whether to log errors

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding=encoding)
        return True

    except Exception as e:
        if log_errors:
            logger.error(f"Error writing file {file_path}: {e}")
        return False


def file_exists(file_path: Union[str, Path]) -> bool:
    """Check if file exists and is a file (not directory).

    Args:
        file_path: Path to check

    Returns:
        True if file exists and is a file
    """
    path = Path(file_path)
    return path.exists() and path.is_file()


def get_file_age_seconds(file_path: Union[str, Path]) -> Optional[float]:
    """Get age of file in seconds since last modification.

    Args:
        file_path: Path to file

    Returns:
        Age in seconds, or None if file doesn't exist
    """
    try:
        import time
        path = Path(file_path)
        if not path.exists():
            return None

        mtime = path.stat().st_mtime
        return time.time() - mtime

    except Exception as e:
        logger.error(f"Error getting file age for {file_path}: {e}")
        return None


def list_files_by_pattern(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
    sort_by_mtime: bool = False
) -> List[Path]:
    """List files matching pattern in directory.

    Args:
        directory: Directory to search
        pattern: Glob pattern
        recursive: Search recursively
        sort_by_mtime: Sort by modification time (newest first)

    Returns:
        List of matching file paths
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return []

    try:
        # Get matching files
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # Filter to files only
        files = [f for f in files if f.is_file()]

        # Sort if requested
        if sort_by_mtime:
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        else:
            files.sort()

        return files

    except Exception as e:
        logger.error(f"Error listing files in {directory}: {e}")
        return []
