from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.run_test_all import batches


ROOT = Path(__file__).resolve().parents[1]


def _run_batch(tmp_path: Path, body: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    test_file = tmp_path / "test_probe.py"
    test_file.write_text(body, encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    result = subprocess.run(
        [sys.executable, "scripts/run_pytest_acceptance_batch.py", "--receipt", str(receipt), str(test_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    return result, payload


def test_batches_are_bounded_and_lossless() -> None:
    items = [Path(f"test-{index}.py") for index in range(5)]
    grouped = batches(items, 2)
    assert grouped == [items[0:2], items[2:4], items[4:5]]


def test_acceptance_batch_receipt_records_duration_and_nonzero_collection(tmp_path: Path) -> None:
    result, payload = _run_batch(tmp_path, "def test_ok():\n    assert True\n")
    assert result.returncode == 0
    assert payload["valid"] is True
    assert payload["collected"] == 1
    assert payload["duration_seconds"] >= 0
    assert payload["skipped"] == []
    assert payload["xfail_or_xpass"] == []



def test_acceptance_batch_does_not_hang_on_leaked_non_daemon_test_thread(tmp_path: Path) -> None:
    test_file = tmp_path / "test_thread_probe.py"
    test_file.write_text(
        "import threading\nimport time\n\ndef test_leaked_thread():\n"
        "    threading.Thread(target=lambda: time.sleep(30), daemon=False).start()\n"
        "    assert True\n",
        encoding="utf-8",
    )
    receipt = tmp_path / "thread-receipt.json"
    result = subprocess.run(
        [sys.executable, "scripts/run_pytest_acceptance_batch.py", "--receipt", str(receipt), str(test_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert payload["valid"] is True
    assert payload["collected"] == 1

def test_acceptance_batch_rejects_skip_as_release_evidence(tmp_path: Path) -> None:
    result, payload = _run_batch(
        tmp_path,
        "import pytest\n\n@pytest.mark.skip(reason='probe')\ndef test_skip():\n    pass\n",
    )
    assert result.returncode != 0
    assert payload["valid"] is False
    assert payload["collected"] == 1
    assert payload["skipped"]


def test_acceptance_batch_receipt_binds_resume_identity(tmp_path: Path) -> None:
    test_file = tmp_path / "test_probe_metadata.py"
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    receipt = tmp_path / "metadata-receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_pytest_acceptance_batch.py",
            "--receipt", str(receipt),
            "--source-tree-digest", "source-digest",
            "--environment-digest", "environment-digest",
            "--batch-signature", "batch-signature",
            "--batch-index", "7",
            str(test_file),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert payload["source_tree_digest"] == "source-digest"
    assert payload["environment_digest"] == "environment-digest"
    assert payload["batch_signature"] == "batch-signature"
    assert payload["batch_index"] == 7


def test_resume_receipt_reuse_is_fail_closed(tmp_path: Path) -> None:
    from scripts.run_test_all import _valid_reusable_receipt

    receipt = tmp_path / "receipt.json"
    payload = {
        "valid": True,
        "paths": ["tests/test_a.py"],
        "source_tree_digest": "source",
        "environment_digest": "environment",
        "batch_signature": "signature",
        "collected": 2,
        "skipped": [],
        "xfail_or_xpass": [],
        "failed": [],
    }
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    assert _valid_reusable_receipt(
        receipt,
        source_digest="source",
        environment_digest="environment",
        signature="signature",
        paths=["tests/test_a.py"],
    ) == payload
    assert _valid_reusable_receipt(
        receipt,
        source_digest="changed",
        environment_digest="environment",
        signature="signature",
        paths=["tests/test_a.py"],
    ) is None
    payload["skipped"] = ["tests/test_a.py::test_skip"]
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    assert _valid_reusable_receipt(
        receipt,
        source_digest="source",
        environment_digest="environment",
        signature="signature",
        paths=["tests/test_a.py"],
    ) is None
