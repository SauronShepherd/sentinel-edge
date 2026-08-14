"""Validate lock metadata without contacting a package index."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    project = tomllib.loads((args.root / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((args.root / "uv.lock").read_text(encoding="utf-8"))
    expected = project["project"]["version"]
    package = next((item for item in lock.get("package", []) if item.get("name") == project["project"]["name"]), None)
    failures: list[str] = []
    if package is None:
        failures.append("project_package_missing_from_lock")
    elif package.get("version") != expected:
        failures.append(f"project_version_mismatch:{package.get('version')}!={expected}")
    normalize = lambda value: str(value).replace(" ", "")
    if normalize(lock.get("requires-python")) != normalize(project["project"]["requires-python"]):
        failures.append("requires_python_mismatch")

    release_lock_path = args.root / "requirements-release.lock.json"
    if release_lock_path.is_file():
        try:
            release_lock = json.loads(release_lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failures.append("release_lock_invalid_json")
        else:
            uv_sha256 = hashlib.sha256((args.root / "uv.lock").read_bytes()).hexdigest()
            if release_lock.get("resolution_kind") != "uv_lock_projection":
                failures.append("release_lock_not_uv_projection")
            if release_lock.get("project_version") != expected:
                failures.append("release_lock_project_version_mismatch")
            if release_lock.get("uv_lock_sha256") != uv_sha256:
                failures.append("release_lock_uv_binding_mismatch")
            if release_lock.get("complete") is not True:
                failures.append("release_lock_incomplete")
    else:
        failures.append("release_lock_missing")
    if failures:
        print("\n".join(failures))
        return 1
    print("offline lock metadata check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
