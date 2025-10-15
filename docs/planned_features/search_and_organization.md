# Search & Organization Features

This document outlines features for finding content, managing entities, monitoring story health, and customizing prompts through templates.

---

## 1. Enhanced Search & Memory System

### Problem Statement

Finding specific scenes, dialogue, or information in long RPs (hundreds of responses across dozens of chapters) is difficult. Need to reference earlier content for consistency, callbacks, or fact-checking, but manual searching through files is tedious.

### How This Helps the RP (Not Just the User)

While search seems like a user convenience feature, it actually significantly improves RP quality:

1. **Consistency**: Claude can quickly reference earlier mentions to stay consistent
   - "What did Marcus say about his childhood last time this came up?"
   - Prevents contradictions by verifying established facts

2. **Callbacks**: Enable powerful narrative callbacks
   - "This is like that time at the coffee shop in Chapter 3..."
   - Creates emotional resonance by connecting to earlier moments

3. **Fact-Checking**: Verify details before writing
   - "When did Lily and Marcus first meet?"
   - "What was the name of that restaurant they went to?"

4. **Plot Thread Tracking**: Find when threads were introduced
   - "When did Marcus mention wanting to change careers?"
   - Helps track dangling plot threads

5. **Character Voice**: Find earlier dialogue for voice consistency
   - "How did Marcus phrase this kind of thing before?"
   - Maintains consistent speaking patterns

### User's Insight: DeepSeek-Powered Memory Extraction

> "Maybe have a separate card just for NPC memories that deepseek could parse through and give details on things that have happened in the past with that character as it is relevant? I don't think you would ever need the entirety of the memory card if that specific memory or quote was given to you. We could have each memory tagged separately with a timestamp and the situation of the memory"

**This is brilliant!** Solves the memory bloat problem:

**The Problem**: After 100+ responses, NPCs have dozens/hundreds of memories. Loading full memory cards = 10,000+ tokens.

**The Solution**:
- Store all memories in separate memory cards (tagged with timestamp + situation)
- DeepSeek queries memory cards based on current conversation
- Extract only relevant memories (~100-500 tokens vs 10,000+)
- Scales infinitely (doesn't matter if Marcus has 500 memories)

### Proposed Solution

Implement DeepSeek-powered memory system with:
- **Structured memory cards** for each NPC (timestamped, tagged, searchable)
- **On-demand memory extraction** (DeepSeek queries memories based on relevance)
- **Traditional search** (full-text, semantic, character-specific, interaction search)
- **Similar scene finding** (for callbacks)
- **Emotion-based search**

### Implementation

#### NPC Memory Card Structure

Each NPC has a separate memory card (distinct from entity card):

```markdown
# Marcus Smith - Memory Bank

## Memory Index
Total Memories: 47
Last Updated: Chapter 9, Response 234
Memory Card Size: ~8,500 tokens (but we only load relevant ones!)

---

## MEMORY #001
**ID**: MEM-001
**Timestamp**: Chapter 3, Response 65, Tuesday 2:00pm
**Location**: Coffee Corner Cafe
**Characters Present**: Marcus, Lily
**Type**: First Meeting
**Emotional Tone**: Nervous, hopeful
**Tags**: #first_meeting #lily #coffee_shop #work_discussion

**Memory**:
Marcus first met Lily at Coffee Corner Cafe. She was working behind the counter, and he ordered his usual black coffee. They struck up a conversation about the rainy weather. Lily mentioned she was studying psychology part-time. Marcus felt an immediate connection but was too nervous to ask for her number. He remembers her smile and how she laughed at his terrible joke about the weather.

**Quote**: "I like the rain," Lily said, smiling. "It makes everything feel quieter, you know? Like the world is taking a breath."

**Significance**: 8/10 - This meeting sparked Marcus's romantic interest in Lily

**Related Memories**: MEM-012 (second meeting), MEM-045 (asked her out)

---

## MEMORY #002
**ID**: MEM-002
**Timestamp**: Chapter 1, Response 12, Monday 9:00am
**Location**: TechCorp Office
**Characters Present**: Marcus, David
**Type**: Work Interaction
**Emotional Tone**: Frustrated, stressed
**Tags**: #work #david #promotion_denied #career

**Memory**:
Marcus learned he didn't get the promotion he'd been working toward for 18 months. His boss said he "wasn't leadership material yet." David found him staring out the office window and asked what was wrong. Marcus confided about the promotion, and David reminded him that he's talented and the company is short-sighted. This moment deepened their friendship.

**Quote**: "You're worth ten of half the managers here," David said firmly. "Their loss."

**Significance**: 6/10 - Turning point in career dissatisfaction

**Related Memories**: MEM-018 (decides to look for new job), MEM-032 (job offer)

---

## MEMORY #012
**ID**: MEM-012
**Timestamp**: Chapter 4, Response 98, Friday 7:00pm
**Location**: Coffee Corner Cafe
**Characters Present**: Marcus, Lily
**Type**: Developing Relationship
**Emotional Tone**: Warm, comfortable
**Tags**: #lily #coffee_shop #conversation #opening_up

**Memory**:
Marcus returned to the coffee shop "by chance" (he'd been hoping to see Lily). They talked for over an hour after her shift ended. He learned about her difficult relationship with her father and her dreams of becoming a therapist. He shared his frustrations with work. The conversation felt effortless. This time, he got her number.

**Quote**: "I feel like I can actually talk to you, you know?" Lily said. "Like you actually listen."

**Significance**: 9/10 - Relationship became personal, not just casual

**Related Memories**: MEM-001 (first meeting), MEM-045 (asked her out)

---

[... 44 more memories ...]
```

#### DeepSeek Memory Extraction System

```python
# src/memory_extraction.py

class NPCMemoryManager:
    """Manage NPC memories with DeepSeek-powered extraction"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.memory_dir = rp_dir / "memories"
        self.memory_dir.mkdir(exist_ok=True)
        self.deepseek = DeepSeekClient()

    def extract_relevant_memories(self, npc_name, context):
        """Extract only relevant memories for current conversation"""

        # Load NPC's full memory bank
        memory_file = self.memory_dir / f"{npc_name}_memories.md"

        if not memory_file.exists():
            return ""  # No memories yet

        full_memory_bank = memory_file.read_text(encoding='utf-8')

        # Query DeepSeek for relevant memories
        prompt = f"""You are helping Claude generate an RP response.

The character "{npc_name}" has a memory bank with {self._count_memories(full_memory_bank)} memories.

**Current context**:
{context}

**Full Memory Bank**:
{full_memory_bank}

**Task**: Extract ONLY the memories relevant to the current conversation.

Consider:
- Is the current topic related to this memory?
- Are the characters mentioned in the current conversation?
- Is the location relevant?
- Would recalling this memory inform {npc_name}'s response?

Return relevant memories in this format:
```
## RELEVANT MEMORIES FOR {npc_name.upper()}

### Memory #{'{'}ID{'}'}
{'{'}Brief memory summary with timestamp and significance{'}'}

### Memory #{'{'}ID{'}'}
{'{'}Another relevant memory{'}'}
```

If no memories are relevant, return "No relevant memories."

Target: 2-5 memories maximum (~300-600 tokens total)
"""

        extracted = self.deepseek.query(prompt)

        return extracted

    def add_memory(self, npc_name, memory_data):
        """Add new memory to NPC's memory bank"""

        memory_file = self.memory_dir / f"{npc_name}_memories.md"

        # Create memory entry
        memory_id = self._generate_memory_id(npc_name)

        memory_entry = f"""
---

## MEMORY #{memory_id}
**ID**: MEM-{memory_id:03d}
**Timestamp**: {memory_data['timestamp']}
**Location**: {memory_data['location']}
**Characters Present**: {', '.join(memory_data['characters'])}
**Type**: {memory_data['type']}
**Emotional Tone**: {memory_data['emotional_tone']}
**Tags**: {' '.join('#' + tag for tag in memory_data['tags'])}

**Memory**:
{memory_data['content']}

**Quote**: "{memory_data.get('quote', 'N/A')}"

**Significance**: {memory_data.get('significance', 5)}/10

**Related Memories**: {memory_data.get('related', 'None yet')}
"""

        # Append to memory bank
        if memory_file.exists():
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write(memory_entry)
        else:
            # Create new memory bank
            header = f"""# {npc_name} - Memory Bank

## Memory Index
Total Memories: 1
Last Updated: {memory_data['timestamp']}
"""
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(memory_entry)

        print(f"💾 Added memory MEM-{memory_id:03d} for {npc_name}")

    def analyze_response_for_memories(self, response_text, chapter, response_num):
        """Analyze response and extract memorable moments"""

        prompt = f"""Analyze this RP response for memorable moments that should be stored:

{response_text}

Extract:
1. Significant events (plot developments, revelations, conflicts)
2. Emotional moments (connections, heartbreak, joy, anger)
3. Character development (realizations, growth, changes)
4. Important interactions (first meetings, major conversations)
5. Memorable quotes (impactful or character-defining lines)

For each memorable moment, provide:
- Characters involved
- What happened (2-3 sentences)
- Why it's significant
- Emotional tone
- Best quote from the moment
- Tags (3-5 relevant tags)

Return as JSON array of memories.
"""

        analysis = self.deepseek.query(prompt)

        memories = json.loads(analysis)

        # Add each memory to relevant NPCs
        for memory in memories:
            for character in memory['characters']:
                memory_data = {
                    'timestamp': f"Chapter {chapter}, Response {response_num}",
                    'location': memory.get('location', 'Unknown'),
                    'characters': memory['characters'],
                    'type': memory.get('type', 'Interaction'),
                    'emotional_tone': memory['emotional_tone'],
                    'tags': memory['tags'],
                    'content': memory['content'],
                    'quote': memory.get('quote'),
                    'significance': memory.get('significance', 5)
                }

                self.add_memory(character, memory_data)

        return len(memories)
```

#### Integration with DeepSeek Context Intelligence

```python
# src/deepseek_context_intelligence.py (updated)

class DeepSeekContextIntelligence:
    """DeepSeek-powered intelligent context loading"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.deepseek = DeepSeekClient()
        self.memory_manager = NPCMemoryManager(rp_dir)  # NEW

        # ... existing initialization ...

    def build_intelligent_context(self, user_message, previous_analysis):
        """Build context using DeepSeek analysis (safety + optimization)"""

        context = []

        # === TIER 0: Core Files (Always) ===
        context.extend(self._load_core_files())

        # === TIER 1: Scene Participants (Full Cards - Safety) ===
        scene_participants = previous_analysis["characters"]["in_scene"]
        current_location = previous_analysis.get("location")

        print(f"🛡️ SAFETY: Loading full cards for scene participants")

        for character in scene_participants:
            # Load full entity card (personality, appearance, etc.)
            full_card = self._load_full_entity_card(character)
            context.append(full_card)

            # === NEW: Load relevant memories ===
            relevant_memories = self.memory_manager.extract_relevant_memories(
                npc_name=character,
                context={
                    "user_message": user_message,
                    "previous_analysis": previous_analysis,
                    "current_location": current_location
                }
            )

            if relevant_memories and "No relevant memories" not in relevant_memories:
                context.append(relevant_memories)
                print(f"   💭 {character}: Loaded relevant memories")
            else:
                print(f"   💭 {character}: No relevant memories needed")

        # === TIER 2: Mentioned But Absent (Smart Extraction) ===
        quick_analysis = self._quick_message_analysis(user_message, previous_analysis)

        mentioned_but_absent = [
            e for e in quick_analysis.get("mentioned_entities", [])
            if e not in scene_participants
        ]

        if mentioned_but_absent:
            print(f"📎 OPTIMIZATION: Extracting facts for mentioned entities")

            for entity in mentioned_but_absent:
                # Extract relevant facts from entity card
                extracted_facts = self._extract_relevant_facts(
                    entity=entity,
                    context=user_message,
                    previous_scene=previous_analysis
                )
                context.append(extracted_facts)

                # Also extract relevant memories for mentioned entity
                relevant_memories = self.memory_manager.extract_relevant_memories(
                    npc_name=entity,
                    context={
                        "user_message": user_message,
                        "previous_analysis": previous_analysis
                    }
                )

                if relevant_memories and "No relevant memories" not in relevant_memories:
                    context.append(relevant_memories)

        return "\n\n".join(context)
```

#### Example: Memory Extraction in Action

**Scenario**: User mentions Lily in conversation with Marcus

```python
# Current conversation
user_message = "I wonder what Lily would think about this"
previous_analysis = {
    "characters": {"in_scene": ["Marcus"]},
    "location": "Marcus's Apartment"
}

# Marcus is in scene, so load his memories
relevant_memories = memory_manager.extract_relevant_memories(
    npc_name="Marcus",
    context={
        "user_message": user_message,
        "previous_analysis": previous_analysis
    }
)

# DeepSeek returns:
"""
## RELEVANT MEMORIES FOR MARCUS

### Memory #001 (MEM-001)
**First meeting with Lily** (Chapter 3, Response 65)
Marcus first met Lily at Coffee Corner Cafe. Immediate connection, but too nervous to ask for her number. She said: "I like the rain. It makes everything feel quieter."
**Significance**: 8/10 - Sparked romantic interest

### Memory #012 (MEM-012)
**Getting Lily's number** (Chapter 4, Response 98)
Talked for over an hour after her shift. Lily: "I feel like I can actually talk to you." Got her number this time.
**Significance**: 9/10 - Relationship became personal

### Memory #045 (MEM-045)
**First date** (Chapter 5, Response 123)
Marcus asked Lily out. She said yes. Dinner at Italian restaurant. Felt natural and right.
**Significance**: 10/10 - Started relationship
"""

# Total: ~400 tokens (vs 8,500 tokens for full memory bank!)
```

**Benefits**:
- ✅ **Scalability**: Works even after 500+ memories (only loads 2-5 relevant ones)
- ✅ **Contextual**: DeepSeek picks memories based on current conversation
- ✅ **Rich detail**: Includes quotes, timestamps, significance for callbacks
- ✅ **Cost effective**: 400 tokens vs 8,500 tokens = 95% reduction
- ✅ **Nearly free**: DeepSeek extraction costs $0.0001 per query

#### Automatic Memory Creation

After each response, DeepSeek analyzes for memorable moments:

```python
# After Claude generates response
def handle_response(response_text, chapter, response_num):
    # 1. Show response immediately
    print(response_text)
    save_response(response_text)

    # 2. Analyze in background (1-response-behind)
    def analyze_in_background():
        # Analyze for scene context
        response_analyzer.analyze_response(response_text, chapter, response_num)

        # NEW: Extract memorable moments
        num_memories = memory_manager.analyze_response_for_memories(
            response_text, chapter, response_num
        )

        if num_memories > 0:
            print(f"💾 Created {num_memories} new memories")

    # Run in background
    threading.Thread(target=analyze_in_background, daemon=True).start()
```

**Example memorable moment extraction**:

```
Response: "Marcus and Lily had their first argument. She accused him of prioritizing work over their relationship. 'I feel like I'm competing with your job,' she said, tears in her eyes. Marcus realized she was right."

DeepSeek extracts:
{
  "characters": ["Marcus", "Lily"],
  "type": "Conflict",
  "emotional_tone": "Tense, hurt, realization",
  "tags": ["#argument", "#lily", "#relationship_conflict", "#work_life_balance"],
  "content": "First serious argument. Lily felt neglected due to Marcus's work focus. Marcus realized she was right - he'd been prioritizing career over relationship.",
  "quote": "I feel like I'm competing with your job",
  "significance": 8,
  "location": "Marcus's Apartment"
}

Automatically added to both Marcus and Lily's memory banks!
```

#### Core Search Engine

```python
# src/search_system.py

class RPSearchEngine:
    """Comprehensive search engine for RP content"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.index = {}
        self.embeddings = {}  # For semantic search
        self._build_search_index()

    def _build_search_index(self):
        """Build searchable index of all content"""
        print("🔍 Building search index...")

        self.index = {
            "chapters": {},     # chapter_num -> {response_num -> text}
            "responses": {},    # response_num -> full text
            "entities": {},     # entity_name -> card content
            "by_character": {}, # character_name -> list of response_nums
            "by_location": {},  # location_name -> list of response_nums
            "by_tag": {},       # tag -> list of response_nums
            "dialogue": {},     # character_name -> list of (response_num, dialogue)
        }

        # Index all chapters
        for chapter_file in sorted(self.rp_dir.glob("chapters/*.md")):
            self._index_chapter(chapter_file)

        # Index entity cards
        for entity_file in self.rp_dir.glob("entities/*.md"):
            self._index_entity(entity_file)

        # Index state files
        self._index_state_files()

        print(f"✓ Indexed {len(self.index['responses'])} responses")
        print(f"✓ Indexed {len(self.index['entities'])} entities")
```

#### Full-Text Search

```python
def search_full_text(self, query, limit=10):
    """Full-text search across all content"""
    results = []

    # Search through responses
    for response_num, text in self.index["responses"].items():
        if query.lower() in text.lower():
            # Extract context around match
            preview = self._extract_context(text, query, context_words=50)

            results.append({
                "type": "response",
                "response_num": response_num,
                "chapter": self._get_chapter_for_response(response_num),
                "preview": preview,
                "full_text": text,
                "relevance": self._calculate_relevance(text, query)
            })

    # Search through entity cards
    for entity_name, card_text in self.index["entities"].items():
        if query.lower() in card_text.lower():
            preview = self._extract_context(card_text, query, context_words=30)

            results.append({
                "type": "entity",
                "entity_name": entity_name,
                "preview": preview,
                "full_text": card_text,
                "relevance": self._calculate_relevance(card_text, query)
            })

    # Sort by relevance
    results.sort(key=lambda r: -r["relevance"])

    return results[:limit]

def _extract_context(self, text, query, context_words=50):
    """Extract text around query match"""
    words = text.split()
    query_words = query.lower().split()

    # Find query position
    for i in range(len(words) - len(query_words) + 1):
        if " ".join(words[i:i+len(query_words)]).lower() == query.lower():
            # Found match, extract context
            start = max(0, i - context_words)
            end = min(len(words), i + len(query_words) + context_words)

            context = " ".join(words[start:end])

            # Highlight match
            context = context.replace(query, f"**{query}**")

            if start > 0:
                context = "..." + context
            if end < len(words):
                context = context + "..."

            return context

    return text[:200] + "..."

def _calculate_relevance(self, text, query):
    """Calculate relevance score"""
    # Simple relevance: count occurrences + position weight
    occurrences = text.lower().count(query.lower())
    position = text.lower().find(query.lower())

    # Earlier mentions = higher relevance
    position_score = 1.0 - (position / max(len(text), 1))

    return occurrences + position_score
```

#### Semantic Search

```python
def search_semantic(self, query, limit=10):
    """Semantic search using embeddings"""

    # Load or create embeddings
    if not self.embeddings:
        self._build_embeddings()

    # Get query embedding
    query_embedding = self._get_embedding(query)

    # Calculate similarity with all responses
    similarities = []

    for response_num, embedding in self.embeddings.items():
        similarity = self._cosine_similarity(query_embedding, embedding)

        if similarity > 0.3:  # Threshold
            similarities.append({
                "response_num": response_num,
                "similarity": similarity,
                "text": self.index["responses"][response_num]
            })

    # Sort by similarity
    similarities.sort(key=lambda s: -s["similarity"])

    return similarities[:limit]

def _build_embeddings(self):
    """Build embeddings for all responses"""
    # Use sentence-transformers or similar
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("🔍 Building semantic embeddings...")

    for response_num, text in self.index["responses"].items():
        # Truncate if too long
        truncated = text[:500]  # First 500 chars
        embedding = model.encode(truncated)
        self.embeddings[response_num] = embedding

    print(f"✓ Built embeddings for {len(self.embeddings)} responses")

def _get_embedding(self, text):
    """Get embedding for text"""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text)

def _cosine_similarity(self, a, b):
    """Calculate cosine similarity"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

#### Character-Specific Search

```python
def search_character_moments(self, character_name, moment_type=None, limit=10):
    """Find all scenes with a character"""

    # Get all responses with this character
    response_nums = self.index["by_character"].get(character_name, [])

    results = []

    for response_num in response_nums:
        text = self.index["responses"][response_num]

        # Extract character's content
        char_content = self._extract_character_content(text, character_name)

        result = {
            "response_num": response_num,
            "chapter": self._get_chapter_for_response(response_num),
            "preview": char_content[:200] + "...",
            "full_text": text
        }

        # Filter by moment type if specified
        if moment_type:
            scene_type = self._classify_scene_type(text)
            if scene_type == moment_type:
                results.append(result)
        else:
            results.append(result)

    return results[:limit]

def search_interactions(self, char_a, char_b, limit=10):
    """Find all interactions between two characters"""

    # Get responses with both characters
    scenes_a = set(self.index["by_character"].get(char_a, []))
    scenes_b = set(self.index["by_character"].get(char_b, []))

    # Intersection = scenes with both
    interaction_scenes = scenes_a & scenes_b

    results = []

    for response_num in sorted(interaction_scenes):
        text = self.index["responses"][response_num]

        # Extract interaction content
        interaction = self._extract_interaction(text, char_a, char_b)

        results.append({
            "response_num": response_num,
            "chapter": self._get_chapter_for_response(response_num),
            "preview": interaction[:200] + "...",
            "full_text": text
        })

    return results[:limit]

def _extract_interaction(self, text, char_a, char_b):
    """Extract portions where both characters interact"""
    # Find paragraphs mentioning both characters
    paragraphs = text.split('\n\n')

    interaction_parts = []
    for para in paragraphs:
        if char_a in para and char_b in para:
            interaction_parts.append(para)

    return "\n\n".join(interaction_parts)
```

#### Similarity Search

```python
def find_similar_scenes(self, response_num, num_results=5):
    """Find scenes similar to a given response"""

    if not self.embeddings:
        self._build_embeddings()

    # Get target embedding
    target_embedding = self.embeddings.get(response_num)
    if not target_embedding:
        return []

    # Calculate similarity with all other responses
    similarities = []

    for other_num, embedding in self.embeddings.items():
        if other_num == response_num:
            continue  # Skip self

        similarity = self._cosine_similarity(target_embedding, embedding)

        similarities.append({
            "response_num": other_num,
            "similarity": similarity,
            "chapter": self._get_chapter_for_response(other_num),
            "preview": self.index["responses"][other_num][:200] + "..."
        })

    # Sort by similarity
    similarities.sort(key=lambda s: -s["similarity"])

    return similarities[:num_results]
```

#### Emotion-Based Search

```python
def search_by_emotion(self, emotion, limit=10):
    """Find scenes with specific emotional tone"""

    # Use semantic search with emotion query
    query = f"scene with {emotion} emotion, {emotion} feeling, {emotion} moment"

    results = self.search_semantic(query, limit=limit*2)

    # Filter and rank by emotion keywords
    emotion_keywords = {
        "romantic": ["love", "kiss", "heart", "intimate", "tender"],
        "tense": ["tension", "conflict", "argument", "fight", "angry"],
        "sad": ["sad", "cry", "tears", "grief", "loss"],
        "happy": ["happy", "joy", "laugh", "smile", "celebrate"],
        "mysterious": ["mystery", "secret", "hidden", "unknown", "strange"]
    }

    keywords = emotion_keywords.get(emotion.lower(), [emotion])

    # Score by keyword presence
    for result in results:
        keyword_count = sum(
            result["text"].lower().count(kw) for kw in keywords
        )
        result["emotion_score"] = keyword_count

    # Sort by emotion score
    results.sort(key=lambda r: -r["emotion_score"])

    return results[:limit]
```

### User Interface

```python
class SearchInterface:
    """User interface for search system"""

    def __init__(self, search_engine):
        self.engine = search_engine

    def search_command(self, args):
        """Handle /search command"""

        if not args:
            print("Usage: /search <query>")
            return

        query = " ".join(args)
        results = self.engine.search_full_text(query, limit=10)

        self._display_results(results, query)

    def _display_results(self, results, query):
        """Display search results"""
        if not results:
            print(f"No results found for: {query}")
            return

        print(f"\n🔍 SEARCH RESULTS FOR: {query}")
        print(f"Found {len(results)} results\n")
        print("="*80)

        for i, result in enumerate(results, 1):
            if result["type"] == "response":
                print(f"[{i}] Response {result['response_num']} (Chapter {result['chapter']})")
            elif result["type"] == "entity":
                print(f"[{i}] Entity Card: {result['entity_name']}")

            print(f"    {result['preview']}")
            print("-"*80)

        print("\nCommands:")
        print("  /search-view <num>  - View full result")
        print("  /search-next        - Show more results")
```

### Configuration

```yaml
search_system:
  enabled: true

  # DeepSeek Memory System
  deepseek_memories:
    enabled: true
    auto_create_memories: true  # Automatically extract memorable moments
    memory_extraction_in_background: true  # Don't block responses
    max_memories_per_query: 5  # Load at most 5 memories at once
    min_significance_threshold: 5  # Only create memories with significance >= 5

  # Indexing
  auto_build_index: true
  rebuild_index_on_startup: false  # Only rebuild if needed
  index_update_frequency: "after_each_response"  # or "manual"

  # Search types
  enable_full_text: true
  enable_semantic: true
  enable_character_search: true
  enable_emotion_search: true

  # Semantic search
  use_sentence_transformers: true
  embedding_model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.3

  # Performance
  max_results_default: 10
  cache_embeddings: true
```

### User Commands

```bash
# Memory commands (NEW!)
/memories Marcus                # View all Marcus's memories
/memories Marcus Lily           # View memories involving both Marcus and Lily
/memory MEM-045                 # View specific memory by ID
/memory-search "first date"     # Search memories for content
/memory-stats                   # Show memory statistics (how many per character)

# Full-text search
/search "Marcus angry"

# Character-specific
/search-character Marcus emotional
/search-character Marcus action

# Interaction search
/search-interaction Marcus Lily

# Similar scenes
/find-similar 245

# Emotion-based
/search-emotion romantic
/search-emotion tense

# Semantic search
/search-semantic "character feeling lost"

# View result
/search-view 3
```

### Benefits

**DeepSeek Memory System**:
- ✅ **Infinite Scalability**: Works even after 500+ memories per character
- ✅ **95% Token Reduction**: Load 400 tokens instead of 8,500 tokens
- ✅ **Automatic Creation**: Memorable moments extracted automatically
- ✅ **Contextual Relevance**: Only load memories that matter to current conversation
- ✅ **Rich Callbacks**: Includes quotes, timestamps, significance for powerful callbacks
- ✅ **Nearly Free**: DeepSeek extraction costs ~$0.0001 per query
- ✅ **Background Processing**: Memory creation happens while user types (no blocking)

**Traditional Search**:
- **Consistency**: Quick fact verification
- **Callbacks**: Easy to reference earlier moments
- **Character Voice**: Find dialogue examples
- **Plot Tracking**: Find thread origins
- **Quality**: Better informed responses

---

## 2. Story Health Dashboard

### Problem Statement

Hard to get an overview of story state. Want to see at a glance: plot threads, character screen time, pacing, scene variety, token usage, etc. Like the memory view (keybind), but for story health metrics.

### Proposed Solution

Create a comprehensive dashboard that shows:
- Active plot threads and stale threads
- Character screen time distribution
- Pacing and tension metrics
- Scene variety
- Token usage and cache efficiency
- Timeline status

**Display Method**: Keybind overlay (like memories view), not always visible

### Implementation

```python
# src/dashboard.py

class StoryHealthDashboard:
    """Comprehensive dashboard for story health metrics"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir

        # Load all tracking systems
        self.plot_tracker = PlotThreadTracker(rp_dir)
        self.timeline = Timeline(rp_dir)
        self.pacing = PacingMonitor(rp_dir)
        self.scene_history = SceneHistory(rp_dir)
        self.search_engine = RPSearchEngine(rp_dir)

    def generate_dashboard(self, lookback=20):
        """Generate comprehensive dashboard"""
        lines = []

        lines.append("="*80)
        lines.append(" STORY HEALTH DASHBOARD ".center(80))
        lines.append("="*80)
        lines.append("")

        # === PLOT THREADS ===
        lines.extend(self._plot_threads_section())
        lines.append("")

        # === CHARACTER SCREEN TIME ===
        lines.extend(self._character_screentime_section(lookback))
        lines.append("")

        # === PACING & TENSION ===
        lines.extend(self._pacing_section())
        lines.append("")

        # === SCENE VARIETY ===
        lines.extend(self._scene_variety_section(lookback))
        lines.append("")

        # === TIMELINE ===
        lines.extend(self._timeline_section())
        lines.append("")

        # === TOKEN USAGE ===
        lines.extend(self._token_usage_section())
        lines.append("")

        # === OVERALL HEALTH SCORE ===
        lines.extend(self._health_score_section())
        lines.append("")

        lines.append("="*80)

        return "\n".join(lines)

    def _plot_threads_section(self):
        """Plot threads section"""
        lines = ["## 📖 PLOT THREADS"]

        active_threads = self.plot_tracker.get_active_threads()
        resolved_threads = self.plot_tracker.get_resolved_threads()

        lines.append(f"  Active: {len(active_threads)}")
        lines.append(f"  Resolved: {len(resolved_threads)}")

        # Check for stale threads
        stale_threads = self.plot_tracker.check_stale_threads(
            self._get_current_response_num(),
            threshold=20
        )

        if stale_threads:
            lines.append(f"  ⚠️  Stale: {len(stale_threads)}")
            lines.append("")
            lines.append("  Stale threads (neglected >20 responses):")
            for thread, responses_since in stale_threads[:3]:
                lines.append(f"    - {thread.description}")
                lines.append(f"      ({responses_since} responses ago, priority: {thread.priority})")

        return lines

    def _character_screentime_section(self, lookback):
        """Character screen time section"""
        lines = [f"## 👥 CHARACTER SCREEN TIME (Last {lookback} responses)"]

        # Calculate screen time
        screentime = self._calculate_screen_time(lookback)

        if not screentime:
            lines.append("  No data yet")
            return lines

        # Sort by screen time
        sorted_chars = sorted(screentime.items(), key=lambda x: -x[1])

        # Display bar chart
        max_count = max(screentime.values()) if screentime else 1

        for char, count in sorted_chars[:10]:  # Top 10
            bar_length = int((count / max_count) * 30)
            bar = "█" * bar_length
            lines.append(f"  {char:20s} {bar} {count}")

        # Flag neglected characters
        neglected = [char for char, count in sorted_chars if count < 2]
        if neglected and len(sorted_chars) > 5:
            lines.append(f"\n  ⚠️  Neglected characters: {', '.join(neglected[:5])}")

        return lines

    def _pacing_section(self):
        """Pacing and tension section"""
        lines = ["## 📊 PACING & TENSION"]

        if not self.pacing.tension_history:
            lines.append("  No data yet")
            return lines

        # Recent tension
        recent_tension = [t[1] for t in self.pacing.tension_history[-10:]]
        avg_tension = np.mean(recent_tension)
        tension_variance = np.var(recent_tension)

        lines.append(f"  Average tension: {avg_tension:.1f}/10")
        lines.append(f"  Variance: {tension_variance:.2f} ({'flat' if tension_variance < 2.0 else 'varied'})")

        # Check for flat pacing
        flat_info = self.pacing.detect_flat_pacing(lookback=15)
        if flat_info["flat"]:
            lines.append(f"  ⚠️  Pacing flat for {flat_info['responses_flat']} responses")
            lines.append(f"     Suggestion: {flat_info['suggestion']}")

        # Mini tension graph
        lines.append("\n  Recent tension curve:")
        lines.append(self._mini_tension_graph(recent_tension))

        return lines

    def _mini_tension_graph(self, tension_values):
        """Generate mini ASCII tension graph"""
        graph_lines = []

        for level in range(10, 0, -2):
            line = f"  {level:2d} |"
            for val in tension_values:
                if val >= level:
                    line += "█"
                else:
                    line += " "
            graph_lines.append(line)

        graph_lines.append("     +" + "-" * len(tension_values))

        return "\n".join(graph_lines)

    def _scene_variety_section(self, lookback):
        """Scene variety section"""
        lines = [f"## 🎬 SCENE VARIETY (Last {lookback//2} responses)"]

        if len(self.scene_history.scenes) < 3:
            lines.append("  No data yet")
            return lines

        # Get scene distribution
        distribution = self.scene_history.get_scene_distribution(lookback=lookback//2)

        if not distribution:
            lines.append("  No data yet")
            return lines

        # Display distribution
        for scene_type, count in sorted(distribution.items(), key=lambda x: -x[1]):
            lines.append(f"  {scene_type:15s}: {count}")

        # Check for stagnation
        stagnation = self.scene_history.check_for_stagnation(lookback=5)
        if stagnation["stagnant"]:
            lines.append(f"\n  ⚠️  Scene stagnation detected")
            if "type" in stagnation:
                lines.append(f"     Last {stagnation['count']} scenes: {stagnation['type']}")
            lines.append(f"     {stagnation['suggestion']}")

        return lines

    def _timeline_section(self):
        """Timeline section"""
        lines = ["## ⏰ TIMELINE"]

        if self.timeline.current_time:
            lines.append(f"  Current time: {self._format_time(self.timeline.current_time)}")

            if self.timeline.story_start_time:
                elapsed = self.timeline.current_time - self.timeline.story_start_time
                lines.append(f"  Time elapsed: {self._format_duration(elapsed)}")
        else:
            lines.append("  Current time: Not yet established")

        # Recent events
        recent_events = self._get_recent_timeline_events(hours=24)
        if recent_events:
            lines.append(f"\n  Recent events (last 24h in-universe):")
            for event in recent_events[:3]:
                time_str = self._format_time(event.timestamp)
                lines.append(f"    - {time_str}: {event.description[:50]}")

        return lines

    def _token_usage_section(self):
        """Token usage section"""
        lines = ["## 💰 TOKEN USAGE"]

        # Load usage stats from logs
        usage_stats = self._load_usage_stats()

        if not usage_stats:
            lines.append("  No usage data available")
            return lines

        lines.append(f"  Total input tokens: {usage_stats['total_input']:,}")
        lines.append(f"  Total output tokens: {usage_stats['total_output']:,}")

        if "cache_read_tokens" in usage_stats:
            cache_hit_rate = usage_stats['cache_read_tokens'] / max(usage_stats['total_input'], 1)
            lines.append(f"  Cache hit rate: {cache_hit_rate:.1%}")
            lines.append(f"  Cache savings: {usage_stats['cache_read_tokens']:,} tokens")

        # Estimated cost (approximate)
        input_cost = (usage_stats['total_input'] / 1_000_000) * 3.0  # $3/M tokens
        output_cost = (usage_stats['total_output'] / 1_000_000) * 15.0  # $15/M tokens
        total_cost = input_cost + output_cost

        lines.append(f"\n  Estimated cost: ${total_cost:.2f}")

        return lines

    def _health_score_section(self):
        """Overall health score"""
        lines = ["## 🎯 OVERALL STORY HEALTH"]

        # Calculate health score (0-100)
        scores = {
            "plot_health": self._calculate_plot_health(),
            "pacing_health": self._calculate_pacing_health(),
            "variety_health": self._calculate_variety_health(),
            "timeline_health": self._calculate_timeline_health()
        }

        overall = sum(scores.values()) / len(scores)

        # Health indicator
        if overall >= 80:
            indicator = "🟢 EXCELLENT"
        elif overall >= 60:
            indicator = "🟡 GOOD"
        elif overall >= 40:
            indicator = "🟠 NEEDS ATTENTION"
        else:
            indicator = "🔴 POOR"

        lines.append(f"  {indicator}: {overall:.0f}/100")
        lines.append("")

        # Component scores
        for component, score in scores.items():
            name = component.replace("_", " ").title()
            bar_length = int(score / 100 * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"  {name:20s} {bar} {score:.0f}/100")

        return lines

    def _calculate_plot_health(self):
        """Calculate plot health score"""
        active = len(self.plot_tracker.get_active_threads())
        stale = len(self.plot_tracker.check_stale_threads(
            self._get_current_response_num(), threshold=20
        ))

        if active == 0:
            return 50  # Neutral - no threads yet

        stale_ratio = stale / max(active, 1)

        # Health decreases with more stale threads
        return max(0, 100 - (stale_ratio * 100))

    def _calculate_pacing_health(self):
        """Calculate pacing health score"""
        if not self.pacing.tension_history:
            return 100  # No data = neutral

        recent_tension = [t[1] for t in self.pacing.tension_history[-15:]]
        variance = np.var(recent_tension)

        # Good pacing has variance between 2-6
        if 2 <= variance <= 6:
            return 100
        elif variance < 2:
            # Too flat
            return max(0, 50 - (2 - variance) * 25)
        else:
            # Too varied/chaotic
            return max(50, 100 - (variance - 6) * 10)

    def _calculate_variety_health(self):
        """Calculate scene variety health score"""
        if len(self.scene_history.scenes) < 5:
            return 100  # Not enough data

        stagnation = self.scene_history.check_for_stagnation(lookback=5)

        if not stagnation["stagnant"]:
            return 100

        if stagnation.get("severity") == "high":
            return 40
        elif stagnation.get("severity") == "moderate":
            return 70
        else:
            return 85

    def _calculate_timeline_health(self):
        """Calculate timeline health score"""
        # Check for inconsistencies
        inconsistencies = []

        for event in self.timeline.events[-20:]:
            incons = self.timeline.detect_time_inconsistencies(event)
            inconsistencies.extend(incons)

        # Major inconsistencies hurt health more
        major = sum(1 for i in inconsistencies if i["severity"] == "major")
        moderate = sum(1 for i in inconsistencies if i["severity"] == "moderate")

        score = 100 - (major * 20) - (moderate * 10)

        return max(0, score)

    def _calculate_screen_time(self, lookback):
        """Calculate character screen time"""
        screentime = {}

        # Get recent responses
        recent_responses = self._get_recent_responses(lookback)

        for response in recent_responses:
            # Extract characters mentioned
            characters = self._extract_characters_from_response(response)

            for char in characters:
                screentime[char] = screentime.get(char, 0) + 1

        return screentime
```

### Keybind Integration

```python
# In TUI, add keybind

def handle_keypress(key):
    """Handle special keypresses"""

    if key == 'H':  # Health dashboard
        dashboard = StoryHealthDashboard(rp_dir)
        print("\033[2J\033[H")  # Clear screen
        print(dashboard.generate_dashboard())
        input("\nPress Enter to continue...")
        # Redraw TUI

    elif key == 'M':  # Memories (existing)
        show_memories()

    elif key == 'T':  # Timeline
        show_timeline()

    elif key == 'P':  # Plot threads
        show_plot_threads()

# Display help
print("📊 Press 'H' for Story Health Dashboard")
```

### Configuration

```yaml
story_dashboard:
  enabled: true

  # What to include
  sections:
    - plot_threads
    - character_screentime
    - pacing
    - scene_variety
    - timeline
    - token_usage
    - health_score

  # Lookback periods
  character_screentime_lookback: 20
  scene_variety_lookback: 10

  # Health score weights
  health_weights:
    plot_health: 0.3
    pacing_health: 0.3
    variety_health: 0.2
    timeline_health: 0.2
```

### Benefits

- **Overview**: See story health at a glance
- **Early Warning**: Identify problems before they become serious
- **Analytics**: Understand story patterns
- **Motivation**: See progress and improvements
- **Focus**: Know what needs attention

---

## 3. Smart Entity Management - Dynamic Personality-Driven Relationships

### Problem Statement

Relationships between characters need to evolve based on interactions, but tracking this manually is tedious. Generic "affection/trust" metrics don't capture individual personality - why does Marcus like honesty but Joe hates sarcasm?

**User's Insight from AI Dungeon**: Each character should have personality-based preferences (likes/dislikes/hates) with point values. Relationship score (-100 to +100) changes when user triggers preferences. Only tier changes matter long-term - minor fluctuations are temporary reactions.

### Proposed Solution

Implement **personality-driven relationship system**:
- **Character preferences**: Each character has likes/dislikes/hates with point values
- **Numeric score**: -100 to +100 relationship score
- **Tier system**: Enemy, Hostile, Stranger, Acquaintance, Friend, Close Friend, Best Friend
- **Smart filtering**: Only tier changes are significant (stored in memory/N+1)
- **Temporary reactions**: Minor changes don't persist (Joe grumpy for a moment ≠ relationship change)
- **DeepSeek analysis**: Automatically detects when preferences are triggered
- **Behavior guidance**: How character acts at each tier

### Implementation

#### Character Relationship Preferences Card

Each character has a separate relationship preferences file:

```markdown
# Marcus Smith - Relationship Preferences

## PERSONALITY-BASED PREFERENCES

### LIKES (Positive Point Values)
- **Honesty** (+10): Marcus values directness and truthfulness
- **Vulnerability** (+8): Opening up emotionally resonates with him
- **Deep conversations** (+6): Intellectual and emotional depth matters
- **Coffee culture** (+4): Shares his passion for good coffee
- **Career ambition** (+5): Respects drive and goals
- **Humor** (+3): Appreciates good jokes and levity
- **Reliability** (+7): Values people who keep their word

### DISLIKES (Negative Point Values)
- **Dishonesty** (-15): Even white lies bother him
- **Superficiality** (-8): Dislikes shallow interactions
- **Flakiness** (-10): Canceling plans or being unreliable frustrates him
- **Arrogance** (-12): Can't stand people who look down on others
- **Avoidance** (-6): Wants issues addressed, not ignored
- **Rushing intimacy** (-5): Needs time to build trust

### HATES (Major Negative Values)
- **Betrayal** (-40): Unforgivable breach of trust
- **Controlling behavior** (-35): Values his autonomy highly
- **Dismissiveness** (-30): Being brushed off or ignored deeply hurts
- **Public humiliation** (-25): Embarrassment in front of others

---

## CURRENT RELATIONSHIPS

### With Protagonist
**Score**: 45/100
**Tier**: Friend (31-60)
**Status**: Growing friendship, comfortable but not deeply intimate yet

**Tier History**:
- **Chapter 1** (Response 1): Started at 0 (Stranger)
- **Chapter 3** (Response 65): Reached 31 (→ Acquaintance tier)
- **Chapter 5** (Response 134): Reached 45 (→ Friend tier)

**Only major tier changes are stored - minor fluctuations don't persist**
```

```markdown
# Joe - Relationship Preferences

## PERSONALITY-BASED PREFERENCES

### LIKES
- **Directness** (+8): No beating around the bush
- **Respect for authority** (+10): Values hierarchy
- **Physical strength** (+5): Admires toughness
- **Loyalty** (+12): Highly values faithful people

### DISLIKES
- **Sarcasm** (-10): Takes things literally, sarcasm annoys him
- **Weakness** (-8): Looks down on emotional vulnerability
- **Questioning authority** (-15): Challenges to hierarchy bother him
- **Tardiness** (-6): Values punctuality

### HATES
- **Disrespect** (-35): Direct insults or mockery
- **Cowardice** (-30): Running from confrontation
- **Disloyalty** (-40): Betraying your group

---

## CURRENT RELATIONSHIPS

### With Protagonist
**Score**: -15/100
**Tier**: Hostile (-29 to -10)
**Status**: Cold, unfriendly. Avoids protagonist when possible.

**Tier History**:
- **Chapter 1** (Response 1): Started at 0 (Stranger)
- **Chapter 2** (Response 43): Dropped to -15 (→ Hostile tier) after protagonist used sarcasm repeatedly
```

#### Dynamic Personality-Driven Relationship System

```python
# src/dynamic_relationships.py

class DynamicRelationshipSystem:
    """Personality-driven relationship system with tiers"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.deepseek = DeepSeekClient()
        self.preferences_dir = rp_dir / "relationships" / "preferences"
        self.scores_file = rp_dir / "state" / "relationship_scores.json"

        # Tier definitions
        self.tiers = {
            "Enemy": (-100, -30),
            "Hostile": (-29, -10),
            "Stranger": (-9, 10),
            "Acquaintance": (11, 30),
            "Friend": (31, 60),
            "Close Friend": (61, 80),
            "Best Friend": (81, 100)
        }

        # Behavior guidance for each tier
        self.tier_behaviors = {
            "Enemy": "Hostile, antagonistic. Actively works against user. Insults, undermines.",
            "Hostile": "Cold, unfriendly. Avoids interaction. Short, curt responses. Visible dislike.",
            "Stranger": "Neutral, cautious. Polite but distant. No personal investment.",
            "Acquaintance": "Friendly but surface-level. Pleasant interactions but no deep trust.",
            "Friend": "Warm, supportive. Shares some personal info. Enjoys user's company.",
            "Close Friend": "Very comfortable. Vulnerable. Seeks out user's company. Deep trust.",
            "Best Friend": "Complete trust. Deep emotional bond. Always has user's back. Like family."
        }

        self.relationship_scores = self._load_scores()

    def analyze_interaction(self, response_text, characters_in_scene, chapter, response_num):
        """Analyze interaction for relationship changes (runs in background)"""

        tier_changes = []

        for character in characters_in_scene:
            # Skip if character doesn't have preferences file
            prefs_file = self.preferences_dir / f"{character}_preferences.md"
            if not prefs_file.exists():
                continue

            # Load character's preferences
            preferences = self._load_preferences(character)

            # Get current score
            current_score = self.relationship_scores.get(character, 0)
            current_tier = self._get_tier(current_score)

            # DeepSeek analyzes against preferences
            analysis = self._analyze_against_preferences(
                response_text,
                character,
                preferences,
                current_score
            )

            if analysis["score_change"] != 0:
                new_score = self._clamp(current_score + analysis["score_change"], -100, 100)
                new_tier = self._get_tier(new_score)

                self.relationship_scores[character] = new_score

                # Tier changed? THIS is significant!
                if new_tier != current_tier:
                    print(f"⚠️ RELATIONSHIP TIER CHANGE: {character}")
                    print(f"   {current_tier} ({current_score}) → {new_tier} ({new_score})")
                    print(f"   Reason: {analysis['reason']}")

                    tier_change = {
                        "character": character,
                        "old_tier": current_tier,
                        "new_tier": new_tier,
                        "old_score": current_score,
                        "new_score": new_score,
                        "reason": analysis["reason"],
                        "triggered": analysis["triggered"]
                    }

                    tier_changes.append(tier_change)

                    # Add to character's memory bank (permanent record)
                    self._add_tier_change_memory(
                        character,
                        tier_change,
                        chapter,
                        response_num
                    )

                else:
                    # Minor change - just log, don't persist
                    print(f"📊 {character}: {current_score} → {new_score} (still {current_tier})")
                    print(f"   Triggered: {', '.join(analysis['triggered'])}")
                    # Temporary reaction shown in this response, but not stored

        self._save_scores()
        return tier_changes

    def _analyze_against_preferences(self, response_text, character, preferences, current_score):
        """DeepSeek analyzes interaction against character's personality preferences"""

        current_tier = self._get_tier(current_score)

        prompt = f"""Analyze this interaction for relationship score changes based on character's personality:

**Character**: {character}
**Current Relationship**: {current_score}/100 ({current_tier})

**Character's Personality Preferences**:

LIKES (positive points):
{self._format_preferences(preferences['likes'])}

DISLIKES (negative points):
{self._format_preferences(preferences['dislikes'])}

HATES (major negative points):
{self._format_preferences(preferences['hates'])}

**Interaction/Response**:
{response_text}

**Task**: Did the user's actions, words, or behavior trigger any of {character}'s preferences?

Consider:
- What did the user say or do?
- Does it align with what {character} likes, dislikes, or hates?
- Multiple preferences can be triggered in one interaction
- Be realistic - not every action triggers preferences

Return JSON:
{{
  "triggered": ["list of triggered preferences with points, e.g., 'Honesty (+10)', 'Sarcasm (-10)'"],
  "score_change": sum_of_all_triggered_points,
  "reason": "1-2 sentence explanation of what the user did and why it matters to {character}",
  "temp_reaction": "how {character} reacts in the moment (shown in response but not stored)"
}}

If nothing triggered: {{"triggered": [], "score_change": 0, "reason": "No preferences triggered", "temp_reaction": "Normal interaction"}}
"""

        result = self.deepseek.query(prompt)
        return json.loads(result)

    def get_relationship_context(self, character):
        """Get relationship context for N+1 prompt (only if tier changed recently)"""

        score = self.relationship_scores.get(character, 0)
        tier = self._get_tier(score)

        # Check if tier changed in last 5 responses
        recent_change = self._check_recent_tier_change(character, responses=5)

        if recent_change:
            # Include the tier change context
            return f"""
## RELATIONSHIP STATUS: {character}

⚠️ RECENT TIER CHANGE:
- **Was**: {recent_change['old_tier']} ({recent_change['old_score']}/100)
- **Now**: {recent_change['new_tier']} ({recent_change['new_score']}/100)
- **Why**: {recent_change['reason']}
- **When**: {recent_change['chapter']}, Response {recent_change['response_num']}

**How {character} now behaves**: {self.tier_behaviors[tier]}

**This tier change affects how {character} interacts with the user in this response.**
"""
        else:
            # No recent change - just current status (minimal)
            return f"""
## RELATIONSHIP STATUS: {character}
**Tier**: {tier} ({score}/100)
**Behavior**: {self.tier_behaviors[tier]}
"""

    def _get_tier(self, score):
        """Get tier name from score"""
        for tier_name, (min_score, max_score) in self.tiers.items():
            if min_score <= score <= max_score:
                return tier_name
        return "Stranger"  # Fallback

    def _format_preferences(self, prefs_dict):
        """Format preferences for prompt"""
        return "\n".join([f"- {pref}: {points} points" for pref, points in prefs_dict.items()])

    def _add_tier_change_memory(self, character, tier_change, chapter, response_num):
        """Add tier change to character's memory bank (uses NPCMemoryManager)"""

        memory_manager = NPCMemoryManager(self.rp_dir)

        memory_data = {
            'timestamp': f"Chapter {chapter}, Response {response_num}",
            'location': 'N/A',  # Tier changes aren't location-specific
            'characters': [character, "User"],
            'type': 'Relationship Tier Change',
            'emotional_tone': 'Significant',
            'tags': ['#relationship_change', f'#{tier_change["new_tier"].lower()}', '#tier_shift'],
            'content': f"Relationship tier changed from {tier_change['old_tier']} to {tier_change['new_tier']}. {tier_change['reason']} Triggered by: {', '.join(tier_change['triggered'])}",
            'quote': 'N/A',
            'significance': 10  # Tier changes are always highly significant
        }

        memory_manager.add_memory(character, memory_data)

        print(f"💾 Added tier change memory for {character}")

    def _clamp(self, value, min_val, max_val):
        """Clamp value between min and max"""
        return max(min_val, min(max_val, value))
```

#### Example: Dynamic Relationship in Action

**Scenario**: User is sarcastic to Joe while Marcus is present

```python
# User says: "Yeah, sure Joe, whatever you say (rolls eyes)"

# DeepSeek analyzes against preferences:

# === JOE ===
# Preferences triggered: "Sarcasm (-10)", "Disrespect (-35)"
# Score change: -45 points
# Joe: 0 → -45 (Stranger → Enemy tier!)

⚠️ RELATIONSHIP TIER CHANGE: Joe
   Stranger (0) → Enemy (-45)
   Reason: User was openly sarcastic and disrespectful to Joe. Joe takes things literally
   and hates being mocked.
   Triggered: Sarcasm (-10), Disrespect (-35)

# THIS gets stored in Joe's memory bank
# THIS gets included in N+1 analysis (tier changed!)

# === MARCUS ===
# Preferences triggered: "Humor (+3)" (saw the sarcasm as humor)
# Score change: +3 points
# Marcus: 45 → 48 (Still Friend tier, no change)

📊 Marcus: 45 → 48 (still Friend)
   Triggered: Humor (+3)

# Minor change - just temporary reaction, NOT stored
# NOT included in N+1 (tier didn't change)
```

**Next Response (N+1)**:

Claude receives:
```markdown
## RELATIONSHIP STATUS: Joe

⚠️ RECENT TIER CHANGE:
- **Was**: Stranger (0/100)
- **Now**: Enemy (-45/100)
- **Why**: User was openly sarcastic and disrespectful to Joe. Joe takes things literally and hates being mocked.
- **When**: Chapter 4, Response 87

**How Joe now behaves**: Hostile, antagonistic. Actively works against user. Insults, undermines.

**This tier change affects how Joe interacts with the user in this response.**

## RELATIONSHIP STATUS: Marcus
**Tier**: Friend (48/100)
**Behavior**: Warm, supportive. Shares some personal info. Enjoys user's company.
```

**Claude's response** reflects this:
> Joe glares at you, his jaw clenched. "You think you're funny?" he snaps, stepping closer with clear hostility. Marcus quickly steps between you, hands raised. "Hey, let's all just calm down—" But Joe's already turning away, muttering something under his breath about "disrespectful punks."

**Perfect!** Joe's tier change created real consequences. Marcus didn't change tiers, so just normal friendly behavior.

#### Integration with Background Analysis

```python
# After Claude generates response (runs in background, 1-response-behind)

def analyze_in_background(response_text, chapter, response_num):
    # 1. Scene analysis (already implemented)
    response_analyzer.analyze_response(response_text, chapter, response_num)

    # 2. Memory extraction (already implemented)
    memory_manager.analyze_response_for_memories(response_text, chapter, response_num)

    # 3. NEW: Relationship analysis
    characters_in_scene = response_analyzer.last_analysis["characters"]["in_scene"]
    tier_changes = relationship_system.analyze_interaction(
        response_text,
        characters_in_scene,
        chapter,
        response_num
    )

    if tier_changes:
        print(f"💔 {len(tier_changes)} relationship tier(s) changed")
```

### Configuration

```yaml
dynamic_relationships:
  enabled: true

  # Analysis
  analyze_in_background: true  # Don't block responses
  use_deepseek: true  # Analyze against personality preferences

  # Filtering
  only_store_tier_changes: true  # Minor fluctuations not stored
  tier_change_lookback: 5  # Include tier changes from last 5 responses in N+1

  # Tier definitions
  tiers:
    Enemy: [-100, -30]
    Hostile: [-29, -10]
    Stranger: [-9, 10]
    Acquaintance: [11, 30]
    Friend: [31, 60]
    Close Friend: [61, 80]
    Best Friend: [81, 100]

  # Starting values
  default_starting_score: 0  # Everyone starts as Stranger
```

### User Commands

```bash
/relationships                  # Show all character relationships with tiers
/relationship Marcus            # Show Marcus's relationship score and tier
/relationship-history Marcus    # Show tier change history
/preferences Marcus             # View Marcus's likes/dislikes/hates
```

### Benefits

- ✅ **Personality-Driven**: Based on who the character actually is, not generic metrics
- ✅ **Clear & Intuitive**: -100 to +100 scale with named tiers
- ✅ **Memory Efficient**: Only tier changes persist (not every +3/-5 fluctuation)
- ✅ **Contextual**: Tier changes included in N+1 for immediate impact
- ✅ **Automatic**: DeepSeek analyzes in background, no manual tracking
- ✅ **Natural Evolution**: Characters react based on their values
- ✅ **Real Consequences**: Tier changes have immediate behavioral impact
- ✅ **Nearly Free**: DeepSeek analysis costs ~$0.0001 per response
- ✅ **Integrates with Memory System**: Tier changes stored as significant memories

---

## 4. Prompt Templates & Macros

### Problem Statement

Different RP settings (grimdark fantasy vs slice-of-life vs action-adventure) need different narrative approaches. Manually adjusting tone/style for each response is tedious. Need system to automatically or easily apply setting-appropriate prompts.

### Proposed Solution

Two approaches (can use both):

1. **Setting-Based Auto-Selection**: System reads RP setting and automatically applies appropriate template
2. **Modular Mix-and-Match**: User picks tone, pacing, description style, etc. separately

### Implementation

#### Approach 1: Setting-Based Templates

```python
# src/prompt_templates.py

class PromptTemplateManager:
    """Manage prompt templates for different settings"""

    def __init__(self):
        self.templates = {
            "grimdark_fantasy": {
                "tone": "Dark, brutal, and morally ambiguous. No guaranteed happy endings.",
                "style": "Gritty, visceral descriptions. Show harsh realities. Moral complexity.",
                "pacing": "Tense, high stakes. Actions have serious consequences.",
                "content": "Mature themes, violence, difficult choices",
                "narrative_voice": "Third person with ominous undertones",
                "guidance": "Embrace darkness. Show cost of choices. No plot armor."
            },

            "slice_of_life": {
                "tone": "Light, heartwarming, focus on daily life and relationships",
                "style": "Gentle, detailed descriptions. Emphasis on mundane beauty.",
                "pacing": "Relaxed, contemplative. Small moments matter.",
                "content": "Everyday situations, personal growth, relationships",
                "narrative_voice": "Warm, observant, intimate",
                "guidance": "Find beauty in ordinary. Slow down. Character depth over plot."
            },

            "action_adventure": {
                "tone": "Exciting, dynamic, heroic adventure",
                "style": "Vivid action descriptions. Bold, dramatic scenes.",
                "pacing": "Fast-paced with breathing moments. Keep momentum.",
                "content": "Action, adventure, challenges, triumphs",
                "narrative_voice": "Third person, energetic, descriptive",
                "guidance": "Keep moving forward. Big moments. Heroes can succeed."
            },

            "mystery_thriller": {
                "tone": "Tense, suspicious, atmospheric",
                "style": "Careful attention to details. Subtle clues. Atmosphere.",
                "pacing": "Measured build-up with tension spikes. Revelations matter.",
                "content": "Investigation, clues, red herrings, revelations",
                "narrative_voice": "Close third person, observant",
                "guidance": "Plant clues. Build suspense. Details matter."
            },

            "romantic": {
                "tone": "Emotional, intimate, hopeful",
                "style": "Focus on internal feelings, chemistry, tension",
                "pacing": "Varied - slow burns and intense moments",
                "content": "Relationships, emotions, connection, intimacy",
                "narrative_voice": "Close third person, emotionally attuned",
                "guidance": "Show chemistry. Internal conflict. Emotional truth."
            },

            "comedy": {
                "tone": "Light, humorous, fun",
                "style": "Witty dialogue, comedic timing, absurd situations",
                "pacing": "Quick, snappy. Land the jokes.",
                "content": "Humor, banter, ridiculous situations",
                "narrative_voice": "Playful, observant of absurdity",
                "guidance": "Commit to the bit. Timing matters. Have fun."
            }
        }

    def get_template(self, setting_type):
        """Get template for setting type"""
        return self.templates.get(setting_type, self.templates["action_adventure"])

    def format_template_for_prompt(self, template):
        """Format template as prompt section"""
        lines = [
            "## NARRATIVE GUIDANCE",
            "",
            f"**Tone**: {template['tone']}",
            f"**Style**: {template['style']}",
            f"**Pacing**: {template['pacing']}",
            f"**Content Focus**: {template['content']}",
            f"**Narrative Voice**: {template['narrative_voice']}",
            "",
            f"**Key Guidance**: {template['guidance']}",
            ""
        ]
        return "\n".join(lines)

    def auto_select_template(self, rp_overview_content):
        """Auto-select template based on RP Overview"""

        # Extract genre/setting from RP Overview
        genre = self._extract_genre(rp_overview_content)

        # Map to template
        genre_map = {
            "grimdark": "grimdark_fantasy",
            "fantasy": "action_adventure",
            "slice of life": "slice_of_life",
            "mystery": "mystery_thriller",
            "thriller": "mystery_thriller",
            "romance": "romantic",
            "comedy": "comedy",
            "action": "action_adventure"
        }

        for keyword, template_name in genre_map.items():
            if keyword in genre.lower():
                return self.get_template(template_name)

        # Default
        return self.get_template("action_adventure")

    def _extract_genre(self, overview_content):
        """Extract genre from RP Overview"""
        # Look for genre markers
        lines = overview_content.lower().split('\n')

        for line in lines:
            if "genre:" in line or "setting:" in line or "tone:" in line:
                return line.split(":", 1)[1].strip()

        return "action"  # Default
```

#### Approach 2: Modular System

```python
class ModularPromptBuilder:
    """Build prompts from individual modules"""

    def __init__(self):
        self.modules = {
            "tone": {
                "dark": "Maintain dark, serious tone. Show harsh realities.",
                "light": "Keep tone lighthearted and optimistic.",
                "balanced": "Mix serious and light moments appropriately.",
                "gritty": "Gritty, realistic tone. No sugarcoating.",
                "whimsical": "Whimsical, fantastical tone. Embrace magic and wonder.",
                "somber": "Somber, melancholy tone. Weight of world.",
                "upbeat": "Upbeat, energetic tone. Positive energy."
            },

            "pacing": {
                "fast": "Fast pacing. Keep action moving. Avoid lengthy descriptions.",
                "slow": "Slow, contemplative pacing. Take time with details and atmosphere.",
                "varied": "Vary pacing to match scene intensity.",
                "deliberate": "Deliberate, measured pacing. Every moment counts.",
                "breathless": "Rapid, intense pacing. No time to breathe."
            },

            "description_style": {
                "minimal": "Minimal description. Focus on action and dialogue.",
                "rich": "Rich, detailed descriptions. Paint vivid scenes.",
                "balanced": "Balance description with action and dialogue.",
                "atmospheric": "Focus on atmosphere and mood.",
                "visceral": "Visceral, sensory descriptions. Make reader feel it."
            },

            "dialogue_style": {
                "realistic": "Realistic dialogue with pauses, interruptions, subtext.",
                "stylized": "Stylized, quotable dialogue. More literary.",
                "minimal": "Minimal dialogue. Show through action.",
                "witty": "Clever, witty dialogue. Verbal sparring.",
                "natural": "Natural, flowing conversation."
            },

            "content_rating": {
                "pg": "Family-friendly content. No violence or adult themes.",
                "pg13": "Some violence and tension. No explicit content.",
                "mature": "Mature themes allowed. Violence, romance, dark topics.",
                "explicit": "Explicit content allowed. No restrictions."
            },

            "narrative_focus": {
                "character": "Focus on character development and relationships.",
                "plot": "Focus on plot progression and events.",
                "world": "Focus on world-building and atmosphere.",
                "balanced": "Balance character, plot, and world.",
                "emotion": "Focus on emotional journey and internal experience."
            },

            "scene_energy": {
                "high": "High energy scene. Dynamic, intense.",
                "low": "Low energy scene. Quiet, intimate.",
                "building": "Building energy. Escalating tension.",
                "climactic": "Climactic moment. Peak intensity.",
                "aftermath": "Aftermath/cooldown. Processing and reflection."
            }
        }

    def build_prompt(self, selected_modules):
        """Build prompt from selected modules"""
        prompt_parts = []

        for category, choice in selected_modules.items():
            if category in self.modules and choice in self.modules[category]:
                guidance = self.modules[category][choice]
                prompt_parts.append(f"**{category.replace('_', ' ').title()}**: {guidance}")

        if not prompt_parts:
            return ""

        prompt = "## NARRATIVE GUIDANCE\n\n" + "\n".join(prompt_parts) + "\n"
        return prompt
```

#### Scene-Specific Auto-Adjustment

```python
class DynamicTemplateAdjuster:
    """Automatically adjust template based on scene type"""

    def __init__(self, base_template):
        self.base_template = base_template

    def adjust_for_scene(self, scene_type):
        """Adjust template for specific scene type"""

        adjustments = {
            "romantic": {
                "tone": "light",
                "pacing": "slow",
                "description_style": "rich",
                "narrative_focus": "emotion"
            },
            "action": {
                "tone": "gritty",
                "pacing": "fast",
                "description_style": "visceral",
                "scene_energy": "high"
            },
            "introspection": {
                "tone": "somber",
                "pacing": "slow",
                "description_style": "minimal",
                "narrative_focus": "character"
            },
            "dialogue": {
                "pacing": "varied",
                "description_style": "minimal",
                "dialogue_style": "natural"
            }
        }

        # Get scene-specific adjustments
        scene_adj = adjustments.get(scene_type, {})

        # Merge with base template
        adjusted = self.base_template.copy()
        adjusted.update(scene_adj)

        return adjusted
```

### Configuration

```yaml
prompt_templates:
  enabled: true

  # Auto-selection
  auto_select_from_rp_overview: true
  base_setting: "action_adventure"  # Fallback if can't determine

  # Manual selection (overrides auto if set)
  manual_template: null  # Set to template name to override

  # Modular system
  use_modular: false  # Use modular instead of templates

  modules:  # Only used if use_modular: true
    tone: "balanced"
    pacing: "varied"
    description_style: "balanced"
    dialogue_style: "realistic"
    content_rating: "mature"
    narrative_focus: "balanced"

  # Scene-specific adjustments
  auto_adjust_for_scenes: true  # Automatically adjust based on scene type

  scene_overrides:
    romantic:
      tone: "light"
      pacing: "slow"
    action:
      tone: "gritty"
      pacing: "fast"
```

### User Commands

```bash
# Template commands
/template                        # Show current template
/template grimdark              # Switch to grimdark template
/template slice_of_life         # Switch to slice of life
/template list                   # List available templates

# Modular commands
/module tone dark               # Set tone module
/module pacing fast             # Set pacing module
/modules                        # Show all current modules
/modules reset                  # Reset to defaults
```

### Integration

```python
# In automation, before building prompt

template_manager = PromptTemplateManager()
modular_builder = ModularPromptBuilder()

if config["use_modular"]:
    # Use modular system
    template_prompt = modular_builder.build_prompt(config["modules"])
else:
    # Use template system
    if config["auto_select_from_rp_overview"]:
        # Auto-select from RP Overview
        rp_overview = load_rp_overview(rp_dir)
        template = template_manager.auto_select_template(rp_overview)
    else:
        # Use manual template
        template_name = config.get("manual_template", config["base_setting"])
        template = template_manager.get_template(template_name)

    # Adjust for scene type if enabled
    if config["auto_adjust_for_scenes"]:
        scene_type = detect_scene_type(user_message)
        adjuster = DynamicTemplateAdjuster(template)
        template = adjuster.adjust_for_scene(scene_type)

    template_prompt = template_manager.format_template_for_prompt(template)

# Add to prompt (TIER_2 or early in cached context)
prompt = f"{template_prompt}\n\n{rest_of_prompt}"
```

### Benefits

- **Consistency**: Maintain setting-appropriate tone
- **Ease**: Automatic template selection
- **Flexibility**: Override when needed
- **Scene-Aware**: Automatically adjust for scene type
- **Variety**: Many templates and modules to choose from

---

## Integration Summary

```python
# All systems working together

# 1. Search (always available)
search_engine = RPSearchEngine(rp_dir)
# User can search anytime with /search commands

# 2. Dashboard (keybind overlay)
dashboard = StoryHealthDashboard(rp_dir)
# Press 'H' to view dashboard

# 3. Relationship tracking (automatic)
relationship_tracker = RelationshipTracker(rp_dir)

# After each response
relationship_tracker.analyze_interaction(response, chapter, response_num)
# Entity cards automatically updated

# 4. Prompt templates (before each prompt)
template_manager = PromptTemplateManager()
template_prompt = template_manager.auto_select_template(rp_overview)

# Add to prompt
prompt = f"{template_prompt}\n\n{rest_of_prompt}"
```

---

## Priority & Implementation Order

**Recommended order:**

1. **DeepSeek Memory System** (NEW!) - Implement with Context Intelligence (2-3 days) **← HIGH PRIORITY**
   - Integrates seamlessly with DeepSeek Context Intelligence from `technical_improvements.md`
   - Solves memory bloat problem (95% token reduction)
   - Automatic memory creation in background
   - On-demand memory extraction
   - **Note**: Should be implemented as part of Phase 1 (DeepSeek Intelligence Layer)

2. **Prompt Templates** - Quick value, improves responses immediately (2 days)
   - Auto-select from RP Overview
   - Modular system for customization

3. **Relationship Tracking** - High impact on story depth (3-4 days)
   - Uses DeepSeek for automatic analysis
   - Updates entity cards automatically
   - Visual relationship graphs

4. **Traditional Search System** - Foundation for reference features (2-3 days) **← OPTIONAL**
   - Full-text search
   - Semantic search
   - Character/interaction search
   - **Note**: Less critical now that DeepSeek handles memory extraction

5. **Dashboard** - Uses other systems, implement last (2 days)
   - Story health metrics
   - Token usage tracking
   - Keybind overlay

**Total: ~2 weeks for full implementation**

**Critical insight**: DeepSeek Memory System should be implemented as part of the DeepSeek Intelligence Layer from `technical_improvements.md` (Phase 1). This gives you:
- 54% token reduction from context intelligence
- 95% memory token reduction from memory extraction
- Combined: ~70-75% total token reduction!

**Quick wins**:
- DeepSeek Memory System = immediate scalability + 95% memory token savings
- Prompt templates = improved response quality
- Traditional search system can wait (DeepSeek memories handle most use cases)
