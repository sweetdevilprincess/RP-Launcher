# Overlap Analysis Visualization

## Known Overlaps by Severity

```
🔴 HIGH SEVERITY (2)
│
├── 1. Session Management Overlap
│   ├── automation/services/session_service.py (31 LOC) - NoOpSessionService PLACEHOLDER
│   └── domain/sessions/service.py (real SessionService) - NOT INTEGRATED
│
└── 2. TUI Mockups Not Integrated
    ├── tui/components/trigger_editor_enhanced_mockup.py (698 LOC)
    ├── tui/components/template_editor_mockup.py (470 LOC)
    └── tui/components/trigger_editor_mockup.py (older version)

🟡 MEDIUM SEVERITY (1)
│
└── 3. Agent Coordination Naming
    ├── automation/agents/registry.py (strategy-level)
    ├── automation/services/agent_runner.py (strategy-level)
    ├── automation/services/agent_catalog.py (individual-level)
    ├── automation/services/agent_coordinator.py (individual-level)
    └── automation/services/agent_executor.py (individual-level)

    NOTE: This is INTENTIONAL dual architecture, not actual overlap

🟢 LOW SEVERITY (3)
│
├── 4. Template Management Multi-Layer
│   ├── automation/templates/ (application layer - 4 modules, orchestration)
│   └── infrastructure/templates/ (infrastructure layer - 2 modules, rendering)
│
├── 5. Logging Multiple Implementations
│   ├── shared/logging.py (SimpleLogger, PythonLogger - general purpose)
│   ├── infrastructure/logging/python_logging.py (PythonLoggingService - specialized)
│   └── infrastructure/logging/agent_logging.py (AgentLogger - domain-specific)
│
└── 6. File Management Multi-Layer
    ├── infrastructure/filesystem/file_manager.py (low-level operations)
    └── infrastructure/filesystem/file_access_service.py (tiered loading orchestration)
```

## Overlap Heatmap by Functional Area

```
Functional Area            | Modules | Potential Overlaps | Severity
---------------------------|---------|--------------------|---------
Agent System               |   11    |        1           |   🟡
Session Management         |    6    |        1           |   🔴
Template System            |    8    |        1           |   🟢
Logging & Telemetry        |    7    |        1           |   🟢
File System                |    8    |        1           |   🟢
TUI Presentation           |   19    |        1           |   🔴
Other Areas                |   74    |        0           |   ✅
```

## Visual Map of Overlapping Components

### 1. Session Management Overlap 🔴

```
┌───────────────────────────────────────────────────────────┐
│          AUTOMATION LAYER (Application)                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  automation/services/session_service.py             │ │
│  │  ┌───────────────────────────────────────────────┐  │ │
│  │  │  class NoOpSessionService                     │  │ │
│  │  │  • Placeholder implementation                 │  │ │
│  │  │  • Returns empty responses                    │  │ │
│  │  │  • 31 LOC                                     │  │ │
│  │  │  STATUS: NEEDS REPLACEMENT                    │  │ │
│  │  └───────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
                           ❌ NOT CONNECTED ❌
┌───────────────────────────────────────────────────────────┐
│             DOMAIN LAYER (Business Logic)                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  domain/sessions/service.py                         │ │
│  │  ┌───────────────────────────────────────────────┐  │ │
│  │  │  class SessionService                         │  │ │
│  │  │  • Full implementation                        │  │ │
│  │  │  • State management                           │  │ │
│  │  │  • Checkpoint support                         │  │ │
│  │  │  STATUS: READY BUT NOT INTEGRATED             │  │ │
│  │  └───────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘

RECOMMENDATION: Connect these layers via adapter/wrapper
```

### 2. TUI Mockups Overlap 🔴

```
┌──────────────────────────────────────────────────────────────┐
│              MAIN TUI APPLICATION (Integrated)               │
│  ✅ app.py                                                   │
│  ✅ chat_display.py                                          │
│  ✅ context_panel.py                                         │
│  ✅ character_editor.py                                      │
│  ✅ provider_selector.py                                     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│           MOCKUPS (Not Integrated - WIP)                     │
│  ⏳ trigger_editor_enhanced_mockup.py (698 LOC)             │
│     ├── Enhanced UI components                               │
│     ├── Pattern editing                                      │
│     ├── Live preview                                         │
│     └── STATUS: Ready for extraction                         │
│                                                              │
│  ⏳ template_editor_mockup.py (470 LOC)                     │
│     ├── Template CRUD operations                             │
│     ├── Genre selection                                      │
│     ├── Variable preview                                     │
│     └── STATUS: Ready for extraction                         │
│                                                              │
│  📦 trigger_editor_mockup.py (older version)                │
│     └── STATUS: Can be deprecated after enhanced version    │
└──────────────────────────────────────────────────────────────┘

INTEGRATION PATH:
  1. Extract components from mockups
  2. Add to tui/components/
  3. Add IPC message handlers
  4. Wire into main app navigation
  5. Add integration tests
  6. Remove mockup files
```

### 3. Agent Coordination Naming 🟡

```
┌────────────────────────────────────────────────────────────┐
│          STRATEGY LEVEL (Workstream D)                     │
│                                                             │
│  automation/agents/registry.py                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ AgentRegistry                                        │ │
│  │ • Loads STRATEGY configurations                      │ │
│  │ • Registers ImmediateAgentStrategy                   │ │
│  │ • Registers BackgroundAgentStrategy                  │ │
│  └──────────────────────────────────────────────────────┘ │
│                            │                               │
│                            ▼                               │
│  automation/services/agent_runner.py                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ AgentRunner                                          │ │
│  │ • Executes STRATEGIES sequentially                   │ │
│  │ • Passes context to each strategy                    │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
                            │
                INVOKES     │
                            ▼
┌────────────────────────────────────────────────────────────┐
│        INDIVIDUAL AGENT LEVEL (Workstream E)               │
│                                                             │
│  automation/services/agent_coordinator.py                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ AgentCoordinator (FACADE)                            │ │
│  │ • Orchestrates INDIVIDUAL agents                     │ │
│  │ • Catalog → Factory → Executor → Formatter           │ │
│  └──────────────────────────────────────────────────────┘ │
│          │           │           │           │             │
│          ▼           ▼           ▼           ▼             │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Catalog │  │ Factory  │  │ Executor │  │ Formatter│  │
│  │ (153)   │  │ (177)    │  │ (372)    │  │ (209)    │  │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────┘

NOTE: This appears to be overlap but is INTENTIONAL architecture:
  - Two different levels of abstraction
  - Strategy level vs individual agent level
  - Clear separation of concerns

RECOMMENDATION: Add documentation clarifying the dual architecture
```

### 4. Template Management Multi-Layer 🟢

```
┌────────────────────────────────────────────────────────────┐
│         APPLICATION LAYER (High-Level Orchestration)       │
│                                                             │
│  automation/templates/                                     │
│  ├── template_cache.py (LRU caching, statistics)          │
│  ├── template_loader.py (JSON loading, validation)        │
│  ├── template_registry.py (discovery, normalization)      │
│  └── narrative_template_manager.py (4 modes)              │
│                                                             │
│  RESPONSIBILITY: Template discovery, loading, caching      │
└────────────────────────────────────────────────────────────┘
                            │
                 DELEGATES  │
                            ▼
┌────────────────────────────────────────────────────────────┐
│      INFRASTRUCTURE LAYER (Low-Level Implementation)       │
│                                                             │
│  infrastructure/templates/                                 │
│  ├── template_renderer.py (variable interpolation)        │
│  └── state_service.py (state template service)            │
│                                                             │
│  RESPONSIBILITY: Template rendering, variable substitution │
└────────────────────────────────────────────────────────────┘

NOTE: This is PROPER layer separation, not actual overlap:
  - Application: What templates to load and when
  - Infrastructure: How to render templates

RECOMMENDATION: Document the separation in architecture docs
```

### 5. Logging Multiple Implementations 🟢

```
┌────────────────────────────────────────────────────────────┐
│                  SHARED LAYER (General Purpose)            │
│                                                             │
│  shared/logging.py                                         │
│  ├── SimpleLogger (print-based, development)               │
│  └── PythonLogger (stdlib logging wrapper)                 │
│                                                             │
│  USE CASE: General application logging                     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│          INFRASTRUCTURE LAYER (Specialized Services)       │
│                                                             │
│  infrastructure/logging/python_logging.py                  │
│  └── PythonLoggingService (service interface)             │
│                                                             │
│  USE CASE: Service-level logging with configuration        │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│       INFRASTRUCTURE LAYER (Domain-Specific Logging)       │
│                                                             │
│  infrastructure/logging/agent_logging.py                   │
│  ├── AgentLogger (agent-specific context)                  │
│  └── AgentCoordinatorLogger (coordination logging)         │
│                                                             │
│  USE CASE: Agent system logging with context               │
└────────────────────────────────────────────────────────────┘

NOTE: Multiple implementations serve DIFFERENT purposes:
  - Shared: Quick, simple logging
  - PythonLoggingService: Configurable service logging
  - AgentLogger: Domain-specific with context

RECOMMENDATION: Document when to use each implementation
```

### 6. File Management Multi-Layer 🟢

```
┌────────────────────────────────────────────────────────────┐
│        HIGH-LEVEL (Tiered Loading Orchestration)           │
│                                                             │
│  infrastructure/filesystem/file_access_service.py          │
│  ├── Tier 1: Always loaded (core files)                   │
│  ├── Tier 2: Frequency-based (guidelines)                  │
│  └── Tier 3: Trigger-based (on-demand)                     │
│                                                             │
│  RESPONSIBILITY: WHEN to load files (50-70% I/O reduction) │
└────────────────────────────────────────────────────────────┘
                            │
                   USES     │
                            ▼
┌────────────────────────────────────────────────────────────┐
│              LOW-LEVEL (File Operations)                   │
│                                                             │
│  infrastructure/filesystem/file_manager.py                 │
│  ├── read_file()                                           │
│  ├── write_file()                                          │
│  ├── file_exists()                                         │
│  └── list_files()                                          │
│                                                             │
│  RESPONSIBILITY: HOW to access files (CRUD operations)     │
└────────────────────────────────────────────────────────────┘

NOTE: Clear separation of concerns:
  - file_access_service: Business logic (tiered loading)
  - file_manager: Technical implementation (file I/O)

RECOMMENDATION: This is proper layering, maintain as-is
```

## Consolidation Opportunities Matrix

| Area | Current State | Consolidation Possible? | Recommended Action |
|------|---------------|------------------------|-------------------|
| Session Management | 2 implementations | ❌ No - need integration | Integrate NoOp with real service |
| TUI Mockups | 3 mockup files | ✅ Yes | Extract and integrate components |
| Agent Coordination | 5 related components | ❌ No - intentional design | Document dual architecture |
| Template Management | 2 layers (6 modules) | ❌ No - proper layering | Document layer separation |
| Logging | 3 implementations | ❌ No - different purposes | Create usage guide |
| File Management | 2 layers | ❌ No - proper layering | Maintain as-is |

## Summary

### Actual Overlaps Requiring Action: 2

1. **Session Management** - Replace NoOpSessionService
2. **TUI Mockups** - Integrate editor components

### Apparent Overlaps (Actually Proper Design): 4

3. **Agent Coordination** - Intentional dual architecture
4. **Template Management** - Proper layer separation
5. **Logging** - Different use cases
6. **File Management** - Proper layer separation

---

*Analysis based on comprehensive codebase audit*
*133 modules analyzed, 6 overlap areas identified*
