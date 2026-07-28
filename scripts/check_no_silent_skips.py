from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

FORBIDDEN_LOG_PATTERNS = {
    "deselected": re.compile(r"\b[1-9][0-9]* deselected\b", re.IGNORECASE),
    "xfailed": re.compile(r"\b[1-9][0-9]* xfailed\b", re.IGNORECASE),
    "xpassed": re.compile(r"\b[1-9][0-9]* xpassed\b", re.IGNORECASE),
    "rerun": re.compile(r"\b[1-9][0-9]* reruns?\b", re.IGNORECASE),
    "collection error": re.compile(r"error collecting|collection errors?", re.IGNORECASE),
}


def inspect_report(path: Path) -> list[str]:
    errors: list[str] = []
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    for suite in suites:
        skipped = int(suite.attrib.get("skipped", "0"))
        failures = int(suite.attrib.get("failures", "0"))
        errors_count = int(suite.attrib.get("errors", "0"))
        if skipped:
            errors.append(f"{path}: {skipped} skipped/xfail tests")
        if failures:
            errors.append(f"{path}: {failures} test failures")
        if errors_count:
            errors.append(f"{path}: {errors_count} test/collection errors")
    for case in root.iter("testcase"):
        for skipped_node in case.findall("skipped"):
            reason = skipped_node.attrib.get("message", "skipped")
            errors.append(f"{path}: {case.attrib.get('classname')}.{case.attrib.get('name')} is not executable: {reason}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+")
    parser.add_argument("--log", action="append", default=[])
    args = parser.parse_args()
    errors: list[str] = []
    for value in args.reports:
        errors.extend(inspect_report(Path(value)))
    for value in args.log:
        text = Path(value).read_text(encoding="utf-8", errors="replace")
        for name, pattern in FORBIDDEN_LOG_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{value}: forbidden result marker: {name}")
    if errors:
        print("\n".join(errors))
        return 1
    print("no-silent-skip gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
