"""Agent implementations package.

This package contains all the concrete agent implementations that inherit
from BaseAgent and provide specific automation functionality.
"""

from .chapter_compression_agent import ChapterCompressionAgent
from .contradiction_synthesis_agent import ContradictionSynthesisAgent
from .knowledge_extraction_agent import KnowledgeExtractionAgent
from .memory_creation_agent import MemoryCreationAgent
from .plot_thread_detection_agent import PlotThreadDetectionAgent
from .relationship_analysis_agent import RelationshipAnalysisAgent
from .response_analyzer_agent import ResponseAnalyzerAgent
from .time_tracking_agent import TimeTrackingAgent

__all__ = [
    "ChapterCompressionAgent",
    "ContradictionSynthesisAgent",
    "KnowledgeExtractionAgent",
    "MemoryCreationAgent",
    "PlotThreadDetectionAgent",
    "RelationshipAnalysisAgent",
    "ResponseAnalyzerAgent",
    "TimeTrackingAgent",
]
