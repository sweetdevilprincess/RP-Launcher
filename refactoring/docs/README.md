# TUI Integration Documentation

Complete documentation for integrating trigger and template editors into the RP Client TUI.

---

## Documentation Index

### 🚀 Start Here
**[START_HERE.md](START_HERE.md)** - Quick start guide for TUI integration work
- What you're working on
- 5-minute quick start
- Task overview and roadmap
- Code templates
- Success criteria

**Start with this if you're new to the integration work.**

---

### 📚 Core Documentation

#### [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
System architecture and design reference
- System architecture diagrams
- Directory structure
- Component hierarchy
- Data flow visualizations
- Message protocol
- State management

**Read this first to understand the system structure.**

#### [TUI_INTEGRATION_GUIDE.md](TUI_INTEGRATION_GUIDE.md)
Complete integration guide with detailed instructions
- Project background
- Current state and completed phases
- Mockup files reference
- Step-by-step integration tasks
- IPC communication guide
- Testing approach
- Design patterns and conventions
- Troubleshooting

**Use this as your complete reference during integration.**

#### [INTEGRATION_QUICK_REFERENCE.md](INTEGRATION_QUICK_REFERENCE.md)
Quick reference for common tasks and code patterns
- File locations
- Component extraction checklist
- IPC message quick reference
- Component pattern examples
- Testing commands
- Common patterns
- Color palette
- Debugging tips

**Keep this open while coding for quick lookups.**

---

## Documentation Reading Order

### For New Developers

1. **START_HERE.md** (15 min)
   - Get oriented
   - Understand the task
   - See what you'll build

2. **ARCHITECTURE_OVERVIEW.md** (30 min)
   - Learn system structure
   - Understand data flow
   - See component relationships

3. **INTEGRATION_QUICK_REFERENCE.md** (15 min)
   - Scan code patterns
   - Note file locations
   - Bookmark for later

4. **TUI_INTEGRATION_GUIDE.md** (as needed)
   - Deep dive into specifics
   - Reference during work
   - Troubleshooting guide

### For Quick Reference

- **Need a code snippet?** → INTEGRATION_QUICK_REFERENCE.md
- **Need to understand data flow?** → ARCHITECTURE_OVERVIEW.md
- **Need detailed steps?** → TUI_INTEGRATION_GUIDE.md
- **Need to get started?** → START_HERE.md

---

## Project Status

### Completed ✅

**Phase 1: Core Infrastructure**
- Socket-based IPC system (server, client, protocol)
- Refactored Bridge service with dependency injection
- Mock LLM client for testing mode
- **Tests**: 20/20 passing

**Phase 2: TUI Modular Architecture**
- Split TUI into modular components
- Implemented core widgets (ChatDisplay, ContextPanel, etc.)
- Updated TUI to use refactored services
- **Tests**: 15/15 passing

**Phase 3: Enhanced UI Components**
- Provider dropdown UI
- Enhanced trigger editor mockup (horizontal scrolling)
- Template editor mockup (three-panel layout)
- Testing mode toggle
- **Tests**: 25/25 passing

**Total Tests**: 60/60 passing ✅

### Current Phase 🔄

**Phase 4: Integration and Testing** (In Progress)
- Integrate trigger editor into main TUI
- Integrate template editor into main TUI
- Connect to Bridge via IPC
- Add Bridge handlers for triggers/templates
- End-to-end testing

### Pending 📋

**Phase 5: Documentation and Polish**
- User documentation
- Code comments
- Video demos (optional)

---

## Quick Start Commands

```bash
# Navigate to project
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"

# Run mockups
python scripts/run_trigger_editor_enhanced.py
python scripts/run_template_editor.py

# Run tests
pytest tests/ -v

# Start Bridge (test mode)
python -m src.application.bridge_service --test-mode

# Start TUI
python -m src.presentation.tui.app

# Dev mode with console
textual console  # Terminal 1
textual run --dev src/presentation/tui/app.py  # Terminal 2
```

---

## File Structure Reference

```
refactoring/
│
├── docs/                                    ← YOU ARE HERE
│   ├── README.md                           ← Documentation index
│   ├── START_HERE.md                       ← Quick start guide
│   ├── ARCHITECTURE_OVERVIEW.md            ← System architecture
│   ├── TUI_INTEGRATION_GUIDE.md            ← Complete guide
│   └── INTEGRATION_QUICK_REFERENCE.md      ← Quick reference
│
├── src/
│   ├── presentation/tui/
│   │   ├── app.py                          ← Main TUI app
│   │   ├── styles.py                       ← Color palette
│   │   └── components/
│   │       ├── trigger_editor_enhanced_mockup.py  ← Extract from
│   │       ├── template_editor_mockup.py          ← Extract from
│   │       ├── trigger_editor.py           ← Create this
│   │       └── template_editor.py          ← Create this
│   │
│   ├── application/
│   │   └── bridge_service.py               ← Add handlers
│   │
│   ├── infrastructure/ipc/
│   │   ├── ipc_protocol.py                 ← Add message types
│   │   ├── socket_client.py                ← TUI IPC client
│   │   └── socket_server.py                ← Bridge IPC server
│   │
│   └── domain/
│       ├── character.py
│       ├── llm_client.py
│       └── mock_llm_client.py
│
├── tests/                                   ← 60/60 passing
│   ├── test_ipc_protocol.py
│   ├── test_socket_client.py
│   ├── test_bridge_service.py
│   └── ...
│
└── scripts/
    ├── run_trigger_editor_enhanced.py
    └── run_template_editor.py
```

---

## Key Concepts

### Architecture
- **TUI**: Presentation layer (Textual framework)
- **Bridge**: Business logic layer
- **IPC**: Socket-based communication (JSON messages)
- **Domain**: Core entities and interfaces

### Communication Patterns
- **Internal (TUI)**: Textual messages between components
- **External (TUI ↔ Bridge)**: IPC messages over socket
- **State**: Reactive properties for UI updates

### Design Principles
- Separation of concerns
- Message-driven architecture
- Async-first
- Testability
- Modularity

---

## Integration Workflow

```
1. Extract Components
   ├─ Copy mockup file
   ├─ Remove sample data
   ├─ Remove standalone app
   └─ Update imports

2. Add IPC Integration
   ├─ Add load methods
   ├─ Add save methods
   ├─ Add error handling
   └─ Test with mock data

3. Integrate into Main TUI
   ├─ Import component
   ├─ Add to app layout
   ├─ Add keybindings
   └─ Add toggle actions

4. Update Bridge
   ├─ Add message types
   ├─ Add handlers
   ├─ Add persistence
   └─ Add validation

5. Test
   ├─ Unit tests
   ├─ Integration tests
   ├─ Manual E2E tests
   └─ Verify all 60+ tests pass
```

---

## Testing Strategy

### Test Pyramid

```
        ┌──────────────┐
        │     E2E      │  Manual testing
        │   (Manual)   │  Full workflows
        └──────────────┘
       ┌────────────────┐
       │  Integration   │  Automated
       │  (IPC Tests)   │  TUI ↔ Bridge
       └────────────────┘
    ┌──────────────────────┐
    │    Unit Tests        │  Automated (60 tests)
    │  (Components, IPC)   │  Individual units
    └──────────────────────┘
```

### Testing Commands

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_trigger_editor.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Manual testing
# Terminal 1: Bridge
python -m src.application.bridge_service --test-mode

# Terminal 2: TUI
python -m src.presentation.tui.app
```

---

## Documentation Maintenance

### When to Update

- **ARCHITECTURE_OVERVIEW.md**: When adding new components or changing data flow
- **TUI_INTEGRATION_GUIDE.md**: When adding new integration steps or patterns
- **INTEGRATION_QUICK_REFERENCE.md**: When adding new code snippets or commands
- **START_HERE.md**: When changing the integration workflow

### Documentation Standards

- Use code blocks with syntax highlighting
- Include visual diagrams where helpful
- Provide working code examples
- Keep quick reference concise
- Update file locations if structure changes

---

## Support

### Resources

- **Textual Documentation**: https://textual.textualize.io/
- **Textual Widget Guide**: https://textual.textualize.io/widgets/
- **Project Tests**: `tests/` directory
- **Example Components**: `src/presentation/tui/components/`

### Debugging

1. **Use Textual dev console**
   ```bash
   textual console
   textual run --dev src/presentation/tui/app.py
   ```

2. **Enable logging**
   ```python
   self.log("Debug message")
   self.log.error(f"Error: {error}")
   ```

3. **Check IPC communication**
   ```python
   # Add logging in socket_client.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Inspect component tree**
   ```python
   # In Textual console
   >>> app.query("TriggerEditor")
   >>> app.query_one("#trigger-list")
   ```

---

## Next Steps

**Ready to start integration?**

1. ✅ Read **START_HERE.md**
2. ✅ Review **ARCHITECTURE_OVERVIEW.md**
3. ✅ Skim **INTEGRATION_QUICK_REFERENCE.md**
4. → Begin trigger editor integration
5. → Follow checklist in **TUI_INTEGRATION_GUIDE.md**

**Need help?** Check the relevant documentation above or review existing code in `src/presentation/tui/components/`.

---

## Changelog

### 2025-10-21
- Created initial documentation suite
- Added START_HERE.md for quick onboarding
- Added ARCHITECTURE_OVERVIEW.md with diagrams
- Added TUI_INTEGRATION_GUIDE.md with detailed steps
- Added INTEGRATION_QUICK_REFERENCE.md for quick lookups
- Documented all 60 passing tests
- Documented completed Phases 1-3
- Outlined Phase 4 integration tasks

---

**For questions or clarifications, refer to the specific documentation files above.**

**Good luck with the integration! 🚀**
