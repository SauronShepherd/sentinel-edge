from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sentinel_edge.release.submission import verify_submission_command_matrix


def main() -> int:
    result = verify_submission_command_matrix(".")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
