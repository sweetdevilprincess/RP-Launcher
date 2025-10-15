# Wiki Quick Reference

Quick lookup for wiki structure and page locations.

---

## 📂 10 Main Sections

| # | Section | Pages | Purpose |
|---|---------|-------|---------|
| 1 | 🚀 **Getting Started** | 5 | Installation and first RP |
| 2 | 📖 **User Guides** | 10 | Using features |
| 3 | 🔧 **Configuration** | 4 | Settings and setup |
| 4 | 🎯 **Features** | 6 | Deep dives |
| 5 | 📝 **Templates** | 3 | RP content templates |
| 6 | 📚 **Technical Reference** | 7 | Developer docs |
| 7 | 🗺️ **Roadmap** | 8 | Future features |
| 8 | 🔧 **Development** | 4 | For contributors |
| 9 | ❓ **FAQ & Troubleshooting** | 3 | Help |
| 10 | 📊 **Examples** | 3 | Walkthroughs |

**Total**: ~53 pages

---

## 🎯 Minimal Viable Wiki (10 Pages)

Start with these to get your wiki functional:

1. **Home.md** - Welcome page with navigation
2. **Getting-Started.md** - Installation basics
3. **Launcher-Guide.md** - Using the TUI
4. **Thinking-Modes.md** - 6 thinking modes explained
5. **Settings-Screen.md** - F9 settings
6. **Roadmap.md** - Future plans
7. **FAQ.md** - Common questions
8. **Troubleshooting.md** - Common issues
9. **_Sidebar.md** - Navigation sidebar
10. **_Footer.md** - Page footer

---

## 📋 Page Naming Convention

GitHub wiki uses dashes in URLs:

| Display Name | File Name | URL |
|--------------|-----------|-----|
| Getting Started | `Getting-Started.md` | `/wiki/Getting-Started` |
| User Guides | `User-Guides.md` | `/wiki/User-Guides` |
| Agent Cache | `Agent-Cache.md` | `/wiki/Agent-Cache` |
| RP Folder Structure | `RP-Folder-Structure.md` | `/wiki/RP-Folder-Structure` |

**Rule**: Replace spaces with dashes, keep original capitalization.

---

## 🔗 Quick Link Reference

### Common Internal Links

```markdown
[Getting Started](Getting-Started)
[User Guides](User-Guides)
[Launcher Guide](Launcher-Guide)
[Thinking Modes](Thinking-Modes)
[Settings Screen](Settings-Screen)
[Roadmap](Roadmap)
[FAQ](FAQ)
```

### Links to Repo Files

```markdown
[THINKING_MODES.md](../blob/main/THINKING_MODES.md)
[launch_rp_tui.py](../blob/main/launch_rp_tui.py)
[Example RP](../tree/main/Example%20RP)
```

### External Links

```markdown
[Claude Code](https://claude.com/claude-code)
[OpenRouter](https://openrouter.ai/)
[Anthropic Console](https://console.anthropic.com/)
```

---

## 📝 Section Templates

### Landing Page Template

```markdown
# [Section Name]

[Brief description of this section]

---

## Pages in This Section

- **[Page 1](Link)** - Description
- **[Page 2](Link)** - Description
- **[Page 3](Link)** - Description

---

## Quick Links

- [Related Section 1](Link)
- [Related Section 2](Link)

---

**See Also**: [FAQ](FAQ) | [Troubleshooting](Troubleshooting)
```

### Content Page Template

```markdown
# [Page Title]

**Section**: [Getting Started/User Guides/etc.]
**Last Updated**: [Date]

---

## Overview

[What this page covers]

---

## [Section 1]

[Content]

### [Subsection 1.1]

[Content]

---

## [Section 2]

[Content]

---

## See Also

- [Related Page 1](Link)
- [Related Page 2](Link)

---

**Questions?** See [FAQ](FAQ) or [open an issue](https://github.com/[user]/[repo]/issues)
```

---

## 🎨 Common Markdown Patterns

### Info Boxes

```markdown
> ℹ️ **Note**: This is an informational note

> ⚠️ **Warning**: This is important

> ✅ **Tip**: This is a helpful tip

> 🚫 **Don't**: This is what not to do
```

### Code Blocks

```markdown
\```python
def example():
    return "syntax highlighting"
\```

\```bash
pip install -r requirements.txt
\```

\```json
{
  "key": "value"
}
\```
```

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

### Task Lists

```markdown
- [x] Completed task
- [ ] Incomplete task
```

### Collapsible Sections

```markdown
<details>
<summary>Click to expand</summary>

Hidden content here

</details>
```

---

## 📊 Content Sources

### Direct Copies (Minimal Editing)

These can be copied almost as-is:

- `THINKING_MODES.md` → `Thinking-Modes.md`
- `docs/planned_features/ROADMAP.md` → `Roadmap.md`
- `docs/planned_features/WRITER_AGENT.md` → `Writer-Agent.md`
- `docs/guides/LAUNCHER_GUIDE.md` → `Launcher-Guide.md`
- `docs/guides/AUTOMATION_GUIDE.md` → `Automation-Guide.md`

### Needs Adaptation

These need wiki-specific formatting:

- `docs/guides/QUICK_START.md` → Needs navigation links
- `setup/README.md` → Split into multiple pages
- Templates → Combine into fewer pages

### Create New

These need to be written fresh:

- `Home.md` - Wiki welcome page
- `Getting-Started.md` - Installation overview
- `FAQ.md` - Common questions
- `Troubleshooting.md` - Common issues

---

## 🔄 Update Workflow

### When Adding Features

1. Code change
2. Update `.md` file in repo (if exists)
3. Update corresponding wiki page
4. Update links in other pages
5. Update changelog

### When Fixing Bugs

1. Code fix
2. Update `Known-Issues.md` wiki page (remove issue)
3. Update `Troubleshooting.md` if relevant
4. Update FAQ if it was common

### Monthly Maintenance

- [ ] Review FAQ for new common questions
- [ ] Update Roadmap with completed features
- [ ] Check all links still work
- [ ] Update version numbers
- [ ] Review analytics for popular pages

---

## 🎯 Priority Matrix

### High Priority (Do First)
- Home page (everyone sees this)
- Getting Started (most important for new users)
- Launcher Guide (core feature)
- Thinking Modes (commonly asked about)
- Settings Screen (core feature)

### Medium Priority (Do Next)
- Automation Guide
- Prompt Caching
- Agent System
- Roadmap
- FAQ

### Low Priority (Nice to Have)
- Deep technical docs
- Advanced features
- Development guides
- Examples

---

## 📈 Analytics Tracking

Add to bottom of important pages:

```markdown
---

**Page Views**: [Track via GitHub insights]
**Last Updated**: October 2025
**Feedback**: [GitHub Issues](https://github.com/[user]/[repo]/issues)
```

---

## ✅ Launch Checklist

Before announcing wiki:

### Content
- [ ] Home page complete with navigation
- [ ] All section landing pages exist
- [ ] Minimum 10 core pages complete
- [ ] No lorem ipsum or TODOs

### Navigation
- [ ] Sidebar works on all pages
- [ ] Footer appears on all pages
- [ ] All internal links work
- [ ] No broken external links

### Quality
- [ ] Code blocks have syntax highlighting
- [ ] Tables display correctly
- [ ] Images load properly
- [ ] Mobile view looks good

### SEO
- [ ] Page titles are descriptive
- [ ] First paragraph explains page purpose
- [ ] Headers use proper hierarchy (H2, H3, H4)
- [ ] Keywords are in headings

### Maintenance
- [ ] Version numbers are current
- [ ] Contact info is correct
- [ ] Links to repo are correct
- [ ] License info is clear

---

## 🚀 Quick Start Commands

```bash
# Clone wiki
git clone https://github.com/[USERNAME]/[REPO].wiki.git
cd [REPO].wiki

# Create essential pages
touch Home.md Getting-Started.md _Sidebar.md _Footer.md

# Edit and commit
git add .
git commit -m "Initialize wiki structure"
git push

# Return to main repo
cd ..
```

---

## 📚 Resources

| Resource | URL |
|----------|-----|
| GitHub Wiki Docs | https://docs.github.com/en/communities/documenting-your-project-with-wikis |
| Markdown Cheatsheet | https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet |
| Emoji Cheatsheet | https://github.com/ikatyang/emoji-cheat-sheet |
| GFM Spec | https://github.github.com/gfm/ |

---

**Ready to start?** See [WIKI_SETUP_GUIDE.md](WIKI_SETUP_GUIDE.md) for detailed instructions!
