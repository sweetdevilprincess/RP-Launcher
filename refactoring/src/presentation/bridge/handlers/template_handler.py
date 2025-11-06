"""Template Handler - Handles narrative template management IPC requests.

This handler processes template-related requests including:
- GET_TEMPLATES: List available narrative templates
- SET_TEMPLATE: Set or enable narrative templates
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.automation.templates import TemplateRegistry
from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class TemplateHandler(BaseHandler):
    """Handler for narrative template management operations.

    Delegates to TemplateRegistry and bridge.config_loader for template operations.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route template request to appropriate handler method.

        Args:
            request: IPC request with template operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_TEMPLATES:
            return self._handle_get_templates(request)
        elif request_type == IPCMessageType.SET_TEMPLATE:
            return self._handle_set_template(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown template request type: {request.type}"
            )

    def _handle_get_templates(self, request: IPCRequest) -> str:
        """Handle GET_TEMPLATES request."""
        try:
            # Get template configuration
            templates_enabled = self.bridge.config_loader.get("narrative_template.enabled", True)
            template_dir_str = self.bridge.config_loader.get(
                "narrative_template.template_dir",
                "config/templates/prompts"
            )
            current_template = self.bridge.config_loader.get("narrative_template.current_template", None)

            # Build template directory path
            template_dir = self.bridge.rp_dir / template_dir_str

            # Get available templates using TemplateRegistry
            template_registry = TemplateRegistry(template_dir)
            available_templates = template_registry.list_available_templates()

            return create_response(
                request.request_id,
                templates={
                    "enabled": templates_enabled,
                    "available": available_templates,
                    "current": current_template,
                    "template_dir": str(template_dir),
                }
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to get templates: {str(e)}"
            )

    def _handle_set_template(self, request: IPCRequest) -> str:
        """Handle SET_TEMPLATE request."""
        template = request.data.get("template")
        enabled = request.data.get("enabled")  # Optional: to enable/disable templates

        try:
            # Update template enabled state if provided
            if enabled is not None:
                self.bridge.config_loader.set("narrative_template.enabled", enabled)

            # Update current template if provided
            if template:
                # Validate template exists
                template_dir_str = self.bridge.config_loader.get(
                    "narrative_template.template_dir",
                    "config/templates/prompts"
                )
                template_dir = self.bridge.rp_dir / template_dir_str
                template_registry = TemplateRegistry(template_dir)

                if not template_registry.has_template(template):
                    available = template_registry.list_available_templates()
                    return create_error_response(
                        request.request_id,
                        f"Template '{template}' not found. Available: {', '.join(available)}"
                    )

                # Update current template
                self.bridge.config_loader.set("narrative_template.current_template", template)

            # Persist changes
            self.bridge.config_loader.save()

            return create_response(
                request.request_id,
                template=template,
                enabled=enabled if enabled is not None else self.bridge.config_loader.get("narrative_template.enabled", True),
                message=f"Template settings updated" + (f": '{template}'" if template else "")
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to update template: {str(e)}"
            )


__all__ = ["TemplateHandler"]
