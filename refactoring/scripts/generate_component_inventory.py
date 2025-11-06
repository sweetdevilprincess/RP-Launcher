#!/usr/bin/env python3
"""
Component Inventory Generator

Scans the codebase and generates a comprehensive CSV inventory of all modules,
including metadata like LOC, complexity, dependencies, and workstream ownership.
"""

import csv
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import ast


def count_lines(file_path: Path) -> Dict[str, int]:
    """Count total, code, comment, and blank lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        total = len(lines)
        blank = sum(1 for line in lines if not line.strip())
        comment = sum(1 for line in lines if line.strip().startswith('#'))
        code = total - blank - comment

        return {'total': total, 'code': code, 'comment': comment, 'blank': blank}
    except Exception as e:
        return {'total': 0, 'code': 0, 'comment': 0, 'blank': 0, 'error': str(e)}


def extract_imports(file_path: Path) -> List[str]:
    """Extract all imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports
    except Exception:
        return []


def extract_classes_and_functions(file_path: Path) -> Dict[str, int]:
    """Count classes and functions in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))

        return {'classes': classes, 'functions': functions}
    except Exception:
        return {'classes': 0, 'functions': 0}


def extract_docstring(file_path: Path) -> Optional[str]:
    """Extract module-level docstring."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        docstring = ast.get_docstring(tree)
        if docstring:
            # Return first line only
            return docstring.split('\n')[0].strip()
        return None
    except Exception:
        return None


def determine_workstream(file_path: Path, content: str) -> str:
    """Determine which workstream created this file based on git history or content."""
    # Convert to string with forward slashes for consistent matching
    path_str = str(file_path).replace('\\', '/')

    # Map based on directory structure and known workstreams (most specific first)
    workstream_patterns = [
        ('src/domain/entities/', 'Workstream C'),
        ('src/domain/sessions/', 'Workstream B/G'),
        ('src/automation/orchestrator/', 'Workstream D'),
        ('src/automation/agents/', 'Workstream E'),
        ('src/automation/services/agent_', 'Workstream E'),
        ('src/automation/services/prompt', 'Workstream D'),
        ('src/automation/services/automation_service', 'Workstream D'),
        ('src/automation/triggers/', 'Workstream F'),
        ('src/automation/templates/', 'Workstream F'),
        ('src/automation/factory', 'Workstream D'),
        ('src/infrastructure/config/', 'Workstream J'),
        ('src/infrastructure/filesystem/', 'Workstream B'),
        ('src/infrastructure/llm/', 'Workstream I'),
        ('src/infrastructure/logging/', 'Workstream H'),
        ('src/infrastructure/telemetry/', 'Workstream H'),
        ('src/infrastructure/retry/', 'Workstream H'),
        ('src/infrastructure/transports/', 'Workstream I'),
        ('src/infrastructure/templates/', 'Workstream F'),
        ('src/infrastructure/ipc/', 'Workstream M'),
        ('src/presentation/tui/', 'Workstream M'),
        ('src/presentation/bridge/', 'Workstream M'),
        ('src/shared/', 'Workstream A'),
        ('src/tools/', 'Workstream K'),
        ('src/wip/', 'WIP'),
    ]

    for pattern, workstream in workstream_patterns:
        if pattern in path_str:
            return workstream

    return 'Unknown'


def determine_layer(file_path: Path) -> str:
    """Determine which architectural layer this file belongs to."""
    path_str = str(file_path)

    if 'domain/' in path_str:
        return 'Domain'
    elif 'automation/' in path_str:
        return 'Application'
    elif 'infrastructure/' in path_str:
        return 'Infrastructure'
    elif 'presentation/' in path_str:
        return 'Presentation'
    elif 'shared/' in path_str:
        return 'Shared'
    elif 'tools/' in path_str:
        return 'Tools'
    else:
        return 'Other'


def determine_functional_area(file_path: Path) -> str:
    """Determine functional area for categorization."""
    # Convert to string with forward slashes for consistent matching
    path_str = str(file_path).replace('\\', '/')

    # Use ordered list for most specific matches first
    area_patterns = [
        ('src/domain/entities/', 'Entity Management'),
        ('src/domain/sessions/', 'Session Management'),
        ('src/automation/orchestrator/', 'Automation Orchestration'),
        ('src/automation/agents/', 'Agent System'),
        ('src/automation/services/agent_', 'Agent System'),
        ('src/automation/services/prompt', 'Automation Orchestration'),
        ('src/automation/services/session', 'Session Management'),
        ('src/automation/services/automation_service', 'Automation Orchestration'),
        ('src/automation/triggers/', 'Trigger System'),
        ('src/automation/templates/', 'Template System'),
        ('src/infrastructure/config/', 'Configuration'),
        ('src/infrastructure/filesystem/', 'File System'),
        ('src/infrastructure/llm/', 'LLM Clients'),
        ('src/infrastructure/logging/', 'Logging & Telemetry'),
        ('src/infrastructure/telemetry/', 'Logging & Telemetry'),
        ('src/infrastructure/retry/', 'Logging & Telemetry'),
        ('src/infrastructure/transports/', 'LLM Clients'),
        ('src/infrastructure/templates/', 'Template System'),
        ('src/infrastructure/ipc/', 'IPC Communication'),
        ('src/presentation/tui/', 'TUI Presentation'),
        ('src/presentation/bridge/', 'Bridge Service'),
        ('src/shared/', 'Shared'),
        ('src/tools/', 'Development Tooling'),
        ('src/wip/', 'WIP'),
    ]

    for pattern, area in area_patterns:
        if pattern in path_str:
            return area

    return 'Other'


def has_test_coverage(file_path: Path, project_root: Path) -> tuple[bool, Optional[str]]:
    """Check if a test file exists for this module."""
    rel_path = file_path.relative_to(project_root / 'src')
    test_path = project_root / 'tests' / rel_path

    # Try exact match
    if test_path.exists():
        return True, str(test_path.relative_to(project_root))

    # Try test_ prefix
    test_file = test_path.parent / f"test_{test_path.name}"
    if test_file.exists():
        return True, str(test_file.relative_to(project_root))

    return False, None


def analyze_file(file_path: Path, project_root: Path) -> Dict:
    """Analyze a single Python file and return metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None

    line_counts = count_lines(file_path)
    imports = extract_imports(file_path)
    code_structure = extract_classes_and_functions(file_path)
    docstring = extract_docstring(file_path)
    workstream = determine_workstream(file_path, content)
    layer = determine_layer(file_path)
    functional_area = determine_functional_area(file_path)
    has_test, test_path = has_test_coverage(file_path, project_root)

    # Count internal dependencies (imports from src/)
    internal_deps = [imp for imp in imports if imp.startswith('src.') or imp.startswith('automation.') or imp.startswith('domain.') or imp.startswith('infrastructure.')]

    rel_path = file_path.relative_to(project_root)

    return {
        'Module Path': str(rel_path).replace('\\', '/'),
        'Module Name': file_path.stem,
        'Layer': layer,
        'Functional Area': functional_area,
        'Workstream': workstream,
        'LOC Total': line_counts['total'],
        'LOC Code': line_counts['code'],
        'LOC Comments': line_counts['comment'],
        'Classes': code_structure['classes'],
        'Functions': code_structure['functions'],
        'Internal Dependencies': len(internal_deps),
        'Total Imports': len(imports),
        'Has Tests': 'Yes' if has_test else 'No',
        'Test Path': test_path or 'N/A',
        'Purpose': docstring or 'N/A',
        'Status': 'Complete',  # Can be updated manually
        'Overlap Flags': '',  # To be filled during overlap analysis
        'Recommendations': '',  # To be filled during recommendation phase
    }


def generate_inventory(project_root: Path, output_file: Path):
    """Generate complete component inventory CSV."""
    src_dir = project_root / 'src'

    # Find all Python files
    python_files = list(src_dir.rglob('*.py'))

    # Filter out __pycache__ and __init__.py files (but keep track of them separately)
    python_files = [f for f in python_files if '__pycache__' not in str(f)]

    # Analyze all files
    print(f"Analyzing {len(python_files)} Python files...")
    components = []

    for i, file_path in enumerate(python_files, 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(python_files)} files...")

        metadata = analyze_file(file_path, project_root)
        if metadata:
            components.append(metadata)

    # Sort by functional area, then by module path
    components.sort(key=lambda x: (x['Functional Area'], x['Module Path']))

    # Write to CSV
    if components:
        fieldnames = list(components[0].keys())

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(components)

        print(f"\n[SUCCESS] Component inventory generated: {output_file}")
        print(f"   Total components: {len(components)}")

        # Print summary statistics
        print("\n[STATISTICS] Summary Statistics:")
        print(f"   Total LOC (code only): {sum(c['LOC Code'] for c in components):,}")
        print(f"   Total classes: {sum(c['Classes'] for c in components):,}")
        print(f"   Total functions: {sum(c['Functions'] for c in components):,}")
        print(f"   Modules with tests: {sum(1 for c in components if c['Has Tests'] == 'Yes')}")
        print(f"   Test coverage: {sum(1 for c in components if c['Has Tests'] == 'Yes') / len(components) * 100:.1f}%")

        # Group by functional area
        print("\n[BY AREA] By Functional Area:")
        areas = {}
        for comp in components:
            area = comp['Functional Area']
            if area not in areas:
                areas[area] = []
            areas[area].append(comp)

        for area, comps in sorted(areas.items()):
            loc = sum(c['LOC Code'] for c in comps)
            print(f"   {area:30s}: {len(comps):3d} modules, {loc:6,} LOC")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    output_file = project_root / 'docs' / 'audit' / 'component_inventory.csv'

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    generate_inventory(project_root, output_file)
