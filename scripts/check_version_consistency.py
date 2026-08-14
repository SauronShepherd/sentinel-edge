"""Check the single implementation version against package metadata."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentinel_edge.version import IMPLEMENTATION_VERSION  # noqa: E402


def main() -> int:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if not declared or declared.group(1) != IMPLEMENTATION_VERSION:
        print(f"version drift: pyproject={declared.group(1) if declared else None} source={IMPLEMENTATION_VERSION}")
        return 1
    print(f"implementation_version={IMPLEMENTATION_VERSION}; contract_version=0.22.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
