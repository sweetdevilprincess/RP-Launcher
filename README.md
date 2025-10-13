# RP Claude Code System

**High-performance TUI for immersive roleplay with Claude Code**

A complete system for running long-form, immersive roleplays with Claude, featuring intelligent automation, prompt caching, and a beautiful terminal interface.

---

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   cd src && npm install
   ```

2. **Set Up Your RP**
   - Copy `Example RP/` folder
   - Rename to your RP name
   - Edit files (characters, story genome, etc.)

3. **Launch**
   ```bash
   python launch_rp_tui.py
   ```

That's it! Two windows will open (TUI + Bridge).

---

## ✨ Features

### Intelligent Automation
- **Auto Entity Tracking** - Tracks characters, locations, items automatically
- **Smart Time Calculation** - Calculates elapsed time from activities
- **Conditional File Loading** - Loads relevant context based on mentions
- **Story Arc Generation** - Auto-generates story arcs every 50 responses

### High Performance SDK
- **10-50x Faster** - No subprocess overhead
- **Real-time Streaming** - See responses as they generate
- **Prompt Caching** - 70-90% cost savings on cached content
- **Visible Cache Stats** - See exactly what's cached

### Beautiful TUI
- **Multi-line Input** - No glitches, unlimited length
- **Quick Access Overlays** (F1-F8) - Memory, Arc, Characters, etc.
- **Real-time Context** - Chapter, time, location, progress bars
- **Clean Interface** - Distraction-free writing

---

## 📖 Documentation

### Getting Started
- [Quick Start Guide](docs/guides/QUICK_START.md) - Complete setup walkthrough
- [System Overview](docs/guides/SYSTEM_OVERVIEW.md) - How everything works
- [Launcher Guide](docs/guides/LAUNCHER_GUIDE.md) - Using the launcher

### Features & Guides
- [Automation Guide](docs/guides/AUTOMATION_GUIDE.md) - Entity tracking, time calc, auto-generation
- [File Loading Tiers](docs/guides/FILE_LOADING_TIERS.md) - TIER_1/2/3 system explained
- [Prompt Caching Guide](docs/guides/PROMPT_CACHING_GUIDE.md) - Save 70-90% on costs
- [Proxy Mode Guide](docs/guides/PROXY_MODE_GUIDE.md) - Custom prompt injection

### Reference
- [RP Folder Structure](docs/reference/RP_FOLDER_STRUCTURE.md) - Complete folder guide
- [SDK Documentation](docs/reference/SDK/) - High-performance SDK details

---

## 📁 Project Structure

```
RP Claude Code/
├── launch_rp_tui.py        # 👈 START HERE - Main launcher
├── requirements.txt         # Python dependencies
│
├── src/                     # Core system code
│   ├── rp_client_tui.py     # TUI interface
│   ├── tui_bridge.py        # Bridge + automation
│   ├── package.json         # Node.js dependencies
│   └── clients/             # Client modules
│       ├── claude_sdk.py    # Claude SDK (Python)
│       ├── claude_sdk_bridge.mjs  # SDK bridge (Node.js)
│       ├── claude_api.py    # Direct API client
│       └── deepseek.py      # DeepSeek API
│
├── docs/                    # Documentation
│   ├── guides/              # How-to guides
│   ├── reference/           # Technical reference
│   └── archive/             # Old docs
│
├── config/                  # Configuration
│   ├── templates/           # RP templates
│   ├── guidelines/          # RP guidelines
│   ├── config.json          # System config
│   └── proxy_prompt.txt     # Proxy mode prompt
│
└── [Your RP Folders]/       # Your RP instances
    ├── Example RP/
    └── [Other RPs]/
```

---

## 🎮 Usage

### Daily Workflow

1. **Launch**
   ```bash
   python launch_rp_tui.py
   ```

2. **Type your message** in the TUI

3. **Press Ctrl+Enter** to send

4. **Use F1-F8** for quick access:
   - F1: Help
   - F2: User Memory
   - F3: Story Arc
   - F4: Characters
   - F5: Scene Notes
   - F6: Entity Tracker
   - F7: Story Genome
   - F8: Status

5. **Watch the bridge** for automation activity (optional)

### Commands

- `/new` - Start fresh conversation
- `Ctrl+Q` - Quit

---

## 💾 Configuration

### Mode Selection

**SDK Mode (Default)** - Fast, cached, streaming:
```json
{
  "use_api_mode": false
}
```

**API Mode** - Direct API, custom caching:
```json
{
  "use_api_mode": true,
  "anthropic_api_key": "your-key"
}
```

### Automation

Edit `{your RP}/state/automation_config.json`:
```json
{
  "entity_tracking": {
    "enabled": true,
    "threshold": 3
  },
  "arc_generation": {
    "enabled": true,
    "interval": 50
  }
}
```

---

## 🛠️ Requirements

- **Python 3.10+**
- **Node.js 18+** (for SDK mode)
- **Claude Code CLI** (installed and in PATH)
- Python packages (see requirements.txt)

---

## 📊 Performance

### Speed Comparison
| Mode | First Call | Subsequent | Streaming |
|------|-----------|------------|-----------|
| Old CLI | ~1.5s | ~1.5s | No |
| SDK (New) | ~0.05s | ~0.01s | Yes |

### Cost Savings with Caching
| Session | Without Caching | With Caching | Savings |
|---------|----------------|--------------|---------|
| 10 messages | $0.375 | $0.105 | 72% |

---

## 🤝 Contributing

This is a personal RP system, but feel free to fork and adapt for your own use!

---

## 📝 License

MIT License - Feel free to modify and use as you wish.

---

## 🔗 Related Projects

- [Claude Code](https://claude.com/claude-code) - Official Anthropic CLI
- [Textual](https://textual.textualize.io/) - TUI framework

---

## 💬 Support

Check the [documentation](docs/guides/) for detailed guides and troubleshooting.

For issues with the SDK bridge, see [SDK docs](docs/reference/SDK/).

---

**Happy RP'ing!** 🎭✨
"# RP-Launcher" 
