# Extended Thinking Configuration

Extended thinking allows Claude to spend more time reasoning before responding, leading to better context retention and fewer corrections. However, it increases response time.

## Thinking Modes

Configure thinking modes in your `config/config.json` or per-RP `state/config.json`:

### Preset Modes

| Mode | Token Budget | Use Case | Speed Impact |
|------|--------------|----------|--------------|
| **disabled** | 0 | No thinking - fastest responses | Baseline (fastest) |
| **think** | ~5,000 | Quick planning, simple refactoring | +5-10 seconds |
| **think hard** | ~10,000 | Feature design, debugging | +10-20 seconds |
| **megathink** | 10,000 | Standard reasoning (default, same as think hard) | +10-20 seconds |
| **think harder** | ~25,000 | Architecture decisions, complex bugs | +30-60 seconds |
| **ultrathink** | 31,999 | System design, major refactoring | +1-3 minutes |

### Configuration Examples

#### Option 1: Use Preset Mode (Recommended)

```json
{
  "thinking_mode": "megathink"
}
```

#### Option 2: Custom Token Budget

```json
{
  "thinking_mode": "megathink",
  "thinking_budget": 15000
}
```

Note: `thinking_budget` overrides `thinking_mode` if both are set.

#### Option 3: Disable Thinking (Fastest)

```json
{
  "thinking_mode": "disabled"
}
```

## Performance vs Quality Trade-off

### Disabled Thinking
- ⚡ Fastest responses (15-30 seconds)
- ⚠️ May require more corrections
- ⚠️ Less context retention across long conversations
- ✅ Good for simple back-and-forth dialogue

### Think Mode (~5k tokens)
- ⚡ Fast responses (20-40 seconds)
- ✅ Quick planning and simple refactoring
- ✅ Better than disabled for multi-step tasks
- ✅ Good for straightforward RP scenarios

### Think Hard Mode (~10k tokens)
- ⏱️ Moderate speed (25-50 seconds)
- ✅ Feature design and debugging
- ✅ Good reasoning for most tasks
- ✅ Recommended for standard RP use cases

### Megathink Mode (10k tokens) - DEFAULT
- ⏱️ Moderate speed (25-50 seconds)
- ✅ Balanced reasoning and speed (same as Think Hard)
- ✅ Good context retention
- ✅ Recommended for most RP use cases

### Think Harder Mode (~25k tokens)
- 🐌 Slower responses (45-90 seconds)
- ✅ Architecture decisions and complex bugs
- ✅ Strong reasoning for intricate plots
- ✅ Use for complex story arcs, major plot points

### Ultrathink Mode (32k tokens)
- 🐌 Slowest responses (60-180 seconds)
- ✅ Maximum reasoning capability
- ✅ System design and major refactoring
- ✅ Excellent context retention
- ✅ Use for major story arcs, pivotal decisions, complex multi-character scenes

## Configuration Locations

### Global Config (All RPs)
`C:\Users\green\Desktop\RP Claude Code\config\config.json`

```json
{
  "thinking_mode": "megathink",
  "use_api_mode": false
}
```

### Per-RP Config (Overrides Global)
`C:\Users\green\Desktop\RP Claude Code\{RP_NAME}\state\config.json`

```json
{
  "thinking_mode": "ultrathink"
}
```

## Recommendations

**For most users**: Use default `"megathink"` or `"think hard"` (10k tokens)
- Good balance of speed and quality
- ~25-50 second responses
- Solid context retention

**For speed**: Use `"think"` (5k tokens) or `"disabled"` (0 tokens)
- 15-40 second responses
- Accept slightly more corrections
- Good for simple conversations

**For complex scenarios**: Use `"think harder"` (25k tokens)
- 45-90 second responses
- Strong reasoning for intricate plots
- Use during complex multi-threaded storylines

**For maximum quality**: Use `"ultrathink"` (32k tokens)
- 60-180 second responses
- Best reasoning and context
- Use during pivotal story moments and major decisions

**Dynamic approach**: Switch modes per RP or per scene
- Simple dialogue/action: `"think"` or `"disabled"`
- Standard RP: `"megathink"` or `"think hard"`
- Complex plots: `"think harder"`
- Major plot points: `"ultrathink"`

## Testing Your Configuration

After changing `thinking_mode` in your config:

1. Stop tui_bridge.py (Ctrl+C)
2. Restart: `python src/tui_bridge.py "Your RP Name"`
3. Look for startup message: `🧠 Thinking mode: megathink`
4. Send a test message and observe response time
5. Check automation log for performance breakdown

## Performance Profiling

The system now includes performance profiling. After each response you'll see:

```
⚡ Automation Performance:
────────────────────────────────────────────────────────────
  tier1_loading                      :    15.2ms ( 42.1%)
  tier2_loading                      :    10.7ms ( 26.7%)
  entity_tracking                    :     5.3ms ( 14.2%)
  ...
────────────────────────────────────────────────────────────
  TOTAL                              :    36.4ms
```

This shows your local automation is fast (~40ms). The 15-45 second response time is almost entirely Claude's processing with extended thinking.

## Combining with Other Features

### With Prompt Caching (Recommended)
```json
{
  "thinking_mode": "megathink",
  "use_api_mode": false
}
```

Caching (94-99% hit rate) + megathink = optimal balance

### Fastest Possible Setup
```json
{
  "thinking_mode": "disabled",
  "use_api_mode": false
}
```

No thinking + caching = 15-30 second responses

### Maximum Quality Setup
```json
{
  "thinking_mode": "ultrathink",
  "use_api_mode": false
}
```

Max thinking + caching = 23-45 seconds, best quality
