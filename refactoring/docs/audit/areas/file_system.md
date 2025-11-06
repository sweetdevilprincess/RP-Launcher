# File System - Functional Area Report

## Overview

**Functional Area:** File System
**Total Modules:** 8
**Total LOC (Code):** 921
**Total Classes:** 11
**Total Functions:** 101
**Test Coverage:** 0/8 modules (0.0%)

## Purpose & Scope

File operations including tiered loading, write queues, and storage abstractions.

**Core Responsibilities:**
- Core file manager operations
- Tiered file loading orchestration (50-70% I/O reduction)
- JSON and Markdown storage abstractions
- Async write queue
- State path management
- Data-driven bundle loading

## Architecture

### Layer Distribution

- **Other:** 8 modules, 921 LOC


### Workstream Ownership

- **Workstream B:** 8 modules, 921 LOC


## Component Inventory

| Module | LOC | Classes | Functions | Tests | Purpose |
|--------|-----|---------|-----------|-------|---------|
| `__init__.py` | 19 | 0 | 0 | ✗ | Filesystem-related adapters. |
| `file_access_service.py` | 114 | 2 | 15 | ✗ | High-level filesystem facade composing manager and tiered... |
| `file_manager.py` | 218 | 1 | 33 | ✗ | Refactored FileManager leveraging JsonStore and MarkdownS... |
| `json_store.py` | 108 | 1 | 5 | ✗ | JSON storage helper with merge semantics. |
| `tiered_loader.py` | 311 | 3 | 17 | ✗ | Data-driven tiered file loading for RP automation. |
| `markdown_store.py` | 58 | 1 | 4 | ✗ | Markdown file read/write helpers. |
| `state_paths.py` | 53 | 1 | 18 | ✗ | Utilities for deriving stateful file system paths. |
| `write_queue.py` | 40 | 2 | 9 | ✗ | Facade around the filesystem write queue. |


## Detailed Component Analysis

### `__init__.py`

**Path:** `src/infrastructure/filesystem/__init__.py`
**Workstream:** Workstream B
**LOC:** 19
**Classes:** 0
**Functions:** 0
**Tests:** No
**Purpose:** Filesystem-related adapters.

### `file_access_service.py`

**Path:** `src/infrastructure/filesystem/file_access_service.py`
**Workstream:** Workstream B
**LOC:** 114
**Classes:** 2
**Functions:** 15
**Tests:** No
**Purpose:** High-level filesystem facade composing manager and tiered loader.

### `file_manager.py`

**Path:** `src/infrastructure/filesystem/file_manager.py`
**Workstream:** Workstream B
**LOC:** 218
**Classes:** 1
**Functions:** 33
**Tests:** No
**Purpose:** Refactored FileManager leveraging JsonStore and MarkdownStore.

### `json_store.py`

**Path:** `src/infrastructure/filesystem/json_store.py`
**Workstream:** Workstream B
**LOC:** 108
**Classes:** 1
**Functions:** 5
**Tests:** No
**Purpose:** JSON storage helper with merge semantics.

### `tiered_loader.py`

**Path:** `src/infrastructure/filesystem/loaders/tiered_loader.py`
**Workstream:** Workstream B
**LOC:** 311
**Classes:** 3
**Functions:** 17
**Tests:** No
**Purpose:** Data-driven tiered file loading for RP automation.

### `markdown_store.py`

**Path:** `src/infrastructure/filesystem/markdown_store.py`
**Workstream:** Workstream B
**LOC:** 58
**Classes:** 1
**Functions:** 4
**Tests:** No
**Purpose:** Markdown file read/write helpers.

### `state_paths.py`

**Path:** `src/infrastructure/filesystem/state_paths.py`
**Workstream:** Workstream B
**LOC:** 53
**Classes:** 1
**Functions:** 18
**Tests:** No
**Purpose:** Utilities for deriving stateful file system paths.

### `write_queue.py`

**Path:** `src/infrastructure/filesystem/write_queue.py`
**Workstream:** Workstream B
**LOC:** 40
**Classes:** 2
**Functions:** 9
**Tests:** No
**Purpose:** Facade around the filesystem write queue.



## Test Coverage Analysis

**Modules with tests:** 0/8 (0.0%)

### Tested Modules

*No test files found*


### Untested Modules

- `__init__.py` (19 LOC)
- `file_access_service.py` (114 LOC)
- `file_manager.py` (218 LOC)
- `json_store.py` (108 LOC)
- `tiered_loader.py` (311 LOC)
- `markdown_store.py` (58 LOC)
- `state_paths.py` (53 LOC)
- `write_queue.py` (40 LOC)


## Complexity Analysis

### Largest Modules (by LOC)

- `tiered_loader.py`: 311 LOC
- `file_manager.py`: 218 LOC
- `file_access_service.py`: 114 LOC
- `json_store.py`: 108 LOC
- `markdown_store.py`: 58 LOC


### Most Complex (by Classes)

- `tiered_loader.py`: 3 classes
- `file_access_service.py`: 2 classes
- `write_queue.py`: 2 classes
- `file_manager.py`: 1 classes
- `json_store.py`: 1 classes


### Most Functions

- `file_manager.py`: 33 functions
- `state_paths.py`: 18 functions
- `tiered_loader.py`: 17 functions
- `file_access_service.py`: 15 functions
- `write_queue.py`: 9 functions


## Dependencies

### Internal Dependencies

- `write_queue.py`: 1 internal dependencies


## Status & Recommendations

### Current Status

❌ **Poor** - 0.0% test coverage, critical need for tests


### Recommendations

1. **Improve Test Coverage:** Add tests for 8 untested modules to reach 90%+ coverage


---

*Report generated from component inventory analysis*
*Total modules analyzed: 8*
*Report date: C:\Users\green\Desktop\RP Claude Code\refactoring*
