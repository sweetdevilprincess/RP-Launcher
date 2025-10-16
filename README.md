# RP Launcher - AI-Powered Roleplay Campaign Manager

**A sophisticated roleplay automation system that feels like having a DM/GM, not a chatbot.**

Built for long-form, persistent storytelling with intelligent continuity tracking, automated memory management, and context-aware responses.

---

## 🎯 What Is This?

RP Launcher is a **terminal-based roleplay system** that combines Claude AI with intelligent automation to manage complex, multi-session campaigns. Unlike traditional chatbots, it:

- **Remembers everything** - Automatic memory extraction and retrieval
- **Tracks relationships** - Dynamic character relationship monitoring
- **Manages plot threads** - Active thread detection and resolution tracking
- **Maintains consistency** - Entity cards, world facts, and contradiction detection
- **Optimizes context** - Smart tier-based loading (54-96% token reduction)
- **Feels like a DM** - Campaign continuity, not conversation threads

---

## ✨ Key Features

### 🤖 **10-Agent Automation System**
- **4 Immediate Agents** (pre-response, 3-5s): Entity analysis, fact extraction, memory retrieval, plot thread loading
- **6 Background Agents** (post-response, hidden): Memory creation, relationship tracking, plot detection, knowledge extraction, response analysis, contradiction detection

### 🧠 **Intelligent Memory System**
- Multi-dimensional memory indexing (characters, location, tone, timestamp, relationship impact)
- Semantic memory retrieval (2-5 most relevant memories per character)
- Automatic memory creation from significant moments
- 96% token reduction vs loading all memories

### 📊 **Campaign Management**
- Entity cards for characters, locations, organizations
- Relationship tracking with tier system (enemy → stranger → friend → close friend)
- Plot thread lifecycle management (active → critical → resolved)
- World-building knowledge base with fact extraction
- Story arc generation and tracking

### ⚡ **Performance Optimization**
- Prompt caching (54-61% token savings)
- Tier-based entity loading (Tier 1: full, Tier 2: facts only, Tier 3: skip)
- Debounced file writes (50-80% I/O reduction)
- Parallel agent execution (ThreadPoolExecutor)
- Hidden background processing (completes while you type)

### 🎨 **Rich Terminal Interface**
- Multi-line text input with Ctrl+Enter to send
- Real-time context display (chapter, time, location, characters)
- F-key overlays (character sheets, story arc, entities, settings)
- Progress tracking and status indicators
- Keyboard shortcuts for quick access

---

## 🤔 Why Does This Exist?
tldr: I hate the chatbot feel and I am sure other people to too.

**Problem:** Existing tools like SillyTavern are optimized for **chatbot interaction** - short conversations with character cards. They don't handle:
- Long-form campaigns (50+ sessions)
- Plot thread management
- Persistent world-building
- Campaign continuity across weeks/months
- DM/GM-style storytelling

**Solution:** RP Launcher is built from the ground up for **persistent campaign management** with:
- Automated continuity tracking
- Smart context management (only loads relevant info)
- Background analysis (doesn't slow you down)
- Multi-dimensional memory system
- Campaign-first architecture

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for SDK bridge)
- Git
- API Key: Anthropic (for Claude) or OpenRouter (for DeepSeek)

### Installation

```bash
# Clone repository
git clone https://github.com/sweetdevilprincess/RP-Launcher.git
cd RP-Launcher

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for SDK bridge)
cd src
npm install
cd ..
```

### Create Your First RP

**Coming soon is a better thing to do this**

```bash
# Use quick setup script
python setup/quick_setup.py "My Campaign Name"

# This creates:
# - Complete folder structure
# - Character templates
# - Story guidance files
# - State tracking files
# - Configuration
```

### Launch

```bash
# Auto-detect single RP or show menu for multiple
python launch_rp_tui.py

# Or specify RP name
python launch_rp_tui.py "My Campaign Name"

# Start typing and press Ctrl+Enter to send!
```

---

## 🎮 Usage

<<<<<<< Updated upstream
### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+Enter** | Send message |
| **F1** | Help overlay |
| **F2** | Character sheet + memory |
| **F3** | Story arc + genome |
| **F4** | Entity list |
| **F5** | Scene notes |
| **F6** | Module toggles |
| **F7** | Status display |
| **F8** | Settings |
| **F10** | Restart bridge |
| **Ctrl+Q** | Quit |

### F-Key Overlays

Press any F-key to open an overlay with relevant information:
- **Character sheets** with current memory
- **Story arc** progress and next developments
- **Entity cards** (characters, locations, organizations)
- **Scene notes** for current session
- **Module toggles** (enable/disable automation)
- **Status** (response count, arc progress, active characters)
- **Settings** (API keys, models, thinking modes)
=======
### Start Here
- **[CLAUDE.md](CLAUDE.md)** - Project instructions and guidelines (READ FIRST!)
- **[Working Guides/DOCUMENTATION_INDEX.md](Working Guides/DOCUMENTATION_INDEX.md)** - Master navigation hub

### Getting Started
- **[Setup Guide](setup/README.md)** - Comprehensive setup instructions
- **[Setup Checklist](setup/CHECKLIST.md)** - Verify your installation
- **[Creating Your First RP](setup/guides/02_CREATING_YOUR_FIRST_RP.md)** - Complete walkthrough
- **[Quick Start Guide](docs/guides/QUICK_START.md)** - 5-minute setup

### User Guides
- **[Launcher Documentation](Working Guides/LAUNCHER_DOCUMENTATION.md)** - Complete launcher system reference (NEW)
- **[Automation Guide](docs/guides/AUTOMATION_GUIDE.md)** - Background agents and automation
- **[System Overview](docs/guides/SYSTEM_OVERVIEW.md)** - How everything works together
- **[Proxy Mode Guide](docs/guides/PROXY_MODE_GUIDE.md)** - Custom prompt injection

### Technical Reference
- **[RP Directory Map](Working Guides/RP_DIRECTORY_MAP.md)** - Complete RP file structure and interactions
- **[System Architecture](Working Guides/SYSTEM_ARCHITECTURE.md)** - Overall system design
- **[Agent Documentation](Working Guides/AGENT_DOCUMENTATION.md)** - Background automation agents
- **[Prompt Caching Guide](docs/guides/PROMPT_CACHING_GUIDE.md)** - Token reduction strategies
- **[Planned Features](docs/planned_features/)** - Upcoming features and roadmap

---

## 🎯 Key Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Enter** | Send message to Claude |
| **Enter** | New line in input (not send) |
| **Ctrl+Q** | Quit launcher |
| **F1** | Help - Display keyboard shortcuts |
| **F2** | Character Sheet - View {{user}} character + memory |
| **F3** | Story Overview - View story arc + STORY_GENOME |
| **F4** | Entities - View entity cards (by type) |
| **F5** | Scene Notes - View session guidance |
| **F6** | Modules - Toggle automation features |
| **F7** | Status - View RP progress and state |
| **F8** | Settings - Configure API keys and modes |
| **F10** | Restart Bridge - Restart backend process |
>>>>>>> Stashed changes

---

## ⚙️ Configuration

### Global Config (`config/config.json`)
```json
{
  "use_api_mode": false,
  "thinking_mode": "megathink",
  "check_for_updates": true
}
```

### Per-RP Config (`{RP}/state/automation_config.json`)
```json
{
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50,
  "auto_memory_update": true,
  "memory_frequency": 15
}
```

---

## 🎨 Example: Memory System in Action

**During Response 47:**
```
User: "I want to go to the Rose bar next week"
    ↓
Entity Analysis Agent:
    ├─ Detects: "Rose bar" (Tier 2 - mentioned but absent)
    └─ Extracts 5 key facts:
        • Location: Downtown, near Bruno's
        • Hours: Tue-Sat, 8pm-2am
        • Known for: Live jazz music
        • Owner: Marcus
        • Atmosphere: Upscale, dim lighting
    ↓
Claude: "Oh, that's the one by Bruno's, right? 
         I heard they have great jazz on Thursdays."
    ↓
Background Agents (after response):
    ├─ Memory Creation: New memory for character about planning visit
    ├─ Knowledge Extraction: Bar hours, location confirmed
    └─ Plot Thread: "Visit to Rose bar" added (low priority)
```

<<<<<<< Updated upstream
**Next session (Response 65):**
```
User: "We're at the Rose bar now"
    ↓
Memory Extraction Agent:
    └─ Loads relevant memory: "Planning to visit Rose bar (Response 47)"
    ↓
Entity Analysis Agent:
    └─ Rose bar now Tier 1 (scene participant) - full card loaded
    ↓
Claude: "The dim lighting and soft jazz create exactly 
         the atmosphere you were hoping for when you 
         suggested this place two weeks ago..."
```

**Perfect continuity without manual tracking.**
=======
1. **Launcher** (`launch_rp_tui.py`) - Entry point and process manager
2. **TUI** (`rp_client_tui.py`) - User interface (Textual)
3. **Bridge** (`tui_bridge.py`) - Backend connecting TUI to Claude

### Two Operating Modes

**SDK Mode (Default)** - No API Key Required:
- Uses Claude Code SDK bridge (Node.js wrapper)
- High-performance streaming responses
- Perfect for local development
- No API key setup needed

**API Mode** - Direct Claude API:
- Direct Anthropic Claude API access
- Requires API key (set in F8 Settings)
- Full token visibility and control
- Automatic fallback to SDK if key unavailable

See [TUI Bridge Documentation](Working Guides/TUI_BRIDGE_DOCUMENTATION.md) for complete details on both modes.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [planned features](docs/planned_features/) for areas that need work.

---

## 📜 License

[Add your license here - MIT, Apache 2.0, etc.]

---

## 🌟 Community

- **[GitHub Issues](https://github.com/[USERNAME]/[REPO]/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/[USERNAME]/[REPO]/discussions)** - Questions and community support

---

## 🎯 Credits

Created by [Your Name/Username]

Powered by Claude (Anthropic) and DeepSeek

---

**Version**: 1.0.0 | **Last Updated**: October 2025

Ready to create immersive roleplays? Run `python setup/quick_setup.py "My RP Name"` to get started!
>>>>>>> Stashed changes
