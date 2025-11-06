"""Base Agent - Foundation for all automation agents.

Provides LLM access via the router system, automatically using
the secondary LLM when configured (or falling back to primary).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.infrastructure.llm.base import LLMResponse
from src.infrastructure.llm.llm_router import call_secondary_llm

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class BaseAgent(ABC):
    """Abstract base class for all automation agents.

    Provides:
    - LLM access via call_llm() method
    - Automatic routing to secondary LLM (or primary if not configured)
    - Common initialization pattern
    - Abstract interface for agent ID and execution
    """

    def __init__(
        self,
        *,
        rp_dir: Path,
        log_file: Optional[Path] = None,
        bridge: Optional["BridgeService"] = None,
    ):
        """Initialize base agent.

        Args:
            rp_dir: RP directory path
            log_file: Optional log file path
            bridge: Bridge service for LLM access (required for production use)
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.bridge = bridge

    @abstractmethod
    def get_agent_id(self) -> str:
        """Return unique agent identifier.

        Returns:
            Agent ID string (e.g., "memory_creation")
        """
        pass

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """Execute agent logic.

        Returns:
            Agent result as string
        """
        pass

    # ==========================================================================
    # LLM Access
    # ==========================================================================

    def call_llm(
        self,
        user_message: str,
        *,
        cached_context: str | None = None,
        **kwargs
    ) -> LLMResponse:
        """Call LLM using the secondary provider (or primary if not configured).

        This method automatically routes to the correct LLM based on the
        bridge's configuration:
        - If use_secondary_for_automation is True, uses secondary client
        - Otherwise, falls back to primary client

        Args:
            user_message: The prompt to send to the LLM
            cached_context: Optional context to cache (TIER_1 files)
            **kwargs: Additional LLM options (temperature, etc.)

        Returns:
            LLM response with content and usage stats

        Raises:
            RuntimeError: If bridge not provided or LLM call fails
        """
        if not self.bridge:
            raise RuntimeError(
                f"Agent {self.get_agent_id()} cannot call LLM: bridge not provided. "
                f"Pass bridge parameter when creating agent."
            )

        try:
            return call_secondary_llm(
                bridge=self.bridge,
                user_message=user_message,
                cached_context=cached_context,
                **kwargs
            )
        except Exception as e:
            # Log error and re-raise
            agent_id = self.get_agent_id()
            raise RuntimeError(f"Agent {agent_id} LLM call failed: {e}") from e

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def log(self, message: str) -> None:
        """Log a message to the agent's log file.

        Args:
            message: Message to log
        """
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{self.get_agent_id()}] {message}\n")
            except Exception:
                # Silently fail if logging fails
                pass

    def parse_json_response(self, response: LLMResponse) -> dict | list | None:
        """Parse JSON from LLM response, extracting from markdown if needed.

        Handles common LLM response formats:
        - Plain JSON: {"key": "value"}
        - Markdown JSON blocks: ```json ... ```
        - Generic code blocks: ``` ... ```

        Args:
            response: LLM response object

        Returns:
            Parsed JSON as dict/list, or None if parsing fails
        """
        import json

        content = response.content.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.log(f"Failed to parse JSON from LLM response: {e}")
            self.log(f"Response content: {content}")
            return None

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format for JSON storage.

        Returns:
            ISO 8601 formatted timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()

    def load_json(self, file_path: Path) -> dict | list | None:
        """Load JSON file with error handling.

        Args:
            file_path: Path to JSON file (relative to rp_dir or absolute)

        Returns:
            Parsed JSON as dict/list, or None if reading/parsing fails
        """
        import json

        # Make path absolute if relative
        if not file_path.is_absolute():
            file_path = self.rp_dir / file_path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log(f"JSON file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            self.log(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            self.log(f"Failed to read JSON from {file_path}: {e}")
            return None

    def save_json(self, file_path: Path, data: dict | list) -> bool:
        """Save data to JSON file with error handling.

        Args:
            file_path: Path to JSON file (relative to rp_dir or absolute)
            data: Data to save (dict or list)

        Returns:
            True if successful, False otherwise
        """
        import json

        # Make path absolute if relative
        if not file_path.is_absolute():
            file_path = self.rp_dir / file_path

        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.log(f"Saved JSON to {file_path}")
            return True
        except Exception as e:
            self.log(f"Failed to save JSON to {file_path}: {e}")
            return False

    def append_to_json_array(self, file_path: Path, entry: dict) -> bool:
        """Append entry to JSON array file.

        If file doesn't exist, creates it with [entry].
        If file exists, appends entry to the array.

        Args:
            file_path: Path to JSON array file (relative to rp_dir or absolute)
            entry: Dict entry to append

        Returns:
            True if successful, False otherwise
        """
        # Make path absolute if relative
        if not file_path.is_absolute():
            file_path = self.rp_dir / file_path

        # Load existing array or create new one
        existing_data = self.load_json(file_path)

        if existing_data is None:
            # File doesn't exist or is invalid - create new array
            data = [entry]
        elif isinstance(existing_data, list):
            # File exists and is an array - append
            data = existing_data + [entry]
        else:
            self.log(f"JSON file {file_path} is not an array, cannot append")
            return False

        # Save updated array
        return self.save_json(file_path, data)

    def save_to_entity_json(
        self,
        character: str,
        data: dict | list,
        filename: str
    ) -> bool:
        """Save data to entity's JSON file.

        Args:
            character: Character name (used as directory name)
            data: Data to save
            filename: Filename (e.g., "memory.json", "relationships.json")

        Returns:
            True if successful, False otherwise
        """
        entity_dir = self.rp_dir / "state" / "entities" / character
        file_path = entity_dir / filename
        return self.save_json(file_path, data)

    def append_to_entity_json(
        self,
        character: str,
        entry: dict,
        filename: str
    ) -> bool:
        """Append entry to entity's JSON array file.

        Args:
            character: Character name (used as directory name)
            entry: Dict entry to append
            filename: Filename (e.g., "memory.json")

        Returns:
            True if successful, False otherwise
        """
        entity_dir = self.rp_dir / "state" / "entities" / character
        file_path = entity_dir / filename
        return self.append_to_json_array(file_path, entry)

    def load_entity_json(self, character: str, filename: str) -> dict | list | None:
        """Load entity's JSON file.

        Args:
            character: Character name (used as directory name)
            filename: Filename (e.g., "memory.json")

        Returns:
            Parsed JSON or None if file doesn't exist
        """
        entity_dir = self.rp_dir / "state" / "entities" / character
        file_path = entity_dir / filename
        return self.load_json(file_path)


__all__ = ["BaseAgent"]
