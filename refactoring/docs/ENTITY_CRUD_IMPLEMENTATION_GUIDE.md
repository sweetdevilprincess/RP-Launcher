# Entity CRUD Implementation Guide

**Status:** Not Yet Implemented
**Priority:** Medium
**Estimated Effort:** ~300-400 lines of code

---

## Current State

### What Works ✅
- **GET_ENTITIES** - EntityHandler properly loads all entities from filesystem
- **EntityManager** - TUI displays entities and has edit UI
- Local state updates work (editing updates UI)

### What's Missing ❌
- **CREATE_ENTITY** - Returns "not yet implemented"
- **UPDATE_ENTITY** - Returns "not yet implemented"
- **DELETE_ENTITY** - Returns "not yet implemented"
- No persistence to disk

---

## Implementation Plan

### Phase 1: Understand Entity File Format

Entities are stored as JSON files in the RP directory:

**File Naming Conventions:**
```
entities/
  character_*.json  - Characters
  location_*.json   - Locations
  organization_*.json - Organizations
  item_*.json       - Items
```

**Example Character JSON:**
```json
{
  "name": "Aria the Brave",
  "basics": {
    "age": "25",
    "gender": "Female",
    "occupation": "Knight"
  },
  "appearance": {
    "height": "5'8\"",
    "build": "Athletic",
    "features": "Red hair, green eyes"
  },
  "personality": {
    "traits": "Courageous, loyal, impulsive",
    "core_mandate": "Protect the innocent"
  },
  "preferences": {
    "likes": "Training, helping others",
    "dislikes": "Injustice, cowardice"
  },
  "abilities": {
    "combat": "Expert swordsman",
    "magic": "Minor healing"
  },
  "background": {
    "origin": "Kingdom of Eldoria",
    "history": "Trained at the Royal Academy..."
  },
  "metadata": {
    "tags": ["protagonist", "combat"],
    "created": "2025-10-23",
    "version": "1.0"
  }
}
```

---

### Phase 2: Check Repository Methods

First, we need to check if `FixtureEntityRepository` has save methods:

**File to Check:** `src/domain/entities/entity_repository.py`

**Methods Needed:**
```python
class FixtureEntityRepository:
    def save_character(self, character: CharacterEntity) -> None:
        """Save character to JSON file"""

    def save_location(self, location: LocationEntity) -> None:
        """Save location to JSON file"""

    def save_organization(self, organization: OrganizationEntity) -> None:
        """Save organization to JSON file"""

    def save_item(self, item: ItemEntity) -> None:
        """Save item to JSON file"""

    def delete_character(self, name: str) -> None:
        """Delete character JSON file"""

    # ... similar for other types
```

**If these methods DON'T exist**, we need to implement them in the repository first.

---

### Phase 3: Implement Repository Save Methods

**File:** `src/domain/entities/entity_repository.py`

```python
def save_character(self, character: CharacterEntity) -> None:
    """Save character entity to JSON file.

    Args:
        character: CharacterEntity to save

    Raises:
        IOError: If unable to write file
    """
    # Generate filename from entity name
    filename = f"character_{character.name.lower().replace(' ', '_')}.json"

    # Determine save path (try entities/ first, then characters/)
    entities_dir = self.rp_dir / "entities"
    characters_dir = self.rp_dir / "characters"

    if entities_dir.exists():
        save_path = entities_dir / filename
    elif characters_dir.exists():
        save_path = characters_dir / filename
    else:
        # Create entities directory if neither exists
        entities_dir.mkdir(parents=True, exist_ok=True)
        save_path = entities_dir / filename

    # Serialize entity to dict
    entity_dict = {
        "name": character.name,
        "basics": dict(character.basics),
        "appearance": dict(character.appearance),
        "personality": dict(character.personality),
        "preferences": dict(character.preferences),
        "abilities": dict(character.abilities),
        "background": dict(character.background),
        "metadata": dict(character.metadata),
    }

    # Write to file with pretty formatting
    import json
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(entity_dict, f, indent=2, ensure_ascii=False)

    # Reload cache
    self._load_entities()

def delete_character(self, name: str) -> None:
    """Delete character entity file.

    Args:
        name: Character name

    Raises:
        FileNotFoundError: If entity doesn't exist
    """
    filename = f"character_{name.lower().replace(' ', '_')}.json"

    # Check both possible directories
    entities_dir = self.rp_dir / "entities"
    characters_dir = self.rp_dir / "characters"

    file_path = None
    if (entities_dir / filename).exists():
        file_path = entities_dir / filename
    elif (characters_dir / filename).exists():
        file_path = characters_dir / filename

    if not file_path:
        raise FileNotFoundError(f"Character '{name}' not found")

    # Delete file
    file_path.unlink()

    # Reload cache
    self._load_entities()

# Repeat for: save_location, save_organization, save_item
# Repeat for: delete_location, delete_organization, delete_item
```

**Estimated:** ~200 lines (50 lines × 4 entity types)

---

### Phase 4: Implement EntityHandler Methods

**File:** `src/presentation/bridge/handlers/entity_handler.py`

#### 4.1 CREATE_ENTITY

```python
def _handle_create_entity(self, request: IPCRequest) -> str:
    """Handle CREATE_ENTITY request - create new entity."""
    entity_data = request.data.get("entity_data")
    if not entity_data:
        return create_error_response(request.request_id, "Missing entity_data")

    entity_type = entity_data.get("type")
    if not entity_type:
        return create_error_response(request.request_id, "Missing entity type")

    try:
        if entity_type == "character":
            # Parse entity data into CharacterEntity
            from src.domain.entities.entity_parser import parse_character
            character = parse_character(entity_data)

            # Save via repository
            self.bridge.entity_service._repository.save_character(character)

            entity_id = f"char_{character.name.lower().replace(' ', '_')}"
            return create_response(
                request.request_id,
                entity_id=entity_id,
                message=f"Created character '{character.name}'"
            )

        elif entity_type == "location":
            from src.domain.entities.entity_parser import parse_location
            location = parse_location(entity_data)
            self.bridge.entity_service._repository.save_location(location)

            entity_id = f"loc_{location.name.lower().replace(' ', '_')}"
            return create_response(
                request.request_id,
                entity_id=entity_id,
                message=f"Created location '{location.name}'"
            )

        elif entity_type == "organization":
            from src.domain.entities.entity_parser import parse_organization
            organization = parse_organization(entity_data)
            self.bridge.entity_service._repository.save_organization(organization)

            entity_id = f"org_{organization.name.lower().replace(' ', '_')}"
            return create_response(
                request.request_id,
                entity_id=entity_id,
                message=f"Created organization '{organization.name}'"
            )

        elif entity_type == "item":
            from src.domain.entities.entity_parser import parse_item
            item = parse_item(entity_data)
            self.bridge.entity_service._repository.save_item(item)

            entity_id = f"item_{item.name.lower().replace(' ', '_')}"
            return create_response(
                request.request_id,
                entity_id=entity_id,
                message=f"Created item '{item.name}'"
            )
        else:
            return create_error_response(
                request.request_id,
                f"Unknown entity type: {entity_type}"
            )

    except Exception as e:
        return create_error_response(
            request.request_id,
            f"Failed to create entity: {str(e)}"
        )
```

#### 4.2 UPDATE_ENTITY

```python
def _handle_update_entity(self, request: IPCRequest) -> str:
    """Handle UPDATE_ENTITY request - update existing entity."""
    entity_id = request.data.get("entity_id")
    entity_data = request.data.get("entity_data")

    if not entity_id or not entity_data:
        return create_error_response(
            request.request_id,
            "Missing entity_id or entity_data"
        )

    entity_type = entity_data.get("type")
    if not entity_type:
        return create_error_response(request.request_id, "Missing entity type")

    try:
        # Same logic as CREATE but saves over existing file
        if entity_type == "character":
            from src.domain.entities.entity_parser import parse_character
            character = parse_character(entity_data)
            self.bridge.entity_service._repository.save_character(character)

            return create_response(
                request.request_id,
                entity_id=entity_id,
                message=f"Updated character '{character.name}'"
            )

        # ... similar for location, organization, item

    except Exception as e:
        return create_error_response(
            request.request_id,
            f"Failed to update entity: {str(e)}"
        )
```

#### 4.3 DELETE_ENTITY

```python
def _handle_delete_entity(self, request: IPCRequest) -> str:
    """Handle DELETE_ENTITY request - delete entity."""
    entity_id = request.data.get("entity_id")
    entity_type = request.data.get("entity_type")

    if not entity_id:
        return create_error_response(request.request_id, "Missing entity_id")

    try:
        # Extract entity name from entity_id
        # entity_id format: "char_aria_the_brave"
        name_part = entity_id.split('_', 1)[1]  # "aria_the_brave"
        entity_name = name_part.replace('_', ' ').title()  # "Aria The Brave"

        # Delete via repository
        if entity_id.startswith('char_'):
            self.bridge.entity_service._repository.delete_character(entity_name)
        elif entity_id.startswith('loc_'):
            self.bridge.entity_service._repository.delete_location(entity_name)
        elif entity_id.startswith('org_'):
            self.bridge.entity_service._repository.delete_organization(entity_name)
        elif entity_id.startswith('item_'):
            self.bridge.entity_service._repository.delete_item(entity_name)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown entity type from ID: {entity_id}"
            )

        return create_response(
            request.request_id,
            entity_id=entity_id,
            message=f"Deleted entity '{entity_name}'"
        )

    except FileNotFoundError:
        return create_error_response(
            request.request_id,
            f"Entity not found: {entity_id}"
        )
    except Exception as e:
        return create_error_response(
            request.request_id,
            f"Failed to delete entity: {str(e)}"
        )
```

**Estimated:** ~150 lines

---

### Phase 5: Update TUI EntityManager

**File:** `src/presentation/tui/components/entity_manager.py`

Update the `save_entity` method to actually call the Bridge:

```python
def save_entity(self, entity_id: str, entity_data: dict) -> None:
    """Save entity to Bridge via IPC."""
    if not self.app.ipc_client or not self.app.connected:
        self.app.notify("Not connected to Bridge", severity="warning")
        return

    try:
        # Determine if this is create or update
        is_new = entity_id not in self.entities

        if is_new:
            response = self.app.ipc_client.send_request(
                IPCMessageType.CREATE_ENTITY,
                timeout=5.0,
                entity_data=entity_data
            )
        else:
            response = self.app.ipc_client.send_request(
                IPCMessageType.UPDATE_ENTITY,
                timeout=5.0,
                entity_id=entity_id,
                entity_data=entity_data
            )

        if response.success:
            # Update local cache
            self.entities[entity_id] = entity_data

            # Refresh UI
            entity_list = self.query_one("#entity-list", _EntityList)
            entity_list.entities = self.entities
            entity_list.refresh_list()

            # Notify user
            action = "Created" if is_new else "Updated"
            self.app.notify(f"{action} {entity_data['name']}", severity="information")

            # Post message
            self.post_message(self.EntitySaved(entity_id, entity_data))
        else:
            self.app.notify(f"Failed to save: {response.error_message}", severity="error")

    except Exception as e:
        self.app.notify(f"Error saving entity: {e}", severity="error")
```

Add delete functionality:

```python
def delete_entity(self, entity_id: str) -> None:
    """Delete entity via Bridge IPC."""
    if not self.app.ipc_client or not self.app.connected:
        self.app.notify("Not connected to Bridge", severity="warning")
        return

    try:
        response = self.app.ipc_client.send_request(
            IPCMessageType.DELETE_ENTITY,
            timeout=5.0,
            entity_id=entity_id
        )

        if response.success:
            # Remove from local cache
            if entity_id in self.entities:
                entity_name = self.entities[entity_id].get('name', entity_id)
                del self.entities[entity_id]

                # Refresh UI
                entity_list = self.query_one("#entity-list", _EntityList)
                entity_list.entities = self.entities
                entity_list.refresh_list()

                # Close drawer if this entity is open
                if self.current_entity_id == entity_id:
                    self.hide_drawer()

                self.app.notify(f"Deleted {entity_name}", severity="information")
        else:
            self.app.notify(f"Failed to delete: {response.error_message}", severity="error")

    except Exception as e:
        self.app.notify(f"Error deleting entity: {e}", severity="error")
```

**Estimated:** ~50 lines

---

## Implementation Checklist

### Step 1: Check Repository ✓
- [ ] Open `src/domain/entities/entity_repository.py`
- [ ] Check if save/delete methods exist
- [ ] If not, implement them (Phase 3)

### Step 2: Implement EntityHandler ✓
- [ ] Implement `_handle_create_entity()` (~40 lines)
- [ ] Implement `_handle_update_entity()` (~40 lines)
- [ ] Implement `_handle_delete_entity()` (~30 lines)
- [ ] Test with IPC calls

### Step 3: Update TUI ✓
- [ ] Update `save_entity()` to call Bridge (~30 lines)
- [ ] Add `delete_entity()` method (~20 lines)
- [ ] Add delete button to entity drawer UI
- [ ] Test in TUI

### Step 4: Testing ✓
- [ ] Test create new character
- [ ] Test update existing character
- [ ] Test delete character
- [ ] Verify file is created/updated/deleted in `entities/` directory
- [ ] Test with locations, organizations, items
- [ ] Test error cases (invalid data, missing fields)

---

## Error Handling Requirements

### Validation
- **Name required:** All entities must have a name
- **Type validation:** Entity type must be valid (character, location, organization, item)
- **Field validation:** Required fields for each type must be present

### File System
- **Directory creation:** Auto-create `entities/` if it doesn't exist
- **File conflicts:** Handle existing files gracefully (update vs create)
- **Permissions:** Handle read-only filesystems
- **Concurrent access:** Handle multiple edits (last write wins)

### User Feedback
- **Success notifications:** "Created character 'Aria the Brave'"
- **Error notifications:** "Failed to save: Invalid entity data"
- **Confirmation dialogs:** "Are you sure you want to delete 'Aria the Brave'?"

---

## Total Estimated Effort

**Repository Implementation:** ~200 lines
**Handler Implementation:** ~150 lines
**TUI Updates:** ~50 lines
**Testing:** ~2 hours

**Total:** ~400 lines of code, ~4-6 hours of work

---

## Notes

- The repository will need to handle both `entities/` and `characters/` directories (legacy support)
- File naming must be consistent: `character_entity_name.json`
- Entity IDs use format: `char_entity_name`, `loc_entity_name`, etc.
- All changes should be atomic (write to temp file, then rename)
- Consider adding backup functionality before overwriting

---

**Next Document:** `BRANCH_OPERATIONS_IMPLEMENTATION_GUIDE.md`
