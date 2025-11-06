"""Message Handler - Handles message sending and state IPC requests.

This handler processes message-related requests including:
- SEND_MESSAGE: Send message to LLM with automation pipeline
- GET_STATE: Get current application state
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from src.automation.contracts import AutomationContext
from src.infrastructure.ipc import (
    IPCMessageType,
    IPCRequest,
    create_error_response,
    create_response,
    create_streaming_chunk,
    create_streaming_done,
)

from .base import BaseHandler

if TYPE_CHECKING:
    from ..bridge_service import BridgeService


class MessageHandler(BaseHandler):
    """Handler for message sending and state operations.

    Delegates to bridge.llm_client and automation_service for message processing.
    """

    def handle(self, request: IPCRequest) -> str:
        """Route message request to appropriate handler method.

        Args:
            request: IPC request with message operation

        Returns:
            JSON response string
        """
        request_type = IPCMessageType(request.type)

        if request_type == IPCMessageType.SEND_MESSAGE:
            return self._handle_send_message(request)
        elif request_type == IPCMessageType.GET_STATE:
            return self._handle_get_state(request)
        else:
            return create_error_response(
                request.request_id,
                f"Unknown message request type: {request.type}"
            )

    def _handle_send_message(self, request: IPCRequest) -> str:
        """Handle SEND_MESSAGE request."""
        user_message = request.data.get("user_message")
        if not user_message:
            return create_error_response(request.request_id, "Missing user_message")

        # Check if primary LLM client is available
        if not self.bridge.primary_client:
            return create_error_response(
                request.request_id,
                "No LLM provider available. "
                "Check bridge logs for initialization errors, or:\n"
                "- For Claude SDK: Run setup.sh/setup.bat to install Node.js dependencies\n"
                "- For API providers: Configure API key in Settings (F8)\n"
                "- Or enable Testing Mode in Settings (F8)"
            )

        try:
            # Step 1: Create automation context
            context = AutomationContext(
                message=user_message,
                rp_dir=self.bridge.rp_dir
            )

            # Step 2: Run automation pipeline to build enhanced prompt
            print(f"[AUTOMATION] Processing message: {user_message[:50]}...")
            automation_result = self.bridge.automation_service.run(context)

            if not automation_result.success:
                error_msg = automation_result.error or "Automation pipeline failed"
                print(f"[ERROR] Automation failed: {error_msg}")
                return create_error_response(request.request_id, f"Automation error: {error_msg}")

            # Get the enhanced prompt
            enhanced_prompt = automation_result.enhanced_prompt or user_message
            cached_context = automation_result.cached_context

            print(f"[LLM] Sending prompt to {self.bridge.current_provider}...")

            # Step 2.5: Load temperature from config
            temperature = self._get_temperature_for_provider(self.bridge.current_provider)
            print(f"[LLM] Using temperature: {temperature}")

            # Step 2.6: Load conversation history for current branch
            conversation_history = self._load_branch_conversation_history()
            print(f"[LLM] Loaded conversation history: {len(conversation_history)} messages")

            # Step 3: Check if provider supports streaming
            capabilities = self.bridge.primary_client.capabilities()

            if capabilities.supports_streaming:
                # Use streaming for real-time display
                print(f"[LLM] Streaming enabled for {self.bridge.current_provider}")

                # Call stream_message() and send chunks via IPC
                full_content = ""
                chunk_count = 0

                for chunk in self.bridge.primary_client.stream_message(
                    user_message=enhanced_prompt,
                    cached_context=cached_context,
                    conversation_history=conversation_history,
                    temperature=temperature
                ):
                    full_content += chunk
                    chunk_count += 1

                    # Send chunk to TUI
                    chunk_msg = create_streaming_chunk(
                        request.request_id,
                        chunk,
                        index=chunk_count
                    )
                    self.bridge.socket_server.send_push_message(chunk_msg)

                print(f"[LLM] Streaming complete ({chunk_count} chunks)")

                # Send streaming done message
                done_msg = create_streaming_done(
                    request.request_id,
                    provider=self.bridge.current_provider,
                    chunk_count=chunk_count
                )
                self.bridge.socket_server.send_push_message(done_msg)

                # Step 4: Run background agents with Claude's response
                response_num = context.response_count + 1
                self._run_background_agents(user_message, full_content, response_num)

                # Return final response with metadata
                # Note: streaming doesn't provide usage stats easily, so we'll estimate
                return create_response(
                    request.request_id,
                    llm_response=full_content,
                    response_num=response_num,
                    metadata={
                        "provider": self.bridge.current_provider,
                        "streaming": True,
                        "chunk_count": chunk_count,
                    }
                )

            else:
                # Use non-streaming for providers that don't support it
                print(f"[LLM] Non-streaming mode for {self.bridge.current_provider}")

                llm_response = self.bridge.primary_client.send_message(
                    user_message=enhanced_prompt,
                    cached_context=cached_context,
                    conversation_history=conversation_history,
                    temperature=temperature
                )

                print(f"[LLM] Received response ({llm_response.usage.total_tokens()} tokens)")

                # Step 4: Run background agents with Claude's response
                response_num = context.response_count + 1
                self._run_background_agents(user_message, llm_response.content, response_num)

                # Step 5: Return LLM response via IPC
                return create_response(
                    request.request_id,
                    llm_response=llm_response.content,
                    response_num=response_num,
                    metadata={
                        "provider": self.bridge.current_provider,
                        "streaming": False,
                        "input_tokens": llm_response.usage.input_tokens,
                        "output_tokens": llm_response.usage.output_tokens,
                        "total_tokens": llm_response.usage.total_tokens(),
                        "cache_creation_tokens": llm_response.usage.cache_creation_input_tokens,
                        "cache_read_tokens": llm_response.usage.cache_read_input_tokens,
                    }
                )

        except Exception as e:
            print(f"[ERROR] Message processing failed: {e}")
            traceback.print_exc()
            return create_error_response(
                request.request_id,
                f"Error processing message: {str(e)}"
            )

    def _handle_get_state(self, request: IPCRequest) -> str:
        """Handle GET_STATE request."""
        # TODO: Get state from automation service once session management is implemented
        # For now, return basic state information
        state = {
            "rp_dir": str(self.bridge.rp_dir),
            "provider": self.bridge.current_provider,
            "testing_mode": self.bridge.testing_mode,
        }

        return create_response(
            request.request_id,
            state=state
        )

    def _run_background_agents(
        self,
        user_message: str,
        claude_response: str,
        message_number: int
    ) -> None:
        """Run background agents to analyze Claude's response.

        Args:
            user_message: The user's original message
            claude_response: Claude's generated response
            message_number: Current message number

        Note:
            Runs asynchronously in background - errors are logged but don't affect response
        """
        try:
            # Get background agent strategy from automation service
            # The strategy is buried inside the agent runner, so we need to access it
            if not hasattr(self.bridge.automation_service, '_agent_runner'):
                print("[INFO] No agent runner configured, saving message without agent data")
                self._save_message_to_session(user_message, claude_response, message_number, {})
                return  # No agent runner configured

            agent_runner = self.bridge.automation_service._agent_runner
            if not hasattr(agent_runner, '_strategies'):
                print("[INFO] No agent strategies configured, saving message without agent data")
                self._save_message_to_session(user_message, claude_response, message_number, {})
                return

            # Find the background agent strategy
            from src.automation.agents.background_agent_strategy import BackgroundAgentStrategy
            background_strategy = None
            for strategy in agent_runner._strategies:
                if isinstance(strategy, BackgroundAgentStrategy):
                    background_strategy = strategy
                    break

            if not background_strategy:
                print("[INFO] No background agents configured, saving message without agent data")
                self._save_message_to_session(user_message, claude_response, message_number, {})
                return  # No background agents configured

            # Execute background agents with Claude's response
            print(f"[AGENTS] Running background agents for message #{message_number}...")
            results = background_strategy.execute_post_response(
                user_message=user_message,
                claude_response=claude_response,
                message_number=message_number,
                rp_dir=self.bridge.rp_dir
            )

            success_count = sum(1 for r in results.values() if r.get("success", False))
            print(f"[AGENTS] Background agents complete: {success_count}/{len(results)} successful")

            # After background agents complete, save message with scene_context snapshot
            self._save_message_to_session(
                user_message=user_message,
                claude_response=claude_response,
                message_number=message_number,
                agent_results=results
            )

        except Exception as e:
            # Don't fail the response if agents fail
            print(f"[WARNING] Background agents failed: {e}")
            import traceback
            traceback.print_exc()

            # Still save message even if agents failed
            self._save_message_to_session(
                user_message=user_message,
                claude_response=claude_response,
                message_number=message_number,
                agent_results={}  # Empty results since agents failed
            )

    def _save_message_to_session(
        self,
        user_message: str,
        claude_response: str,
        message_number: int,
        agent_results: dict
    ) -> None:
        """Save message to session with scene_context snapshot.

        Args:
            user_message: User's message
            claude_response: Claude's response
            message_number: Current message number
            agent_results: Results from background agents

        Note:
            Errors are logged but don't affect the response flow
        """
        try:
            # Get scene_context snapshot (after all agents have updated it)
            scene_context = self.bridge.session_state_service.get_scene_context(self.bridge.rp_dir)

            # Extract chapter number
            chapter = self._extract_chapter_number(scene_context)

            # Prepare agent data for storage
            agent_data_background = {
                "scene_context_snapshot": scene_context,
                "agent_results": agent_results
            }

            # Save message via SessionWriteBack
            response_num = self.bridge.session_writeback.append_message(
                user_message=user_message,
                assistant_response=claude_response,
                chapter=chapter,
                agent_data_background=agent_data_background,
                model_info={"provider": self.bridge.current_provider}
            )

            print(f"[SESSION] Message #{response_num} saved to session (Chapter {chapter})")

            # Also append to chapter file for organized view
            session = self.bridge.session_repository.load_active_session()
            latest_message = session.messages[-1]  # Message we just added

            # Check for chapter transition
            self._handle_chapter_transition(session, latest_message)

            # Append to current chapter file
            self.bridge.chatlog_organizer.append_message_to_chapter(
                session_id=session.session_id,
                message=latest_message
            )
            print(f"[CHATLOG] Message #{response_num} appended to chapter {chapter} file")

        except Exception as e:
            print(f"[WARNING] Failed to save message to session: {e}")
            import traceback
            traceback.print_exc()

    def _handle_chapter_transition(self, session, current_message) -> None:
        """Handle chapter transitions and finalization.

        When a chapter changes, finalize the previous chapter.
        In the future, this can prompt the user for a chapter title.

        Args:
            session: Current session data
            current_message: Latest message that was just added
        """
        # Need at least 2 messages to detect a transition
        if len(session.messages) < 2:
            return

        previous_message = session.messages[-2]
        current_chapter = current_message.chapter
        previous_chapter = previous_message.chapter

        # Check if chapter changed
        if current_chapter != previous_chapter:
            print(f"[CHATLOG] Chapter transition detected: {previous_chapter} → {current_chapter}")

            # Finalize previous chapter with empty title
            # TODO: In the future, prompt user for chapter title via IPC
            # For now, chapters can be named manually or left blank
            try:
                self.bridge.chatlog_organizer.finalize_chapter(
                    session_id=session.session_id,
                    chapter_number=previous_chapter,
                    chapter_title=""  # Empty for now - can be set later
                )
                print(f"[CHATLOG] Chapter {previous_chapter} finalized")
            except Exception as e:
                print(f"[WARNING] Failed to finalize chapter {previous_chapter}: {e}")

    def _extract_chapter_number(self, scene_context: dict) -> int:
        """Extract chapter number from scene_context.

        Args:
            scene_context: Scene context dict

        Returns:
            Chapter number (defaults to 1 if not found)
        """
        # Try to get chapter from scene_context
        chapter_str = scene_context.get("chapter", "1")

        # Parse chapter number (handle "Chapter 1", "1", etc.)
        try:
            # Remove "Chapter " prefix if present
            if isinstance(chapter_str, str):
                chapter_str = chapter_str.replace("Chapter ", "").replace("chapter ", "").strip()
            return int(chapter_str)
        except (ValueError, TypeError):
            # Default to chapter 1 if parsing fails
            return 1

    def _get_temperature_for_provider(self, provider: str) -> float:
        """Load temperature setting from config for the given provider.

        Args:
            provider: Provider name (e.g., "claude_api_client")

        Returns:
            Temperature value (defaults to 1.0 if not configured)
        """
        # Load config
        config = self.bridge.config_loader.load()

        # Get temperature from provider's module config
        provider_config = config.get("modules", {}).get(provider, {}).get("config", {})
        temperature = provider_config.get("temperature", 1.0)

        # Handle empty string or None (use default)
        if temperature == "" or temperature is None:
            temperature = 1.0

        # Convert to float and clamp to valid range
        try:
            temperature = float(temperature)
            # Clamp to 0.0-2.0 range (supports both Claude 0-1 and OpenAI/OpenRouter 0-2)
            temperature = max(0.0, min(2.0, temperature))
        except (ValueError, TypeError):
            print(f"[WARNING] Invalid temperature value for {provider}: {temperature}, using 1.0")
            temperature = 1.0

        return temperature

    def _load_branch_conversation_history(self) -> list[dict[str, str]]:
        """Load conversation history for currently active branch.

        This method loads all messages from the current session/branch and converts
        them to the conversation history format expected by LLM clients.

        The session_repository.load_active_session() automatically handles branch
        awareness by checking session_state_service to determine which timeline
        is currently active (main or a branch).

        Returns:
            List of conversation messages in format:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

        Note:
            Returns empty list on error to avoid breaking the message flow.
            Works with ALL LLM providers (SDK, API, OpenAI, OpenRouter, etc.)
        """
        try:
            # Load active session (automatically uses correct branch based on session state)
            session = self.bridge.session_repository.load_active_session()

            # Convert SessionMessage objects to conversation history format
            history = []
            for msg in session.messages:
                history.append({"role": "user", "content": msg.user_message})
                history.append({"role": "assistant", "content": msg.assistant_response})

            return history

        except Exception as e:
            print(f"[WARNING] Failed to load conversation history: {e}")
            import traceback
            traceback.print_exc()
            # Return empty history on error - don't break the flow
            return []


__all__ = ["MessageHandler"]
