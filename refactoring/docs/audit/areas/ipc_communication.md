# IPC Communication - Functional Area Report

## Overview

**Functional Area:** IPC Communication
**Total Modules:** 5
**Total LOC (Code):** 860
**Total Classes:** 9
**Total Functions:** 50
**Test Coverage:** 1/5 modules (20.0%)

## Purpose & Scope

Inter-process communication between TUI and backend via socket-based protocol.

**Core Responsibilities:**
- Socket client/server implementation
- Message protocol (20+ message types)
- Request/response handling
- Connection management
- Async communication

## Architecture

### Layer Distribution

- **Other:** 5 modules, 860 LOC


### Workstream Ownership

- **Workstream M:** 5 modules, 860 LOC


## Component Inventory

| Module | LOC | Classes | Functions | Tests | Purpose |
|--------|-----|---------|-----------|-------|---------|
| `__init__.py` | 37 | 0 | 0 | ✗ | Inter-process communication module for TUI-Bridge communi... |
| `ipc_channel.py` | 132 | 3 | 10 | ✗ | Schema-validated IPC channel for automation state exchanges. |
| `ipc_protocol.py` | 232 | 4 | 14 | ✓ | IPC Protocol for TUI-Bridge Communication. |
| `socket_client.py` | 265 | 1 | 14 | ✗ | Socket Client for TUI-side IPC. |
| `socket_server.py` | 194 | 1 | 12 | ✗ | Socket Server for Bridge-side IPC. |


## Detailed Component Analysis

### `__init__.py`

**Path:** `src/infrastructure/ipc/__init__.py`
**Workstream:** Workstream M
**LOC:** 37
**Classes:** 0
**Functions:** 0
**Tests:** No
**Purpose:** Inter-process communication module for TUI-Bridge communication.

### `ipc_channel.py`

**Path:** `src/infrastructure/ipc/ipc_channel.py`
**Workstream:** Workstream M
**LOC:** 132
**Classes:** 3
**Functions:** 10
**Tests:** No
**Purpose:** Schema-validated IPC channel for automation state exchanges.

### `ipc_protocol.py`

**Path:** `src/infrastructure/ipc/ipc_protocol.py`
**Workstream:** Workstream M
**LOC:** 232
**Classes:** 4
**Functions:** 14
**Tests:** Yes (tests\infrastructure\ipc\test_ipc_protocol.py)
**Purpose:** IPC Protocol for TUI-Bridge Communication.

### `socket_client.py`

**Path:** `src/infrastructure/ipc/socket_client.py`
**Workstream:** Workstream M
**LOC:** 265
**Classes:** 1
**Functions:** 14
**Tests:** No
**Purpose:** Socket Client for TUI-side IPC.

### `socket_server.py`

**Path:** `src/infrastructure/ipc/socket_server.py`
**Workstream:** Workstream M
**LOC:** 194
**Classes:** 1
**Functions:** 12
**Tests:** No
**Purpose:** Socket Server for Bridge-side IPC.



## Test Coverage Analysis

**Modules with tests:** 1/5 (20.0%)

### Tested Modules

- `ipc_protocol.py` → `tests\infrastructure\ipc\test_ipc_protocol.py`


### Untested Modules

- `__init__.py` (37 LOC)
- `ipc_channel.py` (132 LOC)
- `socket_client.py` (265 LOC)
- `socket_server.py` (194 LOC)


## Complexity Analysis

### Largest Modules (by LOC)

- `socket_client.py`: 265 LOC
- `ipc_protocol.py`: 232 LOC
- `socket_server.py`: 194 LOC
- `ipc_channel.py`: 132 LOC
- `__init__.py`: 37 LOC


### Most Complex (by Classes)

- `ipc_protocol.py`: 4 classes
- `ipc_channel.py`: 3 classes
- `socket_client.py`: 1 classes
- `socket_server.py`: 1 classes


### Most Functions

- `ipc_protocol.py`: 14 functions
- `socket_client.py`: 14 functions
- `socket_server.py`: 12 functions
- `ipc_channel.py`: 10 functions


## Dependencies

### Internal Dependencies

*No high-dependency modules identified*


## Status & Recommendations

### Current Status

❌ **Poor** - 20.0% test coverage, critical need for tests


### Recommendations

1. **Improve Test Coverage:** Add tests for 4 untested modules to reach 90%+ coverage


---

*Report generated from component inventory analysis*
*Total modules analyzed: 5*
*Report date: C:\Users\green\Desktop\RP Claude Code\refactoring*
