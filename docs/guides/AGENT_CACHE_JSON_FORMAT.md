# Agent Cache - Condensed JSON Format

**File**: `state/agent_analysis.json` (changed from .md to .json)
**Created**: 2025-10-14

Compact JSON structure for storing agent analysis results.

---

## 🎯 Design Goals

1. **Compact** - Minimal redundancy, short keys
2. **Fast parsing** - Easy to extract specific data
3. **Human-readable** - Still readable when needed
4. **Versionable** - Can track format version
5. **Expandable** - Easy to add new agents

---

## 📄 JSON Schema

```json
{
  "version": "1.0",
  "meta": {
    "resp_num": 120,
    "updated": "2025-10-14T16:45:30",
    "status": "fresh",
    "agents_run": 10,
    "agents_ok": 10,
    "agents_fail": 0
  },
  "background": {
    "resp_analyzer": {
      "dur": 15234,
      "scene": {
        "type": "dialogue",
        "pace": "medium",
        "tension": 6,
        "words": 450
      },
      "chars": {
        "in_scene": ["Marcus Thompson", "Lily Chen"],
        "mentioned": ["David Park", "Sarah Mitchell"]
      },
      "loc": "Coffee Corner Cafe",
      "time": {"elapsed": 30, "timestamp": "Tuesday 3:00 PM"},
      "alerts": {
        "variety": "Last 4/5 dialogue-heavy",
        "pacing": "Tension steady at 6/10 for 3 responses"
      }
    },
    "memory_create": {
      "dur": 5123,
      "memories": [
        {
          "id": "MEM-120-vulnerability",
          "char": "Marcus",
          "loc": "Coffee Corner Cafe",
          "type": "revelation",
          "sig": 8,
          "tone": "vulnerable, hopeful",
          "sum": "Marcus revealed fear of commitment from parents' divorce",
          "quote": "I've never told anyone this before, but...",
          "tags": ["vulnerability", "backstory", "marcus", "lily"]
        },
        {
          "id": "MEM-120-empathy",
          "char": "Lily",
          "loc": "Coffee Corner Cafe",
          "type": "character_moment",
          "sig": 6,
          "tone": "empathetic",
          "sum": "Lily showed deep understanding of Marcus's fears",
          "quote": "It's okay to be scared. That just means it matters.",
          "tags": ["empathy", "lily", "relationship_development"]
        }
      ]
    },
    "relationship": {
      "dur": 4892,
      "interactions": [
        {
          "chars": ["Marcus", "Lily"],
          "tier": "Acquaintance",
          "score": 28,
          "prev": 18,
          "change": 10,
          "trigger": "Lily empathy (Marcus likes: emotional_intelligence +10)",
          "next_tier": "Friend",
          "points_needed": 3
        }
      ]
    },
    "plot_threads": {
      "dur": 5234,
      "new": [
        {
          "id": "THREAD-025",
          "title": "Marcus's Commitment Issues",
          "status": "active",
          "priority": "medium",
          "time_sensitive": false,
          "chars": ["Marcus", "Lily"],
          "tags": ["character_development", "romance", "backstory"]
        }
      ],
      "mentioned": [
        {
          "id": "THREAD-001",
          "title": "Marcus Job Interview",
          "last_mention": 120,
          "conseq_countdown": 5,
          "status": "critical"
        },
        {
          "id": "THREAD-018",
          "title": "Lily's Photography Exhibition",
          "last_mention": 120,
          "time_until": 15,
          "status": "on_track"
        }
      ],
      "resolved": []
    },
    "knowledge": {
      "dur": 3421,
      "facts": [
        {
          "cat": "location",
          "subj": "Coffee Corner Cafe",
          "fact": "Espresso machine broken for 2 weeks",
          "conf": "high",
          "src": "Ch5-R120"
        },
        {
          "cat": "character",
          "subj": "Marcus Thompson",
          "fact": "Parents divorced when he was 12, causing trust issues",
          "conf": "high",
          "src": "Ch5-R120"
        },
        {
          "cat": "setting",
          "subj": "Local Art Scene",
          "fact": "Photography exhibitions monthly at Downtown Gallery",
          "conf": "medium",
          "src": "Ch5-R120"
        }
      ]
    },
    "contradiction": {
      "dur": 0,
      "enabled": false,
      "status": "skipped"
    }
  },
  "immediate": {
    "entity_analysis": {
      "dur": 3124,
      "tier1": [
        {"name": "Marcus Thompson", "file": "entities/Marcus.md", "tokens": 3200}
      ],
      "tier2": [
        {"name": "David Park", "file": "entities/David.md", "tokens": 2200},
        {"name": "Sarah Mitchell", "file": "entities/Sarah.md", "tokens": 1800}
      ],
      "tier3": ["Amy Rodriguez", "[12 others]"],
      "locs": ["Coffee Corner Cafe", "Morrison Law Firm"]
    },
    "fact_extract": {
      "dur": 2341,
      "facts": {
        "David Park": [
          "Marcus's best friend since college",
          "Works as software engineer at TechCorp",
          "Known for being blunt and direct",
          "Doesn't approve of Lily (thinks she's 'too flighty')",
          "Recently engaged to Amy Rodriguez"
        ],
        "Sarah Mitchell": [
          "Marcus's younger sister",
          "Grad student studying psychology",
          "Very close with Marcus, worries about him",
          "Met Lily once, thought she was sweet",
          "Stressed about thesis deadline"
        ]
      },
      "reduction": {"before": 4000, "after": 110, "pct": 97}
    },
    "memory_extract": {
      "dur": 2892,
      "memories": {
        "Marcus": [
          {
            "id": "MEM-120",
            "title": "Vulnerability Moment",
            "when": "Ch5-R120",
            "sig": 8,
            "why": "Just occurred, colors current emotional state",
            "sum": "Revealed fear of commitment from divorce"
          },
          {
            "id": "MEM-087",
            "title": "First Coffee with Lily",
            "when": "Ch4-R87",
            "sig": 7,
            "why": "Foundation of developing connection",
            "sum": "First real conversation, shared interests"
          },
          {
            "id": "MEM-012",
            "title": "Parents' Divorce Memory",
            "when": "Ch1-R12",
            "sig": 9,
            "why": "Root cause of commitment issues",
            "sum": "Witnessed parents' bitter divorce at age 12"
          }
        ],
        "Lily": [
          {
            "id": "MEM-087",
            "title": "First Coffee with Marcus",
            "when": "Ch4-R87",
            "sig": 7,
            "why": "Shared memory, mutual connection",
            "sum": "Felt comfortable opening up to Marcus"
          },
          {
            "id": "MEM-105",
            "title": "Past Relationship Trauma",
            "when": "Ch5-R105",
            "sig": 8,
            "why": "Makes empathy for Marcus meaningful",
            "sum": "Ex was emotionally unavailable, caused deep hurt"
          }
        ]
      },
      "reduction": {"before": 14700, "after": 590, "pct": 96}
    },
    "thread_extract": {
      "dur": 3012,
      "loaded": [
        {
          "id": "THREAD-001",
          "title": "Marcus Job Interview",
          "priority": "high",
          "status": "critical",
          "countdown": 5,
          "why": "Critical urgency, mentioned in conversation"
        },
        {
          "id": "THREAD-018",
          "title": "Lily's Photography Exhibition",
          "priority": "medium",
          "time_until": 15,
          "why": "Recently mentioned, relevant to Lily"
        },
        {
          "id": "THREAD-025",
          "title": "Marcus's Commitment Issues",
          "priority": "medium",
          "new": true,
          "why": "Just introduced, shapes current scene"
        }
      ],
      "monitored": 22,
      "reduction": {"before": 5500, "after": 785, "pct": 86}
    }
  },
  "stats": {
    "bg_dur": 30000,
    "bg_cost": 0.00075,
    "im_dur": 5000,
    "im_cost": 0.00085,
    "total_dur": 35000,
    "total_cost": 0.0016,
    "total_reduction": {"before": 24200, "after": 1515, "pct": 94, "saved": 22685},
    "roi": 42.5
  }
}
```

---

## 🔑 Key Abbreviations

```
resp_num     = response number
dur          = duration (ms)
resp_analyzer = response analyzer agent
memory_create = memory creation agent
chars        = characters
in_scene     = in scene
loc          = location
sig          = significance (1-10)
sum          = summary
cat          = category
subj         = subject
conf         = confidence
src          = source
pct          = percentage
bg           = background
im           = immediate
conseq       = consequence
```

---

## 📤 Condensed Prompt Format (From JSON)

**Function**: Extract ~300-400 tokens for Claude prompt injection

```python
def format_for_prompt(cache_json: dict) -> str:
    """Convert JSON cache to condensed prompt format"""

    bg = cache_json["background"]
    im = cache_json["immediate"]

    # Scene summary (1 line)
    scene = bg["resp_analyzer"]["scene"]
    scene_line = f"Scene: {scene['type']}, Tension {scene['tension']}/10"
    if "alerts" in bg["resp_analyzer"]:
        alerts = bg["resp_analyzer"]["alerts"]
        if "variety" in alerts:
            scene_line += f", ⚠️ {alerts['variety']}"

    # Characters (1 line)
    chars = bg["resp_analyzer"]["chars"]
    char_line = f"In Scene: {', '.join(chars['in_scene'])}"
    if chars.get("mentioned"):
        char_line += f" | Mentioned: {', '.join(chars['mentioned'])}"

    # Memories created (1 line)
    mems = bg["memory_create"]["memories"]
    mem_line = f"Memories Created: {len(mems)}"
    if mems:
        top_mem = max(mems, key=lambda m: m["sig"])
        mem_line += f" (Top: {top_mem['char']} - {top_mem['sum'][:40]}... sig:{top_mem['sig']})"

    # Relationships (1 line)
    rel_line = ""
    if bg["relationship"]["interactions"]:
        for inter in bg["relationship"]["interactions"]:
            rel_line += f"{inter['chars'][0]} ↔ {inter['chars'][1]}: {inter['change']:+d} (now {inter['score']}, {inter['tier']})"

    # Plot threads (2-3 lines)
    threads = bg["plot_threads"]
    thread_lines = []
    if threads.get("new"):
        thread_lines.append(f"NEW: {', '.join([t['id'] for t in threads['new']])}")
    for t in threads.get("mentioned", [])[:3]:  # Top 3
        status_emoji = "⚠️" if t.get("status") == "critical" else "📍"
        thread_lines.append(f"{status_emoji} {t['id']}: {t['title']}")

    # Knowledge (1 line)
    facts = bg["knowledge"]["facts"]
    know_line = f"Knowledge Added: {len(facts)} facts"
    if facts:
        know_line += f" ({', '.join([f['subj'] for f in facts[:2]])}...)"

    # Context for next response
    context_lines = []

    # Tier 2 entities
    if im["fact_extract"]["facts"]:
        for name, facts in list(im["fact_extract"]["facts"].items())[:2]:  # First 2
            context_lines.append(f"{name}: {', '.join(facts[:3])}")  # First 3 facts

    # Memories
    if im["memory_extract"]["memories"]:
        for char, mems in list(im["memory_extract"]["memories"].items())[:2]:  # First 2 chars
            mem_titles = ', '.join([m['id'] for m in mems[:2]])  # First 2 memories
            context_lines.append(f"{char} Memories: {mem_titles}")

    # Active threads
    if im["thread_extract"]["loaded"]:
        thread_ids = ', '.join([t['id'] for t in im["thread_extract"]["loaded"][:3]])
        context_lines.append(f"Active Threads: {thread_ids}")

    # Build final output (~300-400 tokens)
    output = f"""<!-- AGENT CONTEXT -->
**Scene**: {scene_line}
**Characters**: {char_line}
**Memories**: {mem_line}
{"**Relationships**: " + rel_line if rel_line else ""}
**Threads**: {', '.join(thread_lines)}
**Knowledge**: {know_line}

**Context for N+1**:
{chr(10).join(f"- {line}" for line in context_lines)}
<!-- END AGENT CONTEXT -->"""

    return output
```

**Output example** (~350 tokens):
```markdown
<!-- AGENT CONTEXT -->
**Scene**: dialogue, Tension 6/10, ⚠️ Last 4/5 dialogue-heavy
**Characters**: In Scene: Marcus Thompson, Lily Chen | Mentioned: David Park, Sarah Mitchell
**Memories**: Memories Created: 2 (Top: Marcus - Marcus revealed fear of commitment from... sig:8)
**Relationships**: Marcus ↔ Lily: +10 (now 28, Acquaintance)
**Threads**: NEW: THREAD-025, ⚠️ THREAD-001: Marcus Job Interview, 📍 THREAD-018: Lily's Photography Exhibition
**Knowledge**: Knowledge Added: 3 facts (Coffee Corner Cafe, Marcus Thompson...)

**Context for N+1**:
- David Park: Marcus's best friend since college, Works as software engineer, Doesn't approve of Lily
- Sarah Mitchell: Marcus's younger sister, Grad student, Very close with Marcus
- Marcus Memories: MEM-120, MEM-087
- Lily Memories: MEM-087, MEM-105
- Active Threads: THREAD-001, THREAD-018, THREAD-025
<!-- END AGENT CONTEXT -->
```

---

## 💾 Implementation Changes

### 1. Update save_to_cache()

**File**: `src/automation/agent_coordinator.py`

```python
def save_to_cache(self, cache_file: Path, response_number: int) -> None:
    """Save agent results to JSON cache"""
    import json

    cache_data = {
        "version": "1.0",
        "meta": {
            "resp_num": response_number,
            "updated": datetime.now().isoformat(),
            "status": "fresh",
            "agents_run": len(self.results),
            "agents_ok": len([r for r in self.results.values() if r.success]),
            "agents_fail": len([r for r in self.results.values() if not r.success])
        },
        "background": {},
        "immediate": {},
        "stats": self._calculate_stats()
    }

    # Add each agent's data
    for agent_id, result in self.results.items():
        if result.success:
            # Parse agent's JSON output (each agent returns structured dict)
            agent_data = json.loads(result.content)

            # Categorize by agent type
            if agent_id in BACKGROUND_AGENTS:
                cache_data["background"][agent_id] = agent_data
            else:
                cache_data["immediate"][agent_id] = agent_data

    # Write JSON
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)
```

### 2. Update load_from_cache()

```python
def load_from_cache(self, cache_file: Path) -> Optional[str]:
    """Load JSON cache and convert to prompt format"""
    import json

    if not cache_file.exists():
        return None

    with open(cache_file, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)

    # Convert to condensed prompt format
    return self._format_for_prompt(cache_data)
```

### 3. Update Agent.format_output()

**Each agent returns structured dict instead of markdown string**

**Example**: `response_analyzer.py`

```python
def format_output(self, result: str, data: dict) -> str:
    """Format as JSON dict (returned as JSON string)"""
    import json

    # Parse DeepSeek result into structured data
    output_dict = {
        "dur": int((time.time() - data.get('start_time', 0)) * 1000),
        "scene": self._parse_scene_data(result),
        "chars": self._parse_characters(result),
        "loc": self._parse_location(result),
        "time": self._parse_time(result),
        "alerts": self._parse_alerts(result)
    }

    return json.dumps(output_dict)
```

---

## 📊 File Size Comparison

**Current Markdown**:
- ~12KB per cache file
- ~3000+ tokens when full
- Difficult to parse specific data

**New JSON**:
- ~4KB per cache file (67% smaller)
- ~400 tokens in condensed format (87% smaller)
- Easy to extract specific fields
- Can query: `cache["background"]["relationship"]["interactions"][0]["score"]`

---

## ✅ Benefits

1. **Much more compact** - 67% smaller file size
2. **Faster parsing** - No regex, direct JSON access
3. **Easy queries** - `cache["immediate"]["memory_extract"]["memories"]["Marcus"]`
4. **Better for prompts** - Condensed format ~400 tokens vs ~3000
5. **Versionable** - Can track format version
6. **Type-safe** - Can validate with JSON schema

---

## 🚀 Migration Steps

1. **Update agents** - Return JSON dicts instead of markdown
2. **Update AgentCoordinator** - save/load JSON format
3. **Add format_for_prompt()** - Convert JSON to condensed text
4. **Test** - Verify prompt injection works
5. **Migrate existing** - Convert any existing .md files to .json

---

**Summary**: JSON format is 67% smaller, easier to parse, and produces much more compact prompt injection (~400 tokens vs ~3000). Each agent returns structured data as JSON dict instead of markdown string.
