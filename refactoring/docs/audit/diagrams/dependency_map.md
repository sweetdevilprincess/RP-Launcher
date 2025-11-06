# Dependency Map

## High-Level Module Dependencies

```
┌──────────────────────────────────────────────────────────────────┐
│                     DEPENDENCY FLOW                              │
└──────────────────────────────────────────────────────────────────┘

presentation/tui/
├── presentation/bridge/bridge_service.py  (9 deps)
├── infrastructure/ipc/ipc_channel.py      (5 deps)
├── infrastructure/logging/                (2 deps)
└── shared/models.py                       (3 deps)

presentation/bridge/bridge_service.py
├── automation/services/automation_service.py  (8 deps)
├── domain/entities/entity_service.py          (13 deps)
├── domain/sessions/service.py                 (deps)
├── infrastructure/llm/                        (7 deps)
├── infrastructure/config/config_loader.py     (7 deps)
└── infrastructure/filesystem/file_manager.py  (deps)

automation/services/automation_service.py
├── automation/services/prompt_builder.py       (6 deps)
├── automation/services/agent_runner.py         (5 deps)
├── automation/triggers/coordinator.py          (3 deps)
├── automation/templates/narrative_template_manager.py (8 deps)
├── infrastructure/filesystem/file_access_service.py
└── domain/sessions/service.py

automation/services/agent_coordinator.py
├── automation/services/agent_catalog.py        (3 deps)
├── automation/services/agent_factory.py        (6 deps)
├── automation/services/agent_executor.py      (10 deps)
├── automation/services/agent_formatter.py      (6 deps)
└── infrastructure/logging/agent_logging.py    (deps)

automation/services/agent_executor.py
├── infrastructure/retry/retry_policy.py        (deps)
├── infrastructure/telemetry/performance.py    (deps)
└── concurrent.futures                         (builtin)

automation/triggers/coordinator.py
├── automation/triggers/keyword_evaluator.py    (3 deps)
├── automation/triggers/regex_evaluator.py      (4 deps)
├── automation/triggers/semantic_evaluator.py   (4 deps)
├── automation/triggers/frequency_tracker.py    (5 deps)
└── automation/triggers/registry.py            (8 deps)

automation/templates/narrative_template_manager.py
├── automation/templates/template_cache.py      (5 deps)
├── automation/templates/template_loader.py     (6 deps)
├── automation/templates/template_registry.py   (3 deps)
└── infrastructure/templates/template_renderer.py

domain/entities/entity_service.py
├── domain/entities/entity_repository.py        (8 deps)
├── domain/entities/entity_parser.py            (4 deps)
├── domain/entities/preference_generator.py     (8 deps)
└── infrastructure/filesystem/json_store.py

domain/entities/preference_generator.py
├── infrastructure/llm/base.py                  (protocol)
├── infrastructure/llm/openai_client.py
├── infrastructure/llm/openrouter_client.py
└── infrastructure/llm/semantic_ai_client.py

domain/sessions/service.py
├── domain/sessions/repository.py               (deps)
├── domain/sessions/write_back.py              (deps)
└── infrastructure/filesystem/

infrastructure/config/config_loader.py
├── infrastructure/config/defaults.py           (2 deps)
└── os, json, pathlib                          (builtin)

infrastructure/llm/
├── infrastructure/transports/                  (deps)
├── infrastructure/retry/retry_policy.py       (deps)
└── requests                                   (external)

infrastructure/filesystem/file_access_service.py
├── infrastructure/filesystem/file_manager.py
├── infrastructure/filesystem/loaders/tiered_loader.py
└── infrastructure/filesystem/state_paths.py
```

## Modules by Internal Dependency Count

### High Dependency (5+ internal deps)

| Module | Internal Deps | Functional Area |
|--------|--------------|-----------------|
| `agent_executor.py` | 10 | Agent System |
| `bridge_service.py` | 9 | Bridge Service |
| `automation_service.py` | 8 | Automation |
| `entity_service.py` | 13 | Entity Management |
| `preference_generator.py` | 8 | Entity Management |
| `config_loader.py` | 7 | Configuration |
| `narrative_template_manager.py` | 8 | Template System |

### Medium Dependency (3-4 internal deps)

| Module | Internal Deps | Functional Area |
|--------|--------------|-----------------|
| `agent_coordinator.py` | 11 | Agent System |
| `agent_factory.py` | 6 | Agent System |
| `agent_formatter.py` | 6 | Agent System |
| `prompt_builder.py` | 6 | Automation |
| `trigger/coordinator.py` | 3 | Trigger System |
| `entity_repository.py` | 8 | Entity Management |
| `entity_parser.py` | 4 | Entity Management |

### Low Dependency (0-2 internal deps)

Most modules have low internal dependencies, which is healthy!

## Cross-Layer Dependencies

### ✅ Allowed (Following Architecture Rules)

```
Presentation → Application
  bridge_service.py → automation_service.py

Application → Domain
  automation_service.py → sessions/service.py
  agent_factory.py → entities/entity_service.py

Application → Infrastructure
  agent_executor.py → retry/retry_policy.py
  prompt_builder.py → filesystem/file_manager.py

Domain → Infrastructure
  entity_service.py → filesystem/json_store.py
  preference_generator.py → llm/semantic_ai_client.py

Any → Shared
  All layers can use shared/interfaces, shared/models
```

### ❌ Violations (None Found)

✅ No layer dependency violations detected!

## Circular Dependency Analysis

### Risk Areas

1. **Agent System** - Multiple interdependent components
   - AgentCoordinator depends on Catalog, Factory, Executor, Formatter
   - All are in same package, risk of circular imports
   - **Status:** No circular dependencies found
   - **Why:** Clear hierarchy and interface boundaries

2. **Automation Services** - Complex interdependencies
   - AutomationService → PromptBuilder → FileAccessService
   - AgentRunner → Strategies → AgentCoordinator
   - **Status:** No circular dependencies found
   - **Why:** Proper use of composition over inheritance

3. **File System** - Tiered loading
   - FileAccessService → TieredLoader → FileManager
   - FileManager → WriteQueue
   - **Status:** No circular dependencies found
   - **Why:** Unidirectional dependency flow

### ✅ No Circular Dependencies Detected

The codebase successfully avoids circular dependencies through:
- Proper layering
- Dependency injection
- Protocol/interface abstraction
- Composition over inheritance

## External Dependencies

### Core External Libraries

```
Python Standard Library:
  - pathlib, os, sys
  - json, csv
  - logging
  - concurrent.futures, threading
  - typing, dataclasses
  - re, ast
  - socket

Third-Party Libraries:
  - requests (HTTP client)
  - textual (TUI framework)
  - anthropic (Claude API - assumed)
  - openai (OpenAI API)
  - pytest (testing)
  - ruff (linting)
  - black (formatting)
  - mypy (type checking)
```

### By Functional Area

**LLM Clients:**
- requests
- anthropic
- openai

**TUI Presentation:**
- textual
- rich (via textual)

**Testing:**
- pytest
- pytest-cov
- pytest-asyncio

**Development:**
- ruff
- black
- mypy

## Dependency Health Metrics

### Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| Avg Internal Deps per Module | 1.3 | ✅ Excellent (low coupling) |
| Max Internal Deps | 13 | ⚠️ Monitor (entity_service.py) |
| Modules with 0 Deps | 89/133 | ✅ Excellent (67% self-contained) |
| Modules with 5+ Deps | 8/133 | ✅ Good (6% high coupling) |
| Circular Dependencies | 0 | ✅ Excellent |
| Layer Violations | 0 | ✅ Excellent |

### Recommendations

1. **entity_service.py (13 deps):**
   - Consider extracting LLM preference logic to separate service
   - Repository pattern is appropriate, keep it

2. **agent_coordinator.py (11 deps):**
   - High dependency count is intentional (facade pattern)
   - All dependencies are within same functional area
   - Document facade pattern in code comments

3. **bridge_service.py (9 deps):**
   - Bridge naturally connects many systems
   - Consider extracting message handlers to reduce direct dependencies
   - Current structure is acceptable for bridge role

## Import Analysis Tool

The codebase includes `src/tools/import_audit.py` for automated dependency checking:

**Features:**
- Detects layer boundary violations
- Identifies circular dependencies
- Validates import patterns
- Enforces architecture rules

**Usage:**
```bash
python src/tools/import_audit.py
```

**Recommendation:** Run as part of CI/CD pipeline to prevent violations.

## Dependency Management Best Practices

### Current Strengths

1. ✅ **Clear Layering** - Dependencies flow downward
2. ✅ **Protocol Abstraction** - Interfaces reduce coupling
3. ✅ **Dependency Injection** - Factory pattern for flexibility
4. ✅ **Repository Pattern** - Data access abstraction
5. ✅ **No Circular Dependencies** - Clean import structure

### Areas for Improvement

1. **Documentation** - Add dependency diagrams to module READMEs
2. **Testing** - Test high-dependency modules thoroughly
3. **Monitoring** - Track dependency metrics over time

---

*Generated from component inventory import analysis*
*Total modules: 133, Average internal dependencies: 1.3*
