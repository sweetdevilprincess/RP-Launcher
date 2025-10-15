# GitHub Wiki Setup Guide

This guide shows you how to set up your GitHub wiki using the structure defined in `WIKI_STRUCTURE.md`.

---

## 🚀 Quick Setup

### Step 1: Enable Wiki

1. Go to your GitHub repository
2. Click **Settings**
3. Scroll to **Features** section
4. Check ✅ **Wikis**
5. Click **Save changes**

### Step 2: Initialize Wiki

1. Click the **Wiki** tab at the top of your repo
2. Click **Create the first page**
3. This will create `Home.md`

### Step 3: Clone Wiki Locally (Recommended)

The GitHub wiki is actually a separate git repository. Clone it to work locally:

```bash
# Clone the wiki repository
git clone https://github.com/[USERNAME]/[REPO].wiki.git

cd [REPO].wiki
```

### Step 4: Create Pages

You can create wiki pages in two ways:

**Option A: Through GitHub UI**
1. Click **New Page** button
2. Enter page title (e.g., "Getting Started")
3. Write content in markdown
4. Click **Save Page**

**Option B: Locally (Faster for bulk pages)**
1. Create `.md` files in the wiki repo
2. Name them with dashes: `Getting-Started.md`, `User-Guides.md`
3. Commit and push:
```bash
git add .
git commit -m "Add wiki pages"
git push
```

---

## 📝 Creating Your First Pages

### Priority 1: Essential Pages

Create these first to get your wiki functional:

#### 1. Home.md

```markdown
# Welcome to RP Claude Code Wiki

An advanced roleplay launcher for Claude Code with intelligent automation, prompt caching, and background analysis.

## 🎯 Quick Links

- **New Users**: Start with [Getting Started](Getting-Started)
- **Using the Launcher**: See [Launcher Guide](Launcher-Guide)
- **Thinking Modes**: Learn about [Thinking Modes](Thinking-Modes)
- **Configuration**: Check [Settings Screen](Settings-Screen)
- **Roadmap**: See [Roadmap](Roadmap)

## ✨ Key Features

- **Quick Setup**: Create complete RPs in one command with templates
- **6 Thinking Modes**: From disabled to ultrathink (5k-32k tokens)
- **Background Agents**: Automatic analysis while you type
- **Prompt Caching**: 54-61% token reduction
- **Bridge Restart**: F10 to apply settings without closing
- **OpenRouter Support**: Use any OpenRouter model
- **Auto Updates**: GitHub update checking

## 📖 Documentation Sections

### [Getting Started](Getting-Started)
First-time setup, installation, and your first RP.

### [User Guides](User-Guides)
How to use the launcher, thinking modes, automation, and more.

### [Configuration](Configuration)
Settings screen, API keys, and system configuration.

### [Features](Features)
Deep dives into agent system, caching, and advanced features.

### [Templates](Templates)
Entity templates, story templates, and examples.

### [Technical Reference](Technical-Reference)
For developers: folder structure, agent development, SDK integration.

### [Roadmap](Roadmap)
Future features, planned improvements, and development status.

## ❓ Need Help?

- [FAQ](FAQ)
- [Troubleshooting](Troubleshooting)
- [GitHub Issues](https://github.com/[USERNAME]/[REPO]/issues)

---

**Version**: 1.0.0 | **Last Updated**: October 2025
```

#### 2. Getting-Started.md

```markdown
# Getting Started

Welcome! This guide will help you install and set up RP Claude Code.

---

## Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** installed
- **Git** installed
- **Claude Code** extension (if using VS Code)
- **API Key**: Anthropic or OpenRouter

---

## Quick Installation

### 1. Clone Repository

```bash
git clone https://github.com/[USERNAME]/[REPO].git
cd [REPO]
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node dependencies (for SDK bridge)
cd src
npm install
cd ..
```

### 3. Create Your First RP

Use the quick setup script to create a complete RP in one command:

```bash
python setup/quick_setup.py "My RP Name"
```

This creates a complete RP with templates, character sheets, and all required files.

**Alternative**: Run `python launch_rp_tui.py` and select **Create New RP** for manual setup.

### 4. Configure API Keys

Press **F9** in the launcher to configure:
- Anthropic API key (for Claude direct)
- OpenRouter API key (for DeepSeek and other models)

---

## Next Steps

- [Creating Your First RP](Creating-Your-First-RP) - Detailed RP creation guide
- [Launcher Guide](Launcher-Guide) - Using the TUI interface
- [Thinking Modes](Thinking-Modes) - Choosing the right thinking mode
- [Setup Checklist](Setup-Checklist) - Verify your installation

---

## Troubleshooting

**Common Issues:**

### "No module named..."
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (should be 3.10+)

### "npm: command not found"
- Install Node.js from nodejs.org
- Verify: `node --version`

### "API key invalid"
- Anthropic keys start with `sk-ant-`
- OpenRouter keys start with `sk-or-v1-`
- Check for extra spaces in settings

---

**See Also:**
- [Installation](Installation) - Detailed installation guide
- [FAQ](FAQ) - Frequently asked questions
- [Troubleshooting](Troubleshooting) - More solutions
```

#### 3. _Sidebar.md

GitHub wikis support a `_Sidebar.md` file for navigation:

```markdown
## Navigation

**🚀 [Getting Started](Getting-Started)**
- [Installation](Installation)
- [Quick Start](Quick-Start)
- [First RP](Creating-Your-First-RP)

**📖 [User Guides](User-Guides)**
- [System Overview](System-Overview)
- [Launcher Guide](Launcher-Guide)
- [Thinking Modes](Thinking-Modes)
- [Automation](Automation-Guide)

**🔧 [Configuration](Configuration)**
- [Settings (F9)](Settings-Screen)
- [API Keys](API-Keys)
- [Automation Config](Automation-Config)

**🎯 [Features](Features)**
- [Background Agents](Background-Agents)
- [Immediate Agents](Immediate-Agents)
- [Bridge Restart (F10)](Bridge-Restart)

**📝 [Templates](Templates)**

**📚 [Technical](Technical-Reference)**

**🗺️ [Roadmap](Roadmap)**

**❓ [Help](FAQ)**
- [FAQ](FAQ)
- [Troubleshooting](Troubleshooting)
```

#### 4. _Footer.md

Add a consistent footer to all pages:

```markdown
---
**RP Claude Code** | [Home](Home) | [Getting Started](Getting-Started) | [Roadmap](Roadmap) | [GitHub](https://github.com/[USERNAME]/[REPO])
```

---

## 🔗 Linking Between Pages

### Internal Links

Link to other wiki pages using the page name:

```markdown
See the [Launcher Guide](Launcher-Guide) for details.
```

### Links to Repository Files

Link to files in your repo:

```markdown
See [THINKING_MODES.md](https://github.com/[USERNAME]/[REPO]/blob/main/THINKING_MODES.md)
```

### Anchors/Headings

Link to specific sections:

```markdown
See [Installation > Prerequisites](#prerequisites)
```

---

## 📋 Wiki Migration Script

To help migrate your existing docs to wiki format, here's a helper script:

```python
# scripts/wiki_migrate.py
"""
Migrate documentation files to GitHub wiki format
"""

import shutil
from pathlib import Path

# Map source files to wiki page names
FILE_MAPPING = {
    'THINKING_MODES.md': 'Thinking-Modes.md',
    'docs/guides/LAUNCHER_GUIDE.md': 'Launcher-Guide.md',
    'docs/guides/AUTOMATION_GUIDE.md': 'Automation-Guide.md',
    'docs/guides/SYSTEM_OVERVIEW.md': 'System-Overview.md',
    'docs/planned_features/ROADMAP.md': 'Roadmap.md',
    # Add more mappings...
}

def migrate_files(repo_path: Path, wiki_path: Path):
    """Copy files to wiki repo with wiki naming convention"""

    for source, dest in FILE_MAPPING.items():
        source_file = repo_path / source
        dest_file = wiki_path / dest

        if source_file.exists():
            print(f"Copying {source} -> {dest}")
            shutil.copy2(source_file, dest_file)
        else:
            print(f"Warning: {source} not found")

if __name__ == '__main__':
    repo = Path('.')
    wiki = Path('../RP-Claude-Code.wiki')  # Adjust path

    if not wiki.exists():
        print("Wiki repo not found. Clone it first:")
        print("git clone https://github.com/[USERNAME]/[REPO].wiki.git")
    else:
        migrate_files(repo, wiki)
        print("\nDone! Don't forget to:")
        print("1. cd ../RP-Claude-Code.wiki")
        print("2. git add .")
        print("3. git commit -m 'Add wiki pages'")
        print("4. git push")
```

Run it:
```bash
python scripts/wiki_migrate.py
```

---

## 🎨 Styling Tips

### Use Emojis for Visual Navigation

```markdown
## 🚀 Getting Started
## 📖 User Guides
## 🔧 Configuration
## 🎯 Features
```

### Code Blocks with Language

```markdown
```python
def example():
    pass
\```

```bash
npm install
\```
```

### Callout Boxes

Use blockquotes for important notes:

```markdown
> ⚠️ **Important**: API keys must start with `sk-ant-` or `sk-or-v1-`

> ✅ **Tip**: Press F10 to restart the bridge without closing the launcher
```

### Tables for Comparisons

```markdown
| Mode | Tokens | Speed |
|------|--------|-------|
| think | 5k | Fast |
| megathink | 10k | Medium |
| ultrathink | 32k | Slow |
```

---

## 📊 Best Practices

### ✅ Do

- **Keep pages focused** - One topic per page
- **Use clear headings** - H2 for sections, H3 for subsections
- **Link liberally** - Connect related pages
- **Update regularly** - Keep in sync with code
- **Include examples** - Show, don't just tell
- **Add "See Also"** - Related pages at bottom
- **Version stamp** - Note when features were added

### ❌ Don't

- **Don't duplicate content** - Link to existing docs instead
- **Don't use absolute paths** - Use relative wiki links
- **Don't forget images** - Add screenshots for UI features
- **Don't skip code blocks** - Always use proper formatting
- **Don't orphan pages** - Every page should be reachable

---

## 🔄 Workflow

### Regular Updates

1. **After feature addition**: Update relevant wiki pages
2. **After bug fix**: Update Known-Issues page
3. **After release**: Update Changelog page
4. **Monthly**: Review FAQ for common questions

### Pull Request Process

When adding features:
1. Update code
2. Update relevant `.md` files in repo
3. Update wiki pages
4. Link PR to wiki changes in commit message

---

## 📸 Adding Images

### Upload to Wiki

1. Go to any wiki page in edit mode
2. Drag and drop image
3. Copy the generated markdown: `![image](url)`
4. Use in any wiki page

### Or Store in Repo

```markdown
![Screenshot](https://raw.githubusercontent.com/[USERNAME]/[REPO]/main/docs/images/screenshot.png)
```

---

## 🎯 Priority Order

### Week 1: Core Structure
- [ ] Home.md
- [ ] Getting-Started.md
- [ ] _Sidebar.md
- [ ] _Footer.md

### Week 2: User Documentation
- [ ] Launcher-Guide.md
- [ ] Thinking-Modes.md
- [ ] Settings-Screen.md
- [ ] FAQ.md

### Week 3: Features & Technical
- [ ] Background-Agents.md
- [ ] Agent-Cache.md
- [ ] RP-Folder-Structure.md
- [ ] Roadmap.md

### Week 4: Polish
- [ ] Examples.md
- [ ] Troubleshooting.md
- [ ] Best-Practices.md
- [ ] Add screenshots

---

## ✅ Checklist

Before launching your wiki:

- [ ] Home page welcomes users
- [ ] Sidebar navigation works
- [ ] All links are tested
- [ ] Code blocks have syntax highlighting
- [ ] Images display correctly
- [ ] Mobile view looks good
- [ ] Search finds relevant pages
- [ ] No broken links
- [ ] Version numbers are current
- [ ] Contact/support info is clear

---

## 📚 Resources

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

**Next Steps**: Start with Home.md and Getting-Started.md, then expand based on user feedback!
