from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "release-candidate.json"


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"release_admitted": False, "failures": ["release_candidate_missing_or_invalid"]}, sort_keys=True))
        return 2
    admitted = payload.get("release_admitted") is True
    result = {
        "candidate_id": payload.get("candidate_id"),
        "release_profile": payload.get("release_profile"),
        "release_admitted": admitted,
        "admission_reason": payload.get("admission_reason"),
        "admission_blockers": payload.get("admission_blockers", []),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if admitted else 2


if __name__ == "__main__":
    raise SystemExit(main())
