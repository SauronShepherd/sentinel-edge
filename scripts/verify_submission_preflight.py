from __future__ import annotations
import json
from sentinel_edge.release.submission import verify_submission_command_matrix


def main() -> int:
    result = verify_submission_command_matrix(".")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
