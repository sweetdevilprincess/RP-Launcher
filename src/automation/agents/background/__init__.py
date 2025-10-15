"""
Background Agents

These agents run after Response N while the user types Message N+1.
Total execution time: ~30 seconds (hidden from user, zero perceived latency)

Agents:
1. ResponseAnalyzerAgent - Scene classification, pacing, variety (~15s)
2. MemoryCreationAgent - Extract memorable moments (~5s)
3. RelationshipAnalysisAgent - Preference matching, tier tracking (~5s)
4. PlotThreadDetectionAgent - New/mentioned/resolved threads (~5s)
5. KnowledgeExtractionAgent - World-building facts (~3s)
6. ContradictionDetectionAgent - Optional fact-checking (~2s)
"""

from src.automation.agents.background.response_analyzer import (
    ResponseAnalyzerAgent,
    analyze_response
)
from src.automation.agents.background.memory_creation import (
    MemoryCreationAgent,
    extract_memories
)
from src.automation.agents.background.relationship_analysis import (
    RelationshipAnalysisAgent,
    analyze_relationships
)
from src.automation.agents.background.plot_thread_detection import (
    PlotThreadDetectionAgent,
    detect_plot_threads
)
from src.automation.agents.background.knowledge_extraction import (
    KnowledgeExtractionAgent,
    extract_knowledge
)
from src.automation.agents.background.contradiction_detection import (
    ContradictionDetectionAgent,
    detect_contradictions
)

__all__ = [
    "ResponseAnalyzerAgent",
    "MemoryCreationAgent",
    "RelationshipAnalysisAgent",
    "PlotThreadDetectionAgent",
    "KnowledgeExtractionAgent",
    "ContradictionDetectionAgent",
    "analyze_response",
    "extract_memories",
    "analyze_relationships",
    "detect_plot_threads",
    "extract_knowledge",
    "detect_contradictions",
]
