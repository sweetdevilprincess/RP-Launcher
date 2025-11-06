"""
File Manager Module

Wraps FileManager for the module management system.
Handles all file operations for JSON, Markdown, directories, and IPC.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import RPModule
from file_manager import FileManager


class FileManagerModule(RPModule):
    """Module wrapper for FileManager.

    Provides centralized file management for all system components.
    Handles JSON, Markdown, directories, IPC, and file tracking.

    Dependencies: None (foundation module)
    """

    # Module metadata
    name = "file_manager"
    version = "1.0.0"
    description = "Centralized file management for JSON, Markdown, and directories"
    dependencies: List[str] = []  # No dependencies
    optional = False  # Core foundation module

    def __init__(self, rp_dir: Path, config: Dict[str, Any], manager: 'ModuleManager'):
        """Initialize file manager module.

        Args:
            rp_dir: Path to RP directory
            config: Module configuration
            manager: Module manager instance
        """
        super().__init__(rp_dir, config, manager)

        # File manager instance (created during initialize)
        self.file_manager: Optional[FileManager] = None

    # ==================== Lifecycle Methods ====================

    def initialize(self) -> bool:
        """Initialize file manager.

        Creates FileManager instance and validates RP directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create file manager
            self.file_manager = FileManager(self.rp_dir)

            self.log_info("File manager initialized successfully")
            return True

        except Exception as e:
            self.log_error("Failed to initialize file manager", e)
            return False

    def start(self) -> bool:
        """Start file manager.

        File manager is passive (no background tasks).

        Returns:
            True (always succeeds)
        """
        self.log_info("File manager started (passive module)")
        return True

    def stop(self) -> bool:
        """Stop file manager.

        File manager is passive (nothing to stop).

        Returns:
            True (always succeeds)
        """
        self.log_info("File manager stopped")
        return True

    def cleanup(self) -> None:
        """Cleanup file manager resources.

        File manager has no persistent resources to cleanup.
        """
        self.log_info("File manager cleanup complete")
        self.file_manager = None

    # ==================== JSON Operations ====================

    def read_json(self, file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
        """Read JSON file with error handling.

        Args:
            file_path: Path to JSON file (relative to rp_dir or absolute)
            default: Default value if file doesn't exist

        Returns:
            Parsed JSON data or default value

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_json(file_path, default)

    def write_json(self, file_path: Union[str, Path], data: Any, indent: int = 2, create_dirs: bool = True) -> None:
        """Write data to JSON file.

        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation level
            create_dirs: Create parent directories if needed

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_json(file_path, data, indent, create_dirs)

    def update_json(self, file_path: Union[str, Path], updates: Dict, create_if_missing: bool = True) -> None:
        """Update JSON file by merging with existing data.

        Args:
            file_path: Path to JSON file
            updates: Dictionary of updates to merge
            create_if_missing: Create file if it doesn't exist

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.update_json(file_path, updates, create_if_missing)

    # ==================== IPC Operations ====================

    def write_ipc_input(self, message: str, state_dir: Optional[Union[str, Path]] = None) -> None:
        """Write IPC input message in JSON format.

        Args:
            message: User message to write
            state_dir: State directory path

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_ipc_input(message, state_dir)

    def read_ipc_input(self, state_dir: Optional[Union[str, Path]] = None) -> str:
        """Read IPC input message.

        Args:
            state_dir: State directory path

        Returns:
            User message string

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_ipc_input(state_dir)

    def write_ipc_response(self, response: str, model: Optional[str] = None,
                          cache_stats: Optional[dict] = None,
                          state_dir: Optional[Union[str, Path]] = None) -> None:
        """Write IPC response in JSON format.

        Args:
            response: Claude's response text
            model: Model name (optional)
            cache_stats: Cache statistics (optional)
            state_dir: State directory path

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_ipc_response(response, model, cache_stats, state_dir)

    def read_ipc_response(self, state_dir: Optional[Union[str, Path]] = None) -> str:
        """Read IPC response.

        Args:
            state_dir: State directory path

        Returns:
            Claude's response string

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_ipc_response(state_dir)

    # ==================== Session Triggers Operations ====================

    def read_session_triggers(self, state_dir: Optional[Union[str, Path]] = None) -> List[str]:
        """Read session triggers (active characters).

        Args:
            state_dir: State directory path

        Returns:
            List of active character names

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_session_triggers(state_dir)

    def write_session_triggers(self, characters: list, state_dir: Optional[Union[str, Path]] = None) -> None:
        """Write session triggers in JSON format.

        Args:
            characters: List of character dicts
            state_dir: State directory path

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_session_triggers(characters, state_dir)

    # ==================== Counter Operations ====================

    def read_response_counter(self, state_dir: Optional[Union[str, Path]] = None) -> int:
        """Read response counter.

        Args:
            state_dir: State directory path

        Returns:
            Current response count

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_response_counter(state_dir)

    def write_response_counter(self, count: int, state_dir: Optional[Union[str, Path]] = None) -> None:
        """Write response counter.

        Args:
            count: Response count to write
            state_dir: State directory path

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_response_counter(count, state_dir)

    def increment_response_counter(self, state_dir: Optional[Union[str, Path]] = None) -> int:
        """Increment response counter and return new value.

        Args:
            state_dir: State directory path

        Returns:
            New response count

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.increment_response_counter(state_dir)

    # ==================== Markdown Operations ====================

    def read_markdown(self, file_path: Union[str, Path], default: Optional[str] = None) -> str:
        """Read markdown file.

        Args:
            file_path: Path to markdown file
            default: Default value if file doesn't exist

        Returns:
            File contents as string

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.read_markdown(file_path, default)

    def write_markdown(self, file_path: Union[str, Path], content: str, create_dirs: bool = True) -> None:
        """Write content to markdown file.

        Args:
            file_path: Path to markdown file
            content: Markdown content
            create_dirs: Create parent directories if needed

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.write_markdown(file_path, content, create_dirs)

    def append_markdown(self, file_path: Union[str, Path], content: str, create_if_missing: bool = True) -> None:
        """Append content to markdown file.

        Args:
            file_path: Path to markdown file
            content: Content to append
            create_if_missing: Create file if it doesn't exist

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        self.file_manager.append_markdown(file_path, content, create_if_missing)

    # ==================== Directory Operations ====================

    def ensure_directory(self, dir_path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if needed.

        Args:
            dir_path: Path to directory

        Returns:
            Resolved Path object

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.ensure_directory(dir_path)

    def list_files(self, dir_path: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """List files in directory matching pattern.

        Args:
            dir_path: Directory to search
            pattern: Glob pattern
            recursive: Search recursively

        Returns:
            List of matching file paths

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.list_files(dir_path, pattern, recursive)

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists.

        Args:
            file_path: Path to file

        Returns:
            True if file exists

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.file_exists(file_path)

    def directory_exists(self, dir_path: Union[str, Path]) -> bool:
        """Check if directory exists.

        Args:
            dir_path: Path to directory

        Returns:
            True if directory exists

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.directory_exists(dir_path)

    # ==================== File Tracking ====================

    def get_file_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file metadata.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with metadata

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.get_file_metadata(file_path)

    def has_file_changed(self, file_path: Union[str, Path], last_modified: float) -> bool:
        """Check if file has been modified since timestamp.

        Args:
            file_path: Path to file
            last_modified: Previous modification timestamp

        Returns:
            True if file has been modified

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.has_file_changed(file_path, last_modified)

    # ==================== Backup Operations ====================

    def backup_file(self, file_path: Union[str, Path], backup_suffix: str = ".backup") -> Path:
        """Create backup copy of file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file

        Returns:
            Path to backup file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.backup_file(file_path, backup_suffix)

    # ==================== Convenience Methods ====================

    def get_state_file(self, filename: str) -> Path:
        """Get path to file in state/ directory.

        Args:
            filename: Filename in state directory

        Returns:
            Path to state file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.get_state_file(filename)

    def get_entity_file(self, entity_name: str) -> Path:
        """Get path to entity file.

        Args:
            entity_name: Name of entity

        Returns:
            Path to entity file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.get_entity_file(entity_name)

    def get_chapter_file(self, chapter_num: int) -> Path:
        """Get path to chapter file.

        Args:
            chapter_num: Chapter number

        Returns:
            Path to chapter file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.get_chapter_file(chapter_num)

    def get_memory_file(self, character_name: str) -> Path:
        """Get path to memory file.

        Args:
            character_name: Character name

        Returns:
            Path to memory file

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager.get_memory_file(character_name)

    # ==================== Command Handling ====================

    def handle_command(self, command: str, args: List[str]) -> Optional[str]:
        """Handle file manager commands.

        Commands:
            status - Show file manager status
            stats - Show file statistics

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Response string or None
        """
        if command == "status":
            status = self.get_status()
            lines = [f"File Manager v{self.version}"]
            lines.append(f"Status: {'Running' if self._running else 'Stopped'}")
            lines.append(f"RP Directory: {self.rp_dir}")
            return "\n".join(lines)

        elif command == "stats":
            try:
                if not self.file_manager:
                    return "File manager not initialized"

                # Count files in different directories
                stats = {}

                # Check common directories
                dirs_to_check = ["state", "chapters", "entities", "memories", "sessions"]
                for dir_name in dirs_to_check:
                    dir_path = self.rp_dir / dir_name
                    if dir_path.exists():
                        files = list(dir_path.glob("*"))
                        stats[dir_name] = len([f for f in files if f.is_file()])
                    else:
                        stats[dir_name] = 0

                lines = ["📊 File Statistics:"]
                for dir_name, count in stats.items():
                    lines.append(f"  {dir_name}/: {count} files")

                return "\n".join(lines)

            except Exception as e:
                return f"Error getting file stats: {e}"

        # Default to parent handler
        return super().handle_command(command, args)

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get module status.

        Returns:
            Status dictionary
        """
        status = super().get_status()

        # Add file manager specific info
        status["rp_directory"] = str(self.rp_dir)

        return status

    # ==================== Direct Access ====================

    def get_file_manager(self) -> FileManager:
        """Get the underlying FileManager instance.

        For legacy code that needs direct access.

        Returns:
            FileManager instance

        Raises:
            RuntimeError: If module not initialized
        """
        if not self.file_manager:
            raise RuntimeError("File manager not initialized")
        return self.file_manager
