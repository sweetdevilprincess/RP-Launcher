#!/usr/bin/env python3
"""
Pipeline Base Classes

Core pipeline architecture for composing automation stages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import traceback

from src.automation.context import AutomationContext, AutomationResult
from src.automation.core import log_to_file


@dataclass
class PipelineContext:
    """
    Context that flows through the pipeline.

    Wraps AutomationContext with pipeline-specific metadata.
    """
    automation_context: AutomationContext
    stage_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skip_remaining: bool = False

    def record_result(self, stage_name: str, result: Any) -> None:
        """Record a stage result."""
        self.stage_results[stage_name] = result

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def update_automation_context(self, **kwargs) -> None:
        """Update the underlying automation context."""
        self.automation_context = self.automation_context.with_update(**kwargs)


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    context: PipelineContext
    stages_executed: List[str] = field(default_factory=list)
    stages_skipped: List[str] = field(default_factory=list)
    execution_time: float = 0.0

    def to_automation_result(self) -> AutomationResult:
        """Convert to AutomationResult for compatibility."""
        ctx = self.context.automation_context
        return AutomationResult(
            success=self.success,
            enhanced_prompt=ctx.tier1_files.get('enhanced_prompt'),
            cached_context=ctx.tier1_files.get('cached_context'),
            dynamic_prompt=ctx.tier1_files.get('dynamic_prompt'),
            loaded_entities=ctx.loaded_entities,
            profiler=ctx.profiler,
            error='; '.join(self.context.errors) if self.context.errors else None
        )


class PipelineStage(ABC):
    """
    Base class for pipeline stages.

    Each stage represents a discrete step in the automation process.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None):
        """
        Initialize pipeline stage.

        Args:
            name: Stage name
            log_file: Optional log file path
        """
        self.name = name
        self.log_file = log_file

    @abstractmethod
    def execute(self, context: PipelineContext) -> bool:
        """
        Execute the stage.

        Args:
            context: Pipeline context

        Returns:
            True if successful, False otherwise
        """
        pass

    def should_skip(self, context: PipelineContext) -> bool:
        """
        Check if this stage should be skipped.

        Args:
            context: Pipeline context

        Returns:
            True if stage should be skipped
        """
        return context.skip_remaining

    def log(self, message: str) -> None:
        """Log a message."""
        if self.log_file:
            log_to_file(self.log_file, f"[{self.name}] {message}")


class ConditionalStage(PipelineStage):
    """Stage that executes conditionally based on a predicate."""

    def __init__(self, name: str, stage: PipelineStage,
                 condition: Callable[[PipelineContext], bool],
                 log_file: Optional[Path] = None):
        """
        Initialize conditional stage.

        Args:
            name: Stage name
            stage: Wrapped stage
            condition: Condition function
            log_file: Optional log file
        """
        super().__init__(name, log_file)
        self.stage = stage
        self.condition = condition

    def execute(self, context: PipelineContext) -> bool:
        """Execute if condition is met."""
        if not self.condition(context):
            self.log(f"Skipping {self.stage.name} - condition not met")
            return True
        return self.stage.execute(context)


class ParallelStage(PipelineStage):
    """Stage that executes multiple stages in parallel."""

    def __init__(self, name: str, stages: List[PipelineStage],
                 log_file: Optional[Path] = None):
        """
        Initialize parallel stage.

        Args:
            name: Stage name
            stages: Stages to run in parallel
            log_file: Optional log file
        """
        super().__init__(name, log_file)
        self.stages = stages

    def execute(self, context: PipelineContext) -> bool:
        """Execute all stages in parallel."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        self.log(f"Executing {len(self.stages)} stages in parallel")

        with ThreadPoolExecutor(max_workers=len(self.stages)) as executor:
            futures = {
                executor.submit(stage.execute, context): stage
                for stage in self.stages
            }

            success = True
            for future in as_completed(futures):
                stage = futures[future]
                try:
                    stage_success = future.result(timeout=30)
                    if not stage_success:
                        self.log(f"Stage {stage.name} failed")
                        success = False
                except Exception as e:
                    self.log(f"Stage {stage.name} raised exception: {e}")
                    context.add_error(f"{stage.name}: {str(e)}")
                    success = False

        return success


class Pipeline:
    """
    Main pipeline executor.

    Orchestrates the execution of stages in sequence.
    """

    def __init__(self, name: str = "automation_pipeline",
                 log_file: Optional[Path] = None):
        """
        Initialize pipeline.

        Args:
            name: Pipeline name
            log_file: Optional log file
        """
        self.name = name
        self.log_file = log_file
        self.stages: List[PipelineStage] = []
        self.error_handlers: Dict[str, Callable] = {}

    def add_stage(self, stage: PipelineStage) -> 'Pipeline':
        """
        Add a stage to the pipeline.

        Args:
            stage: Stage to add

        Returns:
            Self for chaining
        """
        self.stages.append(stage)
        return self

    def add_conditional_stage(self, stage: PipelineStage,
                            condition: Callable[[PipelineContext], bool]) -> 'Pipeline':
        """
        Add a conditional stage.

        Args:
            stage: Stage to add
            condition: Condition function

        Returns:
            Self for chaining
        """
        conditional = ConditionalStage(
            f"conditional_{stage.name}",
            stage,
            condition,
            self.log_file
        )
        return self.add_stage(conditional)

    def add_parallel_stages(self, stages: List[PipelineStage],
                          name: str = "parallel") -> 'Pipeline':
        """
        Add stages to run in parallel.

        Args:
            stages: Stages to run in parallel
            name: Name for parallel group

        Returns:
            Self for chaining
        """
        parallel = ParallelStage(name, stages, self.log_file)
        return self.add_stage(parallel)

    def on_error(self, stage_name: str,
                 handler: Callable[[PipelineContext, Exception], None]) -> 'Pipeline':
        """
        Register an error handler for a stage.

        Args:
            stage_name: Stage name
            handler: Error handler function

        Returns:
            Self for chaining
        """
        self.error_handlers[stage_name] = handler
        return self

    def execute(self, context: PipelineContext) -> PipelineResult:
        """
        Execute the pipeline.

        Args:
            context: Pipeline context

        Returns:
            Pipeline execution result
        """
        import time
        start_time = time.time()

        self.log(f"Starting pipeline execution with {len(self.stages)} stages")

        result = PipelineResult(
            success=True,
            context=context
        )

        for stage in self.stages:
            if stage.should_skip(context):
                result.stages_skipped.append(stage.name)
                self.log(f"Skipping stage: {stage.name}")
                continue

            self.log(f"Executing stage: {stage.name}")

            try:
                stage_success = stage.execute(context)

                if stage_success:
                    result.stages_executed.append(stage.name)
                    self.log(f"Stage {stage.name} completed successfully")
                else:
                    result.success = False
                    self.log(f"Stage {stage.name} failed")
                    context.add_error(f"Stage {stage.name} failed")

                    # Check if we should continue on failure
                    if not context.automation_context.config.get('continue_on_error', False):
                        break

            except Exception as e:
                self.log(f"Stage {stage.name} raised exception: {e}")
                self.log(traceback.format_exc())

                # Call error handler if registered
                if stage.name in self.error_handlers:
                    try:
                        self.error_handlers[stage.name](context, e)
                    except Exception as handler_error:
                        self.log(f"Error handler failed: {handler_error}")

                result.success = False
                context.add_error(f"{stage.name}: {str(e)}")

                if not context.automation_context.config.get('continue_on_error', False):
                    break

        result.execution_time = time.time() - start_time
        self.log(f"Pipeline completed in {result.execution_time:.2f}s")
        self.log(f"Stages executed: {len(result.stages_executed)}")
        self.log(f"Stages skipped: {len(result.stages_skipped)}")

        return result

    def log(self, message: str) -> None:
        """Log a message."""
        if self.log_file:
            log_to_file(self.log_file, f"[{self.name}] {message}")