from fastapi.testclient import TestClient

from sentinel_edge.gateway import create_app


def test_mission_control_uix_exposes_required_h0_truth_and_proof_surfaces(viewer_headers: dict[str, str]) -> None:
    client = TestClient(create_app())
    page = client.get("/client").text
    css = client.get("/client/styles.css").text
    script = client.get("/client/app.js").text

    assert "Arm64 emulated demonstration environment" in page
    assert "deterministic simulations" in page
    assert "Research MVP" in page
    assert "Raspberry Pi 5" in page
    assert "physical Raspberry Pi measurements" in page
    assert all(label in script for label in ("Wildfire", "Earthquake", "Flood", "Landslide"))
    assert "Monitoring Coverage" in script
    assert "Arm AI Orchestrator" in script
    assert "Why state changed" in script
    assert "Evidence" in script and "Uncertainty" in script and "Review actions" in script
    assert "Benchmark Lab" in script and "Judge Proof" in script
    assert "Collaborative Detection" in script and "Default OFF" in script
    assert "privacy-preserving pseudonymous sharing" in script
    assert "exactly six" in script.lower()

    assert "--sidebar-w:244px" in css
    assert "--topbar-h: 68px" in css
    assert "--inspector-w: 324px" in css
    assert "#1769ff" in css.lower()
    assert "#12a66a" in css.lower()
    assert "#e5484d" in css.lower()
    assert "@media(max-width:900px)" in css
    assert "@media(max-width:640px)" in css

    benchmark = client.get("/v1/benchmark/summary", headers=viewer_headers)
    assert benchmark.status_code == 200
    body = benchmark.json()
    assert body["claim_class"] == "simulated"
    assert body["environment"]["guest_architecture"] == "aarch64"
    assert body["variants"]["B0"]["median_end_to_end_ms"] == 111.5
    assert body["variants"]["O1"]["median_end_to_end_ms"] == 69.0
    assert body["quality_guardrails_passed"] is True

    proof = client.get("/v1/judge-proof", headers=viewer_headers)
    assert proof.status_code == 200
    proof_body = proof.json()
    assert len(proof_body["gates"]) == 12
    assert proof_body["physical_hardware_required"] is False
    assert proof_body["physical_sensors_required"] is False
    assert proof_body["architecture"]["top_level_component_count"] == 6
    assert proof_body["architecture"]["hazard_adapter_count"] == 4
