# TUI Theming Guide - Complete Reference

**Last Updated**: 2025-10-16
**File Reference**: `src/rp_client_tui.py`
**Difficulty**: Medium
**Time to Create New Theme**: 15-30 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Theme Architecture](#theme-architecture)
3. [Color Reference](#color-reference)
4. [Themeable Elements](#themeable-elements)
5. [Create Your Own Theme](#create-your-own-theme)
6. [Theme Presets](#theme-presets)
7. [Advanced Customization](#advanced-customization)
8. [Testing & Debugging](#testing--debugging)

---

## Overview

The RP Client TUI uses a **three-layer theming system**:

1. **PALETTE dictionary** - 9 core colors that define the theme
2. **CSS styling** - Global styles using PALETTE colors
3. **Inline Python styling** - Component-specific colors and styles
4. **Textual themes** - Built-in theme system (dark, light, nord, dracula, etc.)

All three layers work together to create a cohesive visual experience.

### Quick Theme Change

Users can cycle through built-in themes with **Ctrl+T** (lines 1762-1779):
```python
available_themes = [
    "dark", "light", "nord", "dracula",
    "solarized-dark", "solarized-light", "monokai"
]
```

---

## Theme Architecture

### Layer 1: PALETTE Dictionary

**Location**: `src/rp_client_tui.py:54-64`

```python
PALETTE = {
    "primary": "#4c2a85",        # Main brand color (header, overlays)
    "surface": "#120f1c",         # Main background
    "panel": "#1b1430",          # Panel backgrounds
    "boost": "#221a38",          # Elevated areas (input, footer)
    "accent": "#f9a826",         # Highlights, important text
    "text": "#f2ecff",           # Primary text color
    "text_muted": "#9e94c6",     # Dimmed text (hints, metadata)
    "border": "#31224c",         # Borders and dividers
    "warning": "#f6c177",        # Warning/caution text
}
```

**What each color does:**
- `primary`: Header background, overlay headers, modal backgrounds
- `surface`: Main chat area background, main app background
- `panel`: Left sidebar, footers, input area background
- `boost`: More elevated than panel (input boxes, focus states)
- `accent`: Buttons, highlights, active elements, tab indicators
- `text`: All primary text
- `text_muted`: Secondary text, hints, metadata, disabled states
- `border`: All borders and dividers
- `warning`: Warning text, caution messages, hints

### Layer 2: CSS Styling

**Location**: `src/rp_client_tui.py:1294-1526`

The CSS uses the PALETTE colors in f-string interpolation:
```python
CSS = dedent(
    f"""
    Screen {{
        background: {PALETTE['surface']};
        color: {PALETTE['text']};
    }}

    #app-header {{
        background: {PALETTE['primary']};
        border-bottom: solid {PALETTE['border']};
    }}
    ...
    """
)
```

**Key CSS elements:**
- `Screen` - Main background
- `#app-header` - Top header bar
- `Footer` - Bottom footer
- `#context-panel` - Left sidebar
- `#chat-panel` - Main chat area
- `#input-container` - Bottom input area
- `#input-area` - Text input box
- Overlay containers and modals
- Settings screens
- Buttons, inputs, switches

### Layer 3: Inline Python Styling

**Location**: Various lines in styling functions

**Chat bubbles** (lines 1202-1209):
```python
style_map = {
    "you": ("You", "deep_sky_blue1", Style(bgcolor="#1a2a48")),
    "system": ("System", "gold1", Style(bgcolor="#2c223d")),
    "claude": ("DM", "spring_green3", Style(bgcolor="#1c2f1c")),
}
```

**Context panel cards** (lines 1064-1141):
```python
# Dynamic colors based on component
make_panel("Chapter", [chapter_text], border="medium_purple3")
make_panel("Session Time", [time_text], border="turquoise2")
make_panel("Location", [location_text], border="medium_spring_green")
make_panel("Active Characters", active_lines, border="gold1")
```

**Progress bar colors** (lines 1112-1117):
```python
if completion_ratio < 0.33:
    bar_color = "dark_cyan"
elif completion_ratio < 0.66:
    bar_color = "gold1"
else:
    bar_color = "spring_green3"
```

---

## Color Reference

### Palette Colors with Hex Values

| Color | Hex Value | Usage | RGB |
|-------|-----------|-------|-----|
| primary | #4c2a85 | Headers, overlays, modals | 76, 42, 133 |
| surface | #120f1c | Main background | 18, 15, 28 |
| panel | #1b1430 | Panels, sidebars | 27, 20, 48 |
| boost | #221a38 | Elevated elements | 34, 26, 56 |
| accent | #f9a826 | Highlights, buttons | 249, 168, 38 |
| text | #f2ecff | Primary text | 242, 236, 255 |
| text_muted | #9e94c6 | Secondary text | 158, 148, 198 |
| border | #31224c | Borders | 49, 34, 76 |
| warning | #f6c177 | Warnings, hints | 246, 193, 119 |

### Current Theme (Aesthetic)

**Style**: Dark purple and gold theme
- **Palette**: Deep purples, gold accents
- **Mood**: Mystical, sophisticated
- **Accessibility**: Good contrast, readable

---

## Themeable Elements

### By Component

#### 1. Header (`#app-header`)
- **Background**: `PALETTE['primary']`
- **Border**: `PALETTE['border']`
- **Text**: `PALETTE['accent']` (location/time)
- **Location**: Lines 1301-1305, 1264-1267

#### 2. Footer
- **Background**: `PALETTE['panel']`
- **Border**: `PALETTE['border']`
- **Text**: Default text color
- **Location**: Lines 1307-1311

#### 3. Left Sidebar (`#context-panel`)
- **Background**: `PALETTE['panel']`
- **Border**: `PALETTE['border']`
- **Text**: `PALETTE['text']`
- **Card borders**: Dynamic colors (medium_purple3, turquoise2, etc.)
- **Location**: Lines 1318-1329, 1064-1148

#### 4. Chat Panel (`#chat-panel`)
- **Background**: `PALETTE['surface']`
- **Text**: `PALETTE['text']`
- **Message bubbles**: Inline styles (lines 1202-1209)
  - You: deep_sky_blue1 with bgcolor="#1a2a48"
  - System: gold1 with bgcolor="#2c223d"
  - Claude/DM: spring_green3 with bgcolor="#1c2f1c"
- **Location**: Lines 1331-1341, 1202-1225

#### 5. Input Area (`#input-container`)
- **Background**: `PALETTE['panel']`
- **Border**: `PALETTE['border']`
- **Label text**: `PALETTE['accent']`
- **Text**: `PALETTE['text']`
- **Location**: Lines 1343-1397

#### 6. Input Field (`#input-area`)
- **Background**: `PALETTE['boost']` (normal), `PALETTE['surface']` (focused)
- **Border**: `PALETTE['border']` (normal), `PALETTE['accent']` (focused)
- **Text**: `PALETTE['text']`
- **Location**: Lines 1362-1373

#### 7. Progress Bar
- **Colors**: Dynamic based on completion
  - 0-33%: dark_cyan
  - 33-66%: gold1
  - 66-100%: spring_green3
- **Location**: Lines 1112-1117

#### 8. Overlays & Modals
- **Background**: `PALETTE['panel']`
- **Header background**: `PALETTE['primary']`
- **Border**: `PALETTE['border']`
- **Text**: `PALETTE['text']`, `PALETTE['text_muted']`
- **Location**: Lines 1400-1441

#### 9. Settings Screen
- **Background**: `PALETTE['panel']`
- **Section titles**: `PALETTE['accent']`
- **Labels**: `PALETTE['text']`
- **Info text**: `PALETTE['text_muted']`
- **Hints**: `PALETTE['warning']`
- **Location**: Lines 1443-1521

#### 10. Buttons
- **Focus state**: Bold text
- **Styling**: Standard Textual button styling
- **Location**: Lines 1509-1511

#### 11. Inputs & Switches
- **Background**: `PALETTE['boost']`
- **Border**: `PALETTE['border']` (normal), `PALETTE['accent']` (focused)
- **Location**: Lines 1513-1524

---

## Create Your Own Theme

### Step 1: Define Your PALETTE

Choose 9 colors that work well together. Consider:
- **Color harmony** - Complementary, analogous, or triadic schemes
- **Contrast** - Ensure text is readable on backgrounds
- **Mood** - Dark/light, warm/cool, energetic/calm

**Template**:
```python
MY_THEME_PALETTE = {
    "primary": "#XXXXXX",        # Main brand color
    "surface": "#XXXXXX",         # Main background
    "panel": "#XXXXXX",          # Panel backgrounds
    "boost": "#XXXXXX",          # Elevated areas
    "accent": "#XXXXXX",         # Highlights
    "text": "#XXXXXX",           # Primary text
    "text_muted": "#XXXXXX",     # Dimmed text
    "border": "#XXXXXX",         # Borders
    "warning": "#XXXXXX",        # Warning text
}
```

### Step 2: Example Themes

#### Theme: "Ocean Blue"
```python
OCEAN_PALETTE = {
    "primary": "#001f3f",        # Navy
    "surface": "#000814",        # Very dark blue
    "panel": "#001d3d",          # Dark blue
    "boost": "#003566",          # Ocean blue
    "accent": "#00d4ff",         # Cyan
    "text": "#e0f7ff",           # Light cyan
    "text_muted": "#7fa3b3",     # Muted blue
    "border": "#004d73",         # Blue
    "warning": "#ffa500",        # Orange
}
```

#### Theme: "Forest Green"
```python
FOREST_PALETTE = {
    "primary": "#1b4332",        # Dark green
    "surface": "#0b3618",        # Very dark green
    "panel": "#2d6a4f",          # Forest green
    "boost": "#40916c",          # Medium green
    "accent": "#95d5b2",         # Light green
    "text": "#d8f3dc",           # Very light green
    "text_muted": "#74a99b",     # Muted green
    "border": "#1b4332",         # Dark green
    "warning": "#ffb700",        # Amber
}
```

#### Theme: "Cherry Red"
```python
CHERRY_PALETTE = {
    "primary": "#5c0a0a",        # Dark red
    "surface": "#2a0506",        # Very dark red
    "panel": "#7a0d0d",          # Cherry red
    "boost": "#a01a1a",          # Medium red
    "accent": "#ff6b6b",         # Bright red
    "text": "#ffe6e6",           # Light pink
    "text_muted": "#c9a8a8",     # Muted red
    "border": "#6b1414",         # Red
    "warning": "#ffd700",        # Gold
}
```

### Step 3: Update Chat Bubble Colors

If using a different color scheme, update the inline styles at lines 1202-1209:

```python
style_map = {
    "you": ("You", "YOUR_COLOR_1", Style(bgcolor="YOUR_BG_1")),
    "system": ("System", "YOUR_COLOR_2", Style(bgcolor="YOUR_BG_2")),
    "claude": ("DM", "YOUR_COLOR_3", Style(bgcolor="YOUR_BG_3")),
}
```

Use Rich color names or hex codes. Common colors:
- Blues: `deep_sky_blue1`, `blue`, `steel_blue`
- Greens: `spring_green3`, `green`, `sea_green`
- Purples: `medium_purple3`, `purple`, `plum`
- Oranges: `orange1`, `gold1`, `orange_red1`

### Step 4: Update Progress Bar Colors

If using a different color scheme, update lines 1112-1117:

```python
if completion_ratio < 0.33:
    bar_color = "YOUR_LOW_COLOR"      # Early progress
elif completion_ratio < 0.66:
    bar_color = "YOUR_MID_COLOR"      # Mid progress
else:
    bar_color = "YOUR_HIGH_COLOR"     # Near complete
```

### Step 5: Update Context Panel Card Borders

If using a different color scheme, update lines 1082-1103:

```python
add_card(make_panel("Chapter", [chapter_text], border="YOUR_COLOR"))
add_card(make_panel("Session Time", [time_text], border="YOUR_COLOR"))
add_card(make_panel("Location", [location_text], border="YOUR_COLOR"))
add_card(make_panel("Active Characters", active_lines, border="YOUR_COLOR"))
```

### Step 6: Apply Your Theme

Replace the PALETTE definition at lines 54-64:

```python
PALETTE = MY_THEME_PALETTE  # or OCEAN_PALETTE, FOREST_PALETTE, etc.
```

---

## Theme Presets

### Using Built-in Textual Themes

The app supports cycling through built-in themes with **Ctrl+T**.

**Current rotation** (lines 1764-1766):
```python
available_themes = [
    "dark", "light", "nord", "dracula",
    "solarized-dark", "solarized-light", "monokai"
]
```

**To add more themes**, edit the list at line 1765:

```python
available_themes = [
    "dark", "light", "nord", "dracula",
    "solarized-dark", "solarized-light", "monokai",
    "your_theme_name",  # Add custom themes here
]
```

### Creating Multiple Palettes

Store multiple palettes and switch between them:

```python
PALETTES = {
    "current": {
        "primary": "#4c2a85",
        ...
    },
    "ocean": {
        "primary": "#001f3f",
        ...
    },
    "forest": {
        "primary": "#1b4332",
        ...
    },
}

# To switch:
PALETTE = PALETTES["ocean"]
```

---

## Advanced Customization

### 1. Dynamic Theming (Runtime Theme Switching)

Create a theme configuration file (`config/theme.json`):

```json
{
    "active_theme": "default",
    "custom_palettes": {
        "ocean": {
            "primary": "#001f3f",
            "surface": "#000814",
            ...
        },
        "forest": {
            "primary": "#1b4332",
            "surface": "#0b3618",
            ...
        }
    }
}
```

Load at runtime:
```python
def load_theme():
    theme_file = Path(__file__).parent.parent / "config" / "theme.json"
    if theme_file.exists():
        config = json.loads(theme_file.read_text())
        return config["custom_palettes"].get(config["active_theme"], PALETTE)
    return PALETTE
```

### 2. User-Configurable Colors

Add a theme editor to the settings screen (F8):

```python
# In SettingsScreen.compose():
yield Static("## Custom Colors", classes="settings-section-title")
yield Static("Primary Color:", classes="settings-label")
yield Input(placeholder="#4c2a85", id="theme-primary-input")
yield Static("Accent Color:", classes="settings-label")
yield Input(placeholder="#f9a826", id="theme-accent-input")
# ... etc for all 9 colors
```

Save to config, then reload on app restart.

### 3. Time-Based Themes

Switch themes based on time of day:

```python
def get_time_based_theme():
    from datetime import datetime
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return PALETTES["morning"]   # Warm theme
    elif 12 <= hour < 17:
        return PALETTES["afternoon"]  # Bright theme
    elif 17 <= hour < 21:
        return PALETTES["evening"]    # Twilight theme
    else:
        return PALETTES["night"]      # Dark theme
```

### 4. Accessibility Themes

Create high-contrast themes for accessibility:

```python
HIGH_CONTRAST_PALETTE = {
    "primary": "#000000",          # Pure black
    "surface": "#ffffff",          # Pure white
    "panel": "#f0f0f0",            # Light gray
    "boost": "#e0e0e0",            # Medium gray
    "accent": "#ff0000",           # Pure red
    "text": "#000000",             # Pure black text on white
    "text_muted": "#666666",       # Dark gray
    "border": "#000000",           # Black borders
    "warning": "#ff6600",          # Orange
}
```

---

## Testing & Debugging

### Test Checklist

When creating a new theme, verify:

- [ ] **Text Readability**: All text is readable (contrast ratio > 4.5:1 for AA)
- [ ] **Color Blindness**: Check with deuteranopia (green-blind) simulator
- [ ] **All Components**: Header, footer, sidebar, chat, input, overlays
- [ ] **Message Bubbles**: All three types (You, System, DM) are distinct
- [ ] **Progress Bar**: All three stages (low, mid, high) are visible
- [ ] **Focused States**: Input field highlight is visible
- [ ] **Buttons**: Primary and default buttons are distinct
- [ ] **Consistency**: Colors used consistently across UI

### Color Contrast Tool

Use online tools to verify accessibility:
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Color Review](https://colorview.io/)

Calculate contrast ratio:
```
Contrast = (L1 + 0.05) / (L2 + 0.05)
where L = (R*0.299 + G*0.587 + B*0.114) / 255
```

For accessibility:
- **AA**: 4.5:1 for normal text, 3:1 for large text
- **AAA**: 7:1 for normal text, 4.5:1 for large text

### Debug Color Values

Print color values to verify:

```python
from rich import print as rprint
from rich.table import Table

table = Table(title="Theme Palette")
table.add_column("Name")
table.add_column("Hex")
table.add_column("Usage")

for name, color in PALETTE.items():
    table.add_row(name, color, "See component list above")

rprint(table)
```

### Test in Different Terminals

Themes may look different in:
- Windows Terminal
- macOS Terminal
- Linux Terminal (various)
- Visual Studio Code integrated terminal
- Different color profiles

Test in multiple environments when possible.

---

## Reference: Complete Theme Example

Here's a complete minimal theme to use as a starting point:

```python
MINIMAL_PALETTE = {
    "primary": "#2c3e50",        # Dark blue-gray
    "surface": "#ecf0f1",        # Light background
    "panel": "#bdc3c7",          # Medium gray
    "boost": "#95a5a6",          # Slightly darker gray
    "accent": "#e74c3c",         # Bright red
    "text": "#2c3e50",           # Dark text
    "text_muted": "#7f8c8d",     # Medium gray text
    "border": "#34495e",         # Dark blue-gray
    "warning": "#f39c12",        # Amber
}
```

---

## File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `src/rp_client_tui.py` | Main theme implementation | 54-64, 1294-1526 |
| `src/rp_client_tui.py` | Chat bubble styling | 1202-1209 |
| `src/rp_client_tui.py` | Context panel styling | 1064-1148 |
| `src/rp_client_tui.py` | Progress bar coloring | 1112-1117 |
| `src/rp_client_tui.py` | Theme cycling | 1762-1779 |

---

## Summary

To create a new theme:

1. **Define PALETTE** with 9 colors (line 54-64)
2. **Choose chat bubble colors** (line 1202-1209)
3. **Choose progress bar colors** (line 1112-1117)
4. **Choose panel card borders** (lines 1082-1103)
5. **Test** all components
6. **Share** with others!

---

**Need Help?**
- Check existing theme examples in this guide
- Use color palette generators (coolors.co, paletton.com)
- Test accessibility with WebAIM Contrast Checker
- Refer to Textual documentation for available color names
