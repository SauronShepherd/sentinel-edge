from __future__ import annotations
import json
from pathlib import Path

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
    return errors

def check_paths(old_path: Path, new_path: Path) -> list[str]:
    return compare(json.loads(old_path.read_text()), json.loads(new_path.read_text()))
