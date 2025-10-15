"""GitHub update checker for RP Launcher.

Checks if a newer version is available on GitHub.
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional, Tuple
import requests

# Add project root to path for imports when running standalone
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.version import get_current_version, get_current_version_full, is_semantic_version


# GitHub repository info
GITHUB_OWNER = "sweetdevilprincess"
GITHUB_REPO = "RP-Launcher"
GITHUB_API_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits"
GITHUB_API_TAGS_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/tags"

# Cache settings
CACHE_FILE = Path(__file__).parent.parent / ".update_check_cache"
CACHE_DURATION = 86400  # 24 hours in seconds


class UpdateCheckResult:
    """Result of an update check."""

    def __init__(self, available: bool, current: str, latest: str, error: Optional[str] = None):
        self.available = available
        self.current = current
        self.latest = latest
        self.error = error

    def __repr__(self):
        if self.error:
            return f"UpdateCheckResult(error={self.error})"
        return f"UpdateCheckResult(available={self.available}, current={self.current[:7]}, latest={self.latest[:7]})"


def _load_cache() -> Optional[dict]:
    """Load cached update check result.

    Returns:
        Cached data or None if cache is invalid/expired
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        # Check if cache is still valid
        timestamp = cache.get("timestamp", 0)
        cache_duration = cache.get("cache_duration", CACHE_DURATION)
        if time.time() - timestamp < cache_duration:
            return cache
    except Exception:
        pass

    return None


def _save_cache(result: UpdateCheckResult, cache_duration: int = CACHE_DURATION) -> None:
    """Save update check result to cache.

    Args:
        result: Update check result to cache
        cache_duration: How long to cache the result (seconds)
    """
    try:
        cache_data = {
            "timestamp": time.time(),
            "cache_duration": cache_duration,
            "available": result.available,
            "current": result.current,
            "latest": result.latest,
            "error": result.error
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except Exception:
        pass  # Failing to cache is not critical


def _check_github_latest_tag(timeout: int = 3) -> Optional[str]:
    """Check GitHub API for latest release tag.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Latest tag name (e.g., "v1.0.0") or None if request fails
    """
    try:
        response = requests.get(
            GITHUB_API_TAGS_URL,
            params={"per_page": 1},
            timeout=timeout,
            headers={"Accept": "application/vnd.github.v3+json"}
        )

        if response.status_code == 200:
            tags = response.json()
            if tags and len(tags) > 0:
                return tags[0]["name"]
        elif response.status_code == 403:
            # Rate limit exceeded
            return None
    except Exception:
        pass

    return None


def _check_github_latest_commit(timeout: int = 3) -> Optional[str]:
    """Check GitHub API for latest commit SHA.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Latest commit SHA or None if request fails
    """
    try:
        # Use per_page=1 to only get the most recent commit
        response = requests.get(
            GITHUB_API_COMMITS_URL,
            params={"per_page": 1},
            timeout=timeout,
            headers={"Accept": "application/vnd.github.v3+json"}
        )

        if response.status_code == 200:
            commits = response.json()
            if commits and len(commits) > 0:
                return commits[0]["sha"]
        elif response.status_code == 403:
            # Rate limit exceeded
            return None
    except Exception:
        pass

    return None


def check_for_updates(
    use_cache: bool = True,
    cache_duration: int = CACHE_DURATION,
    timeout: int = 3
) -> UpdateCheckResult:
    """Check if an update is available on GitHub.

    Checks for semantic version tags first, then falls back to commit comparison.

    Args:
        use_cache: Whether to use cached result if available
        cache_duration: How long to cache the result (seconds)
        timeout: Request timeout in seconds

    Returns:
        UpdateCheckResult with information about available updates
    """
    # Try to load from cache first
    if use_cache:
        cached = _load_cache()
        if cached:
            return UpdateCheckResult(
                available=cached["available"],
                current=cached["current"],
                latest=cached["latest"],
                error=cached.get("error")
            )

    # Get current version
    current_version = get_current_version()
    current_full = get_current_version_full()
    if not current_version:
        result = UpdateCheckResult(
            available=False,
            current="unknown",
            latest="unknown",
            error="Unable to determine current version"
        )
        _save_cache(result, cache_duration)
        return result

    # Check if we're on a semantic version (release) or commit
    current_is_semantic = is_semantic_version(current_version)

    # Check GitHub for latest version
    # Try tags first (semantic versions)
    latest_version = _check_github_latest_tag(timeout)

    if latest_version and is_semantic_version(latest_version):
        # We have a semantic version from GitHub
        # If we're also on a semantic version, compare them
        if current_is_semantic:
            update_available = current_version != latest_version
        else:
            # We're on a commit, but there's a tagged release available
            # Consider this an update available
            update_available = True
    else:
        # No semantic version available, fall back to commit comparison
        latest_commit = _check_github_latest_commit(timeout)
        if not latest_commit:
            result = UpdateCheckResult(
                available=False,
                current=current_version,
                latest="unknown",
                error="Unable to fetch latest version from GitHub"
            )
            _save_cache(result, cache_duration)
            return result

        # Compare commits
        latest_version = latest_commit[:7]  # Short SHA for display
        if current_is_semantic:
            # We're on a release but GitHub has newer commits
            # Can't reliably determine if update is needed
            update_available = False
        else:
            # Both are commits, compare SHAs
            update_available = current_full != latest_commit

    result = UpdateCheckResult(
        available=update_available,
        current=current_version,
        latest=latest_version
    )
    _save_cache(result, cache_duration)
    return result


def clear_cache() -> bool:
    """Clear the update check cache.

    Returns:
        True if cache was cleared, False if it didn't exist
    """
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
            return True
        except Exception:
            pass
    return False


# CLI interface for testing
if __name__ == "__main__":
    import sys

    print("Checking for updates...")
    print("-" * 50)

    # Check if --no-cache flag is present
    use_cache = "--no-cache" not in sys.argv

    result = check_for_updates(use_cache=use_cache)

    # Format version display
    current_display = result.current if result.current else 'unknown'
    latest_display = result.latest if result.latest else 'unknown'

    print(f"Current version: {current_display}")
    print(f"Latest version:  {latest_display}")
    print(f"Update available: {result.available}")

    if result.error:
        print(f"Error: {result.error}")

    if result.available:
        print("\n[UPDATE] Update available!")
        if is_semantic_version(latest_display):
            print(f"   New release: {latest_display}")
        print("   Run 'git pull' to update")
    elif not result.error:
        print("\n[OK] You're running the latest version")
