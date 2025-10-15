"""
File Manager for RP System
Handles reading/writing JSON and Markdown files, directory management, and file tracking.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import shutil


class FileManager:
    """
    Centralized file management system for RP infrastructure.
    Handles JSON, Markdown, and directory operations.
    """

    def __init__(self, rp_dir: Union[str, Path]):
        """
        Initialize FileManager with RP directory.

        Args:
            rp_dir: Path to the RP directory
        """
        self.rp_dir = Path(rp_dir)

        if not self.rp_dir.exists():
            raise ValueError(f"RP directory does not exist: {self.rp_dir}")

    # ==================== JSON Operations ====================

    def read_json(self, file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
        """
        Read JSON file with error handling.

        Args:
            file_path: Path to JSON file (relative to rp_dir or absolute)
            default: Default value if file doesn't exist

        Returns:
            Parsed JSON data or default value
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(f"JSON file not found: {full_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {full_path}: {e}")

    def write_json(self, file_path: Union[str, Path], data: Any, indent: int = 2, create_dirs: bool = True) -> None:
        """
        Write data to JSON file.

        Args:
            file_path: Path to JSON file (relative to rp_dir or absolute)
            data: Data to write
            indent: JSON indentation level
            create_dirs: Create parent directories if they don't exist
        """
        full_path = self._resolve_path(file_path)

        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def update_json(self, file_path: Union[str, Path], updates: Dict, create_if_missing: bool = True) -> None:
        """
        Update JSON file by merging with existing data.

        Args:
            file_path: Path to JSON file
            updates: Dictionary of updates to merge
            create_if_missing: Create file if it doesn't exist
        """
        full_path = self._resolve_path(file_path)

        if full_path.exists():
            existing = self.read_json(full_path)
        else:
            if not create_if_missing:
                raise FileNotFoundError(f"JSON file not found: {full_path}")
            existing = {}

        # Deep merge
        merged = self._deep_merge(existing, updates)
        self.write_json(full_path, merged)

    # ==================== IPC Operations (TUI Bridge) ====================

    def write_ipc_input(self, message: str, state_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Write IPC input message in JSON format.

        Args:
            message: User message to write
            state_dir: State directory path (defaults to rp_dir/state)
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "rp_client_input.json"

        data = {
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        self.write_json(json_file, data)

    def read_ipc_input(self, state_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Read IPC input message with auto-migration from .txt to .json.

        Args:
            state_dir: State directory path (defaults to rp_dir/state)

        Returns:
            User message string
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "rp_client_input.json"
        txt_file = state_dir / "rp_client_input.txt"

        # Try JSON first (new format)
        if json_file.exists():
            try:
                data = self.read_json(json_file)
                return data.get("message", "")
            except Exception:
                pass  # Fall through to .txt

        # Try .txt (old format) - no migration, just read
        if txt_file.exists():
            try:
                return txt_file.read_text(encoding='utf-8').strip()
            except Exception:
                return ""

        return ""

    def write_ipc_response(self, response: str, model: Optional[str] = None,
                          cache_stats: Optional[dict] = None,
                          state_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Write IPC response in JSON format.

        Args:
            response: Claude's response text
            model: Model name (optional)
            cache_stats: Cache statistics dict (optional)
            state_dir: State directory path (defaults to rp_dir/state)
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "rp_client_response.json"

        data = {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

        if model:
            data["model"] = model

        if cache_stats:
            data["cache_stats"] = cache_stats

        self.write_json(json_file, data)

    def read_ipc_response(self, state_dir: Optional[Union[str, Path]] = None) -> str:
        """
        Read IPC response with auto-migration from .txt to .json.

        Args:
            state_dir: State directory path (defaults to rp_dir/state)

        Returns:
            Claude's response string
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "rp_client_response.json"
        txt_file = state_dir / "rp_client_response.txt"

        # Try JSON first (new format)
        if json_file.exists():
            try:
                data = self.read_json(json_file)
                return data.get("response", "")
            except Exception:
                pass  # Fall through to .txt

        # Try .txt (old format) - no migration, just read
        if txt_file.exists():
            try:
                return txt_file.read_text(encoding='utf-8').strip()
            except Exception:
                return ""

        return ""

    # ==================== Session Triggers Operations ====================

    def read_session_triggers(self, state_dir: Optional[Union[str, Path]] = None) -> list[str]:
        """
        Read session triggers (active characters) with auto-migration from .txt to .json.

        Args:
            state_dir: State directory path (defaults to rp_dir/state)

        Returns:
            List of active character names
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "session_triggers.json"
        txt_file = state_dir / "session_triggers.txt"

        # Try JSON first (new format)
        if json_file.exists():
            try:
                data = self.read_json(json_file)
                return [char["name"] for char in data.get("characters", [])]
            except Exception:
                pass  # Fall through to .txt

        # Try .txt (old format) and migrate
        if txt_file.exists():
            try:
                content = txt_file.read_text(encoding='utf-8')
                characters = []
                char_data = []

                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        # Format: "- Silas (Triggers: Silas, him, boyfriend)"
                        if '(' in line:
                            name = line.split('(')[0].replace('-', '').strip()
                            if name:
                                characters.append(name)

                                # Extract triggers if present
                                triggers = []
                                if 'Triggers:' in line:
                                    trigger_part = line.split('Triggers:')[1].strip().rstrip(')')
                                    triggers = [t.strip() for t in trigger_part.split(',')]

                                char_data.append({
                                    "name": name,
                                    "triggers": triggers
                                })

                # Migrate to JSON
                if char_data:
                    self.write_session_triggers(char_data, state_dir)
                    # Delete old .txt file
                    txt_file.unlink()

                return characters
            except Exception:
                return []

        return []

    def write_session_triggers(self, characters: list, state_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Write session triggers in JSON format.

        Args:
            characters: List of character dicts with 'name' and 'triggers' keys
            state_dir: State directory path (defaults to rp_dir/state)
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "session_triggers.json"

        data = {
            "characters": characters,
            "last_updated": datetime.now().isoformat()
        }

        self.write_json(json_file, data)

    # ==================== Counter Operations ====================

    def read_response_counter(self, state_dir: Optional[Union[str, Path]] = None) -> int:
        """
        Read response counter with auto-migration from .txt to .json.

        Args:
            state_dir: State directory path (defaults to rp_dir/state)

        Returns:
            Current response count (0 if file doesn't exist)
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "response_counter.json"
        txt_file = state_dir / "response_counter.txt"

        # Try JSON first (new format)
        if json_file.exists():
            try:
                data = self.read_json(json_file)
                return data.get("response_number", 0)
            except Exception:
                pass  # Fall through to .txt

        # Try .txt (old format) and migrate
        if txt_file.exists():
            try:
                count = int(txt_file.read_text(encoding='utf-8').strip())
                # Migrate to JSON
                self.write_response_counter(count, state_dir)
                # Delete old .txt file
                txt_file.unlink()
                return count
            except Exception:
                return 0

        return 0

    def write_response_counter(self, count: int, state_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Write response counter in JSON format.

        Args:
            count: Response count to write
            state_dir: State directory path (defaults to rp_dir/state)
        """
        if state_dir is None:
            state_dir = self.rp_dir / "state"
        else:
            state_dir = Path(state_dir)

        json_file = state_dir / "response_counter.json"

        data = {
            "response_number": count,
            "last_updated": datetime.now().isoformat()
        }

        self.write_json(json_file, data)

    def increment_response_counter(self, state_dir: Optional[Union[str, Path]] = None) -> int:
        """
        Increment response counter and return new value.

        Args:
            state_dir: State directory path (defaults to rp_dir/state)

        Returns:
            New response count after increment
        """
        count = self.read_response_counter(state_dir)
        count += 1
        self.write_response_counter(count, state_dir)
        return count

    # ==================== Markdown Operations ====================

    def read_markdown(self, file_path: Union[str, Path], default: Optional[str] = None) -> str:
        """
        Read markdown file.

        Args:
            file_path: Path to markdown file
            default: Default value if file doesn't exist

        Returns:
            File contents as string
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            if default is not None:
                return default
            raise FileNotFoundError(f"Markdown file not found: {full_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_markdown(self, file_path: Union[str, Path], content: str, create_dirs: bool = True) -> None:
        """
        Write content to markdown file.

        Args:
            file_path: Path to markdown file
            content: Markdown content
            create_dirs: Create parent directories if needed
        """
        full_path = self._resolve_path(file_path)

        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def append_markdown(self, file_path: Union[str, Path], content: str, create_if_missing: bool = True) -> None:
        """
        Append content to markdown file.

        Args:
            file_path: Path to markdown file
            content: Content to append
            create_if_missing: Create file if it doesn't exist
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists() and not create_if_missing:
            raise FileNotFoundError(f"Markdown file not found: {full_path}")

        if create_if_missing:
            full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)

    # ==================== Directory Operations ====================

    def ensure_directory(self, dir_path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if needed.

        Args:
            dir_path: Path to directory (relative to rp_dir or absolute)

        Returns:
            Resolved Path object
        """
        full_path = self._resolve_path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path

    def list_files(self, dir_path: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        List files in directory matching pattern.

        Args:
            dir_path: Directory to search
            pattern: Glob pattern (e.g., "*.md", "*.json")
            recursive: Search recursively

        Returns:
            List of matching file paths
        """
        full_path = self._resolve_path(dir_path)

        if not full_path.exists():
            return []

        if recursive:
            return sorted(full_path.rglob(pattern))
        else:
            return sorted(full_path.glob(pattern))

    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists."""
        full_path = self._resolve_path(file_path)
        return full_path.exists() and full_path.is_file()

    def directory_exists(self, dir_path: Union[str, Path]) -> bool:
        """Check if directory exists."""
        full_path = self._resolve_path(dir_path)
        return full_path.exists() and full_path.is_dir()

    # ==================== File Tracking ====================

    def get_file_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get file metadata (modified time, size, etc.).

        Args:
            file_path: Path to file

        Returns:
            Dictionary with metadata
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        stat = full_path.stat()

        return {
            "path": str(full_path.relative_to(self.rp_dir)),
            "absolute_path": str(full_path),
            "size_bytes": stat.st_size,
            "modified_timestamp": stat.st_mtime,
            "modified_datetime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": full_path.is_file(),
            "is_directory": full_path.is_dir()
        }

    def has_file_changed(self, file_path: Union[str, Path], last_modified: float) -> bool:
        """
        Check if file has been modified since last_modified timestamp.

        Args:
            file_path: Path to file
            last_modified: Previous modification timestamp

        Returns:
            True if file has been modified
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            return False

        current_mtime = full_path.stat().st_mtime
        return current_mtime > last_modified

    # ==================== Backup Operations ====================

    def backup_file(self, file_path: Union[str, Path], backup_suffix: str = ".backup") -> Path:
        """
        Create backup copy of file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file

        Returns:
            Path to backup file
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {full_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = full_path.with_suffix(f"{backup_suffix}_{timestamp}{full_path.suffix}")

        shutil.copy2(full_path, backup_path)
        return backup_path

    # ==================== Helper Methods ====================

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve path relative to rp_dir if not absolute.

        Args:
            path: Path to resolve

        Returns:
            Resolved absolute Path
        """
        path = Path(path)

        if path.is_absolute():
            return path
        else:
            return self.rp_dir / path

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            updates: Updates to merge

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    # ==================== Convenience Methods ====================

    def get_state_file(self, filename: str) -> Path:
        """Get path to file in state/ directory."""
        return self.rp_dir / "state" / filename

    def get_entity_file(self, entity_name: str) -> Path:
        """Get path to entity file in entities/ directory."""
        return self.rp_dir / "entities" / f"{entity_name}.md"

    def get_chapter_file(self, chapter_num: int) -> Path:
        """Get path to chapter file in chapters/ directory."""
        return self.rp_dir / "chapters" / f"chapter_{chapter_num:03d}.md"

    def get_memory_file(self, character_name: str) -> Path:
        """Get path to memory file in memories/ directory."""
        return self.rp_dir / "memories" / f"{character_name}_memories.md"


# StateFileTracker removed - was never used, FileChangeTracker is the active implementation
