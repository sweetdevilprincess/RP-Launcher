# Extended Thinking Configuration

Extended thinking allows Claude to spend more time reasoning before responding, leading to better context retention and fewer corrections. However, it increases response time.

## Thinking Modes

Configure thinking modes in your `config/config.json` or per-RP `state/config.json`:

### Preset Modes

| Mode | Token Budget | Use Case | Speed Impact |
|------|--------------|----------|--------------|
| **disabled** | 0 | No thinking - fastest responses | Baseline (fastest) |
| **think** | 4,000 | Quick reasoning for simple tasks | +1-2 seconds |
| **megathink** | 10,000 | Standard reasoning (default) | +3-5 seconds |
| **ultrathink** | 31,999 | Maximum reasoning for complex scenarios | +8-15 seconds |

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

### Think Mode (4k tokens)
- ⚡ Fast responses (16-32 seconds)
- ✅ Basic reasoning for simple decisions
- ✅ Better than disabled for multi-step tasks
- ✅ Good for straightforward RP scenarios

### Megathink Mode (10k tokens) - DEFAULT
- ⏱️ Moderate speed (18-35 seconds)
- ✅ Balanced reasoning and speed
- ✅ Good context retention
- ✅ Recommended for most RP use cases

### Ultrathink Mode (32k tokens)
- 🐌 Slower responses (23-45 seconds)
- ✅ Maximum reasoning capability
- ✅ Best for complex plot points
- ✅ Excellent context retention
- ✅ Use for story arcs, major decisions, complex scenes

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

**For most users**: Use default `"megathink"` (10k tokens)
- Good balance of speed and quality
- ~18-35 second responses
- Solid context retention

**For speed**: Use `"think"` (4k tokens) or `"disabled"` (0 tokens)
- 15-32 second responses
- Accept slightly more corrections
- Good for simple conversations

**For quality**: Use `"ultrathink"` (32k tokens)
- 23-45 second responses
- Best reasoning and context
- Use during important story moments

**Dynamic approach**: Switch modes per RP
- Action scenes: `"think"` or `"disabled"`
- Normal RP: `"megathink"`
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
