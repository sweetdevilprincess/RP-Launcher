"""Author's Notes loader - Highest priority story rules and constraints.

This module loads AUTHOR'S_NOTES.md from the RP root directory and parses
it for:
- Story mechanics and systems
- Character behavior rules (absolutes)
- Information asymmetry tracking
- Conditional rules
- Meta story rules (POV, pacing)
- Active Genome references (for complex RPs)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...shared.interfaces import LoggingService


@dataclass
class AuthorNotesData:
    """Parsed author notes with main content and genome reference."""

    content: str  # Full author notes content
    active_genome_file: str | None = None  # e.g., "GENOME_DEMON_LORD_PATH.md"
    active_genome_since: str | None = None  # e.g., "Chapter 15"
    active_genome_reason: str | None = None  # Why this genome was activated


class AuthorNotesLoader:
    """Load and parse AUTHOR'S_NOTES.md with genome reference extraction."""

    AUTHOR_NOTES_FILENAME = "AUTHOR'S_NOTES.md"
    GENOME_SECTION_PATTERN = re.compile(
        r"##\s+Current Active Genome\s*\n"
        r"\s*\*\*Active:\*\*\s+(.+?)\.md\s*\n"
        r"\s*\*\*Since:\*\*\s+(.+?)\s*\n"
        r"\s*\*\*Reason:\*\*\s+(.+?)(?:\n|$)",
        re.IGNORECASE | re.MULTILINE
    )

    def __init__(self, rp_dir: Path, logger: LoggingService) -> None:
        """Initialize author notes loader.

        Args:
            rp_dir: Root directory of the RP
            logger: Logging service for debug/info
        """
        self._rp_dir = rp_dir
        self._logger = logger

    def load(self) -> AuthorNotesData:
        """Load author notes from AUTHOR'S_NOTES.md.

        Returns:
            AuthorNotesData with content and optional genome reference
        """
        author_notes_path = self._rp_dir / self.AUTHOR_NOTES_FILENAME

        if not author_notes_path.exists():
            self._logger.debug(
                "author_notes.not_found",
                context={"path": str(author_notes_path)}
            )
            return AuthorNotesData(content="")

        try:
            with open(author_notes_path, "r", encoding="utf-8") as f:
                content = f.read()

            self._logger.info(
                "author_notes.loaded",
                context={
                    "path": str(author_notes_path),
                    "size": len(content),
                }
            )

            # Parse genome reference if present
            genome_data = self._parse_genome_reference(content)

            # If genome is referenced, load and append it
            if genome_data.active_genome_file:
                genome_content = self._load_genome_file(genome_data.active_genome_file)
                if genome_content:
                    # Append genome content to author notes
                    content = f"{content}\n\n---\n\n## ACTIVE GENOME CONTENT\n\n{genome_content}"
                    self._logger.info(
                        "author_notes.genome_loaded",
                        context={"genome": genome_data.active_genome_file}
                    )

            return AuthorNotesData(
                content=content,
                active_genome_file=genome_data.active_genome_file,
                active_genome_since=genome_data.active_genome_since,
                active_genome_reason=genome_data.active_genome_reason,
            )

        except Exception as e:
            self._logger.error(
                "author_notes.load_failed",
                context={"error": str(e), "path": str(author_notes_path)}
            )
            return AuthorNotesData(content="")

    def _parse_genome_reference(self, content: str) -> AuthorNotesData:
        """Extract genome reference from author notes if present.

        Args:
            content: Author notes content

        Returns:
            AuthorNotesData with genome metadata (or None if not found)
        """
        match = self.GENOME_SECTION_PATTERN.search(content)

        if match:
            genome_file = match.group(1).strip()
            genome_since = match.group(2).strip()
            genome_reason = match.group(3).strip()

            # Add .md extension if not present
            if not genome_file.endswith(".md"):
                genome_file = f"{genome_file}.md"

            self._logger.debug(
                "author_notes.genome_found",
                context={
                    "file": genome_file,
                    "since": genome_since,
                    "reason": genome_reason,
                }
            )

            return AuthorNotesData(
                content="",  # Will be set by caller
                active_genome_file=genome_file,
                active_genome_since=genome_since,
                active_genome_reason=genome_reason,
            )

        return AuthorNotesData(content="")

    def _load_genome_file(self, genome_filename: str) -> str:
        """Load a genome file from the RP directory.

        Args:
            genome_filename: Genome filename (e.g., "GENOME_DEMON_LORD_PATH.md")

        Returns:
            Genome file content, or empty string if not found
        """
        genome_path = self._rp_dir / genome_filename

        if not genome_path.exists():
            self._logger.warning(
                "author_notes.genome_not_found",
                context={"path": str(genome_path)}
            )
            return ""

        try:
            with open(genome_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self._logger.error(
                "author_notes.genome_load_failed",
                context={"error": str(e), "path": str(genome_path)}
            )
            return ""


__all__ = ["AuthorNotesLoader", "AuthorNotesData"]
