"""Comprehensive dead code analysis."""
import ast
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

class DefinitionCollector(ast.NodeVisitor):
    """Collect all definitions in a file."""
    def __init__(self):
        self.functions = {}  # name -> lineno
        self.classes = {}    # name -> lineno
        
    def visit_FunctionDef(self, node):
        if not node.name.startswith('_'):
            self.functions[node.name] = node.lineno
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if not node.name.startswith('_'):
            self.classes[node.name] = node.lineno
        self.generic_visit(node)

class UsageCollector(ast.NodeVisitor):
    """Collect all name usages."""
    def __init__(self):
        self.used_names = set()
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Also collect from attribute access
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

def analyze_definitions():
    """Analyze all function/class definitions and their usage."""
    base = Path("C:/Users/green/Desktop/RP Claude Code/refactoring/src")
    
    # Collect all definitions across codebase
    all_functions = defaultdict(list)  # name -> [(file, lineno), ...]
    all_classes = defaultdict(list)
    all_used_names = set()
    
    files_analyzed = 0
    for py_file in base.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            # Collect definitions
            def_collector = DefinitionCollector()
            def_collector.visit(tree)
            
            for name, lineno in def_collector.functions.items():
                all_functions[name].append((py_file, lineno))
            for name, lineno in def_collector.classes.items():
                all_classes[name].append((py_file, lineno))
            
            # Collect usages
            usage_collector = UsageCollector()
            usage_collector.visit(tree)
            all_used_names.update(usage_collector.used_names)
            
            files_analyzed += 1
        except Exception as e:
            pass
    
    print(f"Analyzed {files_analyzed} files\n")
    
    # Find unused functions
    print("="*80)
    print("POTENTIALLY UNUSED FUNCTIONS")
    print("="*80)
    unused_funcs = []
    for name, locations in all_functions.items():
        if name not in all_used_names and len(locations) == 1:
            unused_funcs.append((name, locations[0]))
    
    for name, (filepath, lineno) in sorted(unused_funcs, key=lambda x: str(x[1][0])):
        print(f"{filepath}:{lineno} - Function '{name}' not used")
    print(f"\nTotal: {len(unused_funcs)}")
    
    # Find unused classes
    print("\n" + "="*80)
    print("POTENTIALLY UNUSED CLASSES")
    print("="*80)
    unused_classes = []
    for name, locations in all_classes.items():
        if name not in all_used_names and len(locations) == 1:
            unused_classes.append((name, locations[0]))
    
    for name, (filepath, lineno) in sorted(unused_classes, key=lambda x: str(x[1][0])):
        print(f"{filepath}:{lineno} - Class '{name}' not used")
    print(f"\nTotal: {len(unused_classes)}")

if __name__ == "__main__":
    analyze_definitions()
