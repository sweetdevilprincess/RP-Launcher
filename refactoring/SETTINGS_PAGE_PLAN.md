# Settings Page Implementation Plan & Status

**Date:** 2025-10-27
**Component:** `src/presentation/tui/components/settings_overlay.py`
**Status:** In Progress - Core structure complete, refinements ongoing

---

## 📋 Overview

The Settings Page is a full-screen overlay with side navigation, providing comprehensive configuration options for the RP Client TUI application.

### Design Pattern
- **Layout:** Side navigation (20% width) + Content area (80% width)
- **Navigation:** 9 sections accessible via left sidebar
- **Overlay Style:** Full-screen, respects header/footer (margins: top 3, bottom 2)
- **Scrolling:** Both sidebar and content areas independently scrollable

---

## 🎨 Original Design Concept

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ [Tabs: Chat | Entities | Branches | Modules | Settings] │  ← App Header (3 units)
├──────────┬──────────────────────────────────────────────┤
│          │  LLM Setup                        [💾 Save]  │  ← Section Header (4 units)
├──────────┼──────────────────────────────────────────────┤
│ 🤖 LLM   │                                              │
│ ⚡ Perf   │  Provider: [Anthropic Claude (SDK) ▼]       │
│ 🎨 Theme  │  Temperature: [━━━━━━●────] 70              │
│ 📁 Paths  │  Proxy: [Enable ☐]                          │
│ 🔧 Adv    │  ... (scrollable content)                   │
│ 🧪 Test   │                                              │
│ 🔄 Auto   │                                              │
│ 📊 Mods   │                                              │
│ 💾 Data   │                                              │
└──────────┴──────────────────────────────────────────────┘
│ Footer info                                             │  ← App Footer (2 units)
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Implemented Features

### Core Structure
- ✅ Full-screen overlay with proper layering (layer: overlay)
- ✅ Side navigation with 9 sections
- ✅ Content switcher for dynamic section loading
- ✅ Scrollable sidebar and content areas
- ✅ Header/footer margins (3 top, 2 bottom)
- ✅ Save button integration

### 9 Settings Sections

#### 1. 🤖 LLM Setup
**Status:** ✅ Complete
- Primary LLM provider selection (dropdown with SDK option)
- API key input (password masked)
- Model name input
- Temperature slider (0-100, converts to 0.0-1.0)
- Max tokens input
- Prompt caching toggle
- **Proxy configuration section:**
  - Enable proxy toggle
  - Proxy URL input
  - Username (optional)
  - Password (optional, masked)
- Secondary LLM configuration:
  - Enable toggle
  - Provider selection
  - API key
  - Model name
  - Temperature slider

#### 2. ⚡ Performance
**Status:** ✅ Complete (Basic)
- Enable streaming responses
- Enable caching
- Cache size configuration
- Request timeout

#### 3. 🎨 Appearance
**Status:** ✅ Complete (Basic)
- Theme selection dropdown
- Font size selection
- Show timestamps toggle

#### 4. 📁 Paths
**Status:** ✅ Complete (Basic)
- RPs root directory
- Templates directory
- Logs directory

#### 5. 🔧 Advanced
**Status:** ✅ Complete (Basic)
- Log level selection
- IPC Bridge host/port
- Enable debug mode toggle

#### 6. 🧪 Testing
**Status:** ✅ Complete (Basic)
- Enable testing mode toggle
- Mock response delay
- Response delay input

#### 7. 🔄 Automation
**Status:** ✅ Complete (Basic)
- Enable automation agents toggle
- Auto-generate preferences toggle
- Auto-generation frequency

#### 8. 📊 Modules
**Status:** ✅ Complete (Basic)
- Entity Manager toggle
- Session Management toggle
- Branch Management toggle

#### 9. 💾 Data
**Status:** ✅ Complete (Basic)
- Auto-backup toggle
- Backup frequency selection
- Backup Now button
- Export All Data button

---

## 🎨 User Customizations Applied

### Layout Adjustments
- **Sidebar width:** 15% → **20%** (more room for navigation)
- **Content width:** 85% → **80%** (adjusted accordingly)
- **Header height:** 3 → **4** units
- **Header alignment:** left middle → **right middle** (Save button alignment)

### Sizing Refinements
- **Sidebar elements:** 100% → **90%** width (better margins)
- **Content elements:** 100% → **95%** width (better readability)
- **Slider width:** 100% → **95%**
- **Slider label:** 100% → **90%** width
- **Input fields:** 100% → **95%** width
- **Select dropdowns:** 100% → **95%** width
- **Inline fields:** 100% → **95%** width
- **Settings sections:** 100% → **95%** width

### Removed Elements
- **Sidebar title:** "⚙️ Settings" Static removed from compose()
  - Navigation buttons now start immediately

---

## 🔧 Technical Implementation

### Component Structure
```
SettingsOverlay (Container)
├── Vertical (sidebar, 20% width, scrollable)
│   ├── Button (🤖 LLM Setup)
│   ├── Button (⚡ Performance)
│   ├── Button (🎨 Appearance)
│   ├── Button (📁 Paths)
│   ├── Button (🔧 Advanced)
│   ├── Button (🧪 Testing)
│   ├── Button (🔄 Automation)
│   ├── Button (📊 Modules)
│   └── Button (💾 Data)
└── Vertical (content, 80% width)
    ├── Horizontal (header, height: 4)
    │   ├── Static (title)
    │   └── Button (💾 Save)
    └── ContentSwitcher
        ├── ScrollableContainer (LLM section)
        ├── ScrollableContainer (Performance section)
        ├── ScrollableContainer (Appearance section)
        ├── ScrollableContainer (Paths section)
        ├── ScrollableContainer (Advanced section)
        ├── ScrollableContainer (Testing section)
        ├── ScrollableContainer (Automation section)
        ├── ScrollableContainer (Modules section)
        └── ScrollableContainer (Data section)
```

### Dependencies
- **textual-slider:** `pip install textual-slider` (for temperature sliders)
- **IPC Integration:** Uses `IPCMessageType.UPDATE_SETTINGS` for save operations

### Key CSS Classes
- `.section-title` - Section headers (colored, bold)
- `.section-divider` - Horizontal separators
- `.section-description` - Italic description text
- `.slider-label` - Container for slider with value display
- `.slider-value` - Current slider value (colored, right-aligned)
- `.inline-field` - Horizontal label + input layout

---

## 🐛 Issues Fixed

### Issue 1: Blank Page
**Problem:** Settings overlay displayed completely blank
**Cause:** Redundant `with Horizontal():` wrapper in compose()
**Fix:** Removed wrapper - Container already has `layout: horizontal` in CSS

### Issue 2: Header/Footer Covered
**Problem:** Overlay covered tabs and footer
**Cause:** 100% height without accounting for docked elements
**Fix:** Added `margin-top: 3` and `margin-bottom: 2`

### Issue 3: Crash on Launch
**Problem:** `TypeError: SettingsOverlay.__init__() got an unexpected keyword argument 'id'`
**Cause:** Duplicate import - `SettingsOverlay` imported from both `.components` and `.screens`
**Fix:** Removed duplicate import from `.screens` in `app.py`

### Issue 4: Rendering Artifacts
**Problem:** "Messed up pixels" in sidebar label and save button
**Cause:** Inconsistent heights and padding causing text overflow
**Fix:** Set fixed `height: 3` for all header elements, consistent padding

---

## 📝 Current State

### What Works
✅ All 9 sections accessible and navigable
✅ Temperature sliders functional (integer 0-100)
✅ Proxy configuration fully implemented
✅ SDK option in provider dropdown
✅ Scrolling in both sidebar and content
✅ Save button triggers IPC save operation
✅ Clean rendering without artifacts
✅ Proper margins respect header/footer
✅ Consistent styling with other overlays

### What Needs Work
⚠️ **IPC Integration:** Save operations need Bridge handler implementation
⚠️ **Load Settings:** Need to implement loading saved settings from Bridge
⚠️ **Validation:** Input validation for numeric fields (ports, sizes, etc.)
⚠️ **Temperature Conversion:** Slider uses 0-100 but needs to convert to 0.0-1.0 for APIs
⚠️ **Secondary LLM Conditional:** Fields should disable when secondary is off
⚠️ **Proxy Conditional:** Proxy fields should disable when proxy toggle is off
⚠️ **Testing Integration:** Testing mode toggle needs to actually switch to mock mode
⚠️ **Module Toggles:** Need to connect to actual module enable/disable logic
⚠️ **Backup Actions:** Backup/Export buttons need actual implementation
⚠️ **Form State Management:** Need to track dirty/unsaved state

---

## 🚀 Next Steps

### High Priority
1. **Implement IPC handlers in Bridge:**
   - `GET_SETTINGS` - Load current settings
   - `UPDATE_SETTINGS` - Save settings changes
   - `TEST_CONNECTION` - Test API keys

2. **Add form validation:**
   - Numeric inputs (ports, sizes, timeouts)
   - Required field checking (API keys if provider selected)
   - URL validation for proxy

3. **Conditional field enabling:**
   - Disable secondary LLM fields when toggle is off
   - Disable proxy fields when proxy toggle is off
   - Show/hide SDK-specific options

### Medium Priority
4. **Load settings on mount:**
   - Call `GET_SETTINGS` when overlay opens
   - Populate all fields with current values
   - Show loading state during fetch

5. **State management:**
   - Track unsaved changes
   - Warn before discarding changes
   - Show "saved" indicator after successful save

6. **Better UX:**
   - Add tooltips/help text for complex options
   - Keyboard navigation improvements
   - Tab order optimization

### Low Priority
7. **Advanced features:**
   - Settings presets (Creative, Balanced, Precise)
   - Import/Export settings as JSON
   - Reset to defaults button
   - Settings search/filter

---

## 📚 Related Files

### Implementation
- `src/presentation/tui/components/settings_overlay.py` - Main component
- `src/presentation/tui/components/__init__.py` - Export SettingsOverlay
- `src/presentation/tui/app.py` - Integration into main app

### Configuration
- `requirements.txt` - Added `textual-slider>=0.1.0`

### Bridge (Needs Implementation)
- `src/presentation/bridge/handlers/settings_handler.py` - To be created
- `src/infrastructure/ipc/ipc_protocol.py` - Add GET_SETTINGS, UPDATE_SETTINGS

---

## 🎯 Design Decisions

### Why Side Navigation?
- **Scalability:** Easy to add new sections without cluttering
- **Visibility:** Always see what sections are available
- **Context:** Current section clearly indicated
- **Efficiency:** One-click section switching

### Why Overlay vs Regular Page?
- **Consistency:** Matches Modules and Entity Manager patterns
- **Focus:** Settings are a configuration task, overlay provides focus
- **Return:** Easy to return to previous context after configuration

### Why Temperature as Slider?
- **Intuitive:** Visual representation of "creativity" scale
- **Common Pattern:** Many LLM UIs use sliders for temperature
- **Constraint:** Prevents invalid values (must be 0-100)

### Why 0-100 Scale for Temperature?
- **Integer Limitation:** textual-slider only supports integers
- **Conversion:** Easy to convert to 0.0-1.0 in save handler (value / 100)
- **User-Friendly:** Percentage-like scale is intuitive

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] All 9 sections load without errors
- [ ] Sidebar scrolls when many sections
- [ ] Content scrolls in each section
- [ ] Temperature sliders move and update value display
- [ ] Save button triggers save operation
- [ ] Switching sections maintains form state
- [ ] Navigation button highlights correctly
- [ ] Proxy fields appear/work
- [ ] Secondary LLM fields appear/work
- [ ] All dropdowns populate correctly
- [ ] All input fields accept text
- [ ] All toggles switch on/off
- [ ] Header and footer remain visible
- [ ] No rendering artifacts

### Integration Testing
- [ ] Settings persist after save
- [ ] Settings load on overlay open
- [ ] IPC communication works
- [ ] API key validation (if implemented)
- [ ] Settings affect application behavior
- [ ] Testing mode actually uses mocks

---

## 📖 Usage

### For Users
1. Click **⚙️ Settings** tab in main navigation
2. Use **sidebar buttons** to navigate sections
3. Configure settings in each section
4. Click **💾 Save** to persist changes
5. Click another tab to close settings

### For Developers
```python
# Import the component
from src.presentation.tui.components import SettingsOverlay

# Create instance
settings = SettingsOverlay(id="settings-overlay")

# Show/hide
settings.styles.display = "block"  # Show
settings.styles.display = "none"   # Hide

# Access via app
app.settings_overlay.styles.display = "block"
```

---

## 🔗 References

### Textual Documentation
- **Containers:** https://textual.textualize.io/guide/layout/
- **ContentSwitcher:** https://textual.textualize.io/widgets/content_switcher/
- **Input:** https://textual.textualize.io/widgets/input/
- **Select:** https://textual.textualize.io/widgets/select/
- **Switch:** https://textual.textualize.io/widgets/switch/
- **Slider:** https://github.com/TomJGooding/textual-slider

### Related Documentation
- `docs/CONFIGURATION_GUIDE.md` - Configuration system overview
- `docs/TRANSPORT_SYSTEM.md` - LLM provider integration
- `docs/LOGGING_CONVENTIONS.md` - Logging standards

---

## 📋 Detailed Section Enhancement Plan

This section outlines what needs to be added/changed for each settings section to make them fully functional.

### 🤖 LLM Setup - MOST COMPLETE
**Current State:** ~85% complete
**Priority:** High (core functionality)

#### What's Working
- ✅ Provider dropdown with SDK option
- ✅ API key inputs (password masked)
- ✅ Model name inputs
- ✅ Temperature sliders (0-100)
- ✅ Proxy configuration (all fields)
- ✅ Secondary LLM section

#### What Needs Implementation
1. **Provider-specific fields**
   - Show/hide fields based on provider selection
   - OpenRouter: Add model selector dropdown
   - Ollama: Add local model list
   - Google: Add project ID field

2. **Model dropdown population**
   - Fetch available models from each provider
   - Cache model lists
   - Add "Custom" option for manual entry

3. **API Key validation**
   - "Test Connection" button next to each API key
   - Visual feedback (✓/✗) on key validity
   - Error messages for invalid keys

4. **Conditional field disabling**
   - Disable API key when SDK mode selected
   - Disable secondary LLM fields when toggle is off
   - Disable proxy fields when proxy toggle is off

5. **Advanced LLM options**
   - Top-p slider
   - Frequency penalty slider
   - Presence penalty slider
   - Stop sequences input

#### Code Changes Needed
```python
def on_select_changed(self, event: Select.Changed):
    """Handle provider selection changes."""
    if event.select.id == "primary-provider":
        provider = event.value
        # Show/hide provider-specific fields
        self._update_provider_fields(provider)

def _update_provider_fields(self, provider: str):
    """Show/hide fields based on provider."""
    # Implementation needed
```

---

### ⚡ Performance - NEEDS EXPANSION
**Current State:** ~30% complete
**Priority:** Medium

#### What's Working
- ✅ Basic toggles (streaming, caching)
- ✅ Cache size input
- ✅ Request timeout input

#### What Needs Implementation
1. **Streaming settings**
   - Buffer size input
   - Update frequency slider
   - Show typing indicator toggle

2. **Caching details**
   - Cache TTL (time to live) input
   - "Clear Cache Now" button
   - Cache statistics display (current size, hit rate)

3. **Rate limiting**
   - Max requests per minute
   - Retry attempts input
   - Backoff strategy dropdown (Linear, Exponential)
   - "Respect API rate limits" toggle

4. **Connection pooling**
   - Max concurrent connections
   - Connection timeout
   - Keep-alive toggle

5. **Performance monitoring**
   - Enable performance logging toggle
   - Show response times toggle
   - Token usage tracking toggle

#### Code Example
```python
def _compose_performance_section(self) -> ComposeResult:
    # Add sections:
    # - Response Generation
    # - Caching & Memory
    # - Rate Limiting
    # - Connection Settings
    # - Monitoring
```

---

### 🎨 Appearance - NEEDS SIGNIFICANT WORK
**Current State:** ~25% complete
**Priority:** Low (nice to have)

#### What's Working
- ✅ Theme selector
- ✅ Font size selector
- ✅ Show timestamps toggle

#### What Needs Implementation
1. **Layout preferences**
   - Context panel width slider (20-40%)
   - Compact mode toggle
   - Show message separators toggle
   - Minimize whitespace toggle

2. **Chat display options**
   - Message style dropdown (Bubbles, Flat, Compact)
   - Avatar style dropdown (Icons, Text, None)
   - Max messages to display input
   - Auto-scroll toggle

3. **Syntax highlighting**
   - Enable code highlighting toggle
   - Render markdown toggle
   - Code theme selector

4. **Color customization**
   - Custom theme builder (advanced)
   - Accent color picker
   - Background color picker

5. **Accessibility**
   - High contrast mode
   - Larger text mode
   - Reduce motion toggle

#### Implementation Priority
1. Layout preferences (Medium priority)
2. Chat display (Low priority)
3. Syntax highlighting (Low priority)
4. Color customization (Very low - advanced feature)

---

### 📁 Paths - NEEDS VALIDATION & BROWSE
**Current State:** ~40% complete
**Priority:** Medium

#### What's Working
- ✅ Basic path inputs (RPs, templates, logs)

#### What Needs Implementation
1. **Additional paths**
   - Exports directory
   - Backups directory
   - User templates directory
   - Cache directory

2. **Browse buttons**
   - "Browse..." button next to each path
   - Directory picker dialog
   - Path validation (directory exists)
   - Create directory option

3. **File handling**
   - Default encoding dropdown
   - Line endings dropdown (Auto, LF, CRLF)
   - Auto-create directories toggle
   - Use relative paths toggle

4. **Path validation**
   - Check if paths exist
   - Check write permissions
   - Visual feedback (✓/✗)
   - Suggest fixes for invalid paths

5. **Quick actions**
   - "Open in Explorer/Finder" button
   - "Reset to Defaults" button
   - "Validate All Paths" button

#### Code Structure
```python
def _compose_paths_section(self) -> ComposeResult:
    # Group by category:
    # - RP Directories
    # - Output & Logs
    # - File Handling
    # Add browse buttons using Horizontal containers
```

---

### 🔧 Advanced - NEEDS IPC SETTINGS
**Current State:** ~35% complete
**Priority:** High (needed for bridge connection)

#### What's Working
- ✅ Log level selector
- ✅ IPC host/port inputs
- ✅ Debug mode toggle

#### What Needs Implementation
1. **System configuration**
   - Worker threads input
   - IPC timeout input
   - Enable performance monitoring toggle
   - Collect usage statistics toggle
   - Verbose logging toggle

2. **IPC & Networking**
   - Connection timeout input
   - Auto-reconnect toggle
   - Max reconnect attempts input
   - "Test Connection" button

3. **Developer options**
   - Show internal IDs toggle
   - Log all IPC messages toggle
   - Profile performance toggle
   - Export debug info button
   - Clear logs button
   - **Reset All Settings button** (with confirmation)

4. **Security**
   - Enable SSL/TLS toggle
   - Certificate path input
   - API request signing toggle

#### Critical Features
- **Test Connection button** - Must validate bridge connectivity
- **Reset All** - Should warn user and require confirmation

---

### 🧪 Testing - NEEDS MOCK INTEGRATION
**Current State:** ~20% complete
**Priority:** Medium (essential for development)

#### What's Working
- ✅ Enable testing mode toggle
- ✅ Mock response delay input

#### What Needs Implementation
1. **Mock behavior**
   - Response style dropdown (Realistic, Simple, Error-prone)
   - Randomize response times toggle
   - Simulate streaming toggle
   - Inject random errors toggle (with percentage slider)

2. **Test data management**
   - Load test RP button
   - Generate sample entities button
   - Load fixtures dropdown
   - Reset test data button

3. **Validation settings**
   - Validate entities on save toggle
   - Check template syntax toggle
   - Verify file structure toggle
   - "Run Full System Check" button

4. **Integration with testing mode**
   - Actually switch to MockClient when enabled
   - Show "TESTING MODE" banner in app
   - Different styling when in test mode

#### Code Changes
```python
def on_switch_changed(self, event: Switch.Changed):
    if event.switch.id == "enable-testing":
        # Need to actually switch IPC to use mock mode
        self.app.ipc_client.testing_mode = event.value
        # Show banner
        if event.value:
            self.app.notify("⚠️ TESTING MODE ENABLED", timeout=0)
```

---

### 🔄 Automation - NEEDS AGENT INTEGRATION
**Current State:** ~30% complete
**Priority:** High (core feature)

#### What's Working
- ✅ Enable agents toggle
- ✅ Auto-generate preferences toggle
- ✅ Generation frequency selector

#### What Needs Implementation
1. **Agent system configuration**
   - Default strategy dropdown (Smart trigger, Interval, Manual)
   - Fallback strategy dropdown
   - Max agents running input

2. **Trigger settings**
   - Evaluation mode dropdown (Semantic, Keyword, Pattern, State)
   - Enable specific trigger types (checkboxes)
   - Max evaluations per turn input
   - Trigger cooldown input

3. **Auto-generation options**
   - Auto-update summaries toggle
   - Auto-generate scene notes toggle
   - Generation threshold input
   - LLM provider dropdown (Primary/Secondary)

4. **Template management**
   - Active templates count display
   - "Manage Templates..." button → opens template editor
   - "Edit Triggers..." button → opens trigger editor

5. **Agent monitoring**
   - Show agent activity toggle
   - Log agent decisions toggle
   - Agent statistics display

#### Integration Requirements
- Must connect to actual agent system
- Need to load available agent strategies
- Need to save trigger configuration

---

### 📊 Modules - NEEDS ACTUAL MODULE SYSTEM
**Current State:** ~25% complete
**Priority:** High (core feature control)

#### What's Working
- ✅ Basic module toggles (3 modules)

#### What Needs Implementation
1. **Complete module list**
   - Entity Manager ✓
   - Session Management ✓
   - Template System
   - Trigger System
   - Branch Management ✓
   - Character Preferences
   - Story Genome
   - Scene Tracking
   - Advanced Analytics
   - Export System

2. **Module information**
   - Description for each module
   - Dependencies (e.g., "Requires Entity Manager")
   - "(Essential)" / "(Recommended)" / "(Optional)" labels
   - Resource usage indicator

3. **Module status**
   - Currently loaded modules
   - Module status indicator (✓ Running, ⚠️ Error, ○ Disabled)
   - Last loaded timestamp
   - "Reload Modules" button

4. **Extensions**
   - Installed extensions count
   - "Browse Extensions..." button
   - "Install from file..." button
   - Extension update checker

5. **Module configuration**
   - Click module name to configure
   - Per-module settings (opens modal)

#### Integration Requirements
- Connect to actual module system in Bridge
- Load module states from configuration
- Save module enable/disable state
- Handle module dependencies

---

### 💾 Data - NEEDS BACKUP SYSTEM
**Current State:** ~35% complete
**Priority:** Medium (important for safety)

#### What's Working
- ✅ Auto-backup toggle
- ✅ Backup frequency selector
- ✅ Backup/Export buttons

#### What Needs Implementation
1. **Session data display**
   - Current session info (turns, duration)
   - Total sessions count
   - Total turns count
   - "View History" button
   - "Export Session" button

2. **Backup configuration**
   - Backup location display
   - Last backup timestamp
   - Backup size display
   - Backup before major changes toggle
   - Daily backup time picker
   - "Manage Backups..." button → backup browser

3. **Backup actions**
   - "Backup Now" → actually create backup
   - Progress indicator during backup
   - Success/failure notification
   - "Restore..." button → restore picker

4. **Data export**
   - Export format dropdown (Markdown, JSON, ZIP)
   - Include/exclude checkboxes:
     - Characters
     - Locations
     - Items
     - Story genome
     - Chat history
     - Preferences
     - System data
     - Debug logs
   - "Export All..." → file picker
   - "Export Selected..." → selective export

5. **Storage management**
   - Total RP size display
   - Breakdown by type (entities, sessions, media)
   - "Cleanup Temp Files" button
   - "Optimize Storage" button
   - Disk space available display

#### Integration Requirements
- Implement backup service in Bridge
- File system operations
- Progress tracking for long operations
- Restore functionality with validation

---

## 🎯 Implementation Priority Matrix

### Must Have (P0) - Core Functionality
1. **LLM Setup:** Provider validation, conditional fields
2. **Advanced:** IPC connection testing
3. **Automation:** Agent system integration
4. **Modules:** Load/save actual module state

### Should Have (P1) - Important Features
5. **Performance:** Rate limiting, caching controls
6. **Paths:** Validation and browse buttons
7. **Testing:** Mock mode integration
8. **Data:** Backup/restore functionality

### Nice to Have (P2) - Enhancement
9. **Appearance:** Layout customization
10. **Performance:** Monitoring and statistics
11. **Data:** Advanced export options

### Future (P3) - Advanced Features
12. **Appearance:** Custom theme builder
13. **Paths:** Path history and suggestions
14. **Modules:** Extension marketplace

---

## 🛠️ Cross-Cutting Concerns

### Issues Affecting All Sections

#### 1. **Form Validation**
Every section needs:
- Input validation (types, ranges, formats)
- Visual feedback (red borders, error messages)
- Prevent invalid values from being saved

#### 2. **State Management**
Every section needs:
- Track if values changed (dirty state)
- Warn before discarding unsaved changes
- Show "saved" indicator after save

#### 3. **Loading State**
Every section needs:
- Load current values from Bridge on mount
- Show loading spinner while fetching
- Handle load failures gracefully

#### 4. **Help Text**
Every section needs:
- Tooltips on hover (where appropriate)
- Description text under complex options
- Link to documentation

#### 5. **Conditional Visibility**
Many sections need:
- Show/hide fields based on other settings
- Disable fields when not applicable
- Gray out dependent fields

---

## 📝 Implementation Guidelines

### Adding a New Field

1. **Add to `_compose_X_section()`:**
```python
yield Label("New Setting:")
yield Input(placeholder="default", id="new-setting")
```

2. **Add CSS if needed:**
```css
SettingsOverlay #new-setting {
    width: 95%;
    margin: 0 0 2 0;
}
```

3. **Add to save handler:**
```python
def _save_settings(self):
    settings["new_setting"] = self.query_one("#new-setting", Input).value
```

4. **Add to load handler:**
```python
def _load_settings(self):
    new_setting = self.query_one("#new-setting", Input)
    new_setting.value = self.settings.get("new_setting", "")
```

### Adding Conditional Logic

```python
def on_switch_changed(self, event: Switch.Changed):
    if event.switch.id == "enable-feature":
        # Get dependent fields
        field1 = self.query_one("#dependent-field-1", Input)
        field2 = self.query_one("#dependent-field-2", Select)

        # Enable/disable based on toggle
        field1.disabled = not event.value
        field2.disabled = not event.value
```

### Adding Validation

```python
def _validate_settings(self) -> bool:
    """Validate all settings before saving."""
    errors = []

    # Validate port number
    port = self.query_one("#bridge-port", Input).value
    try:
        port_num = int(port)
        if not (1024 <= port_num <= 65535):
            errors.append("Port must be between 1024-65535")
    except ValueError:
        errors.append("Port must be a number")

    # Show errors
    if errors:
        self.app.notify("\n".join(errors), severity="error")
        return False

    return True
```

---

## 🔗 Integration Points

### Bridge Service Requirements

Each section needs corresponding handlers in Bridge:

```python
# src/presentation/bridge/handlers/settings_handler.py

class SettingsHandler:
    def handle_get_settings(self) -> dict:
        """Load all settings from config."""
        # Return settings dict

    def handle_update_settings(self, settings: dict) -> bool:
        """Save settings to config."""
        # Validate and save

    def handle_test_connection(self, api_key: str, provider: str) -> bool:
        """Test API key validity."""
        # Make test request

    def handle_get_available_models(self, provider: str) -> list:
        """Get list of models for provider."""
        # Query provider API
```

### Configuration File Structure

```json
{
  "version": "2.0.0",
  "llm": {
    "primary": {
      "provider": "claude_api_client",
      "api_key": "sk-...",
      "model": "claude-3-5-sonnet-20241022",
      "temperature": 0.7,
      "max_tokens": 4096,
      "prompt_caching": true
    },
    "secondary": {
      "enabled": false,
      "provider": "openai_client",
      "api_key": "",
      "model": "gpt-4o",
      "temperature": 0.3
    },
    "proxy": {
      "enabled": false,
      "url": "",
      "username": "",
      "password": ""
    }
  },
  "performance": {
    "streaming": true,
    "caching": true,
    "cache_size_mb": 100,
    "request_timeout": 30
  },
  "appearance": {
    "theme": "textual-dark",
    "font_size": "medium",
    "show_timestamps": true
  },
  "paths": {
    "rps_root": "./RPs",
    "templates": "./templates",
    "logs": "./logs"
  },
  "advanced": {
    "log_level": "INFO",
    "bridge_host": "127.0.0.1",
    "bridge_port": 5555,
    "debug_mode": false
  },
  "testing": {
    "enabled": false,
    "mock_delay_ms": 500
  },
  "automation": {
    "agents_enabled": true,
    "auto_generate_prefs": true,
    "generation_frequency": 10
  },
  "modules": {
    "entity_manager": true,
    "session_management": true,
    "branch_management": true
  },
  "data": {
    "auto_backup": true,
    "backup_frequency": "daily"
  }
}
```

---

**Last Updated:** 2025-10-27
**Version:** 2.0
**Status:** Core implementation complete, detailed enhancement plan added
