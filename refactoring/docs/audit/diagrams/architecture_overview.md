# Architecture Overview Diagram

## Layered Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                            │
│  ┌──────────────────────┐         ┌──────────────────────┐        │
│  │   TUI Components     │◄────────┤   Bridge Service     │        │
│  │   - Main App         │   IPC   │   - Message Routing  │        │
│  │   - Chat Display     │ Socket  │   - State Management │        │
│  │   - Context Panel    │         │   - Service Coord    │        │
│  │   - Character Editor │         │   (514 LOC)          │        │
│  │   - Provider Select  │         └──────────────────────┘        │
│  │   (19 modules)       │                                          │
│  │   (2,677 LOC)        │                                          │
│  └──────────────────────┘                                          │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │   AUTOMATION ORCHESTRATION                                   │ │
│  │   - AutomationService (6-step lifecycle)                     │ │
│  │   - PromptBuilder (modular assembly)                         │ │
│  │   - Orchestrator v2 (facade)                                 │ │
│  │   (5 modules, 421 LOC)                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                 │                                   │
│          ┌──────────────────────┼────────────────────┐            │
│          │                      │                    │            │
│          ▼                      ▼                    ▼            │
│  ┌──────────────┐      ┌──────────────┐    ┌──────────────┐     │
│  │AGENT SYSTEM  │      │TRIGGER SYSTEM│    │TEMPLATE SYS  │     │
│  │- Coordinator │      │- Evaluators  │    │- Cache/Load  │     │
│  │- Executor    │      │- Frequency   │    │- Registry    │     │
│  │- Formatter   │      │- Patterns    │    │- Narrative   │     │
│  │- Catalog     │      │(9 modules)   │    │(8 modules)   │     │
│  │- Factory     │      │(1,065 LOC)   │    │(775 LOC)     │     │
│  │(11 modules)  │      └──────────────┘    └──────────────┘     │
│  │(2,207 LOC)   │                                                 │
│  └──────────────┘                                                 │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                                │
│  ┌──────────────────────┐         ┌──────────────────────┐        │
│  │  ENTITY MANAGEMENT   │         │ SESSION MANAGEMENT   │        │
│  │  - EntityService     │         │ - SessionService     │        │
│  │  - EntityRepository  │         │ - SessionRepository  │        │
│  │  - EntityParser      │         │ - WriteBack          │        │
│  │  - Preference Gen    │         │ - Models             │        │
│  │  (7 modules)         │         │ (6 modules)          │        │
│  │  (824 LOC)           │         │ (954 LOC)            │        │
│  └──────────────────────┘         └──────────────────────┘        │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ LLM CLIENTS  │  │ FILE SYSTEM  │  │CONFIGURATION │            │
│  │ - Providers  │  │ - Tiered     │  │ - 4-Layer    │            │
│  │ - Transport  │  │ - FileManager│  │ - Validation │            │
│  │ - Retry      │  │ - WriteQueue │  │ - Defaults   │            │
│  │ (16 modules) │  │ (8 modules)  │  │ (3 modules)  │            │
│  │ (2,182 LOC)  │  │ (921 LOC)    │  │ (1,106 LOC)  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │LOGGING/TELEM │  │IPC CHANNEL   │  │TEMPLATE INFRA│            │
│  │ - PythonLog  │  │ - Socket     │  │ - Renderer   │            │
│  │ - AgentLog   │  │ - Protocol   │  │ - StateServ  │            │
│  │ - Performance│  │ - Messages   │  │              │            │
│  │ (7 modules)  │  │ (5 modules)  │  │ (2 modules)  │            │
│  │ (799 LOC)    │  │ (860 LOC)    │  │ (included)   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                       SHARED / CROSS-CUTTING                       │
│  - Interfaces & Protocols                                          │
│  - Shared Models & Enums                                           │
│  - Common Logging Utilities                                        │
│  (8 modules, 251 LOC)                                              │
└────────────────────────────────────────────────────────────────────┘
```

## Statistics by Layer

| Layer         | Modules | LOC   | Key Responsibilities                    |
|---------------|---------|-------|-----------------------------------------|
| Presentation  | 21      | 3,191 | User interface, IPC, bridge service     |
| Application   | 33      | 4,468 | Orchestration, agents, triggers, templates |
| Domain        | 13      | 1,778 | Business logic, entities, sessions      |
| Infrastructure| 41      | 6,868 | Technical services, LLM, files, config  |
| Shared        | 8       | 251   | Cross-cutting concerns, protocols       |
| Tools         | 2       | 104   | Development tooling                     |
| Other/WIP     | 15      | 1,508 | Uncategorized, experimental             |

**Total:** 133 modules, 17,168 LOC

## Dependency Flow Rules

```
✅ ALLOWED Dependencies:
   Presentation → Application → Domain → Infrastructure
   Application → Domain → Infrastructure
   Domain → Infrastructure
   Any Layer → Shared

❌ FORBIDDEN Dependencies:
   Infrastructure ↛ Domain
   Infrastructure ↛ Application
   Domain ↛ Application
   Any Layer ↛ Presentation
```

## Key Design Patterns

1. **Layered Architecture** - Clear separation of concerns
2. **Dependency Injection** - Factory pattern for service creation
3. **Repository Pattern** - Entity and session repositories
4. **Strategy Pattern** - Agent execution strategies
5. **Facade Pattern** - AgentCoordinator, AutomationService
6. **Registry Pattern** - Agent catalog, trigger registry, template registry
7. **Observer Pattern** - IPC message handling

## Workstream Ownership Map

```
┌─────────────────────────────────────────────────────┐
│ Workstream A: Architecture & Boundaries            │
│ • Shared interfaces, protocols, base architecture   │
│ • 8 modules in shared/                              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream B/G: Session Management                 │
│ • Session domain & file system                      │
│ • 14 modules (domain/sessions + infrastructure/fs) │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream C: Entity Domain                        │
│ • Entity management, parsing, repositories          │
│ • 7 modules in domain/entities/                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream D: Automation Pipeline                  │
│ • Orchestration, prompt building                    │
│ • 5 modules in automation/orchestrator & services   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream E: Agent System                         │
│ • Agent coordination, execution, formatting         │
│ • 11 modules in automation/agents & services        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream F: Triggers & Templates                 │
│ • Trigger evaluation, template management           │
│ • 17 modules across automation/triggers & templates │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream H: Logging & Telemetry                  │
│ • Performance monitoring, retry policies            │
│ • 7 modules in infrastructure/logging & telemetry   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream I: LLM Clients & Transport              │
│ • Multi-provider LLM support, transport abstraction │
│ • 16 modules in infrastructure/llm & transports     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream J: Configuration                        │
│ • 4-layer config system, validation                 │
│ • 3 modules in infrastructure/config/               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream K: Testing & Tooling                    │
│ • Development tools, testing infrastructure         │
│ • 2 modules + 37 test files                         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workstream M: TUI/Bridge Integration               │
│ • Terminal UI, IPC, bridge service                  │
│ • 21 modules in presentation/tui & bridge           │
│ • STATUS: IN PROGRESS (mockups need integration)   │
└─────────────────────────────────────────────────────┘
```

## Data Flow

```
User Input (TUI)
    │
    ▼
IPC Channel (Socket)
    │
    ▼
Bridge Service
    │
    ▼
Automation Service (6-step lifecycle)
    │
    ├──► Step 1: File Access (Tiered Loading)
    │    └──► tier1 (always) + tier2 (frequency) + tier3 (triggers)
    │
    ├──► Step 2: Prompt Building
    │    └──► Sections: context + entities + history + instructions
    │
    ├──► Step 3: Trigger Evaluation
    │    └──► Keyword | Regex | Semantic
    │
    ├──► Step 4: Agent Execution (Immediate)
    │    └──► QuickEntityAnalysis, FactExtraction, MemoryExtraction
    │
    ├──► Step 5: LLM Invocation
    │    └──► Provider: Claude | OpenAI | OpenRouter | DeepSeek
    │
    └──► Step 6: Agent Execution (Background)
         └──► ResponseAnalyzer, MemoryCreation, RelationshipAnalysis
```

---

*Diagram generated from component inventory analysis*
*Total components: 133 modules, 17,168 LOC*
