from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "build/i02-artifacts"
OUT = ROOT / "provenance/iterations/I02/evidence/package-artifacts.json"

def main() -> int:
    items = []
    for path in sorted(ART.glob("*.whl")):
        items.append({"filename": path.name, "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if len(items) != 9: print(f"expected 9 package artifacts, found {len(items)}"); return 1
    OUT.write_bytes((json.dumps({"artifacts": items}, indent=2) + "\n").encode())
    print(f"package evidence: PASS ({len(items)} artifacts)"); return 0

if __name__ == "__main__": raise SystemExit(main())
