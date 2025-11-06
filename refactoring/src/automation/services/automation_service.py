"""High-level orchestration service for automation workflows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, Protocol

from ...infrastructure.filesystem import TieredContext, TieredLoadResult
from ...shared.interfaces import ConfigService, LoggingService
from ..contracts import AutomationContext, AutomationResult


class EntityServiceProtocol(Protocol):
    """Placeholder contract for the entity service dependency."""

    def prepare_entities(self, context: AutomationContext) -> AutomationContext: ...


class SessionServiceProtocol(Protocol):
    """Placeholder contract for the session service dependency."""

    def enrich_session(self, context: AutomationContext) -> AutomationContext: ...


class PromptBuilderProtocol(Protocol):
    """Construct prompts for agent execution."""

    def build_prompt(self, context: AutomationContext) -> str: ...


class AgentRunnerProtocol(Protocol):
    """Execute agents and transform their results."""

    def run(self, context: AutomationContext, prompt: str) -> AutomationResult: ...


class FileAccessServiceProtocol(Protocol):
    """Filesystem workflows needed by automation."""

    def increment_response_counter(self) -> int: ...

    def load_tiered_context(
        self,
        *,
        response_count: int | None,
        triggered_files: Sequence[Path] | None = None,
        tier3_referenced_files: Sequence[Path] | None = None,
    ) -> TieredContext: ...


class AutomationService:
    """Coordinates automation activities using injected dependencies."""

    def __init__(
        self,
        *,
        config: ConfigService,
        logger: LoggingService,
        entity_service: EntityServiceProtocol,
        session_service: SessionServiceProtocol,
        prompt_builder: PromptBuilderProtocol,
        agent_runner: AgentRunnerProtocol,
        file_access: FileAccessServiceProtocol,
    ) -> None:
        self._config = config
        self._logger = logger
        self._entity_service = entity_service
        self._session_service = session_service
        self._prompt_builder = prompt_builder
        self._agent_runner = agent_runner
        self._file_access = file_access

    def run(self, context: AutomationContext) -> AutomationResult:
        """Execute the automation pipeline for a single RP request."""

        self._logger.info("automation.run.start", context={"rp_dir": str(context.rp_dir)})

        # Step 1: hydrate configuration + session state.
        hydrated_context = self._load_configuration(context)
        hydrated_context = self._session_service.enrich_session(hydrated_context)

        # Step 2: gather domain/entity information (determines in-scene vs referenced).
        domain_context = self._entity_service.prepare_entities(hydrated_context)

        # Step 3: increment counters and gather tiered files.
        counter_value = self._file_access.increment_response_counter()
        tiered_context = self._file_access.load_tiered_context(
            response_count=counter_value,
            triggered_files=domain_context.tier3_files,
            tier3_referenced_files=domain_context.tier3_referenced_files,
        )
        enriched_context = self._apply_file_context(
            domain_context,
            counter_value=counter_value,
            tiered_context=tiered_context,
        )

        # Step 4: build prompt.
        prompt = self._prompt_builder.build_prompt(enriched_context)

        # Step 5: execute agents.
        result = self._agent_runner.run(enriched_context, prompt)

        # Step 6: post-run bookkeeping (counters, logs, etc.).
        self._finalise(enriched_context, result)

        self._logger.info("automation.run.complete", context={"success": result.success})
        return result

    def _load_configuration(self, context: AutomationContext) -> AutomationContext:
        """Inject the latest configuration into the context."""

        config_data = self._config.section("automation")
        return replace(context, config=config_data)

    def _apply_file_context(
        self,
        context: AutomationContext,
        *,
        counter_value: int,
        tiered_context: TieredContext,
    ) -> AutomationContext:
        """Merge tiered file results and counter info into the context."""

        # Extract author notes (highest priority)
        author_notes_content = ""
        active_genome = None
        if tiered_context.author_notes:
            author_notes_content = tiered_context.author_notes.content
            active_genome = tiered_context.author_notes.active_genome_file

        tier1_files = self._flatten_files(tiered_context.tier1)
        tier2_files = self._flatten_files(tiered_context.tier2)
        tier3_loaded_files = self._flatten_files(tiered_context.tier3)
        tier3_referenced_loaded_files = self._flatten_files(tiered_context.tier3_referenced)
        tier3_entities = self._collect_entities_with_cores(tiered_context)

        should_generate_arc = self._should_generate_arc(
            config=context.config,
            counter_value=counter_value,
        )

        return context.with_update(
            response_count=counter_value,
            should_generate_arc=should_generate_arc,
            author_notes=author_notes_content,
            active_genome=active_genome,
            tier1_files=tier1_files,
            tier2_files=tier2_files,
            tier3_loaded_files=tier3_loaded_files,
            entities_with_cores=tier3_entities,
        )

    def _flatten_files(self, bundles: dict[str, TieredLoadResult]) -> dict[str, str]:
        combined: dict[str, str] = {}
        for result in bundles.values():
            combined.update(result.files)
        return combined

    def _collect_entities_with_cores(self, tiered_context: TieredContext) -> Sequence[str]:
        entities: set[str] = set()
        for bucket in (
            tiered_context.tier1,
            tiered_context.tier2,
            tiered_context.tier3,
            tiered_context.tier3_referenced,
        ):
            for result in bucket.values():
                names = result.metadata.get("entities_with_cores")
                if isinstance(names, list):
                    for name in names:
                        if isinstance(name, str):
                            entities.add(name)
        return sorted(entities)

    def _should_generate_arc(self, *, config: dict[str, Any], counter_value: int) -> bool:
        arc_frequency = int(config.get("arc_frequency", 50)) if config else 50
        auto_story_arc = bool(config.get("auto_story_arc", True)) if config else True
        if arc_frequency <= 0:
            return False
        return auto_story_arc and counter_value % arc_frequency == 0

    def _finalise(self, context: AutomationContext, result: AutomationResult) -> None:
        """Hook for persisting counters, logging metrics, etc."""

        if result.success:
            self._logger.debug("automation.run.success", context={"rp_dir": str(context.rp_dir)})
        else:
            self._logger.warning(
                "automation.run.failure",
                context={"rp_dir": str(context.rp_dir), "error": result.error},
            )
