from __future__ import annotations

from typing import Any

from sentinel_edge.qualification import KnownAnswerCase, KnownAnswerSuite, run_known_answer_suite


class Session:
    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        value = float(inputs["value"])
        branch = "positive" if value >= 0 else "negative"
        return {"score": 1.0 if branch == "positive" else 0.0, "branch": branch}


def suite() -> KnownAnswerSuite:
    return KnownAnswerSuite(
        suite_id="seismic-kat-v1",
        model_graph_sha256="a" * 64,
        runtime_profile_sha256="b" * 64,
        required_branches=("positive", "negative"),
        cases=(
            KnownAnswerCase(case_id="positive", branch_id="positive", inputs={"value": 1}, expected_outputs={"score": 1.0, "branch": "positive"}),
            KnownAnswerCase(case_id="negative", branch_id="negative", inputs={"value": -1}, expected_outputs={"score": 0.0, "branch": "negative"}),
        ),
    )


def test_known_answer_passes_development_but_not_target() -> None:
    report = run_known_answer_suite(suite(), Session, target_host_qualified=False, target_runtime_qualified=False)
    assert report["development_passed"] is True
    assert report["service_start_allowed"] is True
    assert report["target_qualified"] is False
    assert report["state"] == "tested"


def test_initialization_failure_blocks_service() -> None:
    def broken() -> None:
        raise RuntimeError("boom")
    report = run_known_answer_suite(suite(), broken, target_host_qualified=True, target_runtime_qualified=True)
    assert report["service_start_allowed"] is False
    assert any(value.startswith("session_initialization_failed") for value in report["failures"])


def test_wrong_output_or_missing_branch_fails() -> None:
    class Wrong:
        def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
            return {"score": 99.0, "branch": "positive"}
    report = run_known_answer_suite(suite(), Wrong, target_host_qualified=True, target_runtime_qualified=True)
    assert report["development_passed"] is False
    assert "required_branch_not_covered:negative" in report["failures"]
    assert any("known_answer_mismatch" in value for value in report["failures"])
