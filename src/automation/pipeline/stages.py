#!/usr/bin/env python3
"""
Pipeline Stages

Concrete implementations of pipeline stages for automation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.automation.pipeline.base import PipelineStage, PipelineContext
from src.automation.context import LoadingContext, AgentContext
from src.automation.agents import AgentFactory, AgentOrchestrator
from src.automation.helpers import PromptBuilder
from src.automation.status import StatusManager
from src.automation.file_loading import TierFileLoader
from src.automation.core import (
    log_to_file, get_response_count, increment_counter, load_config
)
from src.automation.decorators import profile


class ConfigurationStage(PipelineStage):
    """Load and validate configuration."""

    def __init__(self, log_file: Optional[Path] = None):
        super().__init__("configuration", log_file)

    @profile("load_configuration")
    def execute(self, context: PipelineContext) -> bool:
        """Load configuration and response count."""
        try:
            ctx = context.automation_context

            # Load configuration
            config_file = ctx.rp_dir / "config.json"
            config = load_config(config_file)
            self.log(f"Loaded configuration from {config_file}")

            # Get response count
            counter_file = ctx.state_dir / "response_counter.json"
            response_count = get_response_count(counter_file)
            self.log(f"Current response count: {response_count}")

            # Check for arc generation
            should_generate_arc = (
                config.get('auto_story_arc', True) and
                response_count > 0 and
                response_count % config.get('arc_frequency', 50) == 0
            )

            # Update context
            context.update_automation_context(
                config=config,
                response_count=response_count,
                should_generate_arc=should_generate_arc
            )

            context.record_result('configuration', {
                'config': config,
                'response_count': response_count,
                'should_generate_arc': should_generate_arc
            })

            return True

        except Exception as e:
            context.add_error(f"Configuration failed: {e}")
            return False


class FileLoadingStage(PipelineStage):
    """Load tier files and entity data."""

    def __init__(self, log_file: Optional[Path] = None):
        super().__init__("file_loading", log_file)
        self.loader = None

    @profile("load_files")
    def execute(self, context: PipelineContext) -> bool:
        """Load all required files."""
        try:
            ctx = context.automation_context

            # Initialize loader
            loading_context = LoadingContext(
                rp_dir=ctx.rp_dir,
                response_count=ctx.response_count,
                message=ctx.message,
                config=ctx.config
            )

            self.loader = TierFileLoader(ctx.rp_dir, self.log_file)

            # Load TIER_1 files
            tier1_files = self.loader.load_tier1_files()
            self.log(f"Loaded {len(tier1_files)} TIER_1 files")

            # Load TIER_2 files conditionally
            tier2_files = {}
            if loading_context.should_load_tier2:
                tier2_files = self.loader.load_tier2_files()
                self.log(f"Loaded {len(tier2_files)} TIER_2 files")

            # Load TIER_3 entity files
            tier3_files = self.loader.load_tier3_entities(ctx.message)
            self.log(f"Loaded {len(tier3_files)} TIER_3 entity files")

            # Extract entity names
            loaded_entities = [
                p.stem for p in tier3_files
                if p.stem not in ['world', 'setting']
            ]

            # Update context
            context.update_automation_context(
                tier1_files=tier1_files,
                tier2_files=tier2_files,
                tier3_files=tier3_files,
                loaded_entities=loaded_entities
            )

            context.record_result('file_loading', {
                'tier1_count': len(tier1_files),
                'tier2_count': len(tier2_files),
                'tier3_count': len(tier3_files),
                'loaded_entities': loaded_entities
            })

            return True

        except Exception as e:
            context.add_error(f"File loading failed: {e}")
            return False


class ImmediateAgentsStage(PipelineStage):
    """Run immediate agents for context gathering."""

    def __init__(self, log_file: Optional[Path] = None):
        super().__init__("immediate_agents", log_file)

    @profile("run_immediate_agents")
    def execute(self, context: PipelineContext) -> bool:
        """Run immediate agents."""
        try:
            ctx = context.automation_context

            # Skip if disabled
            if not ctx.config.get('agents', {}).get('immediate', {}).get('enabled', True):
                self.log("Immediate agents disabled in config")
                return True

            # Run agents
            orchestrator = AgentOrchestrator(
                ctx.rp_dir,
                self.log_file,
                max_workers=4
            )

            agent_context = orchestrator.run_immediate_agents(
                ctx.message,
                ctx.response_count,
                ctx.loaded_entities
            )

            # Update context
            context.update_automation_context(
                immediate_agent_context=agent_context
            )

            context.record_result('immediate_agents', {
                'context_generated': bool(agent_context),
                'context_length': len(agent_context) if agent_context else 0
            })

            return True

        except Exception as e:
            context.add_error(f"Immediate agents failed: {e}")
            # Continue even if agents fail
            return True


class PromptBuildingStage(PipelineStage):
    """Build enhanced or cached prompts."""

    def __init__(self, cache_mode: bool = False, log_file: Optional[Path] = None):
        super().__init__("prompt_building", log_file)
        self.cache_mode = cache_mode

    @profile("build_prompts")
    def execute(self, context: PipelineContext) -> bool:
        """Build prompts."""
        try:
            ctx = context.automation_context

            # Initialize builder
            builder = PromptBuilder(ctx.rp_dir, self.log_file)

            # Build prompt
            if self.cache_mode:
                cached_context, dynamic_prompt = builder.build_prompt(
                    tier1_files=ctx.tier1_files,
                    tier2_files=ctx.tier2_files,
                    tier3_files=ctx.tier3_files,
                    message=ctx.message,
                    agent_context=ctx.merge_agent_context(),
                    should_generate_arc=ctx.should_generate_arc,
                    total_minutes=ctx.total_minutes,
                    activities_desc=ctx.activities_desc,
                    loaded_entities=ctx.loaded_entities,
                    entities_with_cores=ctx.entities_with_cores,
                    cache_mode=True
                )

                context.update_automation_context(
                    tier1_files={
                        **ctx.tier1_files,
                        'cached_context': cached_context,
                        'dynamic_prompt': dynamic_prompt
                    }
                )

                context.record_result('prompt_building', {
                    'mode': 'cached',
                    'cached_length': len(cached_context),
                    'dynamic_length': len(dynamic_prompt)
                })

            else:
                enhanced_prompt = builder.build_prompt(
                    tier1_files=ctx.tier1_files,
                    tier2_files=ctx.tier2_files,
                    tier3_files=ctx.tier3_files,
                    message=ctx.message,
                    agent_context=ctx.merge_agent_context(),
                    should_generate_arc=ctx.should_generate_arc,
                    total_minutes=ctx.total_minutes,
                    activities_desc=ctx.activities_desc,
                    loaded_entities=ctx.loaded_entities,
                    entities_with_cores=ctx.entities_with_cores,
                    cache_mode=False
                )

                context.update_automation_context(
                    tier1_files={
                        **ctx.tier1_files,
                        'enhanced_prompt': enhanced_prompt
                    }
                )

                context.record_result('prompt_building', {
                    'mode': 'enhanced',
                    'prompt_length': len(enhanced_prompt)
                })

            return True

        except Exception as e:
            context.add_error(f"Prompt building failed: {e}")
            return False


class ValidationStage(PipelineStage):
    """Validate pipeline results before completion."""

    def __init__(self, log_file: Optional[Path] = None):
        super().__init__("validation", log_file)

    def execute(self, context: PipelineContext) -> bool:
        """Validate results."""
        ctx = context.automation_context

        # Check for required outputs
        if self.cache_mode:
            if not ctx.tier1_files.get('cached_context'):
                context.add_error("Missing cached context")
                return False
            if not ctx.tier1_files.get('dynamic_prompt'):
                context.add_error("Missing dynamic prompt")
                return False
        else:
            if not ctx.tier1_files.get('enhanced_prompt'):
                context.add_error("Missing enhanced prompt")
                return False

        # Validate file counts
        if len(ctx.tier1_files) == 0:
            context.add_warning("No TIER_1 files loaded")

        # Log validation results
        self.log(f"Validation passed - Errors: {len(context.errors)}, Warnings: {len(context.warnings)}")

        return len(context.errors) == 0


class StatusUpdateStage(PipelineStage):
    """Update status files."""

    def __init__(self, log_file: Optional[Path] = None):
        super().__init__("status_update", log_file)

    @profile("update_status")
    def execute(self, context: PipelineContext) -> bool:
        """Update status files."""
        try:
            ctx = context.automation_context

            # Update status file
            status_file = ctx.rp_dir / "CURRENT_STATUS.md"
            state_file = ctx.state_dir / "current_state.md"
            counter_file = ctx.state_dir / "response_counter.json"

            manager = StatusManager(ctx.rp_dir)
            manager.update_status_file(
                status_file,
                state_file,
                counter_file,
                ctx.config,
                ctx.loaded_entities
            )

            self.log("Status file updated")

            # Increment counter for next run
            increment_counter(counter_file)
            new_count = ctx.response_count + 1
            self.log(f"Incremented response counter to {new_count}")

            context.record_result('status_update', {
                'status_updated': True,
                'new_count': new_count
            })

            return True

        except Exception as e:
            context.add_warning(f"Status update failed: {e}")
            # Don't fail pipeline for status update errors
            return True


class BackgroundAgentsStage(PipelineStage):
    """Run background agents after response."""

    def __init__(self, response_text: str, log_file: Optional[Path] = None):
        super().__init__("background_agents", log_file)
        self.response_text = response_text

    @profile("run_background_agents")
    def execute(self, context: PipelineContext) -> bool:
        """Run background agents."""
        try:
            ctx = context.automation_context

            # Skip if disabled
            if not ctx.config.get('agents', {}).get('background', {}).get('enabled', True):
                self.log("Background agents disabled in config")
                return True

            # Run agents
            orchestrator = AgentOrchestrator(
                ctx.rp_dir,
                self.log_file,
                max_workers=6
            )

            # Extract characters from scene (simplified)
            characters_in_scene = []
            for entity in ctx.loaded_entities:
                if entity.lower() not in ['world', 'setting']:
                    characters_in_scene.append(entity)

            orchestrator.run_background_agents(
                self.response_text,
                ctx.response_count,
                characters_in_scene=characters_in_scene if characters_in_scene else None,
                chapter=ctx.config.get('current_chapter'),
                config=ctx.config
            )

            self.log("Background agents completed")

            context.record_result('background_agents', {
                'executed': True,
                'characters_analyzed': len(characters_in_scene)
            })

            return True

        except Exception as e:
            context.add_warning(f"Background agents failed: {e}")
            # Don't fail pipeline for background agent errors
            return True