#!/usr/bin/env python3
"""
Character Consistency Checklist Generator

Generates proactive consistency checklists for characters with Personality Cores.
This is a PREVENTION system (guides Claude while writing), NOT a validation system.

Part of Phase 1.3: Proactive Character Consistency System
"""

from pathlib import Path
from typing import List, Optional
from src.entity_manager import EntityManager


def generate_consistency_checklist(
    loaded_entity_names: List[str],
    entity_manager: EntityManager
) -> Optional[str]:
    """Generate character consistency checklist for all characters

    This checklist is injected BEFORE the user message to guide Claude's response
    generation, preventing consistency issues proactively rather than detecting
    them reactively.

    Args:
        loaded_entity_names: List of entity names that were loaded into the prompt
        entity_manager: EntityManager instance with indexed entities

    Returns:
        Consistency checklist markdown or None if no characters are loaded
    """
    if not loaded_entity_names:
        return None

    # Separate characters with Personality Cores from others
    characters_with_cores = []
    all_characters = []

    for name in loaded_entity_names:
        entity = entity_manager.get_entity(name)
        if entity:
            all_characters.append(name)
            if entity.personality_core:
                characters_with_cores.append(name)

    # No checklist needed if no characters found
    if not all_characters:
        return None

    # Build character list with Personality Core markers
    character_list_parts = []
    for name in all_characters:
        if name in characters_with_cores:
            character_list_parts.append(f"{name} (⚠️ PERSONALITY CORE)")
        else:
            character_list_parts.append(name)

    # Build checklist
    checklist = f"""<!-- ========== CHARACTER CONSISTENCY CHECKLIST ========== -->

**⚠️ BEFORE WRITING: Character Consistency Check**

Characters in scene: {', '.join(character_list_parts)}

For each character, verify:

- [ ] **Speaking Style**: Does dialogue match the character's established speaking style?
- [ ] **Core Values**: Do the character's actions align with their core values?
- [ ] **Never Do Behaviors**: Am I avoiding behaviors explicitly marked as "NEVER DO"?
- [ ] **Non-Negotiables**: Is the character following their locked/non-negotiable behaviors?
- [ ] **Positivity Bias Warning**: Am I avoiding unrealistic agreeableness or conflict avoidance?
- [ ] **Personality Integrity**: Does this character feel authentic to their established personality?
"""

    # Add separate section for Personality Core characters if any exist
    if characters_with_cores:
        checklist += f"""
---

**⚠️ PERSONALITY CORE CHARACTERS (STRICT ADHERENCE REQUIRED):**
"""
        for name in characters_with_cores:
            checklist += f"- **{name}** - Has locked Personality Core (see highlighted section above)\n"

        checklist += """
These characters' core traits are LOCKED and must be followed exactly. Personality Cores define fundamental, unchangeable aspects of the character.
"""

    checklist += "\n---\n"

    return checklist


def should_include_checklist(
    loaded_entity_names: List[str],
    entity_manager: EntityManager
) -> bool:
    """Check if any characters are loaded (checklist applies to all characters)

    Args:
        loaded_entity_names: List of entity names loaded into prompt
        entity_manager: EntityManager instance

    Returns:
        True if at least one character entity is loaded
    """
    for name in loaded_entity_names:
        entity = entity_manager.get_entity(name)
        if entity:
            return True
    return False
