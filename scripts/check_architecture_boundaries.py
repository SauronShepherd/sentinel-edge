from __future__ import annotations

import ast

from _repo import ROOT

FORBIDDEN_IMPLEMENTATION_PREFIXES = (
    "modules.streaming_source_collector",
    "modules.analysis_enrichment_engine",
    "modules.model_workload_runtime",
    "modules.incident_event_engine",
    "modules.rest_api_integration_gateway",
    "modules.client_applications",
)


def main() -> int:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in {".venv", "build"} for part in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.startswith(FORBIDDEN_IMPLEMENTATION_PREFIXES):
                    errors.append(f"{path.relative_to(ROOT)}:{node.lineno}: forbidden module implementation import {name}")
    source_docs = ROOT / "docs/baseline/v0.13.0"
    if not source_docs.is_dir():
        errors.append("immutable source baseline directory is missing")
    if errors:
        print("\n".join(errors))
        return 1
    print("architecture boundary gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
