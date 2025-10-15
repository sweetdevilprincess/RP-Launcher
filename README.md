# RP Claude Code

An advanced roleplay launcher for Claude Code with intelligent automation, prompt caching, and background analysis. Create immersive, long-form roleplays with AI assistance while maintaining perfect continuity and consistency.

---

## ✨ Key Features

### 🚀 Quick Setup System
- **One-command RP creation** - Complete RP setup with templates in seconds
- **Comprehensive templates** - Character sheets, story guides, and all required files
- **Three user paths** - 5-minute quick start, 30-minute guided, or 2-minute expert setup

### 🧠 Extended Thinking Modes
- **6 thinking modes** - From disabled to ultrathink (5k-32k tokens)
- **Granular control** - Match thinking depth to task complexity
- **Performance optimization** - Avoid over-thinking simple tasks

### 🤖 Background Automation
- **Intelligent agents** - Automatic entity extraction, memory creation, and story arc analysis
- **Non-blocking processing** - Agents work in background while you write
- **Performance metrics** - Detailed timing breakdowns and optimization recommendations

### 💾 Prompt Caching
- **54-61% token reduction** - Massive cost savings on long RPs
- **Automatic cache management** - Smart invalidation and updates
- **Cross-session persistence** - Cache survives restarts

### 🔄 Seamless Workflow
- **F10 bridge restart** - Apply settings without closing launcher
- **F9 settings screen** - Configure API keys, thinking modes, and more
- **F1-F8 overlays** - Quick access to memory, characters, arc, and references

### 🌐 Flexible API Support
- **OpenRouter integration** - Use DeepSeek, Claude, GPT, and other models
- **Direct Anthropic API** - Use Claude directly with your API key
- **Model switching** - Change models without code changes

### 📦 Auto Updates
- **GitHub update checker** - Automatic notification of new versions
- **Semantic versioning** - Clear version tracking with git tags
- **24-hour caching** - Respects API rate limits

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for SDK bridge)
- **Git**
- **API Key**: Anthropic or OpenRouter

### Installation

```bash
# Clone repository
git clone https://github.com/sweetdevilprincess/RP-Launcher.git
cd Rp-Launcher

# Install dependencies
pip install -r requirements.txt

# Install Node dependencies
cd src
npm install
cd ..
```

### Create Your First RP

Use the quick setup script to create a complete RP in one command:

```bash
python setup/quick_setup.py "My RP Name"
```

This creates:
- Complete folder structure
- Character templates ({{user}}.md, {{char}}.md)
- Story guidance files (AUTHOR'S_NOTES.md, STORY_GENOME.md)
- State files and configuration
- Example chapter template

### Configure API Keys

Launch the system and press **F9** to configure:

```bash
python launch_rp_tui.py
```

- **Anthropic API key** (for Claude direct) - starts with `sk-ant-`
- **OpenRouter API key** (for DeepSeek/other models) - starts with `sk-or-v1-`

### Start Writing!

Press **Ctrl+Enter** to send messages, **F1-F8** for quick reference overlays, **F10** to restart the bridge after settings changes.

---

## 📖 Documentation

### Getting Started
- **[Quick Start Guide](docs/guides/QUICK_START.md)** - 5-minute setup
- **[Setup Guide](setup/README.md)** - Comprehensive setup instructions
- **[Setup Checklist](setup/CHECKLIST.md)** - Verify your installation
- **[Creating Your First RP](setup/guides/02_CREATING_YOUR_FIRST_RP.md)** - Complete walkthrough

### User Guides
- **[Launcher Guide](docs/guides/LAUNCHER_GUIDE.md)** - Using the TUI interface
- **[Thinking Modes](docs/THINKING_MODES.md)** - Choosing the right thinking mode (6 modes explained)
- **[Automation Guide](docs/guides/AUTOMATION_GUIDE.md)** - Background agents and automation
- **[System Overview](docs/guides/SYSTEM_OVERVIEW.md)** - How everything works together

### Technical Reference
- **[RP System Overview](docs/guides/RP_SYSTEM_OVERVIEW.md)** - RP folder structure and file reference
- **[Update Checker](docs/guides/UPDATE_CHECKER.md)** - Auto-update system documentation
- **[Planned Features](docs/planned_features/)** - Upcoming features and roadmap

---

## 🎯 Key Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Enter** | Send message to Claude |
| **F9** | Open settings (API keys, thinking mode, model) |
| **F10** | Restart bridge (apply settings changes) |
| **F1** | Help overlay |
| **F2** | Memory overlay |
| **F3** | Story arc overlay |
| **F4** | Characters overlay |
| **F5** | Scene notes overlay |
| **F6** | Entities overlay |
| **F7** | Story genome overlay |
| **F8** | Current state overlay |

---

## 🧠 Thinking Modes

| Mode | Token Budget | Use Case | Speed Impact |
|------|--------------|----------|--------------|
| **disabled** | 0 | No thinking - fastest responses | Baseline |
| **think** | ~5,000 | Quick planning, simple tasks | +5-10s |
| **think hard** | ~10,000 | Feature design, debugging | +10-20s |
| **megathink** | 10,000 | Standard reasoning (default) | +10-20s |
| **think harder** | ~25,000 | Complex architecture decisions | +30-60s |
| **ultrathink** | 31,999 | System design, major refactoring | +1-3min |

Configure in settings (F9) or in `config/config.json`.

---

## 📊 Example Project Structure

```
RP Claude Code/
├── README.md                   # Main project overview
├── launch_rp_tui.py           # Main launcher (start here!)
├── requirements.txt            # Python dependencies
├── config/                     # Configuration files
│   ├── config.json            # Main configuration
│   ├── CLAUDE.md              # Project instructions for Claude Code
│   ├── guidelines/            # Custom guidelines
│   └── templates/             # File templates
├── docs/                       # Documentation
│   ├── THINKING_MODES.md      # Thinking mode documentation
│   ├── guides/                # User guides
│   ├── planned_features/      # Roadmap
│   └── changelogs/            # Release notes
├── setup/                      # Setup system
│   ├── quick_setup.py         # One-command RP creation
│   ├── README.md              # Setup documentation
│   └── templates/             # RP templates
├── src/                        # Source code
│   ├── rp_client_tui.py       # TUI application
│   ├── tui_bridge.py          # Bridge process
│   ├── clients/               # API clients
│   └── automation/            # Background agents
└── Example RP/                 # Example RP for reference
```

---

## 🏗️ Architecture

### Three-Process System

1. **TUI (Textual)** - User interface
2. **Bridge** - Connects TUI to Claude Code/API
3. **Claude Code/API** - AI inference

### Two Operating Modes

**SDK Mode (Default)**:
- Uses Claude Code SDK bridge
- Full feature support
- Auto-detects VS Code integration

**API Mode**:
- Direct API calls to Anthropic or OpenRouter
- No VS Code required
- Configure in settings (F9)

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
