"""
Session Manager Module

Wraps SessionManager for the module management system.
Handles session logs for retry, branching, checkpointing, and switching.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from session_manager import SessionManager


class SessionManagerModule(RPModule):
    """Module wrapper for SessionManager.

    Provides session management functionality within the module system.
    Handles retry, branching, checkpointing, and session switching.

    Dependencies: None (can optionally use file_manager)
    """

    # Module metadata
    name = "session_manager"
    version = "1.0.0"
    description = "Session log management for retry, branching, and checkpointing"
    dependencies: List[str] = []  # No hard dependencies
    optional = False  # Core module

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize session manager module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # Session manager instance (created during initialize)
        self.session_manager: Optional[SessionManager] = None

        # Configuration
        self.auto_checkpoint_frequency = config.get('auto_checkpoint_frequency', 10)
        self.keep_archived = config.get('keep_archived', 20)
        self.compression = config.get('compression', False)

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize session manager.

        Creates SessionManager instance and validates RP directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create session manager
            self.session_manager = SessionManager(self.rp_dir)

            # Ensure active session exists (or can be created)
            if not self.session_manager.active_session_path.exists():
                self.log_info("No active session found - will be created on first use")

            self.log_info("Session manager initialized successfully")
            return True

        except Exception as e:
            self.log_error("Failed to initialize session manager", e)
            return False

    def start(self) -> bool:
        """Start session manager.

        Session manager is passive (no background tasks).

        Returns:
            True (always succeeds)
        """
        self.log_info("Session manager started (passive module)")
        return True

    def stop(self) -> bool:
        """Stop session manager.

        Session manager is passive (nothing to stop).

        Returns:
            True (always succeeds)
        """
        self.log_info("Session manager stopped")
        return True

    def cleanup(self) -> None:
        """Cleanup session manager resources.

        Session manager has no persistent resources to cleanup.
        """
        self.log_info("Session manager cleanup complete")
        self.session_manager = None

    # ==================== Session Commands ====================

    def retry(self, tags: Optional[List[str]] = None) -> Path:
        """Retry last response.

        Args:
            tags: Optional tags for archived session

        Returns:
            Path to archived session

        Raises:
            RuntimeError: If module not initialized
            ValueError: If session is empty
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.retry(tags)

    def branch(
        self,
        branch_name: str,
        response_num: Optional[int] = None,
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> Path:
        """Create named branch from specific point.

        Args:
            branch_name: Name for the branch
            response_num: Response to branch from (default: current)
            tags: Optional tags
            description: Optional description

        Returns:
            Path to branch session file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.branch(branch_name, response_num, tags, description)

    def checkpoint(
        self,
        checkpoint_name: str,
        tags: Optional[List[str]] = None,
        description: str = ""
    ) -> Path:
        """Save checkpoint at current point.

        Args:
            checkpoint_name: Name for checkpoint
            tags: Optional tags
            description: Optional description

        Returns:
            Path to checkpoint file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.checkpoint(checkpoint_name, tags, description)

    def switch(self, session_name: str) -> Path:
        """Switch to different session.

        Args:
            session_name: Name of session to switch to

        Returns:
            Path to new active session

        Raises:
            RuntimeError: If module not initialized
            FileNotFoundError: If session doesn't exist
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.switch(session_name)

    def list_sessions(self, tag_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available sessions.

        Args:
            tag_filter: Optional tag to filter by

        Returns:
            List of session info dictionaries

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.list_sessions(tag_filter)

    # ==================== Message Management ====================

    def append_message_entry(self, message: Dict[str, Any], status: Optional[str] = None) -> Dict[str, Any]:
        """Append a message entry to the active session log."""
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.append_message_entry(message, status=status)

    def update_message_entry(
        self,
        response_num: int,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        merge: bool = True
    ) -> Dict[str, Any]:
        """Update message metadata/status for a specific response."""
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.update_message_entry(
            response_num=response_num,
            metadata=metadata,
            status=status,
            merge=merge
        )

    # ==================== Message Management ====================

    def append_message(
        self,
        user_message: str,
        assistant_response: str,
        agent_data_background: Optional[Dict] = None,
        agent_data_immediate: Optional[Dict] = None,
        model_info: Optional[Dict] = None
    ) -> int:
        """Append new message to active session.

        Args:
            user_message: User's input
            assistant_response: Claude's response
            agent_data_background: Agent analyses from previous response
            agent_data_immediate: Context for next response
            model_info: Model information

        Returns:
            New response number

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.append_message(
            user_message,
            assistant_response,
            agent_data_background,
            agent_data_immediate,
            model_info
        )

    def update_message_agent_data(
        self,
        response_num: int,
        field: str,
        data: Dict[str, Any]
    ) -> None:
        """Update agent data for a specific message.

        Args:
            response_num: Response number to update (1-indexed)
            field: "agent_data_background" or "agent_data_immediate"
            data: Agent data to set

        Raises:
            RuntimeError: If module not initialized
            ValueError: If response_num or field invalid
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        self.session_manager.update_message_agent_data(response_num, field, data)

    # ==================== Utility Methods ====================

    def get_current_response_count(self) -> int:
        """Get current response count from active session.

        Returns:
            Current response count

        Raises:
            RuntimeError: If module not initialized
            FileNotFoundError: If active session doesn't exist
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.get_current_response_count()

    def session_exists(self, session_name: str) -> bool:
        """Check if a session exists.

        Args:
            session_name: Name of session to check

        Returns:
            True if session exists, False otherwise

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        return self.session_manager.session_exists(session_name)

    def create_initial_session(self, rp_name: str, chapter: int = 1) -> None:
        """Create initial empty session.

        Args:
            rp_name: Name of the RP
            chapter: Starting chapter number

        Raises:
            RuntimeError: If module not initialized
            FileExistsError: If active session already exists
        """
        if not self.session_manager:
            raise RuntimeError("Session manager not initialized")

        self.session_manager.create_initial_session(rp_name, chapter)

    # ==================== Auto-Checkpoint Feature ====================

    def should_auto_checkpoint(self, response_num: int) -> bool:
        """Check if auto-checkpoint should be created.

        Args:
            response_num: Current response number

        Returns:
            True if checkpoint should be created
        """
        if self.auto_checkpoint_frequency <= 0:
            return False

        return response_num % self.auto_checkpoint_frequency == 0

    def auto_checkpoint(self, response_num: int) -> Optional[Path]:
        """Create automatic checkpoint if needed.

        Args:
            response_num: Current response number

        Returns:
            Path to checkpoint if created, None otherwise
        """
        if not self.should_auto_checkpoint(response_num):
            return None

        try:
            checkpoint_name = f"auto_{response_num}"
            path = self.checkpoint(
                checkpoint_name,
                tags=["auto-checkpoint"],
                description=f"Automatic checkpoint at response {response_num}"
            )
            self.log_info(f"Auto-checkpoint created: {checkpoint_name}")
            return path

        except Exception as e:
            self.log_error(f"Failed to create auto-checkpoint: {e}")
            return None

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle session-specific commands.

        Commands:
            status - Show session manager status
            list [tag] - List sessions (optionally filtered by tag)
            info - Show current session info

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"Session Manager v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")

            # Add session count
            try:
                if self.session_manager:
                    sessions = self.list_sessions()
                    lines.append(f"Total sessions: {len(sessions)}")

                    # Count by type
                    types = {}
                    for s in sessions:
                        t = s['type']
                        types[t] = types.get(t, 0) + 1

                    lines.append(f"Active: {types.get('active', 0)}")
                    lines.append(f"Branches: {types.get('branch', 0)}")
                    lines.append(f"Checkpoints: {types.get('checkpoint', 0)}")
                    lines.append(f"Archived: {types.get('archived', 0)}")
            except Exception as e:
                lines.append(f"Error: {e}")

            return "\n".join(lines)

        elif command == "list":
            tag_filter = args[0] if args else None
            try:
                sessions = self.list_sessions(tag_filter)
                if not sessions:
                    return "No sessions found"

                lines = ["📁 Sessions:"]
                for s in sessions[:10]:  # Limit to 10
                    type_icon = {
                        "active": "▶️",
                        "branch": "🌿",
                        "checkpoint": "💾",
                        "archived": "📦"
                    }.get(s['type'], "📄")

                    lines.append(
                        f"  {type_icon} {s['name']} "
                        f"({s['response_count']} responses) "
                        f"[{', '.join(s['tags'][:3])}]"
                    )

                if len(sessions) > 10:
                    lines.append(f"  ... and {len(sessions) - 10} more")

                return "\n".join(lines)

            except Exception as e:
                return f"Error listing sessions: {e}"

        elif command == "info":
            try:
                if not self.session_manager:
                    return "Session manager not initialized"

                active = self.session_manager.load_session()
                lines = ["📊 Current Session Info:"]
                lines.append(f"  ID: {active['session_id']}")
                lines.append(f"  Type: {active['session_type']}")
                lines.append(f"  Responses: {active['current_response']}")
                lines.append(f"  Tags: {', '.join(active.get('tags', []))}")
                lines.append(f"  Last Modified: {active.get('last_modified', 'Unknown')}")

                if active.get('parent_session'):
                    lines.append(f"  Parent: {active['parent_session']}")
                    lines.append(f"  Branch Point: {active.get('branch_point', 'N/A')}")

                return "\n".join(lines)

            except Exception as e:
                return f"Error getting session info: {e}"

        # Default to parent handler
        return super().handle_command(command, args)

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status with session-specific info.

        Returns:
            Status dictionary
        """
        status = super().get_status()

        # Add session-specific info
        if self.session_manager:
            try:
                status["session_count"] = len(self.list_sessions())
                status["current_response"] = self.get_current_response_count()
            except Exception:
                pass  # Ignore errors in status

        status["auto_checkpoint_frequency"] = self.auto_checkpoint_frequency
        status["keep_archived"] = self.keep_archived

        return status
