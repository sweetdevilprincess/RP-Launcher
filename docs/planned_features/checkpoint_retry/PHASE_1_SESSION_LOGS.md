# Phase 1: Session Log System - Implementation Guide

**Phase**: 1 (Core System)
**Goal**: Implement session log system with retry, branching, checkpointing, and switching
**Timeline**: 4-5 days
**Status**: Implementation
**Created**: 2025-10-17

---

## Table of Contents

1. [Overview](#overview)
2. [Session Log Format](#session-log-format)
3. [SessionManager API](#sessionmanager-api)
4. [Core Operation: copy_session()](#core-operation-copy_session)
5. [Command Implementations](#command-implementations)
6. [Tagging System](#tagging-system)
7. [Bridge Integration](#bridge-integration)
8. [TUI Integration](#tui-integration)
9. [Migration Strategy](#migration-strategy)
10. [Error Handling](#error-handling)
11. [Testing Checklist](#testing-checklist)

---

## Overview

### What We're Building

A session log system that treats the conversation history as the single source of truth. Retry, branching, and checkpointing are all the same operation: **copying a session up to a specific response number**.

### Key Insight

```python
# ALL features use this one operation:
copy_session(up_to_response, new_name, tags)

# Retry = copy without last response
retry() -> copy_session(current-1, "retry_TIMESTAMP", ["retry"])

# Branch = copy up to response N
branch(N, "name") -> copy_session(N, "name", ["branch"])

# Checkpoint = copy current state
checkpoint("name") -> copy_session(current, "name", ["checkpoint"])
```

### Architecture Shift

**Old Approach** (PHASE_1_SIMPLE_RETRY.md - OUTDATED):
- Modify chapter markdown files
- Parse and remove response blocks
- Complex text manipulation
- Separate agent cache file

**New Approach** (This Document):
- Session logs are JSON files
- Copy messages array
- Simple data operations
- Agent data embedded in session

### Benefits

✅ Single source of truth (session JSON)
✅ TUI reloads session file (no "erasing" needed)
✅ All features use same core operation
✅ Agent data embedded (no sync issues)
✅ Natural branching model
✅ Atomic operations (no partial failures)

---

## Session Log Format

### Complete Session Structure

```json
{
  "session_id": "main",
  "session_type": "active",
  "parent_session": null,
  "branch_point": null,
  "created": "2025-10-15T14:57:25",
  "last_modified": "2025-10-17T10:30:00",
  "current_response": 45,
  "tags": ["main-timeline"],
  "description": "",

  "rp_metadata": {
    "rp_name": "Lilith and Silas",
    "chapter": 1,
    "scene": "The Crimson Hour bar"
  },

  "messages": [
    {
      "response_num": 1,
      "timestamp": "2025-10-15T15:00:00",
      "chapter": 1,

      "user_message": "I approach the tattooed stranger at the bar...",
      "assistant_response": "Silas looked up as you approached...",

      "agent_data_background": {
        "scene_analysis": {...},
        "characters_in_scene": ["Lilith", "Silas"],
        "memories_created": [...],
        "relationship_changes": {...}
      },

      "agent_data_immediate": {
        "entities_to_load": ["Lilith", "Silas"],
        "relevant_memories": [],
        "tier_2_facts": {}
      },

      "model_info": {
        "model": "claude-sonnet-4",
        "temperature": 0.85,
        "tokens_input": 5234,
        "tokens_output": 432
      }
    }
  ]
}
```

### Field Descriptions

**Session Metadata**:
- `session_id`: Unique identifier (e.g., "main", "romance_path")
- `session_type`: "active", "branch", "archived", "checkpoint"
- `parent_session`: If branched, which session it came from
- `branch_point`: If branched, which response number
- `created`: ISO timestamp of creation
- `last_modified`: ISO timestamp of last change
- `current_response`: Number of messages in session
- `tags`: Array of tags for searching
- `description`: Optional user description

**RP Metadata**:
- `rp_name`: Name of the RP
- `chapter`: Current chapter number
- `scene`: Current scene description

**Message Structure**:
- `response_num`: Sequential message number (1-indexed)
- `timestamp`: When this message was created
- `chapter`: Chapter number at time of message
- `user_message`: User's input
- `assistant_response`: Claude's response
- `agent_data_background`: Agent analyses (from previous response)
- `agent_data_immediate`: Context for next response
- `model_info`: Model used, tokens, temperature, etc.

---

## SessionManager API

### Class Overview

```python
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

class SessionManager:
    """Manages session logs for retry, branching, and checkpointing."""

    def __init__(self, rp_dir: Path):
        """Initialize SessionManager.

        Args:
            rp_dir: Path to RP directory

        Raises:
            ValueError: If rp_dir doesn't exist
        """
        self.rp_dir = Path(rp_dir)
        self.sessions_dir = self.rp_dir / "sessions"
        self.branches_dir = self.sessions_dir / "branches"
        self.archived_dir = self.sessions_dir / "archived"

        # Ensure directories exist
        self.sessions_dir.mkdir(exist_ok=True)
        self.branches_dir.mkdir(exist_ok=True)
        self.archived_dir.mkdir(exist_ok=True)

        # Path to active session
        self.active_session_path = self.sessions_dir / "session_main.json"
```

### Core Methods

#### 1. Session Loading & Saving

```python
def load_session(self, session_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load session from JSON file.

    Args:
        session_path: Path to session file (default: active session)

    Returns:
        Session dictionary

    Raises:
        FileNotFoundError: If session file doesn't exist
        ValueError: If JSON is invalid
    """
    if session_path is None:
        session_path = self.active_session_path

    if not session_path.exists():
        raise FileNotFoundError(f"Session not found: {session_path}")

    with open(session_path, 'r', encoding='utf-8') as f:
        session = json.load(f)

    # Validate session structure
    self._validate_session(session)

    return session


def save_session(self, session: Dict[str, Any], session_path: Optional[Path] = None) -> None:
    """Save session to JSON file.

    Args:
        session: Session dictionary
        session_path: Path to save (default: active session)

    Raises:
        ValueError: If session structure is invalid
    """
    if session_path is None:
        session_path = self.active_session_path

    # Validate before saving
    self._validate_session(session)

    # Update last_modified
    session["last_modified"] = datetime.now().isoformat()

    # Ensure parent directory exists
    session_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with pretty formatting
    with open(session_path, 'w', encoding='utf-8') as f:
        json.dump(session, f, indent=2, ensure_ascii=False)


def _validate_session(self, session: Dict[str, Any]) -> None:
    """Validate session structure.

    Args:
        session: Session dictionary

    Raises:
        ValueError: If session is invalid
    """
    required_fields = [
        "session_id", "session_type", "created",
        "current_response", "tags", "messages"
    ]

    for field in required_fields:
        if field not in session:
            raise ValueError(f"Session missing required field: {field}")

    # Validate message structure
    for msg in session["messages"]:
        if "response_num" not in msg or "user_message" not in msg:
            raise ValueError("Invalid message structure")
```

#### 2. Core Operation: copy_session()

```python
def copy_session(
    self,
    up_to_response: int,
    new_session_name: str,
    session_type: str = "branch",
    tags: Optional[List[str]] = None,
    description: str = ""
) -> Path:
    """Copy session up to specific response number.

    This is the CORE operation that powers all features:
    - Retry: copy_session(current-1, "retry_TIMESTAMP", "archived", ["retry"])
    - Branch: copy_session(N, name, "branch", tags)
    - Checkpoint: copy_session(current, name, "checkpoint", tags)

    Args:
        up_to_response: Last response to include (1-indexed)
        new_session_name: Name for new session
        session_type: "branch", "archived", or "checkpoint"
        tags: Optional tags for searching
        description: Optional description

    Returns:
        Path to new session file

    Raises:
        ValueError: If response number invalid or name taken
    """
    # Load active session
    active = self.load_session()

    # Validate response number
    if up_to_response < 0 or up_to_response > active["current_response"]:
        raise ValueError(
            f"Invalid response number: {up_to_response} "
            f"(session has {active['current_response']} messages)"
        )

    # Sanitize session name
    safe_name = self._sanitize_name(new_session_name)

    # Determine save path
    if session_type == "branch":
        save_path = self.branches_dir / f"session_{safe_name}.json"
    elif session_type in ["archived", "checkpoint"]:
        prefix = "checkpoint_" if session_type == "checkpoint" else ""
        save_path = self.archived_dir / f"{prefix}{safe_name}.json"
    else:
        raise ValueError(f"Invalid session_type: {session_type}")

    # Check if name already exists
    if save_path.exists():
        raise ValueError(f"Session already exists: {safe_name}")

    # Create new session
    new_session = {
        "session_id": safe_name,
        "session_type": session_type,
        "parent_session": active["session_id"],
        "branch_point": up_to_response,
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "current_response": up_to_response,
        "tags": tags or [],
        "description": description,
        "rp_metadata": active.get("rp_metadata", {}).copy(),
        "messages": active["messages"][:up_to_response].copy()
    }

    # Add auto-tags
    new_session["tags"] = self._add_auto_tags(
        new_session["tags"],
        session_type,
        up_to_response,
        active.get("chapter", 1)
    )

    # Save new session
    self.save_session(new_session, save_path)

    return save_path


def _sanitize_name(self, name: str) -> str:
    """Sanitize session name for filesystem.

    Args:
        name: User-provided name

    Returns:
        Safe filename
    """
    # Remove invalid characters
    safe = "".join(c for c in name if c.isalnum() or c in " _-")
    # Replace spaces with underscores
    safe = safe.replace(" ", "_")
    # Lowercase
    safe = safe.lower()
    # Remove consecutive underscores
    while "__" in safe:
        safe = safe.replace("__", "_")
    # Limit length
    return safe[:50]
```

#### 3. Retry Command

```python
def retry(self, tags: Optional[List[str]] = None) -> Path:
    """Retry last response.

    Removes last message from active session and archives it.

    Args:
        tags: Optional tags for archived session

    Returns:
        Path to archived session

    Raises:
        ValueError: If session is empty
    """
    # Load active session
    active = self.load_session()

    # Check if there are messages to retry
    if active["current_response"] == 0:
        raise ValueError("Cannot retry: Session is empty")

    # Create archive name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"retry_{timestamp}"

    # Copy current session to archive
    archive_path = self.copy_session(
        up_to_response=active["current_response"],
        new_session_name=archive_name,
        session_type="archived",
        tags=tags or ["retry"],
        description="Retried response"
    )

    # Remove last message from active session
    active["messages"] = active["messages"][:-1]
    active["current_response"] -= 1
    active["last_modified"] = datetime.now().isoformat()

    # Save modified active session
    self.save_session(active)

    return archive_path
```

#### 4. Branch Command

```python
def branch(
    self,
    branch_name: str,
    response_num: Optional[int] = None,
    tags: Optional[List[str]] = None,
    description: str = ""
) -> Path:
    """Create named branch from specific point.

    Args:
        branch_name: Name for the branch
        response_num: Response to branch from (default: current)
        tags: Optional tags
        description: Optional description

    Returns:
        Path to branch session file
    """
    # Load active session
    active = self.load_session()

    # Default to current response
    if response_num is None:
        response_num = active["current_response"]

    # Create branch
    return self.copy_session(
        up_to_response=response_num,
        new_session_name=branch_name,
        session_type="branch",
        tags=tags or [],
        description=description
    )
```

#### 5. Checkpoint Command

```python
def checkpoint(
    self,
    checkpoint_name: str,
    tags: Optional[List[str]] = None,
    description: str = ""
) -> Path:
    """Save checkpoint at current point.

    Args:
        checkpoint_name: Name for checkpoint
        tags: Optional tags
        description: Optional description

    Returns:
        Path to checkpoint file
    """
    # Load active session
    active = self.load_session()

    # Create checkpoint
    return self.copy_session(
        up_to_response=active["current_response"],
        new_session_name=checkpoint_name,
        session_type="checkpoint",
        tags=tags or ["checkpoint"],
        description=description
    )
```

#### 6. Switch Command

```python
def switch(self, session_name: str) -> Path:
    """Switch to different session.

    Swaps active session with specified session.

    Args:
        session_name: Name of session to switch to

    Returns:
        Path to new active session

    Raises:
        FileNotFoundError: If session doesn't exist
    """
    # Find session file
    candidates = [
        self.branches_dir / f"session_{session_name}.json",
        self.archived_dir / f"{session_name}.json",
        self.archived_dir / f"checkpoint_{session_name}.json"
    ]

    session_path = None
    for candidate in candidates:
        if candidate.exists():
            session_path = candidate
            break

    if session_path is None:
        raise FileNotFoundError(f"Session not found: {session_name}")

    # Backup current active session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = self.archived_dir / f"switch_backup_{timestamp}.json"

    active = self.load_session()
    self.save_session(active, backup_path)

    # Load target session
    target = self.load_session(session_path)

    # Save target as new active session
    target["session_type"] = "active"
    self.save_session(target, self.active_session_path)

    return self.active_session_path
```

#### 7. Session Listing & Search

```python
def list_sessions(self, tag_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available sessions.

    Args:
        tag_filter: Optional tag to filter by

    Returns:
        List of session info dictionaries
    """
    sessions = []

    # Add active session
    if self.active_session_path.exists():
        active = self.load_session()
        sessions.append({
            "name": active["session_id"],
            "type": "active",
            "path": self.active_session_path,
            "response_count": active["current_response"],
            "tags": active.get("tags", []),
            "description": active.get("description", ""),
            "last_modified": active.get("last_modified", "")
        })

    # Add branches
    for session_file in self.branches_dir.glob("session_*.json"):
        session = self.load_session(session_file)
        sessions.append({
            "name": session["session_id"],
            "type": "branch",
            "path": session_file,
            "response_count": session["current_response"],
            "tags": session.get("tags", []),
            "description": session.get("description", ""),
            "last_modified": session.get("last_modified", "")
        })

    # Add archived (retries and checkpoints)
    for session_file in self.archived_dir.glob("*.json"):
        # Skip switch backups
        if "switch_backup" in session_file.name:
            continue

        session = self.load_session(session_file)
        sessions.append({
            "name": session["session_id"],
            "type": session.get("session_type", "archived"),
            "path": session_file,
            "response_count": session["current_response"],
            "tags": session.get("tags", []),
            "description": session.get("description", ""),
            "last_modified": session.get("last_modified", "")
        })

    # Filter by tag if specified
    if tag_filter:
        sessions = [s for s in sessions if tag_filter in s["tags"]]

    # Sort by last_modified (newest first)
    sessions.sort(key=lambda s: s.get("last_modified", ""), reverse=True)

    return sessions
```

#### 8. Message Management

```python
def append_message(
    self,
    user_message: str,
    assistant_response: str,
    agent_data_background: Optional[Dict] = None,
    agent_data_immediate: Optional[Dict] = None,
    model_info: Optional[Dict] = None
) -> int:
    """Append new message to active session.

    Args:
        user_message: User's input
        assistant_response: Claude's response
        agent_data_background: Agent analyses from previous response
        agent_data_immediate: Context for next response
        model_info: Model information

    Returns:
        New response number
    """
    # Load active session
    session = self.load_session()

    # Create new message
    response_num = session["current_response"] + 1

    message = {
        "response_num": response_num,
        "timestamp": datetime.now().isoformat(),
        "chapter": session.get("rp_metadata", {}).get("chapter", 1),
        "user_message": user_message,
        "assistant_response": assistant_response,
        "agent_data_background": agent_data_background or {},
        "agent_data_immediate": agent_data_immediate or {},
        "model_info": model_info or {}
    }

    # Append message
    session["messages"].append(message)
    session["current_response"] = response_num

    # Save session
    self.save_session(session)

    return response_num
```

---

## Core Operation: copy_session()

### The Foundation

**Every feature is built on this one operation:**

```python
def copy_session(up_to_response, new_name, tags) -> Path:
    # 1. Load active session
    # 2. Slice messages array
    # 3. Create new session with copied messages
    # 4. Save to appropriate location
    # 5. Return path
```

### Why This Works

**Retry** = Copy session without last message, then remove last message from active:
```python
def retry():
    # Archive current state
    copy_session(current_response, "retry_TIMESTAMP", ["retry"])
    # Remove last message from active
    active.messages.pop()
```

**Branch** = Copy session up to response N:
```python
def branch(N, name):
    copy_session(N, name, ["branch"])
```

**Checkpoint** = Copy session at current point:
```python
def checkpoint(name):
    copy_session(current_response, name, ["checkpoint"])
```

### Implementation Notes

1. **Always validate** response number before copying
2. **Sanitize** session names for filesystem
3. **Check for duplicates** before creating
4. **Add auto-tags** (retry, branch, checkpoint, chapter-N, date)
5. **Update timestamps** on all modifications
6. **Deep copy** messages array to avoid references

---

## Command Implementations

### Command Syntax

```bash
# Retry
/retry
/retry #better-dialogue #rewrite

# Branch
/branch "name"
/branch "name" #tag1 #tag2
/branch 42 "name"              # Branch from response 42
/branch 42 "name" #tag

# Checkpoint
/checkpoint "name"
/checkpoint "name" #important #chapter-end

# Switch
/switch "name"

# List
/sessions
/sessions tag:romance
/sessions tag:chapter-2
```

### Tag Parsing

```python
def parse_command_with_tags(command: str) -> tuple[str, List[str]]:
    """Parse command and extract tags.

    Example:
        "/retry #better-dialogue #rewrite"
        -> ("/retry", ["better-dialogue", "rewrite"])

    Args:
        command: Full command string

    Returns:
        (command_without_tags, list_of_tags)
    """
    tags = []
    parts = command.split()

    # Extract tags (words starting with #)
    clean_parts = []
    for part in parts:
        if part.startswith("#"):
            tags.append(part[1:])  # Remove #
        else:
            clean_parts.append(part)

    clean_command = " ".join(clean_parts)
    return clean_command, tags
```

### Response Number Parsing

```python
def parse_branch_command(command: str) -> tuple[Optional[int], str, List[str]]:
    """Parse branch command.

    Examples:
        '/branch "romance path"'
        -> (None, "romance path", [])

        '/branch 42 "romance path" #romance'
        -> (42, "romance path", ["romance"])

    Args:
        command: Full branch command

    Returns:
        (response_num, branch_name, tags)
    """
    # Extract tags first
    clean_command, tags = parse_command_with_tags(command)

    # Remove "/branch" prefix
    args = clean_command.replace("/branch", "").strip()

    # Check for response number
    parts = args.split(maxsplit=1)

    if len(parts) == 2 and parts[0].isdigit():
        # Has response number
        response_num = int(parts[0])
        branch_name = parts[1].strip('"\'')
    else:
        # No response number
        response_num = None
        branch_name = args.strip('"\'')

    return response_num, branch_name, tags
```

---

## Tagging System

### Auto-Tags

System automatically adds:

- `retry` - All retry operations
- `checkpoint` - All checkpoints
- `branch` - All named branches
- `chapter-N` - Current chapter number
- `response-N` - Response number at branch point
- `date-YYYYMMDD` - Date created

### Implementation

```python
def _add_auto_tags(
    self,
    user_tags: List[str],
    session_type: str,
    response_num: int,
    chapter: int
) -> List[str]:
    """Add auto-tags to user tags.

    Args:
        user_tags: Tags provided by user
        session_type: Type of session
        response_num: Response number
        chapter: Chapter number

    Returns:
        Combined tag list
    """
    tags = user_tags.copy()

    # Add type tag
    if session_type == "archived":
        tags.append("retry")
    elif session_type == "checkpoint":
        tags.append("checkpoint")
    elif session_type == "branch":
        tags.append("branch")

    # Add chapter tag
    tags.append(f"chapter-{chapter}")

    # Add response tag
    tags.append(f"response-{response_num}")

    # Add date tag
    date_tag = datetime.now().strftime("date-%Y%m%d")
    tags.append(date_tag)

    # Remove duplicates
    return list(set(tags))
```

---

## Bridge Integration

### Command Detection in tui_bridge.py

Add this code after the `/new` command handler:

```python
# ============================================================================
# SESSION MANAGEMENT COMMANDS
# ============================================================================

from src.session_manager import SessionManager

# Initialize session manager
session_manager = SessionManager(rp_dir)

# Parse command and tags
message_clean, tags = parse_command_with_tags(message.strip())
command_lower = message_clean.lower()

# --- /retry command ---
if command_lower == "/retry":
    try:
        # Perform retry
        archive_path = session_manager.retry(tags=tags if tags else None)

        response = f"""✅ Retry successful!

Last response removed and archived to:
{archive_path.name}

{f'Tags: {", ".join(tags)}' if tags else ''}

You can now send your message again to get a new response."""

        log_to_file(log_file, f"[RETRY] Archived to {archive_path}")

    except ValueError as e:
        response = f"❌ Retry failed: {str(e)}"
        log_to_file(log_file, f"[ERROR] Retry failed: {e}")

    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue

# --- /branch command ---
if command_lower.startswith("/branch"):
    try:
        # Parse branch command
        response_num, branch_name, branch_tags = parse_branch_command(message)

        # Create branch
        branch_path = session_manager.branch(
            branch_name=branch_name,
            response_num=response_num,
            tags=branch_tags if branch_tags else None
        )

        response = f"""✅ Branch created!

Name: {branch_name}
Branched from: Response {response_num or 'current'}
Location: {branch_path.name}
{f'Tags: {", ".join(branch_tags)}' if branch_tags else ''}

You can /switch "{branch_name}" to work on this branch, or continue here."""

        log_to_file(log_file, f"[BRANCH] Created {branch_name}")

    except ValueError as e:
        response = f"❌ Branch failed: {str(e)}"
        log_to_file(log_file, f"[ERROR] Branch failed: {e}")

    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue

# --- /checkpoint command ---
if command_lower.startswith("/checkpoint"):
    try:
        # Extract checkpoint name
        checkpoint_name = message_clean.replace("/checkpoint", "").strip().strip('"\'')

        if not checkpoint_name:
            raise ValueError("Checkpoint name required")

        # Create checkpoint
        checkpoint_path = session_manager.checkpoint(
            checkpoint_name=checkpoint_name,
            tags=tags if tags else None
        )

        response = f"""✅ Checkpoint saved!

Name: {checkpoint_name}
Location: {checkpoint_path.name}
{f'Tags: {", ".join(tags)}' if tags else ''}"""

        log_to_file(log_file, f"[CHECKPOINT] Created {checkpoint_name}")

    except ValueError as e:
        response = f"❌ Checkpoint failed: {str(e)}"
        log_to_file(log_file, f"[ERROR] Checkpoint failed: {e}")

    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue

# --- /switch command ---
if command_lower.startswith("/switch"):
    try:
        # Extract session name
        session_name = message_clean.replace("/switch", "").strip().strip('"\'')

        if not session_name:
            raise ValueError("Session name required")

        # Switch session
        new_active_path = session_manager.switch(session_name)

        response = f"""✅ Switched to: {session_name}

TUI will reload with this session's history.

Type /sessions to see all available sessions."""

        log_to_file(log_file, f"[SWITCH] Switched to {session_name}")

        # TODO: Signal TUI to reload session
        # (TUI needs to re-read session_main.json)

    except FileNotFoundError as e:
        response = f"❌ Switch failed: {str(e)}"
        log_to_file(log_file, f"[ERROR] Switch failed: {e}")

    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue

# --- /sessions command ---
if command_lower.startswith("/sessions"):
    try:
        # Parse tag filter
        tag_filter = None
        if "tag:" in command_lower:
            tag_filter = command_lower.split("tag:")[1].strip()

        # List sessions
        sessions = session_manager.list_sessions(tag_filter=tag_filter)

        # Format response
        lines = ["📁 Available Sessions:\n"]

        # Active session
        active_sessions = [s for s in sessions if s["type"] == "active"]
        if active_sessions:
            s = active_sessions[0]
            lines.append(f"  ● {s['name']} (Response {s['response_count']}) [ACTIVE]")
            if s['tags']:
                lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
            lines.append("")

        # Branches
        branches = [s for s in sessions if s["type"] == "branch"]
        if branches:
            lines.append("  Branches:")
            for s in branches:
                lines.append(f"    {s['name']} (Response {s['response_count']})")
                if s['tags']:
                    lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
                if s['description']:
                    lines.append(f"    └─ \"{s['description']}\"")
            lines.append("")

        # Archived
        archived = [s for s in sessions if s["type"] in ["archived", "checkpoint"]]
        if archived:
            lines.append("  Archived:")
            for s in archived[:10]:  # Limit to 10 most recent
                lines.append(f"    {s['name']} (Response {s['response_count']})")
                if s['tags']:
                    lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
            if len(archived) > 10:
                lines.append(f"    ... and {len(archived)-10} more")

        response = "\n".join(lines)

    except Exception as e:
        response = f"❌ List failed: {str(e)}"
        log_to_file(log_file, f"[ERROR] List failed: {e}")

    file_manager.write_ipc_response(response, state_dir=state_dir)
    done_flag.touch()
    print("📤 Response sent to TUI")
    print()
    continue
```

### Helper Functions

Add these helper functions near the top of tui_bridge.py:

```python
def parse_command_with_tags(command: str) -> tuple:
    """Parse command and extract hashtags."""
    tags = []
    parts = command.split()
    clean_parts = []

    for part in parts:
        if part.startswith("#"):
            tags.append(part[1:])
        else:
            clean_parts.append(part)

    return " ".join(clean_parts), tags


def parse_branch_command(command: str) -> tuple:
    """Parse branch command to extract response num, name, and tags."""
    clean_command, tags = parse_command_with_tags(command)
    args = clean_command.replace("/branch", "").strip()
    parts = args.split(maxsplit=1)

    if len(parts) == 2 and parts[0].isdigit():
        return int(parts[0]), parts[1].strip('"\''), tags
    else:
        return None, args.strip('"\''), tags
```

---

## TUI Integration

### Session Loading in rp_client_tui.py

The TUI needs to load chat history from session_main.json:

```python
def load_chat_from_session(self):
    """Load chat history from session file."""
    session_file = self.rp_dir / "sessions" / "session_main.json"

    if not session_file.exists():
        # Create initial session
        self._create_initial_session()
        return

    # Load session
    with open(session_file, 'r', encoding='utf-8') as f:
        session = json.load(f)

    # Clear current chat
    self.chat_history.clear()

    # Load messages
    for msg in session["messages"]:
        self.add_message_to_chat(
            user=msg["user_message"],
            assistant=msg["assistant_response"],
            response_num=msg["response_num"]
        )


def _create_initial_session(self):
    """Create initial session file if it doesn't exist."""
    from src.session_manager import SessionManager

    session_manager = SessionManager(self.rp_dir)

    initial_session = {
        "session_id": "main",
        "session_type": "active",
        "parent_session": None,
        "branch_point": None,
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "current_response": 0,
        "tags": ["main-timeline"],
        "description": "",
        "rp_metadata": {
            "rp_name": self.rp_name,
            "chapter": 1,
            "scene": ""
        },
        "messages": []
    }

    session_manager.save_session(initial_session)
```

### Reload on Switch

When user switches sessions, TUI should reload:

```python
def reload_session(self):
    """Reload session from file (called after switch command)."""
    self.load_chat_from_session()
    self.refresh()
```

---

## Migration Strategy

### From Existing Chapter Files

If user has existing chapter markdown files:

```python
def migrate_chapter_to_session(chapter_file: Path, rp_dir: Path):
    """Migrate chapter markdown to session log.

    Args:
        chapter_file: Path to chapter markdown file
        rp_dir: RP directory path
    """
    from src.session_manager import SessionManager

    # Parse chapter markdown
    messages = parse_chapter_markdown(chapter_file)

    # Create session
    session = {
        "session_id": "main",
        "session_type": "active",
        "parent_session": None,
        "branch_point": None,
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "current_response": len(messages),
        "tags": ["main-timeline", "migrated"],
        "description": f"Migrated from {chapter_file.name}",
        "rp_metadata": {
            "rp_name": rp_dir.name,
            "chapter": 1,
            "scene": ""
        },
        "messages": messages
    }

    # Save
    session_manager = SessionManager(rp_dir)
    session_manager.save_session(session)

    print(f"✅ Migrated {len(messages)} messages to session log")


def parse_chapter_markdown(chapter_file: Path) -> List[Dict]:
    """Parse chapter markdown into message list.

    Returns:
        List of message dictionaries
    """
    # Read file
    content = chapter_file.read_text(encoding='utf-8')

    # Split on "### Response #N" markers
    messages = []
    current_response = 0

    # Simple regex to find response blocks
    import re
    pattern = r"### Response #(\d+)\n\n(.*?)(?=### Response #|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)

    for response_num_str, response_content in matches:
        response_num = int(response_num_str)

        # Split into user message and assistant response
        # (This depends on your chapter format)
        parts = response_content.split("\n\n", 1)

        if len(parts) == 2:
            user_msg = parts[0].strip()
            assistant_resp = parts[1].strip()
        else:
            user_msg = ""
            assistant_resp = parts[0].strip()

        messages.append({
            "response_num": response_num,
            "timestamp": datetime.now().isoformat(),
            "chapter": 1,
            "user_message": user_msg,
            "assistant_response": assistant_resp,
            "agent_data_background": {},
            "agent_data_immediate": {},
            "model_info": {}
        })

    return messages
```

---

## Error Handling

### Common Errors

1. **Session not found**
   - Error: `FileNotFoundError`
   - Message: "Session not found: {name}"
   - Recovery: List available sessions

2. **Invalid response number**
   - Error: `ValueError`
   - Message: "Invalid response number: {num}"
   - Recovery: Show valid range

3. **Duplicate name**
   - Error: `ValueError`
   - Message: "Session already exists: {name}"
   - Recovery: Suggest different name

4. **Empty session**
   - Error: `ValueError`
   - Message: "Cannot retry: Session is empty"
   - Recovery: Explain that there's nothing to retry

5. **Invalid JSON**
   - Error: `json.JSONDecodeError`
   - Message: "Session file corrupted"
   - Recovery: Restore from backup (if exists)

### Error Handling Pattern

```python
try:
    # Operation
    result = session_manager.retry()
    # Success message
    response = f"✅ Retry successful!"
except ValueError as e:
    # User error (invalid input)
    response = f"❌ Retry failed: {str(e)}"
    log_to_file(log_file, f"[ERROR] {e}")
except FileNotFoundError as e:
    # File not found
    response = f"❌ Session not found: {str(e)}"
    log_to_file(log_file, f"[ERROR] {e}")
except Exception as e:
    # Unexpected error
    response = f"❌ Unexpected error: {str(e)}"
    log_to_file(log_file, f"[CRITICAL] {e}")
```

---

## Testing Checklist

### Unit Tests (test_session_manager.py)

- [ ] `test_create_session_manager()`
- [ ] `test_load_session()`
- [ ] `test_save_session()`
- [ ] `test_validate_session_valid()`
- [ ] `test_validate_session_invalid()`
- [ ] `test_copy_session_basic()`
- [ ] `test_copy_session_with_tags()`
- [ ] `test_copy_session_invalid_response_num()`
- [ ] `test_retry_success()`
- [ ] `test_retry_empty_session()`
- [ ] `test_retry_with_tags()`
- [ ] `test_branch_from_current()`
- [ ] `test_branch_from_response_num()`
- [ ] `test_branch_duplicate_name()`
- [ ] `test_checkpoint_success()`
- [ ] `test_switch_to_branch()`
- [ ] `test_switch_session_not_found()`
- [ ] `test_list_sessions_empty()`
- [ ] `test_list_sessions_with_results()`
- [ ] `test_list_sessions_with_tag_filter()`
- [ ] `test_append_message()`
- [ ] `test_sanitize_name()`
- [ ] `test_add_auto_tags()`

### Integration Tests (test_session_integration.py)

- [ ] `test_full_retry_workflow()`
- [ ] `test_full_branch_workflow()`
- [ ] `test_full_switch_workflow()`
- [ ] `test_multiple_branches()`
- [ ] `test_bridge_retry_command()`
- [ ] `test_bridge_branch_command()`
- [ ] `test_bridge_checkpoint_command()`
- [ ] `test_bridge_switch_command()`
- [ ] `test_bridge_sessions_command()`
- [ ] `test_tag_parsing()`
- [ ] `test_branch_command_parsing()`

### Manual Tests

- [ ] Start new RP, send message, retry, verify works
- [ ] Create branch, switch to it, send message, switch back
- [ ] Create checkpoint, verify saved correctly
- [ ] Test all tag variations
- [ ] Test with 100+ messages (performance)
- [ ] Test error cases (invalid names, missing sessions)

---

## Implementation Timeline

### Day 1: Core Session Manager
- [ ] Create `src/session_manager.py`
- [ ] Implement SessionManager class skeleton
- [ ] Implement `load_session()` and `save_session()`
- [ ] Implement `copy_session()` (CORE)
- [ ] Write unit tests for core operations

### Day 2: Commands
- [ ] Implement `retry()`
- [ ] Implement `branch()`
- [ ] Implement `checkpoint()`
- [ ] Implement `switch()`
- [ ] Implement `list_sessions()`
- [ ] Write unit tests for all commands

### Day 3: Bridge Integration
- [ ] Add command detection to `tui_bridge.py`
- [ ] Add tag parsing helpers
- [ ] Implement all command handlers
- [ ] Test commands manually

### Day 4: TUI Integration & Testing
- [ ] Add session loading to TUI
- [ ] Add session reload on switch
- [ ] Write integration tests
- [ ] Manual testing with real RP

### Day 5: Polish & Documentation
- [ ] Error handling improvements
- [ ] Performance testing
- [ ] User documentation
- [ ] Code review
- [ ] Update IMPLEMENTATION_LOG.md

---

## Success Criteria

Phase 1 is complete when:

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ `/retry` command works reliably
- ✅ `/branch` command works reliably
- ✅ `/checkpoint` command works reliably
- ✅ `/switch` command works reliably
- ✅ `/sessions` command works reliably
- ✅ Tagging system works
- ✅ Session files are valid JSON
- ✅ TUI reloads correctly after switch
- ✅ Performance is acceptable (<500ms for typical operations)
- ✅ Error handling is robust
- ✅ User documentation is complete

---

## References

- **Architecture**: `ARCHITECTURE.md` (v2.0)
- **Testing Plan**: `TESTING.md`
- **Main Roadmap**: `ROADMAP.md`
- **Implementation Log**: `IMPLEMENTATION_LOG.md`

---

**Last Updated**: 2025-10-17
**Version**: 1.0
**Status**: Ready for implementation
