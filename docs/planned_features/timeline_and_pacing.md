# Timeline & Pacing Management

This document outlines features for managing story timeline, maintaining continuity, and ensuring good pacing through automatic scene analysis and tension monitoring.

---

## 1. Timeline & Continuity Tracker

### Problem Statement

Current timestamp system in `current_state.md` isn't sufficient. Time inconsistencies occur (characters at two places at once, "yesterday was Tuesday, today is Monday", time jumps without explanation). The RP needs active timeline management beyond simple timestamps.

### Proposed Solution

Implement an intelligent timeline system that:
- Tracks in-universe time separately from real-world progression
- Detects temporal inconsistencies
- Maintains calendar of events
- Reminds Claude of time context
- Handles multiple timelines (flashbacks, parallel stories)

### Implementation

#### Core Data Structures

```python
# src/timeline_tracker.py

class TimelineEvent:
    """A single event on the timeline"""

    def __init__(self, event_id, description, timestamp, duration=None):
        self.id = event_id
        self.description = description
        self.timestamp = timestamp  # datetime or string like "Tuesday morning"
        self.duration = duration  # timedelta or string like "2 hours"
        self.chapter = None
        self.response = None
        self.participants = []  # Characters involved
        self.location = None
        self.tags = []  # morning, evening, flashback, etc.
        self.certainty = 1.0  # 0-1, how certain we are about this time

class Timeline:
    """Main timeline management system"""

    def __init__(self, rp_dir):
        self.timeline_file = rp_dir / "state" / "timeline.json"
        self.events = []  # Chronologically sorted events
        self.current_time = None  # Current in-universe time
        self.time_references = []  # All extracted time references
        self.story_start_time = None  # When story began (in-universe)
        self.calendars = {}  # Support multiple calendar systems

        self._load()
```

#### Time Extraction

```python
def extract_time_from_response(self, response_text):
    """Extract time references from response using DeepSeek"""
    prompt = f"""Extract all time references from this text:

Text: {response_text}

Find:
1. Absolute times: "3pm", "Monday morning", "July 15th 2024"
2. Relative times: "the next day", "two hours later", "last week"
3. Implicit times: "after breakfast", "before sunset", "at dawn"
4. Duration: "for three hours", "all night", "briefly"

For each reference, provide:
- Type: absolute/relative/implicit
- Value: the time/duration
- Context: surrounding text
- Certainty: 0-1 (how certain this is a time reference)

Format as JSON.
"""

    extracted = self._call_deepseek(prompt)

    # Parse and create time references
    time_refs = []
    for ref in extracted:
        time_refs.append({
            "type": ref["type"],
            "value": ref["value"],
            "context": ref["context"],
            "certainty": ref["certainty"],
            "raw_text": ref.get("raw_text", "")
        })

    return time_refs

def parse_time_to_absolute(self, time_ref, context):
    """Convert relative/implicit time to absolute time"""
    if time_ref["type"] == "absolute":
        # Already absolute
        return self._parse_absolute_time(time_ref["value"])

    elif time_ref["type"] == "relative":
        # Calculate from current time
        if not self.current_time:
            return None

        # Parse relative expressions
        if "next day" in time_ref["value"].lower():
            return self.current_time + timedelta(days=1)
        elif "hours later" in time_ref["value"].lower():
            hours = self._extract_number(time_ref["value"])
            return self.current_time + timedelta(hours=hours)
        # ... more relative time parsing

    elif time_ref["type"] == "implicit":
        # Guess based on context
        if "after breakfast" in time_ref["value"].lower():
            # Assume breakfast is ~9am
            return self._set_time_of_day(self.current_time, hour=9)
        elif "before sunset" in time_ref["value"].lower():
            # Assume sunset is ~7pm
            return self._set_time_of_day(self.current_time, hour=19)
        # ... more implicit time parsing

    return None
```

#### Inconsistency Detection

```python
def detect_time_inconsistencies(self, new_event):
    """Check if new event creates timeline inconsistencies"""
    inconsistencies = []

    # Check 1: Time going backwards (not flashback)
    if new_event.timestamp < self.current_time:
        if "flashback" not in new_event.tags:
            inconsistencies.append({
                "type": "backwards_time",
                "event": new_event,
                "current_time": self.current_time,
                "severity": "major",
                "message": f"Time went backwards: current is {self.current_time}, "
                          f"event is {new_event.timestamp}"
            })

    # Check 2: Character in multiple places at once
    for existing in self.events:
        if self._events_overlap(new_event, existing):
            # Check if same character in both
            common_chars = set(new_event.participants) & set(existing.participants)
            if common_chars:
                if new_event.location != existing.location:
                    inconsistencies.append({
                        "type": "simultaneous_locations",
                        "event_a": new_event,
                        "event_b": existing,
                        "characters": common_chars,
                        "severity": "major",
                        "message": f"{', '.join(common_chars)} can't be in "
                                  f"{new_event.location} and {existing.location} "
                                  f"at the same time"
                    })

    # Check 3: Impossible durations
    if new_event.duration:
        if new_event.duration > timedelta(days=1):
            inconsistencies.append({
                "type": "impossible_duration",
                "event": new_event,
                "severity": "moderate",
                "message": f"Event duration ({new_event.duration}) seems unusually long"
            })

    # Check 4: Skipped time without explanation
    if self.current_time and new_event.timestamp:
        time_gap = (new_event.timestamp - self.current_time).total_seconds()
        if time_gap > 86400:  # More than 24 hours
            inconsistencies.append({
                "type": "large_time_jump",
                "gap": timedelta(seconds=time_gap),
                "severity": "minor",
                "message": f"Large time jump: {timedelta(seconds=time_gap)} passed"
            })

    return inconsistencies

def _events_overlap(self, event_a, event_b):
    """Check if two events occur at the same time"""
    if not (event_a.timestamp and event_b.timestamp):
        return False

    a_end = event_a.timestamp + (event_a.duration or timedelta(0))
    b_end = event_b.timestamp + (event_b.duration or timedelta(0))

    # Check for overlap
    return (event_a.timestamp <= b_end and event_b.timestamp <= a_end)
```

#### Timeline Context for Prompts

```python
def generate_timeline_context(self):
    """Generate timeline context for Claude"""
    context = ["⏰ TIMELINE CONTEXT:\n"]

    # Current time
    if self.current_time:
        context.append(f"**Current in-universe time**: {self._format_time(self.current_time)}")

        # Time since story start
        if self.story_start_time:
            elapsed = self.current_time - self.story_start_time
            context.append(f"**Time since story began**: {self._format_duration(elapsed)}")

    else:
        context.append("**Current time**: Not yet established")

    context.append("")

    # Recent events (last 24 hours in-universe)
    recent = self._get_recent_events(hours=24)
    if recent:
        context.append("**Recent events** (last 24 hours in-universe):")
        for event in recent:
            time_str = self._format_time(event.timestamp)
            context.append(f"  - {time_str}: {event.description}")
            if event.location:
                context.append(f"    at {event.location}")
        context.append("")

    # Upcoming events (scheduled/planned)
    upcoming = self._get_upcoming_events()
    if upcoming:
        context.append("**Upcoming events**:")
        for event in upcoming:
            time_str = self._format_time(event.timestamp)
            context.append(f"  - {time_str}: {event.description}")
        context.append("")

    # Time reminders
    reminders = self._generate_time_reminders()
    if reminders:
        context.append("**Time reminders**:")
        for reminder in reminders:
            context.append(f"  - {reminder}")
        context.append("")

    return "\n".join(context)

def _generate_time_reminders(self):
    """Generate reminders about time"""
    reminders = []

    # Check time of day
    if self.current_time:
        hour = self.current_time.hour
        if 22 <= hour or hour < 6:
            reminders.append("It's late night/early morning - most people would be sleeping")
        elif 6 <= hour < 9:
            reminders.append("It's morning - people getting ready for day")
        elif 12 <= hour < 13:
            reminders.append("It's around lunch time")
        elif 18 <= hour < 21:
            reminders.append("It's evening - people finishing work/dinner time")

        # Check day of week
        if self.current_time.weekday() < 5:  # Monday-Friday
            if 9 <= hour < 17:
                reminders.append("It's a weekday during business hours")
        else:  # Weekend
            reminders.append("It's the weekend")

    return reminders

def suggest_time_advancement(self):
    """Suggest when to advance time"""
    # If scene has been running for many responses without time passing
    if self.current_time:
        responses_since_time_change = self._get_responses_since_time_change()

        if responses_since_time_change > 10:
            return f"⏰ Time hasn't advanced in {responses_since_time_change} responses. " \
                   f"Consider advancing to next significant moment."

    return None
```

#### Automatic Timeline Updates

```python
def auto_update_timeline(self, response_text, chapter, response_num):
    """Automatically update timeline from response"""

    # Extract time references
    time_refs = self.extract_time_from_response(response_text)

    if not time_refs:
        return  # No time info in this response

    # Parse to absolute times
    new_events = []
    for ref in time_refs:
        absolute_time = self.parse_time_to_absolute(ref, response_text)

        if absolute_time:
            # Create event
            event = TimelineEvent(
                event_id=f"event_{int(time.time())}_{random.randint(1000,9999)}",
                description=ref["context"][:100],
                timestamp=absolute_time
            )
            event.chapter = chapter
            event.response = response_num
            event.certainty = ref["certainty"]

            # Extract participants and location
            event.participants = self._extract_participants(ref["context"])
            event.location = self._extract_location(ref["context"])

            new_events.append(event)

    # Check for inconsistencies
    all_inconsistencies = []
    for event in new_events:
        inconsistencies = self.detect_time_inconsistencies(event)
        all_inconsistencies.extend(inconsistencies)

    # If major inconsistencies, prompt user
    if all_inconsistencies:
        self._handle_inconsistencies(all_inconsistencies)

    # Add events to timeline
    for event in new_events:
        self.add_event(event)

    # Update current time
    if new_events:
        # Set current time to most recent event
        latest = max(new_events, key=lambda e: e.timestamp)
        self.current_time = latest.timestamp

    self._save()

def _handle_inconsistencies(self, inconsistencies):
    """Handle detected inconsistencies"""
    major = [i for i in inconsistencies if i["severity"] == "major"]

    if major:
        print("\n⚠️ TIMELINE INCONSISTENCY DETECTED:\n")
        for inc in major:
            print(f"  - {inc['message']}")

        print("\nOptions:")
        print("  [1] Accept (maybe this is intentional)")
        print("  [2] Edit response to fix inconsistency")
        print("  [3] Mark as flashback/special case")

        choice = input("\nChoice (1/2/3): ").strip()

        if choice == "2":
            return "needs_edit"
        elif choice == "3":
            # Mark events as flashback
            for inc in major:
                if "event" in inc:
                    inc["event"].tags.append("flashback")
```

#### Calendar System

```python
class Calendar:
    """Support for different calendar systems"""

    def __init__(self, calendar_type="gregorian"):
        self.calendar_type = calendar_type
        self.months = []
        self.days_per_month = []
        self.special_days = {}  # Holidays, events

    @classmethod
    def gregorian(cls):
        """Standard Earth calendar"""
        cal = cls("gregorian")
        cal.months = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
        cal.days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return cal

    @classmethod
    def custom(cls, name, months, days_per_month):
        """Custom fantasy/sci-fi calendar"""
        cal = cls(name)
        cal.months = months
        cal.days_per_month = days_per_month
        return cal

# Example custom calendar for fantasy RP:
fantasy_calendar = Calendar.custom(
    "Aetherian Calendar",
    months=["Firewane", "Frostmoon", "Greentide", "Harvestfall"],
    days_per_month=[90, 90, 90, 95]  # Year = 365 days
)
```

### Configuration

```yaml
timeline_tracking:
  enabled: true

  # Time extraction
  extract_every_response: true
  use_deepseek_for_extraction: true

  # Inconsistency detection
  detect_inconsistencies: true
  auto_flag_major: true
  auto_flag_moderate: false

  # Timeline context
  inject_timeline_context: true
  show_recent_events_hours: 24
  show_upcoming_events: true

  # Calendar
  calendar_system: "gregorian"  # or "custom"
  custom_calendar_file: null

  # Time reminders
  remind_time_of_day: true
  remind_day_of_week: true
  suggest_time_advancement: true
  suggest_after_n_responses: 10
```

### User Commands

```bash
/timeline                      # Show current timeline
/timeline events              # List all events
/timeline recent              # Show recent events
/timeline upcoming            # Show upcoming events
/timeline set "Monday 3pm"    # Manually set current time
/timeline add "Dinner at 7pm" # Add scheduled event
/timeline visualize           # Show visual timeline
```

### Timeline Visualization

```python
def visualize_timeline(self, format="ascii"):
    """Generate visual timeline"""

    if format == "ascii":
        # ASCII timeline for terminal
        print("\n" + "="*80)
        print("STORY TIMELINE")
        print("="*80 + "\n")

        # Group events by day
        events_by_day = {}
        for event in self.events:
            day_key = event.timestamp.date() if hasattr(event.timestamp, 'date') else "unknown"
            if day_key not in events_by_day:
                events_by_day[day_key] = []
            events_by_day[day_key].append(event)

        # Print each day
        for day, events in sorted(events_by_day.items()):
            print(f"📅 {day}")
            print("-" * 80)
            for event in sorted(events, key=lambda e: e.timestamp):
                time_str = event.timestamp.strftime("%I:%M %p")
                print(f"  {time_str} - {event.description}")
                if event.participants:
                    print(f"           {', '.join(event.participants)}")
            print()

    elif format == "html":
        # Generate HTML timeline (can open in browser)
        self._generate_html_timeline()
```

### Benefits

- **Consistency**: No more time contradictions
- **Awareness**: Claude always knows current time
- **Planning**: Track scheduled events
- **Debugging**: See when events happened
- **Immersion**: Better temporal coherence

---

## 2. Automatic Scene Analyzer

### Problem Statement

Scenes sometimes get stale - too many dialogue scenes in a row, or all action with no breathing room. Currently requires manual OOC comments like "This is stale. Stuff should be happening." Need automatic detection and gentle nudges toward variety.

### Proposed Solution

Implement automatic scene analysis that:
- Classifies each scene by type (dialogue, action, introspection, etc.)
- Tracks scene variety over time
- Detects when scenes are getting repetitive
- Suggests scene variety to maintain engagement
- Analyzes pacing and emotional beats

### Implementation

#### Scene Classification

```python
# src/scene_analyzer.py

class SceneAnalyzer:
    """Analyze RP scenes for type, pacing, and variety"""

    def __init__(self):
        self.scene_types = {
            "dialogue": "Character conversations, discussions",
            "action": "Physical action, combat, chase scenes",
            "introspection": "Internal thoughts, character reflection",
            "description": "Setting/atmosphere description",
            "transition": "Moving between scenes or locations",
            "exposition": "Information delivery, explanation",
            "emotional": "Emotional beats, character development",
            "romantic": "Romantic/intimate scenes",
            "conflict": "Arguments, tension, disagreements",
            "humor": "Comedy, jokes, banter",
            "mystery": "Clues, investigation, secrets",
            "worldbuilding": "Lore, history, magic system explanation"
        }

    def analyze_scene(self, response_text):
        """Classify scene type and extract metrics"""

        prompt = f"""Analyze this RP scene:

{response_text}

Provide analysis:
1. **Primary scene type**: Choose from: {', '.join(self.scene_types.keys())}
2. **Secondary scene types**: Any other types present (if applicable)
3. **Pacing**: fast/medium/slow - how quickly is the scene moving?
4. **Tension level**: 1-10 - how much tension/conflict/stakes?
5. **Emotional intensity**: 1-10 - how emotionally charged?
6. **Estimated duration**: How much in-universe time does this cover?
7. **Major beats**: What are the 2-3 most important moments?
8. **Character focus**: Which characters get the most focus?

Format as JSON.
"""

        analysis = self._call_deepseek(prompt)

        return {
            "primary_type": analysis["primary_scene_type"],
            "secondary_types": analysis.get("secondary_scene_types", []),
            "pacing": analysis["pacing"],
            "tension": analysis["tension_level"],
            "emotional_intensity": analysis["emotional_intensity"],
            "duration": analysis.get("estimated_duration"),
            "beats": analysis.get("major_beats", []),
            "character_focus": analysis.get("character_focus", [])
        }
```

#### Stagnation Detection

```python
def detect_scene_stagnation(self, recent_scenes, lookback=5):
    """Check if scenes are getting stale"""

    if len(recent_scenes) < lookback:
        return {"stagnant": False}

    # Get last N scenes
    last_n = recent_scenes[-lookback:]

    # Check if all same type
    primary_types = [s["primary_type"] for s in last_n]

    # Count unique types
    unique_types = len(set(primary_types))

    if unique_types == 1:
        # All same type - definitely stagnant!
        return {
            "stagnant": True,
            "type": primary_types[0],
            "count": len(primary_types),
            "severity": "high",
            "suggestion": self._suggest_scene_variety(primary_types[0])
        }

    elif unique_types == 2 and len(primary_types) >= 8:
        # Only 2 types over 8+ scenes - moderately stagnant
        return {
            "stagnant": True,
            "types": list(set(primary_types)),
            "count": len(primary_types),
            "severity": "moderate",
            "suggestion": "Consider adding more scene variety"
        }

    # Check pacing stagnation
    pacing_values = [s["pacing"] for s in last_n]
    if len(set(pacing_values)) == 1:
        return {
            "stagnant": True,
            "reason": "pacing",
            "pacing": pacing_values[0],
            "severity": "moderate",
            "suggestion": f"Pacing has been consistently {pacing_values[0]} - consider variation"
        }

    return {"stagnant": False}

def _suggest_scene_variety(self, current_type):
    """Suggest complementary scene type"""
    suggestions = {
        "dialogue": ["action", "description", "introspection"],
        "action": ["emotional", "dialogue", "introspection"],
        "introspection": ["dialogue", "action", "worldbuilding"],
        "description": ["action", "dialogue", "conflict"],
        "exposition": ["action", "dialogue", "emotional"],
        "emotional": ["humor", "action", "description"],
        "romantic": ["humor", "conflict", "action"],
        "conflict": ["emotional", "introspection", "humor"]
    }

    options = suggestions.get(current_type, ["dialogue", "action"])
    return f"Consider transitioning to: {', '.join(options)}"
```

#### Scene History Tracking

```python
# src/scene_history.py

class SceneHistory:
    """Track scene history and analyze trends"""

    def __init__(self, rp_dir):
        self.history_file = rp_dir / "state" / "scene_history.json"
        self.scenes = []
        self.analyzer = SceneAnalyzer()

        self._load()

    def add_scene(self, response_text, chapter, response_num):
        """Analyze and record new scene"""
        analysis = self.analyzer.analyze_scene(response_text)

        analysis["chapter"] = chapter
        analysis["response"] = response_num
        analysis["timestamp"] = datetime.now().isoformat()

        self.scenes.append(analysis)
        self._save()

        return analysis

    def check_for_stagnation(self, lookback=5):
        """Check recent scenes for stagnation"""
        return self.analyzer.detect_scene_stagnation(self.scenes, lookback)

    def get_scene_distribution(self, lookback=10):
        """Get distribution of scene types"""
        recent = self.scenes[-lookback:]

        distribution = {}
        for scene in recent:
            stype = scene["primary_type"]
            distribution[stype] = distribution.get(stype, 0) + 1

        return distribution

    def generate_scene_context(self):
        """Generate scene analysis context for prompt"""
        if len(self.scenes) < 3:
            return ""  # Not enough data yet

        context = ["📊 SCENE ANALYSIS:\n"]

        # Recent distribution
        dist = self.get_scene_distribution(lookback=10)
        context.append("**Recent scenes** (last 10):")
        for stype, count in sorted(dist.items(), key=lambda x: -x[1]):
            context.append(f"  - {stype}: {count}")
        context.append("")

        # Check for stagnation
        stagnation = self.check_for_stagnation(lookback=5)

        if stagnation["stagnant"]:
            severity = stagnation.get("severity", "moderate")
            context.append(f"⚠️ **SCENE VARIETY NOTICE** ({severity}):")

            if "type" in stagnation:
                context.append(f"  Last {stagnation['count']} scenes have been primarily "
                             f"{stagnation['type']}-focused.")
            elif "reason" in stagnation:
                context.append(f"  {stagnation['suggestion']}")

            context.append(f"  {stagnation['suggestion']}")
            context.append("  This will help maintain story variety and engagement.")
            context.append("")

        # Pacing trend
        recent_pacing = [s["pacing"] for s in self.scenes[-5:]]
        context.append(f"**Recent pacing**: {', '.join(recent_pacing)}")

        # Tension trend
        recent_tension = [s["tension"] for s in self.scenes[-5:]]
        avg_tension = sum(recent_tension) / len(recent_tension)
        context.append(f"**Average tension**: {avg_tension:.1f}/10")
        context.append("")

        return "\n".join(context)
```

#### Prompt Integration

```python
# In automation, before building prompt

scene_history = SceneHistory(rp_dir)

# Generate scene context
scene_context = scene_history.generate_scene_context()

# Add to dynamic prompt if stagnation detected
if "SCENE VARIETY NOTICE" in scene_context:
    dynamic_sections.append(scene_context)

# Always track for analytics (don't inject every time)
# After Claude response:
scene_history.add_scene(response, chapter, response_num)
```

### Configuration

```yaml
scene_analysis:
  enabled: true

  # Analysis
  analyze_every_response: true
  use_deepseek_for_analysis: true

  # Stagnation detection
  detect_stagnation: true
  stagnation_lookback: 5  # Check last 5 scenes
  inject_variety_prompts: true

  # When to flag
  flag_high_severity: true
  flag_moderate_severity: true
  flag_low_severity: false

  # Scene distribution targets (optional)
  target_distribution:
    dialogue: 30  # 30% dialogue scenes
    action: 20
    emotional: 15
    introspection: 10
    description: 10
    other: 15
```

### User Commands

```bash
/scenes                    # Show scene history
/scenes distribution      # Show scene type distribution
/scenes recent            # Show recent scene types
/scenes analyze           # Analyze current scene trends
```

### Benefits

- **Variety**: Automatic detection of repetitive scenes
- **Engagement**: Better pacing through varied scenes
- **No Manual Intervention**: Replaces OOC "this is stale" comments
- **Analytics**: Understand scene patterns
- **Quality**: Maintains story freshness

---

## 3. Pacing & Tension Monitor

### Problem Statement

Story pacing can become flat - tension stays constant for too long without peaks and valleys. Need automatic detection and intervention (like the arc generator countdown) to inject plot developments when pacing gets stale.

### Proposed Solution

Implement pacing monitor that:
- Tracks tension levels over time
- Detects flat pacing (no variation)
- Automatically injects plot developments when needed
- Works with story arc to pull in plot beats
- Provides pacing visualization

### Implementation

#### Pacing Monitor

```python
# src/pacing_monitor.py

class PacingMonitor:
    """Monitor and analyze story pacing"""

    def __init__(self, rp_dir):
        self.pacing_file = rp_dir / "state" / "pacing_data.json"
        self.tension_history = []  # List of (response_num, tension_level)
        self.pacing_history = []   # List of (response_num, pacing_speed)
        self.momentum_history = [] # List of (response_num, story_momentum)

        self._load()

    def analyze_pacing(self, response_text):
        """Analyze pacing and tension of response"""

        prompt = f"""Analyze the pacing and tension of this scene:

{response_text}

Provide:
1. **Tension level** (1-10): How much tension/conflict/stakes?
   1 = completely calm, 10 = maximum tension
2. **Pacing speed** (1-10): How fast is the scene moving?
   1 = very slow, 10 = rapid/intense pacing
3. **Emotional intensity** (1-10): How emotionally charged?
4. **Story momentum** (1-10): How much is the plot advancing?
   1 = no progress, 10 = major plot developments
5. **Breathing room**: Does scene allow characters to breathe/reflect? (yes/no)

Format as JSON.
"""

        analysis = self._call_deepseek(prompt)

        return {
            "tension": analysis["tension_level"],
            "pacing": analysis["pacing_speed"],
            "emotional_intensity": analysis["emotional_intensity"],
            "momentum": analysis["story_momentum"],
            "breathing_room": analysis["breathing_room"]
        }

    def add_data_point(self, response_num, analysis):
        """Add pacing data point"""
        self.tension_history.append((response_num, analysis["tension"]))
        self.pacing_history.append((response_num, analysis["pacing"]))
        self.momentum_history.append((response_num, analysis["momentum"]))

        self._save()
```

#### Flat Pacing Detection

```python
def detect_flat_pacing(self, lookback=15):
    """Detect if pacing has been flat"""

    if len(self.tension_history) < lookback:
        return {"flat": False}

    # Get recent tension values
    recent_tension = [t[1] for t in self.tension_history[-lookback:]]

    # Calculate variance
    tension_variance = np.var(recent_tension)
    avg_tension = np.mean(recent_tension)

    # Low variance = flat pacing
    if tension_variance < 2.0:  # Threshold for "flat"
        return {
            "flat": True,
            "reason": "tension",
            "average_tension": avg_tension,
            "responses_flat": lookback,
            "severity": self._assess_flatness_severity(tension_variance, avg_tension),
            "suggestion": self._suggest_tension_change(avg_tension)
        }

    # Check momentum
    recent_momentum = [m[1] for m in self.momentum_history[-lookback:]]
    avg_momentum = np.mean(recent_momentum)

    if avg_momentum < 3.0:  # Low momentum for extended period
        return {
            "flat": True,
            "reason": "momentum",
            "average_momentum": avg_momentum,
            "responses_flat": lookback,
            "severity": "moderate",
            "suggestion": "Story momentum is low - consider advancing plot"
        }

    # Check for monotonous high tension
    if avg_tension > 7.0 and tension_variance < 2.0:
        return {
            "flat": True,
            "reason": "sustained_high_tension",
            "average_tension": avg_tension,
            "responses_flat": lookback,
            "severity": "moderate",
            "suggestion": "High tension sustained too long - characters need breathing room"
        }

    return {"flat": False}

def _assess_flatness_severity(self, variance, avg_tension):
    """Assess how severe the flatness is"""
    if variance < 1.0:
        return "high"  # Very flat
    elif variance < 2.0:
        return "moderate"
    else:
        return "low"

def _suggest_tension_change(self, current_tension):
    """Suggest how to change tension"""
    if current_tension < 4:
        return "increase"  # Too calm, add conflict
    elif current_tension > 7:
        return "decrease"  # Too intense, add breathing room
    else:
        return "vary"  # Mix it up
```

#### Automatic Plot Injection

```python
# src/pacing_manager.py

class AutomaticPacingManager:
    """Automatically manage pacing with plot injections"""

    def __init__(self, rp_dir, plot_tracker, pacing_monitor):
        self.rp_dir = rp_dir
        self.plot_tracker = plot_tracker
        self.pacing_monitor = pacing_monitor

        # Hidden countdown (like arc generator)
        self.flat_countdown = 15  # Trigger after 15 flat responses
        self.config_file = rp_dir / "state" / "pacing_config.json"

    def check_and_inject(self, response_num):
        """Check pacing and inject stimulus if needed"""

        # Check if pacing is flat
        flat_info = self.pacing_monitor.detect_flat_pacing(lookback=15)

        if flat_info["flat"]:
            # Decrement countdown
            self.flat_countdown -= 1

            print(f"⚡ Pacing flat detected ({self.flat_countdown} responses until injection)")

            if self.flat_countdown <= 0:
                # Inject plot development
                print("⚡ PACING INTERVENTION: Injecting plot development")

                plot_injection = self._get_plot_injection_from_arc()

                # Reset countdown
                self.flat_countdown = 15

                return plot_injection

        else:
            # Pacing is varied, reset countdown
            if self.flat_countdown < 15:
                print(f"✓ Pacing improved, countdown reset")
            self.flat_countdown = 15

        return None

    def _get_plot_injection_from_arc(self):
        """Get next plot beat from story arc"""

        # Read story arc
        arc_file = self.rp_dir / "state" / "story_arc.md"
        if not arc_file.exists():
            # No arc, use generic injection
            return self._generic_plot_injection()

        arc_content = arc_file.read_text(encoding='utf-8')

        # Use plot tracker to find unresolved threads
        active_threads = self.plot_tracker.get_active_threads()

        if not active_threads:
            return self._generic_plot_injection()

        # Get highest priority thread
        priority_thread = max(active_threads, key=lambda t: self._thread_priority_value(t.priority))

        # Generate injection prompt
        injection = f"""
🎬 PACING INTERVENTION:

Story pacing has been flat for multiple responses. Time to advance the plot!

**Plot Thread to Address**: {priority_thread.description}
**Priority**: {priority_thread.priority}
**Introduced**: Chapter {priority_thread.introduced['chapter']}

Consider:
- Introduce a complication or obstacle related to this thread
- Have consequences catch up with characters
- Introduce new information or revelation
- Create a decision point for characters

Advance this plot thread naturally in your response.
"""

        return injection

    def _generic_plot_injection(self):
        """Generic plot injection when no specific threads"""
        return """
🎬 PACING INTERVENTION:

Story pacing has been flat. Consider:
- Introduce unexpected event or complication
- Have character make important decision
- Introduce new conflict or tension
- Advance time to next significant moment
- Introduce new character or information

Add something to move the story forward!
"""

    def _thread_priority_value(self, priority_str):
        """Convert priority string to numeric value"""
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(priority_str, 2)
```

#### Prompt Integration

```python
# In automation, before building prompt

pacing_manager = AutomaticPacingManager(rp_dir, plot_tracker, pacing_monitor)

# Check if intervention needed
plot_injection = pacing_manager.check_and_inject(response_num)

if plot_injection:
    # Add to dynamic prompt (high priority)
    dynamic_sections.insert(0, plot_injection)

# After Claude response, analyze pacing
pacing_analysis = pacing_monitor.analyze_pacing(response)
pacing_monitor.add_data_point(response_num, pacing_analysis)
```

#### Pacing Visualization

```python
def visualize_pacing_curve(self):
    """Generate visual pacing curve"""

    print("\n" + "="*80)
    print("PACING & TENSION CURVE")
    print("="*80 + "\n")

    # ASCII graph
    max_height = 10
    width = min(50, len(self.tension_history))

    # Sample tension values
    if len(self.tension_history) > width:
        # Downsample
        step = len(self.tension_history) // width
        sampled = self.tension_history[::step]
    else:
        sampled = self.tension_history

    # Print graph
    for level in range(max_height, 0, -1):
        line = f"{level:2d} |"
        for resp_num, tension in sampled:
            if tension >= level:
                line += "█"
            else:
                line += " "
        print(line)

    print("   +" + "-" * len(sampled))
    print(f"   Response numbers: {sampled[0][0]} to {sampled[-1][0]}")

    # Statistics
    tensions = [t[1] for t in self.tension_history]
    print(f"\nStatistics:")
    print(f"  Average tension: {np.mean(tensions):.1f}/10")
    print(f"  Min: {min(tensions)}, Max: {max(tensions)}")
    print(f"  Variance: {np.var(tensions):.2f} ({'flat' if np.var(tensions) < 2.0 else 'varied'})")
```

### Configuration

```yaml
pacing_management:
  enabled: true

  # Analysis
  analyze_every_response: true
  use_deepseek_for_analysis: true

  # Flat detection
  detect_flat_pacing: true
  flat_lookback: 15
  flat_variance_threshold: 2.0

  # Automatic intervention
  auto_inject_plot_beats: true
  inject_after_n_flat: 15  # Inject after 15 flat responses
  use_plot_threads: true  # Use plot tracker for injections

  # Visualization
  show_pacing_graph: false  # Show after each response (verbose)
```

### User Commands

```bash
/pacing                  # Show pacing statistics
/pacing graph           # Show pacing curve visualization
/pacing recent          # Show recent pacing data
/pacing inject          # Manually trigger plot injection
```

### Benefits

- **Automatic Management**: No manual intervention needed
- **Plot Integration**: Works with plot tracker for relevant developments
- **Natural Intervention**: Suggestions, not forced changes
- **Analytics**: Understand pacing patterns
- **Engagement**: Maintains story interest

---

## Integration Summary

All three systems work together:

```python
# Complete integration

# 1. Timeline tracking
timeline = Timeline(rp_dir)

# Before building prompt
timeline_context = timeline.generate_timeline_context()
time_advancement_suggestion = timeline.suggest_time_advancement()

if time_advancement_suggestion:
    dynamic_sections.append(time_advancement_suggestion)

# After response
timeline.auto_update_timeline(response, chapter, response_num)

# 2. Scene analysis
scene_history = SceneHistory(rp_dir)

# Before building prompt
scene_context = scene_history.generate_scene_context()

if "SCENE VARIETY NOTICE" in scene_context:
    dynamic_sections.append(scene_context)

# After response
scene_history.add_scene(response, chapter, response_num)

# 3. Pacing management
pacing_manager = AutomaticPacingManager(rp_dir, plot_tracker, pacing_monitor)

# Before building prompt
plot_injection = pacing_manager.check_and_inject(response_num)

if plot_injection:
    dynamic_sections.insert(0, plot_injection)  # Highest priority

# After response
pacing_analysis = pacing_monitor.analyze_pacing(response)
pacing_monitor.add_data_point(response_num, pacing_analysis)
```

---

## Priority & Implementation Order

**Recommended order:**

1. **Scene Analyzer** - Simplest, high value (2-3 days)
2. **Pacing Monitor** - Uses scene analyzer (2-3 days)
3. **Timeline Tracker** - Most complex (4-5 days)

**Total: ~1.5 weeks for full implementation**

**Quick wins**:
- Scene analyzer can be implemented quickly for immediate value
- Pacing monitor's flat detection is simple but effective
- Timeline tracking can start simple and grow more sophisticated

**Future enhancements**:
- Machine learning for pacing prediction
- Automatic story beat detection
- Multi-timeline support (parallel stories)
- Interactive timeline editor
