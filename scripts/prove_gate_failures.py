
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"failure", "skip"}:
        print("usage: prove_gate_failures.py failure|skip")
        return 2
    mode = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        test = root / "test_controlled.py"
        if mode == "failure":
            test.write_text("def test_controlled_failure():\n    assert False, 'controlled gate proof'\n", encoding="utf-8")
        else:
            test.write_text("import pytest\n\ndef test_controlled_skip():\n    pytest.skip('controlled skip proof')\n", encoding="utf-8")
        report = root / "report.xml"
        log = root / "pytest.log"
        result = subprocess.run([sys.executable, "-m", "pytest", str(test), "-q", f"--junitxml={report}"], text=True, capture_output=True)
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        checker = subprocess.run([sys.executable, "scripts/check_no_silent_skips.py", str(report), "--log", str(log)], text=True, capture_output=True)
        if checker.returncode == 0:
            print(f"controlled {mode} did not block the gate")
            return 1
        print(f"controlled {mode} proof: PASS (gate correctly rejected the result)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
