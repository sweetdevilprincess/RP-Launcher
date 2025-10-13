# Documentation Index

Complete documentation for the RP Claude Code system.

---

## 📚 User Guides

**Getting Started:**
- [Quick Start](guides/QUICK_START.md) - Complete setup walkthrough
- [System Overview](guides/SYSTEM_OVERVIEW.md) - How everything works together
- [Launcher Guide](guides/LAUNCHER_GUIDE.md) - Using the launcher
- [TUI Guide](guides/README_TUI.md) - Using the terminal interface

**Features & Configuration:**
- [Automation Guide](guides/AUTOMATION_GUIDE.md) - Entity tracking, time calculation, auto-generation
- [File Loading Tiers](guides/FILE_LOADING_TIERS.md) - Understanding TIER_1/2/3 system
- [Prompt Caching Guide](guides/PROMPT_CACHING_GUIDE.md) - Saving 70-90% on API costs
- [Proxy Mode Guide](guides/PROXY_MODE_GUIDE.md) - Custom prompt injection

---

## 📖 Reference Documentation

**Structure & Organization:**
- [RP Folder Structure](reference/RP_FOLDER_STRUCTURE.md) - Complete guide to organizing your RP files

**SDK Documentation:**
- [SDK Quick Start](reference/SDK/QUICKSTART_SDK.md) - 5-minute SDK setup
- [SDK Reference](reference/SDK/README_SDK.md) - Full SDK documentation
- [SDK Summary](reference/SDK/SDK_SUMMARY.md) - Architecture overview

---

## 📦 Archive

Old documentation and planning documents (for reference):
- Integration status reports
- Old planning docs
- Completed feature summaries

See [archive/](archive/) folder.

---

## 🔍 Quick Reference

### Common Tasks

**Set up a new RP:**
1. Copy `Example RP/` folder
2. Rename to your RP name
3. Fill in templates (see [RP Folder Structure](reference/RP_FOLDER_STRUCTURE.md))

**Configure automation:**
- Edit `{your RP}/state/automation_config.json`
- See [Automation Guide](guides/AUTOMATION_GUIDE.md) for options

**Use SDK mode (faster, cached):**
- Install Node.js + dependencies: `cd src && npm install`
- See [SDK Quick Start](reference/SDK/QUICKSTART_SDK.md)

**Switch between modes:**
- Edit `config/config.json`
- `"use_api_mode": false` = SDK mode (default, faster)
- `"use_api_mode": true` = API mode (simpler)

---

## 💡 Tips

- Start with the [Quick Start Guide](guides/QUICK_START.md)
- Check [System Overview](guides/SYSTEM_OVERVIEW.md) to understand the architecture
- Use [RP Folder Structure](reference/RP_FOLDER_STRUCTURE.md) as your reference
- Enable SDK mode for 10-50x performance boost

---

**Have questions?** Check the guides above or see the main [README](../README.md).
