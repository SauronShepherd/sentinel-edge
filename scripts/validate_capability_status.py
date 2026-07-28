from __future__ import annotations

from typing import Any

from _repo import ROOT, load_json, repo_path

STATES = {"planned", "active", "demonstrated", "retired"}


def validate_registry(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        return ["capabilities must be a list"]
    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for raw in capabilities:
        if not isinstance(raw, dict):
            errors.append("capability entry must be an object")
            continue
        cap_id = raw.get("id")
        if not isinstance(cap_id, str) or not cap_id:
            errors.append("capability id is required")
            continue
        if cap_id in ids:
            errors.append(f"duplicate capability: {cap_id}")
        ids.add(cap_id)
        by_id[cap_id] = raw
        state = raw.get("state")
        if state not in STATES:
            errors.append(f"{cap_id}: illegal state {state!r}")
        if not raw.get("owner"):
            errors.append(f"{cap_id}: owner is required")
        tests = raw.get("acceptance_tests", [])
        evidence = raw.get("evidence_paths", [])
        if state in {"active", "demonstrated"}:
            if not isinstance(tests, list) or not tests:
                errors.append(f"{cap_id}: {state} capability lacks acceptance tests")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{cap_id}: {state} capability lacks evidence paths")
            for value in tests if isinstance(tests, list) else []:
                if not isinstance(value, str) or not repo_path(value).is_file():
                    errors.append(f"{cap_id}: missing acceptance test {value!r}")
            for value in evidence if isinstance(evidence, list) else []:
                if not isinstance(value, str) or not repo_path(value).exists():
                    errors.append(f"{cap_id}: missing evidence path {value!r}")
    for cap_id, raw in by_id.items():
        deps = raw.get("depends_on", [])
        if not isinstance(deps, list):
            errors.append(f"{cap_id}: depends_on must be a list")
            continue
        for dep in deps:
            if dep not in by_id:
                errors.append(f"{cap_id}: unknown dependency {dep!r}")
    return errors


def legal_transition(old: str, new: str, evidence_current: bool = False) -> bool:
    if old == new:
        return True
    allowed = {
        "planned": {"active"},
        "active": {"demonstrated", "planned"},
        "demonstrated": {"active", "retired"},
        "retired": {"active"},
    }
    if new not in allowed.get(old, set()):
        return False
    return new != "demonstrated" or evidence_current


def main() -> int:
    errors = validate_registry(load_json(ROOT / "provenance/capability-status.yaml"))
    if errors:
        print("\n".join(errors))
        return 1
    print("capability registry: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
