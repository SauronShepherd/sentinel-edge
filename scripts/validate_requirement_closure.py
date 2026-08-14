"""Fail-closed validation for requirement verification claims."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    requirements = yaml.safe_load((root / "registries/requirements.yaml").read_text(encoding="utf-8"))["items"]
    evidence = {item["id"]: item for item in yaml.safe_load((root / "registries/evidence.yaml").read_text(encoding="utf-8"))["items"]}
    failures: list[str] = []
    for requirement in requirements:
        if requirement.get("status") != "VERIFIED":
            continue
        rid = requirement.get("id")
        evidence_ids = requirement.get("verification_evidence_ids", [])
        test_ids = requirement.get("verification_test_ids", [])
        execution_id = requirement.get("completion_execution_id")
        if not evidence_ids or not test_ids or not execution_id:
            failures.append(f"verified_missing_receipt_fields:{rid}")
        for evidence_id in evidence_ids:
            record = evidence.get(evidence_id)
            if not record:
                failures.append(f"verified_evidence_missing:{rid}:{evidence_id}")
                continue
            if record.get("status") != "ACTIVE":
                failures.append(f"verified_evidence_not_active:{rid}:{evidence_id}")
            digest = str(record.get("sha256", ""))
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                failures.append(f"verified_evidence_invalid_digest:{rid}:{evidence_id}")
            path = (root / str(record.get("path", ""))).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                failures.append(f"verified_evidence_path_outside_root:{rid}:{evidence_id}")
                continue
            if not path.is_file():
                failures.append(f"verified_evidence_file_missing:{rid}:{evidence_id}")
                continue
            if digest != hashlib.sha256(path.read_bytes()).hexdigest():
                failures.append(f"verified_evidence_digest_mismatch:{rid}:{evidence_id}")
    print("requirement closure: PASS" if not failures else "\n".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
