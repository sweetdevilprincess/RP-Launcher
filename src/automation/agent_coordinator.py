#!/usr/bin/env python3
"""
Agent Coordinator - Multi-Agent Orchestration

Coordinates multiple DeepSeek agents working together to gather context
before sending to Claude. Each agent can query different areas and all
results are collected and formatted for injection into the prompt.

Usage:
    coordinator = AgentCoordinator(rp_dir, log_file)

    # Register agents
    coordinator.add_agent("world_state", query_world_state_func, arg1, arg2)
    coordinator.add_agent("character_memory", query_memories_func, character_name)
    coordinator.add_agent("plot_tracker", summarize_plot_func)

    # Run all agents concurrently and collect results
    context = coordinator.run_all_agents(timeout=30)

    # Context is now ready to inject into Claude prompt
    full_prompt = context + "\n\n" + user_message
"""

import time
import json
import concurrent.futures
from pathlib import Path
from typing import Dict, Callable, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.automation.core import log_to_file

# Agent type classification
BACKGROUND_AGENTS = {
    'response_analyzer', 'memory_creation', 'relationship_analysis',
    'plot_thread_detection', 'knowledge_extraction', 'contradiction_detection'
}
IMMEDIATE_AGENTS = {
    'quick_entity_analysis', 'fact_extraction', 'memory_extraction',
    'plot_thread_extraction'
}
from src.clients.deepseek import InsufficientBalanceError


@dataclass
class AgentTask:
    """Represents a single agent task"""
    agent_id: str
    func: Callable
    args: tuple
    kwargs: dict
    description: str


@dataclass
class AgentResult:
    """Result from an agent execution"""
    agent_id: str
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    is_balance_error: bool = False


class AgentCoordinator:
    """Coordinates multiple DeepSeek agents working together

    Features:
    - Concurrent agent execution
    - Result collection and aggregation
    - Timeout handling
    - Partial success (some agents fail, still use successful results)
    - Formatted output for Claude injection
    """

    def __init__(self, rp_dir: Path, log_file: Path, max_workers: int = 4):
        """Initialize agent coordinator

        Args:
            rp_dir: RP directory path
            log_file: Path to log file
            max_workers: Maximum concurrent agents (default 4)
        """
        self.rp_dir = rp_dir
        self.log_file = log_file
        self.max_workers = max_workers
        self.agents: List[AgentTask] = []
        self.results: Dict[str, AgentResult] = {}

    def add_agent(self, agent_id: str, func: Callable, *args,
                  description: str = "", **kwargs) -> None:
        """Register an agent task

        Args:
            agent_id: Unique identifier for this agent
            func: Function to execute (should return string content)
            *args: Positional arguments for function
            description: Human-readable description of what this agent does
            **kwargs: Keyword arguments for function
        """
        agent = AgentTask(
            agent_id=agent_id,
            func=func,
            args=args,
            kwargs=kwargs,
            description=description or agent_id
        )
        self.agents.append(agent)
        log_to_file(self.log_file, f"[AgentCoordinator] Registered agent: {agent_id} - {description}")

    def clear_agents(self) -> None:
        """Clear all registered agents"""
        self.agents.clear()
        self.results.clear()

    def _execute_agent(self, agent: AgentTask) -> AgentResult:
        """Execute a single agent (runs in thread pool)

        Args:
            agent: Agent task to execute

        Returns:
            AgentResult with success/failure and content
        """
        start_time = time.perf_counter()

        try:
            log_to_file(self.log_file, f"[AgentCoordinator] Executing: {agent.agent_id}")

            # Execute the agent function
            content = agent.func(*agent.args, **agent.kwargs)

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            log_to_file(self.log_file,
                       f"[AgentCoordinator] ✓ {agent.agent_id} completed in {duration_ms}ms")

            return AgentResult(
                agent_id=agent.agent_id,
                success=True,
                content=content,
                duration_ms=duration_ms
            )

        except InsufficientBalanceError as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_to_file(self.log_file,
                       f"[AgentCoordinator] ⚠️ {agent.agent_id} FAILED - LOW BALANCE: {e}")

            return AgentResult(
                agent_id=agent.agent_id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                is_balance_error=True
            )

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_to_file(self.log_file,
                       f"[AgentCoordinator] ✗ {agent.agent_id} FAILED: {e}")

            return AgentResult(
                agent_id=agent.agent_id,
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )

    def run_all_agents(self, timeout: float = 60.0,
                       allow_partial: bool = True) -> str:
        """Execute all registered agents concurrently and collect results

        Args:
            timeout: Maximum time to wait for all agents (seconds)
            allow_partial: If True, return results even if some agents fail

        Returns:
            Formatted context string ready for Claude injection

        Raises:
            TimeoutError: If agents don't complete within timeout
            RuntimeError: If all agents fail and allow_partial=False
        """
        if not self.agents:
            log_to_file(self.log_file, "[AgentCoordinator] No agents registered")
            return ""

        log_to_file(self.log_file,
                   f"[AgentCoordinator] Running {len(self.agents)} agents (timeout: {timeout}s)")

        start_time = time.perf_counter()

        # Execute all agents concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all agent tasks
            future_to_agent = {
                executor.submit(self._execute_agent, agent): agent
                for agent in self.agents
            }

            # Collect results as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_agent, timeout=timeout):
                agent = future_to_agent[future]
                result = future.result()
                self.results[agent.agent_id] = result
                completed += 1

        total_duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Analyze results
        successful = [r for r in self.results.values() if r.success]
        failed = [r for r in self.results.values() if not r.success]
        balance_errors = [r for r in failed if r.is_balance_error]

        log_to_file(self.log_file,
                   f"[AgentCoordinator] Completed: {len(successful)}/{len(self.agents)} successful "
                   f"in {total_duration_ms}ms")

        if balance_errors:
            log_to_file(self.log_file,
                       f"[AgentCoordinator] ⚠️ WARNING: {len(balance_errors)} agents failed due to low balance")

        # Check if we have any usable results
        if not successful:
            if allow_partial:
                log_to_file(self.log_file, "[AgentCoordinator] All agents failed, returning empty context")
                return ""
            else:
                raise RuntimeError(f"All {len(self.agents)} agents failed")

        # Format results for Claude
        context = self._format_context(successful, failed)

        return context

    def _format_context(self, successful: List[AgentResult],
                       failed: List[AgentResult]) -> str:
        """Format agent results into context for Claude

        Args:
            successful: List of successful agent results
            failed: List of failed agent results

        Returns:
            Formatted markdown context
        """
        sections = []

        # Header
        sections.append("<!-- ========== AGENT CONTEXT SYNTHESIS ========== -->")
        sections.append(f"<!-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->")
        sections.append(f"<!-- Agents: {len(successful)} successful, {len(failed)} failed -->")
        sections.append("")

        # Successful agent outputs
        for result in successful:
            # Find agent description
            agent_desc = next(
                (a.description for a in self.agents if a.agent_id == result.agent_id),
                result.agent_id
            )

            sections.append(f"### Agent: {agent_desc}")
            sections.append(f"<!-- Agent ID: {result.agent_id} | Duration: {result.duration_ms}ms -->")
            sections.append("")
            sections.append(result.content)
            sections.append("")

        # Note any failures
        if failed:
            sections.append("<!-- AGENT FAILURES -->")
            for result in failed:
                error_type = "LOW BALANCE" if result.is_balance_error else "ERROR"
                sections.append(f"<!-- {error_type}: {result.agent_id} - {result.error} -->")
            sections.append("")

        sections.append("<!-- ========== END AGENT CONTEXT ========== -->")

        return "\n".join(sections)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about last agent run

        Returns:
            Dict with execution statistics
        """
        if not self.results:
            return {
                'agents_registered': len(self.agents),
                'agents_executed': 0,
                'successful': 0,
                'failed': 0,
                'balance_errors': 0
            }

        successful = [r for r in self.results.values() if r.success]
        failed = [r for r in self.results.values() if not r.success]
        balance_errors = [r for r in failed if r.is_balance_error]

        return {
            'agents_registered': len(self.agents),
            'agents_executed': len(self.results),
            'successful': len(successful),
            'failed': len(failed),
            'balance_errors': len(balance_errors),
            'avg_duration_ms': int(sum(r.duration_ms for r in self.results.values()) / len(self.results)),
            'max_duration_ms': max((r.duration_ms for r in self.results.values()), default=0)
        }

    def get_result(self, agent_id: str) -> Optional[AgentResult]:
        """Get result for a specific agent

        Args:
            agent_id: Agent identifier

        Returns:
            AgentResult or None if not found
        """
        return self.results.get(agent_id)

    def save_to_cache(self, cache_file: Path, response_number: int) -> dict:
        """Save agent results to JSON cache file

        Args:
            cache_file: Path to agent_analysis.json
            response_number: Current response number

        Returns:
            Dict with timing stats including write_ms
        """
        try:
            write_start = time.perf_counter()

            stats = self.get_stats()

            # Build JSON cache structure
            cache_data = {
                "version": "1.0",
                "meta": {
                    "resp_num": response_number,
                    "updated": datetime.now().isoformat(),
                    "status": "fresh",
                    "agents_run": stats['agents_executed'],
                    "agents_ok": stats['successful'],
                    "agents_fail": stats['failed']
                },
                "background": {},
                "immediate": {},
                "stats": {
                    "bg_dur": 0,
                    "bg_cost": 0.0,
                    "im_dur": 0,
                    "im_cost": 0.0,
                    "total_dur": stats.get('max_duration_ms', 0),
                    "total_cost": 0.0  # TODO: Track costs from agents
                }
            }

            # Add each agent's data
            for agent_id, result in self.results.items():
                if result.success:
                    try:
                        # Parse agent's JSON output
                        agent_data = json.loads(result.content)

                        # Categorize by agent type
                        if agent_id in BACKGROUND_AGENTS:
                            cache_data["background"][agent_id] = agent_data
                            cache_data["stats"]["bg_dur"] += result.duration_ms
                        elif agent_id in IMMEDIATE_AGENTS:
                            cache_data["immediate"][agent_id] = agent_data
                            cache_data["stats"]["im_dur"] += result.duration_ms
                        else:
                            # Unknown agent type, put in background by default
                            cache_data["background"][agent_id] = agent_data

                    except json.JSONDecodeError as e:
                        log_to_file(self.log_file, f"[AgentCoordinator] Warning: Agent {agent_id} returned non-JSON content: {e}")
                        # Store as raw text if JSON parsing fails
                        if agent_id in BACKGROUND_AGENTS:
                            cache_data["background"][agent_id] = {"raw": result.content, "error": "non-json"}
                        else:
                            cache_data["immediate"][agent_id] = {"raw": result.content, "error": "non-json"}

            # Write JSON to file
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)

            write_time = (time.perf_counter() - write_start) * 1000

            log_to_file(self.log_file, f"[AgentCoordinator] Saved JSON cache to {cache_file} ({stats['successful']}/{stats['agents_executed']} agents) in {write_time:.1f}ms")

            return {
                'write_ms': round(write_time, 1),
                'agents_ok': stats['successful'],
                'agents_total': stats['agents_executed']
            }

        except Exception as e:
            log_to_file(self.log_file, f"[AgentCoordinator] Error saving cache: {e}")
            import traceback
            log_to_file(self.log_file, traceback.format_exc())
            return {'write_ms': 0, 'agents_ok': 0, 'agents_total': 0}

    def load_from_cache(self, cache_file: Path) -> Optional[str]:
        """Load JSON cache and convert to condensed prompt format

        Args:
            cache_file: Path to agent_analysis.json

        Returns:
            Condensed agent context for prompt injection or None if file doesn't exist
        """
        try:
            if not cache_file.exists():
                log_to_file(self.log_file, "[AgentCoordinator] No cache file found")
                return None

            # Load JSON cache
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Convert to condensed prompt format
            condensed_context = self._format_for_prompt(cache_data)

            log_to_file(self.log_file, f"[AgentCoordinator] Loaded JSON cache successfully (Response {cache_data['meta']['resp_num']})")
            return condensed_context

        except json.JSONDecodeError as e:
            log_to_file(self.log_file, f"[AgentCoordinator] Error parsing JSON cache: {e}")
            return None
        except Exception as e:
            log_to_file(self.log_file, f"[AgentCoordinator] Error loading cache: {e}")
            return None

    def clear_cache(self, cache_file: Path) -> None:
        """Clear agent cache file

        Args:
            cache_file: Path to agent_analysis.json
        """
        try:
            if cache_file.exists():
                cache_file.unlink()
                log_to_file(self.log_file, "[AgentCoordinator] Cleared cache file")
        except Exception as e:
            log_to_file(self.log_file, f"[AgentCoordinator] Error clearing cache: {e}")

    def _format_for_prompt(self, cache_data: dict) -> str:
        """Convert JSON cache to condensed prompt format (~300-400 tokens)

        Args:
            cache_data: JSON cache dict

        Returns:
            Condensed text format for Claude prompt injection
        """
        lines = []
        lines.append("<!-- AGENT CONTEXT -->")

        bg = cache_data.get("background", {})
        im = cache_data.get("immediate", {})

        # Scene summary (if response analyzer ran)
        if "response_analyzer" in bg or "resp_analyzer" in bg:
            resp_data = bg.get("response_analyzer", bg.get("resp_analyzer", {}))
            if "scene" in resp_data:
                scene = resp_data["scene"]
                scene_parts = [f"Scene: {scene.get('type', 'unknown')}"]
                if "tension" in scene:
                    scene_parts.append(f"Tension {scene['tension']}/10")
                if "alerts" in resp_data:
                    alerts = resp_data["alerts"]
                    if alerts.get("variety"):
                        scene_parts.append(f"⚠️ {alerts['variety']}")
                lines.append(f"**Scene**: {', '.join(scene_parts)}")

        # Characters (if response analyzer ran)
        if "response_analyzer" in bg or "resp_analyzer" in bg:
            resp_data = bg.get("response_analyzer", bg.get("resp_analyzer", {}))
            if "chars" in resp_data:
                chars = resp_data["chars"]
                char_parts = []
                if chars.get("in_scene"):
                    char_parts.append(f"In Scene: {', '.join(chars['in_scene'])}")
                if chars.get("mentioned"):
                    char_parts.append(f"Mentioned: {', '.join(chars['mentioned'])}")
                if char_parts:
                    lines.append(f"**Characters**: {' | '.join(char_parts)}")

        # Memories created (if memory creation ran)
        if "memory_creation" in bg or "memory_create" in bg:
            mem_data = bg.get("memory_creation", bg.get("memory_create", {}))
            if "memories" in mem_data:
                mems = mem_data["memories"]
                if mems:
                    top_mem = max(mems, key=lambda m: m.get("sig", 0))
                    mem_summary = f"{len(mems)} created (Top: {top_mem.get('char', 'Unknown')} - {top_mem.get('sum', '')[:40]}... sig:{top_mem.get('sig', 0)})"
                    lines.append(f"**Memories**: {mem_summary}")

        # Relationships (if relationship analysis ran)
        if "relationship_analysis" in bg or "relationship" in bg:
            rel_data = bg.get("relationship_analysis", bg.get("relationship", {}))
            if "interactions" in rel_data and rel_data["interactions"]:
                rel_parts = []
                for inter in rel_data["interactions"][:2]:  # Max 2 relationships
                    chars = inter.get("chars", [])
                    if len(chars) >= 2:
                        rel_parts.append(f"{chars[0]} ↔ {chars[1]}: {inter.get('change', 0):+d} (now {inter.get('score', 0)}, {inter.get('tier', 'Unknown')})")
                if rel_parts:
                    lines.append(f"**Relationships**: {'; '.join(rel_parts)}")

        # Plot threads (if plot thread detection ran)
        if "plot_thread_detection" in bg or "plot_threads" in bg:
            thread_data = bg.get("plot_thread_detection", bg.get("plot_threads", {}))
            thread_lines = []
            if thread_data.get("new"):
                new_ids = [t.get("id", "?") for t in thread_data["new"]]
                thread_lines.append(f"NEW: {', '.join(new_ids)}")
            for t in thread_data.get("mentioned", [])[:3]:  # Max 3 mentioned
                status_emoji = "⚠️" if t.get("status") == "critical" else "📍"
                thread_lines.append(f"{status_emoji} {t.get('id', '?')}: {t.get('title', 'Unknown')}")
            if thread_lines:
                lines.append(f"**Threads**: {', '.join(thread_lines)}")

        # Knowledge facts (if knowledge extraction ran)
        if "knowledge_extraction" in bg or "knowledge" in bg:
            know_data = bg.get("knowledge_extraction", bg.get("knowledge", {}))
            if "facts" in know_data:
                facts = know_data["facts"]
                if facts:
                    fact_subjs = [f.get("subj", "?") for f in facts[:2]]
                    lines.append(f"**Knowledge**: Added {len(facts)} facts ({', '.join(fact_subjs)}...)")

        # Context for next response
        lines.append("")
        lines.append("**Context for N+1**:")

        # Tier 2 entity facts (if fact extraction ran)
        if "fact_extraction" in im or "fact_extract" in im:
            fact_data = im.get("fact_extraction", im.get("fact_extract", {}))
            if "facts" in fact_data:
                for name, facts in list(fact_data["facts"].items())[:2]:  # Max 2 entities
                    if facts:
                        lines.append(f"- {name}: {', '.join(facts[:3])}")  # Max 3 facts each

        # Memories (if memory extraction ran)
        if "memory_extraction" in im or "memory_extract" in im:
            mem_data = im.get("memory_extraction", im.get("memory_extract", {}))
            if "memories" in mem_data:
                for char, mems in list(mem_data["memories"].items())[:2]:  # Max 2 characters
                    if mems:
                        mem_ids = [m.get("id", "?") for m in mems[:2]]  # Max 2 memories each
                        lines.append(f"- {char} Memories: {', '.join(mem_ids)}")

        # Active threads (if thread extraction ran)
        if "plot_thread_extraction" in im or "thread_extract" in im:
            thread_data = im.get("plot_thread_extraction", im.get("thread_extract", {}))
            if "loaded" in thread_data:
                thread_ids = [t.get("id", "?") for t in thread_data["loaded"][:3]]  # Max 3 threads
                if thread_ids:
                    lines.append(f"- Active Threads: {', '.join(thread_ids)}")

        lines.append("<!-- END AGENT CONTEXT -->")

        return "\n".join(lines)


# Example agent functions (to show how to structure agents)

def example_world_state_agent(rp_dir: Path, message: str) -> str:
    """Example: Query world state based on message

    Args:
        rp_dir: RP directory
        message: User message to analyze

    Returns:
        Formatted world state context
    """
    from src.clients.deepseek import call_deepseek

    # Read current state
    state_file = rp_dir / "state" / "current_state.md"
    current_state = state_file.read_text(encoding='utf-8') if state_file.exists() else ""

    # Query DeepSeek
    prompt = f"""Based on this user message and current state, summarize relevant world information.

USER MESSAGE: {message}

CURRENT STATE:
{current_state}

Provide a brief summary (3-5 sentences) of relevant world state information that Claude should know."""

    result = call_deepseek(prompt, rp_dir=rp_dir)

    return f"**World State Context:**\n{result}"


def example_character_memory_agent(rp_dir: Path, character_name: str, message: str) -> str:
    """Example: Query character-specific memories

    Args:
        rp_dir: RP directory
        character_name: Name of character to query
        message: User message to analyze

    Returns:
        Formatted character memory context
    """
    from src.clients.deepseek import call_deepseek

    # Read character card
    char_file = rp_dir / "characters" / f"{character_name}.md"
    if not char_file.exists():
        return f"**{character_name} Memories:** No character file found"

    char_content = char_file.read_text(encoding='utf-8')

    # Query DeepSeek
    prompt = f"""Based on this character and user message, summarize relevant memories/personality traits.

USER MESSAGE: {message}

CHARACTER FILE:
{char_content}

Provide a brief summary (3-5 sentences) of relevant memories or personality traits for this interaction."""

    result = call_deepseek(prompt, rp_dir=rp_dir)

    return f"**{character_name} Context:**\n{result}"


def example_plot_summary_agent(rp_dir: Path) -> str:
    """Example: Summarize recent plot developments

    Args:
        rp_dir: RP directory

    Returns:
        Formatted plot summary
    """
    from src.clients.deepseek import call_deepseek

    # Read story arc
    arc_file = rp_dir / "state" / "story_arc.md"
    story_arc = arc_file.read_text(encoding='utf-8') if arc_file.exists() else "No story arc file"

    # Query DeepSeek
    prompt = f"""Summarize the current plot situation in 2-3 sentences.

STORY ARC:
{story_arc}

Provide a concise summary of where the story currently stands."""

    result = call_deepseek(prompt, rp_dir=rp_dir)

    return f"**Plot Summary:**\n{result}"
