#!/usr/bin/env python3
"""
Pipeline Builder

Fluent builder for constructing automation pipelines.
"""

from pathlib import Path
from typing import Optional, List, Callable

from src.automation.pipeline.base import Pipeline, PipelineContext
from src.automation.pipeline.stages import (
    ConfigurationStage,
    FileLoadingStage,
    ImmediateAgentsStage,
    PromptBuildingStage,
    ValidationStage,
    StatusUpdateStage,
    BackgroundAgentsStage
)
from src.automation.context import AutomationContext


class PipelineBuilder:
    """
    Builder for constructing automation pipelines.

    Provides fluent interface for pipeline configuration.
    """

    def __init__(self, name: str = "automation", log_file: Optional[Path] = None):
        """
        Initialize pipeline builder.

        Args:
            name: Pipeline name
            log_file: Optional log file
        """
        self.pipeline = Pipeline(name, log_file)
        self.log_file = log_file
        self._cache_mode = False
        self._enable_agents = True
        self._enable_status = True
        self._enable_validation = True

    def with_cache_mode(self, enabled: bool = True) -> 'PipelineBuilder':
        """
        Enable cache mode for prompt building.

        Args:
            enabled: Whether to use cache mode

        Returns:
            Self for chaining
        """
        self._cache_mode = enabled
        return self

    def with_agents(self, enabled: bool = True) -> 'PipelineBuilder':
        """
        Enable/disable agent execution.

        Args:
            enabled: Whether to run agents

        Returns:
            Self for chaining
        """
        self._enable_agents = enabled
        return self

    def with_status_update(self, enabled: bool = True) -> 'PipelineBuilder':
        """
        Enable/disable status updates.

        Args:
            enabled: Whether to update status

        Returns:
            Self for chaining
        """
        self._enable_status = enabled
        return self

    def with_validation(self, enabled: bool = True) -> 'PipelineBuilder':
        """
        Enable/disable validation.

        Args:
            enabled: Whether to validate

        Returns:
            Self for chaining
        """
        self._enable_validation = enabled
        return self

    def add_custom_stage(self, stage) -> 'PipelineBuilder':
        """
        Add a custom stage.

        Args:
            stage: Custom stage to add

        Returns:
            Self for chaining
        """
        self.pipeline.add_stage(stage)
        return self

    def build_standard_pipeline(self) -> Pipeline:
        """
        Build standard automation pipeline.

        Returns:
            Configured pipeline
        """
        # Configuration stage - always needed
        self.pipeline.add_stage(ConfigurationStage(self.log_file))

        # File loading stage - always needed
        self.pipeline.add_stage(FileLoadingStage(self.log_file))

        # Immediate agents - conditional
        if self._enable_agents:
            self.pipeline.add_conditional_stage(
                ImmediateAgentsStage(self.log_file),
                lambda ctx: ctx.automation_context.config.get(
                    'agents', {}
                ).get('immediate', {}).get('enabled', True)
            )

        # Prompt building
        self.pipeline.add_stage(
            PromptBuildingStage(self._cache_mode, self.log_file)
        )

        # Validation - conditional
        if self._enable_validation:
            validation = ValidationStage(self.log_file)
            # Set cache mode on validation stage
            validation.cache_mode = self._cache_mode
            self.pipeline.add_stage(validation)

        # Status update - conditional
        if self._enable_status:
            self.pipeline.add_stage(StatusUpdateStage(self.log_file))

        return self.pipeline

    def build_background_pipeline(self, response_text: str) -> Pipeline:
        """
        Build pipeline for background agent execution.

        Args:
            response_text: Response text to analyze

        Returns:
            Configured pipeline
        """
        pipeline = Pipeline("background_agents", self.log_file)

        # Only configuration and background agents
        pipeline.add_stage(ConfigurationStage(self.log_file))
        pipeline.add_stage(BackgroundAgentsStage(response_text, self.log_file))

        return pipeline

    def build_minimal_pipeline(self) -> Pipeline:
        """
        Build minimal pipeline for testing.

        Returns:
            Minimal pipeline with only essential stages
        """
        pipeline = Pipeline("minimal", self.log_file)

        pipeline.add_stage(ConfigurationStage(self.log_file))
        pipeline.add_stage(FileLoadingStage(self.log_file))
        pipeline.add_stage(PromptBuildingStage(self._cache_mode, self.log_file))

        return pipeline

    @classmethod
    def create_standard(cls, rp_dir: Path, message: str,
                       cache_mode: bool = False) -> PipelineContext:
        """
        Create standard pipeline context.

        Args:
            rp_dir: RP directory
            message: User message
            cache_mode: Whether to use cache mode

        Returns:
            Configured pipeline context
        """
        # Create automation context
        automation_ctx = AutomationContext(
            message=message,
            rp_dir=rp_dir
        )

        # Create pipeline context
        return PipelineContext(automation_context=automation_ctx)


def build_automation_pipeline(config: dict,
                             log_file: Optional[Path] = None) -> Pipeline:
    """
    Build automation pipeline from configuration.

    Args:
        config: Configuration dictionary
        log_file: Optional log file

    Returns:
        Configured pipeline
    """
    builder = PipelineBuilder("automation", log_file)

    # Configure based on config
    builder.with_cache_mode(config.get('use_cache_mode', False))
    builder.with_agents(config.get('enable_agents', True))
    builder.with_status_update(config.get('update_status', True))
    builder.with_validation(config.get('enable_validation', True))

    # Build and return
    return builder.build_standard_pipeline()