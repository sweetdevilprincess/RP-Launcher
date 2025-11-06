"""Bridge Service - Connects TUI to Automation System.

This module implements the bridge that runs as a separate process,
handling requests from the TUI and routing them to the refactored
automation system.
"""

from pathlib import Path
from typing import Optional

from src.automation.contracts import AutomationContext
from src.automation.factory import create_automation_service
from src.automation.services import AutomationService
from src.automation.templates import TemplateRegistry
from src.domain.entities.entity_service import EntityService
from src.domain.sessions import ChatlogOrganizer, SessionRepository, SessionWriteBack
from src.infrastructure.config import ConfigLoader
from src.infrastructure.filesystem import StatePaths
from src.infrastructure.ipc import (
    IPCMessageType,
    IPCRequest,
    SocketServer,
    create_error_response,
    create_response,
    create_streaming_chunk,
    create_streaming_done,
)
from src.infrastructure.llm import LLMClient
from src.infrastructure.llm.registry import get_provider, list_providers
from src.infrastructure.sessions.session_state_service import SessionStateService
from src.shared.logging import get_logger
from src.wip import WipExecutor

from .handlers import HANDLER_REGISTRY


class BridgeService:
    """Bridge service for TUI-to-Automation communication.

    The bridge runs as a separate process and:
    - Starts a socket server for IPC
    - Initializes refactored automation services
    - Routes TUI requests to appropriate handlers
    - Manages LLM client instances
    """

    def __init__(self, rp_dir: Path, host: str = "127.0.0.1", port: int = 5555):
        """Initialize bridge service.

        Args:
            rp_dir: RP directory path
            host: Socket server host
            port: Socket server port
        """
        self.rp_dir = rp_dir
        self.host = host
        self.port = port

        # Socket server
        self.socket_server: Optional[SocketServer] = None

        # Refactored services
        self.config_loader: Optional[ConfigLoader] = None
        self.automation_service: Optional[AutomationService] = None
        self.entity_service: Optional[EntityService] = None
        self.session_state_service: Optional[SessionStateService] = None
        self.session_repository: Optional[SessionRepository] = None
        self.session_writeback: Optional[SessionWriteBack] = None
        self.chatlog_organizer: Optional[ChatlogOrganizer] = None

        # LLM clients (dual-provider support)
        self.primary_client: Optional[LLMClient] = None
        self.secondary_client: Optional[LLMClient] = None
        self.llm_routing: dict = {}  # LLM routing configuration

        # Backwards compatibility (deprecated - use primary_client)
        self.llm_client: Optional[LLMClient] = None

        # State
        self.current_provider: Optional[str] = None
        self.testing_mode: bool = False
        self.logger = get_logger("bridge")

        # WIP testing system
        wip_root = Path(__file__).parents[2] / "wip"  # src/wip/
        self.wip_executor: Optional[WipExecutor] = WipExecutor(wip_root)

    def start(self) -> None:
        """Start the bridge service."""
        print("[START] Starting Bridge Service...")
        print(f"[INFO] RP Directory: {self.rp_dir}")

        # Load configuration
        self._load_configuration()

        # Initialize services
        self._initialize_services()

        # Start socket server
        self._start_socket_server()

        print("[OK] Bridge Service ready")

    def _load_configuration(self) -> None:
        """Load configuration from RP directory."""
        print("[CONFIG] Loading configuration...")
        self.config_loader = ConfigLoader(self.rp_dir)
        config = self.config_loader.load()

        # Validate RP directory structure
        errors = self.config_loader.validate_rp_directory()
        if errors:
            print("[WARNING] RP directory validation warnings:")
            for error in errors:
                print(f"          - {error}")

        print(f"[OK] Configuration loaded (version: {config.get('version', 'unknown')})")

    def _initialize_services(self) -> None:
        """Initialize refactored automation services."""
        print("[INIT] Initializing services...")

        # Automation service (using factory with bridge reference for agent LLM access)
        self.automation_service = create_automation_service(self.rp_dir, bridge=self)
        print("[OK] Automation service initialized")

        # Entity service
        self.entity_service = EntityService()
        print("[OK] Entity service initialized")

        # Session state service
        self.session_state_service = SessionStateService(logger=self.logger)
        print("[OK] Session state service initialized")

        # Session repository and write-back service
        paths = StatePaths(rp_dir=self.rp_dir)
        self.session_repository = SessionRepository(
            paths=paths,
            logger=self.logger,
            session_state_service=self.session_state_service
        )
        self.session_writeback = SessionWriteBack(
            repository=self.session_repository,
            logger=self.logger
        )
        self.chatlog_organizer = ChatlogOrganizer(
            paths=paths,
            logger=self.logger,
            repository=self.session_repository
        )
        print("[OK] Session repository initialized")

        # LLM clients (get primary/secondary from routing config) - optional, may fail if no providers configured
        try:
            self._initialize_llm_clients()
        except Exception as e:
            print(f"[WARNING] LLM client initialization failed: {e}")
            import traceback
            traceback.print_exc()
            print("[INFO] For Claude SDK: Run setup.sh/setup.bat to install Node.js dependencies")
            print("[INFO] For API providers: Configure an API key in settings")
            print("[INFO] Or enable Testing Mode (F8) to continue without LLM")
            print("[INFO] Bridge will continue but message sending will require configuration")

    def _initialize_llm_clients(self) -> None:
        """Initialize primary and secondary LLM clients based on routing config."""
        if self.testing_mode:
            # Use mock client in testing mode
            from src.infrastructure.llm.mock_client import MockLLMClient
            mock_client = MockLLMClient()
            self.primary_client = mock_client
            self.secondary_client = mock_client
            self.llm_client = mock_client  # Backwards compatibility
            self.current_provider = "mock"
            print("[TEST] Testing mode: Using mock LLM client")
            return

        # Load routing config
        config = self.config_loader.load()
        from src.infrastructure.config.defaults import LLM_ROUTING_DEFAULTS
        self.llm_routing = config.get("llm", LLM_ROUTING_DEFAULTS)

        # Get primary provider
        primary_provider = self.llm_routing.get("primary_provider")
        if not primary_provider:
            # Fallback: find first enabled LLM module
            primary_provider = self._find_first_enabled_provider(config)

        if not primary_provider:
            raise RuntimeError("No LLM provider configured")

        # Initialize primary client
        self.primary_client = self._create_client(primary_provider)
        self.current_provider = primary_provider
        print(f"[OK] Primary LLM initialized: {primary_provider}")

        # Initialize secondary client
        secondary_provider = self.llm_routing.get("secondary_provider", "")
        use_secondary = self.llm_routing.get("use_secondary_for_automation", False)

        # Only create separate secondary client if toggle is ON and provider is different
        if use_secondary and secondary_provider and secondary_provider != primary_provider:
            # Different provider for secondary (and toggle is ON)
            try:
                self.secondary_client = self._create_client(secondary_provider)
                print(f"[OK] Secondary LLM initialized: {secondary_provider}")
            except Exception as e:
                print(f"[WARNING] Secondary LLM initialization failed: {e}")
                print(f"[INFO] Falling back to primary LLM for automation")
                self.secondary_client = self.primary_client
        else:
            # Use primary for everything (toggle OFF or no secondary configured)
            self.secondary_client = self.primary_client
            if secondary_provider and use_secondary:
                print(f"[OK] Secondary LLM uses same instance as primary")
            else:
                print(f"[OK] Using primary LLM for all operations (secondary disabled)")

        # Backwards compatibility
        self.llm_client = self.primary_client

    def _find_first_enabled_provider(self, config: dict) -> Optional[str]:
        """Find first enabled LLM provider in modules config.

        Args:
            config: Full configuration dict

        Returns:
            Provider name or None if none enabled
        """
        modules = config.get("modules", {})
        llm_providers = [
            "claude_api_client", "claude_sdk_client",
            "openai_client", "openrouter_client"
        ]

        for module_name, module_config in modules.items():
            if module_config.get("enabled") and module_name in llm_providers:
                return module_name

        return None

    def _create_client(self, provider_name: str) -> LLMClient:
        """Create an LLM client instance for the given provider.

        Args:
            provider_name: Provider module name (e.g., "claude_sdk_client")

        Returns:
            Initialized LLM client instance

        Raises:
            RuntimeError: If provider not found or creation fails
        """
        config = self.config_loader.load()

        # Check if Claude API client has use_sdk enabled
        if provider_name == "claude_api_client":
            claude_config = config.get("modules", {}).get("claude_api_client", {}).get("config", {})
            use_sdk = claude_config.get("use_sdk", False)
            if use_sdk:
                provider_name = "claude_sdk_client"
                print("[SDK] use_sdk enabled - switching to claude_sdk_client")

        # Get provider from registry
        provider_spec = get_provider(provider_name)
        if not provider_spec:
            raise RuntimeError(f"Provider not found: {provider_name}")

        # Extract module-specific config and flatten for factory
        module_config = config.get("modules", {}).get(provider_name, {}).get("config", {})

        # Add runtime metadata required by factories
        factory_config = {
            **module_config,  # Provider settings at root level
            "rp_dir": self.rp_dir,  # Runtime path to RP directory
            "project_root": self.rp_dir,  # Some factories expect this name
        }

        # Create client using factory
        return provider_spec.factory(factory_config)

    def _start_socket_server(self) -> None:
        """Start socket server for IPC."""
        print(f"[SOCKET] Starting socket server on {self.host}:{self.port}...")

        self.socket_server = SocketServer(self.host, self.port)
        self.socket_server.set_handler(self._handle_request)
        self.socket_server.start()

        print("[OK] Socket server started")

    def _handle_request(self, request: IPCRequest) -> str:
        """Handle incoming IPC request using handler registry.

        Args:
            request: Request from TUI

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        try:
            # Look up handler in registry
            handler_class = HANDLER_REGISTRY.get(request_type)

            if handler_class:
                # Create handler instance and delegate
                handler = handler_class(self)
                return handler.handle(request)
            else:
                return create_error_response(
                    request.request_id,
                    f"Unknown request type: {request.type}"
                )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Error handling request: {str(e)}"
            )

    # ==========================================================================
    # Service Lifecycle
    # ==========================================================================

    def stop(self) -> None:
        """Stop the bridge service."""
        print("[STOP] Stopping Bridge Service...")

        if self.socket_server:
            self.socket_server.stop()

        print("[OK] Bridge Service stopped")

    def run(self) -> None:
        """Run the bridge service (blocks until stopped)."""
        self.start()

        try:
            # Keep running until stopped
            while self.socket_server and self.socket_server.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[WARNING] Interrupted by user")
        finally:
            self.stop()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
