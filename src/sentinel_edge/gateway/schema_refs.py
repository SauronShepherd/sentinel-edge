"""Bounded offline schema-reference resolution."""
from __future__ import annotations

import re
from typing import Any


def resolve_schema_refs(document: dict[str, Any], *, max_depth: int = 8, max_nodes: int = 256) -> dict[str, Any]:
    nodes = 0
    root = document

    def walk(value: Any, depth: int) -> Any:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes or depth > max_depth:
            raise ValueError("schema reference bounds exceeded")
        if isinstance(value, list):
            return [walk(item, depth + 1) for item in value]
        if not isinstance(value, dict):
            return value
        ref = value.get("$ref")
        if ref is not None:
            if not isinstance(ref, str) or not ref.startswith("#/"):
                raise ValueError("external schema reference is not allowlisted")
            target: Any = root
            for part in ref[2:].split("/"):
                if not isinstance(target, dict) or part not in target:
                    raise ValueError("schema reference target is missing")
                target = target[part]
            return walk(target, depth + 1)
        result = {}
        for key, item in value.items():
            if key == "description" and isinstance(item, str):
                result[key] = re.sub(r"\s+", " ", item).strip()[:2048]
            else:
                result[key] = walk(item, depth + 1)
        return result

    return walk(document, 0)
