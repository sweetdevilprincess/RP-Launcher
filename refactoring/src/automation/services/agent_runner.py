"""Automation agent execution entry point."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from ...shared.interfaces import LoggingService
from ..contracts import AgentContext, AutomationContext, AutomationResult


class AgentStrategy(Protocol):
    """Signature for agent strategy components."""

    def create_context(self, context: AutomationContext) -> AgentContext: ...

    def execute(self, agent_context: AgentContext, prompt: str) -> AutomationResult: ...


class AgentRunner:
    """Coordinates agent execution strategies."""

    def __init__(self, *, logger: LoggingService, strategies: Iterable[AgentStrategy]) -> None:
        self._logger = logger
        self._strategies = tuple(strategies)

    def run(self, context: AutomationContext, prompt: str) -> AutomationResult:
        """Run all strategies in sequence, accumulating their results.

        Unlike traditional strategy patterns, we execute ALL strategies in order
        since each can enhance the prompt further:
        1. Immediate agents add context before Claude
        2. Background agents run post-response analysis
        3. Fallback triggers provide legacy compatibility

        Args:
            context: Automation context
            prompt: Initial prompt to enhance

        Returns:
            AutomationResult with fully enhanced prompt and accumulated context
        """
        self._logger.info("agent_runner.start", context={"strategy_count": len(self._strategies)})

        if not self._strategies:
            self._logger.warning("agent_runner.no_strategies")
            return AutomationResult(success=True, enhanced_prompt=prompt)

        current_prompt = prompt
        accumulated_cached_context = ""
        last_failure: str | None = None
        strategies_executed = 0
        strategies_successful = 0

        for strategy in self._strategies:
            strategy_name = type(strategy).__name__
            self._logger.debug("agent_runner.strategy.begin", context={"strategy": strategy_name})

            agent_context = strategy.create_context(context)
            strategies_executed += 1

            try:
                result = strategy.execute(agent_context, current_prompt, context)

                if result.success:
                    strategies_successful += 1
                    # Update prompt with enhancements from this strategy
                    if result.enhanced_prompt:
                        current_prompt = result.enhanced_prompt

                    # Accumulate context for final result
                    if result.cached_context:
                        accumulated_cached_context += result.cached_context

                    self._logger.info(
                        "agent_runner.strategy.success",
                        context={"strategy": strategy_name},
                    )
                else:
                    last_failure = result.error or f"{strategy_name} reported failure"
                    self._logger.warning(
                        "agent_runner.strategy.failure",
                        context={"strategy": strategy_name, "error": last_failure},
                    )

            except Exception as exc:
                last_failure = f"{strategy_name}: {exc}"
                self._logger.exception(
                    "agent_runner.strategy.error",
                    context={"strategy": strategy_name},
                    exc=exc,
                )
                # Continue to next strategy even on error

        self._logger.info(
            "agent_runner.complete",
            context={
                "total": strategies_executed,
                "successful": strategies_successful,
                "failed": strategies_executed - strategies_successful,
            },
        )

        # Return final accumulated result
        return AutomationResult(
            success=strategies_successful > 0,
            enhanced_prompt=current_prompt,
            cached_context=accumulated_cached_context or None,
            error=last_failure if strategies_successful == 0 else None,
        )
