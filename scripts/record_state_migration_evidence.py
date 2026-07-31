from __future__ import annotations
import json
import tempfile
from pathlib import Path

def migrate(state: dict) -> dict:
    if state.get("schema") == 1:
        return {"schema": 2, "sequence": state["sequence"], "reconciled": True}
    if state.get("schema") != 2: raise ValueError("unsupported state schema")
    return state

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sentinel-owned-state-") as directory:
        path = Path(directory) / "owned-state.json"
        path.write_text(json.dumps({"schema": 1, "sequence": 7}), encoding="utf-8")
        upgraded = migrate(json.loads(path.read_text(encoding="utf-8")))
        path.write_text(json.dumps(upgraded), encoding="utf-8")
        restored = json.loads(path.read_text(encoding="utf-8"))
        if restored != {"schema": 2, "sequence": 7, "reconciled": True}: return 1
    print("owned-state migration: PASS")
    return 0

if __name__ == "__main__": raise SystemExit(main())
