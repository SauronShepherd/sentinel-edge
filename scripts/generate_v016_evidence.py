from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from sentinel_edge.qualification import (
    evaluate_host_trust,
    evaluate_idle_noise,
    evaluate_network_isolation,
    observe_benchmark_host,
    observe_host_trust,
    verify_host_trust_report,
    write_host_trust_report,
)
from sentinel_edge.release import (
    AdvisoryCoveragePolicy,
    apply_coverage_policy,
    build_security_review,
    scan_toolchain_inventory,
    verify_reproducibility_report,
    write_reproducibility_report,
)
from sentinel_edge.release.advisories import load_advisory_snapshot
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def build(root: Path) -> dict:
    reproduction = write_reproducibility_report(root, root / 'reproducibility-report.json')
    host = write_host_trust_report(root / 'host-trust-report.json')

    affected_fixture = root / 'fixtures/security/asyncapi-affected-package-lock.json'
    blocked_toolchain = scan_toolchain_inventory([affected_fixture])
    closed_toolchain = scan_toolchain_inventory(
        [affected_fixture],
        exposure_attestations={
            'ASYNCAPI-NPM-2026-07': {
                'credential_review': True,
                'runner_review': True,
                'clean_rebuild': True,
            }
        },
    )
    actual_toolchain = scan_toolchain_inventory([])

    sbom = json.loads((root / 'sbom.cdx.json').read_text(encoding='utf-8'))
    snapshot_paths = [
        root / 'fixtures/security/advisory-osv-bounded.json',
        root / 'fixtures/security/advisory-github_advisory-bounded.json',
        root / 'fixtures/security/advisory-cisa_kev-bounded.json',
        root / 'fixtures/security/advisory-vendor-bounded.json',
    ]
    review = build_security_review(sbom, [load_advisory_snapshot(path) for path in snapshot_paths])
    review = apply_coverage_policy(review, AdvisoryCoveragePolicy(), toolchain_review=actual_toolchain)
    (root / 'security-review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    benchmark_host = observe_benchmark_host(provider_threads=1)
    idle_envelope = evaluate_idle_noise(
        [{'load1': 0.05, 'cpu_psi_avg10': 0.0, 'dirty_kb': 0.0}],
        max_load1=1.0,
        max_cpu_psi_avg10=0.1,
        max_dirty_kb=1024.0,
    )
    app_network = evaluate_network_isolation({
        'mode': 'python_guard',
        'egress_probe_blocked': True,
        'misbehaving_adapter_blocked': True,
    })
    namespace_fixture = evaluate_network_isolation({
        'mode': 'network_namespace',
        'egress_probe_blocked': True,
        'misbehaving_adapter_blocked': True,
    })
    qualification_dir = root / 'qualification'
    qualification_dir.mkdir(exist_ok=True)
    (qualification_dir / 'benchmark-host-observation.json').write_text(json.dumps(benchmark_host, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (qualification_dir / 'benchmark-idle-envelope.json').write_text(json.dumps(idle_envelope, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (qualification_dir / 'benchmark-network-isolation.json').write_text(json.dumps(app_network, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    base = {
        'schema': 'sentinel-edge-v016-evidence/1.0',
        'reproducibility': {
            'path': 'reproducibility-report.json',
            'sha256': sha256_file(reproduction),
            'verification': verify_reproducibility_report(reproduction, root),
        },
        'host_trust': {
            'path': 'host-trust-report.json',
            'sha256': sha256_file(host),
            'verification': verify_host_trust_report(host),
            'policy_evaluation': evaluate_host_trust(observe_host_trust()),
        },
        'advisory_coverage': {
            'path': 'security-review.json',
            'sha256': sha256_file(root / 'security-review.json'),
            'source_classes': review['coverage']['observed_source_classes'],
            'complete': review['coverage']['complete'],
            'release_eligible': review['release_eligible'],
            'failures': review['coverage']['failures'],
        },
        'asyncapi_incident': {
            'blocked_without_reviews': blocked_toolchain,
            'closed_only_with_all_required_reviews': closed_toolchain,
        },
        'benchmark_host': {
            'observation_digest': benchmark_host['observation_digest'],
            'idle_envelope': idle_envelope,
            'application_only_network_guard': app_network,
            'network_namespace_contract_fixture': namespace_fixture,
        },
        'limitations': [
            'Byte reproducibility is proven only for the deterministic source bundle.',
            'The dependency lock has exact installed versions but no wheel hashes or offline mirror.',
            'Advisory sources are bounded fixtures and do not prove current live-feed completeness.',
            'The observed host does not prove Raspberry Pi customer-key secure boot.',
            'Below-application benchmark egress denial is a contract fixture, not deployed-host evidence.',
            'No release admission or target-device qualification is claimed.',
        ],
    }
    return {**base, 'receipt_sha256': sha256_bytes(canonical_json_bytes(base))}


def main() -> int:
    output = ROOT / 'evidence/v0.16.0-repro-advisory-host.json'
    output.parent.mkdir(exist_ok=True)
    payload = build(ROOT)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
