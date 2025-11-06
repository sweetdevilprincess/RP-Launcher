"""Audit imports to enforce layer dependency rules during the refactor."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

INTERNAL_LAYERS = {"automation", "domain", "infrastructure", "shared", "tools"}

LAYER_RULES = {
    "automation": {"automation", "domain", "infrastructure", "shared"},
    "domain": {"domain", "infrastructure", "shared"},
    "infrastructure": {"infrastructure", "shared"},
    "shared": {"shared"},
    "tools": {"automation", "domain", "infrastructure", "shared", "tools"},
}


@dataclass
class ImportViolation:
    file: Path
    importer_layer: str
    imported_module: str
    imported_layer: str

    def format(self, base: Path) -> str:
        relative = self.file.relative_to(base)
        return (
            f"{relative}: {self.importer_layer} depends on "
            f"{self.imported_layer} via {self.imported_module}"
        )


def discover_python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        yield path


def infer_layer(root: Path, file_path: Path) -> str | None:
    try:
        relative = file_path.relative_to(root)
    except ValueError:
        return None
    parts = relative.parts
    if not parts:
        return None
    top_level = parts[0]
    return top_level if top_level in INTERNAL_LAYERS else None


def extract_imports(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
    elif isinstance(node, ast.ImportFrom):
        if node.level != 0 or not node.module:
            return
        yield node.module


def target_layer(module: str) -> str | None:
    top = module.split(".", 1)[0]
    return top if top in INTERNAL_LAYERS else None


def audit_file(root: Path, file_path: Path) -> list[ImportViolation]:
    layer = infer_layer(root, file_path)
    if layer is None:
        return []
    allowed = LAYER_RULES.get(layer)
    if allowed is None:
        return []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    violations: list[ImportViolation] = []
    for node in ast.walk(tree):
        for module in extract_imports(node):
            dep_layer = target_layer(module)
            if dep_layer is None or dep_layer in allowed:
                continue
            violations.append(
                ImportViolation(
                    file=file_path,
                    importer_layer=layer,
                    imported_module=module,
                    imported_layer=dep_layer,
                )
            )
    return violations


def audit(root: Path) -> list[ImportViolation]:
    violations: list[ImportViolation] = []
    for file_path in discover_python_files(root):
        violations.extend(audit_file(root, file_path))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Root package to audit (defaults to refactoring/src)",
    )
    args = parser.parse_args()
    root = args.path.resolve()
    violations = audit(root)
    if not violations:
        print("No dependency violations detected.")
        return 0
    print("Dependency violations detected:")
    for violation in violations:
        print(f" - {violation.format(root)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
