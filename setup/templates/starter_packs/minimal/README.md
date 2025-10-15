# Minimal Template - Quick Start RP

**Version:** 1.0
**Type:** Starter Pack
**Difficulty:** Beginner-friendly

---

## 📦 What's This Template?

This is a **complete, ready-to-use RP structure** with all required files and helpful templates.

**Perfect for:**
- ✅ First-time users who want to get started quickly
- ✅ Anyone who wants a clean slate with helpful guidance
- ✅ Users who prefer to fill in templates rather than create from scratch

**Includes:**
- All required directory structure
- All necessary state files (pre-configured)
- Template files with examples and instructions
- Character sheet templates for {{user}} and NPCs
- Starter chapter template with writing tips

---

## 🚀 Quick Start (2 Methods)

### Method 1: Using the Script (Easiest)

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python setup/quick_setup.py "My New RP" --template minimal
```

**Done!** The script copies this template and sets up everything.

### Method 2: Manual Copy

1. **Copy this entire folder** to the `RPs/` directory in your project
2. **Rename the folder** to your RP name (e.g., "My New RP")
3. **Rename `RP_NAME.md`** to match your folder (e.g., "My New RP.md")
4. **Fill in the templates** (see below)
5. **Launch:** `python launch_rp_tui.py "My New RP"`

---

## 📁 What's Included

### Directory Structure

```
Your RP Name/
├── RP_NAME.md                    ← Rename to match your RP folder!
├── AUTHOR'S_NOTES.md             ← Story rules (optional but recommended)
├── STORY_GENOME.md               ← Story direction (optional but recommended)
├── SCENE_NOTES.md                ← Current session notes (optional)
├── chapters/
│   └── chapter_001.md            ← Write your opening scene here!
├── characters/
│   ├── {{user}}.md               ← YOUR character (REQUIRED)
│   └── {{char}}.md               ← Main NPC template (optional)
├── entities/                     ← Auto-generated entity cards
├── state/                        ← System files (REQUIRED)
│   ├── plot_threads_master.md
│   ├── current_state.md
│   ├── automation_config.json
│   ├── entity_tracker.json
│   ├── file_tracking.json
│   └── response_counter.json
├── memories/                     ← Character memories (optional)
├── relationships/                ← Relationship tracking (optional)
├── locations/                    ← Location details (optional)
├── sessions/                     ← Session logs (auto-created)
└── exports/                      ← Exported content
```

### File Status Legend
- ✅ **REQUIRED** - Must fill out before launching
- ⭐ **RECOMMENDED** - Strongly suggested for best experience
- ⭕ **OPTIONAL** - Nice to have but not necessary

---

## 📝 Step-by-Step Setup

### Step 1: Rename Files ✅ REQUIRED

1. Rename the RP folder to your desired name
2. Rename `RP_NAME.md` to match (e.g., "Epic Quest.md" if folder is "Epic Quest")

### Step 2: Fill in Core Files

#### `RP_NAME.md` - ⭐ RECOMMENDED
**What it is:** Overview of your RP
**Time:** 5 minutes
**Action:**
- Open the file
- Fill in the template sections
- Define genre, setting, premise
- Add your main characters

#### `characters/{{user}}.md` - ✅ REQUIRED
**What it is:** YOUR character sheet
**Time:** 10-15 minutes
**Action:**
- Open the file
- Fill in your character's details
- Be honest about flaws and weaknesses
- Define their goals and motivations

**Minimum to fill:**
- Name, age, gender
- Basic appearance
- Core personality traits
- Current situation

#### `chapters/chapter_001.md` - ✅ REQUIRED (file must exist)
**What it is:** Your first chapter file
**Time:** 0-20 minutes (or leave blank!)
**Options:**

**Option 1: Leave it blank (Easiest)**
- The template file is already set up
- Start writing directly in the TUI when you launch
- Perfect for starting fresh!

**Option 2: Pre-write your opening**
- Open the file and write your opening scene
- Read the tips in the comments (optional)
- Continue in the TUI when you launch

**Note:** The file must exist, but it can be empty. You'll write your story in the TUI!

### Step 3: Optional But Helpful Files

#### `AUTHOR'S_NOTES.md` - ⭐ RECOMMENDED
**What it does:** Sets absolute rules for your story
**Time:** 5-10 minutes
**Why use it:**
- Prevents story directions you don't want
- Ensures important events happen
- Defines your writing style preferences

**Quick setup:**
- List a few things that MUST happen
- List a few things that MUST NOT happen
- Define your preferred writing style

#### `STORY_GENOME.md` - ⭐ RECOMMENDED
**What it does:** Defines your intended story direction
**Time:** 10-15 minutes
**Why use it:**
- Helps Claude understand where you're going
- Provides story arc structure
- Keeps themes and goals in focus

**Quick setup:**
- Fill in genre and setting
- Outline basic story beats
- List themes you want to explore

#### `SCENE_NOTES.md` - ⭕ OPTIONAL
**What it does:** Guides the current session
**Time:** 2-3 minutes per session
**Why use it:**
- Focus Claude on session goals
- Track who's in the current scene
- Set mood and atmosphere

**Quick setup:**
- Update before each session
- Delete after session ends
- Keep it brief and focused

#### `characters/{{char}}.md` - ⭕ OPTIONAL
**What it does:** Template for your main NPC
**Time:** 5-10 minutes
**Why use it:**
- Create a companion or important NPC
- Give them depth and personality
- You can also let Claude create NPCs organically

**Note:** You can create NPCs as you go! The automation system will generate entity cards when characters are mentioned multiple times.

### Step 4: Review State Files ✅ REQUIRED

The `state/` directory is already set up with default configurations. You don't need to edit these files unless you want to customize automation.

**Files in `state/` directory:**
- `plot_threads_master.md` - Plot tracking (auto-updated)
- `current_state.md` - Current story state (auto-updated)
- `automation_config.json` - Automation settings
- `entity_tracker.json` - Entity mentions (auto-managed)
- `file_tracking.json` - File tracking (auto-managed)
- `response_counter.json` - Message counter (auto-managed)

**To customize automation:**
Open `state/automation_config.json` and adjust:
- `entity_mention_threshold` - How many mentions before creating entity card (default: 2)
- `arc_frequency` - How often to update story arc (default: every 50 messages)
- `auto_entity_cards` - Enable/disable entity extraction (default: true)

### Step 5: Launch Your RP! 🚀

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
python launch_rp_tui.py "Your RP Name"
```

**What happens:**
1. Launcher checks for updates
2. Finds your RP folder
3. Starts the bridge
4. Opens the TUI interface

**Start writing:**
1. Type your first message
2. Press Ctrl+Enter to send
3. Claude responds
4. Your story begins!

---

## ⚙️ Configuration Options

### Automation Settings

Edit `state/automation_config.json`:

```json
{
  "auto_entity_cards": true,        // Auto-create entity cards
  "entity_mention_threshold": 2,    // Mentions needed before card
  "auto_story_arc": true,           // Auto-update story arc
  "arc_frequency": 50,              // Update every N messages
  "auto_memory": false,             // Auto-create memories (experimental)
  "memory_frequency": 25            // Create memory every N messages
}
```

**Recommended settings for beginners:**
- Keep defaults unless you have a reason to change
- Enable `auto_entity_cards` to track characters automatically
- Set `entity_mention_threshold` to 2 or 3
- Enable `auto_story_arc` to track plot development

### Launcher Settings

Press **F9** in the launcher to configure:
- API keys (OpenRouter or Anthropic)
- Model selection (if using OpenRouter)
- Thinking modes
- API mode vs SDK mode

---

## 💡 Tips for Success

### Before You Start

**Do:**
- ✅ Fill in at least {{user}}.md character sheet
- ✅ Write an opening in chapter_001.md
- ✅ Skim through AUTHOR'S_NOTES.md template for ideas
- ✅ Read the guide: `setup/guides/02_CREATING_YOUR_FIRST_RP.md`

**Don't:**
- ❌ Try to fill out every single field
- ❌ Spend hours on backstory before starting
- ❌ Worry about making it "perfect"
- ❌ Forget you can update files as you go!

### During Your RP

**Do:**
- ✅ Update character sheets as they develop
- ✅ Add NPCs to `characters/` as they become important
- ✅ Use SCENE_NOTES.md for session-specific guidance
- ✅ Check F-key overlays (F1-F9) for info and settings

**Don't:**
- ❌ Feel locked into your initial plans
- ❌ Rush through interesting moments
- ❌ Ignore the automation features (they help!)
- ❌ Be afraid to experiment

---

## 📚 Next Steps

### After Setup
1. ✅ **Launch your RP** and send your first message
2. ✅ **Explore the TUI** - Try the F-key overlays (F1-F9)
3. ✅ **Write 5-10 messages** to get a feel for it
4. ✅ **Check entity extraction** - See what the system captures
5. ✅ **Update character sheet** as your character develops

### Learning More
- **Complete Guide:** `setup/guides/02_CREATING_YOUR_FIRST_RP.md`
- **Understanding Structure:** `setup/guides/03_UNDERSTANDING_STRUCTURE.md`
- **Writing Tips:** `setup/guides/04_WRITING_YOUR_STORY.md`
- **Advanced Features:** `setup/guides/05_ADVANCED_FEATURES.md`
- **Troubleshooting:** `setup/guides/99_TROUBLESHOOTING.md`

### Growing Your RP
- Add more characters as you meet them
- Create location files for important places
- Build relationship files for complex dynamics
- Use the memory system for character development
- Export your favorite scenes

---

## ❓ FAQ

### Q: Do I have to fill out every template field?
**A:** No! Fill in what feels relevant and skip the rest. You can always add more later.

### Q: Can I change things after I start?
**A:** Absolutely! All files can be edited anytime. The system is flexible.

### Q: What's the bare minimum to start?
**A:**
1. RP folder with correct name
2. {{user}}.md with basic character info
3. chapter_001.md with an opening scene
4. state/ directory with the included files

That's it! Everything else is optional.

### Q: How do I add more NPCs?
**A:** Just create new .md files in `characters/` directory. Name them whatever you want (e.g., "Zara the Merchant.md").

### Q: Can I use this for multiple RPs?
**A:** Yes! Copy the template for each new RP. Each RP is completely separate.

### Q: What if I mess something up?
**A:** Copy the template again! Or use the validation tool: `python setup/scripts/validate_rp.py "RP Name"` (coming soon)

---

## 🛠️ Customization

This template is a **starting point**, not a rigid structure!

**Feel free to:**
- Add new directories (like `factions/`, `events/`, `timelines/`)
- Create additional character templates
- Add custom tracking files
- Organize however makes sense to you
- Delete optional files you don't need

**Just don't delete:**
- The `state/` directory or its files
- Your RP overview file (RP_NAME.md)
- The `chapters/` directory

---

## 🆘 Troubleshooting

### "RP folder not found"
→ Make sure folder is in the `RPs/` directory, not inside `setup/templates/`

### "Missing state directory"
→ The `state/` folder must exist with all JSON files

### "Can't launch RP"
→ Check folder name matches exactly in the launch command

### "No response from Claude"
→ Press F9 to check API key settings

### Need more help?
→ See `setup/guides/99_TROUBLESHOOTING.md`

---

## 🎉 You're Ready!

Everything you need is here. Now go create something amazing!

**Remember:**
- There's no "right" way to roleplay
- Have fun and be creative
- Update files as you go
- Your story is unique—make it yours!

**Questions?** Check the guides in `setup/guides/` or the main `setup/README.md`

**Happy roleplaying!** ✨

---

**Template Version:** 1.0
**Last Updated:** October 2025
**Maintained By:** RP Launcher Project
