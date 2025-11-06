# Extending the Template System

This guide explains how to add new narrative templates to customize AI responses for different roleplay genres.

## Table of Contents

- [Overview](#overview)
- [Template Structure](#template-structure)
- [Creating a New Genre Template](#creating-a-new-genre-template)
- [Creating Composite Templates](#creating-composite-templates)
- [Template Modes](#template-modes)
- [Testing Your Template](#testing-your-template)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

The template system provides genre-specific narrative guidance to the AI. Templates define:

- **Tone and atmosphere**: Set the mood for responses
- **Pacing guidelines**: Control narrative speed and structure
- **Character development**: Guide characterization approaches
- **Relationship dynamics**: Define interaction patterns
- **Worldbuilding elements**: Establish setting details

### Template Modes

The system supports 4 template modes:

1. **Auto**: Automatically detects genre from `ROLEPLAY_OVERVIEW.md`
2. **Composite**: Uses pre-made multi-genre templates
3. **Modular**: Mix and match sections from different genres
4. **Layered**: Primary genre + secondary highlights

## Template Structure

Templates are JSON files stored in the template directory (e.g., `templates/narrative/`).

### Basic Template Format

```json
{
  "display_name": "Genre Name",
  "description": "Brief description of this template",
  "highlights": [
    "Key characteristic 1",
    "Key characteristic 2",
    "Key characteristic 3"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Guideline 1",
        "Guideline 2",
        "Guideline 3"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Pacing guideline 1",
        "Pacing guideline 2"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Character guideline 1",
        "Character guideline 2"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Relationship guideline 1",
        "Relationship guideline 2"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Worldbuilding guideline 1",
        "Worldbuilding guideline 2"
      ]
    }
  }
}
```

### Required Fields

- **`display_name`** (string): Human-readable template name
- **`sections`** (object): Section definitions (see below)

### Optional Fields

- **`description`** (string): Template description for documentation
- **`highlights`** (list): Key characteristics (used in layered mode)

### Standard Sections

Templates typically include these sections (all optional):

| Section Key | Title | Purpose |
|------------|-------|---------|
| `tone_and_atmosphere` | Tone & Atmosphere | Set mood, feeling, emotional tone |
| `pacing` | Pacing | Control narrative speed, scene transitions |
| `character_development` | Character Development | Guide characterization approach |
| `relationship_dynamics` | Relationship Dynamics | Define interaction patterns |
| `worldbuilding` | Worldbuilding | Establish setting, rules, details |

You can add custom sections as needed.

## Creating a New Genre Template

### Step 1: Define Your Genre

Decide on:
- **Genre name**: e.g., "Cyberpunk", "Steampunk", "Urban Fantasy"
- **Filename**: Lowercase with underscores, e.g., `cyberpunk.json`, `urban_fantasy.json`
- **Key characteristics**: What makes this genre unique?

### Step 2: Create the Template File

Create a new JSON file in the template directory:

**Example: `templates/narrative/cyberpunk.json`**

```json
{
  "display_name": "Cyberpunk",
  "description": "High-tech dystopian future with corporate control and underground resistance",
  "highlights": [
    "Neon-lit urban environments with stark class divisions",
    "Advanced technology contrasted with societal decay",
    "Themes of identity, control, and rebellion"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Create a gritty, neon-soaked atmosphere with rain-slicked streets and holographic advertisements",
        "Emphasize the contrast between high-tech luxury and low-life squalor",
        "Incorporate themes of corporate oppression, surveillance, and technological augmentation",
        "Use sensory details: buzzing neon, chrome reflections, synthetic smells, digital interference"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Balance high-octane action sequences with slower moments of introspection and planning",
        "Use quick cuts and rapid scene transitions during chase scenes or cyber-combat",
        "Allow for methodical pacing during hacking sequences or investigation scenes",
        "Build tension through countdown timers, corporate pursuit, or system failures"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Explore the impact of cybernetic augmentation on identity and humanity",
        "Develop characters with complex relationships to technology (addiction, dependence, rejection)",
        "Show moral ambiguity: antiheroes, corrupt cops, sympathetic corporate agents",
        "Address themes of memory, consciousness, and what makes someone 'real'"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Build relationships based on mutual benefit, shared survival, or common enemies",
        "Incorporate digital intimacy: relationships formed or maintained through cyberspace",
        "Show trust issues stemming from constant surveillance and identity theft",
        "Explore found family dynamics within street gangs, hacker collectives, or rebel cells"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Describe megacorporations that control aspects of daily life (water, air, data, security)",
        "Detail cyberspace/the net as a parallel dimension with its own rules and dangers",
        "Incorporate body modification shops, underground markets, and safe houses",
        "Reference AI entities, rogue programs, and digital ghosts",
        "Show environmental decay: acid rain, polluted skies, abandoned zones"
      ]
    }
  }
}
```

### Step 3: Test the Template

1. **Place the file** in your template directory
2. **Update ROLEPLAY_OVERVIEW.md** with `**Genre**: Cyberpunk`
3. **Set config** to use auto mode: `narrative_template.mode = "auto"`
4. **Generate a response** and verify the template loads

### Step 4: Verify Template Discovery

Check that your template is discoverable:

```python
from refactoring.src.automation.templates.template_registry import TemplateRegistry

registry = TemplateRegistry(template_dir)
available = registry.list_available_templates()

assert "cyberpunk" in available
assert registry.has_template("cyberpunk")
```

## Creating Composite Templates

Composite templates combine two genres into a single template.

### Naming Convention

Use format: `{genre1}_{genre2}.json`

Examples:
- `dark_romance.json` = Dark + Romance
- `fantasy_mystery.json` = Fantasy + Mystery
- `sci_fi_horror.json` = Sci-Fi + Horror

### Structure

Composite templates have the same structure as regular templates but blend elements:

**Example: `templates/narrative/dark_romance.json`**

```json
{
  "display_name": "Dark Romance",
  "description": "Intense romance with dark themes, moral complexity, and emotional turmoil",
  "highlights": [
    "Emotionally intense relationships with high stakes",
    "Morally complex characters with dark pasts or impulses",
    "Themes of obsession, redemption, and forbidden love"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Create an atmosphere of tension and intensity with gothic or noir elements",
        "Balance passionate moments with darker themes (danger, secrets, moral conflict)",
        "Use sensory details that evoke both desire and unease",
        "Incorporate shadows, storms, isolated settings that heighten emotional intensity"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Build slow-burn tension punctuated by intense emotional or physical confrontations",
        "Use close proximity and forced proximity scenarios to heighten attraction",
        "Balance intimate moments with revelations that complicate the relationship",
        "Allow for emotional processing after intense scenes"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Develop flawed, complex characters with dark secrets or troubled pasts",
        "Show internal conflict between desire and self-preservation",
        "Explore themes of redemption, healing through connection, or mutual corruption",
        "Reveal character depths gradually through vulnerability and confession"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Emphasize power dynamics that shift and evolve",
        "Build relationships on intense attraction mixed with danger or moral conflict",
        "Show emotional intimacy developing alongside (or despite) physical attraction",
        "Incorporate themes of obsession, possession, devotion, or codependency",
        "Allow for unhealthy patterns that characters recognize and work to change"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Set scenes in atmospheric locations: gothic manors, isolated cabins, underground clubs",
        "Incorporate elements that isolate characters or force them together",
        "Use setting to reflect character psychology (decay, shadows, locked rooms)",
        "Include societal or moral constraints that make the relationship forbidden or dangerous"
      ]
    }
  }
}
```

### Auto-Discovery

The system automatically discovers composite templates:

```python
# In ROLEPLAY_OVERVIEW.md:
**Genre**: Dark / Romance

# System will:
# 1. Try to find "dark_romance.json" or "romance_dark.json"
# 2. Fall back to layered mode (dark.json + romance highlights)
```

## Template Modes

### Mode 1: Auto (Recommended)

Automatically detects genre from `ROLEPLAY_OVERVIEW.md`.

**Configuration:**
```json
{
  "narrative_template": {
    "mode": "auto"
  }
}
```

**ROLEPLAY_OVERVIEW.md:**
```markdown
## Basic Information

**Genre**: Cyberpunk / Romance
```

**Behavior:**
1. Tries to find composite template: `cyberpunk_romance.json` or `romance_cyberpunk.json`
2. Falls back to layered: `cyberpunk.json` + `romance` highlights
3. Falls back to primary only: `cyberpunk.json`

### Mode 2: Composite

Uses a specific pre-made template.

**Configuration:**
```json
{
  "narrative_template": {
    "mode": "composite",
    "template": "dark_romance"
  }
}
```

**Use when:** You want to force a specific template regardless of ROLEPLAY_OVERVIEW.md.

### Mode 3: Modular

Mix sections from different templates.

**Configuration:**
```json
{
  "narrative_template": {
    "mode": "modular",
    "sections": {
      "tone_and_atmosphere": "cyberpunk",
      "pacing": "thriller",
      "character_development": "romance",
      "relationship_dynamics": "romance",
      "worldbuilding": "cyberpunk"
    }
  }
}
```

**Use when:** You want fine-grained control over each section.

### Mode 4: Layered

Primary genre + secondary highlights.

**Configuration:**
```json
{
  "narrative_template": {
    "mode": "layered",
    "primary": "cyberpunk",
    "secondary": "romance"
  }
}
```

**Output:**
```
**Genre**: Cyberpunk
[Full cyberpunk template sections]

**Secondary Influences: Romance**
- Emotional intimacy and vulnerability
- Character relationships as central focus
- Themes of connection and trust
```

## Testing Your Template

### Manual Testing

1. **Create test ROLEPLAY_OVERVIEW.md**:
```markdown
**Genre**: Your New Genre
```

2. **Set auto mode** in config

3. **Generate narrative instructions**:
```python
from refactoring.src.automation.templates.narrative_template_manager import NarrativeTemplateManager

manager = NarrativeTemplateManager(rp_dir, config, loader, registry)
instructions = manager.generate_narrative_instructions()
print(instructions)
```

4. **Verify output** contains your template sections

### Automated Testing

Create tests in `tests/automation/templates/`:

```python
"""Test custom genre template loading."""

import json
import tempfile
from pathlib import Path

import pytest

from refactoring.src.automation.templates.template_loader import TemplateLoader
from refactoring.src.automation.templates.template_cache import TemplateCache


@pytest.fixture
def temp_template_dir():
    """Create temporary template directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "templates"
        template_dir.mkdir()
        yield template_dir


def test_cyberpunk_template_loads(temp_template_dir):
    """Test cyberpunk template loads correctly."""
    # Create template file
    template_data = {
        "display_name": "Cyberpunk",
        "sections": {
            "tone_and_atmosphere": {
                "title": "Tone & Atmosphere",
                "content": ["Neon-lit streets", "Corporate dystopia"]
            }
        }
    }

    template_file = temp_template_dir / "cyberpunk.json"
    template_file.write_text(json.dumps(template_data, indent=2))

    # Load template
    cache = TemplateCache(max_size=10)
    loader = TemplateLoader(template_dir=temp_template_dir, cache=cache)

    loaded = loader.load_template("cyberpunk")

    assert loaded is not None
    assert loaded["display_name"] == "Cyberpunk"
    assert "tone_and_atmosphere" in loaded["sections"]


def test_composite_template_discovery(temp_template_dir):
    """Test composite template is discovered correctly."""
    from refactoring.src.automation.templates.template_registry import TemplateRegistry

    # Create composite template
    template_data = {"display_name": "Dark Romance", "sections": {}}
    template_file = temp_template_dir / "dark_romance.json"
    template_file.write_text(json.dumps(template_data, indent=2))

    # Test discovery
    registry = TemplateRegistry(template_dir=temp_template_dir)

    assert registry.has_template("dark_romance")
    found = registry.find_composite_template("dark", "romance")
    assert found == "dark_romance"
```

## Best Practices

### Content Guidelines

1. **Be specific and actionable**: Instead of "Make it dark", say "Use shadowy lighting, morally ambiguous choices, and consequences that linger"

2. **Provide examples**: Instead of "Good pacing", say "Balance high-action chase scenes with slower moments of planning and recovery"

3. **Address multiple senses**: Include visual, auditory, tactile, olfactory details where appropriate

4. **Balance prescription and flexibility**: Give guidance without being overly restrictive

### Structure Guidelines

1. **Use consistent section keys**: Stick to standard sections when possible for modular mode compatibility

2. **Keep sections focused**: Each section should address its specific aspect (tone vs. pacing vs. relationships)

3. **3-5 content items per section**: Enough detail without overwhelming

4. **Prioritize most important guidance**: Put critical elements first

### Naming Guidelines

1. **Filename**: Lowercase, underscores, descriptive
   - ✅ `urban_fantasy.json`
   - ❌ `Urban Fantasy.json`
   - ❌ `uf.json`

2. **Display name**: Capitalized, spaces, readable
   - ✅ `"Urban Fantasy"`
   - ❌ `"urban_fantasy"`

3. **Composite templates**: Both genre names, order doesn't matter
   - ✅ `sci_fi_horror.json` or `horror_sci_fi.json`
   - ❌ `scifi_horror.json` (inconsistent abbreviation)

### Maintenance

1. **Version control**: Track template changes in git
2. **Documentation**: Include `description` field explaining template purpose
3. **Testing**: Test templates after creating/modifying
4. **Backward compatibility**: Avoid breaking changes to existing templates

## Examples

### Fantasy Template

**File**: `templates/narrative/fantasy.json`

```json
{
  "display_name": "Fantasy",
  "description": "Classic fantasy with magic, quests, and epic scope",
  "highlights": [
    "Magic systems with clear rules and costs",
    "Epic quests with high stakes",
    "Rich worldbuilding with history and cultures"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Create a sense of wonder and adventure",
        "Balance light and dark moments: heroism and sacrifice",
        "Incorporate magical elements that feel wondrous yet dangerous",
        "Use sensory details that evoke medieval-inspired settings: stone castles, forest paths, tavern hearths"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Allow for epic scope: long journeys, gradual character growth, world exploration",
        "Balance action sequences with quieter character moments and worldbuilding",
        "Use quest structure: preparation, journey, confrontation, resolution",
        "Include setbacks and victories to create rising and falling action"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Show heroes growing from inexperienced to capable",
        "Explore themes of destiny vs. choice, power vs. responsibility",
        "Develop mentors, companions, and rivals with their own arcs",
        "Address the cost of heroism: what characters must sacrifice or lose"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Build found family dynamics within adventuring parties",
        "Show bonds forged through shared danger and hardship",
        "Explore loyalty, betrayal, and redemption",
        "Include political alliances, ancient enmities, and unlikely friendships"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Describe diverse cultures, kingdoms, and magical traditions",
        "Incorporate ancient prophecies, historical conflicts, and legendary artifacts",
        "Show magic as a force with rules, limitations, and consequences",
        "Reference mythical creatures, enchanted locations, and sacred sites",
        "Detail social structures: guilds, noble houses, magical orders"
      ]
    }
  }
}
```

### Slice of Life Template

**File**: `templates/narrative/slice_of_life.json`

```json
{
  "display_name": "Slice of Life",
  "description": "Everyday moments and relationships with emotional authenticity",
  "highlights": [
    "Focus on mundane beauty and small meaningful moments",
    "Character-driven with emphasis on relationships and growth",
    "Gentle pacing with emphasis on atmosphere and emotion"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Create a warm, grounded atmosphere that feels lived-in and authentic",
        "Emphasize sensory details of everyday life: morning coffee, seasonal changes, familiar routines",
        "Balance comfortable moments with gentle emotional depth",
        "Use tone to evoke nostalgia, contentment, or bittersweet reflection"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Allow for slow, meandering scenes that linger on small moments",
        "Let conversations develop naturally without rushing to plot points",
        "Use seasonal or time-of-day markers to structure scenes gently",
        "Permit introspection and observation without constant action"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Show gradual, subtle character growth through small realizations",
        "Focus on internal emotional journeys rather than external conflicts",
        "Develop characters through their daily habits, preferences, and quirks",
        "Explore how relationships shape and change people over time"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Build relationships through repeated small interactions and shared routines",
        "Show intimacy in quiet moments: comfortable silences, inside jokes, thoughtful gestures",
        "Explore family dynamics, friendships, and community connections",
        "Address minor conflicts that reveal deeper understanding"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Describe settings that feel like real places: neighborhood cafes, local parks, cozy apartments",
        "Incorporate seasonal details and how they affect daily life",
        "Show community through recurring background characters and local culture",
        "Ground the world in specific, relatable details rather than grand scope"
      ]
    }
  }
}
```

### Mystery Template

**File**: `templates/narrative/mystery.json`

```json
{
  "display_name": "Mystery",
  "description": "Investigation and puzzle-solving with clues and red herrings",
  "highlights": [
    "Structured clue revelation and deduction",
    "Atmosphere of suspense and intrigue",
    "Fair play mystery with solvable puzzles"
  ],
  "sections": {
    "tone_and_atmosphere": {
      "title": "Tone & Atmosphere",
      "content": [
        "Create an atmosphere of intrigue and suspicion",
        "Use environmental details that hint at secrets: locked rooms, hidden compartments, whispered conversations",
        "Balance tension with moments of deductive clarity",
        "Incorporate motifs that recur as clues: specific objects, phrases, or behaviors"
      ]
    },
    "pacing": {
      "title": "Pacing",
      "content": [
        "Structure investigation in phases: discovery, evidence gathering, deduction, revelation",
        "Intersperse action or discovery with analysis and theorizing",
        "Build tension through ticking clocks, escalating danger, or mounting evidence",
        "Pace clue revelation to maintain engagement without overwhelming"
      ]
    },
    "character_development": {
      "title": "Character Development",
      "content": [
        "Show investigative mindset: observation, logical thinking, pattern recognition",
        "Develop characters through how they approach problems and handle dead ends",
        "Explore themes of truth-seeking, justice, and the cost of knowledge",
        "Include character flaws that complicate investigation: biases, blind spots, personal stakes"
      ]
    },
    "relationship_dynamics": {
      "title": "Relationship Dynamics",
      "content": [
        "Build partnerships based on complementary skills and mutual trust",
        "Show suspicion affecting relationships: everyone is a potential suspect",
        "Explore loyalty vs. truth when evidence implicates friends or allies",
        "Include interrogation dynamics: reading people, building rapport, applying pressure"
      ]
    },
    "worldbuilding": {
      "title": "Worldbuilding",
      "content": [
        "Describe settings that can hold secrets: old mansions, corporate offices, small towns with history",
        "Incorporate social structures that affect investigation: class barriers, professional codes, local politics",
        "Show how evidence is preserved, analyzed, or contaminated",
        "Reference investigative tools and methods appropriate to the setting"
      ]
    }
  }
}
```

## Summary

1. Create JSON template with `display_name` and `sections`
2. Use standard section keys for modular compatibility
3. Write specific, actionable content guidelines
4. Test template loading and rendering
5. Follow naming conventions for auto-discovery
6. Document your template with `description` field

For questions or issues, refer to existing templates in `templates/narrative/`.
