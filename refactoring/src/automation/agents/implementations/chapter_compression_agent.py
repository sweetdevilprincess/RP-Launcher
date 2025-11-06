"""Chapter Compression Agent - Generate chapter summaries using primary LLM.

This agent orchestrates the chapter compression workflow:
1. Loads chapter_compression_protocol.md
2. Extracts chapter content from session history
3. Calls PRIMARY LLM to generate ~3,000 word summary
4. Saves summary to chapters/chapter_{X}_summary.md
5. Triggers ContradictionSynthesisAgent async
6. Updates chapter number in scene_context

Unlike other agents, this uses the PRIMARY LLM (the same LLM the user is roleplaying with)
for better quality summaries that match the narrative voice.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base_agent import BaseAgent

if TYPE_CHECKING:
    from src.presentation.bridge.bridge_service import BridgeService


class ChapterCompressionAgent(BaseAgent):
    """Generate comprehensive chapter summaries using the primary LLM.

    This agent:
    1. Loads compression protocol for instructions
    2. Extracts all messages in chapter range
    3. Builds detailed prompt for primary LLM
    4. Generates ~3,000 word summary with quotes
    5. Saves to chapters/chapter_{X}_summary.md
    6. Triggers background contradiction synthesis
    7. Updates scene_context with new chapter number

    Example usage:
        agent.execute(
            chapter_number=1,
            message_range=(1, 47),
            chapter_title="The Tavern Incident",
            tags=["combat", "mystery"]
        )
    """

    def get_agent_id(self) -> str:
        """Return unique agent identifier."""
        return "chapter_compression"

    def execute(
        self,
        chapter_number: int,
        message_range: tuple[int, int] | None = None,
        chapter_title: str = "",
        tags: list[str] | None = None,
        session_id: str = "main",
        **kwargs
    ) -> dict[str, Any]:
        """Execute chapter compression workflow.

        Args:
            chapter_number: Chapter number being compressed (e.g., 1)
            message_range: Optional (start_msg, end_msg) tuple. If None, uses all messages in current chapter.
            chapter_title: Optional user-provided title for the chapter
            tags: Optional list of tags for categorization
            session_id: Session ID (default: "main")
            **kwargs: Additional context

        Returns:
            Dict with:
                - success: bool
                - summary_path: Path to saved summary
                - word_count: Number of words in summary
                - original_word_count: Number of words in original chapter
                - compression_ratio: Percentage
                - chapter_number: Chapter that was compressed
                - error: Error message if failed
        """
        try:
            self.log(f"Starting chapter {chapter_number} compression")

            # Step 1: Load compression protocol
            protocol = self._load_protocol()
            if not protocol:
                return {
                    "success": False,
                    "error": "Failed to load chapter_compression_protocol.md"
                }

            # Step 2: Extract chapter content from session history
            chapter_data = self._extract_chapter_content(
                chapter_number=chapter_number,
                message_range=message_range,
                session_id=session_id
            )

            if not chapter_data["chapter_content"]:
                return {
                    "success": False,
                    "error": "No chapter content found to compress"
                }

            self.log(f"Extracted {chapter_data['message_count']} messages, {chapter_data['word_count']} words")

            # Step 3: Build compression prompt for primary LLM
            compression_prompt = self._build_compression_prompt(
                protocol=protocol,
                chapter_data=chapter_data,
                chapter_number=chapter_number,
                chapter_title=chapter_title
            )

            # Step 4: Call PRIMARY LLM for compression
            self.log("Calling primary LLM for chapter compression...")
            summary = self.call_llm(
                user_message=compression_prompt,
                temperature=0.7,  # Slightly creative for narrative flow
                use_primary=True  # IMPORTANT: Use primary LLM, not secondary
            )

            if not summary or len(summary.strip()) < 500:
                return {
                    "success": False,
                    "error": "LLM returned insufficient summary content"
                }

            summary_word_count = len(summary.split())
            self.log(f"Generated summary: {summary_word_count} words")

            # Step 5: Save summary to chapters/ folder
            summary_path = self._save_summary(
                summary=summary,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                tags=tags or [],
                chapter_data=chapter_data,
                session_id=session_id
            )

            # Step 6: Trigger contradiction synthesis (async)
            self._trigger_contradiction_synthesis(
                chapter_number=chapter_number,
                message_range=chapter_data["message_range"],
                session_id=session_id
            )

            # Step 7: Update chapter number in scene_context
            self._increment_chapter_number(chapter_number)

            compression_ratio = (summary_word_count / chapter_data['word_count'] * 100) if chapter_data['word_count'] > 0 else 0

            result = {
                "success": True,
                "summary_path": str(summary_path),
                "word_count": summary_word_count,
                "original_word_count": chapter_data['word_count'],
                "compression_ratio": f"{compression_ratio:.0f}%",
                "chapter_number": chapter_number,
                "message_range": chapter_data["message_range"],
                "message_count": chapter_data["message_count"]
            }

            self.log(f"Chapter {chapter_number} compression complete: {summary_path}")
            return result

        except Exception as e:
            self.log(f"Error in chapter compression: {e}")
            import traceback
            self.log(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    # ==========================================================================
    # Protocol Loading
    # ==========================================================================

    def _load_protocol(self) -> str:
        """Load chapter compression protocol from config/guidelines/.

        Returns:
            Protocol content as string, or empty string if failed
        """
        # Try to find protocol file
        # First check in refactoring root config/guidelines
        protocol_path = None

        # Look up from rp_dir to find config/guidelines
        search_dir = self.rp_dir
        for _ in range(5):  # Search up to 5 levels
            candidate = search_dir / "config" / "guidelines" / "chapter_compression_protocol.md"
            if candidate.exists():
                protocol_path = candidate
                break
            search_dir = search_dir.parent

        if not protocol_path:
            self.log("Could not find chapter_compression_protocol.md")
            return ""

        try:
            with open(protocol_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.log(f"Loaded protocol from {protocol_path} ({len(content)} chars)")
            return content
        except Exception as e:
            self.log(f"Failed to read protocol: {e}")
            return ""

    # ==========================================================================
    # Chapter Content Extraction
    # ==========================================================================

    def _extract_chapter_content(
        self,
        chapter_number: int,
        message_range: tuple[int, int] | None,
        session_id: str
    ) -> dict[str, Any]:
        """Extract chapter content from session history.

        Args:
            chapter_number: Chapter number
            message_range: Optional (start, end) message range
            session_id: Session ID

        Returns:
            Dict with chapter_content, message_count, word_count, message_range, etc.
        """
        session_file = self.rp_dir / "sessions" / f"session_{session_id}.json"

        if not session_file.exists():
            self.log(f"Session file not found: {session_file}")
            return {
                "chapter_content": "",
                "message_count": 0,
                "word_count": 0,
                "message_range": (0, 0),
                "characters": [],
                "locations": []
            }

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except Exception as e:
            self.log(f"Failed to load session file: {e}")
            return {
                "chapter_content": "",
                "message_count": 0,
                "word_count": 0,
                "message_range": (0, 0),
                "characters": [],
                "locations": []
            }

        all_messages = session_data.get("messages", [])

        # Determine message range
        if message_range:
            start_msg, end_msg = message_range
        else:
            # Use all messages in current chapter (or all if no chapter tracking)
            start_msg = 1
            end_msg = len(all_messages)

        # Extract messages in range
        chapter_messages = []
        characters = set()
        locations = set()

        for msg in all_messages:
            msg_num = msg.get("response_num", msg.get("message_number", 0))

            if start_msg <= msg_num <= end_msg:
                chapter_messages.append(msg)

                # Extract characters and locations
                scene_ctx = msg.get("agent_data_background", {}).get("scene_context_snapshot", {})
                if not scene_ctx:
                    scene_ctx = msg.get("scene_context_snapshot", {})

                chars = scene_ctx.get("characters_in_scene", [])
                loc = scene_ctx.get("location", "")

                characters.update(chars)
                if loc and loc != "Unknown":
                    locations.add(loc)

        # Build chapter content for LLM
        content_parts = []
        total_words = 0

        for msg in chapter_messages:
            msg_num = msg.get("response_num", msg.get("message_number", 0))
            user_msg = msg.get("user_message", "")
            assistant_msg = msg.get("assistant_response", msg.get("claude_response", ""))

            content_parts.append(f"**Message {msg_num}:**")
            content_parts.append(f"**User:** {user_msg}")
            content_parts.append(f"**Assistant:** {assistant_msg}")
            content_parts.append("")  # Blank line

            total_words += len(user_msg.split()) + len(assistant_msg.split())

        chapter_content = "\n".join(content_parts)

        self.log(f"Extracted messages {start_msg}-{end_msg}: {len(chapter_messages)} messages, {total_words} words")

        return {
            "chapter_content": chapter_content,
            "message_count": len(chapter_messages),
            "word_count": total_words,
            "message_range": (start_msg, end_msg),
            "characters": list(characters),
            "locations": list(locations)
        }

    # ==========================================================================
    # Prompt Building
    # ==========================================================================

    def _build_compression_prompt(
        self,
        protocol: str,
        chapter_data: dict[str, Any],
        chapter_number: int,
        chapter_title: str
    ) -> str:
        """Build compression prompt for primary LLM.

        Args:
            protocol: Full protocol text
            chapter_data: Extracted chapter data
            chapter_number: Chapter number
            chapter_title: Optional user-provided title

        Returns:
            Complete prompt string
        """
        title_text = f": {chapter_title}" if chapter_title else ""

        return f"""You are compressing Chapter {chapter_number}{title_text} into a long-term summary for future reference.

Follow the Chapter Compression Protocol below exactly:

{protocol}

---

CHAPTER TO COMPRESS:

Chapter {chapter_number}{title_text}
Messages: {chapter_data['message_range'][0]} - {chapter_data['message_range'][1]}
Total messages: {chapter_data['message_count']}
Characters present: {', '.join(chapter_data['characters']) if chapter_data['characters'] else 'None detected'}
Locations: {', '.join(chapter_data['locations']) if chapter_data['locations'] else 'Unknown'}

---

FULL CHAPTER CONTENT:

{chapter_data['chapter_content']}

---

Generate the chapter summary now, following the protocol format exactly. Target ~3,000 words.
"""

    # ==========================================================================
    # Summary Saving
    # ==========================================================================

    def _save_summary(
        self,
        summary: str,
        chapter_number: int,
        chapter_title: str,
        tags: list[str],
        chapter_data: dict[str, Any],
        session_id: str
    ) -> Path:
        """Save chapter summary to chapters/ folder with metadata.

        Args:
            summary: Generated summary text
            chapter_number: Chapter number
            chapter_title: User-provided title (or empty)
            tags: List of tags
            chapter_data: Chapter metadata
            session_id: Session ID

        Returns:
            Path to saved file
        """
        chapters_dir = self.rp_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        # Build filename
        filename = f"chapter_{chapter_number}_summary.md"
        file_path = chapters_dir / filename

        # Build frontmatter
        summary_word_count = len(summary.split())
        compression_ratio = (summary_word_count / chapter_data['word_count'] * 100) if chapter_data['word_count'] > 0 else 0

        frontmatter = f"""---
chapter_number: {chapter_number}
title: "{chapter_title if chapter_title else f"Chapter {chapter_number}"}"
tags: {json.dumps(tags)}
compressed_at: "{datetime.now(timezone.utc).isoformat()}"
session_id: "{session_id}"
message_range: {list(chapter_data['message_range'])}
message_count: {chapter_data['message_count']}
word_count: {summary_word_count}
original_word_count: {chapter_data['word_count']}
compression_ratio: "{compression_ratio:.0f}%"
characters: {json.dumps(chapter_data['characters'])}
locations: {json.dumps(chapter_data['locations'])}
---

"""

        # Combine frontmatter + summary
        full_content = frontmatter + summary

        # Write to file atomically
        temp_file = file_path.with_suffix(".md.tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(full_content)
            temp_file.replace(file_path)
            self.log(f"Saved chapter summary to {file_path}")
        except Exception as e:
            self.log(f"Failed to save summary: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

        return file_path

    # ==========================================================================
    # Contradiction Synthesis Integration
    # ==========================================================================

    def _trigger_contradiction_synthesis(
        self,
        chapter_number: int,
        message_range: tuple[int, int],
        session_id: str
    ) -> None:
        """Trigger ContradictionSynthesisAgent in background.

        Args:
            chapter_number: Chapter number
            message_range: Message range
            session_id: Session ID
        """
        try:
            # Import here to avoid circular dependencies
            from .contradiction_synthesis_agent import ContradictionSynthesisAgent

            contradiction_agent = ContradictionSynthesisAgent(
                bridge=self.bridge,
                rp_dir=self.rp_dir
            )

            # Run in background (don't block compression completion)
            # Bridge should handle async execution
            self.log(f"Triggering contradiction synthesis for chapter {chapter_number}")

            # Execute agent (bridge will handle async if configured)
            contradiction_agent.execute(
                chapter_number=chapter_number,
                message_range=message_range,
                session_id=session_id
            )

            self.log("Contradiction synthesis triggered successfully")

        except Exception as e:
            self.log(f"Failed to trigger contradiction synthesis: {e}")
            # Don't fail the compression if contradiction analysis fails

    # ==========================================================================
    # State Updates
    # ==========================================================================

    def _increment_chapter_number(self, current_chapter: int) -> None:
        """Update scene_context with next chapter number.

        Args:
            current_chapter: Chapter that was just compressed
        """
        try:
            next_chapter = current_chapter + 1

            # Use session state service to update chapter
            if self.bridge and self.bridge.session_state_service:
                self.bridge.session_state_service.set_current_chapter(
                    self.rp_dir,
                    f"Chapter {next_chapter}"
                )
                self.log(f"Updated scene_context: Chapter {current_chapter} → Chapter {next_chapter}")
            else:
                self.log("Warning: Could not update chapter number (no session state service)")

        except Exception as e:
            self.log(f"Failed to update chapter number: {e}")
            # Don't fail compression if state update fails


__all__ = ["ChapterCompressionAgent"]
