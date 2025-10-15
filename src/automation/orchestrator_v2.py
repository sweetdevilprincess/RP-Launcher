#!/usr/bin/env python3
"""
Automation Orchestrator V2

Refactored orchestrator using pipeline architecture and modern design patterns.

This version replaces the monolithic orchestrator with:
- Pipeline architecture for execution flow
- AutomationContext for data flow
- ConfigContainer for typed configuration
- Event Bus for decoupled communication
- Component Registry for dependency injection
- Profiling decorators for performance tracking
- Strategy pattern for file loading

Comparison with V1:
- V1: 570 lines, GOD object anti-pattern, manual profiling
- V2: ~200 lines, clean separation of concerns, automatic profiling
"""

from pathlib import Path
from typing import Tuple, List, Optional
from contextlib import contextmanager

from src.automation.context import AutomationContext, AutomationResult
from src.automation.config import ConfigContainer, load_config_container
from src.automation.pipeline import PipelineBuilder, PipelineContext, Pipeline
from src.automation.decorators import profile, ProfileContext
from src.automation.events import (
    publish, ResponseGeneratedEvent, ErrorEvent, ProfilingEvent, StatusUpdateEvent
)
from src.automation.core import log_to_file, get_response_count
from src.automation.profiling import PerformanceProfiler
from src.file_change_tracker import FileChangeTracker
from src.entity_manager import EntityManager
from src.automation.prompt_templates import PromptTemplateManager


class AutomationOrchestratorV2:
    """
    Modern orchestrator using pipeline architecture.

    Replaces the monolithic V1 orchestrator with clean, composable stages.
    """

    def __init__(self, rp_dir: Path, enable_profiling: bool = True):
        """
        Initialize orchestrator.

        Args:
            rp_dir: RP directory path
            enable_profiling: Whether to enable performance profiling
        """
        self.rp_dir = rp_dir
        self.state_dir = rp_dir / "state"

        # Setup paths
        self.counter_file = self.state_dir / "response_counter.json"
        self.config_file = self.state_dir / "automation_config.json"
        self.state_file = self.state_dir / "current_state.md"
        self.status_file = rp_dir / "CURRENT_STATUS.md"
        self.log_file = self.state_dir / "hook.log"

        # Ensure state directory exists
        self.state_dir.mkdir(exist_ok=True)

        # Create agent system directories
        for dir_name in ['entities', 'locations', 'memories', 'relationships']:
            (rp_dir / dir_name).mkdir(exist_ok=True)

        # Load configuration
        self.config = load_config_container(self.config_file)

        # Initialize supporting systems
        self.file_tracker = FileChangeTracker(rp_dir)
        self.profiler = PerformanceProfiler() if enable_profiling else None
        self.profiling_enabled = enable_profiling

        # Initialize entity manager
        self.entity_manager = EntityManager(rp_dir)
        try:
            self.entity_manager.scan_and_index()
            log_to_file(self.log_file, f"[EntityManager] Indexed {len(self.entity_manager.entities)} entities")
        except Exception as e:
            log_to_file(self.log_file, f"[EntityManager] Warning: Failed to index entities: {e}")

        # Initialize template manager
        try:
            self.template_manager = PromptTemplateManager(rp_dir)
        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Init failed: {e}")
            self.template_manager = None

        log_to_file(self.log_file, "[OrchestratorV2] Initialized with pipeline architecture")

    @profile("run_automation")
    def run_automation(self, message: str) -> Tuple[str, List[str]]:
        """
        Run automation in simple mode (no caching).

        Args:
            message: User message

        Returns:
            Tuple of (enhanced_prompt, loaded_entities)
        """
        log_to_file(self.log_file, "========== RP Automation V2 Starting (Simple Mode) ==========")

        # Create automation context
        context = self._create_context(message, cache_mode=False)

        # Build and execute pipeline
        pipeline = self._build_pipeline(cache_mode=False)
        result = self._execute_pipeline(pipeline, context)

        # Extract results
        if result.success:
            enhanced_prompt = result.context.automation_context.tier1_files.get('enhanced_prompt', '')
            loaded_entities = result.context.automation_context.loaded_entities

            # Publish success event
            publish(ResponseGeneratedEvent(
                response_number=result.context.automation_context.response_count,
                response_length=len(enhanced_prompt),
                cache_mode=False
            ))

            log_to_file(self.log_file, "========== Automation V2 Complete ==========")
            return enhanced_prompt, loaded_entities
        else:
            # Publish error event
            error_msg = '; '.join(result.context.errors) if result.context.errors else "Unknown error"
            publish(ErrorEvent(
                error_type="automation_failure",
                error_message=error_msg,
                component="orchestrator_v2"
            ))

            log_to_file(self.log_file, f"========== Automation V2 Failed: {error_msg} ==========")
            return "", []

    @profile("run_automation_with_caching")
    def run_automation_with_caching(self, message: str,
                                    enable_profiling: bool = True) -> Tuple[str, str, List[str], Optional[PerformanceProfiler]]:
        """
        Run automation in API mode with caching.

        Args:
            message: User message
            enable_profiling: Whether to enable profiling (kept for compatibility)

        Returns:
            Tuple of (cached_context, dynamic_prompt, loaded_entities, profiler)
        """
        log_to_file(self.log_file, "========== RP Automation V2 Starting (API Mode with Caching) ==========")

        # Create automation context
        context = self._create_context(message, cache_mode=True)

        # Build and execute pipeline
        pipeline = self._build_pipeline(cache_mode=True)
        result = self._execute_pipeline(pipeline, context)

        # Extract results
        if result.success:
            cached_context = result.context.automation_context.tier1_files.get('cached_context', '')
            dynamic_prompt = result.context.automation_context.tier1_files.get('dynamic_prompt', '')
            loaded_entities = result.context.automation_context.loaded_entities

            # Publish success event
            publish(ResponseGeneratedEvent(
                response_number=result.context.automation_context.response_count,
                response_length=len(cached_context) + len(dynamic_prompt),
                cache_mode=True
            ))

            # Publish profiling data
            if self.profiler:
                for operation, duration in self.profiler.get_summary().items():
                    publish(ProfilingEvent(
                        operation_name=operation,
                        duration_seconds=duration,
                        component="orchestrator_v2"
                    ))

            log_to_file(self.log_file, "========== Automation V2 Complete ==========")
            return cached_context, dynamic_prompt, loaded_entities, self.profiler
        else:
            error_msg = '; '.join(result.context.errors) if result.context.errors else "Unknown error"
            publish(ErrorEvent(
                error_type="automation_failure",
                error_message=error_msg,
                component="orchestrator_v2"
            ))

            log_to_file(self.log_file, f"========== Automation V2 Failed: {error_msg} ==========")
            return "", "", [], self.profiler

    def _create_context(self, message: str, cache_mode: bool) -> PipelineContext:
        """
        Create pipeline context.

        Args:
            message: User message
            cache_mode: Whether using cache mode

        Returns:
            Pipeline context
        """
        # Create automation context
        automation_ctx = AutomationContext(
            message=message,
            rp_dir=self.rp_dir,
            config=self.config.to_dict(),
            profiler=self.profiler,
            profiling_enabled=self.profiling_enabled
        )

        # Create pipeline context
        return PipelineContext(automation_context=automation_ctx)

    def _build_pipeline(self, cache_mode: bool) -> Pipeline:
        """
        Build execution pipeline.

        Args:
            cache_mode: Whether to use cache mode

        Returns:
            Configured pipeline
        """
        builder = PipelineBuilder("automation_v2", self.log_file)

        builder.with_cache_mode(cache_mode)
        builder.with_agents(self.config.automation.agents.immediate.enabled)
        builder.with_status_update(True)
        builder.with_validation(True)

        return builder.build_standard_pipeline()

    def _execute_pipeline(self, pipeline: Pipeline, context: PipelineContext):
        """
        Execute pipeline and handle profiling.

        Args:
            pipeline: Pipeline to execute
            context: Pipeline context

        Returns:
            Pipeline result
        """
        with ProfileContext("pipeline_execution", self.profiler,
                          self.profiling_enabled, self.log_file):
            result = pipeline.execute(context)

        # Log execution summary
        log_to_file(self.log_file, f"[Pipeline] Executed {len(result.stages_executed)} stages")
        log_to_file(self.log_file, f"[Pipeline] Skipped {len(result.stages_skipped)} stages")
        log_to_file(self.log_file, f"[Pipeline] Errors: {len(result.context.errors)}")
        log_to_file(self.log_file, f"[Pipeline] Warnings: {len(result.context.warnings)}")

        return result

    @profile("run_background_agents")
    def run_background_agents_after_response(self, response_text: str) -> None:
        """
        Run background agents after response is generated.

        Args:
            response_text: Generated response text
        """
        log_to_file(self.log_file, "--- Running Background Agents (Post-Response) ---")

        try:
            from src.automation.pipeline import PipelineBuilder

            # Get current response count
            response_count = get_response_count(self.counter_file)

            # Create minimal context for background agents
            automation_ctx = AutomationContext(
                message="",
                rp_dir=self.rp_dir,
                response_count=response_count,
                config=self.config.to_dict()
            )

            pipeline_ctx = PipelineContext(automation_context=automation_ctx)

            # Build background pipeline
            builder = PipelineBuilder(log_file=self.log_file)
            pipeline = builder.build_background_pipeline(response_text)

            # Execute
            result = pipeline.execute(pipeline_ctx)

            if result.success:
                log_to_file(self.log_file, "[Background Agents] Completed successfully")
            else:
                log_to_file(self.log_file, f"[Background Agents] Failed: {result.context.errors}")

        except Exception as e:
            log_to_file(self.log_file, f"[Background Agents] Error: {e}")
            publish(ErrorEvent(
                error_type="background_agents_error",
                error_message=str(e),
                component="orchestrator_v2"
            ))

    @staticmethod
    @contextmanager
    def _nullcontext():
        """Null context manager for compatibility."""
        yield


# Backward compatibility function
def create_orchestrator(rp_dir: Path, use_v2: bool = False) -> any:
    """
    Create orchestrator instance.

    Args:
        rp_dir: RP directory
        use_v2: Whether to use V2 architecture

    Returns:
        Orchestrator instance
    """
    if use_v2:
        return AutomationOrchestratorV2(rp_dir)
    else:
        from src.automation.orchestrator import AutomationOrchestrator
        return AutomationOrchestrator(rp_dir)
