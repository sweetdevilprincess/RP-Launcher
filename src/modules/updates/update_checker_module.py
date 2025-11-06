"""
Update Checker Module

Wraps UpdateChecker for the module management system.
Checks GitHub for available updates.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from update_checker import (
    check_for_updates,
    clear_cache,
    UpdateCheckResult,
    CACHE_DURATION
)


class UpdateCheckerModule(RPModule):
    """Module wrapper for UpdateChecker.

    Checks GitHub for available updates:
    - Semantic version tag checking
    - Commit SHA comparison
    - Result caching (24 hour default)
    - Rate limit handling

    Dependencies: None (optional module)
    """

    # Module metadata
    name = "update_checker"
    version = "1.0.0"
    description = "GitHub update checker for version checking"
    dependencies: List[str] = []  # No dependencies
    optional = True  # Optional module (can be disabled)

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize update checker module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # Configuration
        self.check_on_startup = config.get('check_on_startup', False)
        self.cache_duration = config.get('cache_duration', CACHE_DURATION)
        self.timeout = config.get('timeout', 3)
        self.auto_check_interval = config.get('auto_check_interval', 86400)  # 24 hours

        # Last check result
        self.last_result: Optional[UpdateCheckResult] = None

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize update checker.

        Optionally checks for updates on startup.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log_info("Update checker initialized")

            # Check on startup if configured
            if self.check_on_startup:
                self.log_info("Checking for updates...")
                result = self.check_for_updates(use_cache=True)

                if result.error:
                    self.log_warning(f"Update check error: {result.error}")
                elif result.available:
                    self.log_info(f"Update available: {result.latest}")
                else:
                    self.log_info("Running latest version")

            return True

        except Exception as e:
            self.log_error("Failed to initialize update checker", e)
            return False

    def start(self) -> bool:
        """Start update checker.

        Update checker is passive (no background tasks by default).

        Returns:
            True (always succeeds)
        """
        self.log_info("Update checker started (passive module)")
        return True

    def stop(self) -> bool:
        """Stop update checker.

        Update checker is passive (nothing to stop).

        Returns:
            True (always succeeds)
        """
        self.log_info("Update checker stopped")
        return True

    def cleanup(self) -> None:
        """Cleanup update checker resources.

        Update checker has no persistent resources to cleanup.
        """
        self.log_info("Update checker cleanup complete")

    # ==================== Update Check Operations ====================

    def check_for_updates(
        self,
        use_cache: bool = True,
        force: bool = False
    ) -> UpdateCheckResult:
        """Check for available updates.

        Args:
            use_cache: Use cached result if available
            force: Force check even if recently checked

        Returns:
            UpdateCheckResult with update information
        """
        # Override cache if forcing
        if force:
            use_cache = False

        result = check_for_updates(
            use_cache=use_cache,
            cache_duration=self.cache_duration,
            timeout=self.timeout
        )

        self.last_result = result
        return result

    def clear_cache(self) -> bool:
        """Clear update check cache.

        Returns:
            True if cache was cleared
        """
        return clear_cache()

    def get_last_result(self) -> Optional[UpdateCheckResult]:
        """Get last check result.

        Returns:
            Last UpdateCheckResult or None
        """
        return self.last_result

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle update checker commands.

        Commands:
            status - Show update checker status
            check - Check for updates (uses cache)
            check --force - Force update check (bypass cache)
            clear-cache - Clear update check cache

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"Update Checker v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")
            lines.append(f"Check on startup: {self.check_on_startup}")
            lines.append(f"Cache duration: {self.cache_duration}s")

            # Add last result if available
            if self.last_result:
                lines.append(f"\nLast check:")
                lines.append(f"  Current: {self.last_result.current}")
                lines.append(f"  Latest: {self.last_result.latest}")
                lines.append(f"  Update available: {self.last_result.available}")

                if self.last_result.error:
                    lines.append(f"  Error: {self.last_result.error}")

            return "\n".join(lines)

        elif command == "check":
            try:
                # Check for --force flag
                force = "--force" in args

                self.log_info("Checking for updates...")
                result = self.check_for_updates(use_cache=not force, force=force)

                lines = ["🔍 Update Check Result:"]
                lines.append(f"  Current version: {result.current}")
                lines.append(f"  Latest version: {result.latest}")

                if result.error:
                    lines.append(f"  ❌ Error: {result.error}")
                elif result.available:
                    lines.append(f"  ✨ Update available!")
                    lines.append(f"  Run 'git pull' to update")
                else:
                    lines.append(f"  ✓ You're running the latest version")

                return "\n".join(lines)

            except Exception as e:
                return f"Error checking for updates: {e}"

        elif command == "clear-cache":
            try:
                if self.clear_cache():
                    return "✓ Update check cache cleared"
                else:
                    return "Cache was already empty"

            except Exception as e:
                return f"Error clearing cache: {e}"

        # Default to parent handler
        return super().handle_command(command, args)

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status with update checker-specific info.

        Returns:
            Status dictionary
        """
        status = super().get_status()

        # Add update checker-specific info
        status["check_on_startup"] = self.check_on_startup
        status["cache_duration"] = self.cache_duration

        if self.last_result:
            status["last_check"] = {
                "available": self.last_result.available,
                "current": self.last_result.current,
                "latest": self.last_result.latest,
                "error": self.last_result.error
            }

        return status
