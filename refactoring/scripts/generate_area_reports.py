#!/usr/bin/env python3
"""
Functional Area Report Generator

Reads the component inventory CSV and generates detailed markdown reports
for each functional area, including architecture, components, testing, and analysis.
"""

import csv
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


def load_inventory(csv_file: Path) -> List[Dict]:
    """Load component inventory from CSV."""
    components = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            components.append(row)
    return components


def group_by_area(components: List[Dict]) -> Dict[str, List[Dict]]:
    """Group components by functional area."""
    areas = defaultdict(list)
    for comp in components:
        area = comp['Functional Area']
        areas[area].append(comp)
    return dict(areas)


def generate_area_report(area_name: str, components: List[Dict], output_dir: Path):
    """Generate a detailed markdown report for a functional area."""

    # Sort components by module path
    components = sorted(components, key=lambda x: x['Module Path'])

    # Calculate statistics
    total_loc = sum(int(c['LOC Code']) for c in components)
    total_classes = sum(int(c['Classes']) for c in components)
    total_functions = sum(int(c['Functions']) for c in components)
    tested_modules = sum(1 for c in components if c['Has Tests'] == 'Yes')
    test_coverage_pct = (tested_modules / len(components) * 100) if components else 0

    # Group by workstream
    workstreams = defaultdict(list)
    for comp in components:
        workstreams[comp['Workstream']].append(comp)

    # Group by layer
    layers = defaultdict(list)
    for comp in components:
        layers[comp['Layer']].append(comp)

    # Generate filename
    filename = area_name.lower().replace(' & ', '_').replace(' ', '_') + '.md'
    filepath = output_dir / filename

    # Generate report content
    content = f"""# {area_name} - Functional Area Report

## Overview

**Functional Area:** {area_name}
**Total Modules:** {len(components)}
**Total LOC (Code):** {total_loc:,}
**Total Classes:** {total_classes}
**Total Functions:** {total_functions}
**Test Coverage:** {tested_modules}/{len(components)} modules ({test_coverage_pct:.1f}%)

## Purpose & Scope

"""

    # Add purpose description based on area
    purpose_map = {
        'Entity Management': '''This functional area handles all domain entities (characters, locations, organizations, items, memories).
It provides CRUD operations, parsing, validation, and LLM-based preference generation for entity data.

**Core Responsibilities:**
- Entity data models and validation
- Entity repository with fixture support
- Entity service orchestration
- Multi-provider LLM preference generation
- Entity parsing from JSON/Markdown''',

        'Session Management': '''Manages session state, checkpoints, and persistence for roleplay sessions.
Provides state transitions, metadata tracking, and write-back logic.

**Core Responsibilities:**
- Session state management
- Checkpoint system for state snapshots
- Session repository for storage abstraction
- Write-back logic for async persistence
- State transition validation''',

        'Agent System': '''Orchestrates the execution of immediate and background agents for context analysis,
memory extraction, and relationship tracking.

**Core Responsibilities:**
- Agent discovery and cataloging
- Agent creation with conditional logic
- Concurrent agent execution with thread pools
- Result formatting (JSON cache, prompt injection)
- Agent coordination facade
- Retry logic and timeout handling''',

        'Automation Orchestration': '''High-level orchestration of the automation pipeline, including prompt building
and automation service coordination.

**Core Responsibilities:**
- 6-step automation lifecycle
- Prompt assembly from modular sections
- Automation service coordination
- File access integration
- Orchestrator v2 facade''',

        'Trigger System': '''Evaluates triggers to determine when to load contextual files (tier3 bundles).
Supports keyword, regex, and semantic evaluation with frequency tracking.

**Core Responsibilities:**
- Keyword-based trigger evaluation
- Regex pattern matching with caching
- AI-based semantic evaluation
- Frequency tracking and auto-escalation
- Pattern file discovery
- Trigger registry for extensibility''',

        'Template System': '''Manages narrative templates for genre-specific guidance and prompt customization.

**Core Responsibilities:**
- Template loading from JSON files
- LRU caching for performance
- Template discovery and registry
- 4 template modes (auto, composite, modular, layered)
- Template rendering with variable interpolation''',

        'LLM Clients': '''Provides abstraction layer for multiple LLM providers with transport and retry logic.

**Core Responsibilities:**
- LLM client protocol definition
- Multi-provider support (Claude, OpenAI, OpenRouter, DeepSeek, Mock)
- Transport abstraction (Requests, Logging, Proxy, Fake)
- Provider registry
- Retry logic with exponential backoff''',

        'Configuration': '''4-layer configuration system with precedence, validation, and schema definitions.

**Core Responsibilities:**
- Configuration loading from multiple sources
- Deep merge with precedence (ENV → config.json → .env → defaults)
- TypedDict schema validation
- Directory structure validation
- Unknown field warnings''',

        'File System': '''File operations including tiered loading, write queues, and storage abstractions.

**Core Responsibilities:**
- Core file manager operations
- Tiered file loading orchestration (50-70% I/O reduction)
- JSON and Markdown storage abstractions
- Async write queue
- State path management
- Data-driven bundle loading''',

        'Logging & Telemetry': '''Logging infrastructure with performance monitoring and profiling capabilities.

**Core Responsibilities:**
- Python logging service
- Agent-specific logging
- Performance timing and profiling
- Retry policies with backoff strategies
- Statistical aggregation''',

        'IPC Communication': '''Inter-process communication between TUI and backend via socket-based protocol.

**Core Responsibilities:**
- Socket client/server implementation
- Message protocol (20+ message types)
- Request/response handling
- Connection management
- Async communication''',

        'TUI Presentation': '''Terminal user interface components using Textual framework.

**Core Responsibilities:**
- Main TUI application
- Chat display and message rendering
- Context panel and sidebar
- Character editor
- Provider selection
- Testing mode toggle
- Component theming and styles''',

        'Bridge Service': '''Business logic layer connecting TUI to automation backend.

**Core Responsibilities:**
- TUI-backend orchestration
- State management
- Message routing
- Service coordination
- Response handling''',

        'Shared': '''Cross-cutting concerns including interfaces, protocols, and shared utilities.

**Core Responsibilities:**
- Shared protocol definitions
- Common logging utilities
- Shared data models and enums
- Cross-layer interfaces''',

        'Development Tooling': '''Development and build tools for the project.

**Core Responsibilities:**
- Import dependency auditing
- Architecture rule enforcement
- Build automation
- Linting and formatting''',

        'WIP': '''Work-in-progress experimental code not yet integrated.

**Core Responsibilities:**
- Experimental features
- Prototype implementations
- Not yet integrated into main codebase''',

        'Other': '''Miscellaneous components not yet categorized.

**Core Responsibilities:**
- Package initialization files
- Uncategorized utility modules'''
    }

    content += purpose_map.get(area_name, 'Purpose description not yet documented.')

    content += f"""

## Architecture

### Layer Distribution

"""
    for layer, layer_comps in sorted(layers.items()):
        layer_loc = sum(int(c['LOC Code']) for c in layer_comps)
        content += f"- **{layer}:** {len(layer_comps)} modules, {layer_loc:,} LOC\n"

    content += f"""

### Workstream Ownership

"""
    for workstream, ws_comps in sorted(workstreams.items()):
        ws_loc = sum(int(c['LOC Code']) for c in ws_comps)
        content += f"- **{workstream}:** {len(ws_comps)} modules, {ws_loc:,} LOC\n"

    content += f"""

## Component Inventory

| Module | LOC | Classes | Functions | Tests | Purpose |
|--------|-----|---------|-----------|-------|---------|
"""

    for comp in components:
        module_name = Path(comp['Module Path']).name
        loc = comp['LOC Code']
        classes = comp['Classes']
        functions = comp['Functions']
        has_tests = '✓' if comp['Has Tests'] == 'Yes' else '✗'
        purpose = comp['Purpose'] if comp['Purpose'] != 'N/A' else ''
        if len(purpose) > 60:
            purpose = purpose[:57] + '...'

        content += f"| `{module_name}` | {loc} | {classes} | {functions} | {has_tests} | {purpose} |\n"

    content += f"""

## Detailed Component Analysis

"""

    for comp in components:
        module_path = comp['Module Path']
        module_name = Path(module_path).name
        loc = int(comp['LOC Code'])
        classes = int(comp['Classes'])
        functions = int(comp['Functions'])
        has_tests = comp['Has Tests']
        test_path = comp['Test Path']
        purpose = comp['Purpose']
        workstream = comp['Workstream']

        content += f"""### `{module_name}`

**Path:** `{module_path}`
**Workstream:** {workstream}
**LOC:** {loc}
**Classes:** {classes}
**Functions:** {functions}
**Tests:** {has_tests}"""

        if test_path != 'N/A':
            content += f" ({test_path})"

        content += f"""
**Purpose:** {purpose if purpose != 'N/A' else 'Not documented'}

"""

    content += f"""

## Test Coverage Analysis

**Modules with tests:** {tested_modules}/{len(components)} ({test_coverage_pct:.1f}%)

### Tested Modules

"""

    tested = [c for c in components if c['Has Tests'] == 'Yes']
    if tested:
        for comp in tested:
            content += f"- `{Path(comp['Module Path']).name}` → `{comp['Test Path']}`\n"
    else:
        content += "*No test files found*\n"

    content += f"""

### Untested Modules

"""

    untested = [c for c in components if c['Has Tests'] == 'No']
    if untested:
        for comp in untested:
            content += f"- `{Path(comp['Module Path']).name}` ({int(comp['LOC Code'])} LOC)\n"
    else:
        content += "*All modules have tests*\n"

    content += f"""

## Complexity Analysis

### Largest Modules (by LOC)

"""

    by_loc = sorted(components, key=lambda x: int(x['LOC Code']), reverse=True)[:5]
    for comp in by_loc:
        content += f"- `{Path(comp['Module Path']).name}`: {comp['LOC Code']} LOC\n"

    content += f"""

### Most Complex (by Classes)

"""

    by_classes = sorted(components, key=lambda x: int(x['Classes']), reverse=True)[:5]
    for comp in by_classes:
        if int(comp['Classes']) > 0:
            content += f"- `{Path(comp['Module Path']).name}`: {comp['Classes']} classes\n"

    content += f"""

### Most Functions

"""

    by_functions = sorted(components, key=lambda x: int(x['Functions']), reverse=True)[:5]
    for comp in by_functions:
        if int(comp['Functions']) > 0:
            content += f"- `{Path(comp['Module Path']).name}`: {comp['Functions']} functions\n"

    content += f"""

## Dependencies

### Internal Dependencies

"""

    by_deps = sorted(components, key=lambda x: int(x['Internal Dependencies']), reverse=True)[:10]
    high_dep_found = False
    for comp in by_deps:
        deps = int(comp['Internal Dependencies'])
        if deps > 0:
            high_dep_found = True
            content += f"- `{Path(comp['Module Path']).name}`: {deps} internal dependencies\n"

    if not high_dep_found:
        content += "*No high-dependency modules identified*\n"

    content += f"""

## Status & Recommendations

### Current Status

"""

    if test_coverage_pct >= 90:
        content += f"✅ **Excellent** - {test_coverage_pct:.1f}% test coverage\n"
    elif test_coverage_pct >= 70:
        content += f"⚠️ **Good** - {test_coverage_pct:.1f}% test coverage, could be improved\n"
    elif test_coverage_pct >= 50:
        content += f"⚠️ **Fair** - {test_coverage_pct:.1f}% test coverage, needs improvement\n"
    else:
        content += f"❌ **Poor** - {test_coverage_pct:.1f}% test coverage, critical need for tests\n"

    content += f"""

### Recommendations

"""

    # Generate recommendations based on analysis
    recommendations = []

    if test_coverage_pct < 90:
        recommendations.append(f"**Improve Test Coverage:** Add tests for {len(untested)} untested modules to reach 90%+ coverage")

    if any(int(c['LOC Code']) > 500 for c in components):
        large_modules = [c for c in components if int(c['LOC Code']) > 500]
        recommendations.append(f"**Refactor Large Modules:** Consider breaking down {len(large_modules)} modules exceeding 500 LOC")

    if any(int(c['Internal Dependencies']) > 5 for c in components):
        high_dep = [c for c in components if int(c['Internal Dependencies']) > 5]
        recommendations.append(f"**Reduce Dependencies:** {len(high_dep)} modules have >5 internal dependencies, review for tight coupling")

    if len(workstreams) > 3:
        recommendations.append(f"**Documentation:** Multiple workstreams ({len(workstreams)}) contributed - ensure consistent patterns")

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            content += f"{i}. {rec}\n"
    else:
        content += "*No major recommendations - area is well-structured*\n"

    content += f"""

---

*Report generated from component inventory analysis*
*Total modules analyzed: {len(components)}*
*Report date: {Path.cwd()}*
"""

    # Write report
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def generate_all_reports(project_root: Path):
    """Generate reports for all functional areas."""
    csv_file = project_root / 'docs' / 'audit' / 'component_inventory.csv'
    output_dir = project_root / 'docs' / 'audit' / 'areas'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load inventory
    print("Loading component inventory...")
    components = load_inventory(csv_file)

    # Group by area
    areas = group_by_area(components)

    print(f"\nGenerating reports for {len(areas)} functional areas...\n")

    # Generate reports
    generated = []
    for area_name, area_comps in sorted(areas.items()):
        print(f"  Generating: {area_name}...")
        filepath = generate_area_report(area_name, area_comps, output_dir)
        generated.append(filepath)

    print(f"\n[SUCCESS] Generated {len(generated)} functional area reports")
    print(f"  Output directory: {output_dir}")

    # Create index file
    index_file = output_dir / 'README.md'
    index_content = """# Functional Area Reports

This directory contains detailed reports for each functional area in the codebase.

## Available Reports

"""

    for area_name in sorted(areas.keys()):
        filename = area_name.lower().replace(' & ', '_').replace(' ', '_') + '.md'
        module_count = len(areas[area_name])
        loc = sum(int(c['LOC Code']) for c in areas[area_name])
        index_content += f"- [{area_name}](./{filename}) - {module_count} modules, {loc:,} LOC\n"

    index_content += """

## Report Structure

Each report includes:

1. **Overview** - Statistics and metrics
2. **Purpose & Scope** - What this area does
3. **Architecture** - Layer and workstream distribution
4. **Component Inventory** - Detailed module listing
5. **Detailed Analysis** - Per-module breakdown
6. **Test Coverage** - Testing status
7. **Complexity Analysis** - Largest/most complex modules
8. **Dependencies** - Internal dependency analysis
9. **Recommendations** - Improvement suggestions

---

*Generated from component inventory analysis*
"""

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)

    print(f"  Index file: {index_file}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    generate_all_reports(project_root)
