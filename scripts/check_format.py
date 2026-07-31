from __future__ import annotations

from _repo import ROOT

TEXT_SUFFIXES = {".py", ".pyi", ".md", ".toml", ".yaml", ".yml", ".json", ".jsonl", ".txt"}
IGNORED = {".git", ".venv", ".idea", "build", "dist", ".pytest_cache", "node_modules", ".egg-info"}


def main() -> int:
    errors: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in IGNORED or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.name not in {"Makefile", ".editorconfig", ".gitignore"} and path.suffix not in TEXT_SUFFIXES:
            continue
        raw = path.read_bytes()
        rel = path.relative_to(ROOT)
        if b"\r" in raw:
            errors.append(f"{rel}: non-LF line ending")
        if raw and not raw.endswith(b"\n"):
            errors.append(f"{rel}: missing final newline")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: not UTF-8")
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if line.rstrip(" \t") != line and path.suffix != ".md":
                errors.append(f"{rel}:{number}: trailing whitespace")
    if errors:
        print("\n".join(errors))
        return 1
    print("format check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
