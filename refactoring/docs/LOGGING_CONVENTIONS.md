# Logging Conventions

**Workstream H - Logging & Telemetry**

This document describes the logging system, conventions, and best practices for the RP Launcher refactoring project.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Logging Levels](#logging-levels)
- [Structured Logging](#structured-logging)
- [Performance Profiling](#performance-profiling)
- [Testing with Logging](#testing-with-logging)
- [Configuration](#configuration)
- [File Locations](#file-locations)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

The logging system provides structured, consistent logging across all refactored modules. It is built on Python's standard `logging` module with additional features for structured context and performance tracking.

### Architecture

```
┌─────────────────────────────────────────┐
│   Application Code                      │
│                                         │
│   from shared.logging import get_logger │
│   logger = get_logger(__name__)        │
│   logger.info("event", context={...})  │
└───────────┬─────────────────────────────┘
            │
            ↓
┌───────────────────────────────────────────┐
│   LoggingService Protocol                  │
│   (shared/interfaces/logging_service.py)   │
└───────────┬───────────────────────────────┘
            │
            ↓
┌───────────────────────────────────────────┐
│   PythonLogger Implementation              │
│   (shared/logging.py)                      │
│   - Structured context support             │
│   - JSON formatting                        │
└───────────┬───────────────────────────────┘
            │
            ↓
┌───────────────────────────────────────────┐
│   Python logging.Logger                    │
│   - Standard logging levels                │
│   - Handler/formatter configuration        │
└───────────────────────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **LoggingService** | `shared/interfaces/logging_service.py` | Protocol defining logging interface |
| **get_logger()** | `shared/logging.py` | Factory for creating loggers |
| **PythonLogger** | `shared/logging.py` | Production logger implementation |
| **PerformanceTimer** | `infrastructure/telemetry/performance.py` | Manual timing |
| **timed_operation** | `infrastructure/telemetry/performance.py` | Context manager timing |
| **@timed** | `infrastructure/telemetry/performance.py` | Function timing decorator |
| **PerformanceProfiler** | `infrastructure/telemetry/performance.py` | Aggregated profiling |

---

## Quick Start

### Basic Logging

```python
from shared.logging import get_logger

# Create logger (typically at module level)
logger = get_logger(__name__)

# Log messages
logger.info("operation.started")
logger.debug("processing.file", context={"file": "data.json"})
logger.warning("deprecated.feature_used", context={"feature": "old_api"})
logger.error("operation.failed", context={"error": "timeout"})
```

### With Structured Context

```python
logger.info(
    "entity.loaded",
    context={
        "entity_type": "character",
        "entity_name": "Alice",
        "load_time_ms": 123.5,
    }
)
```

### Performance Timing

```python
from infrastructure.telemetry import timed_operation

with timed_operation("entity_loading", logger):
    # ... load entities ...
    pass  # Automatically logs duration
```

---

## Logging Levels

Use appropriate logging levels based on the nature of the message:

### DEBUG

**When to use:**
- Detailed diagnostic information for developers
- Variable values during debugging
- Entry/exit of functions (when needed)
- Intermediate calculation results

**Examples:**
```python
logger.debug("trigger.evaluation.started", context={"patterns_count": len(patterns)})
logger.debug("cache.lookup", context={"key": cache_key, "hit": False})
```

### INFO

**When to use:**
- General operational information
- Successful completion of operations
- System state changes
- Important business events

**Examples:**
```python
logger.info("session.created", context={"session_id": session_id})
logger.info("entities.loaded", context={"count": 5, "duration_ms": 123})
```

### WARNING

**When to use:**
- Recoverable issues
- Deprecated feature usage
- Unusual but handled situations
- Performance degradation

**Examples:**
```python
logger.warning("config.missing_key", context={"key": "optional_setting"})
logger.warning("cache.full", context={"size": cache_size, "evicting": True})
```

### ERROR

**When to use:**
- Operation failures
- Unrecoverable errors
- User-visible errors
- Data inconsistencies

**Examples:**
```python
logger.error("file.read_failed", context={"path": str(path), "error": str(e)})
logger.error("api.request_failed", context={"url": url, "status": 500})
```

### EXCEPTION

**When to use:**
- Logging exceptions with stack traces
- Unexpected errors during exception handling

**Examples:**
```python
try:
    result = process_data(data)
except Exception as exc:
    logger.exception("data.processing_failed", context={"data_type": "entity"}, exc=exc)
    raise
```

---

## Structured Logging

All log messages should use structured context for better searchability and analysis.

### Event Names

Use dot-separated event names that describe what happened:

**Pattern:** `<component>.<entity>.<action>`

**Examples:**
```python
logger.info("trigger.keyword.matched")
logger.info("entity.character.loaded")
logger.info("session.checkpoint.created")
logger.info("cache.template.evicted")
```

### Context Dictionary

Include relevant data in the context dictionary:

```python
logger.info(
    "trigger.frequency.escalated",
    context={
        "entity_name": "Alice",
        "trigger_count": 5,
        "threshold": 3,
        "window_size": 10,
    }
)
```

### Context Conventions

| Context Key | Type | Usage |
|-------------|------|-------|
| `operation` | str | Name of the operation |
| `duration_ms` | float | Duration in milliseconds |
| `error` | str | Error message |
| `path` | str | File path |
| `count` | int | Number of items |
| `entity_name` | str | Entity identifier |
| `entity_type` | str | Type of entity |
| `status` | str | Operation status |
| `reason` | str | Reason for action |

---

## Performance Profiling

The telemetry system provides multiple ways to measure and log performance.

### Manual Timing

```python
from infrastructure.telemetry import PerformanceTimer

logger = get_logger(__name__)
timer = PerformanceTimer("entity_loading", logger)

timer.start()
# ... do work ...
duration_ms = timer.stop(context={"entities_loaded": 10})
```

### Context Manager

```python
from infrastructure.telemetry import timed_operation

with timed_operation("pattern_matching", logger):
    # ... match patterns ...
    pass  # Automatically logs on exit
```

### Function Decorator

```python
from infrastructure.telemetry import timed

@timed("user_validation")
def validate_user(user_id: str, logger) -> bool:
    # ... validation logic ...
    return True

# Usage
result = validate_user("alice", logger=logger)
```

**Note:** Decorated functions must have a `logger` parameter (as positional or keyword argument), or be methods with `self._logger` or `self.logger`.

### Aggregated Profiling

```python
from infrastructure.telemetry import PerformanceProfiler

profiler = PerformanceProfiler(logger)

# Time multiple operations
for entity in entities:
    with profiler.time("entity_parsing"):
        parse_entity(entity)

for template in templates:
    with profiler.time("template_loading"):
        load_template(template)

# Log summary statistics
profiler.log_summary()
# Outputs: {
#   "entity_parsing": {"count": 10, "avg_ms": 15.2, ...},
#   "template_loading": {"count": 5, "avg_ms": 8.4, ...}
# }
```

---

## Testing with Logging

### Using Silent Logger

For tests that don't need logging output:

```python
from shared.logging import get_silent_logger

def test_entity_loading():
    logger = get_silent_logger(__name__)
    service = EntityService(logger=logger)
    # ... test logic ...
```

### Mocking Logger

For tests that verify logging behavior:

```python
from unittest.mock import MagicMock

def test_error_logging():
    logger = MagicMock()
    service = EntityService(logger=logger)

    service.process_invalid_data(bad_data)

    # Verify error was logged
    logger.error.assert_called_once()
    call_context = logger.error.call_args[1]["context"]
    assert "error" in call_context
```

### Testing Performance Timing

```python
def test_operation_timing():
    logger = MagicMock()

    with timed_operation("test_op", logger):
        # ... operation ...
        pass

    # Verify timing was logged
    logger.info.assert_called()
    context = logger.info.call_args[1]["context"]
    assert "duration_ms" in context
    assert context["duration_ms"] > 0
```

---

## Configuration

### Basic Configuration

Configure logging at application startup:

```python
from infrastructure.logging import configure_logging
import logging

# Configure with INFO level
configure_logging(level=logging.INFO)

# Or with DEBUG for development
configure_logging(level=logging.DEBUG)
```

### Custom Configuration

For more control, use Python's logging configuration:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(),
    ]
)
```

### Environment-Specific Configuration

```python
import os
import logging

level = logging.DEBUG if os.getenv("DEBUG") else logging.INFO
configure_logging(level=level)
```

---

## File Locations

### Source Files

| File | Purpose |
|------|---------|
| `src/shared/interfaces/logging_service.py` | LoggingService protocol definition |
| `src/shared/logging.py` | Logger factory and implementations |
| `src/infrastructure/logging/python_logging.py` | PythonLoggingService (alternative implementation) |
| `src/infrastructure/logging/agent_logging.py` | Specialized agent logging (legacy) |
| `src/infrastructure/telemetry/performance.py` | Performance profiling utilities |

### Test Files

| File | Purpose |
|------|---------|
| `tests/shared/test_logging.py` | Tests for core logging functionality |
| `tests/infrastructure/telemetry/test_performance.py` | Tests for performance profiling |

### Log Output

By default, logs go to stderr. Configure handlers to write to files:

**Recommended locations:**
- Development: `logs/debug.log`
- Production: `logs/app.log`
- Agents: `logs/agents.log`
- Performance: `logs/performance.log`

---

## Best Practices

### 1. Use Module-Level Logger

Create logger once at module level:

```python
# ✅ Good
from shared.logging import get_logger

logger = get_logger(__name__)

class EntityService:
    def process(self):
        logger.info("processing.started")
```

```python
# ❌ Avoid
class EntityService:
    def process(self):
        logger = get_logger(__name__)  # Don't create every time
        logger.info("processing.started")
```

### 2. Use Structured Events

Use descriptive event names with context:

```python
# ✅ Good
logger.info("entity.loaded", context={"name": "Alice", "type": "character"})

# ❌ Avoid
logger.info("Entity loaded")  # No structure, hard to search
logger.info(f"Loaded entity {name}")  # String formatting loses structure
```

### 3. Don't Log Sensitive Data

Never log passwords, API keys, or personal data:

```python
# ❌ NEVER DO THIS
logger.info("auth.login", context={"password": user_password})

# ✅ Good
logger.info("auth.login", context={"user_id": user_id})
```

### 4. Use Appropriate Log Levels

Don't over-use INFO or DEBUG:

```python
# ✅ Good - INFO for important events
logger.info("session.created", context={"session_id": id})

# ❌ Avoid - INFO for low-level details
logger.info("variable.set", context={"var": "x", "value": 42})  # Use DEBUG
```

### 5. Include Context for Errors

Always include context that helps debug errors:

```python
# ✅ Good
logger.error(
    "file.read_failed",
    context={
        "path": str(file_path),
        "error": str(e),
        "exists": file_path.exists(),
        "permissions": oct(file_path.stat().st_mode),
    }
)

# ❌ Avoid
logger.error("File read failed")  # No context
```

### 6. Time Performance-Critical Operations

Use timing for operations that might be slow:

```python
# ✅ Good - Time potentially slow operations
with timed_operation("database_query", logger):
    results = db.query(complex_query)

# ❌ Avoid timing trivial operations
with timed_operation("variable_assignment", logger):
    x = 42  # Too trivial to time
```

### 7. Handle Exceptions Properly

Log exceptions with full context:

```python
# ✅ Good
try:
    result = process_data(data)
except ValueError as e:
    logger.exception(
        "data.validation_failed",
        context={"data_type": type(data).__name__},
        exc=e
    )
    raise

# ❌ Avoid swallowing exceptions
except ValueError:
    logger.error("Something went wrong")  # Lost exception details
```

### 8. Avoid print() Statements

Use logging instead of print():

```python
# ✅ Good
logger.info("processing.complete", context={"items": count})

# ❌ Avoid (except in CLI tools)
print(f"Processed {count} items")
```

**Exception:** CLI tools may use print() for user-facing output (see `tools/import_audit.py`).

---

## Examples

### Example 1: Service with Logging

```python
from pathlib import Path
from shared.logging import get_logger
from infrastructure.telemetry import timed_operation

logger = get_logger(__name__)

class EntityService:
    def __init__(self, entity_dir: Path):
        self.entity_dir = entity_dir
        logger.info("service.initialized", context={"entity_dir": str(entity_dir)})

    def load_entity(self, entity_name: str) -> dict:
        logger.debug("entity.loading", context={"name": entity_name})

        with timed_operation("entity.file_read", logger):
            entity_path = self.entity_dir / f"{entity_name}.json"

            if not entity_path.exists():
                logger.error(
                    "entity.not_found",
                    context={"name": entity_name, "path": str(entity_path)}
                )
                raise FileNotFoundError(f"Entity not found: {entity_name}")

            try:
                with entity_path.open() as f:
                    data = json.load(f)
            except Exception as e:
                logger.exception(
                    "entity.parse_failed",
                    context={"name": entity_name, "error": str(e)},
                    exc=e
                )
                raise

        logger.info(
            "entity.loaded",
            context={
                "name": entity_name,
                "fields": len(data),
            }
        )
        return data
```

### Example 2: Performance Profiling

```python
from shared.logging import get_logger
from infrastructure.telemetry import PerformanceProfiler

logger = get_logger(__name__)

def process_batch(items: list):
    profiler = PerformanceProfiler(logger)

    for item in items:
        with profiler.time("validation"):
            validate(item)

        with profiler.time("transformation"):
            transform(item)

        with profiler.time("persistence"):
            save(item)

    # Log summary
    profiler.log_summary()
    # Output includes avg_ms, min_ms, max_ms for each operation
```

### Example 3: Error Handling

```python
from shared.logging import get_logger

logger = get_logger(__name__)

def process_user_input(data: dict):
    try:
        logger.debug("input.processing", context={"keys": list(data.keys())})

        if "required_field" not in data:
            logger.warning(
                "input.missing_field",
                context={"field": "required_field", "data": data}
            )
            data["required_field"] = "default"

        result = expensive_operation(data)

        logger.info(
            "input.processed",
            context={"result_size": len(result)}
        )
        return result

    except Exception as e:
        logger.exception(
            "input.processing_failed",
            context={"data_keys": list(data.keys())},
            exc=e
        )
        raise
```

### Example 4: Testing

```python
from unittest.mock import MagicMock
from shared.logging import get_silent_logger

def test_entity_service_logs_errors():
    """Test that service logs errors appropriately."""
    logger = MagicMock()
    service = EntityService(Path("/tmp/entities"), logger=logger)

    with pytest.raises(FileNotFoundError):
        service.load_entity("nonexistent")

    # Verify error was logged
    logger.error.assert_called_once()
    context = logger.error.call_args[1]["context"]
    assert context["name"] == "nonexistent"

def test_silent_logging():
    """Test operation without logging noise."""
    logger = get_silent_logger(__name__)
    service = EntityService(Path("/tmp"), logger=logger)

    # No log output during test
    service.initialize()
```

---

## Migration Notes

### From Legacy Logging

If migrating from legacy code:

**Old:**
```python
print(f"Loaded {count} entities")
log_to_file(log_file, f"Entity {name} processed")
```

**New:**
```python
logger.info("entities.loaded", context={"count": count})
logger.info("entity.processed", context={"name": name})
```

### From Direct logging.Logger

**Old:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {item}")
```

**New:**
```python
from shared.logging import get_logger
logger = get_logger(__name__)
logger.info("item.processing", context={"item": item})
```

---

## Summary

1. **Use `get_logger(__name__)`** for all modules
2. **Use structured event names** with context dictionaries
3. **Choose appropriate log levels** (DEBUG, INFO, WARNING, ERROR)
4. **Time performance-critical operations** with telemetry utilities
5. **Include relevant context** for all log messages
6. **Test with silent logger** or mocks
7. **Never log sensitive data**
8. **Avoid print() statements** except in CLI tools

For questions or issues, refer to:
- Source code: `src/shared/logging.py`, `src/infrastructure/telemetry/performance.py`
- Tests: `tests/shared/test_logging.py`, `tests/infrastructure/telemetry/test_performance.py`
- This document: `docs/LOGGING_CONVENTIONS.md`

---

*Last updated: 2025-10-20*
*Workstream: H (Logging & Telemetry)*
