# Release Checklist for v1.0.0

**Date:** October 15, 2025
**Release Type:** Initial Public Release
**Branch:** main

---

## 🎯 Pre-Release Testing

### Core Features Testing

- [ ] **Update Checker**
  - [ ] Run `python src/update_checker.py --no-cache` to test GitHub API
  - [ ] Verify version detection: `python src/version.py`
  - [ ] Test with cache: Launch normally and check for update notification
  - [ ] Test offline behavior (disconnect internet, launch should work)

- [ ] **OpenRouter Configuration**
  - [ ] Launch TUI, press F9 for settings
  - [ ] Verify OpenRouter API key field shows correct placeholder
  - [ ] Test API key validation (should accept `sk-or-v1-` format)
  - [ ] Test model selection field
  - [ ] Change model, verify it's saved to config.json
  - [ ] Verify changes take effect immediately (no restart needed)

- [ ] **Thinking Modes**
  - [ ] Press F9, verify all 6 modes are listed:
    - [ ] disabled
    - [ ] think
    - [ ] think hard
    - [ ] megathink
    - [ ] think harder
    - [ ] ultrathink
  - [ ] Change thinking mode, save settings
  - [ ] Verify setting is saved to config.json

- [ ] **Bridge Restart (F10)**
  - [ ] Launch TUI
  - [ ] Press F9, change thinking mode
  - [ ] Press F10 to restart bridge
  - [ ] Verify "🔄 Restarting bridge..." notification appears
  - [ ] Verify bridge restarts successfully
  - [ ] Send a test message to confirm bridge is working

- [ ] **Background Agents**
  - [ ] Launch TUI with an RP
  - [ ] Send 2-3 messages
  - [ ] Check terminal output for "🎭 Automation orchestrator initialized"
  - [ ] Verify no orchestrator errors appear
  - [ ] Check `state/hook.log` for timing metrics
  - [ ] Verify entity extraction is working (check entities/ folder after mentioning someone 2+ times)

### RP Setup System Testing

- [ ] **Quick Setup Script**
  - [ ] Run: `python setup/quick_setup.py "Test RP"`
  - [ ] Verify all files are created
  - [ ] Verify directory structure is correct
  - [ ] Check that state/ files have proper content
  - [ ] Try with template: `python setup/quick_setup.py "Test RP 2" --template minimal`
  - [ ] Try custom path: `python setup/quick_setup.py "Test RP 3" --path "C:\Temp"`
  - [ ] Test overwrite protection (run same command twice without --overwrite)
  - [ ] Test overwrite flag: `python setup/quick_setup.py "Test RP" --overwrite`

- [ ] **Documentation Verification**
  - [ ] Open `setup/README.md` - verify all links work
  - [ ] Open `setup/CHECKLIST.md` - verify formatting is correct
  - [ ] Open `setup/guides/02_CREATING_YOUR_FIRST_RP.md` - skim for any errors
  - [ ] Open `setup/templates/starter_packs/minimal/README.md` - verify instructions are clear

- [ ] **Template Pack Verification**
  - [ ] Navigate to `setup/templates/starter_packs/minimal/`
  - [ ] Verify all required directories exist
  - [ ] Open character templates - verify they have content
  - [ ] Open state files - verify JSON is valid
  - [ ] Check that AUTHOR'S_NOTES.md, STORY_GENOME.md have helpful content

- [ ] **Launch Test RP Created by Setup Script**
  - [ ] Run: `python launch_rp_tui.py "Test RP"`
  - [ ] Verify RP is found and launches
  - [ ] Send a test message
  - [ ] Verify Claude responds
  - [ ] Check that automation is working (no errors in terminal)

---

## 📦 Git Repository Preparation

### Step 1: Check Git Status

```bash
cd "C:\Users\green\Desktop\RP Claude Code"
git status
```

Verify you see the expected new and modified files.

### Step 2: Add New Files (Core System)

```bash
# Version tracking and update checker
git add src/version.py
git add src/update_checker.py
git add docs/guides/UPDATE_CHECKER.md

# Changelog
git add CHANGELOG_2025-10-15.md

# Modified core files
git add .gitignore
git add launch_rp_tui.py
git add src/rp_client_tui.py
git add src/clients/deepseek.py
git add config/config.json.template
```

### Step 3: Add RP Setup System Files

```bash
# Core setup files
git add setup/README.md
git add setup/CHECKLIST.md
git add setup/quick_setup.py
git add setup/guides/02_CREATING_YOUR_FIRST_RP.md

# Template pack - add entire minimal directory
git add setup/templates/starter_packs/minimal/
```

### Step 4: Add Modified System Files

Review these files first to ensure changes are intentional:

```bash
# Review changes
git diff THINKING_MODES.md
git diff src/automation/__init__.py
git diff src/automation/core.py
git diff src/automation/orchestrator.py
git diff src/tui_bridge.py
git diff src/clients/claude_sdk_bridge.mjs
git diff src/clients/claude_api.py
git diff src/clients/claude_sdk.py
```

If changes look good, add them:

```bash
git add THINKING_MODES.md
git add src/automation/__init__.py
git add src/automation/core.py
git add src/automation/orchestrator.py
git add src/automation/status.py
git add src/tui_bridge.py
git add src/clients/claude_sdk_bridge.mjs
git add src/clients/claude_api.py
git add src/clients/claude_sdk.py
git add src/automation/agents/base_agent.py
git add src/automation/agent_coordinator.py
```

### Step 5: Add Documentation Files

```bash
# Performance and wiki docs (if you want to include them)
git add docs/planned_features/WRITER_AGENT.md
git add docs/WIKI_STRUCTURE.md
git add docs/WIKI_SETUP_GUIDE.md
git add docs/WIKI_QUICK_REFERENCE.md
git add docs/COMMUNITY_SHOWCASE_WIKI.md
```

### Step 6: Verify .gitignore

Ensure these are in .gitignore:

```bash
cat .gitignore | grep -E "config.json|update_check_cache"
```

Should show:
- `config.json` (root level - line 17)
- `.update_check_cache` (line 139)

### Step 7: DO NOT Add These Files

**CRITICAL**: Do not commit these files (they contain personal data):

```bash
# DO NOT add:
# - config.json (contains API keys)
# - Example RP/CURRENT_STATUS.md
# - Example RP/state/hook.log
# - Example RP/state/response_counter.json
# - Example RP/state/trigger_history.json
# - .update_check_cache
```

### Step 8: Review Staged Changes

```bash
git status
```

Verify all new files are staged (green) and personal files are not.

### Step 9: Commit Changes

```bash
git commit -m "Release v1.0.0: Initial public release

Major Features:
- Complete RP client TUI with automation
- OpenRouter API integration with model selection
- 6 configurable thinking modes
- In-app bridge restart (F10)
- Automatic GitHub update checker
- Complete RP setup system with templates

New Features:
- Quick setup script for fast RP creation
- Comprehensive documentation and guides
- Minimal template pack with 1000+ lines of templates
- Background agent performance metrics
- Extended thinking modes (think hard, think harder)

Bug Fixes:
- Fixed orchestrator initialization error
- Fixed OpenRouter API key validation
- Fixed restart warnings (only show when changed)
- Fixed thinking mode selection

See CHANGELOG_2025-10-15.md for complete details.

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 🏷️ Create Git Tag

### Step 1: Create Annotated Tag

```bash
git tag -a v1.0.0 -m "RP Launcher v1.0.0 - Initial Public Release

First stable release of RP Launcher with complete automation system.

Features:
- Full RP client TUI with automation
- OpenRouter API integration
- 6 configurable thinking modes
- In-app bridge restart (F10)
- Automatic GitHub update checker
- Complete RP setup system with templates and guides

See CHANGELOG_2025-10-15.md for details."
```

### Step 2: Verify Tag

```bash
git tag -l
git show v1.0.0
```

Verify the tag is created and points to the correct commit.

---

## 🚀 Push to GitHub

### Step 1: Push Commits

```bash
git push origin main
```

Wait for push to complete. Check for any errors.

### Step 2: Push Tags

```bash
git push origin --tags
```

This pushes the v1.0.0 tag to GitHub.

### Step 3: Verify on GitHub

- [ ] Go to: `https://github.com/YOUR_USERNAME/RP-Launcher`
- [ ] Check that latest commit appears
- [ ] Go to "Releases" or "Tags"
- [ ] Verify v1.0.0 tag is visible

---

## 📝 Create GitHub Release

### Step 1: Navigate to Releases

- Go to your repository on GitHub
- Click "Releases" (right sidebar)
- Click "Draft a new release"

### Step 2: Fill in Release Information

**Tag:** v1.0.0

**Release Title:** RP Launcher v1.0.0 - Initial Release

**Description:** (Use this template)

```markdown
# RP Launcher v1.0.0 🎉

**Initial public release** of RP Launcher with complete automation and setup system.

---

## ✨ Highlights

- **Complete RP Setup System** - Create new roleplays in 5 minutes with one command
- **6 Thinking Modes** - Granular control over Claude's reasoning depth
- **In-App Bridge Restart (F10)** - Apply settings without restarting
- **Automatic Update Checker** - Stay up-to-date with new releases
- **OpenRouter Integration** - Use any OpenRouter model with easy configuration

---

## 🎯 Key Features

### RP Management
- Full TUI (Text User Interface) client for Claude
- Background automation agents (entity extraction, memory creation, arc tracking)
- Chapter, character, and entity management
- Session logging and state tracking

### Configuration
- OpenRouter API key configuration (F9 Settings)
- Model selection for any OpenRouter-supported model
- 6 thinking modes (disabled → ultrathink)
- API mode and SDK mode support

### Setup System
- **Quick Setup Script**: `python setup/quick_setup.py "My RP Name"`
- Complete documentation with 3 user paths (5min/30min/2min)
- Minimal template pack with comprehensive examples
- Character templates, story guidance, and pre-configured automation

### Automation
- Entity extraction (auto-creates character cards after N mentions)
- Story arc tracking (updates every N messages)
- Plot thread management
- Current state tracking

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
cd src && npm install
```

### 2. Configure API Key

Launch and press F9 for settings:
```bash
python launch_rp_tui.py
```

Add your OpenRouter API key (get one at https://openrouter.ai/keys)

### 3. Create Your First RP

```bash
python setup/quick_setup.py "My First RP"
python launch_rp_tui.py "My First RP"
```

Type your message, press Ctrl+Enter, and start your adventure!

---

## 📚 Documentation

- **Setup Guide**: `setup/README.md` - Complete setup documentation
- **First RP Guide**: `setup/guides/02_CREATING_YOUR_FIRST_RP.md` - Step-by-step walkthrough
- **Checklist**: `setup/CHECKLIST.md` - Verify your setup is complete
- **Update Checker**: `docs/guides/UPDATE_CHECKER.md` - Update system details
- **Thinking Modes**: `THINKING_MODES.md` - All 6 modes explained

---

## ⌨️ Key Shortcuts

- **F1** - Help overlay
- **F2** - Memory browser
- **F3** - Story arc tracker
- **F4** - Characters
- **F5** - Scene notes
- **F6** - Entities
- **F7** - Story genome
- **F8** - Status display
- **F9** - Settings
- **F10** - Restart bridge
- **Ctrl+Enter** - Send message
- **Ctrl+Q** - Quit

---

## 🔧 Configuration

All configuration is done through the TUI (F9 Settings) or `config.json`:

```json
{
  "openrouter_api_key": "sk-or-v1-...",
  "openrouter_model": "deepseek/deepseek-chat-v3.1",
  "thinking_mode": "megathink",
  "check_for_updates": true
}
```

---

## 📊 What's Included

- **27 new files** (~6,800 lines)
  - Version tracking system
  - Automatic update checker
  - Complete RP setup system
  - Minimal template pack with comprehensive templates
  - Documentation and guides
- **14 modified files** for extended thinking modes, bridge restart, API improvements
- **5 bug fixes** including orchestrator initialization, API key validation

See [CHANGELOG_2025-10-15.md](CHANGELOG_2025-10-15.md) for complete details.

---

## 🐛 Known Issues

- None currently - this is the initial release!
- Report issues at: https://github.com/YOUR_USERNAME/RP-Launcher/issues

---

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://claude.ai) - AI assistance
- [Claude Code](https://claude.com/claude-code) - Development environment
- [OpenRouter](https://openrouter.ai) - Model API access
- [Textual](https://textual.textualize.io/) - TUI framework

---

**Enjoy your roleplaying adventures!** 🎭✨
```

### Step 3: Attach Files (Optional)

You can optionally attach:
- `CHANGELOG_2025-10-15.md` as additional documentation
- `setup/README.md` as setup guide

### Step 4: Publish Release

- [ ] Set as "Latest release"
- [ ] Click "Publish release"

---

## ✅ Post-Release Verification

### Test Update Checker

- [ ] Wait 5 minutes for GitHub to process the release
- [ ] On a different machine (or delete `.update_check_cache`):
  ```bash
  python launch_rp_tui.py
  ```
- [ ] Verify update notification shows (if you're on a commit before v1.0.0)
- [ ] Or verify it says you're on the latest version

### Verify Release on GitHub

- [ ] Visit: `https://github.com/YOUR_USERNAME/RP-Launcher/releases/tag/v1.0.0`
- [ ] Verify release notes display correctly
- [ ] Verify tag shows v1.0.0
- [ ] Check that download links work (if applicable)

### Test Clean Installation

On a fresh clone of the repository:

```bash
git clone https://github.com/YOUR_USERNAME/RP-Launcher.git
cd RP-Launcher
git checkout v1.0.0
pip install -r requirements.txt
cd src && npm install
cd ..
python setup/quick_setup.py "Test RP"
python launch_rp_tui.py "Test RP"
```

Verify everything works as expected.

---

## 📣 Announcement (Optional)

If you want to announce the release:

- [ ] Update project README.md with badge: ![Version](https://img.shields.io/badge/version-1.0.0-blue)
- [ ] Share on social media / Discord / Reddit
- [ ] Update any project documentation sites
- [ ] Notify users who were testing pre-release versions

---

## 🎉 Release Complete!

Once all checkboxes are complete, v1.0.0 is officially released!

**What's Next:**
- Monitor for bug reports
- Gather user feedback
- Plan v1.1.0 features
- Continue development

---

**Release Manager:** (Your name)
**Release Date:** October 15, 2025
**Verified By:** _______________
