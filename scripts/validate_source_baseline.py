from __future__ import annotations

import re

from _repo import ROOT, load_json, sha256_file


def main() -> int:
    base = ROOT / "docs/baseline/v0.13.0"
    manifest = load_json(base / "manifest.json")
    errors: list[str] = []
    for item in manifest.get("documents", []):
        path = base / item["file"]
        if not path.is_file():
            errors.append(f"missing baseline file: {item['file']}")
            continue
        if path.stat().st_size != item["bytes"]:
            errors.append(f"byte mismatch: {item['file']}")
        if sha256_file(path) != item["sha256"]:
            errors.append(f"hash mismatch: {item['file']}")
    expected = {item["file"] for item in manifest["documents"] if item["file"] != "README.md"}
    index_text = (ROOT / "docs/architecture/source-baseline-v0.13.0.md").read_text(encoding="utf-8")
    indexed = set(re.findall(r"\| `([^`]+\.md)` \| `[a-f0-9]{64}` \|", index_text))
    if expected != indexed:
        errors.append(f"baseline index mismatch: missing={sorted(expected-indexed)} extra={sorted(indexed-expected)}")
    if len(expected) != 14:
        errors.append(f"expected 14 source specifications, found {len(expected)}")
    if errors:
        print("\n".join(errors))
        return 1
    print("source baseline: PASS (14 specifications, all hashes valid)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
