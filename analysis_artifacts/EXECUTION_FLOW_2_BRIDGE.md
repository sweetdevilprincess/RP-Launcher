# BridgeService Execution Flow

**File:** `refactoring/src/presentation/bridge/bridge_service.py` (359 lines)
**Purpose:** Core bridge service - connects TUI to automation system via IPC socket
**Class:** `BridgeService` (lines 37-359)

---

## Imports

### Standard Library
- `pathlib.Path` (line 8) - Path handling
- `typing.Optional` (line 9) - Type hints

### Automation Layer
- `src.automation.contracts.AutomationContext` (line 11) - Context object for automation
- `src.automation.factory.create_automation_service` (line 12) → **SERVICE FACTORY**
- `src.automation.services.AutomationService` (line 13) → **CRITICAL SERVICE**
- `src.automation.templates.TemplateRegistry` (line 14) - Template management

### Domain Layer
- `src.domain.entities.entity_service.EntityService` (line 15) → **SERVICE**
- `src.domain.sessions.ChatlogOrganizer` (line 16) → **SERVICE**
- `src.domain.sessions.SessionRepository` (line 16) → **SERVICE**
- `src.domain.sessions.SessionWriteBack` (line 16) → **SERVICE**

### Infrastructure Layer
- `src.infrastructure.config.ConfigLoader` (line 17) → **SERVICE**
- `src.infrastructure.filesystem.StatePaths` (line 18) - Path utilities
- `src.infrastructure.ipc.*` (lines 19-27) - IPC communication components
- `src.infrastructure.llm.LLMClient` (line 28) - LLM client base class
- `src.infrastructure.llm.registry.get_provider` (line 29) - Provider lookup
- `src.infrastructure.llm.registry.list_providers` (line 29) - Provider enumeration
- `src.infrastructure.sessions.SessionStateService` (line 30) → **SERVICE**

### Shared/Other
- `src.shared.logging.get_logger` (line 31) - Logging utility
- `src.wip.WipExecutor` (line 32) - WIP testing system
- `.handlers.HANDLER_REGISTRY` (line 34) - Request handler registry

---

## Constructor: `__init__(rp_dir, host, port)` (lines 47-86)

### Parameters
- `rp_dir: Path` - RP directory path
- `host: str = "127.0.0.1"` - Socket server host
- `port: int = 5555` - Socket server port

### Instance Variables Initialized

#### Basic State (lines 55-57)
- `self.rp_dir = rp_dir`
- `self.host = host`
- `self.port = port`

#### Socket Server (line 60)
- `self.socket_server: Optional[SocketServer] = None`

#### Refactored Services (lines 63-69) - **ALL SET TO None**
- `self.config_loader: Optional[ConfigLoader] = None`
- `self.automation_service: Optional[AutomationService] = None`
- `self.entity_service: Optional[EntityService] = None`
- `self.session_state_service: Optional[SessionStateService] = None`
- `self.session_repository: Optional[SessionRepository] = None`
- `self.session_writeback: Optional[SessionWriteBack] = None`
- `self.chatlog_organizer: Optional[ChatlogOrganizer] = None`

#### LLM Clients (lines 72-77)
- `self.primary_client: Optional[LLMClient] = None`
- `self.secondary_client: Optional[LLMClient] = None`
- `self.llm_routing: dict = {}`
- `self.llm_client: Optional[LLMClient] = None` (deprecated, backwards compat)

#### Runtime State (lines 80-82)
- `self.current_provider: Optional[str] = None`
- `self.testing_mode: bool = False`
- `self.logger = get_logger("bridge")`

#### WIP System (lines 85-86)
- `wip_root = Path(__file__).parents[2] / "wip"` (computes `src/wip/`)
- `self.wip_executor: Optional[WipExecutor] = WipExecutor(wip_root)`
  - **→ Trace WipExecutor if needed**

### Constructor Summary
**NO services instantiated in constructor** - all deferred to `start()` method.

---

## `start()` Method (lines 88-102)

**Called by:** `run()` (line 339) or `__enter__()` (line 353)

### Flow:
1. **Print banner** (lines 90-91)
2. **Calls:** `self._load_configuration()` (line 94)
   - → Go to **`_load_configuration()` section below**
3. **Calls:** `self._initialize_services()` (line 97)
   - → Go to **`_initialize_services()` section below**
4. **Calls:** `self._start_socket_server()` (line 100)
   - → Go to **`_start_socket_server()` section below**
5. **Print ready message** (line 102)

---

## `_load_configuration()` Method (lines 104-117)

### Services Instantiated:

#### 1. ConfigLoader (line 107)
- **File:** `src/infrastructure/config/config_loader.py`
- **Constructor:** `ConfigLoader(self.rp_dir)`
- **Stored:** `self.config_loader`
- **→ TRACE THIS:** ConfigLoader implementation

### Methods Called:

#### `config_loader.load()` (line 108)
- Returns: `config` dict
- **→ TRACE THIS:** What does load() do?

#### `config_loader.validate_rp_directory()` (line 111)
- Returns: `errors` list
- Prints warnings if any validation errors (lines 112-115)

### Result:
- `self.config_loader` is initialized
- Configuration loaded and validated

---

## `_initialize_services()` Method (lines 119-163)

**This is where ALL core services are created!**

### Services Instantiated (in order):

#### 1. AutomationService (line 124)
- **Factory:** `create_automation_service(self.rp_dir, bridge=self)`
  - **File:** `src/automation/factory.py`
  - **→ CRITICAL TRACE:** Agent system initialization
- **Parameters:**
  - `rp_dir`: RP directory path
  - `bridge`: Reference to this BridgeService instance (for agent LLM access)
- **Stored:** `self.automation_service`
- **→ GO TO:** EXECUTION_FLOW_4_AGENTS.md (Phase 1.5)

#### 2. EntityService (line 128)
- **File:** `src/domain/entities/entity_service.py`
- **Constructor:** `EntityService()` (no arguments)
- **Stored:** `self.entity_service`
- **→ TRACE THIS:** EntityService implementation

#### 3. SessionStateService (line 132)
- **File:** `src/infrastructure/sessions/session_state_service.py`
- **Constructor:** `SessionStateService(logger=self.logger)`
- **Stored:** `self.session_state_service`
- **→ TRACE THIS:** Session state management

#### 4. StatePaths (line 136)
- **File:** `src/infrastructure/filesystem/state_paths.py`
- **Constructor:** `StatePaths(rp_dir=self.rp_dir)`
- **Stored:** Local variable `paths` (used for next services)
- **→ TRACE THIS:** Path utilities

#### 5. SessionRepository (lines 137-141)
- **File:** `src/domain/sessions/repository.py`
- **Constructor:** `SessionRepository(paths, logger, session_state_service)`
- **Parameters:**
  - `paths`: StatePaths instance
  - `logger`: Bridge logger
  - `session_state_service`: SessionStateService instance
- **Stored:** `self.session_repository`
- **→ TRACE THIS:** Session data persistence

#### 6. SessionWriteBack (lines 142-145)
- **File:** `src/domain/sessions/write_back.py`
- **Constructor:** `SessionWriteBack(repository, logger)`
- **Parameters:**
  - `repository`: SessionRepository instance
  - `logger`: Bridge logger
- **Stored:** `self.session_writeback`
- **→ TRACE THIS:** Session write operations

#### 7. ChatlogOrganizer (lines 146-150)
- **File:** `src/domain/sessions/chatlog_organizer.py`
- **Constructor:** `ChatlogOrganizer(paths, logger, repository)`
- **Parameters:**
  - `paths`: StatePaths instance
  - `logger`: Bridge logger
  - `repository`: SessionRepository instance
- **Stored:** `self.chatlog_organizer`
- **→ TRACE THIS:** Chat log management

#### 8. LLM Clients (lines 154-163)
- **Calls:** `self._initialize_llm_clients()` (line 155)
- **Catches:** All exceptions (non-fatal)
- **Prints:** Warnings and setup instructions if fails
- **→ Go to:** `_initialize_llm_clients()` section below

### Service Dependency Graph:
```
BridgeService
├─> ConfigLoader (rp_dir)
├─> AutomationService (rp_dir, bridge) ──> AGENT SYSTEM
├─> EntityService ()
├─> SessionStateService (logger)
├─> StatePaths (rp_dir)
├─> SessionRepository (paths, logger, session_state_service)
├─> SessionWriteBack (repository, logger)
├─> ChatlogOrganizer (paths, logger, repository)
└─> LLM Clients
     ├─> primary_client (provider_name)
     └─> secondary_client (provider_name)
```

---

## `_initialize_llm_clients()` Method (lines 165-221)

### Testing Mode Path (lines 167-176)
**If:** `self.testing_mode == True`
1. **Imports:** `MockLLMClient` (line 169)
   - **File:** `src/infrastructure/llm/mock_client.py`
2. **Instantiates:** `mock_client = MockLLMClient()`
3. **Sets:**
   - `self.primary_client = mock_client`
   - `self.secondary_client = mock_client`
   - `self.llm_client = mock_client`
   - `self.current_provider = "mock"`
4. **Returns early**

### Production Mode Path (lines 178-220)

#### Step 1: Load Routing Config (lines 179-181)
- Calls: `self.config_loader.load()` → `config` dict
- Imports: `LLM_ROUTING_DEFAULTS` from `src/infrastructure/config/defaults`
- Gets: `self.llm_routing = config.get("llm", LLM_ROUTING_DEFAULTS)`

#### Step 2: Determine Primary Provider (lines 183-190)
- Gets: `primary_provider = self.llm_routing.get("primary_provider")`
- **If not set:** Calls `self._find_first_enabled_provider(config)` (lines 186-187)
  - → Go to `_find_first_enabled_provider()` section below
- **If still None:** Raises `RuntimeError("No LLM provider configured")`

#### Step 3: Initialize Primary Client (lines 192-195)
- **Calls:** `self._create_client(primary_provider)` (line 193)
  - → Go to `_create_client()` section below
- **Stores:** `self.primary_client`
- **Sets:** `self.current_provider = primary_provider`

#### Step 4: Initialize Secondary Client (lines 197-217)
- Gets: `secondary_provider = self.llm_routing.get("secondary_provider", "")`
- Gets: `use_secondary = self.llm_routing.get("use_secondary_for_automation", False)`

**Conditional Logic:**
- **If:** `use_secondary AND secondary_provider AND secondary_provider != primary_provider`
  - Creates separate secondary client (lines 204-210)
  - Catches exceptions, falls back to primary
- **Else:**
  - Uses primary for everything (line 213)

#### Step 5: Backwards Compatibility (line 220)
- Sets: `self.llm_client = self.primary_client`

---

## `_find_first_enabled_provider(config)` Method (lines 222-241)

**Purpose:** Scans modules config for first enabled LLM provider

### Flow:
1. Gets: `modules = config.get("modules", {})`
2. Defines: `llm_providers` list (lines 232-235)
   - `"claude_api_client"`
   - `"claude_sdk_client"`
   - `"openai_client"`
   - `"openrouter_client"`
3. **Iterates:** `modules.items()`
4. **Checks:** `module_config.get("enabled") AND module_name in llm_providers`
5. **Returns:** First matching provider name, or `None`

---

## `_create_client(provider_name)` Method (lines 243-281)

**Purpose:** Creates LLM client instance for given provider

### Flow:

#### Step 1: Load Config (line 255)
- Calls: `self.config_loader.load()` → `config`

#### Step 2: Claude SDK Redirect (lines 258-263)
**If:** `provider_name == "claude_api_client"`
- Checks: `config["modules"]["claude_api_client"]["config"]["use_sdk"]`
- **If True:** Changes `provider_name = "claude_sdk_client"`

#### Step 3: Get Provider from Registry (lines 266-268)
- **Calls:** `get_provider(provider_name)` (line 266)
  - **File:** `src/infrastructure/llm/registry.py`
  - **→ TRACE THIS:** Provider registry lookup
- **Returns:** `provider_spec` (or None)
- **If None:** Raises `RuntimeError(f"Provider not found: {provider_name}")`

#### Step 4: Prepare Factory Config (lines 271-278)
- Extracts: `module_config = config["modules"][provider_name]["config"]`
- Creates: `factory_config` dict with:
  - All settings from `module_config` (spread)
  - `"rp_dir": self.rp_dir`
  - `"project_root": self.rp_dir`

#### Step 5: Create Client (line 281)
- **Calls:** `provider_spec.factory(factory_config)`
- **Returns:** Initialized `LLMClient` instance

---

## `_start_socket_server()` Method (lines 283-291)

### Services Instantiated:

#### SocketServer (line 287)
- **File:** `src/infrastructure/ipc/socket_server.py`
- **Constructor:** `SocketServer(self.host, self.port)`
- **Stored:** `self.socket_server`
- **→ TRACE THIS:** Socket server implementation

### Methods Called:

#### `socket_server.set_handler(callback)` (line 288)
- Sets handler: `self._handle_request`
- Request handler will be called for each IPC message

#### `socket_server.start()` (line 289)
- Starts listening on socket
- **→ TRACE THIS:** How does start() work?

---

## `_handle_request(request)` Method (lines 293-322)

**Called by:** Socket server for each incoming IPC request

### Flow:

#### Step 1: Parse Request Type (line 302)
- Creates: `request_type = IPCMessageType(request.type)`

#### Step 2: Lookup Handler (line 306)
- **Accesses:** `HANDLER_REGISTRY.get(request_type)`
  - **File:** `src/presentation/bridge/handlers/__init__.py`
  - **→ TRACE THIS:** Handler registry contents

#### Step 3: Execute Handler (lines 308-311)
**If handler found:**
- **Instantiates:** `handler = handler_class(self)` (line 310)
  - Passes BridgeService instance to handler
- **Calls:** `handler.handle(request)` (line 311)
- **Returns:** JSON response string

**If handler not found:** (lines 313-316)
- Returns error response

#### Step 4: Error Handling (lines 318-322)
- Catches all exceptions
- Returns error response

---

## Lifecycle Methods

### `stop()` (lines 328-335)
- Stops socket server if running (lines 332-333)
- Prints status messages

### `run()` (lines 337-349)
**Main blocking method**
1. Calls: `self.start()` (line 339)
2. **Loops:** While `socket_server.running` (lines 343-345)
   - Sleeps 1 second per iteration
   - **BLOCKS indefinitely**
3. Catches: `KeyboardInterrupt` (line 346)
4. **Finally:** Calls `self.stop()` (line 349)

### Context Manager Support (lines 351-358)
- `__enter__()`: Calls `start()`, returns `self`
- `__exit__()`: Calls `stop()`

---

## Services to Trace Next (Priority Order)

### Phase 1.2 Continuation - Trace Each Service:

#### **CRITICAL - Agent System:**
1. `create_automation_service()` → EXECUTION_FLOW_4_AGENTS.md (Phase 1.5)
   - File: `src/automation/factory.py`
   - **HIGHEST PRIORITY** - This initializes all agents

#### **HIGH Priority - Core Services:**
2. `ConfigLoader`
   - File: `src/infrastructure/config/config_loader.py`
   - What does `load()` return?
   - What does `validate_rp_directory()` check?

3. `EntityService`
   - File: `src/domain/entities/entity_service.py`
   - What methods does it expose?

4. `SessionStateService`
   - File: `src/infrastructure/sessions/session_state_service.py`
   - Session state management

5. `SessionRepository`
   - File: `src/domain/sessions/repository.py`
   - How are sessions stored?

6. `SocketServer`
   - File: `src/infrastructure/ipc/socket_server.py`
   - How does IPC work?

7. `HANDLER_REGISTRY`
   - File: `src/presentation/bridge/handlers/__init__.py`
   - What handlers exist? What messages do they handle?

#### **MEDIUM Priority:**
8. `SessionWriteBack` - Session write operations
9. `ChatlogOrganizer` - Chat log organization
10. `StatePaths` - Path utilities
11. `LLM Registry` - `get_provider()` implementation
12. `MockLLMClient` - Testing mode client

---

## Summary

**BridgeService is the central orchestrator:**
1. Loads configuration via ConfigLoader
2. Initializes 7+ core services (automation, entities, sessions, etc.)
3. Sets up dual LLM client system (primary + secondary)
4. Starts socket server for IPC
5. Routes incoming requests to handlers via registry
6. Runs indefinitely until stopped

**Service Count:**
- **Mandatory:** 7 services (config, automation, entity, session state, session repo, write-back, chatlog)
- **Optional:** 2-3 LLM clients (primary, secondary, mock)
- **IPC:** 1 socket server

**Next Critical Traces:**
- `create_automation_service()` - Agent system (Phase 1.5)
- `HANDLER_REGISTRY` - Request routing
- `ConfigLoader` - Configuration system
- Individual services as needed for Phase 2 analysis

---

**Analysis Complete:** Phase 1.2 - BridgeService Initialization
**Next Step:** Phase 1.2 - Trace services instantiated by Bridge (as needed)
**Next Step:** Phase 1.3 - TUI Application Trace
