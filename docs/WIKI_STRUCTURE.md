# GitHub Wiki Structure

This document outlines the recommended structure for organizing the RP Claude Code wiki.

---

## 🏠 Home Page

**File**: `Home.md`
**Content**: Welcome message, elevator pitch, quick navigation

```markdown
# Welcome to RP Claude Code Wiki

An advanced roleplay launcher for Claude Code with intelligent automation, prompt caching, and background analysis.

## Quick Links
- 🚀 [Getting Started](Getting-Started)
- 📖 [User Guides](User-Guides)
- 🔧 [Configuration](Configuration)
- 🎯 [Features](Features)
- 📚 [Technical Reference](Technical-Reference)
- 🗺️ [Roadmap](Roadmap)

## Key Features
- 6 thinking modes (disabled → think → think hard → megathink → think harder → ultrathink)
- Background agent system for analysis
- Prompt caching (54-61% token reduction)
- In-app bridge restart (F10)
- OpenRouter integration
- Automatic update checking
```

---

## 📂 Wiki Structure

### 1. 🚀 Getting Started

**Purpose**: Help new users get up and running

#### Pages:
- **`Getting-Started.md`** (Home for this section)
  - Overview of setup process
  - System requirements
  - Installation steps
  - Links to detailed guides

- **`Installation.md`**
  - Source: `setup/README.md`
  - Prerequisites
  - Step-by-step installation
  - Troubleshooting common issues

- **`Quick-Start.md`**
  - Source: `docs/guides/QUICK_START.md`
  - 5-minute quickstart
  - Create your first RP
  - First message walkthrough

- **`Creating-Your-First-RP.md`**
  - Source: `setup/guides/02_CREATING_YOUR_FIRST_RP.md`
  - Detailed RP creation guide
  - Using templates
  - Best practices

- **`Setup-Checklist.md`**
  - Source: `setup/CHECKLIST.md`
  - Post-installation checklist
  - Configuration verification
  - Testing steps

---

### 2. 📖 User Guides

**Purpose**: How to use specific features

#### Pages:
- **`User-Guides.md`** (Home for this section)
  - Overview of available guides
  - Beginner vs advanced paths

- **`System-Overview.md`**
  - Source: `docs/guides/SYSTEM_OVERVIEW.md`
  - How the system works
  - Architecture overview
  - Key concepts

- **`Launcher-Guide.md`**
  - Source: `docs/guides/LAUNCHER_GUIDE.md`
  - Using the TUI launcher
  - Keyboard shortcuts
  - F1-F10 overlays
  - Settings (F9)
  - Bridge restart (F10)

- **`Thinking-Modes.md`**
  - Source: `THINKING_MODES.md`
  - All 6 thinking modes explained
  - When to use each mode
  - Performance vs quality trade-offs
  - Configuration instructions

- **`Automation-Guide.md`**
  - Source: `docs/guides/AUTOMATION_GUIDE.md`
  - Background agent system
  - Immediate agents
  - Agent cache
  - How automation works

- **`Agent-System.md`**
  - Source: `docs/guides/AGENT_COORDINATION.md`
  - Agent coordination
  - Background vs immediate agents
  - Agent types and purposes
  - Performance metrics

- **`Prompt-Caching.md`**
  - Source: `docs/guides/PROMPT_CACHING_GUIDE.md`
  - How prompt caching works
  - TIER_1, TIER_2, TIER_3 files
  - Token savings
  - Best practices

- **`File-Loading-Tiers.md`**
  - Source: `docs/guides/FILE_LOADING_TIERS.md`
  - Three-tier loading system
  - What goes in each tier
  - Optimization strategies

- **`Proxy-Mode.md`**
  - Source: `docs/guides/PROXY_MODE_GUIDE.md`
  - What is proxy mode
  - When to use it
  - Setup instructions

- **`Update-Checker.md`**
  - Source: `docs/guides/UPDATE_CHECKER.md`
  - Automatic update checking
  - Configuration options
  - Manual checking
  - Troubleshooting

---

### 3. 🔧 Configuration

**Purpose**: Setting up and customizing the system

#### Pages:
- **`Configuration.md`** (Home for this section)
  - Overview of configuration options
  - Quick reference

- **`Settings-Screen.md`**
  - F9 settings overview
  - OpenRouter API configuration
  - Thinking mode selection
  - Model selection
  - API mode toggle
  - Proxy mode toggle

- **`API-Keys.md`**
  - Anthropic API key setup
  - OpenRouter API key setup
  - Key validation
  - Security best practices

- **`Automation-Config.md`**
  - Source: `config/templates/AUTOMATION_CONFIG_README.md`
  - automation_config.json explained
  - Enabling/disabling agents
  - Agent parameters
  - Performance tuning

- **`Guidelines.md`**
  - Overview of guideline files
  - Session instructions
  - Writing style guide
  - Time tracking
  - POV and writing checklist
  - NPC interaction rules

---

### 4. 🎯 Features

**Purpose**: Deep dives into major features

#### Pages:
- **`Features.md`** (Home for this section)
  - All features at a glance

- **`Background-Agents.md`**
  - ResponseAnalyzerAgent
  - MemoryCreationAgent
  - RelationshipAnalysisAgent
  - PlotThreadDetectionAgent
  - KnowledgeExtractionAgent
  - ContradictionDetectionAgent

- **`Immediate-Agents.md`**
  - QuickEntityAnalysisAgent
  - FactExtractionAgent
  - MemoryExtractionAgent
  - PlotThreadExtractionAgent

- **`Agent-Cache.md`**
  - Source: `docs/guides/AGENT_CACHE_FORMAT.md`, `docs/guides/AGENT_CACHE_JSON_FORMAT.md`
  - Cache structure
  - JSON format
  - How cache is used
  - Cache invalidation

- **`Bridge-Restart.md`**
  - F10 bridge restart feature
  - When to restart
  - What gets reloaded
  - Troubleshooting

- **`Performance-Metrics.md`**
  - Timing breakdowns
  - Analysis vs write time
  - Reading hook.log
  - Optimization recommendations

---

### 5. 📝 Templates

**Purpose**: Reference for creating RP content

#### Pages:
- **`Templates.md`** (Home for this section)
  - Overview of all templates
  - How to use templates

- **`RP-Overview-Template.md`**
  - Source: `config/templates/TEMPLATE_ROLEPLAY_OVERVIEW.md`
  - Structure and fields

- **`Entity-Templates.md`**
  - Character template
  - Location template
  - Item template
  - Event template
  - Personality Core format

- **`Story-Templates.md`**
  - Author's Notes
  - Story Genome
  - Scene Notes
  - User Memory

- **`Starter-Packs.md`**
  - Minimal starter pack
  - What's included
  - How to customize

---

### 6. 📚 Technical Reference

**Purpose**: Deep technical documentation for developers

#### Pages:
- **`Technical-Reference.md`** (Home for this section)
  - Overview of technical docs

- **`RP-Folder-Structure.md`**
  - Source: `docs/reference/RP_FOLDER_STRUCTURE.md`
  - Complete folder structure
  - File purposes
  - State management

- **`Agent-Development.md`**
  - Source: `src/automation/agents/AGENT_DEVELOPMENT_GUIDE.md`
  - Creating new agents
  - BaseAgent class
  - Template and examples

- **`Agent-Cache-Spec.md`**
  - Source: `docs/guides/AGENT_CACHE_SPEC.md`
  - Technical specification
  - Cache format details
  - Implementation notes

- **`SDK-Integration.md`**
  - Source: `docs/reference/SDK/SDK_SUMMARY.md`
  - Claude Code SDK integration
  - API vs SDK mode
  - Configuration

- **`Trigger-System.md`**
  - Source: `src/trigger_system/README.md`
  - How triggers work
  - Entity detection
  - Fallback system

- **`Concurrent-DeepSeek.md`**
  - Source: `docs/archive/CONCURRENT_DEEPSEEK.md`
  - Concurrent API calls
  - Background task queue
  - Performance considerations

- **`File-Write-Queue.md`**
  - FSWriteQueue system
  - Debouncing
  - Write optimization

---

### 7. 🗺️ Roadmap

**Purpose**: Future features and development plans

#### Pages:
- **`Roadmap.md`** (Home for this section)
  - Source: `docs/planned_features/ROADMAP.md`
  - Complete roadmap
  - Phase 0-4 overview
  - Implementation status

- **`Planned-Features.md`**
  - Quick overview of upcoming features
  - Priority levels
  - Dependencies

- **`Writer-Agent.md`**
  - Source: `docs/planned_features/WRITER_AGENT.md`
  - Performance testing phase
  - Decision criteria
  - Implementation plan

- **`Story-Continuity-Features.md`**
  - Source: `docs/planned_features/story_continuity.md`
  - Plot thread tracking
  - Contradiction detection
  - Knowledge base

- **`Search-and-Organization.md`**
  - Source: `docs/planned_features/search_and_organization.md`
  - Memory system
  - Relationship system
  - Search features

- **`Technical-Improvements.md`**
  - Source: `docs/planned_features/technical_improvements.md`
  - Architecture improvements
  - Performance optimizations

- **`Timeline-and-Pacing.md`**
  - Source: `docs/planned_features/timeline_and_pacing.md`
  - Time tracking features
  - Pacing analysis

- **`Version-Control.md`**
  - Source: `docs/planned_features/version_control.md`
  - Story checkpointing
  - Branching

---

### 8. 🔧 Development

**Purpose**: For contributors and developers

#### Pages:
- **`Development.md`** (Home for this section)
  - Contributing guide
  - Development setup
  - Coding standards

- **`Changelog.md`**
  - Source: `docs/changelogs/CHANGELOG_2025-10-15.md`
  - Version history
  - Recent changes
  - Migration guides

- **`Obsolescence-Analysis.md`**
  - Source: `docs/OBSOLESCENCE_ANALYSIS.md`
  - Legacy systems
  - Cleanup plan
  - Migration strategy

- **`Refactoring.md`**
  - Source: `docs/refactoring/REFACTORING_2025-10-14.md`
  - Recent refactors
  - Lessons learned

- **`Architecture-Decisions.md`**
  - Why certain choices were made
  - Trade-offs
  - Future considerations

---

### 9. ❓ FAQ & Troubleshooting

**Purpose**: Common questions and issues

#### Pages:
- **`FAQ.md`**
  - General questions
  - Feature questions
  - Configuration questions

- **`Troubleshooting.md`**
  - Common errors
  - Solutions
  - Debug steps
  - Performance issues

- **`Known-Issues.md`**
  - Current limitations
  - Workarounds
  - Planned fixes

---

### 10. 📊 Examples

**Purpose**: Real-world examples and tutorials

#### Pages:
- **`Examples.md`** (Home for this section)
  - Overview of examples

- **`Example-RP-Walkthrough.md`**
  - Tour of Example RP
  - How files are used
  - Entity examples
  - State management examples

- **`Best-Practices.md`**
  - RP organization tips
  - Entity card tips
  - Performance optimization
  - Workflow recommendations

---

## 📋 Page Mapping

### Files → Wiki Pages

| Source File | Wiki Page | Category |
|-------------|-----------|----------|
| `setup/README.md` | Installation | Getting Started |
| `docs/guides/QUICK_START.md` | Quick-Start | Getting Started |
| `setup/guides/02_CREATING_YOUR_FIRST_RP.md` | Creating-Your-First-RP | Getting Started |
| `setup/CHECKLIST.md` | Setup-Checklist | Getting Started |
| `docs/guides/SYSTEM_OVERVIEW.md` | System-Overview | User Guides |
| `docs/guides/LAUNCHER_GUIDE.md` | Launcher-Guide | User Guides |
| `THINKING_MODES.md` | Thinking-Modes | User Guides |
| `docs/guides/AUTOMATION_GUIDE.md` | Automation-Guide | User Guides |
| `docs/guides/AGENT_COORDINATION.md` | Agent-System | User Guides |
| `docs/guides/PROMPT_CACHING_GUIDE.md` | Prompt-Caching | User Guides |
| `docs/guides/FILE_LOADING_TIERS.md` | File-Loading-Tiers | User Guides |
| `docs/guides/PROXY_MODE_GUIDE.md` | Proxy-Mode | User Guides |
| `docs/guides/UPDATE_CHECKER.md` | Update-Checker | User Guides |
| `config/templates/AUTOMATION_CONFIG_README.md` | Automation-Config | Configuration |
| `docs/guides/AGENT_CACHE_FORMAT.md` | Agent-Cache | Features |
| `docs/reference/RP_FOLDER_STRUCTURE.md` | RP-Folder-Structure | Technical Reference |
| `src/automation/agents/AGENT_DEVELOPMENT_GUIDE.md` | Agent-Development | Technical Reference |
| `docs/guides/AGENT_CACHE_SPEC.md` | Agent-Cache-Spec | Technical Reference |
| `docs/reference/SDK/SDK_SUMMARY.md` | SDK-Integration | Technical Reference |
| `src/trigger_system/README.md` | Trigger-System | Technical Reference |
| `docs/archive/CONCURRENT_DEEPSEEK.md` | Concurrent-DeepSeek | Technical Reference |
| `docs/planned_features/ROADMAP.md` | Roadmap | Roadmap |
| `docs/planned_features/WRITER_AGENT.md` | Writer-Agent | Roadmap |
| `docs/planned_features/story_continuity.md` | Story-Continuity-Features | Roadmap |
| `docs/planned_features/search_and_organization.md` | Search-and-Organization | Roadmap |
| `docs/planned_features/technical_improvements.md` | Technical-Improvements | Roadmap |
| `docs/planned_features/timeline_and_pacing.md` | Timeline-and-Pacing | Roadmap |
| `docs/planned_features/version_control.md` | Version-Control | Roadmap |
| `docs/changelogs/CHANGELOG_2025-10-15.md` | Changelog | Development |
| `docs/OBSOLESCENCE_ANALYSIS.md` | Obsolescence-Analysis | Development |
| `docs/refactoring/REFACTORING_2025-10-14.md` | Refactoring | Development |
| Templates in `config/templates/` | Templates section | Templates |

---

## 🎨 Wiki Sidebar

Recommended sidebar structure for easy navigation:

```markdown
## Navigation

**🚀 Getting Started**
- [Installation](Installation)
- [Quick Start](Quick-Start)
- [First RP](Creating-Your-First-RP)
- [Checklist](Setup-Checklist)

**📖 User Guides**
- [System Overview](System-Overview)
- [Launcher Guide](Launcher-Guide)
- [Thinking Modes](Thinking-Modes)
- [Automation](Automation-Guide)
- [Prompt Caching](Prompt-Caching)
- [File Loading Tiers](File-Loading-Tiers)

**🔧 Configuration**
- [Settings Screen](Settings-Screen)
- [API Keys](API-Keys)
- [Automation Config](Automation-Config)

**🎯 Features**
- [Background Agents](Background-Agents)
- [Immediate Agents](Immediate-Agents)
- [Agent Cache](Agent-Cache)
- [Bridge Restart](Bridge-Restart)
- [Performance Metrics](Performance-Metrics)

**📝 Templates**
- [Overview](Templates)
- [Entity Templates](Entity-Templates)
- [Story Templates](Story-Templates)

**📚 Technical**
- [Folder Structure](RP-Folder-Structure)
- [Agent Development](Agent-Development)
- [SDK Integration](SDK-Integration)

**🗺️ Roadmap**
- [Full Roadmap](Roadmap)
- [Writer Agent](Writer-Agent)
- [Planned Features](Planned-Features)

**❓ Help**
- [FAQ](FAQ)
- [Troubleshooting](Troubleshooting)
- [Examples](Examples)
```

---

## 🚀 Implementation Steps

### Phase 1: Core Pages (Priority 1)
1. Create Home.md with welcome message
2. Create Getting-Started.md with installation/quickstart
3. Create User-Guides.md with launcher/thinking modes
4. Create Configuration.md with settings/API keys
5. Create Roadmap.md (link to existing ROADMAP.md)

### Phase 2: Feature Documentation (Priority 2)
1. Create Features.md with agent system
2. Create Templates.md with entity/story templates
3. Create Technical-Reference.md with folder structure
4. Create FAQ.md with common questions
5. Create Examples.md with walkthroughs

### Phase 3: Advanced Content (Priority 3)
1. Create Development.md with changelog/contributing
2. Expand Troubleshooting.md
3. Add detailed agent pages
4. Add best practices guide
5. Add performance tuning guide

---

## 📝 Wiki Page Template

Use this template for consistency:

```markdown
# [Page Title]

**Category**: [Getting Started/User Guides/etc.]
**Last Updated**: [Date]
**Related Pages**: [Links to related wiki pages]

---

## Overview

[Brief description of what this page covers]

---

## [Main Content Sections]

[Content here with clear headings, code blocks, examples]

---

## See Also

- [Related Page 1]
- [Related Page 2]
- [Related Page 3]

---

## Need Help?

- [FAQ](FAQ)
- [Troubleshooting](Troubleshooting)
- [GitHub Issues](https://github.com/[user]/[repo]/issues)
```

---

## 🔄 Maintenance

### Regular Updates
- Update Changelog.md after each release
- Update Roadmap.md as features complete
- Update Known-Issues.md as issues are found/fixed
- Review FAQ.md monthly for common questions

### Version Tracking
- Tag wiki pages with version requirements
- Note when features were added
- Mark deprecated features clearly

### User Feedback
- Monitor GitHub issues for documentation requests
- Add commonly asked questions to FAQ
- Improve pages based on user confusion

---

## 📊 Success Metrics

**Good documentation should:**
- ✅ Answer 80% of user questions without GitHub issues
- ✅ Let new users get started in <15 minutes
- ✅ Have clear navigation (≤3 clicks to any page)
- ✅ Stay up-to-date with latest features
- ✅ Include examples for complex features

---

**Next Steps**: Start with Phase 1 core pages, then expand based on user needs.
