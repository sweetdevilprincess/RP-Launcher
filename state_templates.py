"""
State File Templates for RP System
Provides templates for all state management files.
"""

from typing import Dict, Any
from datetime import datetime


class StateTemplates:
    """
    Template generator for state management files.
    """

    @staticmethod
    def plot_threads_master() -> str:
        """
        Generate template for plot_threads_master.md

        Returns:
            Markdown template string
        """
        return """# PLOT THREADS MASTER FILE

## Metadata
- **Total Active Threads**: 0
- **Last Updated**: {timestamp}
- **Current Chapter**: 1
- **Current Response**: 0

---

## Instructions
This file tracks all active plot threads in the story. Each thread includes:
- Unique ID (THREAD-###)
- Status (Active, Critical, or Resolved)
- Priority (Low, Medium, High)
- Time sensitivity and consequence countdowns
- Related characters, locations, and memories
- Suggested actions and natural consequences

Threads are automatically tracked by the DeepSeek analysis system.
Manual entries are also supported.

---

## Active Threads

<!-- Active plot threads will appear here -->

---

## Recently Resolved Threads

<!-- Recently resolved threads will appear here before archiving -->

---

## Thread Statistics

**By Priority:**
- High: 0
- Medium: 0
- Low: 0

**By Status:**
- Active: 0
- Critical (consequence triggered): 0
- Resolved: 0

**Time-Sensitive Threads:**
- Immediate (0-5 responses): 0
- Near-term (6-15 responses): 0
- Long-term (16+ responses): 0
""".format(timestamp=datetime.now().isoformat())

    @staticmethod
    def knowledge_base() -> str:
        """
        Generate template for knowledge_base.md

        Returns:
            Markdown template string
        """
        return """# WORLD KNOWLEDGE BASE

## Metadata
- **Last Updated**: {timestamp}
- **Current Chapter**: 1
- **Total Entries**: 0

---

## Instructions
This file contains all world-building knowledge extracted from the story.
It serves as a comprehensive reference for:
- Setting details (genre, time period, technology level)
- Geography (locations, neighborhoods, landmarks)
- Organizations (companies, institutions, groups)
- Cultural practices and customs
- Important items and artifacts
- Story themes and tone

Knowledge is automatically extracted by DeepSeek analysis.

---

## Setting

**Genre**: (To be established)
**Time Period**: (To be established)
**Primary Location**: (To be established)
**Technology Level**: (To be established)

*(Source: To be established)*

---

## Geography

### Locations

<!-- Locations will be added here -->

### Regions

<!-- Regions will be added here -->

---

## Organizations

<!-- Organizations will be added here -->

---

## Locations (Detailed)

<!-- Detailed location descriptions will be added here -->

---

## Cultural Details

<!-- Cultural practices and customs will be added here -->

---

## Important Items

<!-- Significant items and artifacts will be added here -->

---

## Story Themes

<!-- Story themes will be added here -->

---

## Tone & Style

<!-- Tone and style notes will be added here -->

---

## World Rules

<!-- Rules about how the world works (magic systems, technology limits, etc.) -->

---

## Historical Events

<!-- Past events that shape the current story -->
""".format(timestamp=datetime.now().isoformat())

    @staticmethod
    def current_state() -> str:
        """
        Generate template for current_state.md

        Returns:
            Markdown template string
        """
        return """# CURRENT STATE

## Story Progress
- **Current Chapter**: 1
- **Current Response**: 0
- **Last Updated**: {timestamp}
- **Session**: 1

---

## Active Scene

**Location**: (No active scene)
**Characters Present**: None
**Time of Day**: (Not established)
**Weather**: (Not established)
**Mood**: (Not established)

---

## Recent Events Summary

<!-- Last 3-5 major events will be summarized here -->

---

## Active Characters

### In Current Scene
- None

### Recently Mentioned (Not in Scene)
- None

### Off-Screen
- None

---

## Current Plot Focus

**Primary Thread**: (None)
**Secondary Threads**: (None)

---

## Pacing & Tension

**Current Tension Level**: Neutral (5/10)
**Recent Scene Types**: (Not enough data)
**Pacing**: Normal

---

## User Notes

<!-- User can add manual notes here -->
""".format(timestamp=datetime.now().isoformat())

    @staticmethod
    def entity_tracker() -> Dict[str, Any]:
        """
        Generate template for entity_tracker.json

        Returns:
            Dictionary template
        """
        return {
            "last_updated": datetime.now().isoformat(),
            "current_chapter": 1,
            "current_response": 0,
            "characters": {},
            "locations": {},
            "organizations": {},
            "items": {}
        }

    @staticmethod
    def relationship_tracker() -> Dict[str, Any]:
        """
        Generate template for relationship_tracker.json

        Returns:
            Dictionary template
        """
        return {
            "last_updated": datetime.now().isoformat(),
            "current_chapter": 1,
            "current_response": 0,
            "relationships": {},
            "recent_tier_changes": []
        }

    @staticmethod
    def memory_index() -> Dict[str, Any]:
        """
        Generate template for memory_index.json

        Returns:
            Dictionary template
        """
        return {
            "last_updated": datetime.now().isoformat(),
            "total_memories": 0,
            "memories_by_character": {},
            "memories_by_chapter": {},
            "recent_memories": []
        }

    @staticmethod
    def automation_config() -> Dict[str, Any]:
        """
        Generate template for automation_config.json

        Returns:
            Dictionary template
        """
        return {
            "last_updated": datetime.now().isoformat(),
            "deepseek_integration": {
                "enabled": True,
                "api_endpoint": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "background_analysis": True,
                "analysis_delay": 0
            },
            "context_intelligence": {
                "enabled": True,
                "three_tier_loading": True,
                "token_budget": {
                    "max_entities": 50000,
                    "max_memories": 10000,
                    "max_plot_threads": 5000
                }
            },
            "plot_tracking": {
                "enabled": True,
                "auto_extract_threads": True,
                "enable_consequences": True,
                "consequence_countdowns": {
                    "high_priority": 5,
                    "medium_priority": 10,
                    "low_priority": 20
                }
            },
            "memory_system": {
                "enabled": True,
                "auto_extract": True,
                "max_memories_per_character": 500,
                "relevance_threshold": 0.7
            },
            "relationship_system": {
                "enabled": True,
                "auto_analyze": True,
                "tier_threshold": 15
            },
            "character_consistency": {
                "enabled": True,
                "always_load_cores": True,
                "include_checklist": True
            },
            "enable_narrative_templates": True,
            "narrative_template": {
                "mode": "auto"
                # Supported modes:
                # - "auto": Smart detection from ROLEPLAY_OVERVIEW.md Genre field
                # - "composite": Pre-made genre combination template
                #     {"mode": "composite", "template": "dark_romance_thriller"}
                # - "modular": Mix sections from different genres
                #     {"mode": "modular", "sections": {"tone_and_atmosphere": "horror", "pacing": "thriller", "dialogue_style": "dark_romance"}}
                # - "layered": Primary genre + secondary highlights
                #     {"mode": "layered", "primary": "dark_romance", "secondary": "thriller"}
            },
            "knowledge_base": {
                "enabled": True,
                "auto_extract": True,
                "load_full_document": True
            },
            "pacing_analysis": {
                "enabled": True,
                "scene_variety_check": True,
                "tension_tracking": True
            }
        }

    @staticmethod
    def character_memory_template(character_name: str) -> str:
        """
        Generate template for character-specific memory file.

        Args:
            character_name: Name of the character

        Returns:
            Markdown template string
        """
        return """# {character_name} - Memories

## Metadata
- **Character**: {character_name}
- **Last Updated**: {timestamp}
- **Total Memories**: 0

---

## Instructions
This file contains all memories for {character_name}.
Memories are automatically extracted by DeepSeek analysis.
Each memory includes:
- Unique ID (MEM-###)
- Description
- Emotional significance
- Related characters
- Source (chapter/response)
- Tags

---

## Recent Memories (Last 10)

<!-- Most recent memories appear here -->

---

## All Memories

<!-- All memories in chronological order -->

---

## Memory Statistics

**By Type:**
- Emotional: 0
- Factual: 0
- Sensory: 0
- Relationship: 0

**By Chapter:**
<!-- Chapter breakdown will appear here -->
""".format(
            character_name=character_name,
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def plot_threads_archive() -> str:
        """
        Generate template for plot_threads_archive.md

        Returns:
            Markdown template string
        """
        return """# PLOT THREADS ARCHIVE

## Metadata
- **Total Archived Threads**: 0
- **Last Updated**: {timestamp}

---

## Instructions
This file contains all resolved plot threads.
Threads are automatically archived when marked as resolved.
Archive maintains full thread history for reference.

---

## Resolved Threads (Chronological)

<!-- Resolved threads will appear here in chronological order -->
""".format(timestamp=datetime.now().isoformat())

    @staticmethod
    def file_tracking() -> Dict[str, Any]:
        """
        Generate template for file_tracking.json

        Returns:
            Dictionary template
        """
        return {
            "last_updated": datetime.now().isoformat(),
            "tracked_files": {}
        }

    @staticmethod
    def chapter_template(chapter_num: int) -> str:
        """
        Generate template for a chapter file.

        Args:
            chapter_num: Chapter number

        Returns:
            Markdown template string
        """
        return """# Chapter {chapter_num}

## Chapter Metadata
- **Chapter Number**: {chapter_num}
- **Started**: {timestamp}
- **Status**: In Progress

---

## Chapter Summary

(Summary will be added as chapter progresses)

---

## Responses

<!-- Individual responses will be appended here -->
""".format(
            chapter_num=chapter_num,
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def entity_card_template(entity_name: str, entity_type: str = "character") -> str:
        """
        Generate template for an entity card.

        Args:
            entity_name: Name of the entity
            entity_type: Type of entity (character, location, organization)

        Returns:
            Markdown template string
        """
        if entity_type == "character":
            return StateTemplates._character_card_template(entity_name)
        elif entity_type == "location":
            return StateTemplates._location_card_template(entity_name)
        elif entity_type == "organization":
            return StateTemplates._organization_card_template(entity_name)
        else:
            return StateTemplates._generic_card_template(entity_name, entity_type)

    @staticmethod
    def _character_card_template(character_name: str) -> str:
        """Character-specific entity card template."""
        return """[CHAR] {character_name}

## PERSONALITY CORE (LOCKED - DO NOT CHANGE)
These traits are fundamental to {character_name}'s character and MUST remain consistent:

### Core Values
- **Primary**: (To be established)
- **Secondary**: (To be established)

### Fatal Flaws
- (To be established)

### Speaking Style
- (To be established)

### Baseline Temperament
- (To be established)

### Non-Negotiable Behaviors
These are things {character_name} ALWAYS does:
- (To be established)

### Contradictory Behaviors (NEVER DO)
These actions would be completely out of character:
- (To be established)

### Character Growth Areas (CAN EVOLVE)
These aspects can change through story events:
- (To be established)

---

## DYNAMIC TRAITS (CAN EVOLVE)

### Current Mood
(To be established)

### Recent Character Development
- (None yet)

### Current Relationships
(See relationships section)

### Temporary States
- (None)

---

## PHYSICAL DESCRIPTION

**Appearance**: (To be established)
**Age**: (To be established)
**Distinctive Features**: (To be established)

---

## BACKGROUND

**History**: (To be established)
**Occupation**: (To be established)
**Skills/Abilities**: (To be established)

---

## RELATIONSHIPS

(Relationships will be tracked separately in relationship files)

---

## NOTES

(Additional notes)
""".format(character_name=character_name)

    @staticmethod
    def _location_card_template(location_name: str) -> str:
        """Location-specific entity card template."""
        return """[LOC] {location_name}

## CORE DETAILS

**Type**: (e.g., cafe, apartment, office, park)
**Address**: (If applicable)
**Description**: (To be established)

---

## ATMOSPHERE

**Ambiance**: (To be established)
**Typical Crowd**: (To be established)
**Notable Features**: (To be established)

---

## LAYOUT

(Describe the layout and key areas)

---

## SIGNIFICANCE

**Story Role**: (Why is this location important?)
**Frequent Visitors**: (Which characters visit here often?)

---

## HISTORY

(Location's history and backstory)

---

## NOTES

(Additional notes)
""".format(location_name=location_name)

    @staticmethod
    def _organization_card_template(org_name: str) -> str:
        """Organization-specific entity card template."""
        return """[ORG] {org_name}

## CORE DETAILS

**Type**: (e.g., company, institution, group)
**Size**: (e.g., small, medium, large)
**Founded**: (If known)
**Location**: (Where is it based?)

---

## PURPOSE

**Mission**: (What does this organization do?)
**Reputation**: (How is it viewed?)

---

## STRUCTURE

**Leadership**: (Who runs it?)
**Key Members**: (Important people in the organization)

---

## SIGNIFICANCE

**Story Role**: (Why is this organization important?)
**Related Characters**: (Which characters are connected?)

---

## NOTES

(Additional notes)
""".format(org_name=org_name)

    @staticmethod
    def _generic_card_template(entity_name: str, entity_type: str) -> str:
        """Generic entity card template."""
        return """[{entity_type_upper}] {entity_name}

## CORE DETAILS

(Core details about this {entity_type})

---

## DESCRIPTION

(Detailed description)

---

## SIGNIFICANCE

**Story Role**: (Why is this {entity_type} important?)

---

## NOTES

(Additional notes)
""".format(
            entity_name=entity_name,
            entity_type=entity_type,
            entity_type_upper=entity_type.upper()
        )
