"""Validate the single source of truth for development and release commands."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z][a-z0-9-]*$")
REQUIRED = {"name", "profile", "purpose", "mutating", "execution_semantics", "empty_allowed"}
SEMANTICS = {"point_in_time", "revalidate_before_commit", "user_reconfirm"}
DOCUMENTED_COMMANDS = {
    "setup", "doctor", "verify", "format", "lint", "type", "governance", "architecture", "contracts",
    "plugins", "testkit", "components", "clients", "packages", "compatibility", "generated", "scenario",
    "security", "privacy", "accessibility", "benchmark", "benchmark-replay", "provenance", "docs", "claims",
    "aer", "report", "package", "backup-verify", "update-verify", "demo", "test-all", "gates",
}


def validate(root: Path) -> dict[str, object]:
    path = root / "architecture/command-catalog.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = payload.get("commands", [])
    failures: list[str] = []
    names: list[str] = []
    if payload.get("schema") != "sentinel-edge.command-catalog.v1":
        failures.append("invalid_schema")
    if payload.get("entrypoint") != "python scripts/dev.py":
        failures.append("invalid_entrypoint")
    if not isinstance(items, list) or not items:
        failures.append("commands_missing_or_empty")
        items = []
    for index, item in enumerate(items):
        prefix = f"item[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{prefix}:not_an_object")
            continue
        missing = REQUIRED - set(item)
        failures.extend(f"{prefix}:missing:{field}" for field in sorted(missing))
        name = item.get("name")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            failures.append(f"{prefix}:invalid_name")
        elif name in names:
            failures.append(f"duplicate_name:{name}")
        else:
            names.append(name)
        if not isinstance(item.get("purpose"), str) or not item.get("purpose", "").strip():
            failures.append(f"{prefix}:empty_purpose")
        if not isinstance(item.get("mutating"), bool):
            failures.append(f"{prefix}:invalid_mutating")
        if item.get("execution_semantics") not in SEMANTICS:
            failures.append(f"{prefix}:invalid_execution_semantics")
        if not isinstance(item.get("empty_allowed"), bool):
            failures.append(f"{prefix}:invalid_empty_allowed")
    source = (root / "scripts/dev.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    runtime_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Attribute):
            continue
        if not isinstance(node.left.value, ast.Name) or node.left.value.id != "args" or node.left.attr != "command":
            continue
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                runtime_names.append(comparator.value)
            elif isinstance(comparator, (ast.Set, ast.List, ast.Tuple)):
                runtime_names.extend(
                    element.value for element in comparator.elts
                    if isinstance(element, ast.Constant) and isinstance(element.value, str)
                )
    if sorted(names) != sorted(runtime_names):
        failures.append("catalog_runtime_command_mismatch")
    if not DOCUMENTED_COMMANDS.issubset(set(names)):
        failures.append("documented_command_missing:" + ",".join(sorted(DOCUMENTED_COMMANDS - set(names))))
    for documentation in (root / "README.md", root / "docs/judge-guide.md"):
        text = documentation.read_text(encoding="utf-8")
        missing = sorted(command for command in DOCUMENTED_COMMANDS if command not in text)
        if missing:
            failures.append(f"documentation_command_missing:{documentation.as_posix()}:{','.join(missing)}")
    return {"valid": not failures, "count": len(names), "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
