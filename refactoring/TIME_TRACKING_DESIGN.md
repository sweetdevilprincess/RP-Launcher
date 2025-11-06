# Time Tracking Agent Design

**Date:** 2025-10-30
**Purpose:** Design agent to accurately track time passage, calculate activity durations, and fix date calculation errors
**Status:** ✅ IMPLEMENTED (Two-Stage Approach)

---

## Two-Stage Approach (IMPLEMENTED)

TimeTrackingAgent uses a two-stage system that combines **structured guidance** with **context-aware decisions**:

### Stage 1: Generate Recommendation (Data-Driven)
- Analyzes Claude's response for activities
- Matches activities to `timing_reference.json`
- Calculates estimated duration based on reference data
- Detects modifiers (fast, slow, etc.)
- Flags unknown activities (making out, cuddling, etc.)
- Notes explicit time mentions ("30 minutes later")

**Output:** Recommendation with estimated time and reasoning

### Stage 2: LLM Review & Final Decision (Context-Aware)
- Reviews Stage 1 recommendation
- Considers full scene context (emotional intensity, time hints)
- Handles unknown activities by combining similar reference activities
- Adjusts for context clues ("for hours", "briefly", "all night")
- Makes final decision: ACCEPT or ADJUST
- Provides clear reasoning for decision

**Output:** Final time with reasoning and any adjustments

### Why Two Stages?

**Benefits:**
1. **Guidance + Flexibility:** Reference data ensures consistency, LLM provides context-awareness
2. **Handles Unknown Activities:** LLM estimates by combining similar activities
3. **Context Sensitivity:** Adjusts for scene intensity, emotional context
4. **Audit Trail:** Both recommendation and final decision stored for debugging
5. **Explainable:** Clear reasoning for every time decision

**Example Flow:**
- Claude: "They made out passionately for a while"
- Stage 1: "Unknown activity 'making out' - no reference data"
- Stage 2: "Estimate 20 minutes - combines brief intimacy similar to partial date activity"
- Result: 20 minutes with reasoning

---

## Problem Statement

### Current Issues:

1. **Incorrect "Days Until" Calculations**
   - Example: "Today is Saturday, I work on Tuesday"
   - **WRONG:** Says "3 days" (elapsed days: Sat→Sun→Mon→Tue)
   - **ALSO WRONG:** Says "4 days" (counting both endpoints)
   - **CORRECT:** Should say "2 days" (intermediate days only)

   **Proper Calculation:**
   - Saturday: Today (day 0, **not counted**)
   - Sunday: Day 1
   - Monday: Day 2
   - Tuesday: Work day (**not counted**, this is arrival)
   - **Answer: 2 days**

2. **Root Cause:**
   - LLM uses `(end_date - start_date).days` which gives elapsed days (3)
   - Should use intermediate days: `(end_date - start_date).days - 1` (2)
   - Week restart confusion (counting inclusively vs. exclusively)

3. **No Activity Duration Tracking**
   - Activities like "eating breakfast" have no standard duration
   - Time passage is vague ("a while later", "30 minutes")
   - Modifiers (fast, slow, relaxed) not considered

4. **Free-Form Time Context**
   - Current `time_context` stores LLM-generated text
   - No structured date/time data
   - No accumulation of time across scenes

---

## Date Calculation Logic (Core Fix)

### The "Days Until" Problem

**User Says:** "Today is Saturday, I work on Tuesday. How many days until I work?"

**WRONG Calculation #1 - Elapsed Days:**
```python
from datetime import date

saturday = date(2024, 3, 12)
tuesday = date(2024, 3, 15)

elapsed = (tuesday - saturday).days  # 3 ❌
# Counts: Sat→Sun (1), Sun→Mon (2), Mon→Tue (3)
```

**WRONG Calculation #2 - Counting Both Endpoints:**
```python
inclusive = (tuesday - saturday).days + 1  # 4 ❌
# Counts: Sat, Sun, Mon, Tue
```

**CORRECT Calculation - Intermediate Days:**
```python
def days_until(current_date: date, future_date: date) -> int:
    """Calculate intermediate days between current and future date.

    Does NOT count:
    - Today (current_date)
    - Arrival day (future_date)

    Only counts days in between.
    """
    elapsed = (future_date - current_date).days
    intermediate = elapsed - 1  # Subtract 1 to exclude arrival day
    return max(0, intermediate)  # Minimum 0 (same day or next day)

# Example:
saturday = date(2024, 3, 12)
tuesday = date(2024, 3, 15)
print(days_until(saturday, tuesday))  # 2 ✓

# Edge cases:
print(days_until(saturday, saturday))  # 0 (same day)
sunday = date(2024, 3, 13)
print(days_until(saturday, sunday))  # 0 (next day, no intermediate days)
monday = date(2024, 3, 14)
print(days_until(saturday, monday))  # 1 (Sunday is in between)
```

**Counting Logic:**
- Saturday (today): **Not counted**
- Sunday: Day 1 ✓
- Monday: Day 2 ✓
- Tuesday (arrival): **Not counted**
- **Result: 2 days**

---

### When to Use "Days Until" vs. "Elapsed Days"

**Use "Days Until" (Intermediate Days):**
- "How many days until X?"
- "X happens in Y days"
- "X days before the event"
- User-facing language

**Use "Elapsed Days" (Total Days):**
- "X days have passed since Y"
- "It's been X days since the RP started"
- Internal tracking of total time

**Example:**
- RP starts: Saturday, March 12
- Current: Tuesday, March 15
- **Elapsed:** 3 days (Sat→Sun→Mon→Tue)
- **Days until:** 0 (already Tuesday)
- **Next event (Friday):** 2 days until (Wed, Thu)

---

## Architecture Design

### Option A: Separate TimeTrackingAgent (RECOMMENDED)

**Why Separate:**
- Single Responsibility Principle - ResponseAnalyzerAgent already has many duties
- Time tracking has complex logic (activity parsing, duration calculation, date arithmetic)
- Can run in parallel with ResponseAnalyzerAgent
- Easier to test and maintain

**Agent Type:** Background (N+1) - analyzes Claude's response for activities

**Responsibilities:**
1. Extract activities mentioned in Claude's response
2. Calculate duration based on timing reference data
3. Apply modifiers (fast, slow, relaxed) to durations
4. Update current in-world date/time
5. Calculate elapsed time accurately
6. **Fix "days until" calculations** using intermediate day logic

**Execution Order:**
- Runs concurrently with ResponseAnalyzerAgent
- Both agents update different parts of `scene_context`
- TimeTrackingAgent updates `time_context` section

---

## Data Structures

### 1. Timing Reference Data (`config/timing_reference.json`)

Stores base durations for 90+ activities in minutes.

```json
{
  "activities": {
    "eat": 10,
    "sleep": 480,
    "walk": 10,
    "fight": 8,
    "shower": 15,
    "drive_car": 30,
    "sex": 45,
    "conversation": 20,
    "work_shift": 480,
    "commute": 30,
    "cook": 30,
    "clean": 45,
    "exercise": 60,
    "read": 30,
    "watch_tv": 60,
    "shop": 60,
    "study": 90,
    "meeting": 60,
    "coffee_break": 15,
    "lunch_break": 45,
    "bathroom": 5,
    "get_dressed": 10,
    "makeup": 20,
    "phone_call": 15
  },
  "modifiers": {
    "fast": 0.75,
    "slow": 1.5,
    "relaxed": 1.2,
    "rushed": 0.6,
    "leisurely": 1.8,
    "thorough": 1.4,
    "quick": 0.7,
    "extended": 2.0
  }
}
```

**Storage Location:** `config/timing_reference.json`

**Rationale:**
- Stored alongside other reference data in config folder
- Can be edited without code changes
- JSON format - easy to parse and extend
- Keeps all reference documents in one place

---

### 2. Time State in scene_context (`state/scene_context_{session_id}.json`)

Enhanced `time_context` section with structured data.

**Current Structure (LLM-generated text):**
```json
{
  "time_context": {
    "elapsed": "30 minutes",
    "timestamp": "Tuesday 3:00 PM",
    "day_chapter": "Day 3"
  }
}
```

**New Structure (Calculated Data):**
```json
{
  "time_context": {
    "current_datetime": {
      "year": 2024,
      "month": 3,
      "day": 15,
      "hour": 15,
      "minute": 0,
      "day_of_week": "Tuesday",
      "formatted": "Tuesday, March 15, 2024 3:00 PM"
    },
    "elapsed_this_scene": {
      "minutes": 30,
      "formatted": "30 minutes"
    },
    "total_elapsed": {
      "days": 3,
      "hours": 72,
      "minutes": 4320,
      "formatted": "3 days elapsed since RP start"
    },
    "activities_detected": [
      {"activity": "conversation", "duration": 20, "modifier": null},
      {"activity": "walk", "duration": 10, "modifier": null}
    ],
    "day_chapter": "Day 3",
    "last_updated_message": 42
  }
}
```

**Key Changes:**
1. `current_datetime` - Structured date/time object
2. `elapsed_this_scene` - Calculated from activities (not LLM guess)
3. `total_elapsed` - Cumulative time since RP start (elapsed days)
4. `activities_detected` - Audit trail of what was detected
5. `day_of_week` - Enables correct "days until" calculations

---

### 3. Initial Time Configuration

**Where to Store Starting Date/Time:**

**Option A:** In session.json (RECOMMENDED)
```json
{
  "time_config": {
    "start_datetime": {
      "year": 2024,
      "month": 3,
      "day": 12,
      "hour": 9,
      "minute": 0,
      "day_of_week": "Saturday"
    },
    "auto_track": true
  }
}
```

**Option B:** Detect from first scene
- LLM extracts starting time from first message/response
- Stores in time_context
- Less accurate but no manual config needed

**Recommendation:** Option A with Option B fallback
- User can set starting date explicitly
- More accurate than LLM extraction
- Falls back to Option B if not configured

---

## TimeTrackingAgent Implementation

### Agent Structure

```python
class TimeTrackingAgent(BaseAgent):
    """Track time passage and update in-world date/time."""

    def get_agent_id(self) -> str:
        return "time_tracking"

    def execute(
        self,
        user_message: str,
        message_number: int,
        claude_response: str,
        **kwargs
    ) -> str:
        """Analyze response for activities and update time."""

        # Step 1: Load timing reference data
        timing_ref = self._load_timing_reference()

        # Step 2: Get current time state from session
        current_time = self._get_current_time()

        # Step 3: Call LLM to extract activities from response
        activities = self._extract_activities(claude_response, timing_ref)

        # Step 4: Calculate elapsed time
        elapsed = self._calculate_elapsed_time(activities, timing_ref)

        # Step 5: Update current datetime
        new_datetime = self._add_time(current_time, elapsed)

        # Step 6: Calculate total elapsed since RP start
        total_elapsed = self._calculate_total_elapsed(new_datetime)

        # Step 7: Update session state
        self._update_time_context(new_datetime, elapsed, activities, total_elapsed)

        # Step 8: Return summary
        return f"Time advanced {elapsed['formatted']} to {new_datetime['formatted']}"
```

---

### Key Helper Methods

#### 1. Days Until Calculation (CORE FIX)

```python
def _days_until(self, current_date: dict, future_date: dict) -> int:
    """Calculate intermediate days between current and future date.

    Does NOT count:
    - Today (current_date) - day 0
    - Arrival day (future_date) - not counted

    Only counts days in between.

    Example:
        Saturday to Tuesday = 2 days
        - Saturday: today (not counted)
        - Sunday: 1
        - Monday: 2
        - Tuesday: arrival (not counted)

    Args:
        current_date: Dict with year, month, day
        future_date: Dict with year, month, day

    Returns:
        Number of intermediate days (0 if same day or next day)
    """
    from datetime import date

    current = date(
        current_date['year'],
        current_date['month'],
        current_date['day']
    )
    future = date(
        future_date['year'],
        future_date['month'],
        future_date['day']
    )

    elapsed = (future - current).days
    intermediate = elapsed - 1  # Subtract 1 to exclude arrival day

    return max(0, intermediate)  # Minimum 0
```

#### 2. Add Time to DateTime

```python
def _add_time(self, current_datetime: dict, elapsed_minutes: int) -> dict:
    """Add time to current datetime and return new datetime.

    Args:
        current_datetime: Dict with year, month, day, hour, minute
        elapsed_minutes: Minutes to add

    Returns:
        New datetime dict with updated values
    """
    from datetime import datetime, timedelta

    # Convert dict to datetime object
    dt = datetime(
        year=current_datetime['year'],
        month=current_datetime['month'],
        day=current_datetime['day'],
        hour=current_datetime['hour'],
        minute=current_datetime['minute']
    )

    # Add elapsed time
    new_dt = dt + timedelta(minutes=elapsed_minutes)

    # Convert back to dict
    return {
        'year': new_dt.year,
        'month': new_dt.month,
        'day': new_dt.day,
        'hour': new_dt.hour,
        'minute': new_dt.minute,
        'day_of_week': new_dt.strftime('%A'),  # "Tuesday"
        'formatted': new_dt.strftime('%A, %B %d, %Y %I:%M %p')
    }
```

#### 3. Calculate Total Elapsed (Since RP Start)

```python
def _calculate_total_elapsed(self, current_datetime: dict) -> dict:
    """Calculate total elapsed time since RP start.

    This is ELAPSED days (different from "days until").

    Args:
        current_datetime: Current date/time

    Returns:
        Dict with days, hours, minutes, formatted
    """
    from datetime import datetime

    # Get RP start time from config
    start_config = self._get_start_datetime()

    current = datetime(
        current_datetime['year'],
        current_datetime['month'],
        current_datetime['day'],
        current_datetime['hour'],
        current_datetime['minute']
    )

    start = datetime(
        start_config['year'],
        start_config['month'],
        start_config['day'],
        start_config['hour'],
        start_config['minute']
    )

    delta = current - start

    total_minutes = int(delta.total_seconds() / 60)
    total_hours = total_minutes // 60
    total_days = total_hours // 24

    return {
        'days': total_days,
        'hours': total_hours,
        'minutes': total_minutes,
        'formatted': f"{total_days} days, {total_hours % 24} hours elapsed since RP start"
    }
```

---

### LLM Prompt for Activity Extraction

```text
Analyze this roleplay response and identify all activities that occurred.

CLAUDE'S RESPONSE:
{claude_response}

AVAILABLE ACTIVITIES (with base durations in minutes):
{json.dumps(timing_reference['activities'], indent=2)}

AVAILABLE MODIFIERS:
{json.dumps(timing_reference['modifiers'], indent=2)}

Extract:
1. **Activities Performed:**
   - Identify activities from the response
   - Match to available activities (or closest equivalent)
   - Detect modifiers (fast, slow, relaxed, etc.)
   - If activity not in list, estimate duration in minutes

2. **Explicit Time References:**
   - If response mentions "30 minutes later", "2 hours passed", etc., note exact time
   - If mentions specific time ("3:00 PM"), note that
   - If mentions day change ("next morning"), note that

3. **Time Passage Hints:**
   - Scene transitions ("later that day")
   - Implicit time passage ("after dinner")

Respond with JSON ONLY:
{
  "activities": [
    {
      "activity": "conversation",
      "base_duration": 20,
      "modifier": null,
      "modified_duration": 20,
      "confidence": "high"
    },
    {
      "activity": "walk",
      "base_duration": 10,
      "modifier": "slow",
      "modified_duration": 15,
      "confidence": "high"
    }
  ],
  "explicit_time": {
    "mentioned": true,
    "value": "30 minutes",
    "type": "duration"
  },
  "time_hints": {
    "scene_transition": false,
    "day_change": false,
    "time_of_day": "afternoon"
  },
  "estimated_total_minutes": 35
}

IMPORTANT:
- Only include activities that actually happened in THIS response
- Use null for modifier if no modifier detected
- confidence: high (clear), medium (implied), low (uncertain)
- If explicit time mentioned, use that as authoritative
```

---

## Providing Context to Claude

### Add Time Info to Context Builder

TimeTrackingAgent should provide accurate time information to Claude's context so Claude can reference correct dates.

**Add to context_builder.py:**

```python
def _build_time_context(self, rp_dir: Path) -> str:
    """Build time context for Claude's prompt.

    Returns formatted string with current date/time and next events.
    """
    scene_context = self.session_state_service.get_scene_context(rp_dir)
    time_ctx = scene_context.get('time_context', {})

    if not time_ctx:
        return ""

    current_dt = time_ctx.get('current_datetime', {})
    if not current_dt:
        return ""

    # Format current time
    formatted = current_dt.get('formatted', 'Unknown')
    day_of_week = current_dt.get('day_of_week', '')

    # Calculate days to common events (if character schedules exist)
    # This would use _days_until() logic

    context = f"""
## Current Time
**Date/Time:** {formatted}
**Day:** {day_of_week}
"""

    return context
```

**Example Context for Claude:**
```
## Current Time
**Date/Time:** Tuesday, March 15, 2024 3:00 PM
**Day:** Tuesday

## Character Schedules
- Lilith's next work shift: Thursday (1 day from now)
- Weekly team meeting: Friday (2 days from now)
```

**Benefit:**
- Claude sees accurate date/time
- Claude can correctly say "I work in 2 days" (when it's Tuesday and work is Friday)
- Prevents date calculation errors in Claude's responses

---

## Integration with Existing System

### 1. Session State Service Updates

**No changes needed!** TimeTrackingAgent writes to same `scene_context` file as ResponseAnalyzerAgent.

**File:** `state/scene_context_{session_id}.json`

Both agents update different sections:
- ResponseAnalyzerAgent updates: chapter, location, characters_in_scene, scene_analysis
- TimeTrackingAgent updates: time_context

Concurrent writes are safe because:
- Each agent reads current state
- Updates only their section
- Atomic file writes prevent corruption

**Potential Race Condition:**
If both agents write simultaneously, one update may be lost.

**Solutions:**
1. **Accept occasional loss** (simple, good enough for Phase 1)
2. **Sequential execution** (ResponseAnalyzer first, then TimeTracking)
3. **File locking** (complex, overkill)

**Recommendation:** Solution #1 for now, Solution #2 if issues arise.

---

### 2. Background Agent Strategy Updates

Add TimeTrackingAgent to available agents:

```python
# In background_agent_strategy.py
from ..implementations import ResponseAnalyzerAgent, TimeTrackingAgent

available_agents = {
    "response_analyzer": ResponseAnalyzerAgent,
    "time_tracking": TimeTrackingAgent,  # NEW
    # ... other agents
}
```

No other changes needed - uses same execution pattern as ResponseAnalyzerAgent.

---

### 3. Configuration Updates

**Enable TimeTrackingAgent in automation config:**

```json
{
  "background_agents": {
    "response_analyzer": true,
    "time_tracking": true,
    "memory_creation": false
  }
}
```

**Add timing reference data:**

Create `config/timing_reference.json` with activity durations.

**Set starting time (optional):**

In `session.json`:
```json
{
  "time_config": {
    "start_datetime": {
      "year": 2024,
      "month": 3,
      "day": 12,
      "hour": 9,
      "minute": 0,
      "day_of_week": "Saturday"
    }
  }
}
```

---

## Edge Cases & Handling

### 1. No Activities Detected
**Scenario:** Pure dialogue with no physical activities

**Solution:**
- Default to minimal passage (5-10 minutes for conversation)
- Or use ResponseAnalyzerAgent's word count (100 words ≈ 1 minute of dialogue)

### 2. Multiple Activities in Parallel
**Scenario:** "While eating breakfast, Alice and Bob discussed the plan" (eating + conversation)

**Solution:**
- Take max duration (not sum)
- Example: eat (10 min) + conversation (20 min) = 20 minutes (not 30)
- LLM detects parallelism: `"parallel": true` in activity object

### 3. Large Time Skips
**Scenario:** "Three days later..." or "The next morning..."

**Solution:**
- LLM detects explicit time skip in `explicit_time` section
- Use explicit time as authoritative (override activity calculations)
- Example: explicit_time.value = "3 days" → add 4320 minutes

### 4. Backward Time References
**Scenario:** Flashback scenes or references to past events

**Solution:**
- Detect flashback keywords ("remembered", "flashback", "three days ago")
- Don't update current_datetime for flashback content
- Note in time_context: `"flashback": true`

### 5. Unknown Activities
**Scenario:** Activity not in timing_reference.json

**Solution:**
- LLM estimates duration based on similar activities
- Example: "praying" not in list → estimate 15 minutes (similar to meditation)
- Confidence: "low"

### 6. Ambiguous Modifiers
**Scenario:** "quickly ate breakfast"

**Solution:**
- Map natural language to modifiers
- "quickly" → "fast" (0.75x)
- "hurried" → "rushed" (0.6x)
- "took their time" → "leisurely" (1.8x)

---

## Testing Strategy

### Unit Tests

1. **"Days Until" Calculation (CRITICAL):**
   ```python
   def test_days_until():
       saturday = {'year': 2024, 'month': 3, 'day': 12}
       tuesday = {'year': 2024, 'month': 3, 'day': 15}

       assert days_until(saturday, tuesday) == 2  # Sun, Mon

       # Edge cases
       assert days_until(saturday, saturday) == 0  # same day
       sunday = {'year': 2024, 'month': 3, 'day': 13}
       assert days_until(saturday, sunday) == 0  # next day, no intermediate
       monday = {'year': 2024, 'month': 3, 'day': 14}
       assert days_until(saturday, monday) == 1  # Sunday in between
   ```

2. **Date Arithmetic:**
   - Test _add_time() with various durations
   - Test month boundaries, year boundaries
   - Test leap years

3. **Activity Duration:**
   - Test modifier application (fast, slow, relaxed)
   - Test parallel activities (take max, not sum)
   - Test unknown activity estimation

4. **LLM Response Parsing:**
   - Test activity extraction from sample responses
   - Test explicit time detection ("30 minutes later")
   - Test edge cases (flashbacks, no activities)

### Integration Tests

1. **Concurrent Agent Execution:**
   - Run ResponseAnalyzer + TimeTracking in parallel
   - Verify both updates appear in scene_context
   - Check for race conditions

2. **Timeline Branching:**
   - Create branch, verify time_context copied correctly
   - Advance time in branch, verify main timeline unaffected

### Manual Tests

1. **Real RP Scenario:**
   - "Alice woke up, showered, ate breakfast, and drove to work"
   - Expected: ~85 minutes (wake: 10, shower: 15, eat: 10, drive: 30, buffer: 20)
   - Verify calculated time matches expectation

2. **"Days Until" Scenario:**
   - Start: Saturday 9:00 AM
   - User: "Lilith works on Tuesday"
   - Verify Claude says "2 days" (not 3, not 4)

3. **Date Progression:**
   - Start: Saturday 9:00 AM
   - Activity: Work shift (8 hours) + sleep (8 hours) + repeat 3x
   - Expected: Tuesday 9:00 AM (verify day_of_week correct)

---

## Implementation Checklist

### Phase 1: Core Functionality
- [ ] Create `config/timing_reference.json` with 90+ activities
- [ ] Implement TimeTrackingAgent class (inherit from BaseAgent)
- [ ] Implement _load_timing_reference() helper
- [ ] Implement _get_current_time() from session state
- [ ] Implement _extract_activities() with LLM call
- [ ] Implement _calculate_elapsed_time() with modifiers
- [ ] **Implement _days_until() with CORRECT intermediate day logic**
- [ ] Implement _add_time() with datetime arithmetic
- [ ] Implement _calculate_total_elapsed() for RP start tracking
- [ ] Implement _update_time_context() to write to session state
- [ ] Add TimeTrackingAgent to implementations/__init__.py
- [ ] Add TimeTrackingAgent to background_agent_strategy.py
- [ ] **Write unit tests for _days_until() calculation**
- [ ] Test with sample RP scenario

### Phase 2: Edge Cases
- [ ] Handle parallel activities (take max duration)
- [ ] Handle explicit time skips ("3 days later")
- [ ] Handle flashbacks (don't update current time)
- [ ] Handle unknown activities (LLM estimation)
- [ ] Add unit tests for edge cases

### Phase 3: Context Integration
- [ ] Add time context to Claude's prompt (context_builder.py)
- [ ] Show current date/time
- [ ] Calculate "days until" for scheduled events
- [ ] Test that Claude uses correct dates in responses

### Phase 4: Enhancements
- [ ] Add confidence scoring for activity detection
- [ ] Add audit log of all time updates (debugging)
- [ ] Add time_context history (last N updates)
- [ ] Consider sequential execution to prevent race conditions

---

## Open Questions

1. **Should we track time per character?**
   - Different characters may experience different time (split party)
   - For now: Single timeline (all characters share same time)
   - Future: Per-character time tracking for complex scenarios

2. **How to handle time compression in narrative?**
   - Example: "They spent the whole day exploring" → 12 hours or summary?
   - Solution: Detect compression hints, use explicit time

3. **Should we expose time tracking to Claude's context?**
   - Add to context_builder: "Current time: Tuesday 3:00 PM"
   - Helps Claude maintain consistency
   - **Recommendation: YES, add to context (Phase 3)**

4. **How granular should activity detection be?**
   - Current: Named activities (eat, sleep, walk)
   - Alternative: Generic duration estimation for any action
   - Recommendation: Start with named activities, expand as needed

---

## Priority Assessment

**Tier:** TIER 1 - CORE AGENT

**Why Core:**
- **Fixes actual bug** (incorrect "days until" calculations)
- Directly impacts narrative consistency
- User explicitly requested this feature
- Foundation for other time-based features (schedules, appointments, deadlines)

**Dependencies:**
- ✅ BaseAgent (already implemented)
- ✅ SessionStateService (already implemented)
- ✅ Background agent execution (already implemented)
- ⚠️ timing_reference.json (need to create)

**Blockers:** NONE - Ready to implement after creating timing reference data

**Implementation Priority:** HIGH - Implement after ResponseAnalyzerAgent, before MemoryCreationAgent

**Rationale:**
- ResponseAnalyzerAgent provides scene context
- TimeTrackingAgent provides temporal context with CORRECT date calculations
- MemoryCreationAgent uses both for accurate memory timestamps

---

## Recommended Implementation Order

### Updated Agent Priority:
1. ✅ **ResponseAnalyzerAgent** - COMPLETE
2. **TimeTrackingAgent** - START HERE (fixes "days until" calculation bug)
3. **MemoryCreationAgent** - After time tracking (needs accurate timestamps)
4. **RelationshipAnalysisAgent** - After memory creation

**Why this order:**
- TimeTracking fixes the "Saturday to Tuesday = 3 days" bug
- Memories need accurate timestamps from TimeTracking
- Relationships need memories for context

---

**Status:** ✅ IMPLEMENTATION COMPLETE
**Implementation Date:** 2025-10-30

**Files Created:**
- ✅ `config/timing_reference.json` - Activity reference data (90+ activities, 16 modifiers)
- ✅ `src/automation/agents/implementations/time_tracking_agent.py` - Two-stage TimeTrackingAgent (~700 lines)

**Files Modified:**
- ✅ `src/automation/agents/implementations/__init__.py` - Added TimeTrackingAgent export
- ✅ `src/automation/agents/background_agent_strategy.py` - Added TimeTrackingAgent to available agents

**Next Actions:**
1. Enable `time_tracking` agent in automation config
2. Test with sample RP scenario
3. Verify "Saturday to Tuesday = 2 days" calculation is correct
4. Proceed to implement MemoryCreationAgent (needs accurate timestamps from TimeTracking)
