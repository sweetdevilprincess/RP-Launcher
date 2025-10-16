# Fantasy Adventure Template

Welcome to the Fantasy Adventure Starter Pack! This template is designed to help you create an epic, immersive fantasy roleplay experience.

---

## What's Included

This template provides everything you need to start a medieval fantasy adventure:

### Story Files (You Edit These)
- **RP_NAME.md** - Overview of your RP (rename to your story title)
- **AUTHOR'S_NOTES.md** - Your story rules and writing preferences
- **STORY_GENOME.md** - Story structure and plot roadmap
- **NAMING_CONVENTIONS.md** - Fantasy naming patterns for consistency
- **SCENE_NOTES.md** - Current session guidance

### Character Templates
- **characters/{{user}}.md** - Your hero/character sheet
- **characters/{{char}}.md** - Your main NPC companion

### Story Chapters
- **chapters/chapter_001.md** - Your opening chapter (customize as you play)

### Auto-Generated Directories
The system creates these on first launch:
- **state/** - Automatic tracking files
- **memories/** - Character memory management
- **entities/** - Generated NPC and location cards
- **locations/** - Place descriptions
- **relationships/** - Relationship tracking
- **sessions/** - Session logs
- **exports/** - Story exports
- **entities/** - Location and entity cards

---

## Quick Start (5 Minutes)

1. **Rename the files:**
   - Rename `RP_NAME.md` to match your RP folder name
   - Example: If folder is "Dragon's Curse", rename to "Dragon's Curse.md"

2. **Fill in the essentials:**
   - Edit `AUTHOR'S_NOTES.md` - Set your story rules
   - Edit `STORY_GENOME.md` - Outline your plot
   - Edit `characters/{{user}}.md` - Create your hero
   - Edit `characters/{{char}}.md` - Create your main companion

3. **Launch your adventure:**
   ```bash
   python launch_rp_tui.py "Your RP Name"
   ```

4. **Start the story:**
   - Type your opening scene
   - Press Ctrl+Enter to send
   - Let Claude respond and your adventure begins!

---

## Customizing This Template

### The Fantasy World

This template assumes a **medieval fantasy setting** but you can customize it:

- **Magic Level:** Low magic (rare)? High magic (common)? No magic?
- **Technology:** Medieval only? Include magitech?
- **Tone:** Dark and gritty? Heroic and hopeful? Dark comedy?
- **Factions:** Kingdoms at war? United realm? Anarchic world?

### Your Story Type

Choose your flavor of fantasy:

- **Heroic Fantasy** - Classic hero saves the day
- **Dark Fantasy** - Morally complex, dangerous world
- **Sword & Sorcery** - Action-packed, adventure-focused
- **Epic Fantasy** - Large-scale, world-changing conflicts

---

## Using the Template Files

### AUTHOR'S_NOTES.md
This file contains your **absolute story rules**. Claude will follow these religiously:
- What MUST happen in your story
- What MUST NOT happen
- Your writing style preferences
- Character guidelines

**Fill this out first** - it guides everything Claude does.

### STORY_GENOME.md
Your **story roadmap** (flexible):
- Act structure and plot points
- Major themes
- Character arcs
- World-building details

This helps Claude understand the bigger picture while staying responsive to your choices.

### NAMING_CONVENTIONS.md
**Pre-filled with fantasy examples**, but customize for your world:
- Character naming patterns (for different cultures/races)
- Location naming patterns
- Organization names
- Legendary item names

Claude uses this to generate new NPCs and places that fit your world.

### SCENE_NOTES.md
**Update between sessions** to guide the current session:
- Where the story is right now
- Key NPCs in this scene
- Your session goals
- Important context to remember

---

## Character Sheets

### {{user}}.md - Your Character
- Your hero's name, appearance, personality
- Skills, equipment, motivations
- Background and relationships
- What drives your character forward

**Make this detailed** - Claude uses it to understand how to play alongside you.

### {{char}}.md - Your Main Companion
- The NPC Claude will play most often
- Their personality, motivations, history
- How they relate to your character
- Their own goals and conflicts

**This NPC should be a real character**, not just a helper. Give them depth!

---

## Starting Your Adventure

### Chapter 1 - Your Opening

The `chapters/chapter_001.md` file has prompts to help you begin:

1. **Choose your starting point:**
   - Humble beginning
   - Already in progress
   - Moment of change
   - Mystery unfolds

2. **Write your opening scene** when you launch the RP

3. **Type your first message** describing the scene and your character's actions

4. **Let Claude respond** and your story unfolds from there!

---

## Tips for Success

### Before You Start
- [ ] Rename RP_NAME.md to your RP name
- [ ] Fill out AUTHOR'S_NOTES.md (most important!)
- [ ] Complete STORY_GENOME.md with your plot outline
- [ ] Detail your character(s) in the character sheets
- [ ] Review NAMING_CONVENTIONS.md and customize as needed

### During Play
- [ ] Be descriptive in your opening scenes
- [ ] Let your character make choices and take actions
- [ ] Develop your relationship with NPCs gradually
- [ ] Don't be afraid to diverge from your plan - that's where the magic happens!
- [ ] Use SCENE_NOTES.md to remind Claude of important context

### Between Sessions
- [ ] Update SCENE_NOTES.md with where you left off
- [ ] Note any important revelations or character changes
- [ ] Plan what you want from the next session
- [ ] Keep your character sheets current

---

## Fantasy Adventure Starting Ideas

### The Prophecy
A mysterious prophecy surrounds your character. They must uncover its meaning and decide whether to fulfill or defy it.

### The Quest
An NPC gives you a task: recover a stolen artifact, rescue someone, or reach a distant location. The journey reveals much larger stakes.

### The Curse
Your character, a companion, or the land itself is cursed. Breaking it requires adventure, sacrifice, and self-discovery.

### The Awakening
Your character discovers they have magical powers, are royalty, are the chosen one, or have a hidden destiny.

### The Escape
Your character flees from something (persecution, death, a terrible past) and must build a new life while being hunted.

### The Revenge
Someone wronged your character or their loved ones. The quest for justice becomes a journey of deeper understanding.

### The Mystery
An unsolved crime, disappearance, or dark secret draws your character into investigation that reveals shocking truths.

---

## Customization Guide

### Adding More Characters

Create additional character files in `characters/`:
- `characters/ally_name.md` - Additional allies
- `characters/villain_name.md` - Antagonists
- `characters/mentor_name.md` - Teachers or guides

### Expanding Your World

Add details to:
- **NAMING_CONVENTIONS.md** - Add more cultures, factions, naming patterns
- **locations/** - Create detailed location descriptions
- **STORY_GENOME.md** - Expand world-building details

### Creating Variants

Copy this template multiple times for different RPs:
- Copy `fantasy_adventure/` folder
- Rename for your new RP
- Customize the files
- Launch each as a separate RP

---

## Frequently Asked Questions

**Q: Can I skip filling out the templates?**
A: No, but you can fill out minimally:
- AUTHOR'S_NOTES.md: At minimum, set your tone and boundaries
- STORY_GENOME.md: At least outline Act 1
- Character sheets: Fill these out - Claude needs to know who you are
- SCENE_NOTES.md: Update before each session

**Q: Can I change the setting to sci-fi or modern?**
A: Yes! This template is just a starting point. Modify NAMING_CONVENTIONS.md, AUTHOR'S_NOTES.md, and STORY_GENOME.md to match your world.

**Q: What if I mess up the file formatting?**
A: Just fix it and re-launch. Markdown is forgiving. If something breaks, you can delete and run the setup script again.

**Q: Can I have multiple companions?**
A: Absolutely! Create more character files in `characters/`. Just remember that {{char}} is your "main" NPC.

**Q: How do I add NPCs during the story?**
A: Simply introduce them in your writing. Claude will create them based on your NAMING_CONVENTIONS.md and character descriptions.

---

## Need Help?

- **Stuck on story structure?** Check STORY_GENOME.md examples
- **Need character ideas?** Review the character sheet templates
- **Want naming ideas?** Look at NAMING_CONVENTIONS.md fantasy examples
- **Trouble with Claude's responses?** Review AUTHOR'S_NOTES.md - be more specific with your rules

For system help, see the main project documentation:
- [LAUNCHER_DOCUMENTATION.md](../../../Working\ Guides/LAUNCHER_DOCUMENTATION.md)
- [SYSTEM_ARCHITECTURE.md](../../../Working\ Guides/SYSTEM_ARCHITECTURE.md)

---

## Let Your Adventure Begin!

This template gives you the structure, but **your imagination provides the magic**.

- Make bold choices
- Let your character surprise you
- Develop real relationships with NPCs
- Follow the story where it wants to go
- Have fun!

**Ready?** Launch your RP and start typing:

```bash
python launch_rp_tui.py "Your RP Name"
```

Your epic fantasy adventure awaits! 🗡️✨
