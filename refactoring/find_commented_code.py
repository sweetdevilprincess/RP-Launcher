"""Find commented-out code blocks."""
from pathlib import Path
import re

def find_commented_code():
    """Find blocks of commented code."""
    base = Path("C:/Users/green/Desktop/RP Claude Code/refactoring/src")
    
    findings = []
    
    # Patterns that suggest commented code (not documentation)
    code_patterns = [
        r'#\s*(def |class |import |from |if |for |while |return |self\.)',
        r'#\s*\w+\s*=\s*',  # Assignments
        r'#\s*\w+\(.*\)',    # Function calls
    ]
    
    for py_file in base.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Skip empty comments and docstrings
                if not stripped or stripped == '#' or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                
                # Check if line matches code patterns
                for pattern in code_patterns:
                    if re.search(pattern, stripped):
                        # Check if this is part of a larger block
                        block_size = 1
                        j = i
                        while j < len(lines) and lines[j].strip().startswith('#'):
                            block_size += 1
                            j += 1
                        
                        if block_size >= 3:  # Only report blocks of 3+ lines
                            findings.append((py_file, i, block_size, stripped[:80]))
                        break
        except Exception as e:
            pass
    
    return findings

if __name__ == "__main__":
    findings = find_commented_code()
    
    print("="*80)
    print("COMMENTED-OUT CODE BLOCKS (3+ lines)")
    print("="*80 + "\n")
    
    # Group by file
    by_file = {}
    for filepath, lineno, size, sample in findings:
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append((lineno, size, sample))
    
    for filepath in sorted(by_file.keys()):
        print(f"\n{filepath}")
        for lineno, size, sample in by_file[filepath]:
            print(f"  Line {lineno}: {size} lines - {sample}")
    
    print(f"\n\nTotal: {len(findings)} commented code blocks")
