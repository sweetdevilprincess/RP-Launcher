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
        self.from_imports: List[Tuple[str, str, int]] = []
        self.functions: List[Tuple[str, int]] = []
        self.classes: List[Tuple[str, int]] = []
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
        if not node.name.startswith('_'):
            self.functions.append((node.name, node.lineno))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if not node.name.startswith('_'):
            self.classes.append((node.name, node.lineno))
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.names_used.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
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
        return None

def main():
    base_dir = Path("C:/Users/green/Desktop/RP Claude Code/refactoring/src")
    
    analyzers = {}
    for py_file in base_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        analyzer = analyze_file(py_file)
        if analyzer:
            analyzers[py_file] = analyzer
    
    print(f"Analyzed {len(analyzers)} files\n")
    print("="*80)
    print("UNUSED IMPORTS")
    print("="*80 + "\n")
    
    unused_count = 0
    for filepath, analyzer in sorted(analyzers.items()):
        unused_in_file = []
        
        # Check regular imports
        for import_name, lineno in analyzer.imports:
            base_name = import_name.split('.')[0]
            if base_name not in analyzer.names_used:
                unused_in_file.append((lineno, f"import {import_name}"))
        
        # Check from imports  
        for module, name, lineno in analyzer.from_imports:
            if name != '*' and name not in analyzer.names_used:
                unused_in_file.append((lineno, f"from {module} import {name}"))
        
        if unused_in_file:
            print(f"\n{filepath}")
            for lineno, import_stmt in sorted(unused_in_file):
                print(f"  Line {lineno}: {import_stmt}")
                unused_count += 1
    
    print(f"\n\nTotal unused imports: {unused_count}")

if __name__ == "__main__":
    main()
