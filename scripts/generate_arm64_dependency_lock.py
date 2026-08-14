from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "requirements-dev.lock.txt"
MANIFEST = ROOT / "config/arm64-python-artifacts.json"
OUTPUT = ROOT / "docker/requirements-arm64.lock.txt"


def render() -> str:
    base = BASE.read_text(encoding="utf-8").rstrip() + "\n"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema") != "sentinel-edge.arm64-python-artifacts.v1":
        raise ValueError("arm64_artifact_manifest_schema_mismatch")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("arm64_artifact_manifest_empty")
    existing = {
        re.match(r"^([A-Za-z0-9_.-]+)==", line).group(1).lower()
        for line in base.splitlines()
        if re.match(r"^([A-Za-z0-9_.-]+)==", line)
    }
    lines = [
        base.rstrip(),
        "",
        "# Arm64 inference-runtime additions. Artifact SHA-256 values are pinned in",
        "# config/arm64-python-artifacts.json and correspond to the canonical CPython",
        "# 3.13 / linux-aarch64 release artifacts. Docker installs this file with",
        "# --require-hashes --only-binary=:all: so source builds/substitution fail closed.",
    ]
    seen: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("arm64_artifact_manifest_entry_invalid")
        name = str(artifact.get("name", "")).lower()
        version = str(artifact.get("version", ""))
        sha256 = str(artifact.get("sha256", ""))
        filename = str(artifact.get("filename", ""))
        if not name or not version or not filename or not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise ValueError(f"arm64_artifact_manifest_entry_incomplete:{name or 'unknown'}")
        if name in seen or name in existing:
            raise ValueError(f"arm64_artifact_duplicate:{name}")
        seen.add(name)
        lines.extend([
            f"# artifact: {filename}",
            f"{name}=={version} \\",
            f"    --hash=sha256:{sha256}",
        ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("arm64 dependency lock: STALE")
            return 2
        print("arm64 dependency lock: PASS")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
