"""Branch Handler - Handles branch/timeline management IPC requests.

This handler processes branch-related requests including:
- GET_BRANCHES: List all timeline branches
- CREATE_BRANCH: Create new timeline branch
- SWITCH_BRANCH: Switch to different timeline
- COMPARE_BRANCHES: Compare two timelines
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.ipc import IPCMessageType, IPCRequest, create_error_response, create_response

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class BranchHandler(BaseHandler):
    """Handler for branch/timeline management operations.

    Delegates to bridge.session_state_service for all branch operations.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route branch request to appropriate handler method.

        Args:
            request: IPC request with branch operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.GET_BRANCHES:
            return self._handle_get_branches(request)
        elif request_type == IPCMessageType.CREATE_BRANCH:
            return self._handle_create_branch(request)
        elif request_type == IPCMessageType.SWITCH_BRANCH:
            return self._handle_switch_branch(request)
        elif request_type == IPCMessageType.COMPARE_BRANCHES:
            return self._handle_compare_branches(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown branch request type: {request.type}"
            )

    def _handle_get_branches(self, request: IPCRequest) -> str:
        """Handle GET_BRANCHES request - get session branches."""
        try:
            # Get current timeline from session state
            session_state = self.bridge.session_state_service.load_session_state(self.bridge.rp_dir)
            current_timeline = session_state.get("timeline", {}).get("current_session_id", "main")

            # Get all sessions (main + branches) using SessionRepository
            all_sessions = []

            # Add main session
            try:
                main_metadata = self.bridge.session_repository.get_session_metadata("main")
                if main_metadata:
                    all_sessions.append(main_metadata)
            except Exception:
                pass

            # Add all branch sessions
            branch_metadatas = self.bridge.session_repository.list_branches()
            all_sessions.extend(branch_metadatas)

            # Format for TUI
            branches = {}
            for metadata in all_sessions:
                session_id = metadata.session_id

                # Load full session to get rp_metadata with branch_title
                try:
                    if session_id == "main":
                        session = self.bridge.session_repository.load_active_session()
                    else:
                        # Load branch session
                        from src.infrastructure.filesystem import JsonStore, StatePaths
                        paths = StatePaths(rp_dir=self.bridge.rp_dir)
                        store = JsonStore(root=paths.session_branches_dir, logger=self.bridge.session_state_service._logger)
                        from pathlib import Path
                        data = store.read(Path(f"session_{session_id}.json"))
                        from src.domain.sessions import SessionData
                        session = SessionData.from_dict(data)

                    # Get branch title from rp_metadata (or use session_id for main)
                    title = session.rp_metadata.get("branch_title", session_id if session_id == "main" else session_id)

                    # Generate preview from last message
                    preview = "No messages yet"
                    if session.messages:
                        last_message = session.messages[-1]
                        content = last_message.user_message
                        if content:
                            preview = content[:100].strip()
                            if len(content) > 100:
                                preview += "..."

                    branches[session_id] = {
                        "title": title,
                        "tags": session.tags,
                        "parent": session.parent_session,
                        "active": session_id == current_timeline,
                        "created_at": session.created,
                        "entry_count": len(session.messages),
                        "preview": preview,
                        "branch_point": session.branch_point
                    }
                except Exception as e:
                    # If we can't load the session, use metadata only
                    branches[session_id] = {
                        "title": session_id,
                        "tags": [],
                        "parent": metadata.parent_session,
                        "active": session_id == current_timeline,
                        "created_at": metadata.created,
                        "entry_count": metadata.message_count,
                        "preview": metadata.description,
                        "branch_point": metadata.branch_point
                    }

            return create_response(
                request.request_id,
                branches=branches,
                current_timeline=current_timeline
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to get branches: {str(e)}"
            )

    def _handle_create_branch(self, request: IPCRequest) -> str:
        """Handle CREATE_BRANCH request - create new timeline branch.

        Expected request data:
        - source_session_id: Session to branch from (optional, defaults to current)
        - branch_name: Name for the branch (required)
        - branch_point: Message index to branch from (optional, defaults to latest)
        - description: Optional description
        """
        branch_name = request.data.get("branch_name")
        if not branch_name:
            return create_error_response(request.request_id, "Missing branch_name")

        source_session_id = request.data.get("source_session_id")
        branch_point = request.data.get("branch_point")  # None = branch from latest
        description = request.data.get("description", "")

        try:
            # Determine source session (default to current if not specified)
            if not source_session_id:
                session_state = self.bridge.session_state_service.load_session_state(
                    self.bridge.rp_dir
                )
                source_session_id = session_state.get("timeline", {}).get(
                    "current_session_id", "main"
                )

            # Create branch via SessionRepository
            branch_session = self.bridge.session_repository.create_branch(
                source_session_id=source_session_id,
                branch_name=branch_name,
                branch_point=branch_point,
                description=description
            )

            # Restore scene_context from branch point
            self._restore_scene_context_at_branch_point(
                branch_session.session_id,
                branch_session.branch_point
            )

            # Copy chatlog files to branch folder
            self._copy_chatlogs_to_branch(
                source_session_id=source_session_id,
                branch_session_id=branch_session.session_id,
                branch_point=branch_session.branch_point
            )

            return create_response(
                request.request_id,
                branch_id=branch_session.session_id,
                branch_point=branch_session.branch_point,
                message_count=len(branch_session.messages),
                message=f"Branch '{branch_name}' created from message #{branch_session.branch_point}"
            )

        except FileNotFoundError as e:
            return create_error_response(
                request.request_id,
                f"Source session not found: {str(e)}"
            )
        except ValueError as e:
            return create_error_response(
                request.request_id,
                f"Invalid branch parameters: {str(e)}"
            )
        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to create branch: {str(e)}"
            )

    def _handle_switch_branch(self, request: IPCRequest) -> str:
        """Handle SWITCH_BRANCH request - switch to different timeline."""
        timeline_id = request.data.get("timeline_id")

        if not timeline_id:
            return create_error_response(request.request_id, "Missing timeline_id")

        try:
            # Switch timeline using session state service
            self.bridge.session_state_service.switch_timeline(self.bridge.rp_dir, timeline_id)

            return create_response(
                request.request_id,
                timeline_id=timeline_id,
                message=f"Switched to timeline '{timeline_id}'"
            )

        except Exception as e:
            return create_error_response(
                request.request_id,
                f"Failed to switch branch: {str(e)}"
            )

    def _handle_compare_branches(self, request: IPCRequest) -> str:
        """Handle COMPARE_BRANCHES request - compare two timelines."""
        # TODO: Implement branch comparison
        return create_error_response(
            request.request_id,
            "Branch comparison not yet implemented"
        )

    def _restore_scene_context_at_branch_point(
        self,
        branch_session_id: str,
        branch_point: int
    ) -> None:
        """Restore scene_context to the state at the branch point.

        Args:
            branch_session_id: New branch session ID
            branch_point: Message index where branch was created

        Raises:
            ValueError: If branch point is invalid or snapshot not found
        """
        try:
            # Load the branch session to get the message at branch_point
            from src.domain.sessions import SessionData
            from src.infrastructure.filesystem import JsonStore, StatePaths

            paths = StatePaths(rp_dir=self.bridge.rp_dir)
            branch_file = paths.session_branches_dir / f"session_{branch_session_id}.json"

            if not branch_file.exists():
                raise FileNotFoundError(f"Branch session file not found: {branch_file}")

            # Load branch session
            store = JsonStore(root=paths.session_branches_dir, logger=self.bridge.session_state_service._logger)
            data = store.read(branch_file.name)
            branch_session = SessionData.from_dict(data)

            # Get the message at branch_point (last message in branch)
            if not branch_session.messages:
                # No messages, use empty scene_context
                scene_context = {}
            else:
                # Get last message (the branch point)
                branch_point_message = branch_session.messages[-1]

                # Extract scene_context snapshot from agent_data_background
                scene_context = branch_point_message.agent_data_background.get(
                    "scene_context_snapshot", {}
                )

            # Create branch-specific scene_context file
            self.bridge.session_state_service.update_scene_context(
                self.bridge.rp_dir,
                scene_context
            )

            print(f"[BRANCH] Scene context restored to state at message #{branch_point}")

        except Exception as e:
            print(f"[WARNING] Failed to restore scene_context for branch: {e}")
            # Non-fatal - branch can still be used, just without restored state
            import traceback
            traceback.print_exc()

    def _copy_chatlogs_to_branch(
        self,
        source_session_id: str,
        branch_session_id: str,
        branch_point: int
    ) -> None:
        """Copy chatlog files up to branch point to the new branch folder.

        Args:
            source_session_id: Source session ID
            branch_session_id: New branch session ID
            branch_point: Message index where branch was created
        """
        try:
            from pathlib import Path
            from src.infrastructure.filesystem import StatePaths
            import shutil
            import json

            paths = StatePaths(rp_dir=self.bridge.rp_dir)

            # Source and destination chatlog directories
            source_chatlogs_dir = paths.sessions_dir / "chatlogs" / source_session_id
            branch_chatlogs_dir = paths.sessions_dir / "chatlogs" / branch_session_id

            if not source_chatlogs_dir.exists():
                print(f"[INFO] No source chatlogs to copy for {source_session_id}")
                return

            # Create branch chatlogs directory
            branch_chatlogs_dir.mkdir(parents=True, exist_ok=True)

            # Copy and filter chapter files
            for chapter_file in sorted(source_chatlogs_dir.glob("chapter_*.json")):
                # Read source chapter
                with open(chapter_file, "r", encoding="utf-8") as f:
                    chapter_data = json.load(f)

                # Filter messages up to branch_point
                filtered_messages = [
                    msg for msg in chapter_data.get("messages", [])
                    if msg.get("message_number", 0) <= branch_point
                ]

                if not filtered_messages:
                    continue  # Skip empty chapters

                # Update chapter metadata
                chapter_data["session_id"] = branch_session_id
                chapter_data["messages"] = filtered_messages
                chapter_data["end_message"] = filtered_messages[-1]["message_number"]

                # Write to branch folder
                dest_file = branch_chatlogs_dir / chapter_file.name
                with open(dest_file, "w", encoding="utf-8") as f:
                    json.dump(chapter_data, f, indent=2, ensure_ascii=False)

                print(f"[BRANCH] Copied {chapter_file.name} to branch (filtered to message #{branch_point})")

        except Exception as e:
            print(f"[WARNING] Failed to copy chatlogs to branch: {e}")
            # Non-fatal - branch can still be used without chatlog files
            import traceback
            traceback.print_exc()


__all__ = ["BranchHandler"]
