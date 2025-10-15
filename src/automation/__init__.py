"""
Automation Module

Provides intelligent automation for the RP system:
- Response counting and progress tracking
- Time calculation from activities
- DeepSeek agent-based entity analysis
- Trigger-based conditional file loading
- Story arc generation
- Status file management

Public API:
    - run_automation() - Main automation orchestration (SDK mode)
    - run_automation_with_caching() - Automation with prompt caching (API mode)
"""

# Export main orchestration functions
from src.automation.orchestrator import (
    run_automation,
    run_automation_with_caching,
    AutomationOrchestrator
)

# Export core utilities (for advanced use)
from src.automation.core import (
    log_to_file,
    load_config,
    increment_counter,
    get_response_count
)

# Export individual components (for advanced use)
from src.automation.time_tracking import TimeTracker, calculate_time
from src.automation.triggers import TriggerManager, identify_triggers, track_tier3_triggers
from src.automation.file_loading import FileLoader, load_tier1_files, load_tier2_files, load_proxy_prompt
from src.automation.story_generation import StoryGenerator, auto_generate_story_arc, auto_generate_chapter_summary
from src.automation.status import StatusManager, update_status_file

__all__ = [
    # Main API
    'run_automation',
    'run_automation_with_caching',
    'AutomationOrchestrator',

    # Core utilities
    'log_to_file',
    'load_config',
    'increment_counter',
    'get_response_count',

    # Components
    'TimeTracker',
    'calculate_time',
    'TriggerManager',
    'identify_triggers',
    'track_tier3_triggers',
    'FileLoader',
    'load_tier1_files',
    'load_tier2_files',
    'load_proxy_prompt',
    'StoryGenerator',
    'auto_generate_story_arc',
    'auto_generate_chapter_summary',
    'StatusManager',
    'update_status_file',
]