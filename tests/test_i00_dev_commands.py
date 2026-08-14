from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_dev_command_surface_contains_no_silent_skips_lane() -> None:
    text = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    assert '"no-silent-skips"' in text
    assert "check_no_silent_skips.py" in text


def test_dev_command_surface_contains_judge_commands() -> None:
    text = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    for command in ("verify", "doctor", "demo", "scenario", "benchmark", "benchmark-replay", "claims", "aer"):
        assert f'"{command}"' in text


def test_arm_lane_is_a_deterministic_doctor_preflight() -> None:
    text = Path("scripts/dev.py").read_text(encoding="utf-8")
    assert '"test-arm"' in text
    assert '"sentinel_edge.cli", "doctor"' in text
    assert "not benchmark evidence" in text


def test_doctor_distinguishes_target_host_and_physical_signal_evidence() -> None:
    text = Path("src/sentinel_edge/cli.py").read_text(encoding="utf-8")
    assert "native_arm64_linux_observed" in text
    assert "physical_signal_evidence_available" in text
    assert "target_qualification_blockers" in text

def test_doctor_exposes_emulated_hackathon_profile() -> None:
    result = subprocess.run([sys.executable, "-m", "sentinel_edge.cli", "doctor"], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["hackathon_release_profile"] == "H0-EMULATED-AARCH64-20260813"
    assert payload["physical_sensors_required_for_hackathon_profile"] is False
    assert payload["sensor_input_mode"] == "deterministic_simulated_or_fixture"


def test_scenario_command_is_repeatable(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    fixture = ROOT / "fixtures/scenarios/simultaneous-event.json"
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-m", "sentinel_edge.cli", "run-scenario", str(fixture), "--state-dir", str(state_dir)],
            cwd=ROOT,
            env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_no_silent_skips_lane_does_not_short_circuit() -> None:
    text = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    assert "pytest_result = run" in text
    assert "skip_result = run" in text


def test_mandatory_test_lane_rejects_zero_tests() -> None:
    from scripts import dev
    with pytest.raises(ValueError, match="cannot be empty"):
        dev.mandatory_test_command([])


def test_verify_and_gates_include_identity_and_hygiene_checks() -> None:
    text = (ROOT / "scripts/dev.py").read_text(encoding="utf-8")
    for check in (
        "check_version_consistency.py",
        "check_lock_metadata.py",
        "check_contract_sync.py",
        "validate_capability_status.py",
        "repository_hygiene.py",
    ):
        assert text.count(check) >= 2
