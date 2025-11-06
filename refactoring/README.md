# RP Launcher - Refactored Codebase

**Version:** 2.0.0
**Status:** 91% Complete (10 of 11 workstreams)
**Test Coverage:** 376+ tests passing
**Last Updated:** 2025-10-21

---

## Overview

This is the refactored version of RP Launcher, built with a clean, modular architecture emphasizing testability, type safety, and maintainability. The refactoring replaces monolithic legacy components with layered, protocol-based services.

### Key Improvements

- ✅ **Layered Architecture**: Clear separation between Domain, Application, and Infrastructure
- ✅ **Type Safety**: Comprehensive type hints with mypy validation
- ✅ **Test Coverage**: 376+ tests with 70%+ coverage minimum
- ✅ **Dependency Injection**: All services accept dependencies via constructor
- ✅ **Protocol-Based**: Easy to extend and mock for testing
- ✅ **Multi-Provider LLM Support**: Works with Claude, OpenAI, OpenRouter, DeepSeek
- ✅ **Modern Tooling**: Ruff, Black, Mypy, Pytest configured

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip or conda for package management

### Installation

```bash
# Navigate to refactoring directory
cd refactoring/

# Install development dependencies
pip install -r requirements-dev.txt

# Run all checks
./scripts/check-all.sh  # Linux/macOS
scripts\check-all.bat   # Windows
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# With coverage
./scripts/test.sh  # Linux/macOS
scripts\test.bat   # Windows

# Specific module
python -m pytest tests/domain/entities/
```

---

## Architecture

### Layered Design

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│         (CLI, TUI, Future Web)          │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        Application Layer                │
│      (Automation, Orchestration)        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│          Domain Layer                   │
│       (Entities, Sessions)              │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Infrastructure Layer               │
│   (Config, Transports, Files, LLM)      │
└─────────────────────────────────────────┘
```

### Directory Structure

```
refactoring/
├── src/
│   ├── automation/          # Application layer: Automation services
│   │   ├── agents/          # Agent strategies and coordination
│   │   ├── contracts/       # Automation contexts and results
│   │   ├── services/        # Core automation services
│   │   ├── templates/       # Template management
│   │   ├── triggers/        # Trigger evaluation
│   │   └── factory.py       # Service factory
│   ├── domain/              # Domain layer: Business logic
│   │   ├── entities/        # Entity management (characters, locations, etc.)
│   │   └── sessions/        # Session state management
│   ├── infrastructure/      # Infrastructure layer: Technical capabilities
│   │   ├── config/          # Configuration loading and validation
│   │   ├── files/           # File operations and access
│   │   ├── llm/             # LLM client implementations
│   │   ├── retry/           # Retry logic
│   │   └── transports/      # HTTP transport abstraction
│   └── shared/              # Cross-cutting concerns
│       ├── interfaces/      # Shared protocols
│       ├── logging.py       # Logging utilities
│       └── models.py        # Shared enums and types
├── tests/                   # Test suite (376+ tests)
│   ├── automation/          # Automation layer tests
│   ├── domain/              # Domain layer tests
│   ├── infrastructure/      # Infrastructure layer tests
│   └── conftest.py          # Shared test fixtures
├── docs/                    # Documentation
│   ├── architecture/        # Architecture documentation
│   ├── entities/            # Entity domain guide
│   ├── CHANGELOG.md         # Change log
│   ├── CONFIGURATION_GUIDE.md  # Configuration guide
│   ├── CONTRIBUTING.md      # Contribution guidelines
│   ├── ENTITY_MANAGER_MIGRATION.md  # Entity migration guide
│   ├── AUTOMATION_MIGRATION.md  # Automation migration guide
│   └── TOOLING.md           # Development tooling guide
├── scripts/                 # Development scripts
│   ├── check-all.{sh,bat}   # Run all checks
│   ├── lint.{sh,bat}        # Lint with ruff
│   ├── format.{sh,bat}      # Format with black
│   ├── typecheck.{sh,bat}   # Type check with mypy
│   └── test.{sh,bat}        # Run tests with coverage
├── pyproject.toml           # Tool configuration
└── requirements-dev.txt     # Development dependencies
```

---

## Workstream Status

| Workstream | Description | Status | Tests |
|------------|-------------|--------|-------|
| A | Architecture & Boundaries | ✅ Complete | - |
| B | Session State Management | ✅ Complete | - |
| C | Entity Domain | ✅ Complete | 78 |
| D | Automation Pipeline | ✅ Complete | 52 |
| E | File Access Service | ✅ Complete | 35 |
| F | Triggers & Templates | ✅ Complete | 80 |
| G | Session Management Testing | ✅ Complete | 39 |
| H | Agent System | ✅ Complete | 24 |
| I | Clients & Transport | ✅ Complete | 42 |
| J | Configuration & Defaults | ✅ Complete | 26 |
| K | Testing & Tooling | ✅ Complete | - |
| L | Documentation & Change Management | ⏳ In Progress | - |

**Total:** 376+ tests passing across all workstreams

---

## Key Features

### 1. Entity Domain (Workstream C)

Modular entity management with multi-provider preference generation.

**Components:**
- `EntityService`: Main orchestration service
- `EntityRepository`: Storage abstraction (JSON-based)
- `EntityParser`: Validation and parsing
- `PreferenceGenerator`: LLM-based preference generation

**Learn More:** [docs/entities/README.md](docs/entities/README.md)

### 2. Automation Pipeline (Workstream D)

Clean automation orchestration with modular prompt building.

**Components:**
- `AutomationService`: Main automation orchestrator
- `AgentRunner`: Agent execution and coordination
- `PromptBuilder`: Modular prompt assembly
- `FileAccessService`: Tiered file loading

**Learn More:** [docs/AUTOMATION_MIGRATION.md](docs/AUTOMATION_MIGRATION.md)

### 3. Trigger System (Workstream F)

Extensible trigger evaluation system.

**Trigger Types:**
- Interval triggers (every N turns)
- Pattern triggers (regex matching)
- State triggers (session state-based)
- Composite triggers (combine multiple)

**Extension Guide:** [docs/EXTENDING_TRIGGERS.md](docs/EXTENDING_TRIGGERS.md)

### 4. Template System (Workstream F)

Template-based narrative guidance.

**Modes:**
- `casual`: Conversational tone
- `dramatic`: High-stakes narrative
- `poetic`: Artistic language
- `technical`: Precise descriptions

**Extension Guide:** [docs/EXTENDING_TEMPLATES.md](docs/EXTENDING_TEMPLATES.md)

### 5. Multi-Provider LLM Support (Workstream I)

Unified client interface for multiple LLM providers.

**Supported Providers:**
- Anthropic Claude (API & SDK)
- OpenAI (GPT-4, GPT-3.5)
- OpenRouter (multi-model gateway)
- DeepSeek

**Transport Layer:** Abstracted HTTP client for easy testing and mocking

**Learn More:** [docs/TRANSPORT_SYSTEM.md](docs/TRANSPORT_SYSTEM.md)

### 6. Configuration System (Workstream J)

4-layer configuration with comprehensive validation.

**Precedence (highest to lowest):**
1. Environment variables (`ANTHROPIC_API_KEY`, etc.)
2. `config.json`
3. `.env` file
4. `defaults.py` (built-in defaults)

**Features:**
- Deep merge with precedence
- Type validation via TypedDict schemas
- Unknown field warnings
- Directory structure validation

**Learn More:** [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md)

### 7. Development Tooling (Workstream K)

Modern Python tooling for quality and consistency.

**Tools:**
- **Ruff**: Fast linting (10-100x faster than flake8)
- **Black**: Code formatting (100-char lines)
- **Mypy**: Static type checking
- **Pytest**: Test framework with fixtures
- **Coverage**: Branch coverage tracking (70% minimum)

**Scripts:**
- `check-all`: Run all checks in one command
- `lint`: Ruff linting with auto-fix
- `format`: Black formatting
- `typecheck`: Mypy type checking
- `test`: Pytest with coverage

**Learn More:** [docs/TOOLING.md](docs/TOOLING.md)

---

## Documentation

### For Users

- **[CHANGELOG.md](docs/CHANGELOG.md)**: What's new and changed
- **[CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md)**: Configuration system guide
- **[Entity Domain Guide](docs/entities/README.md)**: Entity management documentation

### For Developers

- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)**: Contribution guidelines and coding standards
- **[TOOLING.md](docs/TOOLING.md)**: Development tooling guide
- **[Architecture Overview](docs/architecture/README.md)**: Layered architecture and dependency rules

### For Migration

- **[ENTITY_MANAGER_MIGRATION.md](docs/ENTITY_MANAGER_MIGRATION.md)**: Migrating from legacy entity_manager.py
- **[AUTOMATION_MIGRATION.md](docs/AUTOMATION_MIGRATION.md)**: Migrating from legacy automation

### Extension Guides

- **[EXTENDING_TRIGGERS.md](docs/EXTENDING_TRIGGERS.md)**: Adding custom triggers
- **[EXTENDING_TEMPLATES.md](docs/EXTENDING_TEMPLATES.md)**: Adding custom templates
- **[TRANSPORT_SYSTEM.md](docs/TRANSPORT_SYSTEM.md)**: Adding new LLM providers

---

## Development Workflow

### Before Starting Work

```bash
# Update from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Run all checks to ensure clean start
./scripts/check-all.sh
```

### During Development

```bash
# Format code
./scripts/format.sh

# Fix linting issues
./scripts/lint.sh --fix

# Run tests
./scripts/test.sh

# Commit changes
git add <files>
git commit -m "feat: add feature description"
```

### Before Committing

```bash
# Run all checks
./scripts/check-all.sh

# Should see:
# [PASS] Ruff linting passed
# [PASS] Code formatting is correct
# [PASS] Type checking passed
# [PASS] All tests passed
```

---

## Testing

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific module
python -m pytest tests/domain/entities/

# With coverage
python -m pytest tests/ --cov=src --cov-report=html

# Markers
python -m pytest -m unit         # Only unit tests
python -m pytest -m integration  # Only integration tests
python -m pytest -m "not slow"   # Skip slow tests
```

### Test Organization

```
tests/
├── automation/          # Automation layer tests
│   ├── triggers/        # Trigger system tests (42)
│   ├── templates/       # Template system tests (38)
│   ├── agents/          # Agent system tests (24)
│   └── services/        # Service tests (70+)
├── domain/              # Domain layer tests
│   ├── entities/        # Entity tests (78)
│   └── sessions/        # Session tests (39)
├── infrastructure/      # Infrastructure layer tests
│   ├── config/          # Config tests (26)
│   ├── llm/             # LLM client tests (42)
│   └── transports/      # Transport tests
└── conftest.py          # Shared fixtures
```

### Available Fixtures

See `tests/conftest.py` for comprehensive fixtures:
- `temp_rp_dir`: Temporary RP directory with structure
- `character_factory`: Create test characters
- `location_factory`: Create test locations
- `minimal_config` / `full_config`: Configuration dicts
- Auto-markers: `unit`, `integration`, `smoke`, `slow`

---

## Configuration

### Minimal Configuration

Create `config.json` in your RP directory:

```json
{
  "version": "2.0.0",
  "system": {
    "log_level": "INFO"
  },
  "modules": {
    "claude_api_client": {
      "enabled": true,
      "config": {
        "api_key": "${ANTHROPIC_API_KEY}",
        "model": "claude-3-5-sonnet-20241022"
      }
    }
  }
}
```

### Environment Variables

Set API keys via environment variables:

```bash
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"  # Optional
export RP_SYSTEM_LOG_LEVEL="DEBUG"     # Optional
```

### Configuration Precedence

1. **ENV variables** (highest) → `ANTHROPIC_API_KEY`
2. **config.json** → `modules.claude_api_client.config.api_key`
3. **.env file** → `ANTHROPIC_API_KEY=...`
4. **defaults.py** (lowest) → Built-in defaults

See [CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) for details.

---

## Code Quality

### Standards

- **Line Length**: 100 characters
- **Formatting**: Black (enforced)
- **Linting**: Ruff (enforced)
- **Type Hints**: Required for all new code
- **Docstrings**: Google-style, required for public APIs
- **Test Coverage**: 70% minimum, 90%+ for new code

### Running Quality Checks

```bash
# All checks
./scripts/check-all.sh

# Individual checks
./scripts/lint.sh       # Ruff linting
./scripts/format.sh     # Black formatting
./scripts/typecheck.sh  # Mypy type checking
./scripts/test.sh       # Pytest with coverage
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:

- Code of conduct
- Development workflow
- Coding standards
- Testing requirements
- Pull request process
- Documentation standards

### Quick Contribution Checklist

- [ ] All tests pass (`./scripts/test.sh`)
- [ ] Code formatted (`./scripts/format.sh`)
- [ ] No linting errors (`./scripts/lint.sh`)
- [ ] Type checking passes (`./scripts/typecheck.sh`)
- [ ] Documentation updated (if needed)
- [ ] Tests added for new functionality

---

## Performance

### Optimization Features

- **Tiered File Loading**: Load only necessary files (50-70% I/O reduction)
- **Lazy Entity Loading**: Entities loaded on-demand
- **Template Caching**: Parsed templates cached
- **Transport Pooling**: HTTP connection reuse

### Benchmarks (Future)

Performance benchmarking suite planned for future workstream.

---

## Troubleshooting

### Common Issues

**Import errors:**
```python
# Ensure you're in refactoring/ directory
cd refactoring/
python -m pytest tests/
```

**Config not found:**
```bash
# Check config.json exists
ls config/config.json

# Or create minimal config
echo '{"version":"2.0.0"}' > config/config.json
```

**Tests failing:**
```bash
# Run with verbose output
python -m pytest tests/ -vv

# Run specific failing test
python -m pytest tests/path/to/test_file.py::test_function -vv
```

### Getting Help

1. Check relevant documentation in `docs/`
2. Review test examples in `tests/`
3. See migration guides for legacy → refactored mappings
4. Check workstream completion docs for details

---

## License

[Your License Here]

---

## Credits

Developed as part of the RP Launcher refactoring effort.

**Key Technologies:**
- Python 3.10+
- Anthropic Claude API
- OpenAI API
- Ruff, Black, Mypy, Pytest

---

**Status:** 91% Complete (10 of 11 workstreams)
**Next:** Workstream L (Documentation & Change Management)
**Last Updated:** 2025-10-21
**Version:** 2.0.0
