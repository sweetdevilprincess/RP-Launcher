# Tooling Guide - RP Launcher Refactored

**Version:** 2.0.0
**Last Updated:** 2025-10-21

---

## Overview

The RP Launcher refactored codebase uses modern Python tooling for code quality, type safety, and testing. This guide covers installation, usage, and integration of all development tools.

### Tools Used

- **ruff** - Fast Python linter (replaces flake8, isort, etc.)
- **black** - Code formatter (PEP 8 compliant)
- **mypy** - Static type checker
- **pytest** - Test framework with coverage
- **coverage** - Code coverage measurement

---

## Quick Start

### Install Development Dependencies

```bash
# From project root
cd refactoring/

# Install all dev tools
pip install -r requirements-dev.txt
```

### Run All Checks

**Windows:**
```cmd
scripts\check-all.bat
```

**Linux/macOS:**
```bash
./scripts/check-all.sh
```

This runs:
1. Ruff linting
2. Black formatting check
3. Mypy type checking
4. Pytest with coverage

---

## Installation

### Option 1: Install from requirements-dev.txt (Recommended)

```bash
pip install -r requirements-dev.txt
```

**Includes:**
- pytest>=7.4.0
- pytest-cov>=4.1.0
- ruff>=0.1.0
- black>=23.9.0
- mypy>=1.5.0
- coverage>=7.3.0
- And more...

### Option 2: Install Tools Individually

```bash
pip install ruff black mypy pytest pytest-cov coverage
```

### Verify Installation

```bash
ruff --version
black --version
mypy --version
pytest --version
```

---

## Linting with Ruff

**Ruff** is an extremely fast Python linter written in Rust. It replaces multiple tools (flake8, isort, pyupgrade, etc.) with a single, fast linter.

### Configuration

Configured in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    # ... and many more
]
```

### Usage

**Check for issues:**
```bash
# Windows
scripts\lint.bat

# Linux/macOS
./scripts/lint.sh
```

**Auto-fix issues:**
```bash
# Windows
scripts\lint.bat --fix

# Linux/macOS
./scripts/lint.sh --fix
```

**Manual usage:**
```bash
# Check specific directory
ruff check src/

# Check specific file
ruff check src/infrastructure/config/config_loader.py

# Check and auto-fix
ruff check src/ --fix

# Show fixes that would be applied
ruff check src/ --diff
```

### Common Ruff Rules

| Code | Description | Example |
|------|-------------|---------|
| E501 | Line too long | (Handled by black) |
| F401 | Unused import | `import os  # never used` |
| F841 | Unused variable | `x = 5  # never used` |
| I001 | Import sorting | Imports not sorted |
| B006 | Mutable default argument | `def foo(x=[]):` |
| UP | Python upgrade | `typing.List` → `list` |
| SIM | Simplify | Simplification opportunities |

### Per-File Ignores

Tests have relaxed rules (configured in `pyproject.toml`):
```python
# tests/**/*.py ignores:
# - S101 (assert usage)
# - ARG001 (unused fixtures)
```

---

## Formatting with Black

**Black** is an opinionated code formatter that enforces consistent style.

### Configuration

Configured in `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
```

### Usage

**Check formatting (no changes):**
```bash
# Windows
scripts\format.bat --check

# Linux/macOS
./scripts/format.sh --check
```

**Format code:**
```bash
# Windows
scripts\format.bat

# Linux/macOS
./scripts/format.sh
```

**Manual usage:**
```bash
# Format entire project
black src/ tests/

# Check without formatting
black --check src/

# Show diff of changes
black --diff src/

# Format single file
black src/infrastructure/config/config_loader.py
```

### Black vs Ruff

- **Black**: Formats code (fixes whitespace, line breaks, etc.)
- **Ruff**: Checks code style and logic (finds bugs, bad practices)
- Both are **complementary** - use both!

---

## Type Checking with Mypy

**Mypy** performs static type analysis to catch type-related bugs before runtime.

### Configuration

Configured in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
check_untyped_defs = true
no_implicit_optional = true

# Files to check (incremental approach)
files = [
    "src/infrastructure/config/**/*.py",
    "src/infrastructure/transports/**/*.py",
    "src/domain/entities/**/*.py",
    # ... refactored modules only
]
```

### Usage

**Type check configured modules:**
```bash
# Windows
scripts\typecheck.bat

# Linux/macOS
./scripts/typecheck.sh
```

**Type check specific module:**
```bash
# Windows
scripts\typecheck.bat src/infrastructure/config

# Linux/macOS
./scripts/typecheck.sh src/infrastructure/config
```

**Manual usage:**
```bash
# Check configured files
mypy

# Check specific file
mypy src/infrastructure/config/config_loader.py

# Check with more strict settings
mypy --strict src/infrastructure/config/
```

### Type Annotations Example

```python
from typing import Dict, Any, Optional

def load_config(path: str) -> Dict[str, Any]:
    """Load configuration from file.

    Args:
        path: Path to config file

    Returns:
        Configuration dictionary
    """
    ...

def get_value(config: Dict[str, Any], key: str, default: Optional[str] = None) -> Optional[str]:
    """Get value from config with optional default."""
    return config.get(key, default)
```

### Incremental Typing Strategy

1. **Start**: Type new/refactored code
2. **Gradually**: Add types to existing code
3. **Eventually**: Enable strict mode on all modules

Current status: Refactored modules have type checking enabled.

---

## Testing with Pytest

**Pytest** is the test framework with powerful fixtures and plugins.

### Configuration

Configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "-v"]
markers = [
    "slow: slow running tests",
    "integration: integration tests",
    "unit: unit tests",
    "smoke: smoke tests",
]
```

### Usage

**Run all tests:**
```bash
# Windows
scripts\test.bat

# Linux/macOS
./scripts/test.sh
```

**Run specific test file:**
```bash
python -m pytest tests/infrastructure/config/test_config_loader_validation.py
```

**Run tests matching pattern:**
```bash
python -m pytest -k "test_load"
```

**Run with specific marker:**
```bash
# Only unit tests
python -m pytest -m unit

# Skip slow tests
python -m pytest -m "not slow"
```

**Verbose output:**
```bash
python -m pytest -vv
```

**Stop on first failure:**
```bash
python -m pytest -x
```

### Test Fixtures

Comprehensive fixtures available in `tests/conftest.py`:

```python
def test_example(temp_rp_dir, character_factory):
    """Example test using fixtures."""
    # temp_rp_dir: Temporary RP directory with structure
    character = character_factory("Alice")

    # Create character file
    char_file = temp_rp_dir / "entities" / "characters" / "alice.json"
    with open(char_file, "w") as f:
        json.dump(character, f)

    # Test something...
```

**Available Fixtures:**
- `temp_dir` - Basic temporary directory
- `temp_rp_dir` - Full RP directory structure
- `temp_rp_with_config` - RP dir with default config.json
- `character_factory` - Create test characters
- `location_factory` - Create test locations
- `session_state_factory` - Create session states
- `minimal_config` / `full_config` - Configuration dicts

---

## Code Coverage

**Coverage** measures which lines of code are executed during tests.

### Configuration

Configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 70  # Fail if coverage < 70%
show_missing = true
```

### Usage

**Run tests with coverage:**
```bash
# Included in scripts/test.bat and scripts/test.sh
python -m pytest tests --cov=src --cov-report=term-missing --cov-report=html
```

**View HTML report:**
```bash
# After running tests, open in browser
# Windows
start htmlcov\index.html

# Linux/macOS
open htmlcov/index.html
```

**Generate coverage report only:**
```bash
coverage report
coverage html
```

### Coverage Output Example

```
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src/infrastructure/config/__init__.py          3      0   100%
src/infrastructure/config/config_loader.py   250     15    94%   145-150, 200-205
src/infrastructure/config/defaults.py         87      0   100%
------------------------------------------------------------------------
TOTAL                                        2500    150    94%
```

### Coverage Goals

- **Refactored modules**: ≥90% coverage
- **Legacy modules**: Maintain current level
- **Overall project**: ≥70% coverage

---

## All-in-One Check Script

The `check-all` script runs all checks in sequence:

**Windows:**
```cmd
scripts\check-all.bat
```

**Linux/macOS:**
```bash
./scripts/check-all.sh
```

**Output:**
```
========================================
RP Launcher - Running All Checks
========================================

[1/4] Running ruff linting...
[PASS] Ruff linting passed

[2/4] Checking code formatting with black...
[PASS] Code formatting is correct

[3/4] Running type checking with mypy...
[PASS] Type checking passed

[4/4] Running tests with coverage...
[PASS] All tests passed

========================================
ALL CHECKS PASSED!
========================================
```

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run all checks
        run: |
          ./scripts/check-all.sh
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run checks before commit

./scripts/lint.sh || exit 1
./scripts/format.sh --check || exit 1

echo "Pre-commit checks passed!"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## IDE Integration

### Visual Studio Code

**Install extensions:**
- Python (microsoft.python)
- Pylance (microsoft.pylance)
- Ruff (charliermarsh.ruff)
- Black Formatter (microsoft.black-formatter)

**Settings (.vscode/settings.json):**
```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "mypy.runUsingActiveInterpreter": true
}
```

### PyCharm

**Configure tools:**

1. **Black formatter:**
   - Settings → Tools → Black
   - Enable "On save"

2. **Ruff linter:**
   - Settings → Tools → External Tools
   - Add ruff command

3. **Mypy:**
   - Settings → Tools → External Tools
   - Add mypy command

4. **Pytest:**
   - Settings → Tools → Python Integrated Tools
   - Default test runner: pytest

---

## Troubleshooting

### Tool Not Found

**Problem:** `ruff: command not found`

**Solution:**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Or install tool individually
pip install ruff
```

### Import Errors in Tests

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Tests use `conftest.py` to add project root to `sys.path`. Ensure you're running pytest from project root:

```bash
cd refactoring/
python -m pytest tests/
```

### Type Checking Fails on Legacy Code

**Problem:** Mypy reports errors in legacy modules

**Solution:** Mypy only checks refactored modules (configured in `pyproject.toml`). Legacy code is not type-checked.

### Coverage Below Threshold

**Problem:** `FAILED: coverage: total coverage was 65%, expected 70%`

**Solution:**
1. Add more tests to increase coverage
2. Or temporarily lower threshold in `pyproject.toml`:
   ```toml
   [tool.coverage.report]
   fail_under = 65
   ```

### Black and Ruff Conflicts

**Problem:** Black formats code, ruff complains

**Solution:** This shouldn't happen - they're configured to work together. Check:
- Both use same line length (100)
- Ruff has `E501` ignored (line too long)

### Permission Denied on Scripts

**Problem:** `Permission denied: ./scripts/lint.sh`

**Solution:**
```bash
chmod +x scripts/*.sh
```

---

## Best Practices

### Development Workflow

1. **Before starting work:**
   ```bash
   git pull
   ./scripts/check-all.sh
   ```

2. **During development:**
   ```bash
   # Format frequently
   ./scripts/format.sh

   # Check linting
   ./scripts/lint.sh
   ```

3. **Before committing:**
   ```bash
   # Run all checks
   ./scripts/check-all.sh
   ```

4. **Before pushing:**
   ```bash
   # Ensure tests pass
   ./scripts/test.sh
   ```

### Writing Testable Code

```python
# Good: Use dependency injection
def load_config(loader: ConfigLoader) -> Dict[str, Any]:
    return loader.load()

# Bad: Hard to test
def load_config() -> Dict[str, Any]:
    loader = ConfigLoader("/hard/coded/path")
    return loader.load()
```

### Type Hints Best Practices

```python
from typing import Dict, List, Optional, Any

# Good: Specific types
def process_entities(entities: List[Dict[str, Any]]) -> Dict[str, int]:
    ...

# Bad: Vague types
def process_entities(entities):  # No types
    ...
```

---

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Run all checks | `scripts/check-all.bat` or `./scripts/check-all.sh` |
| Lint code | `scripts/lint.bat` or `./scripts/lint.sh` |
| Auto-fix lint issues | `scripts/lint.bat --fix` |
| Format code | `scripts/format.bat` |
| Check formatting | `scripts/format.bat --check` |
| Type check | `scripts/typecheck.bat` |
| Run tests | `scripts/test.bat` |
| Run tests with coverage | `scripts/test.bat` (default) |
| View coverage HTML | `start htmlcov/index.html` |

### File Locations

| File | Purpose |
|------|---------|
| `pyproject.toml` | Tool configuration (ruff, black, mypy, pytest) |
| `requirements-dev.txt` | Development dependencies |
| `tests/conftest.py` | Shared test fixtures |
| `scripts/*.bat` | Windows tooling scripts |
| `scripts/*.sh` | Linux/macOS tooling scripts |
| `htmlcov/` | Coverage HTML reports |
| `.ruff_cache/` | Ruff cache (gitignored) |
| `.mypy_cache/` | Mypy cache (gitignored) |

---

## Further Reading

- **Ruff**: https://docs.astral.sh/ruff/
- **Black**: https://black.readthedocs.io/
- **Mypy**: https://mypy.readthedocs.io/
- **Pytest**: https://docs.pytest.org/
- **Coverage**: https://coverage.readthedocs.io/

---

**Version:** 2.0.0
**Workstream:** K (Testing & Tooling)
**Date:** 2025-10-21
