#!/usr/bin/env python3
"""
Prompt Builder Module

Unified prompt building with support for both cached and non-cached modes.
Eliminates 90% code duplication between the two build methods.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from src.automation.core import log_to_file
from src.automation.story_generation import StoryGenerator
from src.automation.consistency_checklist import generate_consistency_checklist


class PromptBuilder:
    """Unified prompt building with caching support"""

    def __init__(self, rp_dir: Path, log_file: Path, entity_manager, template_manager, config: dict):
        """Initialize prompt builder

        Args:
            rp_dir: RP directory path
            log_file: Log file path
            entity_manager: EntityManager instance
            template_manager: PromptTemplateManager instance (or None)
            config: Configuration dict
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.entity_manager = entity_manager
        self.template_manager = template_manager
        self.config = config

    def build_prompt(self,
                     tier1_files: dict,
                     tier2_files: dict,
                     tier3_files: list,
                     escalated_files: list,
                     message: str,
                     response_count: int,
                     total_minutes: int,
                     activities_desc: str,
                     should_generate_arc: bool,
                     agent_context: Optional[str] = None,
                     loaded_entities: Optional[List[str]] = None,
                     update_notification: str = "",
                     cache_mode: bool = False) -> Union[str, Tuple[str, str]]:
        """Build prompt (unified method for both cached and non-cached modes)

        Args:
            tier1_files: TIER_1 files dict
            tier2_files: TIER_2 files dict
            tier3_files: TIER_3 file paths
            escalated_files: Escalated file paths
            message: User message
            response_count: Current response count
            total_minutes: Calculated time
            activities_desc: Activities description
            should_generate_arc: Whether to inject arc generation
            agent_context: Optional agent analysis context
            loaded_entities: Optional list of entity names for consistency checklist
            update_notification: File update notification
            cache_mode: If True, return (cached_context, dynamic_prompt) tuple

        Returns:
            - If cache_mode=False: single enhanced_prompt string
            - If cache_mode=True: (cached_context, dynamic_prompt) tuple
        """
        if loaded_entities is None:
            loaded_entities = []

        if cache_mode:
            # Build cached context (TIER_1 only)
            cached_context = self._build_tier1_section(tier1_files, is_cached=True)

            # Build dynamic prompt (everything else)
            dynamic_sections = []

            # FILE UPDATE NOTIFICATIONS (highest priority)
            if update_notification:
                dynamic_sections.append(update_notification)

            # Add dynamic content sections
            dynamic_sections.extend(self._build_dynamic_sections(
                should_generate_arc, response_count, total_minutes, activities_desc,
                tier2_files, tier3_files, escalated_files, agent_context, loaded_entities
            ))

            # User message
            dynamic_sections.append(f"<!-- ========== USER MESSAGE ========== -->\n{message}")

            dynamic_prompt = '\n\n'.join(dynamic_sections)
            return cached_context, dynamic_prompt

        else:
            # Build single enhanced prompt
            sections = []

            # Add all content sections
            if should_generate_arc or total_minutes > 0 or tier1_files:
                sections.extend(self._build_dynamic_sections(
                    should_generate_arc, response_count, total_minutes, activities_desc,
                    tier2_files, tier3_files, escalated_files, agent_context, loaded_entities
                ))

            # TIER_1 files (not cached in this mode)
            if tier1_files:
                sections.insert(0, self._build_tier1_section(tier1_files, is_cached=False))

            # User message
            sections.append(f"<!-- ========== USER MESSAGE ========== -->\n{message}")

            return '\n\n'.join(sections)

    def _build_tier1_section(self, tier1_files: dict, is_cached: bool = False) -> str:
        """Build TIER_1 section

        Args:
            tier1_files: TIER_1 files dict
            is_cached: Whether this is for cached context

        Returns:
            Formatted TIER_1 section
        """
        if not tier1_files:
            return ""

        cache_label = " (CACHED)" if is_cached else " (ALWAYS LOADED)"
        section = f"<!-- ========== TIER_1: CORE RP FILES{cache_label} ========== -->\n"

        for filename, content in tier1_files.items():
            section += f"\n<!-- FILE: {filename} -->\n{content}\n"

        return section

    def _build_dynamic_sections(self,
                                should_generate_arc: bool,
                                response_count: int,
                                total_minutes: int,
                                activities_desc: str,
                                tier2_files: dict,
                                tier3_files: list,
                                escalated_files: list,
                                agent_context: Optional[str],
                                loaded_entities: List[str]) -> List[str]:
        """Build all dynamic content sections

        Args:
            should_generate_arc: Whether to inject arc generation
            response_count: Current response count
            total_minutes: Calculated time
            activities_desc: Activities description
            tier2_files: TIER_2 files dict
            tier3_files: TIER_3 file paths
            escalated_files: Escalated file paths
            agent_context: Optional agent analysis context
            loaded_entities: List of entity names for consistency checklist

        Returns:
            List of formatted sections
        """
        sections = []

        # Story arc generation (if threshold reached)
        if should_generate_arc:
            story_gen = StoryGenerator(self.rp_dir, self.log_file)
            arc_instructions = story_gen.generate_story_arc_instructions(response_count)
            sections.append(arc_instructions)

        # Narrative template guidance
        if self.config.get("enable_narrative_templates", True) and self.template_manager:
            try:
                narrative_instructions = self.template_manager.generate_narrative_instructions()
                if narrative_instructions:
                    sections.append(narrative_instructions)
                    log_to_file(self.log_file, "[Narrative Template] Injected")
            except Exception as e:
                log_to_file(self.log_file, f"[Narrative Template] Error: {e}")

        # Time suggestion
        if total_minutes > 0:
            sections.append(f"⏱️ Time suggestion: {total_minutes} minutes ({activities_desc})")

        # TIER_2: Guidelines
        if tier2_files:
            tier2_section = "<!-- ========== TIER_2: GUIDELINES (PERIODIC) ========== -->\n"
            for filename, content in tier2_files.items():
                tier2_section += f"\n<!-- FILE: {filename} -->\n{content}\n"
            sections.append(tier2_section)

        # TIER_3: Triggered files (with entity card special handling)
        if tier3_files:
            tier3_section, entities_with_cores = self._build_tier3_section(tier3_files)
            sections.append(tier3_section)
        else:
            entities_with_cores = []

        # TIER_3 ESCALATED: Frequently triggered files
        if escalated_files:
            escalated_section = "<!-- ========== TIER_3 ESCALATED: FREQUENTLY USED FILES ========== -->\n"
            for file_path in escalated_files:
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        escalated_section += f"\n<!-- FILE: {file_path.name} (ESCALATED) -->\n{content}\n"
                    except Exception as e:
                        log_to_file(self.log_file, f"ERROR: Could not read escalated file {file_path.name}: {e}")
            sections.append(escalated_section)

        # Agent context (if available)
        if agent_context:
            sections.append(agent_context)

        # Character Consistency Checklist
        all_entities_to_check = self._collect_entities_for_checklist(
            entities_with_cores, loaded_entities
        )
        if all_entities_to_check:
            consistency_checklist = generate_consistency_checklist(
                all_entities_to_check,
                self.entity_manager
            )
            if consistency_checklist:
                sections.append(consistency_checklist)
                log_to_file(self.log_file, f"[Consistency Checklist] Added for: {', '.join(all_entities_to_check)}")

        return sections

    def _build_tier3_section(self, tier3_files: list) -> Tuple[str, List[str]]:
        """Build TIER_3 section with entity card special handling

        Args:
            tier3_files: List of TIER_3 file paths

        Returns:
            Tuple of (formatted_section, entities_with_cores)
        """
        tier3_section = "<!-- ========== TIER_3: TRIGGERED FILES (CONDITIONAL) ========== -->\n"
        entities_with_cores = []

        for file_path in tier3_files:
            try:
                # Check if this is an entity card (in entities/ or characters/ directory)
                is_entity = file_path.parent.name in ["entities", "characters"]

                if is_entity:
                    # Use EntityManager to load entity card with Personality Core highlighting
                    entity_name = self._extract_entity_name_from_path(file_path)
                    if entity_name:
                        entity_content = self.entity_manager.load_entity_card(entity_name, highlight_core=True)
                        if entity_content:
                            tier3_section += f"\n{entity_content}\n\n---\n"
                            # Track if this entity has a Personality Core for checklist
                            entity = self.entity_manager.get_entity(entity_name)
                            if entity and entity.personality_core:
                                entities_with_cores.append(entity_name)
                            continue

                # Not an entity card or EntityManager failed - load as regular file
                content = file_path.read_text(encoding='utf-8')
                tier3_section += f"\n<!-- FILE: {file_path.name} -->\n{content}\n"

            except Exception as e:
                log_to_file(self.log_file, f"ERROR: Could not read {file_path.name}: {e}")

        return tier3_section, entities_with_cores

    def _extract_entity_name_from_path(self, file_path: Path) -> Optional[str]:
        """Extract entity name from file path

        Handles formats like:
        - [CHAR] Sarah Mitchell.md -> Sarah Mitchell
        - Sarah Mitchell.md -> Sarah Mitchell

        Args:
            file_path: Path to entity file

        Returns:
            Entity name or None if cannot extract
        """
        filename = file_path.stem  # Get filename without extension

        # Remove [CHAR], [LOC], [ORG] tags if present
        cleaned_name = re.sub(r'^\[(?:CHAR|LOC|ORG)\]\s*', '', filename)

        # If name is empty after cleaning, return None
        if not cleaned_name or not cleaned_name.strip():
            return None

        return cleaned_name.strip()

    def _collect_entities_for_checklist(self,
                                       entities_with_cores: List[str],
                                       loaded_entities: List[str]) -> List[str]:
        """Collect all entities that need consistency checking

        Args:
            entities_with_cores: Entities from TIER_3 with Personality Cores
            loaded_entities: Additional loaded entity names

        Returns:
            List of unique entity names to check
        """
        all_entities = []

        if entities_with_cores:
            all_entities.extend(entities_with_cores)

        if loaded_entities:
            # Also check loaded_entities in case they have cores
            for entity_name in loaded_entities:
                if entity_name not in all_entities:
                    entity = self.entity_manager.get_entity(entity_name)
                    if entity and entity.personality_core:
                        all_entities.append(entity_name)

        return all_entities
