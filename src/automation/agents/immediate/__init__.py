"""
Immediate Agents

These agents run before Response N+1 (user sees this latency).
Total execution time: ~5 seconds (user perceives this delay)

Agents:
1. QuickEntityAnalysisAgent - Identify Tier 1/2/3 entities (~3s)
2. FactExtractionAgent - Extract facts for Tier 2 entities (~2s)
3. MemoryExtractionAgent - Get relevant memories (parallel, ~3s)
4. PlotThreadExtractionAgent - Extract relevant threads (parallel, ~3s)

Note: Agents 3 and 4 run in parallel with others, so total time is ~5s not ~11s.
"""

from src.automation.agents.immediate.quick_entity_analysis import (
    QuickEntityAnalysisAgent,
    analyze_entities
)
from src.automation.agents.immediate.fact_extraction import (
    FactExtractionAgent,
    extract_facts
)
from src.automation.agents.immediate.memory_extraction import (
    MemoryExtractionAgent,
    extract_memories
)
from src.automation.agents.immediate.plot_thread_extraction import (
    PlotThreadExtractionAgent,
    extract_plot_threads
)

__all__ = [
    "QuickEntityAnalysisAgent",
    "FactExtractionAgent",
    "MemoryExtractionAgent",
    "PlotThreadExtractionAgent",
    "analyze_entities",
    "extract_facts",
    "extract_memories",
    "extract_plot_threads",
]
