# Agent Development Guide

Complete reference for developing, integrating, and documenting agents in the RP Claude Code system.

---

## TABLE OF CONTENTS

1. [Agent Architecture](#agent-architecture)
2. [The 5-Method Pattern](#the-5-method-pattern)
3. [BaseAgent Reference](#baseagent-reference)
4. [JSON Output Schemas](#json-output-schemas)
5. [Step-by-Step: Create a New Agent](#step-by-step-create-a-new-agent)
6. [Registration & Integration](#registration--integration)
7. [Real Code Examples](#real-code-examples)
8. [Quick Reference Template](#quick-reference-template)
9. [Common Patterns](#common-patterns)
10. [Debugging & Testing](#debugging--testing)

---

## AGENT ARCHITECTURE

### Overview

All agents in this system follow a standardized pattern:

```
User Message/Response
        ↓
    Gather Data (read files, prepare context)
        ↓
    Build Prompt (format for DeepSeek with JSON schema)
        ↓
    Call DeepSeek API (AI analyzes with your prompt)
        ↓
    Format Output (parse result to standard JSON)
        ↓
    Cache Result (save to state/agent_analysis.json)
        ↓
    Next Pipeline Stage
```

### Agent Types

**Background Agents** (run AFTER response):
- Execute in parallel (ThreadPoolExecutor)
- 3-5 second timeout each
- Run while user types next message (hidden)
- Update state files (memories, relationships, plot threads, facts)
- No user latency

**Immediate Agents** (run BEFORE response):
- Execute in parallel (ThreadPoolExecutor)
- 3-5 second timeout each
- User sees latency (~3 seconds total)
- Gather context for Claude (entity tiers, facts, memories, threads)
- Results cached for this cycle

---

## THE 5-METHOD PATTERN

Every agent must override exactly 5 methods from `BaseAgent`:

### 1. `get_agent_id() -> str`

Returns unique identifier for this agent.

```python
def get_agent_id(self) -> str:
    return "my_agent"  # lowercase, underscore separated, unique
```

**Used for**:
- Logging and identification
- Config lookup
- Error messages
- Registration in factory

**Naming convention**: `snake_case`, descriptive, unique
- Good: `response_analyzer`, `memory_extraction`, `plot_thread_detection`
- Bad: `agent1`, `MyAgent`, `analyzer-agent`

---

### 2. `get_description() -> str`

Returns human-readable description of what agent does.

```python
def get_description(self) -> str:
    return "Analyzes scene structure and pacing"
```

**Used for**:
- Logging and debugging
- Status messages
- Documentation
- User-facing reports

**Should be**:
- Concise (one sentence)
- Clear about purpose
- Active voice

---

### 3. `gather_data(*args, **kwargs) -> dict`

Reads files, prepares context, returns data dict for prompt.

```python
def gather_data(self, response_text: str, response_number: int) -> dict:
    """Gather data for analysis

    Args:
        response_text: The text to analyze
        response_number: Current response number

    Returns:
        Dict with all needed data
    """
    return {
        "response_text": response_text,
        "response_number": response_number,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
```

**Responsibilities**:
- Read files from disk if needed (`self.rp_dir`)
- Parse JSON/markdown
- Handle missing files gracefully
- Prepare context for prompt
- Return dict (not tuple, not list)

**Best practices**:
- Check file existence before reading
- Use try/except for file operations
- Add timestamp for tracking
- Include any data needed by format_output()
- Log warnings if files missing

---

### 4. `build_prompt(data: dict) -> str`

Formats the DeepSeek prompt with JSON schema for structured output.

```python
def build_prompt(self, data: dict) -> str:
    """Build DeepSeek prompt with JSON schema

    Args:
        data: Dict from gather_data()

    Returns:
        Formatted prompt string
    """
    prompt = f"""Analyze this response and return structured data.

TEXT TO ANALYZE:
{data['response_text']}

Return your analysis as JSON:

{{
  "type": "<value1|value2>",
  "score": <1-10>,
  "details": "<explanation>"
}}

Return ONLY the JSON object, no additional text."""

    return prompt
```

**CRITICAL**:
- **Always include a JSON schema in the prompt**
- Example format in triple braces `{{}}`
- Tell DeepSeek to return ONLY JSON
- Never ask for markdown or prose

**Structure**:
1. Task description
2. Context/data to analyze
3. Clear JSON schema
4. Instruction: "Return ONLY the JSON"

**Why JSON?**:
- Consistent, parseable output
- Easy to cache and combine
- No ambiguity in formatting
- Can validate schema

---

### 5. `format_output(result: str, data: dict) -> str`

Parses DeepSeek result, validates, returns standardized JSON string.

```python
def format_output(self, result: str, data: dict) -> str:
    """Format result for cache

    Args:
        result: Raw JSON from DeepSeek
        data: Original data dict (may have duration_ms)

    Returns:
        JSON string ready for cache
    """
    try:
        # Parse the JSON response
        analysis = json.loads(result.strip())

        # Build standardized output
        output = {
            "type": analysis.get("type", "unknown"),
            "score": analysis.get("score", 0),
            "details": analysis.get("details", "")
        }

        # Add execution time if tracked
        if "duration_ms" in data:
            output["dur"] = data["duration_ms"]

        # Return as JSON string
        return json.dumps(output)

    except json.JSONDecodeError as e:
        # Log error and return empty result
        if self.log_file:
            log_to_file(self.log_file, f"[{self.get_agent_id()}] JSON parse error: {e}")
        return json.dumps({"error": str(e)})
```

**Responsibilities**:
- Parse JSON from DeepSeek
- Extract fields you care about
- Validate data types
- Handle errors gracefully
- Add duration_ms if present (from BaseAgent)
- Return JSON string (not dict)

**Error handling**:
- Catch `json.JSONDecodeError`
- Log the error
- Return empty/default result
- Never raise exception (breaks pipeline)

---

## BaseAgent Reference

### BaseAgent Class

**Location**: `src/automation/agents/base_agent.py`

**What it provides**:
- Abstract base class (must be subclassed)
- Common `execute()` method (handles timing, logging, error handling)
- Framework for your 5 methods

### Constructor

```python
def __init__(self, rp_dir: Path, log_file: Optional[Path] = None):
    self.rp_dir = rp_dir        # RP directory path
    self.log_file = log_file    # Log file for agent activity
```

**Usage**:
```python
agent = MyAgent(rp_dir=Path("/path/to/rp"), log_file=Path("/path/to/hook.log"))
```

### Execute Method

Called by agent coordinator. Handles the pipeline:

```python
result = agent.execute(arg1, arg2, kwarg1=value1)
```

**What execute() does**:
1. Logs "Executing agent"
2. Calls `gather_data(*args, **kwargs)`
3. Calls `build_prompt(data)`
4. Calls `call_deepseek(prompt)`
5. Calls `format_output(result, data)`
6. Logs execution time
7. Returns formatted result
8. Catches and logs all errors

**You never call execute directly** - the agent coordinator does.

### Imports to Use

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent
from src.clients.deepseek import call_deepseek
from src.automation.core import log_to_file
```

---

## JSON OUTPUT SCHEMAS

Every agent must define a JSON schema. Here are the patterns used:

### Background Agent Patterns

#### Response Analyzer Schema
```json
{
  "scene": {
    "type": "dialogue|action|introspection|transition|world_building",
    "pace": "fast|medium|slow",
    "tension": 1-10,
    "words": 150
  },
  "chars": {
    "in_scene": ["char1", "char2"],
    "mentioned": ["char3"],
    "new": ["new_char"]
  },
  "loc": "location description",
  "loc_changed": true,
  "time": {
    "elapsed": "30 minutes",
    "timestamp": "Tuesday 3:00 PM",
    "day_chapter": "Day 3"
  },
  "alerts": {
    "variety": "good|warning|critical",
    "variety_msg": "warning text or null",
    "tension_flat": false,
    "recommendation": "suggestion or null"
  }
}
```

**Used by**: Response Analyzer Agent
**Output to**: `state/agent_analysis.json` → `responses[N].analysis`

#### Memory Schema
```json
{
  "id": "MEMORY-uuid",
  "title": "Memory title",
  "characters": ["char1", "char2"],
  "location": "location name",
  "type": "revelation|conflict|first_meeting|character_moment|relationship_development|plot_event",
  "significance": 1-10,
  "emotional_tone": "positive|negative|neutral|mixed",
  "key_quote": "important quote",
  "tags": ["tag1", "tag2"],
  "summary": "brief summary"
}
```

**Used by**: Memory Creation Agent
**Output to**: `memories/{character}/*.md`

#### Relationship Change Schema
```json
{
  "character_pair": ["char1", "char2"],
  "tier": "enemy|hostile|stranger|acquaintance|friend|close_friend|best_friend",
  "score_delta": 5,
  "trigger_event": "what caused the change",
  "reason": "why this change happened",
  "mutual": true
}
```

**Used by**: Relationship Analysis Agent
**Output to**: `state/relationships.json` → updates

#### Plot Thread Schema
```json
{
  "id": "THREAD-###",
  "title": "Thread title",
  "priority": "high|medium|low",
  "status": "active|critical|resolved",
  "time_sensitivity": "immediate|near-term|long-term",
  "consequence_countdown": 5,
  "characters_involved": ["char1", "char2"],
  "location": "relevant location",
  "description": "detailed description",
  "tags": ["tag1", "tag2"]
}
```

**Used by**: Plot Thread Detection Agent
**Output to**: `state/plot_threads_master.md`

#### Knowledge/Fact Schema
```json
{
  "category": "setting|locations|organizations|cultural|geography|items|history",
  "subject": "what is this about",
  "fact": "the actual fact statement",
  "confidence": "high|medium|low",
  "context": "where we learned this",
  "tags": ["tag1", "tag2"]
}
```

**Used by**: Knowledge Extraction Agent
**Output to**: `state/knowledge_base.md`

### Immediate Agent Patterns

#### Entity Analysis Schema
```json
{
  "tier1": ["character1", "character2"],
  "tier2": ["character3"],
  "tier3_count": 5,
  "locs": ["location1", "location2"],
  "new_entities": [
    {
      "name": "NewChar",
      "note": "description or reason for card"
    }
  ]
}
```

**Used by**: Quick Entity Analysis Agent
**Output to**: `state/agent_analysis.json` → `entity_analysis`

#### Facts Schema
```json
{
  "entities": {
    "EntityName": {
      "facts": [
        "First important fact",
        "Second important fact",
        "Third important fact"
      ]
    }
  }
}
```

**Used by**: Fact Extraction Agent
**Output to**: `state/agent_analysis.json` → `fact_extraction`

#### Memory Extraction Schema
```json
{
  "characters": {
    "CharName": {
      "memories": [
        {
          "id": "MEMORY-uuid",
          "title": "Memory title",
          "when": "when it happened",
          "why_relevant": "why this memory matters now",
          "summary": "brief description"
        }
      ]
    }
  }
}
```

**Used by**: Memory Extraction Agent
**Output to**: `state/agent_analysis.json` → `memory_extraction`

#### Plot Threads Schema
```json
{
  "total_active": 5,
  "loaded_threads": [
    {
      "id": "THREAD-001",
      "title": "Thread title",
      "priority": "high",
      "countdown": 3,
      "why_relevant": "why included for this message",
      "status": "active"
    }
  ],
  "monitored_threads": 2
}
```

**Used by**: Plot Thread Extraction Agent
**Output to**: `state/agent_analysis.json` → `plot_extraction`

---

## STEP-BY-STEP: CREATE A NEW AGENT

### Step 1: Decide Agent Type

**Question**: Should this be a background or immediate agent?

- **Background**: Analyzes responses, updates state files
- **Immediate**: Gathers context before response

**Example**: "I want an agent that detects contradictions in dialogue"
- → Background agent (runs after response)

### Step 2: Create File

**Location depends on type**:
- Background: `src/automation/agents/background/my_agent.py`
- Immediate: `src/automation/agents/immediate/my_agent.py`

**Naming**: `lowercase_underscore.py` (e.g., `contradiction_detector.py`)

### Step 3: Write Agent Class

**Use this template**:

```python
#!/usr/bin/env python3
"""
Agent Name

Brief description of what this agent does.
One or two sentences.

Part of Phase X.X (System Area)
Timing info: Runs [before|after] Response N [timing info]
"""

import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent
from src.automation.core import log_to_file


class MyAgentName(BaseAgent):
    """Human-readable agent description

    Detailed explanation of what this agent does, how it works,
    what data it processes, and what it outputs.
    """

    def get_agent_id(self) -> str:
        return "my_agent_id"

    def get_description(self) -> str:
        return "Short description of what agent does"

    def gather_data(self, input1: str, input2: int) -> dict:
        """Gather data for analysis

        Args:
            input1: First input parameter
            input2: Second input parameter

        Returns:
            Dict with all data needed by build_prompt and format_output
        """
        # Read files from self.rp_dir
        # Parse context
        # Return dict

        return {
            "input1": input1,
            "input2": input2,
            "data": "something you read",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build DeepSeek prompt with JSON schema

        Args:
            data: Dict from gather_data()

        Returns:
            Formatted prompt string for DeepSeek
        """
        prompt = f"""Analyze this data and return structured information.

DATA:
{data['input1']}

Return as JSON:

{{
  "field1": "value",
  "field2": <number>,
  "field3": ["list", "of", "items"]
}}

Return ONLY the JSON object, no additional text."""

        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format result for cache

        Args:
            result: Raw JSON from DeepSeek
            data: Original data dict (may have duration_ms)

        Returns:
            JSON string ready for cache
        """
        try:
            # Parse the JSON
            analysis = json.loads(result.strip())

            # Build standardized output
            output = {
                "field1": analysis.get("field1", ""),
                "field2": analysis.get("field2", 0),
                "field3": analysis.get("field3", [])
            }

            # Add duration if tracked
            if "duration_ms" in data:
                output["dur"] = data["duration_ms"]

            return json.dumps(output)

        except json.JSONDecodeError as e:
            if self.log_file:
                log_to_file(self.log_file, f"[{self.get_agent_id()}] JSON parse error: {e}")
            return json.dumps({"error": str(e)})
```

### Step 4: Register in AgentFactory

**File**: `src/automation/agents/agent_factory.py`

Add to the factory registry:

```python
from src.automation.agents.background.my_agent import MyAgentName  # Or immediate

class AgentFactory:
    registry = {
        # Background agents
        "response_analyzer": ResponseAnalyzerAgent,
        # ... existing agents ...
        "my_agent_id": MyAgentName,  # ADD THIS LINE
    }
```

### Step 5: Add to Config

**File**: `state/automation_config.json`

Add agent configuration:

```json
{
  "agents": {
    "background": {
      "response_analyzer": {"enabled": true, "priority": 1},
      ...
      "my_agent_id": {"enabled": true, "priority": 7}
    }
  }
}
```

For immediate agents:
```json
{
  "agents": {
    "immediate": {
      "quick_entity_analysis": {"enabled": true, "timeout_seconds": 5},
      ...
      "my_agent_id": {"enabled": true, "timeout_seconds": 5}
    }
  }
}
```

### Step 6: Update Documentation

**Update**: `AGENT_DOCUMENTATION.md`

Add section under appropriate category:

```markdown
### X. My Agent Name
**Location**: `src/automation/agents/background/my_agent.py`

**What It Does**:
Description of what agent does...

**Pulls From**:
- Input 1
- Input 2
- File X

**Sends To**:
- Output format
- File/cache location

**Purpose**: What problem does it solve?
```

### Step 7: Test

See [Debugging & Testing](#debugging--testing) section below.

---

## REGISTRATION & INTEGRATION

### Complete Integration Checklist

Before considering an agent complete:

- [ ] **File created** in correct location (background or immediate)
- [ ] **Class created** inheriting from BaseAgent
- [ ] **5 methods implemented**:
  - [ ] `get_agent_id()`
  - [ ] `get_description()`
  - [ ] `gather_data()`
  - [ ] `build_prompt()`
  - [ ] `format_output()`
- [ ] **JSON schema defined** in build_prompt()
- [ ] **Registered in AgentFactory** (`agent_factory.py`)
- [ ] **Added to config** (`automation_config.json`)
  - [ ] `enabled: true` (or false if draft)
  - [ ] `priority` set (background agents)
  - [ ] `timeout_seconds` set (immediate agents)
- [ ] **Documentation updated**:
  - [ ] `AGENT_DOCUMENTATION.md` entry
  - [ ] Code docstrings complete
  - [ ] Config documentation
- [ ] **Error handling**:
  - [ ] Handles missing files
  - [ ] Handles JSON parse errors
  - [ ] Logs errors to hook.log
  - [ ] Never raises exceptions
- [ ] **Data flow verified**:
  - [ ] gather_data() reads correct files
  - [ ] build_prompt() includes JSON schema
  - [ ] format_output() returns valid JSON
  - [ ] Results saved to correct location
- [ ] **Caching**:
  - [ ] Results go to `state/agent_analysis.json` (immediate)
  - [ ] Or files updated via FSWriteQueue (background)
  - [ ] Duration tracked if applicable
- [ ] **Testing**:
  - [ ] Manual test with sample data
  - [ ] Verify DeepSeek API call works
  - [ ] Check JSON parsing handles errors
  - [ ] Log file shows execution

---

## REAL CODE EXAMPLES

### Example 1: Response Analyzer (Background)

**File**: `src/automation/agents/background/response_analyzer.py`

See source for complete implementation showing:
- ✅ All 5 methods
- ✅ Complex gather_data (optional parameters)
- ✅ JSON schema with multiple nested objects
- ✅ Comprehensive error handling

### Example 2: Quick Entity Analysis (Immediate)

**File**: `src/automation/agents/immediate/quick_entity_analysis.py`

See source for example showing:
- ✅ Reading from directories
- ✅ File enumeration
- ✅ Tier-based classification
- ✅ New entity detection

### Example 3: Memory Extraction (Immediate)

**File**: `src/automation/agents/immediate/memory_extraction.py`

See source for example showing:
- ✅ Reading multiple memory files
- ✅ Relevance filtering
- ✅ Complex nested JSON
- ✅ Array handling

---

## QUICK REFERENCE TEMPLATE

**Copy and paste this to start a new agent**:

```python
#!/usr/bin/env python3
"""
[AGENT NAME]

[One sentence description]

Part of Phase X.X
Timing: [Before|After] Response N
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.automation.agents.base_agent import BaseAgent
from src.automation.core import log_to_file


class [AgentClassName](BaseAgent):
    """[Human description]"""

    def get_agent_id(self) -> str:
        return "[agent_id_here]"

    def get_description(self) -> str:
        return "[Short description]"

    def gather_data(self, **kwargs) -> dict:
        """Gather data"""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_prompt(self, data: dict) -> str:
        """Build prompt"""
        prompt = f"""[Your prompt here]

Return as JSON:

{{
  "field": "value"
}}

Return ONLY JSON."""
        return prompt

    def format_output(self, result: str, data: dict) -> str:
        """Format output"""
        try:
            analysis = json.loads(result.strip())
            output = {
                "field": analysis.get("field", "")
            }
            if "duration_ms" in data:
                output["dur"] = data["duration_ms"]
            return json.dumps(output)
        except json.JSONDecodeError as e:
            if self.log_file:
                log_to_file(self.log_file, f"[{self.get_agent_id()}] Error: {e}")
            return json.dumps({"error": str(e)})
```

---

## COMMON PATTERNS

### Pattern 1: Reading Entity Cards

```python
def gather_data(self, entity_name: str) -> dict:
    """Read an entity card"""
    entities_dir = self.rp_dir / "entities"
    entity_file = entities_dir / f"{entity_name}.md"

    entity_content = ""
    if entity_file.exists():
        try:
            entity_content = entity_file.read_text(encoding='utf-8')
        except Exception as e:
            if self.log_file:
                log_to_file(self.log_file, f"Error reading {entity_name}: {e}")

    return {"entity_content": entity_content}
```

### Pattern 2: Reading Multiple JSON Files

```python
def gather_data(self, character_name: str) -> dict:
    """Read character memories"""
    memories_dir = self.rp_dir / "memories" / character_name
    memories = []

    if memories_dir.exists():
        for memory_file in memories_dir.glob("*.md"):
            try:
                content = memory_file.read_text(encoding='utf-8')
                memories.append({"name": memory_file.stem, "content": content})
            except Exception as e:
                if self.log_file:
                    log_to_file(self.log_file, f"Error reading memory: {e}")

    return {"memories": memories}
```

### Pattern 3: Directory Scanning

```python
def gather_data(self) -> dict:
    """Get list of available entities"""
    entities_dir = self.rp_dir / "entities"
    available = []

    if entities_dir.exists():
        available = [f.stem for f in entities_dir.glob("*.md")]

    return {"available_entities": available}
```

### Pattern 4: Simple JSON Output

```python
def format_output(self, result: str, data: dict) -> str:
    """Format simple JSON"""
    try:
        analysis = json.loads(result.strip())
        return json.dumps(analysis)  # Pass through
    except json.JSONDecodeError as e:
        return json.dumps({"error": str(e)})
```

### Pattern 5: Complex Nested JSON

```python
def format_output(self, result: str, data: dict) -> str:
    """Format complex nested JSON"""
    try:
        analysis = json.loads(result.strip())

        output = {
            "summary": analysis.get("summary", ""),
            "items": [],
            "meta": {
                "count": len(analysis.get("items", [])),
                "timestamp": data.get("timestamp")
            }
        }

        for item in analysis.get("items", []):
            output["items"].append({
                "id": item.get("id"),
                "title": item.get("title"),
                "score": item.get("score", 0)
            })

        if "duration_ms" in data:
            output["meta"]["dur"] = data["duration_ms"]

        return json.dumps(output)

    except json.JSONDecodeError as e:
        if self.log_file:
            log_to_file(self.log_file, f"[{self.get_agent_id()}] Parse error: {e}")
        return json.dumps({"error": str(e)})
```

---

## DEBUGGING & TESTING

### Manual Agent Testing

**Step 1: Set up test environment**

```python
from pathlib import Path
from src.automation.agents.background.my_agent import MyAgent

rp_dir = Path("/path/to/RP")
log_file = rp_dir / "state" / "hook.log"

agent = MyAgent(rp_dir, log_file)
```

**Step 2: Call execute directly**

```python
result = agent.execute(arg1, arg2, kwarg1=value)
print("Result:", result)
```

**Step 3: Check output**

```python
import json
output = json.loads(result)
print(json.dumps(output, indent=2))
```

### Common Issues

#### Issue: JSON Parse Error

**Symptom**: `"error": "Expecting value: line 1 column 1"`

**Cause**: DeepSeek returned non-JSON text

**Fix**:
1. Check `build_prompt()` - ensure JSON schema in prompt
2. Ensure prompt says "Return ONLY JSON"
3. Add markdown fence stripping to `format_output()`:

```python
# Strip markdown code fences if present
result = result.strip()
if result.startswith("```"):
    result = result.split("```")[1].strip()
    if result.startswith("json"):
        result = result[4:].strip()
```

#### Issue: Missing Required Fields

**Symptom**: Agent output missing fields, None values

**Cause**: DeepSeek didn't provide field or format_output didn't parse

**Fix**:
1. Use `.get()` with defaults in `format_output()`
2. Validate required fields are present
3. Log which fields were missing
4. Return sensible defaults

```python
output = {
    "field": analysis.get("field", "default_value"),
    "score": analysis.get("score", 0),
    "items": analysis.get("items", [])
}
```

#### Issue: File Not Found

**Symptom**: Agent tries to read file that doesn't exist

**Fix**: Always check existence before reading

```python
file_path = self.rp_dir / "somefile.md"
content = ""
if file_path.exists():
    content = file_path.read_text()
else:
    if self.log_file:
        log_to_file(self.log_file, f"File not found: {file_path}")
```

#### Issue: Timeout

**Symptom**: Agent takes too long, gets killed

**Fix**:
1. Check `gather_data()` - is it reading too many files?
2. Check `build_prompt()` - is prompt too long?
3. Increase timeout in config if appropriate
4. Profile to find bottleneck

```python
import time
start = time.perf_counter()
# ... your code ...
elapsed = time.perf_counter() - start
print(f"Took {elapsed:.2f}s")
```

### Checking Logs

Agent execution is logged to `state/hook.log`:

```
[2025-10-16 12:30:45] [response_analyzer] Executing agent
[2025-10-16 12:30:45] [response_analyzer] gather_data completed in 0.01s
[2025-10-16 12:30:45] [response_analyzer] Prompt built: 245 chars
[2025-10-16 12:30:48] [response_analyzer] DeepSeek completed in 2.45s
[2025-10-16 12:30:48] [response_analyzer] format_output completed in 0.02s
[2025-10-16 12:30:48] [response_analyzer] Agent completed in 2.48s
```

### Verifying Cache

After agent runs, check `state/agent_analysis.json`:

```json
{
  "response_analyzer": {
    "scene": {...},
    "chars": {...},
    ...
  },
  "memory_creation": {...},
  ...
}
```

---

## INTEGRATION WITH OTHER SYSTEMS

### How Agents Integrate

**In the Pipeline**:

```
ImmediateAgentsStage
    ├→ AgentCoordinator.run_all_agents()
    │  ├→ ThreadPoolExecutor(max_workers=4)
    │  ├→ Agent 1: execute()
    │  ├→ Agent 2: execute()
    │  ├→ Agent 3: execute()
    │  └→ Agent 4: execute()
    └→ Results cached to state/agent_analysis.json
```

### Agent Dependencies

Agents should be **independent**:
- ✅ Each agent reads files
- ✅ Each agent makes own DeepSeek call
- ✅ Results don't depend on other agents
- ❌ Don't call other agents
- ❌ Don't share state between agents

### Accessing Agent Results

**In PromptBuilder**:

```python
# Load cached agent results
agent_cache = self.rp_dir / "state" / "agent_analysis.json"
if agent_cache.exists():
    with open(agent_cache) as f:
        agent_results = json.load(f)

    # Use results
    entity_analysis = agent_results.get("quick_entity_analysis")
    memory_extraction = agent_results.get("memory_extraction")
```

---

## PERFORMANCE TIPS

### Optimize Gather Data

- Cache results if calling multiple times
- Read only needed files
- Parse efficiently

### Optimize Prompts

- Keep prompts concise
- Only include necessary context
- Use clear, short examples

### Optimize Format Output

- Parse JSON once
- Validate early
- Return immediately on error

### Monitor Performance

- Check hook.log for timing
- Aim for <5 seconds per agent
- Profile slow agents

---

This guide should help you create consistent, well-integrated agents! Refer back to real examples when in doubt.

**Questions?** Check:
1. Real code examples (agents/background, agents/immediate)
2. This guide's patterns section
3. Base agent class documentation
