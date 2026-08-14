import json
from pathlib import Path

from sentinel_edge.qualification import (
    evaluate_host_trust,
    evaluate_idle_noise,
    evaluate_network_isolation,
    observe_host_trust,
    verify_host_trust_report,
    write_host_trust_report,
)
from sentinel_edge.release import (
    AdvisoryCoveragePolicy,
    analyze_difference,
    apply_coverage_policy,
    build_cyclonedx_sbom,
    build_reproducibility_report,
    build_security_review,
    scan_toolchain_inventory,
    verify_reproducibility_report,
    write_release_lock,
    write_reproducibility_report,
)
from sentinel_edge.release.advisories import load_advisory_snapshot


def test_paired_source_bundle_is_byte_exact_and_honestly_scoped(tmp_path: Path) -> None:
    write_release_lock('.', tmp_path / 'lock.json')
    # The repository lock is used by the actual report.
    write_release_lock('.')
    report_path = write_reproducibility_report('.', tmp_path / 'report.json')
    report = json.loads(report_path.read_text())
    source = next(item for item in report['artifact_classes'] if item['artifact'] == 'deterministic-source-bundle')
    assert source['comparison']['byte_exact'] is True
    assert source['build_a']['sha256'] == source['build_b']['sha256']
    assert report['network_control']['network_used'] is False
    assert report['network_control']['below_application_layer_proven'] is False
    assert 'Target binaries, models, firmware, and Raspberry Pi images are outside this report.' in report['limitations']
    assert verify_reproducibility_report(report_path, '.')['valid'] is True


def test_difference_analysis_does_not_hide_executable_content_change() -> None:
    envelope_a = json.dumps({'generated_at': 'a', 'value': 1}).encode()
    envelope_b = json.dumps({'generated_at': 'b', 'value': 1}).encode()
    normalized = analyze_difference(envelope_a, envelope_b, media_type='application/json')
    assert normalized['classification'] == 'normalized_envelope_difference'
    assert normalized['material'] is False
    executable = analyze_difference(b'{"value":1}', b'{"value":2}', media_type='application/json')
    assert executable['classification'] == 'executable_or_unknown_difference'
    assert executable['material'] is True


def test_asyncapi_deny_rule_requires_exposure_closure(tmp_path: Path) -> None:
    lock = tmp_path / 'package-lock.json'
    lock.write_text(json.dumps({'name': 'demo', 'version': '1.0.0', 'packages': {'node_modules/@asyncapi/generator': {'name': '@asyncapi/generator', 'version': '3.3.1'}}}))
    blocked = scan_toolchain_inventory([lock])
    assert blocked['release_eligible'] is False
    assert blocked['findings'][0]['incident_id'] == 'ASYNCAPI-NPM-2026-07'
    closed = scan_toolchain_inventory([lock], exposure_attestations={'ASYNCAPI-NPM-2026-07': {'credential_review': True, 'runner_review': True, 'clean_rebuild': True}})
    assert closed['release_eligible'] is True


def test_advisory_coverage_requires_multiple_declared_source_classes(tmp_path: Path) -> None:
    sbom = build_cyclonedx_sbom('.')
    snapshots = []
    for source_class in ('osv', 'github_advisory', 'cisa_kev', 'vendor'):
        path = tmp_path / f'{source_class}.json'
        path.write_text(json.dumps({'schema': 'sentinel-edge-advisory-snapshot/1.0', 'source': source_class, 'source_class': source_class, 'source_mode': 'signed_snapshot', 'completeness': 'complete', 'advisories': []}))
        snapshots.append(load_advisory_snapshot(path))
    base = build_security_review(sbom, snapshots)
    toolchain = scan_toolchain_inventory([])
    covered = apply_coverage_policy(base, AdvisoryCoveragePolicy(), toolchain_review=toolchain)
    assert covered['coverage']['complete'] is True
    assert covered['release_eligible'] is True
    incomplete = apply_coverage_policy(build_security_review(sbom, snapshots[:1]), AdvisoryCoveragePolicy(), toolchain_review=toolchain)
    assert incomplete['release_eligible'] is False
    assert 'required_advisory_source_classes_missing' in incomplete['coverage']['failures']


def test_known_exploited_reachable_issue_has_distinct_priority(tmp_path: Path) -> None:
    sbom = build_cyclonedx_sbom('.')
    component = sbom['components'][0]
    path = tmp_path / 'kev.json'
    path.write_text(json.dumps({
        'schema': 'sentinel-edge-advisory-snapshot/1.0', 'source': 'cisa-kev', 'source_class': 'cisa_kev',
        'source_mode': 'signed_snapshot', 'completeness': 'complete', 'advisories': [{
            'observation_id': 'obs-kev', 'advisory_id': 'CVE-TEST-1', 'source': 'cisa-kev', 'source_class': 'cisa_kev',
            'source_mode': 'signed_snapshot', 'authority': 'official', 'observed_at': '2026-08-03T00:00:00Z',
            'package': component['name'], 'affected_versions': [component['version']], 'status': 'affected',
            'source_artifact_sha256': 'a'*64, 'known_exploited': True, 'reachable': 'reachable',
            'exploit_maturity': 'active', 'operational_exposure': 'local_api', 'severity_score': 7.0,
        }]
    }))
    review = build_security_review(sbom, [load_advisory_snapshot(path)])
    assert review['blocking_findings'][0]['triage_priority'] == 'critical_exploited_reachable'


def test_host_trust_is_separate_and_does_not_overclaim_secure_boot(tmp_path: Path) -> None:
    observation = observe_host_trust()
    assert observation['application_artifact_trust_separate'] is True
    assert observation['privileged_host_compromise_not_covered'] is True
    assert observation['judge_h0_secure_boot_required'] is False
    report = evaluate_host_trust(observation)
    assert report['valid'] is True
    strict = evaluate_host_trust(observation, require_secure_boot=True)
    if not observation['secure_boot_proven']:
        assert strict['release_eligible'] is False
        assert 'secure_boot_not_proven' in strict['failures']
    path = write_host_trust_report(tmp_path / 'host.json')
    assert verify_host_trust_report(path)['valid'] is True


def test_benchmark_host_contracts_distinguish_idle_and_network_proof() -> None:
    good = evaluate_idle_noise([{'load1': 0.1, 'cpu_psi_avg10': 0.0, 'dirty_kb': 10}], max_load1=1.0, max_cpu_psi_avg10=0.1, max_dirty_kb=100)
    assert good['valid'] is True
    bad = evaluate_idle_noise([{'load1': 2.0, 'cpu_psi_avg10': 0.2, 'dirty_kb': 200}], max_load1=1.0, max_cpu_psi_avg10=0.1, max_dirty_kb=100)
    assert bad['valid'] is False
    app_only = evaluate_network_isolation({'mode': 'python_guard', 'egress_probe_blocked': True, 'misbehaving_adapter_blocked': True})
    assert app_only['valid'] is False
    namespace = evaluate_network_isolation({'mode': 'network_namespace', 'egress_probe_blocked': True, 'misbehaving_adapter_blocked': True})
    assert namespace['valid'] is True
