"""Theme and color palette for RP Client TUI.

This module defines the color palette and semantic style mappings
used throughout the TUI application.
"""

# Color palette - base colors
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

# Semantic style mappings - reference PALETTE colors by component use
STYLES = {
    # Chat message colors
    "message_you_text": PALETTE['accent'],
    "message_you_bg": PALETTE['panel'],
    "message_system_text": PALETTE['accent'],
    "message_system_bg": PALETTE['boost'],
    "message_dm_text": PALETTE['accent'],
    "message_dm_bg": PALETTE['surface'],

    # Context panel card borders
    "card_chapter": PALETTE['primary'],
    "card_time": PALETTE['accent'],
    "card_location": PALETTE['primary'],
    "card_characters": PALETTE['accent'],
    "card_momentum": PALETTE['border'],

    # Progress bar stages
    "progress_low": PALETTE['primary'],
    "progress_mid": PALETTE['accent'],
    "progress_high": PALETTE['text_muted'],

    # Context panel card background
    "card_bg": PALETTE['boost'],

    # Status message colors (using existing palette)
    "status_error": PALETTE['warning'],
    "status_success": PALETTE['accent'],
    "status_waiting": PALETTE['text_muted'],
    "status_info": PALETTE['text'],

    # Text styling colors
    "text_dim": PALETTE['text_muted'],
    "text_emphasis": PALETTE['accent'],

    # Button text colors
    "button_text_default": PALETTE['surface'],
    "button_text_primary": PALETTE['surface'],
}


# =============================================================================
# COMMON CSS COMPONENTS
# =============================================================================

def get_button_css() -> str:
    """Get CSS for styled buttons."""
    return f"""
    Button {{
        background: {PALETTE['text_muted']};
        color: {STYLES['button_text_default']};
        border: round {PALETTE['border']};
    }}

    Button:hover {{
        background: {PALETTE['primary']};
        text-style: bold;
    }}

    Button.primary {{
        background: {PALETTE['accent']};
        color: {STYLES['button_text_primary']};
        border: round {PALETTE['accent']};
    }}

    Button.primary:hover {{
        background: {PALETTE['warning']};
        text-style: bold;
    }}

    Button:focus {{
        text-style: bold;
        border: round {PALETTE['accent']};
    }}

    Button:disabled {{
        opacity: 0.5;
    }}
    """


def get_input_css() -> str:
    """Get CSS for input fields."""
    return f"""
    Input {{
        background: {PALETTE['boost']};
        color: {PALETTE['text']};
        border: round {PALETTE['border']};
    }}

    Input:focus {{
        border: round {PALETTE['accent']};
        color: {PALETTE['text']};
    }}
    """


def get_textarea_css() -> str:
    """Get CSS for text areas."""
    return f"""
    TextArea {{
        background: {PALETTE['boost']};
        color: {PALETTE['text']};
        border: round {PALETTE['border']};
    }}

    TextArea:focus {{
        border: round {PALETTE['accent']};
    }}
    """


def get_select_css() -> str:
    """Get CSS for select dropdowns."""
    return f"""
    Select {{
        background: {PALETTE['boost']};
        color: {PALETTE['text']};
        border: solid {PALETTE['border']};
    }}

    Select:focus {{
        border: solid {PALETTE['accent']};
    }}

    Select > SelectCurrent {{
        background: {PALETTE['boost']};
        color: {PALETTE['text']};
        border: none;
    }}

    Select > SelectOverlay {{
        background: {PALETTE['panel']};
        border: solid {PALETTE['accent']};
    }}

    Select > SelectOverlay > OptionList {{
        background: {PALETTE['panel']};
        color: {PALETTE['text']};
    }}

    Select > SelectOverlay > OptionList > .option-list--option-highlighted {{
        background: {PALETTE['boost']};
        color: {PALETTE['text']};
    }}
    """


def get_scrollbar_css(background_color: str = None) -> str:
    """Get CSS for scrollbars."""
    bg = background_color or PALETTE['panel']
    return f"""
    scrollbar-background: {bg};
    scrollbar-background-hover: {bg};
    scrollbar-color: {PALETTE['accent']};
    scrollbar-color-hover: {PALETTE['accent']};
    scrollbar-size: 2 1;
    """


def get_header_css() -> str:
    """Get CSS for page headers."""
    return f"""
    .page-header {{
        dock: top;
        background: {PALETTE['primary']};
        color: {PALETTE['surface']};
        padding: 1 2;
        text-align: center;
        height: 3;
        text-style: bold;
    }}
    """


def get_panel_css() -> str:
    """Get CSS for content panels."""
    return f"""
    .content-panel {{
        background: {PALETTE['panel']};
        border: round {PALETTE['border']};
        padding: 2;
    }}

    .panel-title {{
        color: {PALETTE['accent']};
        text-style: bold;
        margin-bottom: 1;
    }}

    .panel-description {{
        color: {PALETTE['text_muted']};
        margin-bottom: 2;
        text-style: italic;
    }}
    """


def get_overlay_css() -> str:
    """Get CSS for modal overlay screens."""
    return f"""
    #overlay-container {{
        width: 100%;
        height: 100%;
        background: {PALETTE['panel']};
        border: round {PALETTE['border']};
        padding: 0;
        align: center middle;
    }}

    #overlay-title {{
        text-style: bold;
        background: {PALETTE['primary']};
        color: {PALETTE['surface']};
        padding: 1 2;
        dock: top;
        text-align: center;
    }}

    #overlay-content {{
        height: 1fr;
        padding: 1 2;
        background: {PALETTE['panel']};
        overflow-y: auto;
        scrollbar-background: {PALETTE['panel']};
        scrollbar-background-hover: {PALETTE['panel']};
        scrollbar-color: {PALETTE['accent']};
        scrollbar-color-hover: {PALETTE['accent']};
        scrollbar-size: 2 1;
    }}

    #overlay-footer {{
        text-style: dim;
        text-align: center;
        padding: 1 2;
        dock: bottom;
        background: {PALETTE['boost']};
        color: {PALETTE['text_muted']};
    }}

    #tab-selector {{
        text-align: center;
        padding: 1 2;
        text-style: bold;
        color: {PALETTE['text']};
        background: {PALETTE['boost']};
        dock: top;
    }}

    #story-content {{
        height: 1fr;
        color: {PALETTE['text']};
    }}
    """


def get_app_css() -> str:
    """Get CSS for main RPClientApp."""
    return """
/* ========================================
   GLOBAL STYLES
   ======================================== */

Screen {
    background: $surface;
    color: $text;
    layers: base overlay top;
}


/* ========================================
   LAYOUT & CONTAINERS
   ======================================== */
#top-tabs {
    dock: top;
    layer: top;
    background: $primary;
    border-bottom: solid $primary;
    height: 3;
    padding: 0;
}

#top-tabs Tab {
    background: $primary;
    color: $surface;
    border: none;
    padding: 0 2;
    text-style: none;
    content-align: center middle;
    text-opacity: 70%;
}

#top-tabs Tab:hover {
    background: $panel;
    color: $text;
    text-style: bold;
    text-opacity: 85%;
}

#top-tabs Tab.-active {
    background: $accent;
    color: $surface;
    text-style: bold;
    border-bottom: thick $surface;
    text-opacity: 100%;
}

#app-header {
    dock: bottom;
    layer: top;
    background: $primary;
    color: $surface;
    padding: 0 2;
    height: 2;
    border-top: solid $primary;
}

#main-container {
    layout: horizontal;
    height: 1fr;
}

#content-switcher {
    height: 1fr;
    width: 1fr;
}

.page-container {
    layout: horizontal;
    height: 1fr;
    width: 1fr;
}

#chat-page-header {
    text-style: bold;
    background: $primary;
    color: $surface;
    padding: 1 2;
    text-align: center;
    height: 3;
}

.settings-page, .help-page, .status-page {
    padding: 2;
    background: $surface;
    overflow-y: auto;
    width: 1fr;
}

.transparent-page {
    background: transparent;
    width: 1fr;
    height: 1fr;
}

.blank-page {
    width: 100%;
    height: 100%;
    background: $panel;
}

/* ========================================
   CONTENT PANELS
   ======================================== */
#context-panel {
    width: 30%;
    background: $panel;
    color: $text;
    padding: 1 2;
    margin-top: 3;
    border-right: solid $primary;
    overflow-y: auto;
    overflow-x: hidden;
}

#chat-panel {
    width: 1fr;
    padding: 2 3 2 2;
    margin-top: 2;
    background: $surface;
    overflow: auto;
}

#message-content {
    width: 1fr;
    height: auto;
    color: $text;
    margin-bottom: 3;
}


/* ========================================
   INPUT SECTION
   ======================================== */
#input-container {
    background: $panel;
    padding: 1 2;
    border-top: solid $primary;
    layout: vertical;
    height: 10;
    min-height: 10;
    max-height: 10;
}

#input-label {
    color: $accent;
    text-style: bold;
    height: 1;
}

#input-row {
    layout: horizontal;
    align: left middle;
    padding-right: 1;
    height: 6;
}

#input-area {
    height: 5;
    min-height: 5;
    max-height: 5;
    width: 1fr;
    background: $surface;
    border: round $primary;
    padding: 0 1;
    color: $text;
}

#input-area:focus {
    border: round $accent;
    background: $surface;
    color: $text;
}

#input-controls {
    layout: vertical;
    width: 18;
    height: auto;
    align: center top;
    padding-left: 1;
}

#send-button {
    width: 1fr;
    margin-bottom: 1;
}

#send-hint {
    text-align: center;
    color: $text-muted;
}

#status-message {
    text-align: left;
    color: $text-muted;
    height: 1;
}


/* ========================================
   OVERLAYS
   ======================================== */
#overlay-container {
    width: 100%;
    height: 100%;
    background: $panel;
    border: round $primary;
    padding: 0;
    box-sizing: border-box;
}

#overlay-title {
    text-style: bold;
    background: $primary;
    color: $surface;
    padding: 1 2;
    dock: top;
    border-bottom: solid $primary;
}

#overlay-content {
    height: 1fr;
    padding: 1 2;
    background: $panel;
    overflow-y: auto;
}

#overlay-footer {
    text-style: dim;
    text-align: center;
    padding: 1 2;
    dock: bottom;
    background: $surface;
    border-top: solid $primary;
    color: $text-muted;
}

#tab-selector {
    text-align: center;
    padding: 1 2;
    text-style: bold;
    color: $text;
    background: $surface;
    border-bottom: solid $primary;
    dock: top;
}

#story-content {
    height: 1fr;
    color: $text;
}


/* ========================================
   FORM ELEMENTS
   ======================================== */
Button {
    margin: 0 1;
    background: $surface;
    color: $text;
    border: round $primary;
}

Button:hover {
    background: $primary;
    color: $surface;
    text-style: bold;
}

Button.primary {
    background: $accent;
    color: $surface;
    border: round $accent;
}

Button.primary:hover {
    background: $warning;
    color: $surface;
    text-style: bold;
}

Button:focus {
    text-style: bold;
    border: round $accent;
}

Button:disabled {
    background: $panel;
    color: $text-muted;
    text-style: dim;
}

Input {
    background: $surface;
    color: $text;
    border: round $primary;
}

Input:focus {
    border: round $accent;
    color: $text;
}

Switch {
    margin: 1 0;
}
    """


__all__ = [
    "PALETTE",
    "STYLES",
    "get_button_css",
    "get_input_css",
    "get_textarea_css",
    "get_select_css",
    "get_scrollbar_css",
    "get_header_css",
    "get_panel_css",
    "get_overlay_css",
    "get_app_css",
]
