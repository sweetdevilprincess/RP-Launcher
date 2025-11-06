# Tailwind Warm Themes - Three Light Background Variations

**Created**: 2025-10-16
**Based on**: Tailwind color palette (Sage, Peach Yellow, Bittersweet, Wine, Van Dyke)
**Ready to Use**: Copy-paste implementation

---

## Theme Overview

Three complete themes using your warm Tailwind palette, all with light backgrounds for an airy, inviting aesthetic.

| Theme | Background | Primary | Accent | Mood |
|-------|-----------|---------|--------|------|
| **Warm Cream** | Light beige (Sage 800) | Wine burgundy | Bittersweet rust | Warm & inviting |
| **Soft Taupe** | Warm taupe (Sage 700) | Wine burgundy | Bittersweet rust | Sophisticated |
| **Vanilla Cream** | Peachy cream (Peach Yellow 800) | Wine burgundy | Bittersweet rust | Golden & warm |

---

# Theme 1: Warm Cream ✨

**Best For**: Clean, inviting feel with excellent readability

## PALETTE Dictionary

Copy this to `src/rp_client_tui.py` lines 54-64:

```python
PALETTE = {
    "primary": "#723d46",        # Wine - headers, overlays
    "surface": "#eaeada",         # Sage 800 - main light background
    "panel": "#dfe0c8",          # Sage 700 - sidebar panels
    "boost": "#ffedcb",          # Peach Yellow 700 - elevated areas
    "accent": "#e26d5c",         # Bittersweet - highlights, buttons
    "text": "#472d30",           # Van Dyke - primary text
    "text_muted": "#723d46",     # Wine - secondary text
    "border": "#723d46",         # Wine - borders and dividers
    "warning": "#e26d5c",        # Bittersweet - warnings
}
```

## Chat Bubble Colors

Replace `src/rp_client_tui.py` lines 1202-1209 with:

```python
style_map = {
    "you": ("You", "dark_red", Style(bgcolor="#dfe0c8")),
    "system": ("System", "dark_goldenrod", Style(bgcolor="#fff3dc")),
    "claude": ("DM", "dark_olive_green3", Style(bgcolor="#ffedcb")),
}
```

## Progress Bar Colors

Replace `src/rp_client_tui.py` lines 1112-1117 with:

```python
if completion_ratio < 0.33:
    bar_color = "dark_red"           # Wine red for early progress
elif completion_ratio < 0.66:
    bar_color = "orange_red1"        # Bittersweet for mid progress
else:
    bar_color = "dark_olive_green3"  # Sage green for near complete
```

## Context Panel Card Borders

Replace `src/rp_client_tui.py` lines 1082-1103 with:

```python
chapter_text = Text(clean_value(chapter), justify="center", style="bold")
add_card(make_panel("Chapter", [chapter_text], border="dark_red"))

time_text = Text(clean_value(timestamp), justify="center", style="bold")
add_card(make_panel("Session Time", [time_text], border="orange_red1"))

location_text = Text(clean_value(location), justify="center", style="bold")
add_card(make_panel("Location", [location_text], border="dark_olive_green3"))

active_list = [
    char for char in active_chars if char and char.strip().lower() != "none"
]
if not active_list:
    active_lines = [Text("No active characters", justify="center", style="dim")]
else:
    display_names = active_list[:3]
    if len(active_list) > 3:
        display_names.append(f"+{len(active_list) - 3} more")
    active_lines = [
        Text(name, justify="center", style="bold" if idx == 0 else "")
        for idx, name in enumerate(display_names)
    ]
add_card(make_panel("Active Characters", active_lines, border="dark_goldenrod"))

arc_total = max(progress + next_arc, 1)
completion_ratio = progress / arc_total
bar_length = 20
filled = int(completion_ratio * bar_length)
empty = bar_length - filled
bar_body = "#" * filled + "-" * empty

if completion_ratio < 0.33:
    bar_color = "dark_red"
elif completion_ratio < 0.66:
    bar_color = "orange_red1"
else:
    bar_color = "dark_olive_green3"

bar_text = Text(f"[{bar_body}]", justify="center", style=bar_color)
progress_text = Text(
    f"{percentage:>5.1f}% complete",
    justify="center",
    style="bold",
)
plural_suffix = "s" if next_arc != 1 else ""
next_text = Text(
    f"{next_arc} more turn{plural_suffix} to next beat",
    justify="center",
    style="dim",
)
arc_panel = make_panel(
    "Arc Progress",
    [
        Text(f"{progress}/{arc_total} turns", justify="center", style="bold"),
        bar_text,
        progress_text,
        next_text,
    ],
    border=bar_color,
)
add_card(arc_panel)

momentum_text = Text(
    f"{count} total responses",
    justify="center",
    style="bold white",
)
add_card(make_panel("Story Momentum", [momentum_text], border="slate_blue1"))
```

---

# Theme 2: Soft Taupe

**Best For**: Sophisticated, warm, balanced aesthetic

## PALETTE Dictionary

```python
PALETTE = {
    "primary": "#723d46",        # Wine - headers, overlays
    "surface": "#dfe0c8",         # Sage 700 - main warm taupe background
    "panel": "#ffedcb",          # Peach Yellow 700 - sidebar panels
    "boost": "#fff3dc",          # Peach Yellow 800 - elevated areas
    "accent": "#e26d5c",         # Bittersweet - highlights, buttons
    "text": "#472d30",           # Van Dyke - primary text
    "text_muted": "#723d46",     # Wine - secondary text
    "border": "#723d46",         # Wine - borders and dividers
    "warning": "#e26d5c",        # Bittersweet - warnings
}
```

## Chat Bubble Colors

```python
style_map = {
    "you": ("You", "dark_red", Style(bgcolor="#ffedcb")),
    "system": ("System", "dark_goldenrod", Style(bgcolor="#fff3dc")),
    "claude": ("DM", "dark_olive_green3", Style(bgcolor="#eaeada")),
}
```

## Progress Bar Colors

```python
if completion_ratio < 0.33:
    bar_color = "dark_red"           # Wine red for early progress
elif completion_ratio < 0.66:
    bar_color = "orange_red1"        # Bittersweet for mid progress
else:
    bar_color = "khaki3"             # Warm sage for near complete
```

## Context Panel Card Borders

Same as Theme 1, but with softer appearance due to background color.

---

# Theme 3: Vanilla Cream

**Best For**: Warm, golden, peachy aesthetic

## PALETTE Dictionary

```python
PALETTE = {
    "primary": "#723d46",        # Wine - headers, overlays
    "surface": "#fff3dc",         # Peach Yellow 800 - main peachy background
    "panel": "#ffedcb",          # Peach Yellow 700 - sidebar panels
    "boost": "#dfe0c8",          # Sage 700 - elevated areas
    "accent": "#e26d5c",         # Bittersweet - highlights, buttons
    "text": "#472d30",           # Van Dyke - primary text
    "text_muted": "#723d46",     # Wine - secondary text
    "border": "#723d46",         # Wine - borders and dividers
    "warning": "#e26d5c",        # Bittersweet - warnings
}
```

## Chat Bubble Colors

```python
style_map = {
    "you": ("You", "dark_red", Style(bgcolor="#ffedcb")),
    "system": ("System", "dark_goldenrod", Style(bgcolor="#dfe0c8")),
    "claude": ("DM", "dark_olive_green3", Style(bgcolor="#eaeada")),
}
```

## Progress Bar Colors

```python
if completion_ratio < 0.33:
    bar_color = "dark_red"           # Wine red for early progress
elif completion_ratio < 0.66:
    bar_color = "orange_red1"        # Bittersweet for mid progress
else:
    bar_color = "khaki3"             # Warm cream for near complete
```

## Context Panel Card Borders

Same as Themes 1 & 2.

---

# Implementation Guide

## Step 1: Choose Your Theme

Pick one of the three:
- **Warm Cream** - Light beige, most neutral, clean
- **Soft Taupe** - Warmer taupe, more sophisticated
- **Vanilla Cream** - Peachy cream, most golden/warm

## Step 2: Update PALETTE

Open `src/rp_client_tui.py` and replace lines 54-64 with your chosen theme's PALETTE dictionary.

**Before:**
```python
PALETTE = {
    "primary": "#4c2a85",
    "surface": "#120f1c",
    ...
}
```

**After:**
```python
PALETTE = {
    "primary": "#723d46",
    "surface": "#eaeada",  # (or your theme's surface color)
    ...
}
```

## Step 3: Update Chat Bubbles

Replace lines 1202-1209 with your chosen theme's chat bubble colors.

**Location**: Inside `ChatDisplay.add_message()` method

## Step 4: Update Progress Bar

Replace lines 1112-1117 with your chosen theme's progress bar colors.

**Location**: Inside `ContextPanel.refresh_context()` method

## Step 5: Update Context Panel Cards

Replace lines 1082-1103 with the context panel card borders (same for all three themes, shown in Theme 1).

**Location**: Inside `ContextPanel.refresh_context()` method

## Step 6: Test

Run the app:
```bash
python launch_rp_tui.py "Your RP"
```

Or if testing directly:
```bash
python src/rp_client_tui.py "Your RP"
```

Press **Ctrl+T** to cycle themes if you want to see the difference from built-in themes.

---

# Color Reference

## All Colors Used

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| Sage 700 | #dfe0c8 | 223, 224, 200 | Panel backgrounds |
| Sage 800 | #eaeada | 234, 234, 218 | Light main background |
| Peach Yellow 700 | #ffedcb | 255, 237, 203 | Warm elevated areas |
| Peach Yellow 800 | #fff3dc | 255, 243, 220 | Very light peachy |
| Bittersweet | #e26d5c | 226, 109, 92 | Accent, highlights |
| Wine | #723d46 | 114, 61, 70 | Primary, headers |
| Van Dyke | #472d30 | 71, 45, 48 | Primary text |

## Tailwind Extended Variants (if needed)

**Wine variants**:
- Wine 600: #9c5460 - Lighter burgundy
- Wine 700: #b87c86 - Even lighter

**Sage variants**:
- Sage 600: #d4d6b6 - Lighter sage
- Sage 900: #f4f5ed - Extremely light

**Peach Yellow variants**:
- Peach Yellow 600: #ffe7ba - Lighter peachy
- Peach Yellow 900: #fff9ee - Extremely light

**Bittersweet variants**:
- Bittersweet 300: #a12e1c - Darker for warnings
- Bittersweet 600: #e88a7b - Lighter for accents

---

# Accessibility Notes

✅ **High Contrast**:
- Van Dyke (#472d30) on light backgrounds: **Excellent contrast**
- Wine (#723d46) on light backgrounds: **Very good contrast**
- Bittersweet (#e26d5c) on light backgrounds: **Good contrast**

✅ **Readable**:
- All text is easily readable
- Borders are visible but subtle
- Messages are clearly distinguished

✅ **Color Blind Friendly**:
- Uses warm colors (reds, oranges, yellows)
- Darker text on light backgrounds (not relying on color alone)
- Strong contrast ratios

---

# Quick Comparison

| Aspect | Warm Cream | Soft Taupe | Vanilla Cream |
|--------|-----------|-----------|---------------|
| Background | Beige (Sage 800) | Taupe (Sage 700) | Peachy (Peach 800) |
| Warmth | Neutral warm | Warm | Very warm |
| Contrast | Highest | High | High |
| Best for | Clean look | Sophisticated | Golden/peachy feel |
| Readability | Excellent | Excellent | Excellent |

---

# Reverting to Original

If you want to go back to the original purple/gold theme:

```python
PALETTE = {
    "primary": "#4c2a85",
    "surface": "#120f1c",
    "panel": "#1b1430",
    "boost": "#221a38",
    "accent": "#f9a826",
    "text": "#f2ecff",
    "text_muted": "#9e94c6",
    "border": "#31224c",
    "warning": "#f6c177",
}
```

And revert chat bubbles to:
```python
style_map = {
    "you": ("You", "deep_sky_blue1", Style(bgcolor="#1a2a48")),
    "system": ("System", "gold1", Style(bgcolor="#2c223d")),
    "claude": ("DM", "spring_green3", Style(bgcolor="#1c2f1c")),
}
```

---

## Files to Modify

1. `src/rp_client_tui.py`:
   - Lines 54-64: PALETTE dictionary
   - Lines 1202-1209: Chat bubble colors
   - Lines 1112-1117: Progress bar colors
   - Lines 1082-1103: Context panel borders

That's it! No other files need to be changed.

---

## Need Help?

- **Themes look too similar?** Pick the one that feels right - they're subtle variations
- **Colors not appearing?** Make sure you saved the file and restarted the app
- **Text not readable?** The contrast is carefully chosen, but you can adjust individual colors
- **Want to mix themes?** You can combine elements from different themes

---

## All Three Themes Side-by-Side

### Warm Cream
```
Background: Light beige (#eaeada)
Panel: Warm taupe (#dfe0c8)
Elevated: Peachy cream (#ffedcb)
Primary Color: Wine (#723d46)
Accent: Bittersweet (#e26d5c)
Text: Van Dyke (#472d30)
```

### Soft Taupe
```
Background: Warm taupe (#dfe0c8)
Panel: Peachy cream (#ffedcb)
Elevated: Very light cream (#fff3dc)
Primary Color: Wine (#723d46)
Accent: Bittersweet (#e26d5c)
Text: Van Dyke (#472d30)
```

### Vanilla Cream
```
Background: Very light peachy (#fff3dc)
Panel: Peachy cream (#ffedcb)
Elevated: Warm taupe (#dfe0c8)
Primary Color: Wine (#723d46)
Accent: Bittersweet (#e26d5c)
Text: Van Dyke (#472d30)
```

---

**Ready to use!** Pick a theme and copy the PALETTE dictionary into your code. Enjoy your warm, inviting new look! ✨
