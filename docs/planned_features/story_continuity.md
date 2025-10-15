# Story Continuity & Consistency Features

This document outlines features designed to maintain story continuity, character consistency, and prevent contradictions throughout long-term RPs.

---

## 1. Plot Thread Tracker with DeepSeek Extraction

### Problem Statement
Plot threads get forgotten or lost across hundreds of responses. Characters mention doing something ("I'll call you tomorrow") but it never happens. The story loses continuity as threads are dropped.

**Scaling problem**: After months of RP, you have 50+ plot threads. Loading all of them into every prompt wastes 5,000+ tokens on threads that aren't relevant to the current scene.

**User's Insight**: "We will run into instances where something is like 2 months away and won't need to be in context all the time unless it is called in a memory or something."

### Proposed Solution
Implement a **DeepSeek-powered plot thread system**:
- **Master plot thread file**: Store all threads (50+) in one comprehensive file
- **DeepSeek extraction**: Query only relevant threads for current conversation (2-5 threads)
- **Automatic tracking**: Extract new threads and update mentions in background
- **Consequence system**: Countdown timers for time-sensitive threads
- **Smart filtering**: Only load critical/relevant threads, skip distant ones
- **95% token reduction**: Load 500 tokens instead of 5,000 tokens

### Implementation Approach

#### Master Plot Threads File

All plot threads stored in one comprehensive file:

```markdown
# state/plot_threads_master.md

## PLOT THREADS MASTER FILE
Total Active Threads: 47
Last Updated: Chapter 9, Response 234

---

### THREAD-001: Marcus Job Interview at Morrison Law Firm
**Status**: Active (CRITICAL - Consequence Imminent!)
**Priority**: High
**Introduced**: Chapter 5, Response 120
**Last Mentioned**: Chapter 5, Response 120
**Responses Since Mention**: 114 (interview is OVERDUE!)

**Description**: Marcus scheduled job interview at Morrison Law Firm for Tuesday 2pm. He was excited about the opportunity to switch firms.

**Related Characters**: Marcus, Morrison (potential boss, not yet introduced)
**Related Locations**: Morrison Law Firm
**Related Memories**: MEM-089 (Marcus talking about wanting career change)

**Time Sensitive**: YES - Interview was scheduled for specific time
**Consequence Countdown**: 0 (TRIGGERED!)

**Consequences**:
- ✅ Threshold 5: Interview time passed (TRIGGERED Response 125)
- ✅ Threshold 10: Firm assumed no-show, interviewed others (TRIGGERED Response 130)
- 🔜 Threshold 20: Firm hired someone else (triggers Response 140)
- 🔜 Threshold 30: Marcus's financial stress increases (triggers Response 150)

**Suggested Actions**:
- Marcus realizes he missed the interview
- Marcus gets rejection email/call
- Marcus's career frustration deepens

**Tags**: #career #marcus #time_sensitive #consequence_triggered #critical

---

### THREAD-002: Lily's Father Estrangement
**Status**: Active
**Priority**: Medium
**Introduced**: Chapter 4, Response 98
**Last Mentioned**: Chapter 8, Response 201
**Responses Since Mention**: 33

**Description**: Lily mentioned her difficult relationship with her father. They haven't spoken in 3 years. She gets sad when the topic comes up but hasn't shared details.

**Related Characters**: Lily, Lily's Father (not introduced), Marcus (knows about it)
**Related Locations**: N/A (not location-specific)
**Related Memories**: MEM-012, MEM-087 (Lily mentioning father issues)

**Time Sensitive**: No (slow-burn backstory)
**Consequence Countdown**: None

**Potential Developments**:
- Father could reach out unexpectedly
- Lily might decide to reconnect
- Could affect Lily-Marcus relationship if not addressed
- Lily might open up more about the details

**Tags**: #relationship #lily #backstory #slow_burn #family

---

### THREAD-003: David's Secret Health Issue
**Status**: Active
**Priority**: High
**Introduced**: Chapter 6, Response 156
**Last Mentioned**: Chapter 7, Response 182
**Responses Since Mention**: 52

**Description**: David seemed unusually tired and mentioned "doctor's appointments" vaguely. Marcus noticed but David brushed it off. David is hiding something health-related.

**Related Characters**: David, Marcus
**Related Locations**: N/A
**Related Memories**: MEM-065 (David looking exhausted), MEM-078 (David canceling plans due to "appointments")

**Time Sensitive**: Somewhat (health conditions don't wait)
**Consequence Countdown**: 15 responses remaining (will get worse at Response 197)

**Consequences**:
- Threshold 15: David's condition worsens visibly (triggers Response 197)
- Threshold 25: David has medical emergency (triggers Response 207)
- Threshold 35: Marcus finds out the hard way (triggers Response 217)

**Suggested Actions**:
- David mentions feeling worse
- Marcus notices David declining
- David finally opens up to Marcus

**Tags**: #health #david #marcus #friendship #secret #time_sensitive

---

### THREAD-004: Rent Payment Due End of Month
**Status**: Active
**Priority**: Low (for now)
**Introduced**: Chapter 8, Response 195
**Last Mentioned**: Chapter 8, Response 195
**Responses Since Mention**: 39

**Description**: Marcus mentioned rent is due at the end of the month. He's tight on money this month due to car repairs.

**Related Characters**: Marcus
**Related Locations**: Marcus's Apartment
**Related Memories**: MEM-091 (Marcus worried about money), MEM-094 (car repair expenses)

**Time Sensitive**: Yes (but 2 months away in story time)
**Consequence Countdown**: 60 responses (not relevant until Response 255)

**Consequences**:
- Threshold 60: Rent due date arrives (triggers Response 255)
- Threshold 65: Late fees if unpaid (triggers Response 260)
- Threshold 70: Eviction warning (triggers Response 265)

**Tags**: #finances #marcus #apartment #time_sensitive #distant_future

---

[... 43 more threads ...]
```

#### DeepSeek Plot Thread Extraction System

```python
# src/plot_thread_manager.py

class PlotThreadManager:
    """Manage plot threads with DeepSeek-powered extraction"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.threads_file = rp_dir / "state" / "plot_threads_master.md"
        self.deepseek = DeepSeekClient()

    def extract_relevant_threads(self, user_message, previous_analysis, current_response_num):
        """Extract only relevant plot threads for current conversation"""

        # Load full master file
        if not self.threads_file.exists():
            return ""

        all_threads = self.threads_file.read_text(encoding='utf-8')
        thread_count = self._count_threads(all_threads)

        prompt = f"""You have access to {thread_count} plot threads from this RP story.

**Current Scene Context**:
- Current response: {current_response_num}
- Characters in scene: {previous_analysis['characters']['in_scene']}
- Location: {previous_analysis['location']}
- Recent topics: {previous_analysis.get('summary', 'N/A')}

**User's New Message**:
{user_message}

**ALL PLOT THREADS** (comprehensive master list):
{all_threads}

**Task**: Extract ONLY the plot threads relevant to the current conversation.

Consider these factors:
1. **Immediate relevance**: Does thread involve current characters/location?
2. **Triggered consequences**: Has countdown reached 0 or about to trigger?
3. **Natural progression**: Would this thread naturally come up now?
4. **User mention**: Did user reference this thread explicitly or implicitly?
5. **Priority**: High priority threads take precedence
6. **Time sensitivity**: Urgent threads need attention even if not mentioned

Return JSON:
{{
  "critical_threads": [
    {{
      "thread_id": "THREAD-001",
      "reason": "Consequence triggered - Marcus missed interview, needs resolution",
      "urgency": "immediate",
      "action_needed": "Marcus should realize he missed it or get rejection message"
    }}
  ],
  "relevant_threads": [
    {{
      "thread_id": "THREAD-002",
      "reason": "Lily is in scene, backstory could naturally progress in deep conversation",
      "urgency": "optional",
      "action_needed": "Consider if moment is right for Lily to open up"
    }}
  ],
  "monitoring": [
    {{
      "thread_id": "THREAD-003",
      "reason": "David not in scene but health declining - worth tracking"
    }}
  ],
  "skip": [
    "THREAD-004 (Rent 2 months away, not relevant now)",
    "THREAD-005 (Not related to current scene)",
    ... list other skipped threads ...
  ]
}}

Target: 2-5 threads maximum. Only include what MUST (critical) or SHOULD (relevant) be in Claude's context.
Skip distant-future threads unless specifically mentioned.
"""

        result = self.deepseek.query(prompt)
        analysis = json.loads(result)

        return self._format_threads_for_prompt(analysis, all_threads)

    def _format_threads_for_prompt(self, analysis, all_threads):
        """Format extracted threads for inclusion in prompt"""

        sections = []

        # Critical threads (must address)
        if analysis["critical_threads"]:
            sections.append("## PLOT THREADS - CRITICAL\n")
            for thread in analysis["critical_threads"]:
                thread_content = self._extract_thread_content(all_threads, thread["thread_id"])
                sections.append(f"### {thread_content['title']}")
                sections.append(f"**Urgency**: {thread['urgency'].upper()}")
                sections.append(f"**Why Relevant**: {thread['reason']}")
                sections.append(f"**Action Needed**: {thread['action_needed']}")
                sections.append(f"**Description**: {thread_content['description']}")
                sections.append(f"**Consequence Status**: {thread_content['consequences']}")
                sections.append("")

        # Relevant threads (should consider)
        if analysis["relevant_threads"]:
            sections.append("## PLOT THREADS - ACTIVE\n")
            for thread in analysis["relevant_threads"]:
                thread_content = self._extract_thread_content(all_threads, thread["thread_id"])
                sections.append(f"### {thread_content['title']}")
                sections.append(f"**Why Relevant**: {thread['reason']}")
                sections.append(f"**Suggestion**: {thread['action_needed']}")
                sections.append(f"**Description**: {thread_content['description']}")
                sections.append("")

        # Tracking note
        monitoring_count = len(analysis.get("monitoring", []))
        skip_count = len(analysis.get("skip", []))
        total_tracked = monitoring_count + skip_count

        if total_tracked > 0:
            sections.append(f"## TRACKING: {total_tracked} other threads being monitored but not currently relevant\n")

        return "\n".join(sections) if sections else ""
```

#### Automatic Thread Management (Background)

After each response, DeepSeek updates the master thread file:

```python
def analyze_response_for_threads(self, response_text, chapter, response_num):
    """Analyze response for new threads and updates (runs in background)"""

    prompt = f"""Analyze this RP response for plot thread management:

Response: {response_text}

Current Response Number: {response_num}

**Tasks**:
1. Identify NEW plot threads introduced (promises, plans, goals, conflicts, mysteries)
2. Identify EXISTING threads mentioned (any callback to previous plot points)
3. Identify threads RESOLVED (completed or abandoned)

For NEW threads provide:
- Description (what is the thread?)
- Related characters
- Related locations (if any)
- Priority (low/medium/high)
- Time sensitive (yes/no - will it expire?)
- Consequence countdown (how many responses until natural consequence if ignored?)
- Natural consequences (what happens if ignored?)
- Tags

For MENTIONED threads provide:
- Brief description so we can match it
- Any updates to status

For RESOLVED threads provide:
- How it was resolved

Return JSON:
{{
  "new_threads": [
    {{
      "description": "Marcus scheduled job interview at Morrison Law Firm for Tuesday 2pm",
      "related_characters": ["Marcus", "Morrison"],
      "related_locations": ["Morrison Law Firm"],
      "priority": "high",
      "time_sensitive": true,
      "consequence_countdown": 5,
      "natural_consequences": [
        {{"threshold": 5, "result": "Interview time passes, Marcus misses it"}},
        {{"threshold": 10, "result": "Firm hires someone else"}},
        {{"threshold": 20, "result": "Marcus's financial situation worsens"}}
      ],
      "tags": ["career", "marcus", "time_sensitive"]
    }}
  ],
  "mentioned_threads": [
    {{
      "description": "Lily's father estrangement",
      "update": "Lily opened up more about why they don't talk"
    }}
  ],
  "resolved_threads": [
    {{
      "description": "Marcus fixing his car",
      "resolution": "Car repaired, Marcus picked it up from shop"
    }}
  ]
}}
"""

    result = self.deepseek.query(prompt)
    analysis = json.loads(result)

    # Process new threads
    for new_thread_data in analysis.get("new_threads", []):
        self._add_new_thread(new_thread_data, chapter, response_num)
        print(f"📍 New plot thread: {new_thread_data['description'][:50]}...")

    # Update mentioned threads
    for mentioned in analysis.get("mentioned_threads", []):
        thread_id = self._find_thread_by_description(mentioned["description"])
        if thread_id:
            self._update_thread_mention(thread_id, chapter, response_num)
            print(f"🔄 Updated thread: {mentioned['description'][:50]}...")

    # Resolve completed threads
    for resolved in analysis.get("resolved_threads", []):
        thread_id = self._find_thread_by_description(resolved["description"])
        if thread_id:
            self._resolve_thread(thread_id, resolved["resolution"])
            print(f"✅ Resolved thread: {resolved['description'][:50]}...")

    # Decrement all active consequence countdowns
    self._tick_all_countdowns(current_response_num)

    # Save updated master file
    self._save_master_file()

def _add_new_thread(self, thread_data, chapter, response_num):
    """Add new thread to master file"""

    thread_id = f"THREAD-{len(self.threads) + 1:03d}"

    thread_entry = f"""
---

### {thread_id}: {thread_data['description']}
**Status**: Active
**Priority**: {thread_data['priority'].title()}
**Introduced**: Chapter {chapter}, Response {response_num}
**Last Mentioned**: Chapter {chapter}, Response {response_num}
**Responses Since Mention**: 0

**Description**: {thread_data['description']}

**Related Characters**: {', '.join(thread_data.get('related_characters', []))}
**Related Locations**: {', '.join(thread_data.get('related_locations', ['N/A']))}
**Related Memories**: (To be linked)

**Time Sensitive**: {'YES' if thread_data.get('time_sensitive') else 'No'}
**Consequence Countdown**: {thread_data.get('consequence_countdown', 'None')}

**Consequences**:
{self._format_consequences(thread_data.get('natural_consequences', []))}

**Tags**: {' '.join('#' + tag for tag in thread_data.get('tags', []))}
"""

    # Append to master file
    with open(self.threads_file, 'a', encoding='utf-8') as f:
        f.write(thread_entry)

def _tick_all_countdowns(self, current_response_num):
    """Decrement consequence countdowns for all active threads"""

    # Load master file
    content = self.threads_file.read_text(encoding='utf-8')

    # Update countdown values and "Responses Since Mention"
    # (Implementation would parse and update the markdown)

    # Mark triggered consequences
    # (When countdown reaches 0, mark as TRIGGERED)
```

#### Example: Plot Thread Extraction in Action

**Response 120**: Marcus says "I have an interview at Morrison Law Firm on Tuesday at 2pm. I'm really hoping this works out."

```python
# DeepSeek analysis (background):
{
  "new_threads": [
    {
      "description": "Marcus scheduled job interview at Morrison Law Firm for Tuesday 2pm",
      "related_characters": ["Marcus", "Morrison"],
      "related_locations": ["Morrison Law Firm"],
      "priority": "high",
      "time_sensitive": true,
      "consequence_countdown": 5,
      "natural_consequences": [
        {"threshold": 5, "result": "Interview time passes, Marcus misses it"},
        {"threshold": 10, "result": "Firm hires someone else"},
        {"threshold": 20, "result": "Marcus's financial situation worsens"}
      ],
      "tags": ["career", "marcus", "time_sensitive"]
    }
  ]
}

📍 New plot thread: Marcus scheduled job interview at Morrison Law...
💾 Added THREAD-001 to master file
```

**Response 125** (5 responses later, interview not mentioned):
- Consequence countdown reaches 0
- Thread marked as "TRIGGERED" in master file
- Next prompt (Response 126) will include this as CRITICAL

**Response 126 prompt** (DeepSeek extracts):
```markdown
## PLOT THREADS - CRITICAL

### Marcus Job Interview at Morrison Law Firm
**Urgency**: IMMEDIATE
**Why Relevant**: Consequence triggered - interview time has passed without Marcus attending
**Action Needed**: Marcus should realize he missed the interview or receive a consequence
**Description**: Marcus scheduled job interview for Tuesday 2pm but never attended
**Consequence Status**: TRIGGERED - Interview time passed (Response 125)
```

**Response 126**: Claude writes: "Marcus's phone buzzed. A terse email from Morrison Law Firm: 'We waited for you at 2pm. Since you didn't show or call, we've moved forward with other candidates.' His stomach dropped. He'd completely forgotten about the interview."

Natural consequence executed! Thread continues with new consequences pending.

### Integration with Background Analysis

Plot thread management integrates seamlessly with the existing DeepSeek analysis system:

```python
# After Claude generates response N (runs in background, 1-response-behind)

def analyze_in_background(response_text, chapter, response_num):
    # 1. Scene analysis (who's in scene, location, etc.)
    response_analyzer.analyze_response(response_text, chapter, response_num)

    # 2. Memory extraction (create memorable moments)
    memory_manager.analyze_response_for_memories(response_text, chapter, response_num)

    # 3. Relationship analysis (tier changes)
    characters_in_scene = response_analyzer.last_analysis["characters"]["in_scene"]
    relationship_system.analyze_interaction(response_text, characters_in_scene, chapter, response_num)

    # 4. NEW: Plot thread analysis
    plot_manager.analyze_response_for_threads(response_text, chapter, response_num)
    # ↑ Extracts new threads, updates mentions, resolves threads, ticks countdowns

    print("✓ Background analysis complete")

# All of this happens while user is typing next message!
```

**Before building N+1 prompt:**

```python
# Get analysis from previous response
previous_analysis = response_analyzer.get_last_analysis()

# Extract relevant plot threads (DeepSeek query)
relevant_threads = plot_manager.extract_relevant_threads(
    user_message=user_message,
    previous_analysis=previous_analysis,
    current_response_num=current_response_num
)
# ↑ Only loads 2-5 relevant threads, not all 50!

# Build prompt with everything
prompt = f"""
{core_context}

{relevant_threads}  # ← Plot threads

{previous_response_analysis}  # ← Scene/pacing/variety alerts

{relationship_context}  # ← Recent tier changes

{relevant_memories}  # ← Relevant memories for scene participants

## USER MESSAGE
{user_message}
"""
```

**Timeline from user perspective:**
1. User types message and hits send
2. Claude generates (20 seconds) ← Only wait time
3. Response shows immediately
4. User starts typing next message
5. [Hidden] DeepSeek analyzes:
   - Scene context (15s)
   - Memories (5s)
   - Relationships (5s)
   - Plot threads (5s)
   Total: 30s hidden work
6. User hits send (analysis already complete!)
7. DeepSeek extracts relevant plot threads (5s) ← Quick query
8. Claude generates with complete context (20s)

**Total perceived wait: 25 seconds** (Claude + thread extraction)
**Hidden work: 30 seconds** (while user types)

### Thread Archive System (Scalability)

**Problem**: Master threads file grows indefinitely. After 6 months, you might have 200+ threads, most resolved. System 8 loads all of them, wasting tokens.

**Solution**: Automatic archiving of resolved threads

```python
class PlotThreadArchiver:
    """Automatically archive resolved threads"""

    def __init__(self, rp_dir):
        self.master_file = rp_dir / "state" / "plot_threads_master.md"
        self.archive_file = rp_dir / "state" / "plot_threads_archive.md"

    def resolve_and_archive_thread(self, thread_id, resolution):
        """Move resolved thread from master to archive"""

        # Extract thread content from master
        thread_content = self._extract_thread_from_master(thread_id)

        # Update status
        thread_content = thread_content.replace("**Status**: Active", "**Status**: Resolved")
        thread_content += f"\n**Resolution**: {resolution}\n"
        thread_content += f"**Resolved**: Chapter {self.current_chapter}, Response {self.current_response_num}\n"

        # Append to archive
        with open(self.archive_file, 'a', encoding='utf-8') as f:
            f.write("\n" + thread_content + "\n")

        # Remove from master
        self._remove_thread_from_master(thread_id)

        print(f"✓ Archived THREAD-{thread_id}: {thread_content['title']}")
```

**File Structure**:
```
state/
├── plot_threads_master.md     (Active threads only, <50 threads)
└── plot_threads_archive.md    (Resolved threads, unlimited)
```

**Benefits**:
- Master file stays under 50 threads (~5,000 tokens)
- Archive can grow to 500+ threads without performance impact
- System 8 only queries master (stays fast and cheap)
- User can still query archive: `/threads history` or `/threads search`

---

### Two-Stage Thread Extraction Optimization

**Problem**: System 8 loads ALL active threads (~10,000 tokens) to extract 2-5 relevant ones. Cost scales linearly with thread count.

**Solution**: Metadata-based pre-filter + DeepSeek extraction

#### Stage 1: Lightweight Thread Index

```json
// state/thread_index.json
{
  "THREAD-001": {
    "title": "Marcus Job Interview",
    "characters": ["Marcus", "Morrison"],
    "locations": ["Morrison Law Firm"],
    "tags": ["career", "marcus", "time_sensitive"],
    "priority": "high",
    "consequence_countdown": 0,
    "status": "critical",
    "last_mentioned": 120,
    "introduced": 120
  },
  "THREAD-002": {
    "title": "Lily's Father Estrangement",
    "characters": ["Lily", "Lily's Father"],
    "locations": [],
    "tags": ["relationship", "family", "backstory"],
    "priority": "medium",
    "consequence_countdown": null,
    "status": "active",
    "last_mentioned": 201,
    "introduced": 98
  }
}
```

#### Stage 2: Pre-Filter Algorithm

```python
def _prefilter_threads_by_metadata(self, user_message, previous_analysis):
    """Score threads by metadata, return top 15 candidates"""

    scored_threads = []

    for thread_id, metadata in self.thread_index.items():
        score = 0

        # Critical threads ALWAYS included (highest priority)
        if metadata["consequence_countdown"] == 0:
            score += 100

        # High priority threads
        if metadata["priority"] == "high":
            score += 20

        # Characters in scene match thread characters
        for char in previous_analysis["characters"]["in_scene"]:
            if char in metadata["characters"]:
                score += 30

        # Current location matches thread location
        if previous_analysis["location"] in metadata["locations"]:
            score += 25

        # Tag keywords appear in user message
        for tag in metadata["tags"]:
            if tag.lower() in user_message.lower():
                score += 15

        # Recently mentioned threads (recency bias)
        responses_ago = self.current_response_num - metadata["last_mentioned"]
        if responses_ago < 10:
            score += 10
        elif responses_ago < 20:
            score += 5

        # Time-sensitive threads get boost
        if metadata.get("time_sensitive"):
            score += 12

        scored_threads.append((thread_id, score))

    # Sort by score descending, take top 15
    top_candidates = sorted(scored_threads, key=lambda x: x[1], reverse=True)[:15]
    return [tid for tid, score in top_candidates]
```

#### Stage 3: DeepSeek Extraction on Filtered Set

```python
def extract_relevant_threads(self, user_message, previous_analysis, current_response_num):
    """Two-stage extraction: metadata filter → DeepSeek precision"""

    # Stage 1: Quick metadata filter (50 threads → 15 candidates, no cost)
    candidate_ids = self._prefilter_threads_by_metadata(user_message, previous_analysis)

    # Load full content for top 15 candidates only
    candidates_full_text = []
    for thread_id in candidate_ids:
        thread = self._load_full_thread_content(thread_id)
        candidates_full_text.append(thread)

    # Combine into text for DeepSeek (15 threads × 200 tokens = 3,000 tokens)
    candidates_text = "\n\n".join(candidates_full_text)

    # Stage 2: DeepSeek extraction on filtered set (precise relevance detection)
    prompt = f"""You have access to 15 pre-filtered plot threads (from {self.total_thread_count} total).

**Current Scene Context**:
- Current response: {current_response_num}
- Characters in scene: {previous_analysis['characters']['in_scene']}
- Location: {previous_analysis['location']}
- Recent topics: {previous_analysis.get('summary', 'N/A')}

**User's New Message**:
{user_message}

**PRE-FILTERED THREADS** (top 15 candidates):
{candidates_text}

**Task**: Extract ONLY the most relevant threads for the current conversation.

Return JSON with critical/relevant/monitoring/skip categories.
Target: 2-5 threads total in critical + relevant.
"""

    result = self.deepseek.query(prompt)
    analysis = json.loads(result)

    return self._format_threads_for_prompt(analysis, candidates_full_text)
```

**Performance Comparison**:

| Approach | Input Tokens | Cost per Query | Scalability |
|----------|--------------|----------------|-------------|
| **Current** (load all) | 10,000 | $0.0014 | Linear (doubles at 100 threads) |
| **Optimized** (two-stage) | 3,000 | $0.0004 | **Constant** (stays $0.0004 even at 200 threads) |
| **Savings** | 70% | **$0.001 per turn** | **$1.00 per 1000 turns** |

**Benefit**: Cost becomes **constant** regardless of total thread count. Can scale to 200+ active threads without performance degradation.

---

### Configuration
```yaml
# automation_config.yaml

plot_tracking:
  enabled: true

  # Detection settings
  auto_extract_threads: true
  extraction_model: "deepseek"  # Which model to use for extraction

  # Archive settings
  auto_archive_resolved: true
  archive_file: "state/plot_threads_archive.md"

  # Optimization settings
  use_two_stage_extraction: true  # Enable metadata pre-filtering
  thread_index_file: "state/thread_index.json"
  max_candidates_for_deepseek: 15  # Top N threads to send to DeepSeek

  # Threshold settings
  stale_threshold: 20  # Responses before thread is considered stale
  max_stale_reminders: 3  # Max threads to remind about

  # Consequence settings
  enable_consequences: true
  consequence_countdowns:
    high_priority: 5    # High priority threads trigger after 5 responses
    medium_priority: 10
    low_priority: 20

  # What to track
  track_types:
    - "promises"      # Character promises to do something
    - "plans"         # Planned actions
    - "conflicts"     # Unresolved conflicts
    - "mysteries"     # Unanswered questions
    - "goals"         # Character goals
```

### User Interface
```bash
# TUI commands
/threads list              # Show all active plot threads
/threads stale             # Show stale threads
/threads resolve <id>      # Mark thread as resolved (auto-archives)
/threads priority <id> high  # Change thread priority
/threads history           # Show archived (resolved) threads
/threads search <query>    # Search all threads (active + archive)
```

### Benefits
- **Story Continuity**: No dropped plot threads
- **Natural Consequences**: Actions (or inactions) have consequences
- **User Awareness**: Clear visibility into active plot threads
- **Automatic Tracking**: No manual thread management needed

---

## 2. Character Consistency Checker

### Problem Statement
Characters sometimes act out of character, forget their established traits, or contradict their personality. Long RPs make it easy to lose track of character voice and core attributes.

### Proposed Solution
Implement a **proactive "Personality Core" system** that:
- Defines immutable character traits in entity cards (Personality Core sections)
- Loads Personality Cores with high priority alongside entity cards
- Includes a consistency checklist in every prompt before response generation
- Claude actively follows character cores while writing (prevention, not detection)

### Entity Card Format

#### Enhanced Character Card Structure
```markdown
[CHAR] Marcus Smith

## PERSONALITY CORE (LOCKED - DO NOT CHANGE)
These traits are fundamental to Marcus's character and MUST remain consistent:

### Core Values
- **Primary**: Loyalty, honesty, family-first mentality
- **Secondary**: Hard work, integrity, keeping promises

### Fatal Flaws
- **Stubbornness**: Difficulty admitting mistakes or asking for help
- **Perfectionism**: Can be overly critical of himself and others

### Speaking Style
- Direct and straightforward
- Uses legal metaphors from his law background
- Rarely curses (only when extremely upset)
- Tends to use "Listen," or "Look," to start important points

### Baseline Temperament
- Calm under pressure
- Slow to anger but intense when triggered
- Generally optimistic but realistic

### Non-Negotiable Behaviors
These are things Marcus ALWAYS does:
- Keeps his promises, no matter what
- Puts family before career
- Pays his debts (literal and metaphorical)
- Respects authority but questions unjust rules

### Contradictory Behaviors (NEVER DO)
These actions would be completely out of character:
- Abandon a friend in crisis
- Use violence as a first resort
- Betray a confidence
- Cheat or lie to family
- Back down from protecting someone vulnerable

### Character Growth Areas (CAN EVOLVE)
These aspects can change through story events:
- Learning to ask for help (overcoming stubbornness)
- Work-life balance
- Vulnerability with romantic partners

---

## DYNAMIC TRAITS (CAN EVOLVE)
These change based on story events:

### Current Mood
Cautiously optimistic

### Recent Character Development
- Chapter 7: Learning to delegate at work
- Chapter 9: Opening up to Lily about his past

### Current Relationships
[See Relationships section]

### Temporary States
- Well-rested
- Financially stable
- Emotionally processing recent loss

---

## CONSISTENCY CHECK RULES

Before writing Marcus, verify:
1. Does this action align with his Core Values?
2. Does his dialogue match his Speaking Style?
3. Would this behavior contradict his Non-Negotiables?
4. If contradictory behavior is needed:
   - Is it justified by extreme circumstances?
   - Will it be acknowledged as out-of-character?
   - Will there be consequences for the character?
```

### Implementation

#### Consistency Checklist in Prompt

Before Claude generates each response, include this checklist:

```markdown
## CHARACTER CONSISTENCY CHECKLIST

**Instructions**: Before writing your response, mentally verify the following for EACH character in this scene:

For each character with a Personality Core:
- [ ] **Speaking Style**: Does dialogue use this character's speaking style? Is dialogue adding meaningfully to the scene, or just background approval/agreement?
- [ ] **Core Values**: Do actions align with this character's core values?
- [ ] **Never Do Behaviors**: Am I avoiding behaviors this character would NEVER do?
- [ ] **Non-Negotiable Behaviors**: Is this character following their non-negotiable behaviors?
- [ ] **Positivity Bias**: Is this character showing positivity bias or unrealistic agreeableness toward ANYONE in scene they should not? (Don't make characters artificially nice or conflict-averse)

**If any check fails, revise the character's portrayal before finalizing the response.**
```

#### Loading Personality Cores with High Priority

Entity cards with Personality Cores are loaded with high priority alongside full entity cards:

```python
# src/entity_loader.py

class EntityLoader:
    """Load entity cards with personality cores prioritized"""

    def load_entities_for_scene(self, characters_in_scene):
        """Load entity cards with cores prominently featured"""

        entity_context = []

        for character in characters_in_scene:
            entity_file = self.rp_dir / "entities" / f"{character}.md"

            if not entity_file.exists():
                continue

            # Load full entity card
            full_card = entity_file.read_text(encoding='utf-8')

            # Check if character has Personality Core section
            if "## PERSONALITY CORE" in full_card:
                # Extract and highlight the core
                core_section = self._extract_section(full_card, "PERSONALITY CORE")

                # Format for high visibility in prompt
                entity_context.append(f"""
## {character} - ENTITY CARD

### ⚠️ PERSONALITY CORE (LOCKED - MUST FOLLOW)
{core_section}

---

### Full Character Details
{self._get_non_core_sections(full_card)}
""")
            else:
                # No personality core, just load normal card
                entity_context.append(f"## {character} - ENTITY CARD\n\n{full_card}")

        return "\n\n".join(entity_context)
```

#### Integration into Prompt Building

```python
# When building prompt for Claude

def build_prompt(user_message, characters_in_scene):
    """Build complete prompt with consistency checklist"""

    # Load entity cards with personality cores highlighted
    entity_loader = EntityLoader(rp_dir)
    entity_context = entity_loader.load_entities_for_scene(characters_in_scene)

    # Build prompt
    prompt = f"""
{core_system_instructions}

{entity_context}  # ← Personality cores prominently featured

{plot_threads}  # ← Relevant plot threads

{relevant_memories}  # ← Relevant memories

## CHARACTER CONSISTENCY CHECKLIST

**Instructions**: Before writing your response, mentally verify the following for EACH character in this scene:

For each character with a Personality Core:
- [ ] **Speaking Style**: Does dialogue use this character's speaking style? Is dialogue adding meaningfully to the scene, or just background approval/agreement?
- [ ] **Core Values**: Do actions align with this character's core values?
- [ ] **Never Do Behaviors**: Am I avoiding behaviors this character would NEVER do?
- [ ] **Non-Negotiable Behaviors**: Is this character following their non-negotiable behaviors?
- [ ] **Positivity Bias**: Is this character showing positivity bias or unrealistic agreeableness toward ANYONE in scene they should not? (Don't make characters artificially nice or conflict-averse)

**If any check fails, revise the character's portrayal before finalizing the response.**

---

## USER MESSAGE
{user_message}
"""

    return prompt
```

**Key principle**: The Personality Core is **always loaded** for characters in scene, regardless of tier system. It's non-negotiable for maintaining character consistency.

### Configuration
```yaml
# automation_config.yaml

character_consistency:
  enabled: true

  # Personality Core loading
  always_load_cores: true  # Always load personality cores for scene characters
  highlight_cores: true    # Highlight cores with warning emoji and "MUST FOLLOW" labels

  # Checklist
  include_checklist: true  # Include consistency checklist in every prompt
  checklist_position: "after_context_before_message"  # Where to place checklist

  # Entity card formatting
  separate_core_section: true  # Show personality core separately from rest of card
```

### Benefits
- **Proactive Prevention**: Claude follows character cores while writing (not reactive detection)
- **No False Positives**: No analysis errors or over-flagging minor issues
- **Zero Latency**: No additional processing time or DeepSeek calls
- **Always Loaded**: Personality cores always present for scene characters
- **Positivity Bias Prevention**: Explicitly reminds Claude to avoid making characters unrealistically agreeable

---

## 3. Contradiction Detection System

### Problem Statement
New content sometimes contradicts established facts (hair color changes, dead characters reappear, timeline inconsistencies, etc.). These contradictions break immersion and require retconning.

### Proposed Solution
Build a fact database that:
- Extracts factual statements from each response
- Maintains canonical information about characters, locations, events
- Checks new content against established facts
- Flags contradictions before they become canon
- Allows user to resolve contradictions

### Implementation

#### Fact Database Structure
```python
# src/fact_checker.py

class FactDatabase:
    def __init__(self, rp_dir):
        self.facts_file = rp_dir / "state" / "story_facts.json"
        self.facts = {
            "characters": {
                # "Marcus Smith": {
                #     "physical": {
                #         "eye_color": {"value": "brown", "source": "ch3_r45", "confidence": 0.9},
                #         "height": {"value": "6'1\"", "source": "ch1_r12", "confidence": 0.95}
                #     },
                #     "abilities": {
                #         "lawyer": {"value": true, "source": "ch1_r1", "confidence": 1.0}
                #     },
                #     "relationships": {},
                #     "history": {}
                # }
            },
            "locations": {
                # "Coffee Corner Cafe": {
                #     "address": {"value": "123 Main St", "source": "ch2_r30"},
                #     "description": {...}
                # }
            },
            "events": [
                # {"description": "Marcus graduated law school", "date": "2015", "source": "ch4_r89"}
            ],
            "world_rules": {
                # "magic_exists": {"value": true, "source": "ch1_r5"},
                # "technology_level": {"value": "modern", "source": "ch1_r1"}
            },
            "timeline": {}
        }
        self._load()

    def extract_facts_from_response(self, response_text, chapter, response_num):
        """Use DeepSeek to extract factual statements"""
        prompt = f"""Extract factual statements from this RP response.

Focus on:
1. Character physical descriptions (eye color, hair, height, age, etc.)
2. Character abilities, skills, jobs, education
3. Location descriptions and details
4. Timeline/chronology facts
5. Relationship states
6. World-building rules (how magic works, technology level, etc.)
7. Historical events

Response: {response_text}

Format as JSON:
{{
  "characters": [
    {{"name": "Marcus", "attribute": "eye_color", "value": "brown", "confidence": 0.9}}
  ],
  "locations": [...],
  "events": [...],
  "world_rules": [...]
}}

Only extract explicit facts, not implications or maybes.
"""

        extracted = self._call_deepseek(prompt)

        # Add source info
        source = f"ch{chapter}_r{response_num}"
        for fact_type, facts_list in extracted.items():
            for fact in facts_list:
                fact["source"] = source

        return extracted

    def add_facts(self, extracted_facts):
        """Add facts to database, checking for contradictions first"""
        contradictions = []

        # Process character facts
        for char_fact in extracted_facts.get("characters", []):
            char_name = char_fact["name"]
            attribute = char_fact["attribute"]
            new_value = char_fact["value"]
            source = char_fact["source"]
            confidence = char_fact.get("confidence", 0.8)

            # Initialize character if new
            if char_name not in self.facts["characters"]:
                self.facts["characters"][char_name] = {}

            # Check for contradiction
            existing = self.facts["characters"][char_name].get(attribute)

            if existing and existing["value"] != new_value:
                # Contradiction found!
                contradictions.append({
                    "type": "character",
                    "subject": char_name,
                    "attribute": attribute,
                    "existing_value": existing["value"],
                    "existing_source": existing["source"],
                    "new_value": new_value,
                    "new_source": source,
                    "confidence_diff": confidence - existing.get("confidence", 0.8)
                })
            else:
                # No contradiction, add fact
                self.facts["characters"][char_name][attribute] = {
                    "value": new_value,
                    "source": source,
                    "confidence": confidence
                }

        # Similar for locations, events, world_rules...

        self._save()
        return contradictions

    def generate_contradiction_warning(self, contradictions):
        """Format contradictions for user review"""
        if not contradictions:
            return None

        warning = ["🚨 POTENTIAL CONTRADICTIONS DETECTED:\n"]

        for c in contradictions:
            warning.append(f"**{c['subject']}**: {c['attribute']}")
            warning.append(f"  Established: {c['existing_value']} (Source: {c['existing_source']})")
            warning.append(f"  New response: {c['new_value']} (Source: {c['new_source']})")

            # Suggest resolution based on confidence
            if c.get('confidence_diff', 0) > 0.2:
                warning.append(f"  💡 New info seems more confident - might be intentional retcon?")

            warning.append(f"  Choose action:")
            warning.append(f"    [1] Accept new value (update canon)")
            warning.append(f"    [2] Keep original (reject new response)")
            warning.append(f"    [3] Edit response to match original")
            warning.append(f"    [4] Both are true (needs explanation)")
            warning.append("")

        return "\n".join(warning)
```

#### Integration
```python
# After Claude generates response

fact_db = FactDatabase(rp_dir)

# Extract facts from response
extracted_facts = fact_db.extract_facts_from_response(response, chapter, response_num)

# Check for contradictions
contradictions = fact_db.add_facts(extracted_facts)

if contradictions:
    # Show contradictions
    warning = fact_db.generate_contradiction_warning(contradictions)
    print(warning)

    # For each contradiction, get user resolution
    for c in contradictions:
        choice = input(f"Resolve '{c['subject']}' - {c['attribute']} (1/2/3/4): ")

        if choice == "1":
            # Accept new value - already added to DB
            pass
        elif choice == "2":
            # Keep original - need to regenerate response
            return "regenerate_needed"
        elif choice == "3":
            # Edit response
            # Show user the response and let them edit
            edited_response = user_edit_response(response)
            return edited_response
        elif choice == "4":
            # Both true - add explanation to KB
            explanation = input("How can both be true? ")
            fact_db.add_special_case(c, explanation)
```

### Fact Query System
```python
def query_fact(self, query):
    """Natural language query of fact database"""
    prompt = f"""User question: {query}

Fact database: {json.dumps(self.facts, indent=2)}

Answer the user's question based on the facts.
Include the source reference.
"""

    answer = self._call_deepseek(prompt)
    return answer

# Usage:
# /fact "What color are Marcus's eyes?"
# → "Marcus has brown eyes (established in Chapter 3, Response 45)"
```

### Configuration
```yaml
contradiction_detection:
  enabled: true
  check_every_response: true

  # What to check
  check_types:
    - character_physical
    - character_abilities
    - locations
    - events
    - world_rules
    - timeline

  # Confidence thresholds
  flag_if_confidence_diff: 0.15  # Flag if confidence diff > 15%

  # Auto-resolution
  auto_accept_if_confidence_much_higher: 0.3  # Auto-accept if 30% more confident

  # Fact extraction
  extract_every_n_responses: 1  # Extract facts every N responses
  deep_extraction_every_n: 10   # Deep fact extraction every 10 responses
```

### User Commands
```bash
/fact "What color are Marcus's eyes?"  # Query fact database
/facts character Marcus                # Show all facts about Marcus
/facts location "Coffee Shop"          # Show location facts
/facts timeline                        # Show timeline facts
/facts-export                          # Export fact database as reference doc
```

### Benefits
- **Consistency**: Prevents contradictions
- **Reference**: Easy fact lookup
- **Quality**: Maintains story quality
- **Debugging**: Find when facts were established

---

## 4. Fact Extraction & Knowledge Base

### Problem Statement
Established facts are buried in thousands of lines of text. World-building details, character backgrounds, and story history are hard to reference. Claude doesn't have easy access to the full knowledge base.

### Proposed Solution
Create a **DeepSeek-built knowledge base** that:
- Automatically extracts facts from responses using DeepSeek (background analysis)
- Organizes knowledge into structured markdown document
- Loads entire knowledge base as reference document in prompts
- Provides natural language query interface for user
- Exports as browsable wiki

### Implementation

#### Knowledge Base Structure

All world-building knowledge stored in a comprehensive markdown document:

```markdown
# state/knowledge_base.md

## WORLD KNOWLEDGE BASE
Last Updated: Chapter 9, Response 234

---

## Setting

**Genre**: Contemporary fiction, romance, slice of life
**Time Period**: Modern day (2024)
**Primary Location**: Chicago, Illinois
**Technology Level**: Modern - smartphones, internet, electric cars

*(Established: Chapter 1, Response 1)*

---

## Geography

### Neighborhoods

#### Lincoln Park
- Upscale residential neighborhood
- Tree-lined streets, historic brownstones
- Home to Coffee Corner Cafe

*(Established: Chapter 2, Response 30)*

#### The Loop
- Downtown business district
- High-rise offices, busy streets
- Where Marcus works

*(Established: Chapter 3, Response 45)*

---

## Organizations

### Morrison Law Firm
- **Type**: Corporate law firm
- **Size**: Mid-sized (50-100 attorneys)
- **Specialization**: Corporate law, mergers & acquisitions
- **Reputation**: Prestigious, competitive
- **Location**: Downtown Chicago (The Loop)

*(Established: Chapter 5, Response 120)*

---

## Locations

### Coffee Corner Cafe
- **Type**: Independent coffee shop
- **Address**: 123 Main St, Lincoln Park
- **Features**:
  - Cozy outdoor patio with string lights
  - Fireplace inside for winter
  - Local artwork on walls
  - Live music on weekends
- **Atmosphere**: Artistic, neighborhood favorite, welcoming
- **Regulars**: Marcus, Lily, David

*(Established: Chapter 2, Response 30; expanded Chapter 4, Response 89)*

### Marcus's Apartment
- **Type**: One-bedroom apartment
- **Location**: Lincoln Park
- **Rent**: $1,800/month (due end of month)
- **Features**: Small but well-maintained, close to work

*(Established: Chapter 1, Response 8; rent mentioned Chapter 8, Response 195)*

---

## Cultural Details

### Coffee Culture
Chicago has a strong coffee culture with many independent cafes. People treat cafes as social spaces, not just grab-and-go spots.

*(Established: Chapter 2, Response 32)*

### Sunday Brunch Tradition
Strong brunch culture, especially on Sundays. Popular restaurants often have hour-long waits.

*(Established: Chapter 4, Response 78)*

---

## Important Items

### Marcus's Car (2015 Honda Civic)
- Recently required $800 in repairs
- Causing financial stress for Marcus
- He relies on it for work

*(Established: Chapter 7, Response 180; repairs mentioned Chapter 8, Response 192)*

---

## Story Themes
- Career vs personal life balance
- Vulnerability and emotional connection
- Found family and friendship
- Financial stress and adult responsibilities

---

## Tone & Style
- Realistic, grounded
- Emotionally nuanced
- Focuses on everyday moments and relationships
- Avoids melodrama
```

#### Background Knowledge Extraction (DeepSeek)

DeepSeek automatically extracts world-building knowledge and updates the markdown document:

```python
# src/knowledge_base.py

class KnowledgeBase:
    """DeepSeek-powered knowledge base builder"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.kb_file = rp_dir / "state" / "knowledge_base.md"
        self.deepseek = DeepSeekClient()

    def analyze_response_for_knowledge(self, response_text, chapter, response_num):
        """Extract world-building knowledge (runs in background)"""

        prompt = f"""Extract NEW or EXPANDED world-building knowledge from this RP response.

Response: {response_text}

Extract:
1. Setting details (genre, time period, technology level, etc.)
2. Geography (neighborhoods, locations, landmarks)
3. Organizations (companies, firms, institutions)
4. Location details (cafes, apartments, offices with specific features)
5. Cultural practices or customs
6. Important items (cars, objects with story significance)
7. Story themes or tone

Return JSON:
{{
  "setting": [
    {{"key": "technology_level", "value": "Modern - smartphones, internet", "context": "Marcus used his phone to..."}}
  ],
  "geography": [
    {{"name": "Lincoln Park", "description": "Upscale residential neighborhood", "features": ["tree-lined streets"], "context": "..."}}
  ],
  "organizations": [
    {{"name": "Morrison Law Firm", "type": "law firm", "details": {{"size": "mid-sized"}}, "context": "..."}}
  ],
  "locations": [...],
  "cultural_details": [...],
  "important_items": [...],
  "themes": [...]
}}

Only extract NEW knowledge not already in the existing KB.
Be conservative - only significant world-building details.
"""

        result = self.deepseek.query(prompt)
        extracted = json.loads(result)

        # Update markdown document
        source = f"Chapter {chapter}, Response {response_num}"
        self._update_markdown_kb(extracted, source)

        print(f"✓ Extracted {self._count_items(extracted)} world-building items")

    def _update_markdown_kb(self, extracted, source):
        """Update the markdown knowledge base file"""

        # Load existing KB
        if self.kb_file.exists():
            kb_content = self.kb_file.read_text(encoding='utf-8')
        else:
            kb_content = self._create_empty_kb_template()

        # For each extracted item, add to appropriate section
        # (Implementation would parse markdown, find sections, append new content)

        # Example: Adding a new organization
        for org in extracted.get("organizations", []):
            org_section = f"""
### {org['name']}
- **Type**: {org.get('type', 'N/A')}
- **Details**: {json.dumps(org.get('details', {}))}

*(Established: {source})*
"""
            # Append to Organizations section
            kb_content = self._append_to_section(kb_content, "## Organizations", org_section)

        # Save updated markdown
        self.kb_file.write_text(kb_content, encoding='utf-8')
        print(f"💾 Updated knowledge base: {self.kb_file}")
```

#### Integration with Background Analysis

Knowledge extraction runs in background (1-response-behind):

```python
# After Claude generates response N (runs in background while user types)

def analyze_in_background(response_text, chapter, response_num):
    # 1. Scene analysis
    response_analyzer.analyze_response(response_text, chapter, response_num)

    # 2. Memory extraction
    memory_manager.analyze_response_for_memories(response_text, chapter, response_num)

    # 3. Relationship analysis
    characters_in_scene = response_analyzer.last_analysis["characters"]["in_scene"]
    relationship_system.analyze_interaction(response_text, characters_in_scene, chapter, response_num)

    # 4. Plot thread analysis
    plot_manager.analyze_response_for_threads(response_text, chapter, response_num)

    # 5. NEW: World-building knowledge extraction
    knowledge_base.analyze_response_for_knowledge(response_text, chapter, response_num)
    # ↑ Extracts world-building, updates markdown document

    print("✓ Background analysis complete")
```

#### Loading Knowledge Base into Prompts

The entire knowledge base markdown document is loaded as a reference:

```python
# When building prompt for Claude

def build_prompt(user_message, characters_in_scene):
    """Build complete prompt with knowledge base"""

    # Load full knowledge base markdown
    kb_file = rp_dir / "state" / "knowledge_base.md"

    if kb_file.exists():
        knowledge_base_content = kb_file.read_text(encoding='utf-8')
    else:
        knowledge_base_content = ""

    # Build prompt
    prompt = f"""
{core_system_instructions}

{entity_context}  # ← Entity cards with personality cores

{plot_threads}  # ← Relevant plot threads (DeepSeek extracted 2-5 from 50+)

{knowledge_base_content}  # ← FULL knowledge base document loaded as reference

{relevant_memories}  # ← Relevant memories

## CHARACTER CONSISTENCY CHECKLIST
[... checklist ...]

---

## USER MESSAGE
{user_message}
"""

    return prompt
```

**Key principle**: The entire knowledge base document is loaded as a reference. Claude can consult it as needed during response generation.

#### Natural Language Query (User Command)
```python
def query(self, question):
    """Natural language query of knowledge base for user"""
    kb_content = self.kb_file.read_text(encoding='utf-8')

    prompt = f"""Question: {question}

Knowledge Base:
{kb_content}

Answer the question based on the knowledge base.
Include source references (chapter/response where established).
If information isn't available, say so.
"""

    answer = self.deepseek.query(prompt)
    return answer

# Usage:
# /kb "What organizations have been mentioned?"
# → "Morrison Law Firm (mid-sized corporate law firm, established Chapter 5, Response 120)"
```

#### Wiki Export
```python
def export_wiki(self, output_dir):
    """Export knowledge base as browsable HTML wiki"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate index page
    self._generate_wiki_index(output_dir)

    # Generate category pages
    for category in ["characters", "locations", "organizations", "items"]:
        self._generate_category_page(category, output_dir)

    # Generate world-building page
    self._generate_world_page(output_dir)

    # Generate timeline page
    self._generate_timeline_page(output_dir)

    # Add CSS styling
    self._copy_wiki_css(output_dir)

    print(f"✅ Wiki exported to {output_dir}")
    print(f"   Open {output_dir / 'index.html'} in browser")
```

### Configuration
```yaml
# automation_config.yaml

knowledge_base:
  enabled: true

  # Background extraction (DeepSeek, 1-response-behind)
  auto_extract: true
  analyze_every_response: true
  analysis_model: "deepseek"

  # Document format
  kb_file: "state/knowledge_base.md"  # Markdown format
  include_source_references: true     # Show where facts were established

  # Prompt loading
  load_full_document: true  # Load entire KB as reference (not extracted per-scene)

  # Export
  enable_wiki_export: true
  wiki_output_dir: "exports/wiki"
```

### User Commands
```bash
# TUI commands
/kb "What organizations have been mentioned?"  # Query knowledge base using DeepSeek
/kb show                                       # Display entire knowledge base
/kb export wiki                                # Export as browsable HTML wiki
/kb refresh                                    # Re-scan all chapters for knowledge (rebuild from scratch)
```

### Benefits
- **Automatic Building**: DeepSeek extracts world-building in background
- **No Agent Needed**: Simple background extraction, no dedicated agent
- **Always Available**: Full knowledge base loaded as reference in every prompt
- **Source Tracking**: See when/where every detail was established
- **Markdown Format**: Easy to read and manually edit if needed
- **Wiki Export**: Share world-building with others as HTML

---

## Integration Summary

All four systems work together:

```python
# Complete integration flow

# 1. BEFORE building prompt:
plot_tracker = PlotThreadTracker(rp_dir)
kb = KnowledgeBase(rp_dir)

# Check plot threads
stale_threads = plot_tracker.check_stale_threads(response_num)
consequences = plot_tracker.tick_consequences(response_num)
thread_context = plot_tracker.generate_thread_context(stale_threads, consequences)

# Get relevant knowledge
topics = identify_relevant_topics(user_message)
kb_context = kb.generate_kb_summary_for_prompt(topics)

# Add to prompt
if thread_context:
    prompt += f"\n{thread_context}\n"
if kb_context:
    prompt += f"\n{kb_context}\n"

# 2. AFTER Claude generates response:
characters_in_scene = identify_characters_in_scene(response)

# Check character consistency
consistency_checker = CharacterConsistencyChecker(rp_dir)
violations = consistency_checker.check_response_consistency(response, characters_in_scene)

if violations:
    # Handle violations (user choice)
    response = handle_consistency_violations(violations, response)

# Check for contradictions
fact_db = FactDatabase(rp_dir)
extracted_facts = fact_db.extract_facts_from_response(response, chapter, response_num)
contradictions = fact_db.add_facts(extracted_facts)

if contradictions:
    # Handle contradictions (user choice)
    response = handle_contradictions(contradictions, response)

# Extract plot threads
plot_tracker.extract_threads_from_response(response, chapter, response_num)

# Update knowledge base
kb.auto_update_from_response(response, chapter, response_num)

# 3. Save response
save_response(response)
```

---

## Priority & Implementation Order

**Recommended order:**

1. **Fact Extraction & Knowledge Base** - Foundation for other systems
2. **Contradiction Detection** - Uses fact database, high value
3. **Character Consistency Checker** - Independent, high value
4. **Plot Thread Tracker** - Most complex, build last

**Estimated effort:**
- Knowledge Base: 2-3 days
- Contradiction Detection: 1-2 days (uses KB)
- Character Consistency: 1-2 days
- Plot Thread Tracker: 3-4 days

**Total: ~1-2 weeks for full implementation**
