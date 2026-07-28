from __future__ import annotations

import re
import sys
from pathlib import Path

LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def main() -> int:
    errors: list[str] = []
    roots = [Path(value) for value in sys.argv[1:]]
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for value in LINK.findall(text):
                if value.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = (path.parent / value.split("#", 1)[0]).resolve()
                if not target.exists():
                    errors.append(f"{path}:{value}: missing local link")
    if errors:
        print("\n".join(errors))
        return 1
    print("markdown links: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
