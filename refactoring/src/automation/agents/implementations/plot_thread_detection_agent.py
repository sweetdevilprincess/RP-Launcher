"""Plot Thread Detection Agent - Track narrative plot threads and story arcs.

This agent analyzes Claude's responses to detect:
- New plot threads starting (mysteries, conflicts, goals, secrets)
- Progress on existing threads
- Thread resolutions with outcomes (successful/unsuccessful/complicated/abandoned)
- Long-term effects of resolved threads

Threads are tracked globally with participant lists and archived when resolved.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


# Standardized tag taxonomy for plot threads
THREAD_TAGS = [
    # Genre/Type
    "mystery", "romance", "conflict", "quest", "secret", "betrayal",
    "discovery", "danger", "political", "personal", "professional",

    # Scope
    "character_backstory", "world_building", "main_plot", "subplot",
    "character_arc", "relationship_arc",

    # Urgency
    "time_sensitive", "high_stakes", "low_stakes", "urgent", "slow_burn",

    # Status
    "just_started", "developing", "climax", "resolution_pending"
]


class PlotThreadDetectionAgent(BaseAgent):
    """Detect and track narrative plot threads with full outcome tracking.

    Uses session state from ResponseAnalyzerAgent and TimeTrackingAgent for context.
    Archives resolved threads with complete outcome data for future reference.
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "plot_thread_detection"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str | None = None,
        **kwargs
    ) -> str:
        """Execute plot thread detection and tracking.

        Args:
            user_message: User's original message
            message_number: Current message index
            claude_response: Claude's response to analyze
            **kwargs: Additional context

        Returns:
            Summary string of thread activity
        """
        # Extract claude_response from kwargs if not provided directly
        if claude_response is None:
            claude_response = kwargs.get("claude_response")

        if not claude_response:
            self.log("No Claude response provided, skipping plot thread detection")
            return "No response to analyze"

        try:
            self.log(f"Detecting plot threads for message #{message_number}")

            # Step 1: Get scene context from session state
            scene_context = self.bridge.session_state_service.get_scene_context(self.rp_dir)

            # Step 2: Extract context
            characters_in_scene = scene_context.get("characters_in_scene", [])
            location = scene_context.get("location", "Unknown")
            chapter = scene_context.get("chapter", "")

            # Step 3: Get timestamp from TimeTrackingAgent's time_context
            timestamp = self._get_timestamp_from_time_tracking(scene_context, message_number)

            # Step 4: Load existing threads
            threads_data = self._load_existing_threads()
            active_threads = threads_data.get("threads", [])

            # Step 5: Build LLM prompt
            prompt = self._build_plot_thread_prompt(
                user_message,
                claude_response,
                active_threads,
                characters_in_scene,
                location,
                chapter
            )

            # Step 6: Call LLM for thread detection (temperature=0.0 for consistency)
            response = self.call_llm(user_message=prompt, temperature=0.0)

            # Step 7: Parse JSON response
            thread_updates = self.parse_json_response(response)

            if not thread_updates:
                self.log("Failed to parse thread updates from LLM response")
                return "Thread detection failed"

            # Step 8: Apply updates to threads
            result = self._apply_thread_updates(
                threads_data,
                thread_updates,
                timestamp,
                message_number,
                location,
                characters_in_scene
            )

            # Step 9: Save updated threads and archives
            self._save_threads(threads_data, message_number)

            # Step 10: Return summary
            return self._format_summary(result)

        except Exception as e:
            self.log(f"Error in plot thread detection: {e}")
            import traceback
            self.log(traceback.format_exc())
            return f"Plot thread detection failed: {e}"

    # ==========================================================================
    # LLM Prompt Building
    # ==========================================================================

    def _build_plot_thread_prompt(
        self,
        user_message: str,
        claude_response: str,
        active_threads: list[dict],
        characters_in_scene: list[str],
        location: str,
        chapter: str
    ) -> str:
        """Build LLM prompt for plot thread detection.

        Args:
            user_message: User's message
            claude_response: Claude's response
            active_threads: Currently active plot threads
            characters_in_scene: Characters in current scene
            location: Current location
            chapter: Current chapter

        Returns:
            LLM prompt string
        """
        # Format active threads for context
        active_threads_text = self._format_active_threads(active_threads)

        # Build tag guidance
        thread_tags_str = ", ".join(THREAD_TAGS[:15]) + ", ..."

        characters_str = ", ".join(characters_in_scene) if characters_in_scene else "Unknown"

        return f"""Analyze this roleplay response for plot thread developments.

USER MESSAGE:
{user_message}

CLAUDE'S RESPONSE:
{claude_response}

CURRENT SCENE:
- Chapter: {chapter if chapter else "None"}
- Location: {location}
- Characters: {characters_str}

EXISTING ACTIVE THREADS:
{active_threads_text}

Identify:
1. **NEW THREADS** - New storylines or narrative arcs beginning
   - Only identify threads that have clear narrative potential
   - Don't create threads for mundane conversations
   - Look for: mysteries, conflicts, goals, relationships developing, secrets, quests

2. **THREAD UPDATES** - Progress on existing threads
   - Has information been revealed?
   - Have participants taken actions related to the thread?
   - Has the situation changed or escalated?

3. **RESOLVED THREADS** - Threads that have concluded
   - Was the resolution successful, unsuccessful, complicated, or abandoned?
   - What was the outcome?
   - What are the long-term effects?
   - Which relationships were affected?

**Priority Guidelines:**
- 1-3: Minor subplot
- 4-6: Moderate importance
- 7-9: Major storyline
- 10: Critical main plot

**time_sensitive**: true if there's urgency or a deadline

**Tag Reference** (use these + custom tags as needed):
{thread_tags_str}

Respond with JSON ONLY:
{{
  "new_threads": [
    {{
      "title": "Brief descriptive title",
      "description": "1-2 sentence description of the thread",
      "participants": ["Character names involved"],
      "locations": ["Where this thread takes place"],
      "tags": ["mystery", "character_backstory", "high_stakes"],
      "priority": 7,
      "time_sensitive": false,
      "initial_progress": "What happened in this response to start this thread"
    }}
  ],
  "thread_updates": [
    {{
      "thread_id": "thread_abc123",
      "progress": "Brief description of what progressed in this response",
      "priority_change": null,
      "new_participants": null,
      "new_locations": null,
      "new_tags": null
    }}
  ],
  "resolved_threads": [
    {{
      "thread_id": "thread_def456",
      "resolution_notes": "How the thread was resolved",
      "outcome": "successful",
      "long_term_effects": ["Effect 1", "Effect 2"],
      "affected_relationships": {{"Alice_to_Bob": "Trust increased through cooperation"}}
    }}
  ]
}}

**Outcome values**: "successful", "unsuccessful", "complicated", "abandoned"

IMPORTANT:
- Only create NEW threads for meaningful narrative developments
- Don't create threads for casual conversations unless they hint at deeper issues
- Update existing threads if the response mentions or progresses them
- Mark threads as resolved only if clearly concluded
- If no thread activity detected, return empty arrays
- thread_id must match an existing thread's id field
- priority_change, new_participants, new_locations, new_tags can be null if no changes"""

    def _format_active_threads(self, active_threads: list[dict]) -> str:
        """Format active threads for prompt context.

        Args:
            active_threads: List of active thread dicts

        Returns:
            Formatted string of active threads
        """
        if not active_threads:
            return "No active threads"

        formatted = []
        for thread in active_threads:
            thread_id = thread.get("id", "unknown")
            title = thread.get("title", "Untitled")
            description = thread.get("description", "No description")
            participants = ", ".join(thread.get("participants", []))
            priority = thread.get("priority", 5)

            formatted.append(
                f"[{thread_id}] (Priority {priority}) {title}\n"
                f"  Description: {description}\n"
                f"  Participants: {participants}"
            )

        return "\n\n".join(formatted)

    # ==========================================================================
    # Timestamp Handling
    # ==========================================================================

    def _get_timestamp_from_time_tracking(
        self,
        scene_context: dict,
        message_number: int
    ) -> str:
        """Get timestamp from TimeTrackingAgent's time_context.

        Args:
            scene_context: Scene context from session state
            message_number: Current message number

        Returns:
            ISO 8601 formatted timestamp
        """
        time_ctx = scene_context.get("time_context", {})

        if not time_ctx:
            # No time tracking data - use current real-world time as fallback
            self.log("No time_context found, using current real-world time")
            return datetime.now().isoformat()

        current_datetime = time_ctx.get("current_datetime")

        if not current_datetime:
            # Time tracking exists but no current_datetime
            self.log("time_context exists but no current_datetime, using current time")
            return datetime.now().isoformat()

        # Convert time_context datetime to ISO 8601
        try:
            dt = datetime(
                current_datetime.get("year", 2024),
                current_datetime.get("month", 1),
                current_datetime.get("day", 1),
                current_datetime.get("hour", 0),
                current_datetime.get("minute", 0)
            )
            return dt.isoformat()
        except Exception as e:
            self.log(f"Failed to convert time_context to ISO: {e}")
            return datetime.now().isoformat()

    # ==========================================================================
    # Thread Data Loading
    # ==========================================================================

    def _load_existing_threads(self) -> dict:
        """Load plot_threads_{session_id}.json file.

        Returns:
            Dict with 'threads' list and 'session_id'
        """
        # Get current session ID
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
        thread_file = session_state.get("plot_threads", {}).get("thread_file")

        if not thread_file:
            self.log("No plot_threads pointer in session.json")
            return {
                "threads": [],
                "session_id": "main",
                "last_updated": None
            }

        # Construct full path
        thread_path = self.rp_dir / thread_file

        # Load if exists, otherwise return empty structure
        if not thread_path.exists():
            self.log(f"Plot threads file not found: {thread_path}")
            session_id = session_state["timeline"]["current_session_id"]
            return {
                "threads": [],
                "session_id": session_id,
                "last_updated": None
            }

        # Load existing threads using JSON utility
        try:
            with open(thread_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.log(f"Loaded {len(data.get('threads', []))} threads from {thread_path}")
            return data
        except Exception as e:
            self.log(f"Failed to load plot threads file: {e}")
            return {
                "threads": [],
                "session_id": "main",
                "last_updated": None
            }

    # ==========================================================================
    # Thread Management
    # ==========================================================================

    def _generate_thread_id(self) -> str:
        """Generate unique thread ID.

        Returns:
            Thread ID string (format: thread_a1b2c3d4)
        """
        return f"thread_{uuid4().hex[:8]}"

    def _apply_thread_updates(
        self,
        threads_data: dict,
        thread_updates: dict,
        timestamp: str,
        message_number: int,
        location: str,
        characters_in_scene: list[str]
    ) -> dict:
        """Apply LLM-detected updates to thread data.

        Args:
            threads_data: Existing threads data structure
            thread_updates: Updates from LLM response
            timestamp: Current timestamp
            message_number: Current message number
            location: Current location
            characters_in_scene: Characters in current scene

        Returns:
            Dict with counts of new/updated/resolved threads
        """
        result = {
            "new_count": 0,
            "updated_count": 0,
            "resolved_count": 0,
            "new_threads": [],
            "updated_threads": [],
            "resolved_threads": []
        }

        # Process new threads
        for new_thread in thread_updates.get("new_threads", []):
            thread = self._create_new_thread(
                new_thread,
                timestamp,
                message_number,
                location,
                characters_in_scene
            )
            threads_data["threads"].append(thread)
            result["new_count"] += 1
            result["new_threads"].append(thread["title"])
            self.log(f"Created new thread: {thread['id']} - {thread['title']}")

        # Process thread updates
        for update in thread_updates.get("thread_updates", []):
            success = self._update_existing_thread(
                threads_data["threads"],
                update,
                timestamp,
                message_number
            )
            if success:
                result["updated_count"] += 1
                result["updated_threads"].append(update.get("thread_id"))

        # Process resolved threads
        for resolution in thread_updates.get("resolved_threads", []):
            success = self._resolve_thread(
                threads_data,
                resolution,
                timestamp,
                message_number
            )
            if success:
                result["resolved_count"] += 1
                result["resolved_threads"].append(resolution.get("thread_id"))

        return result

    def _create_new_thread(
        self,
        new_thread: dict,
        timestamp: str,
        message_number: int,
        location: str,
        characters_in_scene: list[str]
    ) -> dict:
        """Create new thread entry.

        Args:
            new_thread: New thread data from LLM
            timestamp: Current timestamp
            message_number: Current message number
            location: Current location
            characters_in_scene: Characters in current scene

        Returns:
            Complete thread dict
        """
        thread_id = self._generate_thread_id()

        # Use LLM-provided locations if available, otherwise use current location
        locations = new_thread.get("locations", [])
        if not locations and location:
            locations = [location]

        # Use LLM-provided participants if available, otherwise use current scene characters
        participants = new_thread.get("participants", [])
        if not participants:
            participants = characters_in_scene.copy()

        # Initial progress update
        initial_progress = new_thread.get("initial_progress", "Thread initiated")
        updates = [{
            "message": message_number,
            "timestamp": timestamp,
            "progress": initial_progress
        }]

        return {
            "id": thread_id,
            "title": new_thread.get("title", "Untitled Thread"),
            "description": new_thread.get("description", ""),
            "status": "active",
            "participants": participants,
            "locations": locations,
            "tags": new_thread.get("tags", []),
            "priority": new_thread.get("priority", 5),
            "time_sensitive": new_thread.get("time_sensitive", False),
            "started_at": timestamp,
            "started_message": message_number,
            "last_updated": timestamp,
            "last_updated_message": message_number,
            "updates": updates,
            "related_memories": [],
            "resolution_notes": None,
            "outcome": None
        }

    def _update_existing_thread(
        self,
        threads: list[dict],
        update: dict,
        timestamp: str,
        message_number: int
    ) -> bool:
        """Update existing thread with progress.

        Args:
            threads: List of thread dicts
            update: Update data from LLM
            timestamp: Current timestamp
            message_number: Current message number

        Returns:
            True if thread was found and updated
        """
        thread_id = update.get("thread_id")

        if not thread_id:
            self.log("Update missing thread_id, skipping")
            return False

        # Find thread by ID
        for thread in threads:
            if thread.get("id") == thread_id:
                # Add progress update
                progress = update.get("progress", "Thread progressed")
                thread["updates"].append({
                    "message": message_number,
                    "timestamp": timestamp,
                    "progress": progress
                })

                # Update metadata
                thread["last_updated"] = timestamp
                thread["last_updated_message"] = message_number

                # Apply optional field updates
                if update.get("priority_change") is not None:
                    thread["priority"] = update["priority_change"]

                if update.get("new_participants"):
                    for participant in update["new_participants"]:
                        if participant not in thread["participants"]:
                            thread["participants"].append(participant)

                if update.get("new_locations"):
                    for loc in update["new_locations"]:
                        if loc not in thread["locations"]:
                            thread["locations"].append(loc)

                if update.get("new_tags"):
                    for tag in update["new_tags"]:
                        if tag not in thread["tags"]:
                            thread["tags"].append(tag)

                self.log(f"Updated thread: {thread_id} - {thread['title']}")
                return True

        self.log(f"Thread not found: {thread_id}")
        return False

    def _resolve_thread(
        self,
        threads_data: dict,
        resolution: dict,
        timestamp: str,
        message_number: int
    ) -> bool:
        """Mark thread as resolved and archive it.

        Args:
            threads_data: Threads data structure (with 'threads' list)
            resolution: Resolution data from LLM
            timestamp: Current timestamp
            message_number: Current message number

        Returns:
            True if thread was found, resolved, and archived
        """
        thread_id = resolution.get("thread_id")

        if not thread_id:
            self.log("Resolution missing thread_id, skipping")
            return False

        # Find thread by ID
        for i, thread in enumerate(threads_data["threads"]):
            if thread.get("id") == thread_id:
                # Update thread with resolution data
                thread["status"] = "resolved"
                thread["last_updated"] = timestamp
                thread["last_updated_message"] = message_number
                thread["resolution_notes"] = resolution.get("resolution_notes", "")
                thread["outcome"] = resolution.get("outcome", "successful")

                # Add resolution as final update
                thread["updates"].append({
                    "message": message_number,
                    "timestamp": timestamp,
                    "progress": f"RESOLVED: {resolution.get('resolution_notes', 'Thread concluded')}"
                })

                # Store long-term effects if provided
                if "long_term_effects" in resolution:
                    thread["long_term_effects"] = resolution["long_term_effects"]

                if "affected_relationships" in resolution:
                    thread["affected_relationships"] = resolution["affected_relationships"]

                # Remove from active threads
                resolved_thread = threads_data["threads"].pop(i)

                # Archive the thread
                self._archive_thread(resolved_thread, timestamp, message_number)

                self.log(f"Resolved and archived thread: {thread_id} - {resolved_thread['title']}")
                return True

        self.log(f"Thread not found for resolution: {thread_id}")
        return False

    def _archive_thread(
        self,
        thread: dict,
        timestamp: str,
        message_number: int
    ) -> None:
        """Archive a resolved thread with full outcome data.

        Args:
            thread: Complete thread dict (with resolution data)
            timestamp: Archive timestamp
            message_number: Archive message number
        """
        # Add archive metadata
        thread["archived_at"] = timestamp
        thread["archived_message"] = message_number

        # Get current session ID for archive file name
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
        session_id = session_state["timeline"]["current_session_id"]

        # Construct archive file path
        archive_path = self.rp_dir / "state" / f"plot_threads_{session_id}_archive.json"

        # Load existing archive or create new
        if archive_path.exists():
            try:
                with open(archive_path, "r", encoding="utf-8") as f:
                    archive_data = json.load(f)
            except Exception as e:
                self.log(f"Failed to load archive, creating new: {e}")
                archive_data = {
                    "session_id": session_id,
                    "archived_threads": []
                }
        else:
            archive_data = {
                "session_id": session_id,
                "archived_threads": []
            }

        # Add thread to archive
        archive_data["archived_threads"].append(thread)
        archive_data["last_updated"] = timestamp

        # Save archive
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(archive_path, "w", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            self.log(f"Archived thread to {archive_path}")
        except Exception as e:
            self.log(f"Failed to save archive: {e}")

    # ==========================================================================
    # Thread Saving
    # ==========================================================================

    def _save_threads(self, threads_data: dict, message_number: int) -> bool:
        """Save updated threads to timeline-specific file.

        Args:
            threads_data: Complete threads data structure
            message_number: Current message number

        Returns:
            True if saved successfully
        """
        # Update last_updated timestamp
        threads_data["last_updated"] = datetime.now().isoformat()

        # Get file path from session state
        session_state = self.bridge.session_state_service.load_session_state(self.rp_dir)
        thread_file = session_state.get("plot_threads", {}).get("thread_file")

        if not thread_file:
            self.log("ERROR: No plot_threads pointer in session.json")
            return False

        thread_path = self.rp_dir / thread_file

        # Ensure directory exists
        thread_path.parent.mkdir(parents=True, exist_ok=True)

        # Save threads
        try:
            with open(thread_path, "w", encoding="utf-8") as f:
                json.dump(threads_data, f, indent=2, ensure_ascii=False)

            self.log(f"Saved {len(threads_data['threads'])} threads to {thread_path}")
            return True
        except Exception as e:
            self.log(f"Failed to save threads: {e}")
            return False

    # ==========================================================================
    # Utilities
    # ==========================================================================

    def _format_summary(self, result: dict) -> str:
        """Format thread activity result as summary string.

        Args:
            result: Dict with counts and lists of thread activity

        Returns:
            Summary string
        """
        new_count = result["new_count"]
        updated_count = result["updated_count"]
        resolved_count = result["resolved_count"]

        if new_count == 0 and updated_count == 0 and resolved_count == 0:
            return "No thread activity detected"

        parts = []
        if new_count > 0:
            threads_str = ", ".join(result["new_threads"][:3])
            if new_count > 3:
                threads_str += f", +{new_count - 3} more"
            parts.append(f"{new_count} new thread(s): {threads_str}")

        if updated_count > 0:
            parts.append(f"{updated_count} thread(s) updated")

        if resolved_count > 0:
            parts.append(f"{resolved_count} thread(s) resolved and archived")

        return "; ".join(parts)


__all__ = ["PlotThreadDetectionAgent"]
