"""Entity Handler - Handles entity management IPC requests.

This handler processes entity-related requests including:
- GET_ENTITIES: List all entities (characters, locations, organizations, items)
- CREATE_ENTITY: Create new entity
- UPDATE_ENTITY: Update existing entity
- DELETE_ENTITY: Delete entity
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class EntityHandler(BaseHandler):
    """Handler for entity management operations.

    Delegates to bridge.entity_service for all entity operations.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route entity request to appropriate handler method.

        Args:
            request: IPC request with entity operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_ENTITIES:
            return self._handle_get_entities(request)
        elif request_type == IPCMessageType.CREATE_ENTITY:
            return self._handle_create_entity(request)
        elif request_type == IPCMessageType.UPDATE_ENTITY:
            return self._handle_update_entity(request)
        elif request_type == IPCMessageType.DELETE_ENTITY:
            return self._handle_delete_entity(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown entity request type: {request.type}"
            )

    def _handle_get_entities(self, request: IPCRequest) -> str:
        """Handle GET_ENTITIES request - get all entities from filesystem."""
        try:
            # Get all entities using EntityService
            characters = self.bridge.entity_service.list_characters()
            locations = self.bridge.entity_service.list_locations()
            organizations = self.bridge.entity_service.list_organizations()
            items = self.bridge.entity_service.list_items()

            # Format entities for TUI
            entities = {}

            # Add characters
            for char in characters:
                entity_id = f"char_{char.name.lower().replace(' ', '_')}"
                entities[entity_id] = {
                    "name": char.name,
                    "type": "character",
                    "tags": char.metadata.get("tags", []),
                    "basics": dict(char.basics) if char.basics else {},
                    "appearance": dict(char.appearance) if char.appearance else {},
                    "personality": dict(char.personality) if char.personality else {},
                    "preferences": dict(char.preferences) if char.preferences else {},
                    "abilities": dict(char.abilities) if char.abilities else {},
                    "background": dict(char.background) if char.background else {},
                    "metadata": dict(char.metadata) if char.metadata else {},
                }

            # Add locations
            for loc in locations:
                entity_id = f"loc_{loc.name.lower().replace(' ', '_')}"
                entities[entity_id] = {
                    "name": loc.name,
                    "type": "location",
                    "tags": loc.metadata.get("tags", []),
                    "basics": dict(loc.basics) if loc.basics else {},
                    "geography": dict(loc.geography) if loc.geography else {},
                    "facilities": dict(loc.facilities) if loc.facilities else {},
                    "culture": dict(loc.culture) if loc.culture else {},
                    "hooks": dict(loc.hooks) if loc.hooks else {},
                    "metadata": dict(loc.metadata) if loc.metadata else {},
                }

            # Add organizations
            for org in organizations:
                entity_id = f"org_{org.name.lower().replace(' ', '_')}"
                entities[entity_id] = {
                    "name": org.name,
                    "type": "organization",
                    "tags": org.metadata.get("tags", []),
                    "basics": dict(org.basics) if org.basics else {},
                    "structure": dict(org.structure) if org.structure else {},
                    "resources": dict(org.resources) if org.resources else {},
                    "relations": dict(org.relations) if org.relations else {},
                    "operations": dict(org.operations) if org.operations else {},
                    "metadata": dict(org.metadata) if org.metadata else {},
                }

            # Add items
            for item in items:
                entity_id = f"item_{item.name.lower().replace(' ', '_')}"
                entities[entity_id] = {
                    "name": item.name,
                    "type": "item",
                    "tags": item.metadata.get("tags", []),
                    "basics": dict(item.basics) if item.basics else {},
                    "attributes": dict(item.attributes) if item.attributes else {},
                    "usage": dict(item.usage) if item.usage else {},
                    "metadata": dict(item.metadata) if item.metadata else {},
                }

            return create_response(
                request.request_id,
                entities=entities,
                count=len(entities)
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to get entities: {str(e)}"
            )

    def _handle_create_entity(self, request: IPCRequest) -> str:
        """Handle CREATE_ENTITY request - create new entity."""
        # TODO: Implement entity creation
        return create_error_response(
            request.request_id,
            "Entity creation not yet implemented"
        )

    def _handle_update_entity(self, request: IPCRequest) -> str:
        """Handle UPDATE_ENTITY request - update existing entity."""
        # TODO: Implement entity updates
        return create_error_response(
            request.request_id,
            "Entity updates not yet implemented"
        )

    def _handle_delete_entity(self, request: IPCRequest) -> str:
        """Handle DELETE_ENTITY request - delete entity."""
        # TODO: Implement entity deletion
        return create_error_response(
            request.request_id,
            "Entity deletion not yet implemented"
        )


__all__ = ["EntityHandler"]
