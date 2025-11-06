#!/usr/bin/env python3
"""
Automation Orchestrator V2 (Simplified)

Hybrid version combining:
- V1's direct, clear procedural flow
- V2's decorator-based profiling
- Module system integration (uses AgentCoordinator module)
- No pipeline complexity or AgentFactory dependencies

This is the production version for the module system.
"""

from pathlib import Path
from typing import Tuple, List, Optional
from contextlib import contextmanager

from src.automation.core import log_to_file, get_response_count, increment_counter
from src.automation.profiling import PerformanceProfiler
from src.automation.time_tracking import TimeTracker
from src.automation.triggers import TriggerManager
from src.automation.file_loading import FileLoader
from src.automation.status import StatusManager
from src.file_change_tracker import FileChangeTracker
from src.entity_manager import EntityManager
from src.automation.prompt_templates import PromptTemplateManager
from src.automation.helpers.prompt_builder import PromptBuilder
from src.automation.agent_coordinator import AgentCoordinator
from src.automation.decorators import profile


class AutomationOrchestratorV2:
    """
    Simplified V2 orchestrator for module system.

    Combines best of V1 and V2:
    - V1's direct, clear flow
    - V2's decorator profiling
    - No complex pipeline dependencies
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
        self.timing_file = rp_dir.parent / "config" / "guidelines" / "Timing.txt"
        self.trigger_history_file = self.state_dir / "trigger_history.json"
        self.agent_cache_file = self.state_dir / "agent_analysis.json"

        # Ensure state directory exists
        self.state_dir.mkdir(exist_ok=True)

        # Create agent system directories
        for dir_name in ['entities', 'locations', 'memories', 'relationships']:
            (rp_dir / dir_name).mkdir(exist_ok=True)

        # Load configuration
        from src.automation.core import load_config
        self.config = load_config(self.config_file)

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

        # Initialize prompt builder
        self.prompt_builder = PromptBuilder(
            self.rp_dir,
            self.log_file,
            self.entity_manager,
            self.template_manager,
            self.config
        )

        log_to_file(self.log_file, "[OrchestratorV2] Initialized (simplified architecture)")

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

        # 1. Increment counter
        response_count, should_generate_arc = increment_counter(
            self.counter_file, self.config, self.log_file
        )

        # 2. Calculate time
        time_tracker = TimeTracker(self.timing_file, self.log_file)
        total_minutes, activities_desc = time_tracker.calculate_time(message, self.state_file)

        # 3. Load TIER_1 files
        log_to_file(self.log_file, "--- TIER_1 Loading (Core Files) ---")
        file_loader = FileLoader(self.rp_dir, self.log_file)
        tier1_files = file_loader.load_tier1_files()

        # 4. Load TIER_2 files
        log_to_file(self.log_file, "--- TIER_2 Loading (Guidelines) ---")
        tier2_files = file_loader.load_tier2_files(response_count)

        # 5. Identify TIER_3 triggers
        log_to_file(self.log_file, "--- TIER_3 Loading (Conditional) ---")
        trigger_manager = TriggerManager(self.rp_dir, self.log_file, self.config)
        tier3_files, loaded_entities = trigger_manager.identify_triggers(message)

        # 6. Track trigger frequency
        escalated_files = trigger_manager.track_trigger_history(tier3_files, self.trigger_history_file)

        # 7. Update status file
        status_manager = StatusManager(self.rp_dir)
        status_manager.update_status_file(
            self.status_file, self.state_file, self.counter_file,
            self.config, loaded_entities
        )

        # 8. Build enhanced prompt using PromptBuilder
        enhanced_prompt = self.prompt_builder.build_enhanced_prompt(
            message=message,
            response_count=response_count,
            should_generate_arc=should_generate_arc,
            total_minutes=total_minutes,
            activities_desc=activities_desc,
            tier1_files=tier1_files,
            tier2_files=tier2_files,
            tier3_files=tier3_files,
            escalated_files=escalated_files
        )

        log_to_file(self.log_file, f"Prompt built: TIER_1={len(tier1_files)} files, "
                                    f"TIER_2={len(tier2_files)} files, "
                                    f"TIER_3={len(tier3_files)} files")
        log_to_file(self.log_file, "========== Automation V2 Complete ==========")

        return enhanced_prompt, loaded_entities

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

        profiler = self.profiler if enable_profiling else None

        # 1. Increment counter
        with profiler.measure("counter_increment") if profiler else self._nullcontext():
            response_count, should_generate_arc = increment_counter(
                self.counter_file, self.config, self.log_file
            )

        # 2. Calculate time
        with profiler.measure("time_calculation") if profiler else self._nullcontext():
            time_tracker = TimeTracker(self.timing_file, self.log_file)
            total_minutes, activities_desc = time_tracker.calculate_time(message, self.state_file)

        # 3. Load TIER_1 files (these will be cached!)
        with profiler.measure("tier1_loading") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- TIER_1 Loading (Core Files - FOR CACHING) ---")
            file_loader = FileLoader(self.rp_dir, self.log_file)
            tier1_files = file_loader.load_tier1_files()

        # 4. Load TIER_2 files
        with profiler.measure("tier2_loading") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- TIER_2 Loading (Guidelines) ---")
            tier2_files = file_loader.load_tier2_files(response_count)

        # 5. Identify TIER_3 triggers
        with profiler.measure("tier3_triggers") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- TIER_3 Loading (Conditional) ---")
            trigger_manager = TriggerManager(self.rp_dir, self.log_file, self.config)
            tier3_files, loaded_entities = trigger_manager.identify_triggers(message)

        # 6. Track trigger frequency
        with profiler.measure("trigger_history") if profiler else self._nullcontext():
            escalated_files = trigger_manager.track_trigger_history(tier3_files, self.trigger_history_file)

        # 7. Load cached background agent results
        cached_background_context = None
        with profiler.measure("cache_loading") if profiler else self._nullcontext():
            coordinator = AgentCoordinator(self.rp_dir, self.log_file)
            cached_background_context = coordinator.load_from_cache(self.agent_cache_file)
            if cached_background_context:
                log_to_file(self.log_file, "--- Loaded cached background agent analysis ---")

        # 8. Run immediate agents
        immediate_agent_context = None
        with profiler.measure("immediate_agents") if profiler else self._nullcontext():
            immediate_agent_context = self._run_immediate_agents(message, response_count, loaded_entities)

        # 9. Combine agent contexts
        agent_context = ""
        if cached_background_context:
            agent_context += cached_background_context + "\n\n"
        if immediate_agent_context:
            agent_context += immediate_agent_context
        agent_context = agent_context if agent_context else None

        # 10. Check for file updates
        with profiler.measure("file_update_check") if profiler else self._nullcontext():
            all_loaded_files = []
            all_loaded_files.extend([self.rp_dir / name for name in tier1_files.keys() if (self.rp_dir / name).exists()])
            all_loaded_files.extend(tier3_files)
            all_loaded_files.extend(escalated_files)

            file_updates, updated_files = self.file_tracker.check_files_for_updates(all_loaded_files)
            update_notification = ""
            if file_updates:
                update_notification = self.file_tracker.generate_update_notification(file_updates)
                log_to_file(self.log_file, f"File updates detected: {len(file_updates)} files")

        # 11. Update status file
        with profiler.measure("status_update") if profiler else self._nullcontext():
            status_manager = StatusManager(self.rp_dir)
            status_manager.update_status_file(
                self.status_file, self.state_file, self.counter_file,
                self.config, loaded_entities
            )

        # 12. Build cached context and dynamic prompt using PromptBuilder
        with profiler.measure("prompt_building") if profiler else self._nullcontext():
            cached_context, dynamic_prompt = self.prompt_builder.build_cached_and_dynamic_prompts(
                tier1_files=tier1_files,
                update_notification=update_notification,
                should_generate_arc=should_generate_arc,
                response_count=response_count,
                total_minutes=total_minutes,
                activities_desc=activities_desc,
                tier2_files=tier2_files,
                tier3_files=tier3_files,
                escalated_files=escalated_files,
                message=message,
                agent_context=agent_context
            )

        log_to_file(self.log_file, f"Prompt built: TIER_1={len(tier1_files)} files (cached), "
                                    f"TIER_2={len(tier2_files)}, TIER_3={len(tier3_files)}")
        log_to_file(self.log_file, "========== Automation V2 Complete ==========")

        return cached_context, dynamic_prompt, loaded_entities, profiler

    def _run_immediate_agents(self, message: str, response_number: int,
                            loaded_entities: List[str]) -> Optional[str]:
        """Run immediate agents (quick context for N+1)

        Args:
            message: User message
            response_number: Current response number
            loaded_entities: Loaded entity names

        Returns:
            Formatted agent context or None
        """
        try:
            from src.automation.agents import (
                QuickEntityAnalysisAgent,
                FactExtractionAgent,
                MemoryExtractionAgent,
                PlotThreadExtractionAgent
            )

            log_to_file(self.log_file, "--- Running Immediate Agents (Pre-Response Context) ---")

            coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=4)

            # Quick entity analysis
            entity_agent = QuickEntityAnalysisAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                entity_agent.get_agent_id(),
                entity_agent.execute,
                message, loaded_entities,
                description=entity_agent.get_description()
            )

            # Fact extraction (Tier 2 entities)
            fact_agent = FactExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                fact_agent.get_agent_id(),
                fact_agent.execute,
                loaded_entities,
                description=fact_agent.get_description()
            )

            # Memory extraction
            memory_agent = MemoryExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                memory_agent.get_agent_id(),
                memory_agent.execute,
                loaded_entities,
                description=memory_agent.get_description()
            )

            # Plot thread extraction
            thread_agent = PlotThreadExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                thread_agent.get_agent_id(),
                thread_agent.execute,
                loaded_entities,
                description=thread_agent.get_description()
            )

            # Run all agents with 5 second timeout (immediate = fast)
            context = coordinator.run_all_agents(timeout=5.0, allow_partial=True)

            return context if context else None

        except Exception as e:
            log_to_file(self.log_file, f"[Immediate Agents] Error: {e}")
            return None

    def run_background_agents_after_response(self, response_text: str) -> None:
        """
        Run background agents after response is generated.

        Args:
            response_text: Generated response text
        """
        log_to_file(self.log_file, "--- Running Background Agents (Post-Response) ---")

        try:
            from src.automation.agents import (
                ResponseAnalyzerAgent,
                MemoryCreationAgent,
                RelationshipAnalysisAgent,
                PlotThreadDetectionAgent,
                KnowledgeExtractionAgent,
                ContradictionDetectionAgent
            )

            # Get current response count
            response_count = get_response_count(self.counter_file)

            coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=6)

            # Response analyzer
            analyzer_agent = ResponseAnalyzerAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                analyzer_agent.get_agent_id(),
                analyzer_agent.execute,
                response_text, response_count,
                description=analyzer_agent.get_description()
            )

            # Memory creation
            memory_agent = MemoryCreationAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                memory_agent.get_agent_id(),
                memory_agent.execute,
                response_text, response_count,
                description=memory_agent.get_description()
            )

            # Relationship analysis
            rel_agent = RelationshipAnalysisAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                rel_agent.get_agent_id(),
                rel_agent.execute,
                response_text, response_count,
                description=rel_agent.get_description()
            )

            # Plot thread detection
            thread_agent = PlotThreadDetectionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                thread_agent.get_agent_id(),
                thread_agent.execute,
                response_text, response_count,
                description=thread_agent.get_description()
            )

            # Knowledge extraction
            knowledge_agent = KnowledgeExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                knowledge_agent.get_agent_id(),
                knowledge_agent.execute,
                response_text, response_count,
                description=knowledge_agent.get_description()
            )

            # Contradiction detection (if enabled)
            if self.config.get("enable_contradiction_detection", False):
                contra_agent = ContradictionDetectionAgent(self.rp_dir, self.log_file)
                coordinator.add_agent(
                    contra_agent.get_agent_id(),
                    contra_agent.execute,
                    response_text, response_count,
                    description=contra_agent.get_description()
                )

            # Run all agents with 30 second timeout
            coordinator.run_all_agents(timeout=30.0, allow_partial=True)

            # Save results to cache
            coordinator.save_to_cache(self.agent_cache_file, response_count)

            log_to_file(self.log_file, "[Background Agents] Completed successfully")

        except Exception as e:
            log_to_file(self.log_file, f"[Background Agents] Error: {e}")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())

    @staticmethod
    @contextmanager
    def _nullcontext():
        """Null context manager for compatibility."""
        yield
