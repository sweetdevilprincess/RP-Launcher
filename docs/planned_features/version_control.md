# Version Control & Alternative Responses

This document outlines features for managing story versions, branching narratives, and exploring alternative responses.

---

## 1. Story Checkpointing & Branching

### Problem Statement
Sometimes a story goes in the wrong direction, but there's no easy way to go back and try a different approach. You might want to explore "what if" scenarios or test different narrative choices without losing your current progress.

### Proposed Solution
Implement a Git-like branching system for story content that allows:
- Creating checkpoints at any point in the story
- Branching from checkpoints to explore alternatives
- Switching between branches
- Comparing different branches
- Merging elements between branches

### Use Cases
1. **Try different approaches**: "What if Marcus said yes instead of no?"
2. **Explore consequences**: See how different choices affect the story
3. **Safety net**: Revert if story goes wrong direction
4. **A/B testing**: Try dramatic vs subtle approach, pick better one
5. **Multiple endings**: Explore different story conclusions

### Implementation

#### Core Data Structures

```python
# src/story_version_control.py

class StoryCheckpoint:
    """Snapshot of complete story state at a point in time"""

    def __init__(self, checkpoint_id, chapter, response_num, description):
        self.id = checkpoint_id
        self.chapter = chapter
        self.response_num = response_num
        self.description = description
        self.timestamp = datetime.now()

        # Complete state snapshot
        self.snapshot = {
            "conversation_history": [],  # All messages up to this point
            "entity_cards": {},  # Copy of all entity cards
            "story_state": {},  # Copy of current_state.md
            "plot_threads": {},  # Active plot threads
            "knowledge_base": {},  # Knowledge base state
            "chapter_summaries": [],  # All chapter summaries
            "fact_database": {},  # Fact database state
            "relationship_states": {}  # Character relationships
        }

class StoryBranch:
    """A divergent timeline from a checkpoint"""

    def __init__(self, branch_id, name, parent_checkpoint):
        self.id = branch_id
        self.name = name
        self.parent = parent_checkpoint  # Which checkpoint this branched from
        self.responses = []  # Responses unique to this branch
        self.created = datetime.now()

        self.metadata = {
            "description": "",
            "tags": [],  # "romance", "action", "alternate_ending", etc.
            "last_updated": None,
            "response_count": 0
        }

class StoryVersionControl:
    """Main version control system"""

    def __init__(self, rp_dir):
        self.rp_dir = rp_dir
        self.checkpoints_dir = rp_dir / "state" / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)

        self.checkpoints = {}  # checkpoint_id -> StoryCheckpoint
        self.branches = {}  # branch_id -> StoryBranch
        self.current_branch = "main"  # Currently active branch

        self._load_version_history()
```

#### Creating Checkpoints

```python
def create_checkpoint(self, description, auto=False):
    """Create a checkpoint of current story state"""
    checkpoint_id = f"cp_{int(time.time())}_{random.randint(1000,9999)}"

    checkpoint = StoryCheckpoint(
        checkpoint_id,
        self._get_current_chapter(),
        self._get_current_response_num(),
        description
    )

    # Capture all state
    checkpoint.snapshot = self._capture_full_state()

    # Save checkpoint
    self._save_checkpoint(checkpoint)

    if not auto:
        print(f"✅ Checkpoint created: {description}")
        print(f"   ID: {checkpoint_id}")
        print(f"   Chapter {checkpoint.chapter}, Response {checkpoint.response_num}")
        print(f"   You can branch from this point anytime with: /branch {checkpoint_id}")

    return checkpoint_id

def _capture_full_state(self):
    """Capture complete snapshot of RP state"""
    return {
        "conversation_history": self._load_conversation_history(),
        "entity_cards": self._copy_all_entity_cards(),
        "story_state": self._copy_file(self.rp_dir / "state" / "current_state.md"),
        "plot_threads": self._copy_file(self.rp_dir / "state" / "plot_threads.json"),
        "knowledge_base": self._copy_file(self.rp_dir / "state" / "knowledge_base.json"),
        "chapter_summaries": self._copy_all_chapter_summaries(),
        "fact_database": self._copy_file(self.rp_dir / "state" / "story_facts.json"),
        "relationship_states": self._copy_file(self.rp_dir / "state" / "relationships.json")
    }

def _save_checkpoint(self, checkpoint):
    """Save checkpoint to disk"""
    checkpoint_file = self.checkpoints_dir / f"{checkpoint.id}.json"

    data = {
        "id": checkpoint.id,
        "chapter": checkpoint.chapter,
        "response_num": checkpoint.response_num,
        "description": checkpoint.description,
        "timestamp": checkpoint.timestamp.isoformat(),
        "snapshot": checkpoint.snapshot
    }

    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    self.checkpoints[checkpoint.id] = checkpoint
```

#### Creating and Managing Branches

```python
def create_branch(self, checkpoint_id, branch_name, description=""):
    """Create a new branch from a checkpoint"""
    if checkpoint_id not in self.checkpoints:
        raise ValueError(f"Checkpoint {checkpoint_id} not found")

    branch_id = f"branch_{int(time.time())}_{random.randint(1000,9999)}"

    # Create branch object
    branch = StoryBranch(branch_id, branch_name, checkpoint_id)
    branch.metadata["description"] = description

    # Restore to checkpoint state
    print(f"🌿 Creating branch '{branch_name}' from checkpoint...")
    self._restore_checkpoint(checkpoint_id)

    # Switch to new branch
    self.current_branch = branch_id
    self.branches[branch_id] = branch

    # Save branch info
    self._save_branch(branch)

    print(f"✅ Branch '{branch_name}' created!")
    print(f"   Branch ID: {branch_id}")
    print(f"   Branched from: {self.checkpoints[checkpoint_id].description}")
    print(f"   All new responses will be saved to this branch")
    print(f"   Switch branches with: /switch <branch_id>")

    return branch_id

def switch_branch(self, branch_id):
    """Switch to a different branch"""
    if branch_id == "main":
        # Switch back to main timeline
        self._restore_to_main()
        self.current_branch = "main"
        print("🔀 Switched to main branch")
        return

    if branch_id not in self.branches:
        raise ValueError(f"Branch {branch_id} not found")

    branch = self.branches[branch_id]

    print(f"🔀 Switching to branch '{branch.name}'...")

    # Restore to branch's parent checkpoint
    self._restore_checkpoint(branch.parent)

    # Apply branch-specific responses
    for response in branch.responses:
        self._apply_response(response)

    self.current_branch = branch_id
    print(f"✅ Now on branch '{branch.name}'")
    print(f"   {len(branch.responses)} responses on this branch")

def _restore_checkpoint(self, checkpoint_id):
    """Restore RP to checkpoint state"""
    checkpoint = self.checkpoints[checkpoint_id]
    snapshot = checkpoint.snapshot

    print(f"   Restoring state from {checkpoint.description}...")

    # Restore all state files
    self._restore_conversation_history(snapshot["conversation_history"])
    self._restore_entity_cards(snapshot["entity_cards"])
    self._restore_file(self.rp_dir / "state" / "current_state.md",
                       snapshot["story_state"])
    self._restore_file(self.rp_dir / "state" / "plot_threads.json",
                       snapshot["plot_threads"])
    self._restore_file(self.rp_dir / "state" / "knowledge_base.json",
                       snapshot["knowledge_base"])
    self._restore_chapter_summaries(snapshot["chapter_summaries"])
    self._restore_file(self.rp_dir / "state" / "story_facts.json",
                       snapshot["fact_database"])
    self._restore_file(self.rp_dir / "state" / "relationships.json",
                       snapshot["relationship_states"])

    print("   ✓ State restored successfully")
```

#### Comparing Branches

```python
def compare_branches(self, branch_a_id, branch_b_id):
    """Compare two branches and show differences"""
    branch_a = self.branches.get(branch_a_id)
    branch_b = self.branches.get(branch_b_id)

    if not branch_a or not branch_b:
        raise ValueError("One or both branches not found")

    print(f"\n📊 COMPARING BRANCHES\n")
    print(f"Branch A: {branch_a.name}")
    print(f"Branch B: {branch_b.name}\n")

    # Find divergence point
    checkpoint_a = self.checkpoints[branch_a.parent]
    checkpoint_b = self.checkpoints[branch_b.parent]

    if checkpoint_a.id == checkpoint_b.id:
        print(f"Diverged from: {checkpoint_a.description}")
        print(f"  (Chapter {checkpoint_a.chapter}, Response {checkpoint_a.response_num})\n")
    else:
        print("⚠️ Branches have different origins\n")

    # Compare response counts
    print(f"Response counts:")
    print(f"  Branch A: {len(branch_a.responses)} responses")
    print(f"  Branch B: {len(branch_b.responses)} responses\n")

    # Compare character developments
    print("Character developments:")
    self._compare_character_states(branch_a, branch_b)

    # Compare plot threads
    print("\nPlot threads:")
    self._compare_plot_threads(branch_a, branch_b)

    # Compare key events
    print("\nKey events:")
    self._compare_events(branch_a, branch_b)

def _compare_character_states(self, branch_a, branch_b):
    """Compare character states between branches"""
    # Load entity cards from each branch
    cards_a = self._load_branch_entity_cards(branch_a)
    cards_b = self._load_branch_entity_cards(branch_b)

    # Find differences
    for char_name in set(cards_a.keys()) | set(cards_b.keys()):
        if char_name not in cards_a:
            print(f"  - {char_name}: Only in Branch B")
        elif char_name not in cards_b:
            print(f"  - {char_name}: Only in Branch A")
        else:
            # Compare character states
            diffs = self._diff_character_cards(cards_a[char_name], cards_b[char_name])
            if diffs:
                print(f"  - {char_name}:")
                for diff in diffs:
                    print(f"      {diff}")
```

#### Merging Branches

```python
def merge_branches(self, source_branch_id, target_branch_id, strategy="interactive"):
    """Merge elements from one branch into another"""
    source = self.branches[source_branch_id]
    target = self.branches[target_branch_id]

    print(f"🔀 MERGING: {source.name} → {target.name}\n")

    if strategy == "interactive":
        # Let user choose what to merge
        print("Select elements to merge:\n")

        # Character developments
        print("1. Character developments")
        char_diffs = self._compare_character_states(source, target)
        if char_diffs:
            merge_chars = input("   Merge character changes? (y/n): ")
            if merge_chars.lower() == 'y':
                self._merge_character_states(source, target)

        # Plot threads
        print("\n2. Plot threads")
        plot_diffs = self._compare_plot_threads(source, target)
        if plot_diffs:
            merge_plots = input("   Merge plot threads? (y/n): ")
            if merge_plots.lower() == 'y':
                self._merge_plot_threads(source, target)

        # Specific responses
        print("\n3. Individual responses")
        print(f"   Source has {len(source.responses)} responses")
        cherry_pick = input("   Cherry-pick specific responses? (y/n): ")
        if cherry_pick.lower() == 'y':
            self._cherry_pick_responses(source, target)

    elif strategy == "take_all":
        # Merge everything from source
        self._merge_all(source, target)

    print("\n✅ Merge complete!")
```

### Automatic Checkpointing

```python
class AutoCheckpointer:
    """Automatically create checkpoints at key moments"""

    def __init__(self, version_control, config):
        self.vc = version_control
        self.config = config
        self.responses_since_checkpoint = 0

    def check_and_create_checkpoint(self, response, response_num):
        """Check if checkpoint should be created"""
        self.responses_since_checkpoint += 1

        # Every N responses
        if self.responses_since_checkpoint >= self.config.get("auto_checkpoint_interval", 50):
            description = f"Auto-checkpoint at response {response_num}"
            self.vc.create_checkpoint(description, auto=True)
            self.responses_since_checkpoint = 0
            return True

        # Before major decisions (detect with keywords)
        if self._is_major_decision(response):
            description = f"Before major decision (response {response_num})"
            self.vc.create_checkpoint(description, auto=True)
            return True

        # Before arc regeneration
        if self._is_arc_regeneration(response_num):
            description = f"Before arc regeneration (response {response_num})"
            self.vc.create_checkpoint(description, auto=True)
            return True

        return False

    def _is_major_decision(self, response):
        """Detect if response contains a major decision"""
        decision_keywords = [
            "decide", "choice", "choose", "accept", "reject",
            "agree", "refuse", "commit", "leave", "stay"
        ]
        return any(kw in response.lower() for kw in decision_keywords)
```

### Configuration

```yaml
# automation_config.yaml

version_control:
  enabled: true

  # Automatic checkpointing
  auto_checkpoint:
    enabled: true
    interval: 50  # Create checkpoint every 50 responses
    before_major_decisions: true
    before_arc_regeneration: true
    before_user_requested: true

  # Storage
  checkpoint_storage:
    compression: true  # Compress checkpoint data
    max_checkpoints: 100  # Max checkpoints to keep
    cleanup_old: true  # Auto-delete old checkpoints

  # Branches
  max_branches: 10  # Limit number of active branches

  # Performance
  background_save: true  # Save checkpoints in background
```

### User Commands

```bash
# Create checkpoint
/checkpoint "Before big choice"

# Create branch from checkpoint
/branch cp_12345 "romance_path" "Choose romance over career"

# List branches
/branches

# Switch to branch
/switch branch_67890

# Compare branches
/compare main romance_path

# Merge branches
/merge romance_path main

# List checkpoints
/checkpoints

# Delete branch
/branch-delete romance_path

# Return to main timeline
/switch main
```

### User Interface

```
=== STORY VERSION CONTROL ===

Current branch: main
Last checkpoint: "Before meeting Lily's parents" (Ch 12, Response 245)

Branches:
  [1] main (active) - 250 responses
  [2] romance_path - 15 responses (branched from Response 120)
  [3] career_focus - 12 responses (branched from Response 120)
  [4] mystery_route - 8 responses (branched from Response 89)

Recent checkpoints:
  [cp_1] Response 245 - "Before meeting Lily's parents"
  [cp_2] Response 200 - "After job offer"
  [cp_3] Response 150 - "Auto-checkpoint"
  [cp_4] Response 120 - "Before major choice"

Commands:
  /checkpoint <description>      - Create checkpoint
  /branch <cp_id> <name> [desc]  - Create branch
  /switch <branch_id>            - Switch branch
  /compare <branch_a> <branch_b> - Compare branches
```

### Benefits

- **Risk-free exploration**: Try different approaches without losing progress
- **Story experimentation**: Test dramatic vs subtle, action vs dialogue
- **Multiple endings**: Explore different conclusions
- **Safety net**: Revert bad decisions
- **Creative freedom**: Not locked into first choice

---

## 2. Response Alternatives Generator

### Problem Statement

Sometimes you want options before committing to a response. You might want a more dramatic version, a more subtle version, or just variety to choose from. Currently you're locked into whatever Claude generates first.

### Proposed Solution

Generate multiple response variations with different tones/styles, allowing you to:
- See 2-3 variations before committing
- Request specific tones (dramatic, subtle, humorous, etc.)
- Blend elements from different variations
- Regenerate specific parts
- Learn your preferences over time

### Implementation

```python
# src/response_alternatives.py

class ResponseAlternativesGenerator:
    """Generate multiple response variations"""

    def __init__(self, claude_client):
        self.client = claude_client
        self.variation_types = {
            "balanced": "Maintain balanced tone and pacing",
            "dramatic": "Increase drama and tension. Make this more intense and emotionally charged",
            "subtle": "Keep subtle and understated. Focus on nuance and restraint",
            "fast_paced": "Speed up the pacing. Move forward quickly",
            "slow_burn": "Slow down. Add detail and atmosphere",
            "humorous": "Add humor and levity",
            "serious": "Keep serious and grounded",
            "romantic": "Emphasize romantic tension and chemistry",
            "action": "Focus on action and movement. Keep dynamic",
            "introspective": "Focus on internal thoughts and emotions",
            "descriptive": "Rich, detailed descriptions of setting and atmosphere"
        }

    def generate_alternatives(self, prompt, num_alternatives=3, variations=None):
        """Generate multiple response variations"""

        if variations is None:
            variations = ["balanced", "dramatic", "subtle"]

        alternatives = []

        print(f"🎭 Generating {num_alternatives} response variations...")

        for i, variation in enumerate(variations[:num_alternatives], 1):
            print(f"   Generating variation {i}/{num_alternatives}: {variation}...")

            # Modify prompt with variation instruction
            varied_prompt = self._apply_variation(prompt, variation)

            # Generate response
            response = self.client.send_message(varied_prompt)

            alternatives.append({
                "variation": variation,
                "content": response["content"],
                "preview": response["content"][:300] + "...",
                "full_response": response
            })

        return alternatives

    def _apply_variation(self, prompt, variation_type):
        """Apply variation instruction to prompt"""
        instruction = self.variation_types.get(variation_type, "")

        variation_prompt = f"""
{prompt}

**TONE VARIATION**: {instruction}
Maintain story continuity but adjust tone/style as indicated.
"""
        return variation_prompt

    def present_alternatives_to_user(self, alternatives):
        """Show alternatives in TUI for user selection"""
        print("\n" + "="*80)
        print("🎭 RESPONSE ALTERNATIVES")
        print("="*80 + "\n")

        for i, alt in enumerate(alternatives, 1):
            print(f"[{i}] {alt['variation'].upper()}")
            print("-" * 80)
            print(alt['preview'])
            print("-" * 80)
            print()

        print("[R] Regenerate with different variations")
        print("[E] Enter custom variation")
        print("[B] Blend elements from multiple")
        print()

        choice = input(f"Select response (1-{len(alternatives)}, R, E, B): ").strip()

        if choice.upper() == 'R':
            # Regenerate with different variations
            return self._regenerate_with_new_variations()
        elif choice.upper() == 'E':
            # Custom variation
            return self._generate_custom_variation()
        elif choice.upper() == 'B':
            # Blend multiple
            return self._blend_responses(alternatives)
        else:
            # Select specific response
            try:
                idx = int(choice) - 1
                return alternatives[idx]["content"]
            except (ValueError, IndexError):
                print("Invalid choice, using first alternative")
                return alternatives[0]["content"]

    def _regenerate_with_new_variations(self):
        """Let user pick different variation types"""
        print("\nAvailable variation types:")
        for i, (var_type, description) in enumerate(self.variation_types.items(), 1):
            print(f"  [{i}] {var_type}: {description}")

        selections = input("\nSelect 3 variations (comma-separated numbers): ").strip()
        var_indices = [int(x.strip()) - 1 for x in selections.split(',')]
        var_types = [list(self.variation_types.keys())[i] for i in var_indices]

        # Regenerate with new variations
        return "regenerate", var_types

    def _generate_custom_variation(self):
        """Generate with custom user-specified variation"""
        custom_instruction = input("\nDescribe desired tone/style: ").strip()

        # Add to variation types temporarily
        self.variation_types["custom"] = custom_instruction

        return "custom", custom_instruction

    def _blend_responses(self, alternatives):
        """Blend elements from multiple responses"""
        print("\nBlend responses:")
        print("Example: Take dialogue from #1 and action from #2")

        blend_instruction = input("\nDescribe what to blend: ").strip()

        # Use Claude to blend based on instruction
        blend_prompt = f"""Please blend these response variations:

{chr(10).join(f"#{i+1}: {alt['content']}" for i, alt in enumerate(alternatives))}

Blend instruction: {blend_instruction}

Generate a blended response that combines the best elements as specified.
"""

        blended = self.client.send_message(blend_prompt)
        return blended["content"]
```

### Integration into Automation

```python
# In automation config
config = {
    "enable_response_alternatives": True,
    "num_alternatives": 3,
    "default_variations": ["balanced", "dramatic", "subtle"],
    "auto_select": False,  # If true, automatically picks "balanced"
    "show_alternatives_every_n": 1  # Show alternatives every N responses
}

# In automation loop
if config["enable_response_alternatives"] and should_show_alternatives():
    generator = ResponseAlternativesGenerator(claude_client)

    alternatives = generator.generate_alternatives(
        prompt,
        num_alternatives=config["num_alternatives"],
        variations=config["default_variations"]
    )

    # Let user choose
    result = generator.present_alternatives_to_user(alternatives)

    if isinstance(result, tuple) and result[0] == "regenerate":
        # Regenerate with new variations
        alternatives = generator.generate_alternatives(prompt, variations=result[1])
        final_response = generator.present_alternatives_to_user(alternatives)
    else:
        final_response = result
else:
    # Normal single response
    final_response = claude_client.send_message(prompt)
```

### Advanced Features

#### Regenerate Specific Part
```python
def regenerate_section(self, response, section_description):
    """Regenerate just a specific part of response"""
    prompt = f"""Original response:
{response}

Please regenerate only: {section_description}

Keep everything else the same, only change the specified section.
"""
    return self.client.send_message(prompt)

# Usage:
# "Regenerate just Marcus's dialogue"
# "Regenerate the action scene at the end"
# "Regenerate the description of the coffee shop"
```

#### Learn Preferences
```python
class PreferenceLearner:
    """Learn which variations user prefers"""

    def __init__(self):
        self.selection_history = []

    def record_selection(self, alternatives, selected_idx):
        """Record which variation was selected"""
        selected_variation = alternatives[selected_idx]["variation"]
        self.selection_history.append(selected_variation)

    def get_preferred_variations(self):
        """Get most commonly selected variations"""
        from collections import Counter
        counts = Counter(self.selection_history[-50:])  # Last 50 selections
        return [var for var, count in counts.most_common(3)]

    def suggest_variations(self):
        """Suggest variations based on history"""
        preferred = self.get_preferred_variations()

        if len(preferred) >= 3:
            return preferred
        else:
            # Fill with defaults
            defaults = ["balanced", "dramatic", "subtle"]
            return preferred + [d for d in defaults if d not in preferred]
```

### Configuration

```yaml
response_alternatives:
  enabled: true

  # When to show
  show_every_n_responses: 1  # Show alternatives every N responses
  show_for_major_scenes: true  # Always show for major scenes

  # Generation
  num_alternatives: 3
  default_variations:
    - balanced
    - dramatic
    - subtle

  # Preferences
  learn_preferences: true
  use_preferred_variations: true  # Use learned preferences

  # Advanced
  allow_custom_variations: true
  allow_blending: true
  allow_section_regeneration: true
```

### User Commands

```bash
/alt                    # Show alternatives for next response
/alt-off               # Disable alternatives
/alt-on                # Enable alternatives
/alt-variations        # See available variation types
/alt-regen dialogue    # Regenerate just dialogue
```

### Benefits

- **Choice**: Not locked into first generation
- **Control**: Fine-tune tone and style
- **Experimentation**: Try different approaches
- **Quality**: Pick best version
- **Learning**: System learns your preferences

---

## 3. Git-Like Version Control

### Problem Statement

Need comprehensive version control like Git but for story content. Want to track changes over time, see what was introduced when, and revert if needed.

### Proposed Solution

Implement Git-like commands and features adapted for story content:
- Log: See history of changes
- Diff: Compare versions
- Blame: Find when facts were introduced
- Revert: Roll back to earlier state
- Cherry-pick: Copy specific responses between branches

### Implementation

```python
# src/story_git.py

class StoryGit:
    """Git-like interface for story version control"""

    def __init__(self, version_control):
        self.vc = version_control

    def log(self, num=10, branch=None):
        """Show recent story history"""
        branch = branch or self.vc.current_branch

        print(f"\n📜 STORY LOG ({branch})\n")

        if branch == "main":
            # Show main timeline
            responses = self._get_main_responses()
        else:
            # Show branch responses
            responses = self.vc.branches[branch].responses

        # Show last N responses
        for response in responses[-num:]:
            self._print_log_entry(response)

    def _print_log_entry(self, response):
        """Print a single log entry"""
        print(f"Response {response['num']} - Chapter {response['chapter']}")
        print(f"  Date: {response['timestamp']}")
        print(f"  Preview: {response['content'][:100]}...")
        print(f"  Characters: {', '.join(response.get('characters', []))}")
        print()

    def diff(self, checkpoint_a, checkpoint_b):
        """Show differences between two checkpoints"""
        cp_a = self.vc.checkpoints[checkpoint_a]
        cp_b = self.vc.checkpoints[checkpoint_b]

        print(f"\n📊 DIFF: {cp_a.description} → {cp_b.description}\n")

        # Character changes
        print("## CHARACTER CHANGES\n")
        self._diff_characters(cp_a.snapshot, cp_b.snapshot)

        # Plot changes
        print("\n## PLOT CHANGES\n")
        self._diff_plots(cp_a.snapshot, cp_b.snapshot)

        # World changes
        print("\n## WORLD-BUILDING CHANGES\n")
        self._diff_world(cp_a.snapshot, cp_b.snapshot)

        # Response count
        resp_a = cp_a.response_num
        resp_b = cp_b.response_num
        print(f"\n## RESPONSE COUNT\n")
        print(f"  Responses between checkpoints: {resp_b - resp_a}")

    def blame(self, fact_query):
        """Find which response introduced a fact"""
        print(f"\n🔍 BLAME: '{fact_query}'\n")

        # Search fact database for fact
        fact_db = FactDatabase(self.vc.rp_dir)
        fact_info = fact_db.query(fact_query)

        if fact_info and "source" in fact_info:
            source = fact_info["source"]
            # Parse source (e.g., "ch5_r123")
            chapter, response = self._parse_source(source)

            print(f"Introduced in: Chapter {chapter}, Response {response}")
            print(f"Content: {fact_info.get('value', 'N/A')}")

            # Show the actual response
            response_content = self._get_response_content(chapter, response)
            print(f"\nResponse excerpt:")
            print(f"  {response_content[:500]}...")

        else:
            print("Fact not found in database")

    def revert(self, checkpoint_id):
        """Revert to previous checkpoint"""
        checkpoint = self.vc.checkpoints[checkpoint_id]

        print(f"⚠️  REVERT to: {checkpoint.description}")
        print(f"   This will discard all changes after Response {checkpoint.response_num}")

        confirm = input("   Are you sure? (yes/no): ")

        if confirm.lower() == "yes":
            self.vc._restore_checkpoint(checkpoint_id)
            print("✅ Reverted successfully")
            print(f"   Now at: Chapter {checkpoint.chapter}, Response {checkpoint.response_num}")
        else:
            print("❌ Revert cancelled")

    def cherry_pick(self, response_id, source_branch, target_branch=None):
        """Copy a specific response to another branch"""
        target_branch = target_branch or self.vc.current_branch

        print(f"🍒 CHERRY-PICK: Response {response_id}")
        print(f"   From: {source_branch}")
        print(f"   To: {target_branch}")

        # Get response from source branch
        source = self.vc.branches[source_branch]
        response = self._find_response(source, response_id)

        if not response:
            print("❌ Response not found")
            return

        # Show preview
        print(f"\nResponse preview:")
        print(f"  {response['content'][:300]}...")

        confirm = input("\nApply this response to current branch? (y/n): ")

        if confirm.lower() == 'y':
            # Apply response
            self._apply_cherry_pick(response, target_branch)
            print("✅ Cherry-pick successful")
        else:
            print("❌ Cherry-pick cancelled")

    def status(self):
        """Show current status (like git status)"""
        print(f"\n📍 STORY STATUS\n")
        print(f"Current branch: {self.vc.current_branch}")

        if self.vc.current_branch == "main":
            print(f"On main timeline")
        else:
            branch = self.vc.branches[self.vc.current_branch]
            print(f"On branch: {branch.name}")
            print(f"  Branched from: {branch.parent}")
            print(f"  Responses on branch: {len(branch.responses)}")

        # Show recent checkpoints
        print(f"\nRecent checkpoints:")
        recent_cps = sorted(self.vc.checkpoints.values(),
                          key=lambda cp: cp.timestamp,
                          reverse=True)[:5]

        for cp in recent_cps:
            print(f"  - {cp.id}: {cp.description}")

        # Show available branches
        print(f"\nAvailable branches:")
        if self.vc.branches:
            for branch in self.vc.branches.values():
                active = "* " if branch.id == self.vc.current_branch else "  "
                print(f"{active}{branch.name} ({len(branch.responses)} responses)")
        else:
            print("  (no branches)")
```

### User Commands

```bash
# Git-like commands
/story-log [n]                    # Show last N responses
/story-diff cp_123 cp_456         # Compare checkpoints
/story-blame "Marcus's job"       # Find when fact introduced
/story-revert cp_123              # Revert to checkpoint
/story-cherry-pick r_456 branch_a # Copy response from branch
/story-status                     # Show current status

# Shortcuts
/log [n]          # Alias for story-log
/diff a b         # Alias for story-diff
/blame <query>    # Alias for story-blame
/revert <cp_id>   # Alias for story-revert
```

### Benefits

- **Transparency**: See full history
- **Debugging**: Find when things changed
- **Control**: Revert mistakes
- **Flexibility**: Move content between branches
- **Understanding**: Track story evolution

---

## Integration Summary

All three systems work together:

```python
# Complete integration

# 1. Auto-checkpointing
auto_cp = AutoCheckpointer(version_control, config)

# After each response
if auto_cp.check_and_create_checkpoint(response, response_num):
    print("💾 Auto-checkpoint created")

# 2. Response alternatives
if config["show_alternatives"]:
    alt_gen = ResponseAlternativesGenerator(claude_client)
    alternatives = alt_gen.generate_alternatives(prompt)
    final_response = alt_gen.present_alternatives_to_user(alternatives)
else:
    final_response = claude_client.send_message(prompt)

# 3. Save response to current branch
version_control.save_response_to_branch(
    final_response,
    version_control.current_branch
)

# 4. User can access Git-like commands anytime
story_git = StoryGit(version_control)
# /log, /diff, /blame, etc.
```

---

## Priority & Implementation Order

**Recommended order:**

1. **Story Checkpointing** - Foundation, 3-4 days
2. **Response Alternatives** - Independent, 2-3 days
3. **Git-Like Commands** - Uses checkpointing, 2 days

**Total: ~1 week for core implementation**

**Optional enhancements** (can add later):
- Visual branch diagram
- Merge conflict resolution
- Automatic preference learning
- Web UI for browsing branches
