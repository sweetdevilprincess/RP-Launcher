# Agent Development Guide

Complete guide for creating new DeepSeek agents in the RP Claude Code system.

---

## 🎯 Quick Start

Creating a new agent takes ~20 minutes:

1. Copy the template below
2. Fill in 5 methods (ID, description, gather data, build prompt, format output)
3. Add to `__init__.py`
4. Register with AgentCoordinator
5. Done!

---

## 📋 Agent Template

```python
#!/usr/bin/env python3
"""
[Agent Name]

[Brief description of what this agent does]

Part of Phase [X.Y] ([Phase Name])
Runs [after Response N | before Response N+1] (~[X] seconds, [hidden|visible])
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent


class [YourAgent]Agent(BaseAgent):
    """[One-line agent description]

    This agent:
    - [What it does]
    - [What it analyzes]
    - [What it outputs]
    """

    def get_agent_id(self) -> str:
        """Unique agent identifier"""
        return "[your_agent_id]"

    def get_description(self) -> str:
        """Human-readable description"""
        return "[Brief description for logs]"

    def gather_data(self, *args, **kwargs) -> dict:
        """Gather data needed for prompt

        Args:
            [your specific args]

        Returns:
            Dict with all data needed for prompt and output formatting
        """
        # Read files, prepare context
        # Example:
        # some_file = self.rp_dir / "path" / "to" / "file.md"
        # data = self._read_file_safe(some_file, "default value")

        return {
            "key1": "value1",
            "key2": "value2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build DeepSeek prompt from gathered data

        Args:
            data: Dict returned from gather_data()

        Returns:
            Formatted prompt string
        """
        prompt = f"""[Your instruction to DeepSeek]

DATA:
{data['key1']}
{data['key2']}

[What you want DeepSeek to do]

Guidelines:
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

Format as structured text with clear headers."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format DeepSeek result for cache file

        Args:
            result: Raw DeepSeek response
            data: Original data dict from gather_data()

        Returns:
            Formatted output for agent_analysis.md
        """
        output = f"""### [N]️⃣ [Agent Name]
<!-- Agent ID: [your_agent_id] | Phase: [X.Y] ([Phase Name]) -->

**[Context Key]**: {data['key1']}
**Timestamp**: {data['timestamp']}
**Status**: ✅ Success

{result}

---"""
        return output


# Convenience function for standalone use
def [function_name](
    rp_dir: Path,
    # your specific args,
    log_file: Optional[Path] = None
) -> str:
    """[Brief description]

    Args:
        rp_dir: RP directory path
        [your specific args]
        log_file: Optional log file

    Returns:
        Formatted [agent name] string
    """
    agent = [YourAgent]Agent(rp_dir, log_file)
    return agent.execute([your args])
```

---

## 🔧 Step-by-Step Guide

### Step 1: Choose Agent Type

**Background Agent** (runs after Response N, hidden ~30s):
- Analyzes Claude's response
- Extracts information for future use
- User doesn't see this latency
- Example: ResponseAnalyzerAgent, MemoryCreationAgent

**Immediate Agent** (runs before Response N+1, visible ~5s):
- Analyzes user's message
- Gathers context for Claude
- User sees this latency (keep it fast!)
- Example: QuickEntityAnalysisAgent, FactExtractionAgent

### Step 2: Fill in the 5 Required Methods

#### 1. `get_agent_id()` - Unique Identifier

```python
def get_agent_id(self) -> str:
    return "emotion_tracker"  # Use snake_case, no spaces
```

**Guidelines:**
- Use snake_case (lowercase with underscores)
- Be specific (not generic like "analyzer")
- Should match class name without "Agent" suffix

#### 2. `get_description()` - Human-Readable Description

```python
def get_description(self) -> str:
    return "Track emotional states and shifts for each character"
```

**Guidelines:**
- Brief (one sentence)
- Describes WHAT it does, not HOW
- Used in logs and coordinator output

#### 3. `gather_data()` - Prepare Context

```python
def gather_data(self, response_text: str, characters: List[str]) -> dict:
    # Read files you need
    emotion_history_file = self.rp_dir / "state" / "emotion_history.json"
    emotion_history = self._read_file_safe(emotion_history_file, "{}")

    # Prepare context
    return {
        "response_text": response_text,
        "characters": characters,
        "emotion_history": emotion_history,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
```

**Guidelines:**
- Read files using `self._read_file_safe(path, default)`
- Return a dict with ALL data you need
- Include timestamp for logging
- Accept `*args, **kwargs` for flexibility

#### 4. `build_prompt()` - DeepSeek Prompt

```python
def build_prompt(self, data: dict) -> str:
    prompt = f"""Track emotional states in this response.

RESPONSE TEXT:
{data['response_text']}

CHARACTERS: {', '.join(data['characters'])}

EMOTION HISTORY:
{data['emotion_history']}

For each character, identify:
1. Primary emotion (current state)
2. Secondary emotion (underlying feeling)
3. Emotion shift (did it change from before?)
4. Intensity (1-10)

Format as structured text with clear headers."""

    return prompt
```

**Guidelines:**
- Be specific about what you want
- Provide context (files, history, etc.)
- Request structured output format
- Keep prompts concise (token cost!)
- Use clear headers and sections

#### 5. `format_output()` - Format for Cache

```python
def format_output(self, result: str, data: dict) -> str:
    output = f"""### 1️⃣1️⃣ Emotion Tracker
<!-- Agent ID: emotion_tracker | Phase: [X.Y] -->

**Characters**: {', '.join(data['characters'])}
**Timestamp**: {data['timestamp']}
**Status**: ✅ Success

{result}

---"""
    return output
```

**Guidelines:**
- Follow the cache file format (see AGENT_CACHE_SPEC.md)
- Include agent ID, phase, timestamp
- Use emoji number based on agent order
- End with `---` separator
- Include metadata in HTML comments

### Step 3: Add to Package

Update `src/automation/agents/__init__.py`:

```python
# Add import
from src.automation.agents.background.emotion_tracker import EmotionTrackerAgent

# Add to __all__
__all__ = [
    # ... existing agents ...
    "EmotionTrackerAgent",
]
```

If it's a background agent, also update `background/__init__.py`.
If it's an immediate agent, also update `immediate/__init__.py`.

### Step 4: Register with AgentCoordinator

```python
from src.automation.agents import EmotionTrackerAgent
from src.automation.agent_coordinator import AgentCoordinator

# Create agent
emotion_tracker = EmotionTrackerAgent(rp_dir, log_file)

# Register with coordinator
coordinator = AgentCoordinator(rp_dir, log_file)
coordinator.add_agent(
    emotion_tracker.get_agent_id(),
    emotion_tracker.execute,
    response_text, characters,  # Your agent's args
    description=emotion_tracker.get_description()
)

# Run all agents
context = coordinator.run_all_agents(timeout=30)
```

### Step 5: Test

```python
# Test standalone
from src.automation.agents import EmotionTrackerAgent
from pathlib import Path

rp_dir = Path("Example RP")
log_file = rp_dir / "state" / "hook.log"

agent = EmotionTrackerAgent(rp_dir, log_file)
result = agent.execute("response text here", ["Marcus", "Lily"])

print(result)
```

---

## 💡 Best Practices

### Data Gathering

✅ **DO:**
```python
def gather_data(self, response_text: str) -> dict:
    # Use utility method for safe file reading
    file_path = self.rp_dir / "state" / "data.json"
    data = self._read_file_safe(file_path, "{}")

    return {
        "response_text": response_text,
        "data": data
    }
```

❌ **DON'T:**
```python
def gather_data(self, response_text: str) -> dict:
    # Don't crash if file doesn't exist
    file_path = self.rp_dir / "state" / "data.json"
    data = file_path.read_text()  # Will crash if file doesn't exist!

    return {"response_text": response_text}
```

### Prompt Building

✅ **DO:**
```python
def build_prompt(self, data: dict) -> str:
    # Clear structure, specific instructions
    return f"""Analyze this text for emotion.

TEXT:
{data['text']}

Identify:
1. Primary emotion
2. Intensity (1-10)
3. Triggers

Format as bullet points."""
```

❌ **DON'T:**
```python
def build_prompt(self, data: dict) -> str:
    # Too vague, no structure
    return f"What emotions are in this text? {data['text']}"
```

### Output Formatting

✅ **DO:**
```python
def format_output(self, result: str, data: dict) -> str:
    # Follow cache format, include metadata
    return f"""### 7️⃣ Emotion Tracker
<!-- Agent ID: emotion_tracker | Phase: 1.4 -->

**Timestamp**: {data['timestamp']}
**Status**: ✅ Success

{result}

---"""
```

❌ **DON'T:**
```python
def format_output(self, result: str, data: dict) -> str:
    # No structure, no metadata
    return result
```

---

## 🧪 Testing Your Agent

### Unit Test Template

```python
# tests/test_emotion_tracker.py
import pytest
from pathlib import Path
from src.automation.agents import EmotionTrackerAgent

def test_emotion_tracker():
    # Setup
    rp_dir = Path("test_rp")
    agent = EmotionTrackerAgent(rp_dir)

    # Execute
    result = agent.execute("test response", ["Marcus"])

    # Verify
    assert "Emotion Tracker" in result
    assert "Marcus" in result
    assert "---" in result  # Has separator
```

### Integration Test with AgentCoordinator

```python
def test_emotion_tracker_with_coordinator():
    rp_dir = Path("test_rp")
    log_file = rp_dir / "test.log"

    # Create coordinator
    coordinator = AgentCoordinator(rp_dir, log_file)

    # Register agent
    agent = EmotionTrackerAgent(rp_dir, log_file)
    coordinator.add_agent(
        agent.get_agent_id(),
        agent.execute,
        "test response", ["Marcus"],
        description=agent.get_description()
    )

    # Run
    context = coordinator.run_all_agents(timeout=10)

    # Verify
    assert "Emotion Tracker" in context
    assert coordinator.get_stats()['successful'] == 1
```

---

## 📊 Common Patterns

### Pattern 1: Analyzing Response Text

```python
def gather_data(self, response_text: str, response_number: int) -> dict:
    return {
        "response_text": response_text,
        "response_number": response_number,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def build_prompt(self, data: dict) -> str:
    return f"""Analyze this response.

RESPONSE:
{data['response_text']}

[Your analysis instructions]"""
```

### Pattern 2: Master File + Extraction

```python
def gather_data(self, user_message: str) -> dict:
    # Load master file
    master_file = self.rp_dir / "state" / "master_data.md"
    master_data = self._read_file_safe(master_file, "")

    return {
        "user_message": user_message,
        "master_data": master_data
    }

def build_prompt(self, data: dict) -> str:
    return f"""Extract 2-5 relevant items from master file.

USER MESSAGE:
{data['user_message']}

MASTER FILE:
{data['master_data']}

Select only the most relevant items for this conversation."""
```

### Pattern 3: Cross-File Analysis

```python
def gather_data(self, response_text: str, characters: List[str]) -> dict:
    # Read multiple related files
    character_data = {}
    for char in characters:
        char_file = self.rp_dir / "characters" / f"{char}.md"
        character_data[char] = self._read_file_safe(char_file, "")

    return {
        "response_text": response_text,
        "character_data": character_data
    }
```

---

## 🚀 Performance Tips

1. **Keep prompts concise** - Shorter prompts = faster execution
2. **Limit file reading** - Only read what you need
3. **Use temperature=0.3** - Default in BaseAgent for consistent analysis
4. **Parallelize when possible** - AgentCoordinator runs agents concurrently
5. **Cache file contents** - Don't re-read same file multiple times

---

## 🔍 Debugging Tips

### Enable Verbose Logging

```python
agent = EmotionTrackerAgent(rp_dir, log_file)
result = agent.execute(args)

# Check log file
print(log_file.read_text())
```

### Test Without Coordinator

```python
# Test agent directly
agent = EmotionTrackerAgent(rp_dir)
try:
    result = agent.execute("test input")
    print("Success:", result)
except Exception as e:
    print("Error:", e)
```

### Check DeepSeek Response

```python
# Temporarily print raw result
def format_output(self, result: str, data: dict) -> str:
    print("RAW DEEPSEEK RESULT:", result)  # Debug line
    return f"""..."""
```

---

## 📚 Examples

See the existing agents for reference:

**Simple Agent** (good starting point):
- `knowledge_extraction.py` - Reads one file, simple extraction
- `quick_entity_analysis.py` - Analyzes user message, simple output

**Medium Complexity**:
- `memory_creation.py` - Multiple outputs, structured format
- `plot_thread_detection.py` - Multiple categories

**Complex Agent** (advanced):
- `response_analyzer.py` - Multiple analyses, variety checking
- `relationship_analysis.py` - Cross-file reading, scoring logic

---

## 🎯 Checklist

Before considering your agent complete:

- [ ] All 5 methods implemented
- [ ] Uses `self._read_file_safe()` for file reading
- [ ] Includes timestamp in gather_data()
- [ ] Prompt has clear instructions and format request
- [ ] Output follows cache file format (see AGENT_CACHE_SPEC.md)
- [ ] Added to `__init__.py`
- [ ] Added convenience function
- [ ] Tested standalone
- [ ] Tested with AgentCoordinator
- [ ] Handles missing files gracefully
- [ ] No hardcoded paths
- [ ] Documentation/docstrings complete

---

## 🆘 Troubleshooting

**Agent not found when importing:**
- Check `__init__.py` has correct import
- Check file is in correct directory (background vs immediate)
- Check class name matches

**DeepSeek returns empty/unexpected result:**
- Check prompt clarity
- Check if you're passing correct data
- Test prompt manually at https://openrouter.ai
- Check temperature (should be 0.3 for analysis)

**Agent crashes:**
- Check file reading (use `_read_file_safe`)
- Check all required data is in gather_data() return dict
- Check prompt f-string has all required keys
- Add try/except for debugging

**Performance issues:**
- Check prompt length (shorter = faster)
- Check if reading too many files
- Consider caching file contents
- Limit master file reading to first N items

---

**Questions?** Check existing agents in `background/` and `immediate/` directories for examples!
