from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def pytest_available(python: Path) -> bool:
    if not python.exists():
        return False
    result = subprocess.run(
        [str(python), "-c", "import pytest; assert int(pytest.__version__.split('.')[0]) >= 9"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv", default=".venv")
    args = parser.parse_args()
    target = Path(args.venv)
    python = target / "bin" / "python"
    base_python = Path(sys.executable).resolve()

    if not pytest_available(base_python):
        print("pytest >= 9 is required before bootstrap; CI provisions the pinned runner first")
        return 1

    if not pytest_available(python):
        if target.exists():
            shutil.rmtree(target)
        (target / "bin").mkdir(parents=True)
        python.write_text(f"#!/usr/bin/env bash\nexec {base_python} \"$@\"\n", encoding="utf-8")
        python.chmod(0o755)
        (target / "bin" / "python3").symlink_to("python")
        (target / "bin" / "python3.13").symlink_to("python")

    subprocess.run([str(python), "-m", "compileall", "-q", "scripts", "tests"], check=True)
    print(f"verified development interpreter shim: {python} -> {base_python}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
