"""Enhanced Multi-Tier Trigger System

Provides intelligent trigger matching with three tiers:
- Keyword matching (enhanced with word boundaries)
- Regex pattern matching
- Semantic matching (optional, AI-powered)
"""

from .trigger_system import TriggerMatcher, TriggerMatch

__all__ = ['TriggerMatcher', 'TriggerMatch']
