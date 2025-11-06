# Runtime Call Graph - Complete Execution Flow

**Purpose:** Synthesize all execution flows traced in Phase 1
**Status:** Based on analysis of launch.py, BridgeService, and RPClientApp

---

## Startup Sequence (Default Mode: Bridge + TUI)

### Timeline Overview

```
t=0.0s   launch.py main() starts
t=0.1s   RP selection or argument parsing
t=0.2s   Bridge process spawned (multiprocessing.Process)
t=0.3s   Bridge subprocess: BridgeService.__init__()
t=0.5s   Bridge subprocess: BridgeService.start()
t=1.0s   Bridge subprocess: Services initialized
t=1.5s   Bridge subprocess: Socket server listening
t=2.0s   Main process: wait_for_bridge() → PING test
t=2.5s   Main process: PING successful
t=3.0s   Main process: RPClientApp.__init__()
t=3.2s   Main process: RPClientApp.compose() → UI built
t=3.5s   Main process: RPClientApp.on_mount()
t=3.6s   Main process: TUI connects to Bridge (IPC)
t=4.0s   Main process: Chat history loaded
t=4.5s   READY - User can interact
```

---

## Detailed Startup Flow

### Phase 1: Launch Process (launch.py)

```
main()
  │
  ├─> Parse arguments (argparse)
  │
  ├─> Determine RP directory
  │    ├─> IF provided via CLI: validate
  │    └─> ELSE: RPLauncherApp.run() → user selection
  │
  ├─> Create log directory
  │    └─> {rp_dir}/logs/launcher.log
  │
  ├─> Start Bridge Process
  │    │
  │    └─> multiprocessing.Process(
  │            target=run_bridge,
  │            args=(rp_dir, host, port),
  │            daemon=True
  │        )
  │        │
  │        └─> run_bridge() [SUBPROCESS STARTS HERE]
  │             │
  │             ├─> Open {rp_dir}/logs/bridge.log
  │             ├─> Redirect stdout/stderr to log
  │             │
  │             └─> BridgeService(rp_dir, host, port)
  │                  │
  │                  └─> bridge.run()
  │                       └─> [GO TO: Bridge Initialization]
  │
  ├─> wait_for_bridge(host, port, timeout=10)
  │    │
  │    ├─> Phase 1: Wait for socket (retry loop)
  │    │    └─> socket.connect((host, port))
  │    │
  │    ├─> Phase 2: Verify Bridge responding
  │    │    │
  │    │    └─> SocketClient(host, port)
  │    │         ├─> client.connect()
  │    │         ├─> client.send_request(IPCMessageType.PING, timeout=2.0)
  │    │         └─> Check: response.success == True
  │    │
  │    └─> RETURNS: True if ready, False if timeout
  │
  ├─> IF wait_for_bridge() failed:
  │    └─> EXIT with error
  │
  ├─> RPClientApp(rp_dir, host, port)
  │    │
  │    └─> app.run()
  │         └─> [GO TO: TUI Initialization]
  │
  └─> Cleanup (finally block)
       ├─> bridge_process.terminate()
       └─> bridge_process.join(timeout=2)
```

---

## Bridge Initialization (BridgeService)

**Process:** Background subprocess spawned by launch.py
**Entry:** `run_bridge()` → `BridgeService.run()` → `BridgeService.start()`

```
BridgeService.__init__(rp_dir, host, port)
  │
  ├─> Initialize instance variables (all None)
  │    ├─> socket_server: None
  │    ├─> config_loader: None
  │    ├─> automation_service: None
  │    ├─> entity_service: None
  │    ├─> session_state_service: None
  │    ├─> session_repository: None
  │    ├─> session_writeback: None
  │    ├─> chatlog_organizer: None
  │    ├─> primary_client: None
  │    ├─> secondary_client: None
  │    └─> llm_client: None
  │
  ├─> get_logger("bridge") → self.logger
  │
  └─> WipExecutor(wip_root) → self.wip_executor


BridgeService.start()
  │
  ├─> _load_configuration()
  │    │
  │    ├─> ConfigLoader(rp_dir)
  │    │    └─> Stores: self.config_loader
  │    │
  │    ├─> config_loader.load()
  │    │    └─> Returns: config dict
  │    │
  │    └─> config_loader.validate_rp_directory()
  │         └─> Returns: list of errors (if any)
  │
  ├─> _initialize_services()
  │    │
  │    ├─> 1. create_automation_service(rp_dir, bridge=self)
  │    │    │   [File: src/automation/factory.py]
  │    │    │
  │    │    └─> Stores: self.automation_service
  │    │         [→ GO TO: Agent System Initialization]
  │    │
  │    ├─> 2. EntityService()
  │    │    │   [File: src/domain/entities/entity_service.py]
  │    │    │
  │    │    └─> Stores: self.entity_service
  │    │
  │    ├─> 3. SessionStateService(logger=self.logger)
  │    │    │   [File: src/infrastructure/sessions/session_state_service.py]
  │    │    │
  │    │    └─> Stores: self.session_state_service
  │    │
  │    ├─> 4. StatePaths(rp_dir=rp_dir)
  │    │    │   [File: src/infrastructure/filesystem/state_paths.py]
  │    │    │
  │    │    └─> Local variable: paths
  │    │
  │    ├─> 5. SessionRepository(paths, logger, session_state_service)
  │    │    │   [File: src/domain/sessions/repository.py]
  │    │    │
  │    │    └─> Stores: self.session_repository
  │    │
  │    ├─> 6. SessionWriteBack(repository, logger)
  │    │    │   [File: src/domain/sessions/write_back.py]
  │    │    │
  │    │    └─> Stores: self.session_writeback
  │    │
  │    ├─> 7. ChatlogOrganizer(paths, logger, repository)
  │    │    │   [File: src/domain/sessions/chatlog_organizer.py]
  │    │    │
  │    │    └─> Stores: self.chatlog_organizer
  │    │
  │    └─> 8. _initialize_llm_clients()
  │         │
  │         ├─> IF testing_mode:
  │         │    │
  │         │    └─> MockLLMClient()
  │         │         └─> Stores: primary_client, secondary_client, llm_client
  │         │
  │         └─> ELSE (Production):
  │              │
  │              ├─> Load routing config
  │              │    └─> config["llm"] → self.llm_routing
  │              │
  │              ├─> Determine primary provider
  │              │    ├─> From: llm_routing["primary_provider"]
  │              │    └─> OR: _find_first_enabled_provider(config)
  │              │
  │              ├─> _create_client(primary_provider)
  │              │    │
  │              │    ├─> get_provider(provider_name)
  │              │    │    [File: src/infrastructure/llm/registry.py]
  │              │    │    └─> Returns: provider_spec
  │              │    │
  │              │    ├─> Extract module config
  │              │    │
  │              │    └─> provider_spec.factory(factory_config)
  │              │         └─> Returns: LLMClient instance
  │              │
  │              ├─> Stores: self.primary_client
  │              │
  │              ├─> IF use_secondary_for_automation:
  │              │    └─> _create_client(secondary_provider)
  │              │         └─> Stores: self.secondary_client
  │              │
  │              └─> Stores: self.llm_client = self.primary_client (backwards compat)
  │
  └─> _start_socket_server()
       │
       ├─> SocketServer(host, port)
       │    [File: src/infrastructure/ipc/socket_server.py]
       │    └─> Stores: self.socket_server
       │
       ├─> socket_server.set_handler(self._handle_request)
       │
       └─> socket_server.start()
            └─> Server listening on socket


BridgeService.run()
  │
  ├─> start() [completed above]
  │
  └─> LOOP: while socket_server.running:
       └─> sleep(1)
           [Blocks indefinitely until KeyboardInterrupt or stop()]
```

---

## TUI Initialization (RPClientApp)

**Process:** Main process (after Bridge ready)
**Entry:** `RPClientApp(rp_dir, host, port)` → `app.run()`

```
RPClientApp.__init__(rp_dir, bridge_host, bridge_port)
  │
  ├─> super().__init__()  [Textual App]
  │
  ├─> Store basic state
  │    ├─> self.rp_dir = rp_dir
  │    ├─> self.bridge_host = bridge_host
  │    └─> self.bridge_port = bridge_port
  │
  ├─> Initialize component references (all None)
  │    ├─> header: None
  │    ├─> context_panel: None
  │    ├─> chat_display: None
  │    ├─> text_area: None
  │    ├─> entity_manager: None
  │    └─> settings_overlay: None
  │
  ├─> Initialize IPC state
  │    ├─> ipc_client: None
  │    ├─> connected: False
  │    └─> connection_time: 0.0
  │
  ├─> Create services
  │    │
  │    ├─> StatePaths(rp_dir=rp_dir)
  │    │    └─> Local variable: paths
  │    │
  │    ├─> PythonLoggingService(logger=logging.getLogger("rp.tui.app"))
  │    │    └─> Local variable: logger
  │    │
  │    ├─> SessionStateService(logger=logger)
  │    │    └─> Local variable: session_state_service
  │    │
  │    └─> SessionRepository(paths, logger, session_state_service)
  │         └─> Stores: self.session_repository
  │
  └─> Initialize tab tracking
       └─> self.last_non_entity_tab = "tab-chat"


RPClientApp.compose() [Called by Textual]
  │
  ├─> Create Tabs widget
  │    └─> Tab("💬 Chat", ...), Tab("🎭 Entities", ...), etc.
  │
  └─> Create ContentSwitcher with pages:
       │
       ├─> Chat Page:
       │    │
       │    ├─> ContextPanel(rp_dir)
       │    │    └─> Stores: self.context_panel
       │    │
       │    ├─> ChatDisplay()
       │    │    └─> Stores: self.chat_display
       │    │
       │    ├─> RPTextArea()
       │    │    └─> Stores: self.text_area
       │    │
       │    └─> Buttons (Send, Compress Chapter)
       │
       ├─> Entities Page (placeholder)
       ├─> Branches Page: BranchesPage()
       ├─> Settings Page (empty, overlay used)
       ├─> Help Page: Markdown (static)
       ├─> Status Page: Markdown (static)
       │
       ├─> Header: AppHeader(rp_dir)
       │    └─> Stores: self.header
       │
       └─> Floating Overlays:
            │
            ├─> EntityManager()
            │    └─> Stores: self.entity_manager
            │
            └─> SettingsOverlay()
                 └─> Stores: self.settings_overlay


RPClientApp.on_mount() [Called by Textual after compose]
  │
  ├─> _load_theme()
  │    │
  │    ├─> Read: {rp_dir}/config/config.json
  │    ├─> Get: config["system"]["theme"]
  │    └─> Set: self.theme = theme
  │
  ├─> _connect_to_bridge()
  │    │
  │    └─> FOR attempt in range(3):
  │         │
  │         ├─> SocketClient(host, port)
  │         │    └─> Stores: self.ipc_client
  │         │
  │         ├─> ipc_client.connect()
  │         │    └─> Opens socket connection
  │         │
  │         ├─> ipc_client.send_request(IPCMessageType.PING, timeout=5.0)
  │         │    └─> Tests Bridge connectivity
  │         │
  │         └─> IF ping successful:
  │              ├─> self.connected = True
  │              ├─> self.connection_time = time.time()
  │              └─> RETURN (success)
  │
  ├─> _load_chat_history()
  │    │
  │    ├─> session_repository.load_active_session()
  │    │    └─> Returns: session object with messages
  │    │
  │    └─> FOR each message in session.messages:
  │         │
  │         ├─> IF user_message exists:
  │         │    └─> post_message(AddMessageRequest(...))
  │         │
  │         └─> IF assistant_response exists:
  │              └─> post_message(AddMessageRequest(...))
  │
  └─> Display welcome message
       └─> post_message(AddMessageRequest("system", welcome_text))
```

---

## IPC Request Flow (User Sends Message)

### User Input → Bridge → LLM → Streaming Response

```
USER: Types message, presses Ctrl+Enter
  │
  └─> RPClientApp.action_submit_message()
       │
       ├─> Generate UUIDs
       │    ├─> _user_message_id
       │    └─> _streaming_message_id
       │
       ├─> Display user message
       │    └─> post_message(AddMessageRequest(sender="you", ...))
       │         └─> ChatDisplay.handle_add_message()
       │
       ├─> Clear text_area
       │
       └─> IF connected:
            │
            ├─> Initialize streaming buffer
            │    └─> _streaming_buffer = ""
            │
            ├─> Create empty assistant message (for streaming updates)
            │    └─> post_message(AddMessageRequest(sender="claude", content="", ...))
            │
            └─> ipc_client.send_request_async(
                    IPCMessageType.SEND_MESSAGE,
                    callback=_handle_llm_response,
                    streaming_callback=_handle_streaming_chunk,
                    user_message=message
                )
                [File: src/infrastructure/ipc/socket_client.py]
                │
                └─> SENDS IPC REQUEST TO BRIDGE
                     │
                     ├─> SocketClient serializes request to JSON
                     ├─> Sends over socket
                     │
                     └─> [ARRIVES AT BRIDGE PROCESS]


BRIDGE PROCESS: Receives IPC request
  │
  └─> SocketServer._handle_client()
       │
       └─> BridgeService._handle_request(request)
            │
            ├─> Parse: IPCMessageType(request.type)
            │    └─> IPCMessageType.SEND_MESSAGE
            │
            ├─> Lookup handler in HANDLER_REGISTRY
            │    [File: src/presentation/bridge/handlers/__init__.py]
            │    └─> Returns: MessageHandler class
            │
            └─> Create handler instance
                 │
                 └─> handler = MessageHandler(bridge_service)
                      │
                      └─> handler.handle(request)
                           [File: src/presentation/bridge/handlers/message_handler.py]
                           │
                           ├─> Extract: user_message from request.data
                           │
                           ├─> Get LLM client
                           │    └─> bridge.primary_client
                           │
                           ├─> Build prompt
                           │    ├─> Load context (entities, state, etc.)
                           │    └─> Format for LLM
                           │
                           └─> Call LLM with streaming
                                │
                                ├─> primary_client.call_llm(
                                │        prompt=prompt,
                                │        max_tokens=...,
                                │        stream=True
                                │    )
                                │    │
                                │    └─> FOR each chunk in stream:
                                │         │
                                │         ├─> Yield chunk to handler
                                │         │
                                │         └─> handler sends streaming chunk back
                                │              │
                                │              └─> create_streaming_chunk(chunk)
                                │                   └─> Serialized to JSON
                                │                        └─> Sent back over socket
                                │                             │
                                │                             └─> [ARRIVES AT TUI PROCESS]


TUI PROCESS: Receives streaming chunk
  │
  └─> SocketClient async thread receives chunk
       │
       └─> Calls: streaming_callback(chunk)
            │
            └─> RPClientApp._handle_streaming_chunk(chunk)
                 │
                 ├─> Accumulate: _streaming_buffer += chunk
                 │
                 └─> post_message(
                          UpdateMessageRequest(
                              message_id=_streaming_message_id,
                              chunk=chunk
                          )
                     )
                     │
                     └─> ChatDisplay.handle_update_message()
                          └─> Appends chunk to message content
                               └─> UI updates in real-time


BRIDGE PROCESS: LLM stream completes
  │
  └─> MessageHandler.handle() completes
       │
       ├─> Send final response
       │    └─> create_response(request_id, success=True, data={...})
       │         └─> Serialized to JSON
       │              └─> Sent back over socket
       │                   │
       │                   └─> [ARRIVES AT TUI PROCESS]


TUI PROCESS: Receives final response
  │
  └─> SocketClient async thread receives response
       │
       └─> Calls: callback(response)
            │
            └─> RPClientApp._handle_llm_response(response)
                 │
                 └─> IF response.success:
                      └─> Log completion
```

---

## Agent System Initialization (Bridge Side)

**Triggered by:** `create_automation_service(rp_dir, bridge)` in BridgeService._initialize_services()

```
create_automation_service(rp_dir, bridge)
  [File: src/automation/factory.py]
  │
  ├─> Load configuration
  │    └─> ConfigLoader(rp_dir).load()
  │
  ├─> Create AutomationService instance
  │    └─> AutomationService(
  │             rp_dir=rp_dir,
  │             config=config,
  │             bridge=bridge
  │        )
  │        │
  │        └─> [File: src/automation/services/automation_service.py]
  │             │
  │             ├─> Initialize agent registries
  │             │    ├─> ImmediateAgentStrategy
  │             │    └─> BackgroundAgentStrategy
  │             │
  │             ├─> Load agent configurations
  │             │    └─> From config["automation"]["agents"]
  │             │
  │             └─> Register agents with strategies
  │                  [→ TO BE TRACED IN PHASE 1.5]
  │
  └─> RETURNS: AutomationService instance
```

**Note:** Full agent system trace deferred to Phase 1.5 (next step)

---

## Process Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN PROCESS (launch.py)                                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  RPClientApp (TUI)                                   │   │
│  │  ├─ StatePaths                                       │   │
│  │  ├─ SessionRepository                                │   │
│  │  ├─ SocketClient ───────────────┐                    │   │
│  │  └─ UI Components                │                   │   │
│  │     ├─ ChatDisplay                │                  │   │
│  │     ├─ ContextPanel               │                  │   │
│  │     ├─ EntityManager              │ IPC Socket       │   │
│  │     └─ SettingsOverlay            │ (localhost:5555) │   │
│  └──────────────────────────────────┼───────────────────┘   │
│                                      │                       │
└──────────────────────────────────────┼───────────────────────┘
                                       │
                                       │ IPC Communication
                                       │ (JSON over socket)
                                       │
┌──────────────────────────────────────┼───────────────────────┐
│  BRIDGE PROCESS (multiprocessing)   │                       │
│                                      │                       │
│  ┌──────────────────────────────────┼───────────────────┐   │
│  │  BridgeService                   │                   │   │
│  │  │                                │                   │   │
│  │  ├─ SocketServer ─────────────────┘                  │   │
│  │  │   └─ Listens on localhost:5555                    │   │
│  │  │                                                    │   │
│  │  ├─ Services                                          │   │
│  │  │   ├─ ConfigLoader                                 │   │
│  │  │   ├─ AutomationService (Agents)                   │   │
│  │  │   ├─ EntityService                                │   │
│  │  │   ├─ SessionRepository                            │   │
│  │  │   ├─ SessionWriteBack                             │   │
│  │  │   └─ ChatlogOrganizer                             │   │
│  │  │                                                    │   │
│  │  ├─ LLM Clients                                       │   │
│  │  │   ├─ primary_client (Claude/OpenAI/etc.)          │   │
│  │  │   └─ secondary_client (for automation)            │   │
│  │  │                                                    │   │
│  │  └─ Request Handlers (HANDLER_REGISTRY)              │   │
│  │       ├─ MessageHandler                              │   │
│  │       ├─ EntityHandler                               │   │
│  │       ├─ SettingsHandler                             │   │
│  │       └─ ... (other handlers)                        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Service Initialization Order

### Bridge Process (7+ services):
1. ConfigLoader
2. AutomationService (includes all agents)
3. EntityService
4. SessionStateService
5. SessionRepository
6. SessionWriteBack
7. ChatlogOrganizer
8. LLM Clients (primary + optional secondary)
9. SocketServer

### TUI Process (4 services):
1. StatePaths
2. PythonLoggingService
3. SessionStateService
4. SessionRepository

### Total Services at Runtime: 11-13 core services across both processes

---

## Next Traces Required (Phase 1.5)

**CRITICAL - Agent System:**
1. `create_automation_service()` detailed trace
   - File: `src/automation/factory.py`
2. `AutomationService` initialization
   - File: `src/automation/services/automation_service.py`
3. Agent strategy initialization
   - `ImmediateAgentStrategy`
   - `BackgroundAgentStrategy`
4. Individual agent registration
5. Agent execution flows

---

**Analysis Complete:** Phase 1.4 - Runtime Call Graph
**Next Step:** Phase 1.5 - Trace Agent Execution Flows
