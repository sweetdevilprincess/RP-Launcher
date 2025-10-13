"""Claude Code CLI wrapper."""

import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional


class ClaudeNotFoundError(Exception):
    """Raised when Claude Code CLI is not found."""
    pass


def _find_claude_exe() -> Optional[str]:
    """Find claude.exe in common installation locations.

    Returns:
        Path to claude.exe or None if not found
    """
    # Check if it's in PATH first
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path

    # Check common installation locations
    possible_locations = [
        # User's .local/bin (common for Claude Code)
        Path.home() / ".local" / "bin" / "claude.exe",
        # Current user's AppData
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "claude" / "claude.exe",
        # Program Files
        Path(os.environ.get("PROGRAMFILES", "")) / "Claude" / "claude.exe",
    ]

    for location in possible_locations:
        if location.exists():
            return str(location)

    return None


def run_claude(
    message: str,
    cwd: Optional[Path] = None,
    timeout: int = 300,
    continue_conversation: bool = True
) -> subprocess.CompletedProcess:
    """Run Claude Code CLI with a message.

    Args:
        message: The message/prompt to send to Claude
        cwd: Working directory for Claude Code (usually RP folder)
        timeout: Timeout in seconds (default 300 = 5 minutes)
        continue_conversation: If True, use -c flag to continue most recent
                              conversation in this directory (default True)

    Returns:
        CompletedProcess with stdout, stderr, returncode

    Raises:
        ClaudeNotFoundError: If Claude Code CLI is not found
        subprocess.TimeoutExpired: If command times out
    """
    # Find claude.exe
    claude_path = _find_claude_exe()
    if not claude_path:
        raise ClaudeNotFoundError(
            "Claude Code CLI not found. Checked:\n"
            "  - System PATH\n"
            "  - %USERPROFILE%\\.local\\bin\\claude.exe\n"
            "  - %LOCALAPPDATA%\\Programs\\claude\\claude.exe\n"
            "  - %PROGRAMFILES%\\Claude\\claude.exe\n\n"
            "Please install Claude Code or add it to your PATH:\n"
            "https://docs.claude.com/en/docs/claude-code"
        )

    # Build command with -c flag if continuing conversation
    cmd = [claude_path]
    if continue_conversation:
        cmd.append("-c")

    # Run claude with the message via stdin (to avoid command-line length limits)
    result = subprocess.run(
        cmd,
        input=message,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding='utf-8',  # Handle Unicode characters properly on Windows
        timeout=timeout
    )

    return result
