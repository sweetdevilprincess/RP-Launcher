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

