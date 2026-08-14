
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_checker(report: Path, log: Path | None = None) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, "scripts/check_no_silent_skips.py", str(report)]
    if log:
        args += ["--log", str(log)]
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def test_clean_junit_is_accepted(tmp_path: Path) -> None:
    report = tmp_path / "clean.xml"
    report.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="x" name="ok"/></testsuite>', encoding="utf-8")
    assert run_checker(report).returncode == 0


def test_skipped_junit_is_rejected(tmp_path: Path) -> None:
    report = tmp_path / "skip.xml"
    report.write_text('<testsuite tests="1" failures="0" errors="0" skipped="1"><testcase classname="x" name="skip"><skipped message="no"/></testcase></testsuite>', encoding="utf-8")
    result = run_checker(report)
    assert result.returncode != 0
    assert "skipped" in result.stdout


def test_deselected_log_is_rejected(tmp_path: Path) -> None:
    report = tmp_path / "clean.xml"
    report.write_text('<testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="x" name="ok"/></testsuite>', encoding="utf-8")
    log = tmp_path / "run.log"
    log.write_text("1 passed, 2 deselected", encoding="utf-8")
    assert run_checker(report, log).returncode != 0


def test_xfail_and_collection_error_are_rejected(tmp_path: Path) -> None:
    report = tmp_path / "xfail.xml"
    report.write_text(
        '<testsuite tests="1" failures="0" errors="1" skipped="0">'
        '<testcase classname="x" name="broken"><error message="collection error"/></testcase>'
        '</testsuite>', encoding="utf-8"
    )
    log = tmp_path / "run.log"
    log.write_text("1 xfailed, 1 xpassed", encoding="utf-8")
    result = run_checker(report, log)
    assert result.returncode != 0
    assert "collection" in result.stdout
    assert "xfailed" in result.stdout
