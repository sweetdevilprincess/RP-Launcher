"""Bridge Handlers - IPC message handler modules.

This package contains all IPC message handlers for the Bridge service.
Each handler module is responsible for processing specific types of
IPC messages and delegating to appropriate bridge services.

Handler Pattern:
---------------
All handlers inherit from BaseHandler and implement the handle() method.
The HANDLER_REGISTRY maps IPCMessageType values to handler classes,
enabling clean request routing without large if/elif chains.

Architecture:
------------
    BridgeService
        ↓
    _handle_request()
        ↓
    HANDLER_REGISTRY lookup
        ↓
    Handler.handle(request)
        ↓
    Bridge services (entity_service, config_loader, etc.)

Usage:
-----
```python
from .handlers import HANDLER_REGISTRY

# In BridgeService._handle_request():
handler_class = HANDLER_REGISTRY.get(request_type)
if handler_class:
    handler = handler_class(self)
    return handler.handle(request)
```
"""

from src.infrastructure.ipc import IPCMessageType

from .base import BaseHandler
from .branch_handler import BranchHandler
from .entity_handler import EntityHandler
from .message_handler import MessageHandler
from .module_handler import ModuleHandler
from .provider_handler import ProviderHandler
from .settings_handler import SettingsHandler
from .system_handler import SystemHandler
from .template_handler import TemplateHandler
from .trigger_handler import TriggerHandler

# Handler Registry
# Maps IPCMessageType to handler class
# This will be populated incrementally as handlers are extracted
HANDLER_REGISTRY: dict[IPCMessageType, type[BaseHandler]] = {
    # Entity handlers
    IPCMessageType.GET_ENTITIES: EntityHandler,
    IPCMessageType.CREATE_ENTITY: EntityHandler,
    IPCMessageType.UPDATE_ENTITY: EntityHandler,
    IPCMessageType.DELETE_ENTITY: EntityHandler,

    # Branch handlers
    IPCMessageType.GET_BRANCHES: BranchHandler,
    IPCMessageType.CREATE_BRANCH: BranchHandler,
    IPCMessageType.SWITCH_BRANCH: BranchHandler,
    IPCMessageType.COMPARE_BRANCHES: BranchHandler,

    # Settings handlers
    IPCMessageType.GET_SETTINGS: SettingsHandler,
    IPCMessageType.UPDATE_SETTINGS: SettingsHandler,

    # Module handlers
    IPCMessageType.GET_MODULES: ModuleHandler,
    IPCMessageType.TOGGLE_MODULE: ModuleHandler,

    # Message handlers
    IPCMessageType.SEND_MESSAGE: MessageHandler,
    IPCMessageType.GET_STATE: MessageHandler,

    # Provider handlers
    IPCMessageType.GET_PROVIDERS: ProviderHandler,
    IPCMessageType.SET_PROVIDER: ProviderHandler,

    # Trigger handlers
    IPCMessageType.GET_TRIGGERS: TriggerHandler,
    IPCMessageType.SET_TRIGGER: TriggerHandler,

    # Template handlers
    IPCMessageType.GET_TEMPLATES: TemplateHandler,
    IPCMessageType.SET_TEMPLATE: TemplateHandler,

    # System handlers
    IPCMessageType.TEST_MODE: SystemHandler,
    IPCMessageType.PING: SystemHandler,
    IPCMessageType.SHUTDOWN: SystemHandler,
}

__all__ = [
    "BaseHandler",
    "HANDLER_REGISTRY",
]
