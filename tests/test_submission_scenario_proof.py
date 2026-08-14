from pathlib import Path

from sentinel_edge.scenario import load_scenario, run_submission_scenario_proof


def test_submission_scenario_proof_covers_required_emulated_h0_campaign(tmp_path: Path) -> None:
    scenario = load_scenario('fixtures/scenarios/simultaneous-event.json')
    proof = run_submission_scenario_proof(scenario, manifest_sha256='a' * 64, output_dir=tmp_path)
    assert proof['schema'] == 'sentinel-edge.simultaneous-event-proof.v1'
    assert proof['claim_class'] == 'simulated'
    assert proof['physical_hardware_required'] is False
    assert proof['physical_sensors_required'] is False
    assert proof['all_invariants_passed'] is True
    assert all(proof['invariants'].values())
    assert proof['trigger_phase']['dispatch_order'][0] == 'earthquake-trigger'
    assert proof['fault_campaign']['replay_backfill']['replay_rejected'] is True
    assert proof['fault_campaign']['replay_backfill']['backfill_zero_contribution'] is True
    assert proof['scheduler_campaign']['deferral']['overloaded'] is True
    assert proof['scheduler_campaign']['wildfire_forced_scan']['processed'] is True
    assert proof['evidence']['count'] >= 1
    assert (tmp_path / 'proof.json').is_file()
    assert (tmp_path / 'transcript.json').is_file()
    assert (tmp_path / 'invariants.json').is_file()


def test_submission_scenario_transcript_identity_is_deterministic(tmp_path: Path) -> None:
    scenario = load_scenario('fixtures/scenarios/simultaneous-event.json')
    first = run_submission_scenario_proof(scenario, manifest_sha256='b' * 64, output_dir=tmp_path / 'first')
    second = run_submission_scenario_proof(scenario, manifest_sha256='b' * 64, output_dir=tmp_path / 'second')

    assert first['transcript_sha256'] == second['transcript_sha256']
    assert first['invariant_report_sha256'] == second['invariant_report_sha256']
    assert first['evidence']['evidence_id'] == second['evidence']['evidence_id']
    assert (tmp_path / 'first' / 'transcript.json').read_bytes() == (tmp_path / 'second' / 'transcript.json').read_bytes()
