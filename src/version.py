"""Version tracking for the RP Launcher.

This module tracks the current version using semantic versioning (git tags).
Falls back to commit SHAs if no tags are available.
"""

import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple

# Current version - updated when tags are created
__version__ = "1.0.0"
__fallback_commit__ = "0fa756999af4bb61160af4d0454c80ded7b6192f"


def get_git_tag() -> Optional[str]:
    """Get the current git tag (semantic version).

    Returns:
        Semantic version (e.g., "v1.0.0") or None if no tag found
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Ensure it starts with 'v' and is a semantic version
            if tag and (tag.startswith('v') or re.match(r'^\d+\.\d+\.\d+', tag)):
                return tag
    except Exception:
        pass
    return None


def get_git_commit() -> Optional[str]:
    """Get the current git commit SHA.

    Returns:
        Full commit SHA or None if unable to determine
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_current_version() -> str:
    """Get the current version (semantic version or commit SHA).

    Tries to get version from git tag first, then falls back to commit SHA,
    then to hardcoded values.

    Returns:
        Version string (e.g., "v1.0.0" or "0fa7569")
    """
    # Try to get semantic version from git tag
    tag = get_git_tag()
    if tag:
        return tag

    # Fall back to commit SHA
    commit = get_git_commit()
    if commit:
        return commit[:7]  # Short SHA

    # Fall back to hardcoded commit
    return __fallback_commit__[:7]


def get_current_version_full() -> str:
    """Get the full current version (semantic version or full commit SHA).

    Returns:
        Full version string
    """
    # Try to get semantic version from git tag
    tag = get_git_tag()
    if tag:
        return tag

    # Fall back to full commit SHA
    commit = get_git_commit()
    if commit:
        return commit

    # Fall back to hardcoded commit
    return __fallback_commit__


def is_semantic_version(version: str) -> bool:
    """Check if a version string is a semantic version.

    Args:
        version: Version string to check

    Returns:
        True if semantic version (e.g., "v1.0.0"), False otherwise
    """
    # Remove 'v' prefix if present
    v = version.lstrip('v')
    return bool(re.match(r'^\d+\.\d+\.\d+', v))


def get_version_info() -> dict:
    """Get detailed version information.

    Returns:
        Dict with version details
    """
    current = get_current_version()
    full = get_current_version_full()
    is_semver = is_semantic_version(current)
    tag = get_git_tag()
    commit = get_git_commit()

    return {
        "version": current,
        "full": full,
        "is_semantic": is_semver,
        "tag": tag,
        "commit": commit[:7] if commit else None,
        "commit_full": commit
    }


if __name__ == "__main__":
    info = get_version_info()
    print(f"RP Launcher Version")
    print(f"  Version:  {info['version']}")
    if info['is_semantic']:
        print(f"  Type:     Semantic Version (release)")
        if info['commit']:
            print(f"  Commit:   {info['commit']}")
    else:
        print(f"  Type:     Development (commit SHA)")
        print(f"  Full SHA: {info['full']}")
    print(f"  Tag:      {info['tag'] if info['tag'] else 'None (no release tag)'}")
