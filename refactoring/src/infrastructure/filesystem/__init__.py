"""Filesystem-related adapters."""

from .author_notes_loader import AuthorNotesData, AuthorNotesLoader
from .file_access_service import FileAccessService, TieredContext
from .file_manager import FileManager
from .json_store import JsonStore
from .loaders.tiered_loader import TieredFileLoader, TieredLoadResult
from .markdown_store import MarkdownStore
from .state_paths import StatePaths
from .write_queue import FileWriteQueue

__all__ = [
    "AuthorNotesData",
    "AuthorNotesLoader",
    "FileAccessService",
    "FileManager",
    "FileWriteQueue",
    "JsonStore",
    "MarkdownStore",
    "StatePaths",
    "TieredContext",
    "TieredFileLoader",
    "TieredLoadResult",
]
