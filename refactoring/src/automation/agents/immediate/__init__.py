"""Immediate agent implementations package.

This package contains immediate agents that run BEFORE Claude responds
to gather context and enhance the prompt with relevant information.
"""

from .fact_extraction_agent import FactExtractionAgent
from .memory_extraction_agent import MemoryExtractionAgent
from .plot_thread_extraction_agent import PlotThreadExtractionAgent

__all__ = [
    "FactExtractionAgent",
    "MemoryExtractionAgent",
    "PlotThreadExtractionAgent",
]
