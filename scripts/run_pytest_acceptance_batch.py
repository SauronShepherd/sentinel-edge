from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest


class AcceptancePlugin:
    def __init__(self) -> None:
        self.collected = 0
        self.skipped: set[str] = set()
        self.xfail_or_xpass: set[str] = set()
        self.failed: set[str] = set()

    def pytest_collection_modifyitems(self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]) -> None:
        self.collected = len(items)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.skipped:
            self.skipped.add(report.nodeid)
        if getattr(report, "wasxfail", None):
            self.xfail_or_xpass.add(report.nodeid)
        if report.failed:
            self.failed.add(report.nodeid)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        # The H0 acceptance contract is fail-closed: a mandatory lane may not
        # silently collect zero tests or hide an unexpected skip/xfail/xpass.
        if self.collected == 0 or self.skipped or self.xfail_or_xpass:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one strict Sentinel Edge acceptance-test batch")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--source-tree-digest")
    parser.add_argument("--environment-digest")
    parser.add_argument("--batch-signature")
    parser.add_argument("--batch-index", type=int)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    plugin = AcceptancePlugin()
    started = time.monotonic()
    exit_code = int(pytest.main(["-q", *args.paths], plugins=[plugin]))
    duration_seconds = round(time.monotonic() - started, 3)
    receipt: dict[str, Any] = {
        "schema": "sentinel-edge.acceptance-test-batch.v1",
        "paths": args.paths,
        "source_tree_digest": args.source_tree_digest,
        "environment_digest": args.environment_digest,
        "batch_signature": args.batch_signature,
        "batch_index": args.batch_index,
        "collected": plugin.collected,
        "failed": sorted(plugin.failed),
        "skipped": sorted(plugin.skipped),
        "xfail_or_xpass": sorted(plugin.xfail_or_xpass),
        "exit_code": exit_code,
        "duration_seconds": duration_seconds,
        "valid": exit_code == 0 and plugin.collected > 0 and not plugin.skipped and not plugin.xfail_or_xpass,
    }
    target = Path(args.receipt)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if plugin.collected == 0:
        print("acceptance batch: FAIL (zero tests collected)")
    if plugin.skipped or plugin.xfail_or_xpass:
        print(f"acceptance batch: FAIL (skipped={len(plugin.skipped)}, xfail/xpass={len(plugin.xfail_or_xpass)})")
    return exit_code


if __name__ == "__main__":
    # This runner is intentionally an isolated subprocess. Some integration
    # tests exercise worker/thread recovery and can leave a non-daemon helper
    # alive after pytest has produced a complete result. Waiting for such a
    # helper would deadlock the canonical `test-all` command even though the
    # acceptance receipt is already final. Flush output and terminate the batch
    # worker explicitly after the receipt is written.
    code = int(main())
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
