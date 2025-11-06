"""Analyze codebase for dead/unused code."""
import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to collect definitions and usages."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.imports: List[Tuple[str, int]] = []
        self.from_imports: List[Tuple[str, str, int]] = []  # (module, name, lineno)
        self.functions: List[Tuple[str, int]] = []
        self.classes: List[Tuple[str, int]] = []
        self.globals: List[Tuple[str, int]] = []
        self.names_used: Set[str] = set()
        
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.append((name, node.lineno))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.from_imports.append((node.module or '', name, node.lineno))
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        if not node.name.startswith('_'):  # Skip private
            self.functions.append((node.name, node.lineno))
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        if not node.name.startswith('_'):
            self.functions.append((node.name, node.lineno))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if not node.name.startswith('_'):
            self.classes.append((node.name, node.lineno))
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        # Check for module-level assignments
        for target in node.targets:
            if isinstance(target, ast.Name) and not target.id.startswith('_'):
                self.globals.append((target.id, node.lineno))
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.names_used.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Track attribute access
        if isinstance(node.value, ast.Name):
            self.names_used.add(node.value.id)
        self.generic_visit(node)

def analyze_file(filepath: Path) -> CodeAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        analyzer = CodeAnalyzer(filepath)
        analyzer.visit(tree)
        return analyzer
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}", file=sys.stderr)
        return None

def main():
    """Analyze codebase."""
    base_dir = Path("src")
    
    # Collect all analyzers
    analyzers = {}
    for py_file in base_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        analyzer = analyze_file(py_file)
        if analyzer:
            analyzers[py_file] = analyzer
    
    print(f"Analyzed {len(analyzers)} files")
    print("\n" + "="*80)
    print("UNUSED IMPORTS ANALYSIS")
    print("="*80 + "\n")
    
    unused_imports = []
    for filepath, analyzer in analyzers.items():
        # Check regular imports
        for import_name, lineno in analyzer.imports:
            base_name = import_name.split('.')[0]
            if base_name not in analyzer.names_used:
                unused_imports.append((filepath, import_name, lineno))
        
        # Check from imports
        for module, name, lineno in analyzer.from_imports:
            if name != '*' and name not in analyzer.names_used:
                unused_imports.append((filepath, f"{module}.{name}", lineno))
    
    # Print unused imports
    if unused_imports:
        for filepath, name, lineno in sorted(unused_imports):
            rel_path = filepath.relative_to(Path.cwd())
            print(f"{rel_path}:{lineno} - Unused import: {name}")
    
    print(f"\nTotal unused imports: {len(unused_imports)}")

if __name__ == "__main__":
    main()
