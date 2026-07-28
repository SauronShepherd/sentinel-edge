from __future__ import annotations

import argparse
import json
from pathlib import Path

from _repo import ROOT, repo_path, sha256_file

REQUIRED = {
    "ADR-0001-modular-monolith-distributed-capable.md": ["Status: Accepted", "six bounded modules", "Module 04", "Module 05"],
    "ADR-0002-task-stage-iteration-workflow.md": ["Status: Accepted", "one primary file", "complete iteration gate"],
    "ADR-0003-no-silent-test-skips.md": ["Status: Accepted", "skipped", "xfail", "full gate"],
    "ADR-0004-default-implementation-profile.md": ["Status: Accepted", "Linux Arm64", "SQLite", "PWA", "mobile"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    errors: list[str] = []
    records: list[dict[str, object]] = []
    for name, tokens in REQUIRED.items():
        path = ROOT / "docs/adr" / name
        if not path.is_file():
            errors.append(f"missing ADR: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        missing = [token for token in tokens if token.lower() not in text.lower()]
        if missing:
            errors.append(f"{name}: missing required decisions {missing}")
        records.append({"file": str(path.relative_to(ROOT)), "sha256": sha256_file(path), "required_tokens": tokens})
    if errors:
        print("\n".join(errors))
        return 1
    report = {"schema_version": 1, "status": "passed", "adrs": records}
    if args.output:
        target = repo_path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("ADR validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
