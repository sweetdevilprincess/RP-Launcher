#!/usr/bin/env python3
"""
Overlap Analysis Tool

Analyzes the codebase for overlapping responsibilities, naming conflicts,
and potential consolidation opportunities.
"""

import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re


def load_inventory(csv_file: Path) -> List[Dict]:
    """Load component inventory from CSV."""
    components = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            components.append(row)
    return components


def analyze_naming_overlaps(components: List[Dict]) -> List[Dict]:
    """Find modules with similar names that might have overlapping responsibilities."""
    overlaps = []

    # Group by base name patterns
    name_groups = defaultdict(list)
    for comp in components:
        name = comp['Module Name']
        # Extract base name (e.g., "agent_" prefix, "service" suffix, etc.)
        if name.startswith('agent_'):
            name_groups['agent_system'].append(comp)
        elif name.startswith('session'):
            name_groups['session'].append(comp)
        elif 'template' in name:
            name_groups['template'].append(comp)
        elif 'trigger' in name:
            name_groups['trigger'].append(comp)
        elif 'logging' in name or 'logger' in name:
            name_groups['logging'].append(comp)
        elif 'config' in name:
            name_groups['config'].append(comp)
        elif name.endswith('_service'):
            name_groups['services'].append(comp)
        elif name.endswith('_manager'):
            name_groups['managers'].append(comp)
        elif name.endswith('_factory'):
            name_groups['factories'].append(comp)

    # Analyze groups for overlaps
    for group_name, group_comps in name_groups.items():
        if len(group_comps) >= 2:
            # Check if they're in different functional areas
            areas = set(c['Functional Area'] for c in group_comps)
            if len(areas) > 1:
                overlaps.append({
                    'type': 'naming_similarity',
                    'group': group_name,
                    'components': group_comps,
                    'areas': list(areas),
                    'severity': 'medium',
                    'description': f"{len(group_comps)} modules with '{group_name}' naming pattern across {len(areas)} functional areas"
                })

    return overlaps


def analyze_responsibility_overlaps(components: List[Dict]) -> List[Dict]:
    """Identify modules with potentially overlapping responsibilities based on purpose."""
    overlaps = []

    # Known overlap patterns from the initial audit
    known_overlaps = [
        {
            'type': 'session_management',
            'modules': ['session_service.py', 'service.py'],
            'areas': ['Session Management', 'Automation Orchestration'],
            'severity': 'high',
            'description': 'NoOpSessionService placeholder needs integration with real SessionService',
            'recommendation': 'Replace NoOpSessionService with real SessionService from domain layer'
        },
        {
            'type': 'template_infrastructure',
            'modules': ['template_cache.py', 'template_loader.py', 'template_registry.py', 'narrative_template_manager.py',
                       'template_renderer.py', 'state_service.py'],
            'areas': ['Template System', 'Template System'],
            'severity': 'low',
            'description': 'Template management spans application and infrastructure layers',
            'recommendation': 'Current separation is appropriate - automation handles orchestration, infrastructure handles rendering'
        },
        {
            'type': 'logging_multiple',
            'modules': ['logging.py', 'python_logging.py', 'agent_logging.py'],
            'areas': ['Shared', 'Logging & Telemetry'],
            'severity': 'low',
            'description': 'Multiple logging implementations for different purposes',
            'recommendation': 'Intentional specialization - shared for general, infrastructure for specialized services'
        },
        {
            'type': 'file_management',
            'modules': ['file_manager.py', 'file_access_service.py'],
            'areas': ['File System', 'File System'],
            'severity': 'low',
            'description': 'Multiple file management layers',
            'recommendation': 'Proper layer separation - file_manager for low-level ops, file_access_service for tiered loading'
        },
        {
            'type': 'agent_coordination',
            'modules': ['registry.py', 'agent_runner.py', 'agent_catalog.py', 'agent_coordinator.py', 'agent_executor.py'],
            'areas': ['Agent System'],
            'severity': 'medium',
            'description': 'Multiple agent coordination components - strategy-level vs individual-level',
            'recommendation': 'Ensure clear distinction: AgentRegistry/Runner for strategies, Catalog/Coordinator/Executor for individual agents'
        },
        {
            'type': 'tui_mockups',
            'modules': ['trigger_editor_enhanced_mockup.py', 'template_editor_mockup.py', 'trigger_editor_mockup.py'],
            'areas': ['TUI Presentation', 'WIP'],
            'severity': 'high',
            'description': 'TUI editor mockups not yet integrated',
            'recommendation': 'Extract and integrate mockup components following TUI_INTEGRATION_GUIDE.md'
        }
    ]

    overlaps.extend(known_overlaps)

    return overlaps


def analyze_functional_overlaps(components: List[Dict]) -> List[Dict]:
    """Identify functional areas with potential overlaps."""
    overlaps = []

    # Group by functional area
    areas = defaultdict(list)
    for comp in components:
        areas[comp['Functional Area']].append(comp)

    # Check for modules that might belong to multiple areas
    for comp in components:
        purpose = comp['Purpose'].lower() if comp['Purpose'] != 'N/A' else ''
        name = comp['Module Name'].lower()

        # Detect cross-cutting concerns
        if 'session' in name or 'session' in purpose:
            if comp['Functional Area'] not in ['Session Management']:
                overlaps.append({
                    'type': 'cross_cutting',
                    'module': comp['Module Path'],
                    'current_area': comp['Functional Area'],
                    'suggested_area': 'Session Management',
                    'severity': 'low',
                    'description': f"Module '{comp['Module Name']}' in {comp['Functional Area']} but appears session-related"
                })

    return overlaps


def generate_overlap_report(components: List[Dict], output_file: Path):
    """Generate comprehensive overlap analysis report."""

    naming_overlaps = analyze_naming_overlaps(components)
    responsibility_overlaps = analyze_responsibility_overlaps(components)
    functional_overlaps = analyze_functional_overlaps(components)

    content = """# Overlap Analysis Report

## Executive Summary

This report identifies areas of the codebase with overlapping responsibilities,
naming conflicts, and potential consolidation opportunities.

"""

    # Summary statistics
    total_overlaps = len(naming_overlaps) + len(responsibility_overlaps) + len(functional_overlaps)
    high_severity = sum(1 for o in responsibility_overlaps if o.get('severity') == 'high')
    medium_severity = sum(1 for o in naming_overlaps if o.get('severity') == 'medium') + \
                      sum(1 for o in responsibility_overlaps if o.get('severity') == 'medium')
    low_severity = sum(1 for o in responsibility_overlaps if o.get('severity') == 'low')

    content += f"""**Total Overlaps Identified:** {total_overlaps}
**High Severity:** {high_severity}
**Medium Severity:** {medium_severity}
**Low Severity:** {low_severity}

---

## 1. Responsibility Overlaps

These are known areas where multiple modules handle similar responsibilities.

"""

    for i, overlap in enumerate(responsibility_overlaps, 1):
        severity_icon = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }.get(overlap['severity'], '⚪')

        content += f"""### {i}. {overlap['type'].replace('_', ' ').title()} {severity_icon}

**Severity:** {overlap['severity'].upper()}
**Functional Areas:** {', '.join(overlap['areas'])}
**Modules Involved:**
"""
        for module in overlap['modules']:
            content += f"- `{module}`\n"

        content += f"""
**Description:** {overlap['description']}

**Recommendation:** {overlap['recommendation']}

---

"""

    content += """

## 2. Naming Pattern Overlaps

Modules with similar naming patterns that might indicate related functionality.

"""

    if naming_overlaps:
        for i, overlap in enumerate(naming_overlaps, 1):
            content += f"""### {i}. {overlap['group'].title()} Pattern

**Modules:** {len(overlap['components'])}
**Functional Areas:** {', '.join(overlap['areas'])}

**Components:**
"""
            for comp in overlap['components']:
                content += f"- `{Path(comp['Module Path']).name}` ({comp['Functional Area']})\n"

            content += f"""
**Analysis:** {overlap['description']}

---

"""
    else:
        content += "*No significant naming pattern overlaps detected.*\n"

    content += """

## 3. Cross-Cutting Concerns

Modules that appear in one functional area but might belong to another.

"""

    if functional_overlaps:
        for i, overlap in enumerate(functional_overlaps, 1):
            content += f"""### {i}. {Path(overlap['module']).name}

**Current Area:** {overlap['current_area']}
**Suggested Area:** {overlap['suggested_area']}
**Severity:** {overlap['severity']}

**Analysis:** {overlap['description']}

---

"""
    else:
        content += "*No cross-cutting concerns detected - functional areas are well-defined.*\n"

    content += """

## 4. Consolidation Opportunities

### High Priority (Action Required)

"""

    high_priority = [o for o in responsibility_overlaps if o.get('severity') == 'high']
    if high_priority:
        for overlap in high_priority:
            content += f"""#### {overlap['type'].replace('_', ' ').title()}

**Action:** {overlap['recommendation']}

**Modules to address:**
"""
            for module in overlap['modules']:
                matching = [c for c in components if module in c['Module Path']]
                if matching:
                    comp = matching[0]
                    content += f"- `{module}` ({int(comp['LOC Code'])} LOC, {comp['Functional Area']})\n"

            content += "\n"
    else:
        content += "*No high-priority consolidation needs identified.*\n"

    content += """

### Medium Priority (Consider for Future Refactoring)

"""

    medium_priority = [o for o in responsibility_overlaps if o.get('severity') == 'medium']
    if medium_priority:
        for overlap in medium_priority:
            content += f"""#### {overlap['type'].replace('_', ' ').title()}

**Consideration:** {overlap['recommendation']}

"""
    else:
        content += "*No medium-priority items.*\n"

    content += """

### Low Priority (Monitoring/Documentation)

"""

    low_priority = [o for o in responsibility_overlaps if o.get('severity') == 'low']
    if low_priority:
        for overlap in low_priority:
            content += f"- **{overlap['type'].replace('_', ' ').title()}:** {overlap['recommendation']}\n"
    else:
        content += "*No low-priority items.*\n"

    content += """

## 5. Agent System Analysis

The agent system has the most complex structure with 11 modules. Here's a detailed breakdown:

### Strategy-Level Components (Workstream D)
- `agent_runner.py` - Executes agent strategies sequentially
- `registry.py` - Loads and configures agent strategies

### Individual Agent Components (Workstream E)
- `agent_catalog.py` - Catalogs individual agents
- `agent_factory.py` - Creates agent instances
- `agent_executor.py` - Executes agents concurrently
- `agent_formatter.py` - Formats agent results
- `agent_coordinator.py` - Facade orchestrating pipeline

### Agent Strategies
- `immediate_agent_strategy.py` - Synchronous execution
- `background_agent_strategy.py` - Async post-response
- `fallback_trigger_strategy.py` - Legacy compatibility

### Recommendation

The current structure is appropriate but could benefit from:
1. **Better documentation** distinguishing strategy-level vs individual-level components
2. **Code comments** explaining the two-tier architecture
3. **Integration tests** validating the complete pipeline

## 6. Summary & Action Items

### Critical Actions
"""

    critical = [o for o in responsibility_overlaps if o.get('severity') == 'high']
    if critical:
        for i, overlap in enumerate(critical, 1):
            content += f"{i}. {overlap['recommendation']}\n"
    else:
        content += "*None - codebase is in good shape*\n"

    content += """

### Recommended Actions
"""

    recommended = [o for o in responsibility_overlaps if o.get('severity') == 'medium']
    if recommended:
        for i, overlap in enumerate(recommended, 1):
            content += f"{i}. {overlap['recommendation']}\n"
    else:
        content += "*None*\n"

    content += """

### Monitoring Points
"""

    monitoring = [o for o in responsibility_overlaps if o.get('severity') == 'low']
    if monitoring:
        for i, overlap in enumerate(monitoring, 1):
            content += f"{i}. Document and monitor: {overlap['type'].replace('_', ' ')}\n"
    else:
        content += "*None*\n"

    content += """

---

*Report generated from component inventory and manual analysis*
*Total components analyzed: """ + str(len(components)) + """*
"""

    # Write report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return output_file


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    csv_file = project_root / 'docs' / 'audit' / 'component_inventory.csv'
    output_file = project_root / 'docs' / 'audit' / 'OVERLAP_ANALYSIS.md'

    print("Loading component inventory...")
    components = load_inventory(csv_file)

    print("Analyzing overlaps...")
    report_file = generate_overlap_report(components, output_file)

    print(f"\n[SUCCESS] Overlap analysis report generated: {report_file}")
