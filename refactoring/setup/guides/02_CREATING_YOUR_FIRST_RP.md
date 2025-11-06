# Creating Your First RP - Complete Walkthrough

**Estimated Time:** 30 minutes
**Difficulty:** Beginner-friendly
**Prerequisites:** System installed and configured (see `01_FIRST_TIME_SETUP.md`)

---

## 📖 What You'll Learn

By the end of this guide, you'll have:
- ✅ A complete, working RP ready to launch
- ✅ Understanding of the folder structure
- ✅ Your first character created
- ✅ Your opening chapter written
- ✅ The launcher running with your RP

---

## 🎯 Two Paths to Choose From

### Path A: Quick Setup (5 minutes)
**Best for:** Getting started immediately
**→** Jump to [Quick Setup Path](#quick-setup-path)

### Path B: Manual Setup (30 minutes)
**Best for:** Understanding every component
**→** Continue reading below

---

## 🚀 Quick Setup Path

If you just want to start writing immediately, use the quick setup script:

### Step 1: Run Quick Setup

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python setup/quick_setup.py "My First RP"
```

This creates a complete RP folder with all required files.

### Step 2: Launch It

```bash
python launch_rp_tui.py "My First RP"
```

### Step 3: Start Writing!

1. The TUI will open automatically
2. Type your first message in the input area
3. Press **Ctrl+Enter** to send
4. Claude responds and the story begins!

**That's it!** You're roleplaying. To customize your RP, see [Customization](#customization) below.

---

## 🔨 Manual Setup Path

This path walks you through creating everything manually so you understand how it all works.

### Step 1: Create Your RP Folder

Navigate to the RPs directory and create a folder for your RP:

```bash
cd "C:\Users\green\Desktop\RP Claude Code\RPs"
mkdir "My First RP"
cd "My First RP"
```

**Naming Tips:**
- Use descriptive names: "Epic Fantasy Quest", "Cyberpunk Detective"
- Avoid special characters: `/\:*?"<>|`
- Spaces are fine!

---

### Step 2: Create the Directory Structure

Create these folders inside your RP directory:

```bash
mkdir chapters
mkdir characters
mkdir entities
mkdir state
mkdir memories
mkdir relationships
mkdir locations
mkdir sessions
mkdir exports
```

**What each folder does:**

| Folder | Purpose | Required? |
|--------|---------|-----------|
| `chapters/` | Your story chapters | ✅ Yes |
| `characters/` | Character sheets | ✅ Yes |
| `entities/` | Auto-generated entity cards | ✅ Yes |
| `state/` | Tracking & automation files | ✅ Yes |
| `memories/` | Character-specific memories | ⭕ Optional |
| `relationships/` | Relationship tracking | ⭕ Optional |
| `locations/` | Location details | ⭕ Optional |
| `sessions/` | Session logs | ⭕ Optional |
| `exports/` | Exported content | ⭕ Optional |

---

### Step 3: Create Core State Files

These files are required for the automation system:

#### `state/plot_threads_master.md`

```markdown
# Plot Threads Master

## Active Threads
- None yet (story just starting!)

## Resolved Threads
- None yet

## Future Threads
- (Ideas for future plot points)
```

#### `state/current_state.md`

```markdown
# Current State

## Date/Time
- (When does your story start?)

## Location
- (Where are we?)

## Present Characters
- {{user}} - Your character

## Current Situation
- Story is just beginning
```

#### `state/automation_config.json`

```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50,
  "auto_memory": false,
  "memory_frequency": 25
}
```

**Configuration explained:**
- `auto_entity_cards`: Create character cards after N mentions
- `entity_mention_threshold`: How many mentions before creating card
- `auto_story_arc`: Auto-update story arc tracking
- `arc_frequency`: Update arc every N messages
- `auto_memory`: Auto-create character memories
- `memory_frequency`: Create memory every N messages

#### `state/entity_tracker.json`

```json
{
  "entities": {},
  "last_updated": ""
}
```

#### `state/file_tracking.json`

```json
{
  "tracked_files": {},
  "last_scan": ""
}
```

#### `state/response_counter.json`

```json
{
  "count": 0
}
```

---

### Step 4: Create Your RP Overview File

Create a file named exactly like your RP folder with `.md` extension.

**Example:** If folder is `My First RP`, create `My First RP.md`

```markdown
# My First RP

## Basic Info
- **Genre:** Fantasy / Adventure / Romance / etc.
- **Setting:** Medieval fantasy world / Modern city / Space station / etc.
- **Tone:** Epic / Lighthearted / Dark / Mysterious / etc.

## Premise
(What's this story about? 2-3 sentences)

Your character finds themselves...

## Main Characters
- **{{user}}** - (Your character's name and brief description)
- **{{char}}** - (Your main NPC companion/antagonist)

## Story Goals
- What do you want to happen in this story?
- What themes do you want to explore?
- Any specific scenes you want to write?

---

**Created:** [Date]
**Status:** Active
```

---

### Step 5: Create Your Character Sheet

Create `characters/{{user}}.md` - this is YOU in the story:

```markdown
# {{user}}

## Basic Info
- **Full Name:** [Your character's name]
- **Age:** [Age]
- **Gender:** [Gender]
- **Occupation:** [What do they do?]

## Appearance
Describe what your character looks like:
- Height, build, distinctive features
- Hair, eyes, style
- How they typically dress
- Any scars, tattoos, or unique marks

## Personality
What's your character like?
- Core personality traits
- How they react to stress
- Sense of humor
- Values and beliefs
- Fears and weaknesses

## Background
Their history before the story starts:
- Where they grew up
- Important life events
- Relationships with family
- Education or training
- How they ended up here

## Skills & Abilities
What can they do?
- Combat skills (if any)
- Magic or special powers (if any)
- Practical skills (crafting, medicine, etc.)
- Social skills (persuasion, intimidation, etc.)

## Current Situation
- Where are they right now?
- What are they doing?
- What do they want?
- What's their immediate goal?

## Relationships
- (Add other characters as you meet them)

---

**Notes:**
- (Anything else important about your character)
```

**Tips for character creation:**
- Make them flawed! Perfect characters are boring
- Give them clear wants and fears
- Think about how they'd react in different situations
- You can update this file as the story progresses

---

### Step 6: Create Your First NPC (Optional)

Create `characters/{{char}}.md` or use a specific name:

```markdown
# [NPC Name]

## Basic Info
- **Full Name:**
- **Age:**
- **Role:** Companion / Antagonist / Quest Giver / etc.

## Appearance
(Describe them)

## Personality
(What are they like?)

## Background
(Their story)

## Relationship to {{user}}
(How do they know your character?)

## Goals & Motivations
(What do they want?)
```

You can also create NPCs as you go - the automation system will help generate entity cards when characters are mentioned frequently.

---

### Step 7: Create Story Guidance Files (Optional but Recommended)

These files guide Claude's responses to match your vision:

#### `AUTHOR'S_NOTES.md` - Story Rules

```markdown
# Author's Notes

## Story Rules - What MUST Happen
- (Things that absolutely must occur in your story)

## Story Rules - What MUST NOT Happen
- (Things you absolutely don't want to happen)

## Writing Style
- Prose style: (Descriptive / Fast-paced / Poetic / etc.)
- Perspective: (First person / Third person limited / etc.)
- Length: (How long should responses be?)

## Content Guidelines
- Tone: (Serious / Light / Dark / etc.)
- Themes: (What themes to explore)
- Content boundaries: (Any topics to avoid)

---

**These are ABSOLUTE rules for the story.**
```

**Example - Fantasy Adventure:**
```markdown
# Author's Notes

## Story Rules - What MUST Happen
- Character should discover their hidden magical abilities gradually
- A mysterious mentor figure will appear at the right time
- The main conflict involves an ancient evil awakening

## Story Rules - What MUST NOT Happen
- No permanent character death without my approval
- No sudden power boosts without proper development
- Magic must always have consequences

## Writing Style
- Descriptive but not purple prose
- Balance action with character moments
- Responses around 3-5 paragraphs

## Content Guidelines
- Tone: Epic but with lighthearted moments
- Themes: Self-discovery, courage, friendship
- PG-13 level content
```

#### `STORY_GENOME.md` - Story Direction

```markdown
# Story Genome

## Genre & Setting
- **Primary Genre:**
- **Secondary Genre:**
- **Setting:**
- **Time Period:**

## Story Beats (High Level Plan)
1. **Opening:** (Where we start)
2. **First Act:** (Initial goals and obstacles)
3. **Midpoint:** (Major twist or revelation)
4. **Second Act:** (Escalation and complications)
5. **Climax:** (Final confrontation)
6. **Resolution:** (How it ends)

## Major Plot Points
- (Key events you want to happen)

## Themes to Explore
- (What ideas interest you?)

## Intended Direction
- (Where do you want this story to go?)

---

**This is your INTENDED story arc, but can evolve organically.**
```

#### `SCENE_NOTES.md` - Current Session Guidance

```markdown
# Scene Notes

## Current Scene
- **Location:**
- **Time:**
- **Present:**

## Scene Goals
- (What should happen this session?)

## NPCs Active This Scene
- (Who's around?)

## Notes for This Session
- (Anything specific to focus on?)
- (Mood or tone to set?)

---

**Delete/update after each session.**
```

---

### Step 8: Create Your First Chapter File

Create `chapters/chapter_001.md`:

**You have two options:**

**Option 1: Start Fresh (Recommended for beginners)**
Just create a minimal file - you'll write your opening directly in the TUI:

```markdown
# Chapter 1
```

That's it! You can start writing when you launch the RP.

**Option 2: Pre-Write Your Opening**
Write your opening scene here before launching:

```markdown
# Chapter 1: [Title]

[Write your opening scene here]

This is where your story begins. Describe:
- The setting - where are we?
- Your character - what are they doing?
- The atmosphere - what's the mood?
- The hook - what draws us in?

---

**Started:** [Date]
**Status:** In Progress
```

**Opening Chapter Tips:**

**Good opening:**
```markdown
# Chapter 1: The Call

The tavern stank of spilled ale and desperation.

I nursed my drink in the corner, trying to ignore the off-key singing from the bard's corner. Three days in this backwater town, and still no word from the guild. My coin purse grew lighter by the hour, and my patience along with it.

That's when she walked in.

Tall, cloaked, moving with the kind of confidence that meant either wealth or power—possibly both. She scanned the room once, and her eyes locked on mine.

Great. Just great.
```

**Why it works:**
- Establishes setting immediately
- Shows character's situation and mood
- Introduces a hook (mysterious woman)
- Leaves room for Claude to continue

---

### Step 9: Test Your Setup (Optional but Recommended)

Before launching, you can verify your structure is correct:

```bash
# Future validation tool (coming soon):
python setup/scripts/validate_rp.py "My First RP"
```

For now, manually check:
- ✅ RP folder exists in `RPs/` directory
- ✅ `state/` directory exists with config files
- ✅ `chapters/` directory exists with chapter_001.md
- ✅ `characters/` directory exists with {{user}}.md
- ✅ RP overview file exists (e.g., `My First RP.md`)

---

### Step 10: Launch Your RP!

Now for the exciting part:

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python launch_rp_tui.py "My First RP"
```

**What happens:**
1. Launcher checks for updates (if enabled)
2. Finds your RP folder
3. Starts the bridge
4. Opens the TUI interface

**The TUI Interface:**

```
┌─────────────────────────────────────────────────────┐
│                  RP Launcher                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Chat messages appear here...                      │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Type your message...                               │
│                                                     │
└─────────────────────────────────────────────────────┘
F1: Help | F2: Memory | F3: Arc | F9: Settings | F10: Restart
```

**Key controls:**
- **Type normally** to write your message
- **Enter** creates a new line
- **Ctrl+Enter** sends your message to Claude
- **F1-F9** open overlay screens (help, settings, etc.)
- **F10** restarts the bridge
- **Ctrl+Q** quits the application

---

## 📝 Your First Messages

### Message 1: Set the Scene

Your first message should establish or continue from your opening chapter:

**Example:**
```
I look up from my drink as the cloaked woman approaches my table.
My hand instinctively moves closer to my sword hilt.

"Can I help you?" I ask, trying to sound more confident than I feel.
```

**Tips:**
- Write in first person or third person (your choice)
- Describe actions and internal thoughts
- End with a hook for Claude to respond to
- Don't worry about length—write naturally

### Message 2: React to Claude's Response

After Claude responds, you react to what happened:

**Example response from Claude:**
```
The woman's lips curl into a knowing smile as she takes the seat
across from you without invitation. Up close, you notice the silver
runes embroidered along the edge of her cloak—expensive work, and
definitely magical.

"I rather think I can help you," she says, her voice carrying the
accent of the northern provinces. "You're looking for work, aren't
you? The kind that pays well and asks few questions?"

She slides a small leather pouch across the table. The clink of
gold is unmistakable.
```

**Your next message:**
```
I glance at the pouch but don't touch it. In my experience, mysterious
strangers offering gold always want something dangerous in return.

"Depends on the work," I say carefully. "I'm not an assassin, if that's
what you're looking for."

I study her face, trying to read her intentions. The northern accent
is real—you can't fake that particular rolling 'r'—but that doesn't
tell me if she's trustworthy.

"What's the job?"
```

---

## 🎮 Using the F-Key Overlays

The TUI has several overlay screens accessed with function keys:

### F1: Help Screen
- Command reference
- Keyboard shortcuts
- Quick tips

### F2: Memory Browser
- View character memories
- See what's been established
- Track important details

### F3: Story Arc Tracker
- Current story arc
- Plot threads
- Story progress

### F4: Characters
- Character list
- Quick character references
- Entity cards

### F5: Session Notes
- Edit SCENE_NOTES.md
- Current session guidance
- Quick note-taking

### F6: Entity Browser
- All extracted entities
- Generated character cards
- Location and item cards

### F7: Story Genome
- View/edit STORY_GENOME.md
- High-level story direction
- Themes and plans

### F8: Status Display
- Current state
- Recent changes
- System information

### F9: Settings
- Configure API keys
- Select models
- Adjust automation
- Set thinking modes

### F10: Restart Bridge
- Restart bridge if needed
- Refresh configuration
- Troubleshooting

---

## 🎨 Customization

Once your RP is running, you can customize it:

### During a Session

**Use commands in your messages:**
- `/note [text]` - Add a quick note
- `/arc` - Update story arc
- `/status` - Update current state
- `/recall [character]` - Recall character details

### Between Sessions

**Edit files directly:**
- Update character sheets as they develop
- Add new NPCs to `characters/`
- Refine story goals in `STORY_GENOME.md`
- Adjust automation in `state/automation_config.json`

### Automation Features

The system automatically:
- **Extracts entities** when mentioned 2+ times
- **Updates story arc** every 50 messages (configurable)
- **Tracks plot threads** in plot_threads_master.md
- **Logs sessions** in sessions/

**Customize automation:**
Press F9 → Settings → Automation section

---

## 💡 Tips for Great Roleplaying

### Writing Style

**Do:**
- Write naturally, like you're telling a story
- Include thoughts and feelings, not just actions
- Give Claude things to respond to
- Be specific about what your character does

**Don't:**
- Control NPCs or predict their responses
- Write multiple actions in one message (give Claude room)
- Rush—take time to describe interesting moments
- Worry about "perfect" writing—have fun!

### Pacing

**Good pacing:**
- Alternate between action and character moments
- Let scenes breathe—don't rush through everything
- Build tension gradually
- End sessions on good stopping points or cliffhangers

### Character Development

- Let your character change over time
- Update character sheets as they grow
- Remember past events and reference them
- Show how experiences affect them

### World Building

- Be consistent with established details
- Add new locations and NPCs organically
- Use the entity system to track world details
- Don't info-dump—reveal things naturally

---

## 🐛 Troubleshooting

### "RP folder not found"
→ Make sure folder is in the `RPs/` directory
→ Folder name in command must match exactly (case-sensitive)

### "Missing state directory"
→ Run: `python setup/quick_setup.py "RP Name"` to recreate

### "No response from Claude"
→ Check terminal for errors
→ Verify API key is set (F9 → Settings)
→ Try restarting bridge (F10)

### "Bridge won't start"
→ Close launcher completely
→ Check no other instances are running
→ Restart: `python launch_rp_tui.py "RP Name"`

### Automation not working
→ Check `state/automation_config.json` settings
→ Ensure automation is enabled (F9 → Settings)
→ Check terminal for background agent status

---

## 📚 Next Steps

### Keep Learning
- **Understanding Structure:** `03_UNDERSTANDING_STRUCTURE.md`
- **Writing Your Story:** `04_WRITING_YOUR_STORY.md`
- **Advanced Features:** `05_ADVANCED_FEATURES.md`

### Explore Features
- Try different thinking modes (F9 → Settings)
- Experiment with automation settings
- Create multiple RPs for different stories
- Export your favorite scenes (exports/ directory)

### Join the Community
- Share your stories
- Get tips from other users
- Report issues on GitHub
- Contribute improvements

---

## 🎉 Congratulations!

You've created your first RP and learned the basics of the system!

**Remember:**
- There's no "wrong" way to roleplay
- The system is flexible—customize it your way
- Have fun and be creative!
- Your story is unique—make it yours!

**Now go write something amazing!** ✨

---

**Need help?** Check `setup/guides/99_TROUBLESHOOTING.md` or the main `setup/README.md`
