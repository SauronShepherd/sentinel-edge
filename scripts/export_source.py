"""Build a clean source export from explicit release-input classes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOW_ROOTS = (
    "apps", "architecture", "artifacts", "config", "contracts", "docker", "docs",
    "fixtures", "modules", "provenance", "qualification", "registries", "schemas",
    "sdk", "src", "scripts", "tests", ".github",
    "pyproject.toml", "uv.lock", "requirements-dev.lock.txt",
    "requirements-bootstrap.lock.txt", "requirements-release.lock.json",
    "package.json", "README.md", "CHANGELOG.md", "HACKATHON_WORKLOG.md",
    "LICENSE", "NOTICE", "SECURITY.md", "CONTRIBUTING.md",
    "THIRD_PARTY_NOTICES.md",
)
EXCLUDED_PARTS = {".git", ".idea", ".pytest_cache", "__pycache__", "build", "dist", ".venv", ".agents", ".codex"}


def allowed(path: Path, root: Path = ROOT) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in rel.parts):
        return False
    rel_parts = rel.parts
    return any(rel_parts == Path(root).parts or rel_parts[: len(Path(root).parts)] == Path(root).parts for root in ALLOW_ROOTS)


def source_files(root: Path = ROOT) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and allowed(p, root))


def artifact_class(path: Path, root: Path = ROOT) -> str:
    top = path.relative_to(root).parts[0]
    if top in {"qualification", "provenance"}:
        return "evidence-input"
    if top in {"artifacts"}:
        return "release-output"
    if top in {"contracts", "sdk"}:
        return "generated-contract"
    return "source"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.require_clean:
        try:
            status = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, text=True, stderr=subprocess.STDOUT)
        except (OSError, subprocess.CalledProcessError):
            print(json.dumps({"valid": False, "reason": "git_metadata_unavailable"}, indent=2))
            return 1
        if status.strip():
            print(json.dumps({"valid": False, "reason": "worktree_not_clean"}, indent=2))
            return 1
    destination = args.output.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    manifest = []
    for source in source_files(root):
        rel = source.relative_to(root)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        manifest.append({"path": str(rel).replace("\\", "/"), "class": artifact_class(source, root), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    (destination / "source-export-manifest.json").write_text(json.dumps({"schema": "sentinel-edge.source-export.v1", "files": manifest}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(manifest), "output": str(destination)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
