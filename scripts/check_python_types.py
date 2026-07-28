from __future__ import annotations

import ast
import sys
from pathlib import Path


def check(path: Path) -> list[str]:
    errors: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("test_") or node.name.startswith("_"):
            continue
        if node.returns is None:
            errors.append(f"{path}:{node.lineno}: public function {node.name} lacks return annotation")
        args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        for arg in args:
            if arg.arg in {"self", "cls"}:
                continue
            if arg.annotation is None:
                errors.append(f"{path}:{node.lineno}: parameter {arg.arg} of {node.name} lacks annotation")
    return errors


def main() -> int:
    roots = [Path(value) for value in sys.argv[1:]] or [Path("scripts"), Path("tests")]
    errors: list[str] = []
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
        for path in paths:
            if ".venv" not in path.parts:
                errors.extend(check(path))
    if errors:
        print("\n".join(errors))
        return 1
    print("static annotation gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
