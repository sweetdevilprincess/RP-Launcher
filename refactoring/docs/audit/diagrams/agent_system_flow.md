# Agent System Flow Diagram

## Overview

The agent system has a **dual architecture**:
- **Strategy-Level** (Workstream D): Manages agent strategies as a whole
- **Individual-Level** (Workstream E): Manages individual agent instances

## Agent System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT SYSTEM LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STRATEGY LEVEL (Workstream D)                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  AgentRegistry (146 LOC)                               │   │
│  │  • Loads agent strategy configurations                 │   │
│  │  • Registers ImmediateAgentStrategy                    │   │
│  │  • Registers BackgroundAgentStrategy                   │   │
│  │  • Registers FallbackTriggerStrategy                   │   │
│  └────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  AgentRunner (81 LOC)                                  │   │
│  │  • Executes strategies sequentially                    │   │
│  │  • Passes context to each strategy                     │   │
│  │  • Aggregates results                                  │   │
│  └────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
├────────────────────────────┼────────────────────────────────────┤
│                            │                                    │
│  INDIVIDUAL LEVEL (Workstream E)                               │
│                            ▼                                    │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  AgentCoordinator (313 LOC) - FACADE                   │   │
│  │  • High-level orchestration                            │   │
│  │  • Coordinates: Catalog → Factory → Executor → Format │   │
│  └────┬──────┬──────┬──────┬──────────────────────────────┘   │
│       │      │      │      │                                   │
│       ▼      ▼      ▼      ▼                                   │
│  ┌─────┐ ┌──────┐ ┌──────┐ ┌─────────┐                       │
│  │Catl │ │Factry│ │Exectr│ │Formattr │                       │
│  │153  │ │177   │ │372   │ │209 LOC  │                       │
│  │LOC  │ │LOC   │ │LOC   │ │         │                       │
│  └─────┘ └──────┘ └──────┘ └─────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Execution Flow: Immediate Agents

```
User Input
    │
    ▼
AutomationService
    │
    ▼
AgentRunner.run_agents()
    │
    ├──► Load ImmediateAgentStrategy
    │    │
    │    ▼
    │    ImmediateAgentStrategy.execute()
    │    │
    │    ▼
    │    AgentCoordinator.run_agents(mode='immediate')
    │    │
    │    ├──► 1. AgentCatalog.discover_agents(mode='immediate')
    │    │    └──► Returns: [QuickEntityAnalysis, FactExtraction, MemoryExtraction]
    │    │
    │    ├──► 2. AgentFactory.create_agents(metadata_list)
    │    │    ├──► For each agent:
    │    │    │    • Check conditional creation logic
    │    │    │    • Map parameters from context
    │    │    │    • Instantiate agent instance
    │    │    └──► Returns: [agent1, agent2, agent3]
    │    │
    │    ├──► 3. AgentExecutor.execute_concurrent(agents)
    │    │    ├──► Thread Pool: 4 workers
    │    │    ├──► Timeout: 10 seconds per agent
    │    │    ├──► Retry Policy: 2 attempts, 0.5s delay
    │    │    ├──► Concurrent execution ⚡
    │    │    └──► Returns: [result1, result2, result3]
    │    │
    │    └──► 4. AgentFormatter.format(results, mode='prompt_injection')
    │         └──► Returns: formatted_context_string
    │
    └──► Returns to AutomationService
         └──► Injected into prompt
              └──► Sent to LLM
```

**Latency:** ~3 seconds typical (blocking user experience)

## Execution Flow: Background Agents

```
LLM Response Received
    │
    ▼
AutomationService (post-response)
    │
    ▼
AgentRunner.run_agents()
    │
    ├──► Load BackgroundAgentStrategy
    │    │
    │    ▼
    │    BackgroundAgentStrategy.execute()
    │    │
    │    ▼
    │    AgentCoordinator.run_agents(mode='background')
    │    │
    │    ├──► 1. AgentCatalog.discover_agents(mode='background')
    │    │    └──► Returns: [ResponseAnalyzer, MemoryCreation,
    │    │                   RelationshipAnalysis, PlotThreadDetection,
    │    │                   KnowledgeExtraction, ContradictionDetection]
    │    │
    │    ├──► 2. AgentFactory.create_agents(metadata_list)
    │    │    └──► Instantiate 6 background agents
    │    │
    │    ├──► 3. AgentExecutor.execute_concurrent(agents)
    │    │    ├──► Thread Pool: 6 workers
    │    │    ├──► Timeout: 60 seconds per agent
    │    │    ├──► Retry Policy: 3 attempts, exponential backoff
    │    │    │    • 2s → 4s → 8s (max 60s)
    │    │    │    • 20% jitter
    │    │    ├──► Concurrent execution ⚡
    │    │    └──► Returns: [result1, result2, ..., result6]
    │    │
    │    └──► 4. AgentFormatter.format(results, mode='json_cache')
    │         └──► Writes to cache files
    │
    └──► User sees response immediately (non-blocking)
         └──► Analysis happens in background
```

**Latency:** Hidden from user, happens post-response

## Fallback Trigger Strategy Flow

```
AutomationService
    │
    ▼
AgentRunner.run_agents()
    │
    ├──► Load FallbackTriggerStrategy
    │    │
    │    ▼
    │    FallbackTriggerStrategy.execute()
    │    │
    │    ├──► Check if any agents executed
    │    │
    │    ├──► IF NO AGENTS EXECUTED:
    │    │    └──► Execute legacy trigger system
    │    │         └──► Load tier3 files
    │    │
    │    └──► IF AGENTS EXECUTED:
    │         └──► Skip (agents already handled context)
    │
    └──► Returns to AutomationService
```

**Purpose:** Backward compatibility with legacy trigger-based file loading

## Agent Catalog Structure

```json
{
  "agents": [
    {
      "name": "QuickEntityAnalysis",
      "mode": "immediate",
      "priority": 1,
      "enabled": true,
      "conditional_creation": {
        "requires": ["entities_loaded"],
        "skip_if": ["response_count < 3"]
      },
      "parameters": {
        "entity_types": ["character", "location"],
        "analysis_depth": "quick"
      }
    },
    {
      "name": "MemoryCreation",
      "mode": "background",
      "priority": 2,
      "enabled": true,
      "conditional_creation": {
        "requires": ["llm_response"],
        "skip_if": ["memory_disabled"]
      }
    }
  ]
}
```

## Thread Pool Configuration

### Immediate Agents
- **Pool Size:** 4 workers
- **Timeout:** 10 seconds (global)
- **Retry:** 2 attempts, 0.5s fixed delay
- **Jitter:** None
- **Target Latency:** <5 seconds total

### Background Agents
- **Pool Size:** 6 workers
- **Timeout:** 60 seconds (global)
- **Retry:** 3 attempts, exponential backoff
  - Attempt 1: 2 seconds
  - Attempt 2: 4 seconds
  - Attempt 3: 8 seconds
- **Jitter:** 20%
- **Target Latency:** Not critical (hidden from user)

## Result Formatting Modes

### 1. Prompt Injection (Immediate Agents)
```python
# Output: String injected into LLM prompt
format = "prompt_injection"
result = """
[Agent Results]
- QuickEntityAnalysis: Character Aurora is active
- FactExtraction: 3 new facts identified
- MemoryExtraction: 2 relevant memories found
"""
```

### 2. JSON Cache (Background Agents)
```python
# Output: Written to cache files
format = "json_cache"
result = {
    "ResponseAnalyzer": {
        "sentiment": "positive",
        "entities_mentioned": ["Aurora", "Celestia"],
        "cache_file": "cache/response_analysis_123.json"
    },
    "MemoryCreation": {
        "memories_created": 2,
        "cache_file": "cache/memories_123.json"
    }
}
```

## Component Responsibilities

| Component | LOC | Responsibility |
|-----------|-----|----------------|
| **AgentRegistry** | 146 | Load strategy configurations |
| **AgentRunner** | 81 | Execute strategies sequentially |
| **ImmediateAgentStrategy** | 297 | Immediate agent logic |
| **BackgroundAgentStrategy** | 229 | Background agent logic |
| **FallbackTriggerStrategy** | 219 | Legacy compatibility |
| **AgentCatalog** | 153 | Agent discovery & metadata |
| **AgentFactory** | 177 | Agent instantiation |
| **AgentExecutor** | 372 | Concurrent execution + retry |
| **AgentFormatter** | 209 | Result formatting |
| **AgentCoordinator** | 313 | Facade orchestrating pipeline |

**Total:** 11 modules, 2,207 LOC

## Key Design Decisions

### Why Two-Tier Architecture?

**Strategy Level (D):**
- Manages collections of agents
- Defines execution policies (immediate vs background)
- Provides extensibility for new agent types

**Individual Level (E):**
- Manages specific agent instances
- Handles concurrent execution
- Provides fine-grained control

**Benefit:** Separation allows independent evolution of strategy policies and individual agent execution logic.

### Why Separate Executor and Coordinator?

**AgentExecutor:**
- Low-level: Thread pools, timeouts, retry logic
- Reusable across different contexts

**AgentCoordinator:**
- High-level: Orchestrates catalog → factory → executor → formatter
- Business logic for agent pipeline

**Benefit:** Single Responsibility Principle - executor focuses on concurrent execution, coordinator focuses on orchestration.

### Why Conditional Agent Creation?

Allows agents to be:
- Enabled/disabled via configuration
- Created only when preconditions are met
- Skipped based on context (e.g., response count < 3)

**Benefit:** Flexibility and performance optimization.

## Test Coverage Analysis

**Current:** 0% (11 modules, 0 have tests)

**Recommended Test Structure:**
```
tests/automation/agents/
  test_background_agent_strategy.py      (NEW)
  test_immediate_agent_strategy.py       (NEW)
  test_fallback_trigger_strategy.py      (NEW)
  test_registry.py                       (NEW)

tests/automation/services/
  test_agent_catalog.py                  (NEW)
  test_agent_coordinator.py              (NEW)
  test_agent_executor.py                 (NEW)
  test_agent_factory.py                  (NEW)
  test_agent_formatter.py                (NEW)
  test_agent_runner.py                   (NEW)
```

**Priority:** HIGH - Core system with no test coverage

---

*Diagram generated from agent system analysis*
*Components analyzed: 11 modules, 2,207 LOC*
