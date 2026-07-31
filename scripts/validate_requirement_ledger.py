from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"OPEN", "IMPLEMENTED_UNVERIFIED", "VERIFIED", "SUPERSEDED"}

def main() -> int:
    ledger = ROOT / "provenance/requirements/i00-i02-ledger.yaml"
    if not ledger.is_file(): print("missing requirement ledger"); return 1
    text = ledger.read_text(encoding="utf-8")
    ids = re.findall(r"^\s*- id: (I\d{2}-S\d{2}-T\d{2})\s*$", text, re.MULTILINE)
    errors = []
    if len(ids) != 73: errors.append(f"expected 73 tasks, found {len(ids)}")
    if len(ids) != len(set(ids)): errors.append("duplicate task id")
    for status in re.findall(r"^\s+status: (\S+)", text, re.MULTILINE):
        if status not in ALLOWED: errors.append(f"invalid status: {status}")
    if errors: print("\n".join(errors)); return 1
    print(f"requirement ledger: PASS ({len(ids)} tasks)"); return 0

if __name__ == "__main__": raise SystemExit(main())
