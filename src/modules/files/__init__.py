"""
File Management Module

Provides centralized file management for JSON, Markdown, and directories.
Also includes debounced write queue for optimized disk I/O.
"""

from .file_manager_module import FileManagerModule
from .fs_write_queue_module import FSWriteQueueModule

__all__ = ['FileManagerModule', 'FSWriteQueueModule']
