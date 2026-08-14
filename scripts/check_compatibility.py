from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def compare(old: dict, new: dict) -> list[str]:
    errors: list[str] = []
    old_required = set(old.get("required", [])); new_required = set(new.get("required", []))
    for field in sorted(old_required - new_required): errors.append(f"removed required field: {field}")
    for field, spec in old.get("properties", {}).items():
        if field not in new.get("properties", {}): continue
        current = new["properties"][field]
        if spec.get("type") != current.get("type"): errors.append(f"changed field type: {field}")
        if set(current.get("enum", spec.get("enum", []))) < set(spec.get("enum", [])): errors.append(f"narrowed enum: {field}")
        old_nullable = spec.get("nullable", "null" in spec.get("type", []) if isinstance(spec.get("type"), list) else False)
        new_nullable = current.get("nullable", "null" in current.get("type", []) if isinstance(current.get("type"), list) else False)
        if old_nullable and not new_nullable: errors.append(f"narrowed nullability: {field}")
        if spec.get("items", {}).get("type") != current.get("items", {}).get("type") and "items" in spec: errors.append(f"changed array item type: {field}")
        for semantic_key, label in (("x-unit", "unit"), ("x-identity", "identity"), ("x-meaning", "meaning")):
            if semantic_key in spec and spec.get(semantic_key) != current.get(semantic_key):
                errors.append(f"changed field {label}: {field}")
    return errors

def check_paths(old_path: Path, new_path: Path) -> list[str]:
    return compare(json.loads(old_path.read_text()), json.loads(new_path.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    policy = yaml.safe_load((root / "contracts/compatibility-matrix/current-n-1.yaml").read_text(encoding="utf-8")) or {}
    failures: list[str] = []
    if policy.get("policy") != "additive-only":
        failures.append("compatibility_policy_not_additive_only")
    required = {"remove-required-field", "change-field-identity", "change-field-type"}
    if not required.issubset(set(policy.get("prohibited", []))):
        failures.append("compatibility_policy_missing_prohibited_changes")
    schemas = sorted((root / "contracts/sentinel-contracts/schemas").glob("*.json"))
    if not schemas:
        failures.append("compatibility_schema_set_empty")
    for path in schemas:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(f"invalid_schema:{path.name}")
            continue
        if not isinstance(payload.get("properties"), dict):
            failures.append(f"schema_properties_missing:{path.name}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"compatibility check: PASS ({len(schemas)} schemas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
