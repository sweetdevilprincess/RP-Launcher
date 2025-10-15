#!/usr/bin/env python3
"""
Base Agent Class

Abstract base class for all DeepSeek agents. Provides common functionality:
- Error handling and logging
- DeepSeek API calls with consistent temperature
- Template method pattern for agent execution

All agents inherit from BaseAgent and override 5 methods:
1. get_agent_id() - Unique identifier
2. get_description() - Human-readable description
3. gather_data() - Read files, prepare context
4. build_prompt() - Format DeepSeek prompt
5. format_output() - Format result for cache
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any

from src.clients.deepseek import call_deepseek
from src.automation.core import log_to_file


class BaseAgent(ABC):
    """Abstract base class for all DeepSeek agents

    Provides common execution logic (timing, error handling, logging)
    while allowing each agent to define its specific behavior.

    Usage:
        class MyAgent(BaseAgent):
            def get_agent_id(self) -> str:
                return "my_agent"

            def get_description(self) -> str:
                return "Does something useful"

            def gather_data(self, *args, **kwargs) -> dict:
                return {"key": "value"}

            def build_prompt(self, data: dict) -> str:
                return f"Analyze: {data['key']}"

            def format_output(self, result: str, data: dict) -> str:
                return f"**Result:**\n{result}"
    """

    def __init__(self, rp_dir: Path, log_file: Optional[Path] = None):
        """Initialize base agent

        Args:
            rp_dir: RP directory path
            log_file: Optional log file for agent activity
        """
        self.rp_dir = rp_dir
        self.log_file = log_file

    @abstractmethod
    def get_agent_id(self) -> str:
        """Get unique agent identifier

        Returns:
            Agent ID like 'response_analyzer', 'memory_creation', etc.
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable agent description

        Returns:
            Description like 'Scene classification and pacing analysis'
        """
        pass

    @abstractmethod
    def gather_data(self, *args, **kwargs) -> dict:
        """Gather data needed for prompt

        This method reads files, prepares context, and returns
        a dict of data that will be passed to build_prompt()
        and format_output().

        Args:
            *args: Agent-specific arguments
            **kwargs: Agent-specific keyword arguments

        Returns:
            Dict of data for prompt and output formatting
        """
        pass

    @abstractmethod
    def build_prompt(self, data: dict) -> str:
        """Build DeepSeek prompt from gathered data

        Args:
            data: Dict returned from gather_data()

        Returns:
            Formatted prompt string for DeepSeek
        """
        pass

    @abstractmethod
    def format_output(self, result: str, data: dict) -> str:
        """Format DeepSeek result for cache file

        Args:
            result: Raw result from DeepSeek
            data: Original data dict from gather_data()

        Returns:
            Formatted output string for agent_analysis.md
        """
        pass

    def execute(self, *args, **kwargs) -> str:
        """Execute agent (main entry point)

        This method orchestrates the agent execution:
        1. Gather data
        2. Build prompt
        3. Call DeepSeek
        4. Format output

        Common logic (timing, error handling, logging) is handled here.

        Args:
            *args: Passed to gather_data()
            **kwargs: Passed to gather_data()

        Returns:
            Formatted output string ready for cache

        Raises:
            Exception: Any exception from gather_data, DeepSeek, or format_output
        """
        import time

        try:
            # Log execution start
            if self.log_file:
                log_to_file(self.log_file, f"[{self.get_agent_id()}] Executing agent")

            total_start = time.perf_counter()

            # Step 1: Gather data (file I/O)
            gather_start = time.perf_counter()
            data = self.gather_data(*args, **kwargs)
            gather_time = (time.perf_counter() - gather_start) * 1000

            # Step 2: Build prompt (in-memory processing)
            prompt_start = time.perf_counter()
            prompt = self.build_prompt(data)
            prompt_time = (time.perf_counter() - prompt_start) * 1000

            # Step 3: Call DeepSeek (network I/O + LLM processing)
            api_start = time.perf_counter()
            result = call_deepseek(
                prompt,
                rp_dir=self.rp_dir,
                temperature=0.3  # Consistent for analysis agents
            )
            api_time = (time.perf_counter() - api_start) * 1000

            # Step 4: Format output (in-memory processing)
            format_start = time.perf_counter()
            formatted = self.format_output(result, data)
            format_time = (time.perf_counter() - format_start) * 1000

            total_time = (time.perf_counter() - total_start) * 1000

            # Store timing metrics in data dict for AgentCoordinator
            data['_timing'] = {
                'gather_ms': round(gather_time, 1),
                'prompt_ms': round(prompt_time, 1),
                'api_ms': round(api_time, 1),
                'format_ms': round(format_time, 1),
                'total_ms': round(total_time, 1)
            }

            # Log success with timing breakdown
            if self.log_file:
                log_to_file(self.log_file,
                    f"[{self.get_agent_id()}] Completed in {total_time:.1f}ms "
                    f"(gather: {gather_time:.1f}ms, prompt: {prompt_time:.1f}ms, "
                    f"api: {api_time:.1f}ms, format: {format_time:.1f}ms)")

            return formatted

        except Exception as e:
            # Log error
            if self.log_file:
                log_to_file(self.log_file, f"[{self.get_agent_id()}] Error: {e}")

            # Re-raise for AgentCoordinator to handle
            raise

    # Utility methods for common operations

    def _read_file_safe(self, file_path: Path, default: str = "") -> str:
        """Safely read a file with fallback

        Args:
            file_path: Path to file
            default: Default value if file doesn't exist

        Returns:
            File contents or default
        """
        try:
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            else:
                return default
        except Exception as e:
            if self.log_file:
                log_to_file(self.log_file, f"[{self.get_agent_id()}] Warning: Could not read {file_path}: {e}")
            return default

    def _get_temperature(self) -> float:
        """Get temperature for DeepSeek calls

        Override this method if your agent needs a different temperature.
        Default is 0.3 for consistent analysis.

        Returns:
            Temperature value (0.0-1.0)
        """
        return 0.3
