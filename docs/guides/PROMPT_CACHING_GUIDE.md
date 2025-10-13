# Prompt Caching Guide

## Overview

The RP automation system now supports **two modes** for calling Claude:

1. **CLI Mode** (default) - Uses `claude` command-line tool
2. **API Mode** (new) - Uses Anthropic API directly with **prompt caching**

## Why API Mode with Prompt Caching?

### The Problem
Your TIER_1 files (AUTHOR'S_NOTES, STORY_GENOME, LOREBOOK, etc.) are loaded with **every single message**. Without caching, you pay full token cost every time.

### The Solution
Prompt caching allows you to cache TIER_1 files once, then pay only **10% of the cost** for subsequent reads (within 5 minutes).

### Cost Savings Example
Let's say your TIER_1 files are 10,000 tokens:

**Without caching (CLI mode):**
- 10 messages = 10,000 × 10 = **100,000 tokens**

**With caching (API mode):**
- First message: 10,000 × 1.25 = 12,500 tokens (write cache)
- Next 9 messages: 10,000 × 0.1 × 9 = 9,000 tokens (read cache)
- Total = **21,500 tokens** (78.5% savings!)

After just **2 messages**, caching pays for itself.

## How It Works

### CLI Mode (Current)
```
User Message
    ↓
Load TIER_1 + TIER_2 + TIER_3 → Enhanced Message
    ↓
Send EVERYTHING to `claude -c`
    ↓
Response
```
- Claude Code CLI may use internal caching (unknown)
- No control over what gets cached
- Simple to use, requires no API key

### API Mode (New)
```
User Message
    ↓
Load TIER_1 (cached) | Load TIER_2 + TIER_3 (dynamic)
    ↓                          ↓
System Prompt (CACHED)    User Message
    ↓                          ↓
        Send to Claude API
             ↓
         Response
```
- TIER_1 files cached in system prompt
- Cache lasts 5 minutes (refreshed on each use)
- Explicit control and monitoring
- Requires Anthropic API key

## Setup Instructions

### Step 1: Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### Step 2: Configure API Mode

You have **two options** for providing your API key:

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Add to system environment variables for persistence
```

**Option B: Config File**
Edit `Example RP/state/config.json`:
```json
{
  "use_api_mode": true,
  "anthropic_api_key": "sk-ant-your-key-here",
  "auto_entity_cards": true,
  "entity_mention_threshold": 2,
  "auto_story_arc": true,
  "arc_frequency": 50
}
```

### Step 3: Enable API Mode

Add or update in `Example RP/state/config.json`:
```json
{
  "use_api_mode": true
}
```

### Step 4: Restart the Bridge

When you launch the RP system, you'll see:

**API Mode:**
```
🌉 TUI Bridge started (API MODE with Prompt Caching)
💾 TIER_1 files will be cached for maximum efficiency!
```

**CLI Mode (fallback):**
```
🌉 TUI Bridge started (CLI MODE)
💡 To enable API mode with prompt caching, add to config.json:
   {"use_api_mode": true, "anthropic_api_key": "your-key"}
```

## Monitoring Cache Performance

In API mode, the bridge terminal will show cache statistics:

```
📊 Token Usage:
  Input: 3,245
  Output: 892
  💾 Cache Created: 12,458 tokens (1.25x cost)
```
*First message - TIER_1 files cached*

```
📊 Token Usage:
  Input: 2,134
  Output: 756
  ⚡ Cache Hit: 12,458 tokens (0.1x cost) - 85.4% of input cached!
```
*Subsequent messages - reading from cache*

## Cache Behavior

### Cache Lifetime
- **Default:** 5 minutes
- Cache is **refreshed** each time it's used
- If inactive for 5+ minutes, cache expires and must be recreated

### What Gets Cached
**TIER_1 files ONLY:**
- AUTHOR'S_NOTES.md
- STORY_GENOME.md
- LOREBOOK.md
- WORLD.md
- CHARSANDRELATIONS.md
- PROJECT.md

**NOT cached (dynamic content):**
- TIER_2 files (guidelines - every 4th response)
- TIER_3 files (triggered by keywords)
- User messages
- Conversation history

### Session Management

The `/new` command works in both modes:
- **CLI Mode:** Clears session flag (next message starts new `claude` conversation)
- **API Mode:** Clears session flag + conversation history (next message starts fresh)

## Comparing Modes

| Feature | CLI Mode | API Mode |
|---------|----------|----------|
| **Setup** | Zero config | Requires API key |
| **Cost** | Full token cost every message | 78-90% savings on TIER_1 |
| **Caching** | Unknown (internal) | Explicit control |
| **Monitoring** | `/cost` command | Real-time stats in terminal |
| **Speed** | Standard | Faster (cached reads) |
| **Conversation** | `-c` flag | Managed internally |

## Troubleshooting

### "API mode enabled but no API key found"
- Set `ANTHROPIC_API_KEY` environment variable, OR
- Add `anthropic_api_key` to config.json

### "Error initializing API mode"
- Check API key is valid (starts with `sk-ant-`)
- Ensure anthropic SDK is installed: `pip install anthropic`
- Check internet connection
- View full error in bridge terminal

### API mode not using cache
- Cache requires minimum 1024-2048 tokens (TIER_1 should exceed this)
- First message creates cache (1.25x cost)
- Subsequent messages read cache (0.1x cost)
- Cache expires after 5 minutes of inactivity

### Switching back to CLI mode
Simply set in config.json:
```json
{
  "use_api_mode": false
}
```

## Recommendations

### When to Use API Mode
- **Long RP sessions** (multiple messages)
- **Large TIER_1 files** (more tokens = more savings)
- **Want explicit cost monitoring**
- **Running on Claude Max** (API usage counts toward Max benefits)

### When to Use CLI Mode
- **Quick testing** (1-2 messages)
- **Don't want to manage API keys**
- **Prefer simplicity**

## Cost Comparison

Based on **Claude Sonnet 4.5** pricing:

### 10-Message Session with 10,000 token TIER_1

**CLI Mode:**
- Input: 10,000 × 10 = 100,000 tokens
- Cost: ~$0.30

**API Mode:**
- Cache write: 10,000 × 1.25 = 12,500 tokens
- Cache reads: 10,000 × 0.1 × 9 = 9,000 tokens
- Total: 21,500 tokens
- Cost: ~$0.06
- **Savings: $0.24 (80%)**

The more messages you send, the greater the savings!

## Future Enhancements

Potential improvements:
- **Extended cache** (1 hour instead of 5 minutes) for longer sessions
- **Cache multiple breakpoints** (TIER_1, TIER_2, conversation history)
- **Automatic mode switching** based on session length
- **Cost tracking** across sessions

---

**Bottom Line:** If you're sending more than 2 messages per RP session, API mode with caching will save you significant tokens and costs.
