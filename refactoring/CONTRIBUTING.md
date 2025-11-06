# Contributing to RP Launcher Refactored

Thank you for your interest in contributing to RP Launcher! This guide explains our architecture, coding standards, and development workflow.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Module Boundaries](#module-boundaries)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation Standards](#documentation-standards)

---

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Help others learn and grow
- Keep discussions professional

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip or conda for package management

### Setup Development Environment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rp-launcher/refactoring
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Verify installation**:
   ```bash
   # Run all checks
   scripts/check-all.bat  # Windows
   ./scripts/check-all.sh  # Linux/macOS
   ```

4. **Run tests**:
   ```bash
   pytest tests/
   ```

---

## Architecture Overview

RP Launcher follows a **layered architecture** with clear separation of concerns:

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

### Key Principles

1. **Dependencies flow downward** - Upper layers depend on lower layers, never the reverse
2. **Domain is pure** - Domain layer has no infrastructure dependencies
3. **Dependency injection** - Services accept dependencies via constructor
4. **Protocol-based interfaces** - Use protocols for flexibility and testing

---

## Module Boundaries

### Domain Layer (`src/domain/`)

**Purpose**: Core business logic, entities, and domain services

**Rules**:
- ✅ **CAN** depend on: Nothing (pure domain logic)
- ❌ **CANNOT** depend on: Infrastructure, application, presentation

**Modules**:
- `entities/` - Character, location, organization, item entities
- `sessions/` - Session state, checkpoints, metadata

**Example**:
```python
# Good: Pure domain logic
from dataclasses import dataclass

@dataclass(frozen=True)
class CharacterEntity:
    name: str
    basics: dict
    personality: dict
```

```python
# Bad: Domain depending on infrastructure
from src.infrastructure.config import ConfigLoader  # ❌ NO!

class CharacterEntity:
    def __init__(self):
        self.config = ConfigLoader()  # ❌ Domain shouldn't know about config loading
```

### Application Layer (`src/automation/`)

**Purpose**: Orchestration, workflows, use cases

**Rules**:
- ✅ **CAN** depend on: Domain, infrastructure (via DI)
- ❌ **CANNOT** depend on: Presentation

**Modules**:
- `services/` - Automation service, agent runner, prompt builder
- `agents/` - Agent strategies (background, immediate, fallback)
- `triggers/` - Trigger evaluation and coordination
- `templates/` - Template loading and management

**Example**:
```python
# Good: Application depends on domain and infrastructure via DI
from src.domain.entities import EntityService
from src.infrastructure.llm import LLMClient

class AutomationService:
    def __init__(self, entity_service: EntityService, llm_client: LLMClient):
        self._entities = entity_service
        self._llm = llm_client
```

### Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Technical capabilities, external integrations

**Rules**:
- ✅ **CAN** depend on: Domain (for implementing repository patterns)
- ❌ **CANNOT** depend on: Application, presentation

**Modules**:
- `config/` - Configuration loading and validation
- `transports/` - HTTP transport abstraction
- `llm/` - LLM client implementations
- `files/` - File operations, stores, loaders
- `retry/` - Retry logic for transient failures

**Example**:
```python
# Good: Infrastructure implementing domain protocol
from typing import Protocol
from src.domain.entities import CharacterEntity

class EntityRepository(Protocol):
    def get_character(self, name: str) -> CharacterEntity: ...

class FixtureEntityRepository:
    """Infrastructure implementation of domain protocol."""
    def get_character(self, name: str) -> CharacterEntity:
        # Load from file system
        ...
```

### Shared Layer (`src/shared/`)

**Purpose**: Cross-cutting concerns, utilities

**Rules**:
- ✅ **CAN** be used by: All layers
- ❌ **CANNOT** depend on: Application, infrastructure (only domain types)

**Modules**:
- `interfaces/` - Shared protocols
- `models.py` - Shared enums and basic types
- `logging.py` - Logging utilities

---

## Development Workflow

### 1. Before Starting Work

```bash
# Update from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Run all checks to ensure clean starting point
./scripts/check-all.sh
```

### 2. During Development

**Make small, focused commits**:
```bash
# After making changes
./scripts/format.sh      # Format code
./scripts/lint.sh --fix  # Fix linting issues
./scripts/test.sh        # Run tests

git add <files>
git commit -m "feat: add character preference caching"
```

**Commit message format**:
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `chore:` - Build/tooling changes

### 3. Before Committing

**Run all checks**:
```bash
./scripts/check-all.sh
```

This runs:
- Ruff linting
- Black formatting check
- Mypy type checking
- Pytest with coverage

All checks must pass before committing.

### 4. Push and Create PR

```bash
# Push to your branch
git push origin feature/your-feature-name

# Create pull request via GitHub/GitLab
```

---

## Coding Standards

### Python Style

We follow **PEP 8** with some modifications:

**Line Length**: 100 characters (not 79)

**Formatting**: Enforced by Black
```bash
# Format code
./scripts/format.sh
```

**Linting**: Enforced by Ruff
```bash
# Check linting
./scripts/lint.sh

# Auto-fix issues
./scripts/lint.sh --fix
```

### Type Hints

**Required for all new code**:

```python
# Good: Fully typed
def load_character(name: str, repository: EntityRepository) -> CharacterEntity:
    """Load character from repository.

    Args:
        name: Character name
        repository: Entity repository

    Returns:
        Character entity

    Raises:
        ValueError: If character not found
    """
    return repository.get_character(name)
```

```python
# Bad: No type hints
def load_character(name, repository):  # ❌ Missing types
    return repository.get_character(name)
```

**Use type aliases for complex types**:
```python
from typing import Dict, List, Any

ConfigDict = Dict[str, Any]
EntityList = List[CharacterEntity]

def process_config(config: ConfigDict) -> EntityList:
    ...
```

### Docstrings

**Required for all public functions/classes**:

```python
def calculate_preference(entity_a: str, entity_b: str, context: Dict[str, Any]) -> float:
    """Calculate relationship preference between two entities.

    Uses personality traits and historical interactions to determine
    how entity_a feels about entity_b.

    Args:
        entity_a: Name of first entity
        entity_b: Name of second entity
        context: Additional context (interactions, setting, etc.)

    Returns:
        Preference score from -1.0 (hostile) to 1.0 (friendly)

    Raises:
        ValueError: If either entity name is invalid
        KeyError: If required context keys are missing

    Example:
        >>> score = calculate_preference("Alice", "Bob", {"setting": "tavern"})
        >>> assert -1.0 <= score <= 1.0
    """
    ...
```

**Format**: Google-style docstrings

**Required sections**:
- Description (first line + optional details)
- `Args:` - All parameters
- `Returns:` - Return value and type
- `Raises:` - Exceptions that can be raised
- `Example:` (optional but encouraged)

### Dependency Injection

**Always use dependency injection**:

```python
# Good: Dependencies injected
class PreferenceGenerator:
    def __init__(self, llm_client: LLMClient, logger: LoggingService):
        self._client = llm_client
        self._logger = logger

    def generate(self, entity: EntityCard) -> PreferenceResult:
        # Use injected dependencies
        ...
```

```python
# Bad: Hard-coded dependencies
class PreferenceGenerator:
    def __init__(self):
        self._client = ClaudeAPIClient("hardcoded-key")  # ❌ Hard to test
        self._logger = print  # ❌ Can't control output

    def generate(self, entity: EntityCard) -> PreferenceResult:
        ...
```

### Immutability

**Prefer immutable data structures**:

```python
# Good: Frozen dataclass (immutable)
from dataclasses import dataclass

@dataclass(frozen=True)
class CharacterEntity:
    name: str
    personality: dict
```

```python
# Bad: Mutable class
class CharacterEntity:
    def __init__(self):
        self.name = ""  # ❌ Can be changed after creation
        self.personality = {}
```

### Error Handling

**Be specific with exceptions**:

```python
# Good: Specific exceptions
def load_config(path: Path) -> ConfigDict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
```

```python
# Bad: Generic exceptions
def load_config(path: Path) -> ConfigDict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:  # ❌ Too broad
        return {}  # ❌ Silently fails
```

---

## Testing Requirements

### Test Coverage

**Minimum coverage**: 70% (enforced)

**Target coverage for new code**: 90%+

Check coverage:
```bash
./scripts/test.sh
# Opens htmlcov/index.html
```

### Test Structure

**Organize by type**:
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Tests with multiple components
└── smoke/          # End-to-end sanity tests
```

**Automatic markers** (applied by conftest.py):
- `unit` - Tests in unit/ directory
- `integration` - Tests in integration/ directory
- `smoke` - Tests with "smoke" in name
- `slow` - Manual marker for slow tests

### Writing Tests

**Use fixtures from conftest.py**:

```python
def test_config_loading(temp_rp_with_config):
    """Test configuration loading with default config."""
    from src.infrastructure.config import ConfigLoader

    loader = ConfigLoader(temp_rp_with_config)
    config = loader.load()

    assert config["version"] == "2.0.0"
    assert loader.validate()
```

**Use factories for test data**:

```python
def test_character_creation(character_factory):
    """Test character entity creation."""
    alice = character_factory("Alice", age="30")

    assert alice["name"] == "Alice"
    assert alice["basics"]["age"] == "30"
```

**Test edge cases**:

```python
def test_empty_input():
    """Test handling of empty input."""
    ...

def test_invalid_input():
    """Test handling of invalid input."""
    with pytest.raises(ValueError, match="Invalid input"):
        ...

def test_boundary_conditions():
    """Test boundary values."""
    ...
```

### Test Naming

```python
# Good: Descriptive test names
def test_load_config_creates_default_if_missing():
    ...

def test_validate_raises_error_for_invalid_log_level():
    ...

# Bad: Vague test names
def test_config():  # ❌ What about config?
    ...

def test_1():  # ❌ No description
    ...
```

---

## Pull Request Process

### 1. Before Creating PR

- [ ] All tests pass locally
- [ ] Code coverage meets minimum (70%)
- [ ] Code is formatted (black)
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated (if needed)

**Run all checks**:
```bash
./scripts/check-all.sh
```

### 2. PR Description

Use this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation update
- [ ] Test improvement

## Changes Made
- Specific change 1
- Specific change 2

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### 3. Review Process

- At least one approval required
- All CI checks must pass
- Address all review comments
- Keep PR scope focused (< 500 lines if possible)

### 4. Merge

- **Squash and merge** for feature branches
- **Rebase and merge** for hotfixes
- Delete branch after merge

---

## Documentation Standards

### Code Documentation

**Every public function/class needs docstrings**:
- Description
- Args
- Returns
- Raises
- Example (when helpful)

### README Files

**Each major module should have a README**:

```
src/domain/entities/README.md
src/automation/README.md
src/infrastructure/config/README.md
```

**Contents**:
- Purpose of the module
- Key components
- Usage examples
- Architecture diagrams (if complex)

### Architectural Documentation

**Update when changing architecture**:

- `docs/architecture/README.md` - Overall architecture
- `docs/architecture/workstream_*.md` - Workstream plans
- `CHANGELOG.md` - Track changes

### Migration Guides

**Create when deprecating features**:

- Document what's changing
- Provide migration path
- Show before/after code examples
- Set timeline for deprecation

---

## Module-Specific Guidelines

### Adding New Entity Types

1. **Define dataclass** in `src/domain/entities/models.py`:
   ```python
   @dataclass(frozen=True)
   class NewEntityType:
       name: str
       field1: dict
       field2: list
   ```

2. **Add parser** in `src/domain/entities/entity_parser.py`:
   ```python
   def parse_new_entity(data: Dict[str, Any]) -> NewEntityType:
       ...
   ```

3. **Add repository methods** in `src/domain/entities/entity_repository.py`:
   ```python
   def get_new_entity(self, name: str) -> NewEntityType:
       ...

   def save_new_entity(self, entity: NewEntityType) -> None:
       ...
   ```

4. **Add tests** for all new functionality

5. **Update documentation**

### Adding New LLM Provider

See `docs/TRANSPORT_SYSTEM.md` for detailed guide.

**Summary**:
1. Implement LLMClient protocol
2. Use Transport abstraction for HTTP
3. Add to provider registry
4. Add tests with FakeTransport
5. Document configuration

### Adding New Trigger Type

See `docs/EXTENDING_TRIGGERS.md` for detailed guide.

**Summary**:
1. Implement TriggerEvaluator protocol
2. Register in TriggerRegistry
3. Add pattern file format
4. Add comprehensive tests
5. Document usage

### Adding New Template Mode

See `docs/EXTENDING_TEMPLATES.md` for detailed guide.

**Summary**:
1. Add mode to NarrativeTemplateManager
2. Create template JSON files
3. Add tests for template loading
4. Document template structure

---

## Common Patterns

### Configuration Access

```python
# Good: Inject ConfigLoader
class MyService:
    def __init__(self, config_loader: ConfigLoader):
        self._config = config_loader.load()

# Bad: Direct import
class MyService:
    def __init__(self):
        self._config = json.load(open("config.json"))  # ❌ Hard to test
```

### Logging

```python
# Good: Inject logger
class MyService:
    def __init__(self, logger: LoggingService):
        self._logger = logger

    def do_something(self):
        self._logger.info("Doing something")

# Bad: Direct print
class MyService:
    def do_something(self):
        print("Doing something")  # ❌ Can't control output
```

### Repository Pattern

```python
# Good: Protocol-based repository
from typing import Protocol

class EntityRepository(Protocol):
    def get_character(self, name: str) -> CharacterEntity: ...

class FixtureEntityRepository:
    def get_character(self, name: str) -> CharacterEntity:
        # Implementation
        ...

# Usage with DI
class EntityService:
    def __init__(self, repository: EntityRepository):  # Accepts any implementation
        self._repo = repository
```

---

## Questions?

- Check existing documentation in `docs/`
- Look at similar code for examples
- Ask in team discussions
- Open an issue for clarification

---

## Resources

- **Architecture**: `docs/architecture/README.md`
- **Configuration**: `docs/CONFIGURATION_GUIDE.md`
- **Tooling**: `docs/TOOLING.md`
- **Testing**: `tests/conftest.py` (fixtures)
- **Changelog**: `CHANGELOG.md`

---

**Thank you for contributing to RP Launcher!**
