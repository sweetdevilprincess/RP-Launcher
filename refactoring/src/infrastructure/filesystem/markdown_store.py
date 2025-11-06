"""Markdown file read/write helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...shared.interfaces import LoggingService


@dataclass(frozen=True)
class MarkdownStore:
    """Read/write convenience for Markdown-backed artefacts."""

    root: Path
    logger: LoggingService

    def read(self, relative_path: Path) -> str | None:
        """Return file contents or None if missing."""

        path = self._resolve(relative_path)
        if not path.exists():
            self.logger.debug("markdown_store.read.missing", context={"path": str(path)})
            return None
        content = path.read_text(encoding="utf-8")
        self.logger.debug(
            "markdown_store.read",
            context={"path": str(path), "bytes": len(content.encode("utf-8"))},
        )
        return content

    def write(self, relative_path: Path, content: str) -> None:
        """Write content to a markdown file, creating parents as needed."""

        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.logger.debug(
            "markdown_store.write",
            context={"path": str(path), "bytes": len(content.encode("utf-8"))},
        )

    def append(self, relative_path: Path, content: str) -> None:
        """Append content with newline separation."""

        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with path.open("a", encoding="utf-8") as handle:
                if path.stat().st_size > 0:
                    handle.write("\n")
                handle.write(content)
        else:
            path.write_text(content, encoding="utf-8")
        self.logger.debug(
            "markdown_store.append",
            context={"path": str(path), "bytes": len(content.encode("utf-8"))},
        )

    def _resolve(self, relative_path: Path) -> Path:
        candidate = (self.root / relative_path).resolve()
        try:
            root = self.root.resolve()
        except FileNotFoundError:
            root = self.root
        if hasattr(candidate, "is_relative_to"):
            if not candidate.is_relative_to(root):  # type: ignore[attr-defined]
                raise ValueError("MarkdownStore paths must stay within the configured root")
        elif not str(candidate).startswith(str(root)):
            raise ValueError("MarkdownStore paths must stay within the configured root")
        return candidate
