# Multi-Agent Coordination System

Coordinate multiple DeepSeek agents to gather context before each Claude response. Each agent can query different areas (world state, character memories, plot developments, etc.) and all results are collected and injected into Claude's prompt.

## 🎯 How It Works

```
User Message
     ↓
[Agent Coordinator]
     ├─→ World State Agent ──→ Query current state
     ├─→ Character Memory Agent ──→ Query character info
     ├─→ Plot Summary Agent ──→ Summarize recent events
     └─→ Location Agent ──→ Describe current location

All agents run CONCURRENTLY (15 seconds total, not 60!)
     ↓
[Results Collected & Formatted]
     ↓
Agent Context + User Message
     ↓
Sent to Claude
```

## 📝 Basic Usage

### Example 1: Simple Agent Setup

```python
from pathlib import Path
from src.automation.agent_coordinator import AgentCoordinator

# Initialize coordinator
rp_dir = Path("Example RP")
log_file = rp_dir / "state" / "hook.log"
coordinator = AgentCoordinator(rp_dir, log_file, max_workers=4)

# Register agents
coordinator.add_agent(
    "world_state",
    query_world_state_func,
    rp_dir, message,
    description="Query relevant world state"
)

coordinator.add_agent(
    "character_memory",
    query_character_memory_func,
    rp_dir, "Lilith", message,
    description="Lilith's relevant memories"
)

coordinator.add_agent(
    "plot_tracker",
    summarize_recent_plot_func,
    rp_dir,
    description="Recent plot developments"
)

# Run all agents concurrently (15s total instead of 45s sequential)
agent_context = coordinator.run_all_agents(timeout=30)

# Inject into Claude prompt
full_prompt = agent_context + "\n\n" + user_message
```

### Example 2: Integration with Automation

```python
# In your automation flow (e.g., orchestrator.py)

def run_automation_with_agents(self, message: str):
    # ... existing automation (counter, time tracking, etc.) ...

    # Run multi-agent context gathering
    coordinator = AgentCoordinator(self.rp_dir, self.log_file)

    # Register your custom agents
    coordinator.add_agent("world_state", self._query_world_state, message)
    coordinator.add_agent("character_context", self._query_character_context, "Lilith", message)
    coordinator.add_agent("location_details", self._query_location_details, message)

    # Execute all agents concurrently
    agent_context = coordinator.run_all_agents(timeout=30, allow_partial=True)

    # Build final prompt
    cached_context, dynamic_prompt, loaded_entities = self._build_prompts(...)

    # Inject agent context into dynamic prompt
    enhanced_dynamic_prompt = agent_context + "\n\n" + dynamic_prompt

    return cached_context, enhanced_dynamic_prompt, loaded_entities
```

## 🏗️ Creating Your Own Agents

### Agent Function Structure

Agents are just Python functions that return a string:

```python
def my_custom_agent(rp_dir: Path, message: str, *args) -> str:
    """
    Custom agent to query something.

    Args:
        rp_dir: RP directory path
        message: User message to analyze
        *args: Any other arguments you need

    Returns:
        String content to inject into Claude prompt
    """
    from src.clients.deepseek import call_deepseek

    # 1. Gather information
    some_file = rp_dir / "some_data.md"
    data = some_file.read_text() if some_file.exists() else ""

    # 2. Query DeepSeek
    prompt = f"""Analyze this message and data:

MESSAGE: {message}
DATA: {data}

Provide relevant context in 3-4 sentences."""

    result = call_deepseek(prompt, rp_dir=rp_dir)

    # 3. Format for Claude
    return f"**My Custom Context:**\n{result}"
```

### Example Agents (Ready to Use)

**World State Agent:**
```python
def query_world_state(rp_dir: Path, message: str) -> str:
    """Summarize relevant world state based on message"""
    from src.clients.deepseek import call_deepseek

    state_file = rp_dir / "state" / "current_state.md"
    current_state = state_file.read_text(encoding='utf-8') if state_file.exists() else ""

    prompt = f"""Based on this user message, extract relevant world state context.

USER MESSAGE: {message}

CURRENT STATE:
{current_state}

Provide 3-5 sentences of relevant world information."""

    result = call_deepseek(prompt, rp_dir=rp_dir, temperature=0.3)
    return f"**World State:**\n{result}"
```

**Character Memory Agent:**
```python
def query_character_memories(rp_dir: Path, character_name: str, message: str) -> str:
    """Query character-specific memories and personality"""
    from src.clients.deepseek import call_deepseek

    char_file = rp_dir / "characters" / f"{character_name}.md"
    if not char_file.exists():
        return f"**{character_name}:** No character file found"

    char_content = char_file.read_text(encoding='utf-8')

    prompt = f"""Given this character and message, summarize relevant personality/memories.

USER MESSAGE: {message}

CHARACTER INFO:
{char_content}

Provide 3-4 sentences of relevant character context."""

    result = call_deepseek(prompt, rp_dir=rp_dir, temperature=0.3)
    return f"**{character_name} Context:**\n{result}"
```

**Plot Tracker Agent:**
```python
def summarize_plot_developments(rp_dir: Path) -> str:
    """Summarize recent plot developments"""
    from src.clients.deepseek import call_deepseek

    arc_file = rp_dir / "state" / "story_arc.md"
    story_arc = arc_file.read_text(encoding='utf-8') if arc_file.exists() else "No story arc"

    prompt = f"""Summarize the current plot situation in 2-3 sentences.

STORY ARC:
{story_arc}

Concise summary of current plot status:"""

    result = call_deepseek(prompt, rp_dir=rp_dir, temperature=0.3)
    return f"**Plot Status:**\n{result}"
```

**Location Details Agent:**
```python
def query_location_details(rp_dir: Path, message: str) -> str:
    """Provide details about current/mentioned location"""
    from src.clients.deepseek import call_deepseek

    # Extract location mentions from message
    locations_dir = rp_dir / "locations"
    if not locations_dir.exists():
        return "**Location:** No locations directory"

    # Simple: Load all location files (or filter by message content)
    location_files = list(locations_dir.glob("*.md"))
    if not location_files:
        return "**Location:** No location files"

    # For simplicity, load all (or implement smart filtering)
    locations_content = "\n\n".join([
        f.read_text(encoding='utf-8') for f in location_files[:3]  # Limit to 3
    ])

    prompt = f"""Based on this message, identify relevant location details.

USER MESSAGE: {message}

AVAILABLE LOCATIONS:
{locations_content}

Provide 2-3 sentences about relevant location context:"""

    result = call_deepseek(prompt, rp_dir=rp_dir, temperature=0.3)
    return f"**Location Context:**\n{result}"
```

## 🚀 Advanced Features

### Partial Success Mode (Recommended)

By default, `allow_partial=True` means if some agents fail, you still get the successful results:

```python
# Agent 1: Success ✓
# Agent 2: Failed (low balance) ✗
# Agent 3: Success ✓
# Agent 4: Failed (timeout) ✗

# Result: Returns context from Agent 1 & 3 (partial success)
context = coordinator.run_all_agents(timeout=30, allow_partial=True)
```

### Strict Mode

If you need ALL agents to succeed:

```python
try:
    context = coordinator.run_all_agents(timeout=30, allow_partial=False)
except RuntimeError:
    # All agents failed, handle error
    context = ""
```

### Timeout Control

```python
# Fast mode: 15 second timeout
context = coordinator.run_all_agents(timeout=15, allow_partial=True)

# Safe mode: 60 second timeout
context = coordinator.run_all_agents(timeout=60, allow_partial=True)
```

### Result Inspection

```python
# Run agents
context = coordinator.run_all_agents(timeout=30)

# Check what happened
stats = coordinator.get_stats()
print(stats)
# {
#     'agents_registered': 4,
#     'agents_executed': 4,
#     'successful': 3,
#     'failed': 1,
#     'balance_errors': 0,
#     'avg_duration_ms': 12500,
#     'max_duration_ms': 15200
# }

# Get specific agent result
world_result = coordinator.get_result("world_state")
if world_result and world_result.success:
    print(f"World state query took {world_result.duration_ms}ms")
```

### Reusing Coordinator

```python
# Create once
coordinator = AgentCoordinator(rp_dir, log_file)

# Use for first message
coordinator.add_agent("agent1", func1)
coordinator.add_agent("agent2", func2)
context1 = coordinator.run_all_agents()

# Clear and reuse for next message
coordinator.clear_agents()
coordinator.add_agent("agent3", func3)
coordinator.add_agent("agent4", func4)
context2 = coordinator.run_all_agents()
```

## 📊 Output Format

The coordinator formats results as markdown comments that Claude can read:

```markdown
<!-- ========== AGENT CONTEXT SYNTHESIS ========== -->
<!-- Generated: 2025-10-14 16:45:30 -->
<!-- Agents: 3 successful, 1 failed -->

### Agent: Query relevant world state
<!-- Agent ID: world_state | Duration: 12300ms -->

**World State:**
The cafe is busy this evening. Marcus has been working behind the counter
for the past 3 hours. The espresso machine broke down earlier but was fixed.

### Agent: Lilith's relevant memories
<!-- Agent ID: character_memory | Duration: 11800ms -->

**Lilith Context:**
Lilith remembers Marcus from their childhood. She's been avoiding the cafe
lately due to her strained relationship with him. She's secretly worried
about his wellbeing.

### Agent: Recent plot developments
<!-- Agent ID: plot_tracker | Duration: 10500ms -->

**Plot Status:**
The story is currently in Act 2. Lilith has just discovered Marcus's secret.
The tension between them is reaching a breaking point.

<!-- AGENT FAILURES -->
<!-- ERROR: location_agent - Timeout after 30 seconds -->

<!-- ========== END AGENT CONTEXT ========== -->
```

## ⚡ Performance

### Sequential (Old Way)
```
Agent 1: [████████████] 15s
Agent 2: [████████████] 12s
Agent 3: [████████████] 11s
Agent 4: [████████████] 14s
Total: 52 seconds
```

### Concurrent (New Way)
```
Agent 1: [████████████] 15s
Agent 2: [████████████] 12s  ← All running simultaneously
Agent 3: [████████████] 11s
Agent 4: [████████████] 14s
Total: 15 seconds (longest agent)
```

**Speedup: 3-4x faster!**

## 🛡️ Error Handling

### Low Balance (402 Error)
```
[AgentCoordinator] Executing: world_state
[AgentCoordinator] ⚠️ world_state FAILED - LOW BALANCE: OpenRouter account balance is too low
[AgentCoordinator] Completed: 2/3 successful in 15000ms
[AgentCoordinator] ⚠️ WARNING: 1 agents failed due to low balance
```

Context still returned with partial results + note about failure.

### Timeout
```python
try:
    context = coordinator.run_all_agents(timeout=15)
except concurrent.futures.TimeoutError:
    # Agents didn't complete in time
    print("Agents timed out, using fallback")
    context = ""
```

### Complete Failure
```python
context = coordinator.run_all_agents(allow_partial=True)
if not context:
    # All agents failed, use fallback
    print("No agent context available")
```

## 📦 Complete Integration Example

```python
# In src/automation/orchestrator.py

from src.automation.agent_coordinator import AgentCoordinator

class AutomationOrchestrator:
    def __init__(self, rp_dir: Path):
        # ... existing init ...
        self.agent_coordinator = AgentCoordinator(rp_dir, self.log_file, max_workers=4)

    def run_automation_with_caching(self, message: str):
        # ... existing automation steps ...

        # STEP 5.5: Run multi-agent context gathering
        with profiler.measure("agent_coordination") if profiler else self._nullcontext():
            self.agent_coordinator.clear_agents()

            # Register agents for this message
            self.agent_coordinator.add_agent(
                "world_state",
                query_world_state,
                self.rp_dir, message,
                description="World state query"
            )

            self.agent_coordinator.add_agent(
                "character_memory",
                query_character_memories,
                self.rp_dir, "Lilith", message,
                description="Lilith's memories"
            )

            self.agent_coordinator.add_agent(
                "plot_summary",
                summarize_plot_developments,
                self.rp_dir,
                description="Plot summary"
            )

            # Execute all agents (15 seconds concurrent, not 45 sequential!)
            try:
                agent_context = self.agent_coordinator.run_all_agents(
                    timeout=30,
                    allow_partial=True
                )
            except Exception as e:
                log_to_file(self.log_file, f"Agent coordination failed: {e}")
                agent_context = ""

        # ... continue with rest of automation ...

        # Build final prompt with agent context
        dynamic_prompt_sections = []

        if agent_context:
            dynamic_prompt_sections.append(agent_context)

        # ... add other sections ...

        dynamic_prompt = '\n\n'.join(dynamic_prompt_sections)

        return cached_context, dynamic_prompt, loaded_entities, profiler
```

## 💡 Best Practices

1. **Keep agents focused**: Each agent should query one specific area
2. **Use temperature=0.3**: More deterministic results for context
3. **Enable partial success**: Don't block on one failing agent
4. **Set reasonable timeouts**: 30 seconds is usually enough
5. **Monitor OpenRouter balance**: Keep $10+ for smooth operation
6. **Log agent activity**: Helps debug what each agent is doing
7. **Reuse coordinator**: Create once, clear and reuse per message

## 🧪 Testing

Create a test file to verify agents work:

```python
# test_agents.py
from pathlib import Path
from src.automation.agent_coordinator import (
    AgentCoordinator,
    example_world_state_agent,
    example_character_memory_agent,
    example_plot_summary_agent
)

rp_dir = Path("Example RP")
log_file = rp_dir / "state" / "test_agents.log"

coordinator = AgentCoordinator(rp_dir, log_file, max_workers=3)

# Register test agents
coordinator.add_agent(
    "world_state",
    example_world_state_agent,
    rp_dir, "Lilith walks into the cafe",
    description="World state test"
)

coordinator.add_agent(
    "character_memory",
    example_character_memory_agent,
    rp_dir, "Lilith", "She sees Marcus behind the counter",
    description="Character memory test"
)

coordinator.add_agent(
    "plot_summary",
    example_plot_summary_agent,
    rp_dir,
    description="Plot summary test"
)

# Run and print results
print("Running agents...")
context = coordinator.run_all_agents(timeout=45, allow_partial=True)

print("\n=== AGENT CONTEXT ===")
print(context)
print("\n=== STATS ===")
print(coordinator.get_stats())
```

You're all set! The multi-agent coordination system is ready for your brainstorming session. 🎉
