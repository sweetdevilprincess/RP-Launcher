"""Prompt section builders for composing agent prompts.

This module provides helpers for building discrete sections of the prompt
that are assembled by the PromptBuilder into the final agent prompt.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import AutomationContext


@dataclass(frozen=True)
class PromptSection:
    """Represents a discrete section in the composed prompt."""

    title: str
    body: str
    priority: int = 0  # Higher priority sections appear first

    def render(self) -> str:
        """Render the section with title comment if present."""
        if self.title:
            return f"<!-- {self.title} -->\n{self.body}"
        return self.body


class AuthorNotesSection:
    """Build section from AUTHOR'S_NOTES.md (highest priority)."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build author notes section if author notes are loaded.

        Args:
            context: Automation context with author_notes content

        Returns:
            PromptSection for author notes or None
        """
        if not context.author_notes or not context.author_notes.strip():
            return None

        # Build title with genome indicator if active
        title = "AUTHOR'S NOTES (ABSOLUTE RULES)"
        if context.active_genome:
            title += f" - ACTIVE GENOME: {context.active_genome}"

        return PromptSection(
            title=title,
            body=context.author_notes,
            priority=110,  # Highest priority (above all other content)
        )


class TierFilesSection:
    """Build section from tier1/tier2 files loaded by filesystem service."""

    @staticmethod
    def build(context: AutomationContext) -> list[PromptSection]:
        """Build sections from tiered file content.

        Args:
            context: Automation context with tier1_files and tier2_files

        Returns:
            List of PromptSections for tier files
        """
        sections = []

        # Tier1 files (always loaded)
        if context.tier1_files:
            tier1_content = []
            for filename, content in context.tier1_files.items():
                if content.strip():
                    tier1_content.append(f"<!-- {filename} -->\n{content}")

            if tier1_content:
                sections.append(
                    PromptSection(
                        title="TIER 1 FILES (Always Loaded)",
                        body="\n\n".join(tier1_content),
                        priority=100,
                    )
                )

        # Tier2 files (loaded periodically)
        if context.tier2_files:
            tier2_content = []
            for filename, content in context.tier2_files.items():
                if content.strip():
                    tier2_content.append(f"<!-- {filename} -->\n{content}")

            if tier2_content:
                sections.append(
                    PromptSection(
                        title="TIER 2 FILES (Periodic Refresh)",
                        body="\n\n".join(tier2_content),
                        priority=90,
                    )
                )

        return sections


class TimeTrackingSection:
    """Build section from time tracking information."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build time tracking section if time info is available.

        Args:
            context: Automation context with total_minutes and activities_desc

        Returns:
            PromptSection for time tracking or None
        """
        if context.total_minutes <= 0:
            return None

        time_text = f"**Time Elapsed:** {context.total_minutes} minutes"
        if context.activities_desc:
            time_text += f"\n**Activities:** {context.activities_desc}"

        return PromptSection(
            title="TIME TRACKING",
            body=time_text,
            priority=70,
        )


class EntitySection:
    """Build section from loaded entity information."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build entity context section.

        Args:
            context: Automation context with loaded_entities and entities_with_cores

        Returns:
            PromptSection for entities or None
        """
        if not context.loaded_entities and not context.entities_with_cores:
            return None

        entity_lines = []

        if context.loaded_entities:
            entity_lines.append(f"**Loaded Entities:** {', '.join(context.loaded_entities)}")

        if context.entities_with_cores:
            entity_lines.append(
                f"**Entities with Personality Cores:** {', '.join(context.entities_with_cores)}"
            )

        return PromptSection(
            title="ENTITY CONTEXT",
            body="\n".join(entity_lines),
            priority=60,
        )


class StoryArcSection:
    """Build section for story arc generation cue."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build story arc generation section if triggered.

        Args:
            context: Automation context with should_generate_arc flag

        Returns:
            PromptSection for story arc cue or None
        """
        if not context.should_generate_arc:
            return None

        arc_text = (
            "**Story Arc Generation:**\n"
            "This is a periodic story arc review point. Consider the overall narrative "
            "direction and suggest any adjustments to the story arc based on recent events."
        )

        return PromptSection(
            title="STORY ARC CUE",
            body=arc_text,
            priority=50,
        )


class FileUpdatesSection:
    """Build section for file update notifications."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build file updates notification section.

        Args:
            context: Automation context with update_notification

        Returns:
            PromptSection for file updates or None
        """
        if not context.update_notification:
            return None

        return PromptSection(
            title="FILE UPDATES",
            body=context.update_notification,
            priority=40,
        )


class AgentContextSection:
    """Build section from agent execution results."""

    @staticmethod
    def build(agent_context: str | None) -> PromptSection | None:
        """Build agent context section.

        Args:
            agent_context: Merged agent context string

        Returns:
            PromptSection for agent context or None
        """
        if not agent_context or not agent_context.strip():
            return None

        return PromptSection(
            title="AGENT CONTEXT",
            body=agent_context,
            priority=80,
        )


class NPCBehavioralSection:
    """Build section for NPC behavioral framework."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection | None:
        """Build NPC behavioral framework section.

        Args:
            context: Automation context with entities_with_archetypes and archetype_categories

        Returns:
            PromptSection for NPC behavioral framework or None
        """
        if not context.entities_with_archetypes and not context.entities_with_modifiers:
            return None

        lines = ["## NPC Behavioral Framework"]
        lines.append("")
        lines.append("**CRITICAL**: NPCs prioritize self-interest before helping strangers.")
        lines.append("")

        # Flag entities by archetype category
        if context.archetype_categories:
            for category, entities in context.archetype_categories.items():
                if entities:
                    # Format category name (authority_figures → Authority Figures)
                    category_label = category.replace("_", " ").title()
                    lines.append(f"**{category_label}**: {', '.join(entities)}")

        # Flag entities with contextual modifiers
        if context.entities_with_modifiers:
            lines.append(
                f"**Entities with Contextual Modifiers**: {', '.join(context.entities_with_modifiers)}"
            )

        lines.append("")
        lines.append("Refer to NPC Interaction Rules guideline (TIER 2) for behavioral matrices.")

        return PromptSection(
            title="NPC BEHAVIORAL FRAMEWORK",
            body="\n".join(lines),
            priority=65,  # Between entity context (60) and time (70)
        )


class UserMessageSection:
    """Build the final user message section."""

    @staticmethod
    def build(context: AutomationContext) -> PromptSection:
        """Build user message section (always present).

        Args:
            context: Automation context with message

        Returns:
            PromptSection for user message
        """
        return PromptSection(
            title="========== USER MESSAGE ==========",
            body=context.message,
            priority=0,  # Always last
        )


def build_all_sections(context: AutomationContext) -> list[PromptSection]:
    """Build all applicable prompt sections from context.

    Args:
        context: Automation context

    Returns:
        List of PromptSections sorted by priority (high to low)
    """
    sections = []

    # Author's Notes (highest priority)
    author_notes_section = AuthorNotesSection.build(context)
    if author_notes_section:
        sections.append(author_notes_section)

    # Tier files
    sections.extend(TierFilesSection.build(context))

    # Time tracking
    time_section = TimeTrackingSection.build(context)
    if time_section:
        sections.append(time_section)

    # Entity context
    entity_section = EntitySection.build(context)
    if entity_section:
        sections.append(entity_section)

    # NPC behavioral framework
    npc_section = NPCBehavioralSection.build(context)
    if npc_section:
        sections.append(npc_section)

    # Story arc
    arc_section = StoryArcSection.build(context)
    if arc_section:
        sections.append(arc_section)

    # File updates
    updates_section = FileUpdatesSection.build(context)
    if updates_section:
        sections.append(updates_section)

    # Agent context (if available in context)
    agent_context = context.merge_agent_context()
    agent_section = AgentContextSection.build(agent_context)
    if agent_section:
        sections.append(agent_section)

    # User message (always last)
    sections.append(UserMessageSection.build(context))

    # Sort by priority (highest first), except user message stays last
    sections.sort(key=lambda s: (s.priority, s.title), reverse=True)

    return sections
