# Infrastructure Layer Analysis

**Layer:** Infrastructure (`refactoring/src/infrastructure/`)
**Purpose:** Low-level services and utilities that other layers depend on
**File Count:** 51 Python files
**Analysis Date:** Phase 2.1

---

## Layer Organization

### Subsystems (9 total)

1. **config/** - Configuration loading and management
2. **filesystem/** - File I/O, paths, stores, write queue
3. **ipc/** - Inter-process communication (socket-based)
4. **llm/** - LLM client implementations and registry
5. **logging/** - Logging services and adapters
6. **retry/** - Retry policies for resilient operations
7. **rp_initialization/** - RP directory creation and setup
8. **sessions/** - Session state management
9. **telemetry/** - Performance monitoring
10. **templates/** - Template services (state, character, schema)
11. **transports/** - HTTP transport abstractions

---

## Complete File Inventory

### 1. Configuration Subsystem (4 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `config/__init__.py` | ? | Exports | - |
| `config/config_loader.py` | ? | Load/validate RP config | BridgeService, Factory |
| `config/defaults.py` | ? | Default config values | ConfigLoader |

**Key Components:**
- ConfigLoader class
- RP directory validation
- Config schema enforcement

**Dependencies:** None (leaf node)

**Used By:**
- `BridgeService._load_configuration()` (Phase 1.2)
- `create_automation_service()` factory (Phase 1.5)

---

### 2. Filesystem Subsystem (9 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `filesystem/__init__.py` | ? | Exports | - |
| `filesystem/author_notes_loader.py` | ? | Load AUTHOR'S_NOTES.md | PromptBuilder |
| `filesystem/file_access_service.py` | ? | High-level file access API | AutomationService |
| `filesystem/file_manager.py` | ? | File operation coordinator | FileAccessService |
| `filesystem/json_store.py` | ? | JSON file persistence | FileManager |
| `filesystem/loaders/tiered_loader.py` | ? | Tiered entity loading | FileAccessService |
| `filesystem/markdown_store.py` | ? | Markdown file persistence | FileManager |
| `filesystem/state_paths.py` | ? | Path constants/utilities | Multiple services |
| `filesystem/write_queue.py` | ? | Debounced file writes | FileManager |

**Key Components:**
- **StatePaths** - Path computation and validation
- **FileManager** - Coordinates JSON/Markdown stores and write queue
- **FileAccessService** - High-level API for automation system
- **TieredFileLoader** - Entity loading with performance tiers
- **JsonStore** - JSON serialization with validation
- **MarkdownStore** - Markdown file operations
- **FSWriteQueue** - Debounced batched writes (prevents file thrashing)

**Dependencies:**
- write_queue (leaf)
- json_store, markdown_store (depend on write_queue)
- file_manager (depends on stores)
- file_access_service (depends on file_manager, tiered_loader)

**Used By:**
- Automation factory (creates FileAccessService)
- TUI app (creates StatePaths for session repo)
- BridgeService (creates StatePaths for repos)

**CRITICAL FILES:**
- `state_paths.py` - Used everywhere for path resolution
- `write_queue.py` - Prevents file corruption from rapid writes
- `file_manager.py` - Central file operation coordinator

---

### 3. IPC Subsystem (5 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `ipc/__init__.py` | ? | Exports | - |
| `ipc/ipc_channel.py` | ? | Abstract IPC channel | SocketServer/Client |
| `ipc/ipc_protocol.py` | ? | IPC message protocol | All IPC components |
| `ipc/socket_client.py` | ? | Client-side socket IPC | TUI app |
| `ipc/socket_server.py` | ? | Server-side socket IPC | BridgeService |

**Key Components:**
- **IPCMessageType** enum - Message type constants (PING, SEND_MESSAGE, etc.)
- **IPCRequest** - Request message structure
- **IPCResponse** - Response message structure
- **SocketServer** - Listens on port, handles requests
- **SocketClient** - Connects to server, sends requests

**Protocol:**
- JSON-based message serialization
- Request/response pattern
- Streaming support for LLM responses
- Timeout handling
- Connection retry logic

**Dependencies:**
- ipc_protocol (defines message structures)
- socket_server/client (implement protocol)

**Used By:**
- `BridgeService._start_socket_server()` (Phase 1.2) - Server side
- `RPClientApp._connect_to_bridge()` (Phase 1.3) - Client side
- `launch.py:wait_for_bridge()` (Phase 1.1) - Connection test

**CRITICAL FILES:**
- `ipc_protocol.py` - Message format (must match on both sides)
- `socket_server.py` - Bridge backend
- `socket_client.py` - TUI frontend

---

### 4. LLM Subsystem (11 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `llm/__init__.py` | ? | Exports | - |
| `llm/base.py` | ? | LLMClient base class | All clients |
| `llm/claude_api_client.py` | ? | Claude API client | Registry |
| `llm/claude_sdk_client.py` | ? | Claude SDK client (Node.js) | Registry |
| `llm/config_utils.py` | ? | LLM config helpers | Clients |
| `llm/llm_router.py` | ? | Route requests to clients | Bridge (potential) |
| `llm/mock_client.py` | ? | Mock client for testing | BridgeService (testing mode) |
| `llm/openai_client.py` | ? | OpenAI API client | Registry |
| `llm/openrouter_client.py` | ? | OpenRouter API client | Registry |
| `llm/proxy.py` | ? | LLM proxy wrapper | Unknown usage |
| `llm/registry.py` | ? | Provider registry | BridgeService._create_client() |
| `llm/semantic_ai_client.py` | ? | SemanticAI client | Registry |

**Key Components:**
- **LLMClient** (abstract base) - Common interface
  - Methods: `call_llm(prompt, ...)`, `stream_llm(...)`
  - Handles: Retries, streaming, error handling
- **Provider Registry** - Maps provider names → factory functions
- **Provider Implementations:**
  - Claude API (direct HTTP)
  - Claude SDK (Node.js subprocess)
  - OpenAI
  - OpenRouter
  - SemanticAI (secondary LLM)
  - Mock (testing)

**Factory Pattern:**
```python
provider_spec = get_provider("claude_api_client")
client = provider_spec.factory(config)
```

**Dependencies:**
- base.py (abstract interface)
- registry.py (provider lookup)
- Individual client implementations
- transports (HTTP abstraction)

**Used By:**
- `BridgeService._initialize_llm_clients()` (Phase 1.2) - Creates primary/secondary
- Background agents (via bridge reference)
- Message handlers (via bridge.primary_client)

**CRITICAL FILES:**
- `base.py` - LLMClient interface
- `registry.py` - Provider selection logic
- `claude_sdk_client.py` - Node.js SDK integration
- `mock_client.py` - Testing without real LLM

---

### 5. Logging Subsystem (3 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `logging/__init__.py` | ? | Exports | - |
| `logging/agent_logging.py` | ? | Agent-specific logging | Agents |
| `logging/python_logging.py` | ? | Python logging adapter | All services |

**Key Components:**
- **LoggingService** interface - Shared logging contract
- **PythonLoggingService** - Wraps Python's logging module
- **AgentLoggingService** - Agent-specific log formatting

**Usage:**
- Most services use `get_logger(name)` from shared.logging
- PythonLoggingService wraps standard logging.Logger
- Structured logging support

**Dependencies:** None (leaf node)

**Used By:**
- All services (via get_logger)
- TUI app (Phase 1.3) - Creates logger
- BridgeService (Phase 1.2) - Creates logger

---

### 6. Retry Subsystem (2 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `retry/__init__.py` | ? | Exports | - |
| `retry/retry_policy.py` | ? | Retry logic with backoff | LLM clients, IPC |

**Key Components:**
- **RetryPolicy** class
- Exponential backoff
- Max attempts configuration
- Exception filtering

**Used By:**
- LLM clients (API call retries)
- IPC clients (connection retries)
- File operations (lock retries)

---

### 7. RP Initialization Subsystem (3 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `rp_initialization/__init__.py` | ? | Exports | - |
| `rp_initialization/markdown_generator.py` | ? | Generate MD files | RPCreator |
| `rp_initialization/rp_creator.py` | ? | Create new RP directory | launch.py:create_new_rp() |

**Key Components:**
- **RPCreator** - Creates RP directory structure
- **MarkdownGenerator** - Generates template files

**Used By:**
- `launch.py:create_new_rp()` (Phase 1.1) - RP wizard
- Setup scripts

---

### 8. Sessions Subsystem (2 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `sessions/__init__.py` | ? | Exports | - |
| `sessions/session_state_service.py` | ? | Session state management | Multiple services |

**Key Components:**
- **SessionStateService** class
  - Loads/saves session_state.json
  - Provides timeline/scene/chapter data
  - Used for consistency across services

**Dependencies:** None (but accessed by many)

**Used By:**
- `BridgeService._initialize_services()` (Phase 1.2) - Creates instance
- `RPClientApp.__init__()` (Phase 1.3) - Creates instance
- Automation factory - Passes to FileManager, EntityService, SessionRepository
- Agents - Access scene/timeline context

**CRITICAL FILE:**
- `session_state_service.py` - Central source of truth for session state

---

### 9. Telemetry Subsystem (2 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `telemetry/__init__.py` | ? | Exports | - |
| `telemetry/performance.py` | ? | Performance monitoring | Services (optional) |

**Key Components:**
- Performance timers
- Metrics collection
- Profiling utilities

**Used By:**
- Services (optional instrumentation)
- Debug/profiling scenarios

---

### 10. Templates Subsystem (5 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `templates/__init__.py` | ? | Exports | - |
| `templates/character_template_generator.py` | ? | Generate character sheets | EntityService |
| `templates/schema_loader.py` | ? | Load JSON schemas | TemplateRenderer |
| `templates/state_service.py` | ? | State file templates | EntityService, Setup |
| `templates/template_renderer.py` | ? | Jinja2 template rendering | Generators |

**Key Components:**
- **StateTemplateService** - State file templates
- **CharacterTemplateGenerator** - Character sheet generation
- **SchemaLoader** - JSON schema validation
- **TemplateRenderer** - Jinja2 rendering

**Used By:**
- EntityService (character creation)
- RP initialization (state file creation)
- Automation factory (creates StateTemplateService)

---

### 11. Transports Subsystem (5 files)

| File | Lines | Purpose | Called By |
|------|-------|---------|-----------|
| `transports/__init__.py` | ? | Exports | - |
| `transports/fake_transport.py` | ? | Mock HTTP transport | Testing |
| `transports/logging_transport.py` | ? | Logging HTTP wrapper | LLM clients |
| `transports/proxy_transport.py` | ? | Proxy HTTP transport | LLM clients |
| `transports/requests_transport.py` | ? | Real HTTP transport (requests lib) | LLM clients |

**Key Components:**
- **Transport** interface - HTTP abstraction
- Implementations for testing, logging, production
- Used by LLM clients to make API calls

**Dependencies:**
- requests library (for real transport)

**Used By:**
- LLM client implementations
- Testing infrastructure

---

## Service Dependencies Graph

```
INFRASTRUCTURE LAYER DEPENDENCIES

config/
  └─> (no dependencies - leaf node)

filesystem/
  ├─> write_queue (leaf)
  ├─> json_store, markdown_store → write_queue
  ├─> state_paths (leaf)
  └─> file_manager → stores, write_queue

  └─> file_access_service → file_manager, tiered_loader
  └─> tiered_loader → markdown_store

ipc/
  ├─> ipc_protocol (leaf - data structures)
  ├─> socket_server → ipc_protocol
  └─> socket_client → ipc_protocol

llm/
  ├─> base (abstract interface)
  ├─> registry → base
  ├─> transports/ (HTTP abstraction)
  └─> clients (claude, openai, etc.) → base, registry, transports

logging/
  └─> (no dependencies - leaf node)

retry/
  └─> (no dependencies - leaf node)

rp_initialization/
  ├─> markdown_generator
  └─> rp_creator → markdown_generator, templates/

sessions/
  └─> (no dependencies - accesses filesystem directly)

telemetry/
  └─> (no dependencies - leaf node)

templates/
  ├─> schema_loader
  ├─> template_renderer → schema_loader
  └─> generators → template_renderer

transports/
  └─> (requests library - external dependency)
```

---

## Runtime Usage by Phase 1 Components

### BridgeService Uses:

| Subsystem | Usage |
|-----------|-------|
| config | ConfigLoader - Load config.json |
| filesystem | StatePaths - Path utilities |
| ipc | SocketServer - Listen for TUI requests |
| llm | Registry, Clients - Primary/secondary LLM |
| logging | get_logger - Bridge logging |
| sessions | SessionStateService - Session state |
| templates | StateTemplateService - State templates (via entities) |

### TUI App Uses:

| Subsystem | Usage |
|-----------|-------|
| filesystem | StatePaths - Path utilities |
| ipc | SocketClient - Connect to bridge |
| logging | PythonLoggingService - TUI logging |
| sessions | SessionStateService, SessionRepository - Chat history |

### Automation Factory Uses:

| Subsystem | Usage |
|-----------|-------|
| config | ConfigLoader - Agent config |
| filesystem | ALL - File I/O for agents |
| logging | get_logger - Service logging |
| sessions | SessionStateService - Timeline consistency |
| templates | StateTemplateService - Entity templates |

### launch.py Uses:

| Subsystem | Usage |
|-----------|-------|
| ipc | SocketClient - Test bridge connection (PING) |
| rp_initialization | RPCreator - Create new RP wizard |

---

## Files Traced in Phase 1

### Already Analyzed:
- `config/config_loader.py` - Referenced in EXECUTION_FLOW_2_BRIDGE.md
- `filesystem/state_paths.py` - Referenced in EXECUTION_FLOW_2_BRIDGE.md, EXECUTION_FLOW_3_TUI.md
- `ipc/socket_server.py` - Referenced in EXECUTION_FLOW_2_BRIDGE.md
- `ipc/socket_client.py` - Referenced in EXECUTION_FLOW_3_TUI.md
- `llm/registry.py` - Referenced in EXECUTION_FLOW_2_BRIDGE.md
- `llm/mock_client.py` - Referenced in EXECUTION_FLOW_2_BRIDGE.md
- `sessions/session_state_service.py` - Referenced in multiple flows

### Need Detailed Analysis (Phase 2):
- All remaining 44 files

---

## Critical Infrastructure Services (Priority Order)

### Tier 1 - Core Runtime Dependencies
1. **state_paths.py** - Used by all file operations
2. **ipc_protocol.py** - Bridge/TUI communication contract
3. **socket_server.py** - Bridge backend
4. **socket_client.py** - TUI frontend
5. **session_state_service.py** - Central state management

### Tier 2 - Essential Services
6. **config_loader.py** - Configuration system
7. **file_manager.py** - File operation coordinator
8. **write_queue.py** - Prevents file corruption
9. **llm/registry.py** - LLM provider selection
10. **llm/base.py** - LLM client interface

### Tier 3 - Supporting Services
11. All LLM client implementations
12. All filesystem stores (JSON, Markdown)
13. Tiered loader (entity loading optimization)
14. File access service (automation API)
15. Logging, retry, telemetry utilities

---

## Dead Code Analysis (Preliminary)

### Potentially Unused Files (Need Verification):
1. **llm/proxy.py** - No obvious usage in traced flows
2. **llm/llm_router.py** - May be legacy/unused
3. **telemetry/** - May be optional/unused in production

### Verification Required (Phase 3):
- Grep for imports across entire codebase
- Check test files for usage
- Cross-reference with config files
- Trace from all entry points

---

## Next Analysis Steps

### Phase 2.1 Detailed Analysis:
1. Read each file systematically
2. Document:
   - Classes and methods
   - Dependencies
   - Called by (cross-reference)
   - State read/write
3. Build complete dependency graph
4. Identify dead code (unused files/methods)
5. Identify duplicated functionality

### Phase 3 Verification:
- Grep every file for imports
- Cross-reference with execution flows
- Confirm dead code findings (3+ ways)

---

**Analysis Status:** Infrastructure layer inventory complete
**Next Step:** Begin detailed file-by-file analysis of infrastructure subsystems
