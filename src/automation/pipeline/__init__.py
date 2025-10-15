"""
Automation Pipeline

Provides pipeline architecture for composing automation stages.
Replaces monolithic execute() method with discrete, testable stages.
"""

from src.automation.pipeline.base import (
    PipelineStage,
    Pipeline,
    PipelineContext,
    PipelineResult
)
from src.automation.pipeline.stages import (
    ConfigurationStage,
    FileLoadingStage,
    ImmediateAgentsStage,
    PromptBuildingStage,
    ValidationStage,
    StatusUpdateStage,
    BackgroundAgentsStage
)
from src.automation.pipeline.builder import PipelineBuilder

__all__ = [
    # Base classes
    'PipelineStage',
    'Pipeline',
    'PipelineContext',
    'PipelineResult',

    # Stages
    'ConfigurationStage',
    'FileLoadingStage',
    'ImmediateAgentsStage',
    'PromptBuildingStage',
    'ValidationStage',
    'StatusUpdateStage',
    'BackgroundAgentsStage',

    # Builder
    'PipelineBuilder'
]