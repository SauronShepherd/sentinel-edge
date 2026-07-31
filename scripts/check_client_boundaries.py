from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "modules" / "client-applications"
FORBIDDEN = re.compile(r"(?:node:fs|node:sqlite|sentinel_(?:incident|model|analysis|streaming|rest)|internal-transport)")

def main() -> int:
    errors = []
    for path in ROOT.rglob("*.ts"):
        if FORBIDDEN.search(path.read_text(encoding="utf-8")):
            errors.append(str(path.relative_to(ROOT)))
    if errors:
        print("forbidden client boundary references: " + ", ".join(errors)); return 1
    print("client boundary gate: PASS"); return 0

if __name__ == "__main__": raise SystemExit(main())
