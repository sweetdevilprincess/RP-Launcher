#!/usr/bin/env python3
"""
Automation Orchestrator

High-level coordination of all automation tasks.
Assembles enhanced prompts with tiered file loading.
"""

from pathlib import Path
from typing import Tuple, List, Optional

from src.file_change_tracker import FileChangeTracker
from src.automation.core import log_to_file, load_config, increment_counter
from src.automation.time_tracking import TimeTracker
from src.automation.triggers import TriggerManager
from src.automation.file_loading import FileLoader
from src.automation.story_generation import StoryGenerator
from src.automation.status import StatusManager
from src.automation.profiling import PerformanceProfiler
from src.automation.agent_coordinator import AgentCoordinator
from src.automation.consistency_checklist import generate_consistency_checklist
from src.automation.prompt_templates import PromptTemplateManager
from src.automation.helpers.prompt_builder import PromptBuilder
from src.automation.agents import (
    QuickEntityAnalysisAgent,
    FactExtractionAgent,
    MemoryExtractionAgent,
    PlotThreadExtractionAgent,
    ResponseAnalyzerAgent,
    MemoryCreationAgent,
    RelationshipAnalysisAgent,
    PlotThreadDetectionAgent,
    KnowledgeExtractionAgent,
    ContradictionDetectionAgent
)
from src.entity_manager import EntityManager


class AutomationOrchestrator:
    """Coordinates all automation tasks"""

    def __init__(self, rp_dir: Path):
        """Initialize orchestrator

        Args:
            rp_dir: RP directory path
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

        # Ensure state directory exists
        self.state_dir.mkdir(exist_ok=True)

        # Create agent system directories
        (rp_dir / "entities").mkdir(exist_ok=True)
        (rp_dir / "locations").mkdir(exist_ok=True)
        (rp_dir / "memories").mkdir(exist_ok=True)
        (rp_dir / "relationships").mkdir(exist_ok=True)

        # Initialize components
        self.config = load_config(self.config_file)
        self.file_tracker = FileChangeTracker(rp_dir)

        # Initialize entity manager for Personality Core loading (Phase 1.3)
        self.entity_manager = EntityManager(rp_dir)
        try:
            self.entity_manager.scan_and_index()
            log_to_file(self.log_file, f"[EntityManager] Indexed {len(self.entity_manager.entities)} entities")
        except Exception as e:
            log_to_file(self.log_file, f"[EntityManager] Warning: Failed to index entities: {e}")
            # Continue even if indexing fails (entity_manager will just have no entities)

        # Agent system files
        self.agent_cache_file = self.state_dir / "agent_analysis.json"

        # Initialize narrative template manager (Phase 3.1)
        try:
            self.template_manager = PromptTemplateManager(rp_dir)
        except Exception as e:
            log_to_file(self.log_file, f"[PromptTemplateManager] Init failed: {e}")
            self.template_manager = None

        # Initialize prompt builder (unified prompt building)
        self.prompt_builder = PromptBuilder(
            self.rp_dir,
            self.log_file,
            self.entity_manager,
            self.template_manager,
            self.config
        )

    def run_automation(self, message: str) -> Tuple[str, List[str]]:
        """Run all automation tasks and return enhanced prompt

        Args:
            message: User message

        Returns:
            Tuple of (enhanced_prompt, loaded_entity_names)
        """
        log_to_file(self.log_file, "========== RP Automation Starting (Full System) ==========")

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

        # 5. Load TIER_2 files
        log_to_file(self.log_file, "--- TIER_2 Loading (Guidelines) ---")
        tier2_files = file_loader.load_tier2_files(response_count)

        # 6. Identify TIER_3 triggers
        log_to_file(self.log_file, "--- TIER_3 Loading (Conditional) ---")
        trigger_manager = TriggerManager(self.rp_dir, self.log_file, self.config)
        tier3_files, loaded_entities = trigger_manager.identify_triggers(message)

        # 7. Track trigger frequency and escalate
        escalated_files = trigger_manager.track_trigger_history(tier3_files, self.trigger_history_file)

        # 8. Update status file
        status_manager = StatusManager(self.rp_dir)
        status_manager.update_status_file(
            self.status_file, self.state_file, self.counter_file,
            self.config, loaded_entities
        )

        # 9. Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            should_generate_arc, response_count, total_minutes, activities_desc,
            tier1_files, tier2_files, tier3_files, escalated_files, message
        )

        log_to_file(self.log_file, f"Prompt built: TIER_1={len(tier1_files)} files, "
                                    f"TIER_2={len(tier2_files)} files, "
                                    f"TIER_3={len(tier3_files)} files, "
                                    f"Escalated={len(escalated_files)} files")
        log_to_file(self.log_file, "========== Automation Complete ==========")

        return enhanced_prompt, loaded_entities

    def run_automation_with_caching(self, message: str,
                                    enable_profiling: bool = True) -> Tuple[str, str, List[str], Optional[PerformanceProfiler]]:
        """Run automation and return cached context + dynamic prompt separately

        This version separates TIER_1 files (which should be cached) from the
        rest of the content for use with the Claude API's prompt caching feature.

        Args:
            message: User message
            enable_profiling: Whether to enable performance profiling

        Returns:
            Tuple of (cached_context, dynamic_prompt, loaded_entities, profiler)
        """
        log_to_file(self.log_file, "========== RP Automation Starting (API Mode with Caching) ==========")

        # Initialize profiler
        profiler = PerformanceProfiler() if enable_profiling else None

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

        # 5. Load TIER_2 files
        with profiler.measure("tier2_loading") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- TIER_2 Loading (Guidelines) ---")
            tier2_files = file_loader.load_tier2_files(response_count)

        # 6. Identify TIER_3 triggers
        with profiler.measure("tier3_triggers") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- TIER_3 Loading (Conditional) ---")
            trigger_manager = TriggerManager(self.rp_dir, self.log_file, self.config)
            tier3_files, loaded_entities = trigger_manager.identify_triggers(message)

        # 7. Track trigger frequency
        with profiler.measure("trigger_history") if profiler else self._nullcontext():
            escalated_files = trigger_manager.track_trigger_history(tier3_files, self.trigger_history_file)

        # 7.25. Load cached background agent results from previous response
        cached_background_context = None
        with profiler.measure("cache_loading") if profiler else self._nullcontext():
            coordinator = AgentCoordinator(self.rp_dir, self.log_file)
            cached_background_context = coordinator.load_from_cache(self.agent_cache_file)
            if cached_background_context:
                log_to_file(self.log_file, "--- Loaded cached background agent analysis from previous response ---")

        # 7.5. Run immediate agents (before prompt building)
        immediate_agent_context = None
        with profiler.measure("immediate_agents") if profiler else self._nullcontext():
            immediate_agent_context = self._run_immediate_agents(message, response_count, loaded_entities)

        # 7.75. Combine cached background context + fresh immediate context
        agent_context = ""
        if cached_background_context:
            agent_context += cached_background_context + "\n\n"
        if immediate_agent_context:
            agent_context += immediate_agent_context
        agent_context = agent_context if agent_context else None

        # 8. Check for file updates
        with profiler.measure("file_update_check") if profiler else self._nullcontext():
            log_to_file(self.log_file, "--- Checking for file updates ---")
            all_loaded_files = []
            all_loaded_files.extend([self.rp_dir / name for name in tier1_files.keys() if (self.rp_dir / name).exists()])
            all_loaded_files.extend(tier3_files)
            all_loaded_files.extend(escalated_files)

            file_updates, updated_files = self.file_tracker.check_files_for_updates(all_loaded_files)
            update_notification = ""
            if file_updates:
                update_notification = self.file_tracker.generate_update_notification(file_updates)
                log_to_file(self.log_file, f"File updates detected: {len(file_updates)} files")
                for update in file_updates:
                    log_to_file(self.log_file, f"  - {update['file_name']} ({update['category']})")

        # 9. Update status file
        with profiler.measure("status_update") if profiler else self._nullcontext():
            status_manager = StatusManager(self.rp_dir)
            status_manager.update_status_file(
                self.status_file, self.state_file, self.counter_file,
                self.config, loaded_entities
            )

        # 10. Build cached context and dynamic prompt
        with profiler.measure("prompt_building") if profiler else self._nullcontext():
            cached_context, dynamic_prompt = self._build_cached_and_dynamic_prompts(
                tier1_files, update_notification, should_generate_arc, response_count,
                total_minutes, activities_desc, tier2_files, tier3_files, escalated_files, message,
                agent_context,  # Inject agent context
                loaded_entities  # For consistency checklist (Phase 1.3)
            )

        log_to_file(self.log_file, f"Prompt built: TIER_1={len(tier1_files)} files (CACHED), "
                                    f"TIER_2={len(tier2_files)} files, "
                                    f"TIER_3={len(tier3_files)} files, "
                                    f"Escalated={len(escalated_files)} files")

        # Log profiling results
        if profiler:
            log_to_file(self.log_file, profiler.report("Automation Performance"))

        log_to_file(self.log_file, "========== Automation Complete (Caching Mode) ==========")

        return cached_context, dynamic_prompt, loaded_entities, profiler

    def _run_immediate_agents(self, message: str, message_number: int, loaded_entities: List[str]) -> str:
        """Run immediate agents before prompt building

        These agents run BEFORE Response N+1:
        - QuickEntityAnalysisAgent - Identify Tier 1/2/3 entities
        - FactExtractionAgent - Extract facts for Tier 2 entities
        - MemoryExtractionAgent - Get relevant memories
        - PlotThreadExtractionAgent - Extract relevant plot threads

        Args:
            message: User message
            message_number: Current message number
            loaded_entities: List of entity names from TIER_3

        Returns:
            Agent context string to inject into prompt
        """
        log_to_file(self.log_file, "--- Running Immediate Agents (Context Gathering) ---")

        # Initialize coordinator
        coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=4)

        # 1. Quick Entity Analysis - Identify which entities to load
        quick_entity = QuickEntityAnalysisAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            quick_entity.get_agent_id(),
            quick_entity.execute,
            message, message_number,
            description=quick_entity.get_description()
        )

        # 2. Fact Extraction - Extract facts for Tier 2 entities (if any exist)
        # Note: Will return minimal results if no entity cards exist yet
        tier2_entities = []  # Will be populated by entity analysis when files exist
        if tier2_entities:
            fact_extraction = FactExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                fact_extraction.get_agent_id(),
                fact_extraction.execute,
                message, tier2_entities,
                description=fact_extraction.get_description()
            )

        # 3. Memory Extraction - Get relevant memories for scene participants
        # Note: Will return minimal results if no memory files exist yet
        scene_participants = loaded_entities if loaded_entities else []
        if scene_participants:
            memory_extraction = MemoryExtractionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                memory_extraction.get_agent_id(),
                memory_extraction.execute,
                message, scene_participants,
                description=memory_extraction.get_description()
            )

        # 4. Plot Thread Extraction - Extract relevant plot threads
        # Note: Will return minimal results if no plot_threads_master.md exists yet
        plot_extraction = PlotThreadExtractionAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            plot_extraction.get_agent_id(),
            plot_extraction.execute,
            message, message_number,
            description=plot_extraction.get_description()
        )

        # Run all agents concurrently (5 second timeout)
        try:
            agent_context = coordinator.run_all_agents(timeout=10, allow_partial=True)

            # Log stats
            stats = coordinator.get_stats()
            log_to_file(self.log_file, f"[Immediate Agents] Completed: {stats['successful']}/{stats['agents_executed']} successful in {stats['max_duration_ms']}ms")

            return agent_context if agent_context else ""

        except Exception as e:
            log_to_file(self.log_file, f"[Immediate Agents] Error: {e}")
            return ""

    def run_background_agents(self, response_text: str, response_number: int,
                              characters_in_scene: Optional[List[str]] = None,
                              chapter: Optional[str] = None) -> None:
        """Run background agents after Claude response (non-blocking)

        These agents run AFTER Response N while user types Message N+1:
        - ResponseAnalyzerAgent - Scene classification, pacing, variety
        - MemoryCreationAgent - Extract memorable moments
        - RelationshipAnalysisAgent - Preference matching, tier tracking
        - PlotThreadDetectionAgent - New/mentioned/resolved threads
        - KnowledgeExtractionAgent - World-building facts
        - ContradictionDetectionAgent - Optional fact-checking

        This method is designed to be called via background task queue.

        Args:
            response_text: Claude's response to analyze
            response_number: Current response number
            characters_in_scene: Optional list of characters in scene
            chapter: Optional chapter identifier
        """
        log_to_file(self.log_file, "--- Running Background Agents (Post-Response Analysis) ---")

        # Initialize coordinator
        coordinator = AgentCoordinator(self.rp_dir, self.log_file, max_workers=6)

        # Track previous scene types for variety checking
        previous_scenes = []  # TODO: Load from state file when available

        # 1. Response Analyzer - Scene classification and pacing
        response_analyzer = ResponseAnalyzerAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            response_analyzer.get_agent_id(),
            response_analyzer.execute,
            response_text, response_number, previous_scenes,
            description=response_analyzer.get_description()
        )

        # 2. Memory Creation - Extract memorable moments
        memory_creation = MemoryCreationAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            memory_creation.get_agent_id(),
            memory_creation.execute,
            response_text, response_number, chapter,
            description=memory_creation.get_description()
        )

        # 3. Relationship Analysis - Preference matching
        if characters_in_scene:
            relationship_analysis = RelationshipAnalysisAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                relationship_analysis.get_agent_id(),
                relationship_analysis.execute,
                response_text, response_number, characters_in_scene,
                description=relationship_analysis.get_description()
            )

        # 4. Plot Thread Detection - New/mentioned/resolved threads
        plot_detection = PlotThreadDetectionAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            plot_detection.get_agent_id(),
            plot_detection.execute,
            response_text, response_number, chapter,
            description=plot_detection.get_description()
        )

        # 5. Knowledge Extraction - World-building facts
        knowledge_extraction = KnowledgeExtractionAgent(self.rp_dir, self.log_file)
        coordinator.add_agent(
            knowledge_extraction.get_agent_id(),
            knowledge_extraction.execute,
            response_text, response_number, chapter,
            description=knowledge_extraction.get_description()
        )

        # 6. Contradiction Detection (Optional) - Fact-checking
        # Note: Can be disabled via config
        if self.config.get("enable_contradiction_detection", False):
            contradiction_detection = ContradictionDetectionAgent(self.rp_dir, self.log_file)
            coordinator.add_agent(
                contradiction_detection.get_agent_id(),
                contradiction_detection.execute,
                response_text, response_number,
                description=contradiction_detection.get_description()
            )

        # Run all agents concurrently (30 second timeout)
        try:
            agent_context = coordinator.run_all_agents(timeout=60, allow_partial=True)

            # Log stats
            stats = coordinator.get_stats()
            log_to_file(self.log_file, f"[Background Agents] Completed: {stats['successful']}/{stats['agents_executed']} successful in {stats['max_duration_ms']}ms")

            # Save results to cache
            write_stats = coordinator.save_to_cache(self.agent_cache_file, response_number)
            log_to_file(self.log_file, "[Background Agents] Results saved to cache")

            # === PERFORMANCE BREAKDOWN ===
            # Calculate aggregate timing stats from agent results
            total_gather_ms = 0
            total_prompt_ms = 0
            total_api_ms = 0
            total_format_ms = 0
            agents_with_timing = 0

            # Note: Individual agent timings are logged by BaseAgent.execute()
            # This is a summary showing overall patterns

            write_ms = write_stats.get('write_ms', 0)
            analysis_total_ms = stats.get('max_duration_ms', 0)

            # Log performance breakdown
            log_to_file(self.log_file, "")
            log_to_file(self.log_file, "⏱️  Background Agent Performance Breakdown:")
            log_to_file(self.log_file, "─────────────────────────────────────────────")
            log_to_file(self.log_file, f"  Analysis Time:  {analysis_total_ms:>6.1f}ms (agents running in parallel)")
            log_to_file(self.log_file, f"  Write Time:     {write_ms:>6.1f}ms (save cache file)")
            log_to_file(self.log_file, f"  Total Time:     {analysis_total_ms + write_ms:>6.1f}ms")
            log_to_file(self.log_file, "─────────────────────────────────────────────")

            # Calculate percentage breakdown
            total_time = analysis_total_ms + write_ms
            if total_time > 0:
                analysis_pct = (analysis_total_ms / total_time) * 100
                write_pct = (write_ms / total_time) * 100
                log_to_file(self.log_file, f"  Analysis: {analysis_pct:>5.1f}% | Write: {write_pct:>5.1f}%")
                log_to_file(self.log_file, "─────────────────────────────────────────────")

                # Analysis: Should we parallelize more?
                if write_ms > analysis_total_ms * 0.5:
                    log_to_file(self.log_file, "  ⚠️  Write time is significant (>50% of analysis)")
                    log_to_file(self.log_file, "     Consider Writer Agent for better parallelism")
                elif write_ms > 100:
                    log_to_file(self.log_file, "  ℹ️  Write time is moderate (>100ms)")
                    log_to_file(self.log_file, "     Writer Agent might improve throughput")
                else:
                    log_to_file(self.log_file, "  ✓  Write time is minimal - current system is efficient")

            log_to_file(self.log_file, "")

        except Exception as e:
            log_to_file(self.log_file, f"[Background Agents] Error: {e}")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())

    @staticmethod
    def _nullcontext():
        """Null context manager for when profiling is disabled"""
        from contextlib import nullcontext
        return nullcontext()

    def _build_enhanced_prompt(self, should_generate_arc: bool, response_count: int,
                                total_minutes: int, activities_desc: str,
                                tier1_files: dict, tier2_files: dict,
                                tier3_files: list, escalated_files: list,
                                message: str) -> str:
        """Build enhanced prompt with all components (delegates to PromptBuilder)

        Args:
            should_generate_arc: Whether to inject arc generation
            response_count: Current response count
            total_minutes: Calculated time
            activities_desc: Activities description
            tier1_files: TIER_1 files dict
            tier2_files: TIER_2 files dict
            tier3_files: TIER_3 file paths
            escalated_files: Escalated file paths
            message: User message

        Returns:
            Enhanced prompt string
        """
        return self.prompt_builder.build_prompt(
            tier1_files=tier1_files,
            tier2_files=tier2_files,
            tier3_files=tier3_files,
            escalated_files=escalated_files,
            message=message,
            response_count=response_count,
            total_minutes=total_minutes,
            activities_desc=activities_desc,
            should_generate_arc=should_generate_arc,
            cache_mode=False
        )

    def _build_cached_and_dynamic_prompts(self, tier1_files: dict, update_notification: str,
                                          should_generate_arc: bool, response_count: int,
                                          total_minutes: int, activities_desc: str,
                                          tier2_files: dict, tier3_files: list,
                                          escalated_files: list, message: str,
                                          agent_context: Optional[str] = None,
                                          loaded_entities: Optional[List[str]] = None) -> Tuple[str, str]:
        """Build cached context and dynamic prompt separately (delegates to PromptBuilder)

        Args:
            tier1_files: TIER_1 files dict
            update_notification: File update notification
            should_generate_arc: Whether to inject arc generation
            response_count: Current response count
            total_minutes: Calculated time
            activities_desc: Activities description
            tier2_files: TIER_2 files dict
            tier3_files: TIER_3 file paths
            escalated_files: Escalated file paths
            message: User message
            agent_context: Optional agent analysis context
            loaded_entities: Optional list of entity names for consistency checklist

        Returns:
            Tuple of (cached_context, dynamic_prompt)
        """
        return self.prompt_builder.build_prompt(
            tier1_files=tier1_files,
            tier2_files=tier2_files,
            tier3_files=tier3_files,
            escalated_files=escalated_files,
            message=message,
            response_count=response_count,
            total_minutes=total_minutes,
            activities_desc=activities_desc,
            should_generate_arc=should_generate_arc,
            agent_context=agent_context,
            loaded_entities=loaded_entities,
            update_notification=update_notification,
            cache_mode=True
        )


# Convenience functions for backward compatibility
def run_automation(message: str, rp_dir: Path) -> Tuple[str, List]:
    """Run all automation tasks (convenience function)

    Args:
        message: User message
        rp_dir: RP directory path

    Returns:
        Tuple of (enhanced_prompt, loaded_entity_names)
    """
    orchestrator = AutomationOrchestrator(rp_dir)
    return orchestrator.run_automation(message)


def run_automation_with_caching(message: str, rp_dir: Path,
                                enable_profiling: bool = True) -> Tuple[str, str, List, Optional[PerformanceProfiler]]:
    """Run automation with caching (convenience function)

    Args:
        message: User message
        rp_dir: RP directory path
        enable_profiling: Whether to enable performance profiling

    Returns:
        Tuple of (cached_context, dynamic_prompt, loaded_entities, profiler)
    """
    orchestrator = AutomationOrchestrator(rp_dir)
    return orchestrator.run_automation_with_caching(message, enable_profiling)
