from __future__ import annotations

from _repo import ROOT


def main() -> int:
    required = {
        "ci-fast.yml": ["make setup", "make format-check", "make lint", "make type", "make architecture", "make governance"],
        "ci-full.yml": ["make gates", "if: always()", "upload-artifact"],
        "ci-arm.yml": ["planned", "make test-arm"],
    }
    errors: list[str] = []
    for name, tokens in required.items():
        path = ROOT / ".github/workflows" / name
        if not path.is_file():
            errors.append(f"missing workflow: {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"{name}: missing {token!r}")
    full = (ROOT / ".github/workflows/ci-full.yml").read_text(encoding="utf-8")
    if "needs: [full-gate]" not in full:
        errors.append("ci-full.yml: aggregate job must depend on full-gate")
    if errors:
        print("\n".join(errors))
        return 1
    print("CI workflow contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
