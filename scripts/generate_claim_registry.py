"""Generate Claim Registry JSON and human-readable tables from evidence artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from sentinel_edge.domain.models import ClaimClass, ClaimRecord
from sentinel_edge.release import ClaimRegistry


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_claim_table(registry: ClaimRegistry, *, target_allowed: bool) -> str:
    """Render the release table solely from the typed Claim Registry records."""
    rows = [
        "# Claim Registry", "",
        "Generated from the validated Claim Registry; no performance values are hand-entered.", "",
        "| Claim ID | Class | Statement | Target measurement allowed |", "|---|---|---|---:|",
    ]
    rows.extend(
        f"| `{claim.claim_id}` | `{claim.claim_class.value}` | {claim.statement} | `{str(target_allowed).lower()}` |"
        for claim in registry.records()
    )
    rows.extend(["", "Numeric performance values are not emitted unless the evidence report explicitly permits a target measurement claim.", ""])
    return "\n".join(rows)


def generate(root: Path) -> tuple[dict, str]:
    emulated_path = root / "qualification/emulated-arm64-benchmark.json"
    identity_path = root / "qualification/benchmark-identity-report.json"
    legacy_report_path = root / "qualification/benchmark-evidence-report.json"

    source_artifacts: list[dict[str, str]] = []
    target_allowed = False
    source_class = "development"
    quality_guardrails_passed = False
    target_host_qualified = False

    if emulated_path.is_file():
        report = json.loads(emulated_path.read_text(encoding="utf-8"))
        env = report.get("environment", {}) if isinstance(report.get("environment"), dict) else {}
        providers = env.get("onnxruntime", {}).get("providers", []) if isinstance(env.get("onnxruntime"), dict) else []
        emulated_valid = (
            report.get("schema") == "sentinel-edge.emulated-arm64-benchmark.v1"
            and report.get("release_profile") == "H0-EMULATED-AARCH64-20260813"
            and str(env.get("guest_architecture", "")).lower() in {"aarch64", "arm64"}
            and env.get("execution_mode") == "docker-qemu-linux-arm64"
            and "CPUExecutionProvider" in providers
            and report.get("claim_class") == "simulated"
            and report.get("quality_guardrails_passed") is True
        )
        quality_guardrails_passed = bool(report.get("quality_guardrails_passed")) and emulated_valid
        source_class = "simulated_emulated_arm64" if emulated_valid else "invalid_emulated_arm64"
        source_artifacts.append({"path": "qualification/emulated-arm64-benchmark.json", "sha256": sha256(emulated_path)})
        refs = [f"sha256:{sha256(emulated_path)}"]
        if identity_path.is_file():
            source_artifacts.append({"path": "qualification/benchmark-identity-report.json", "sha256": sha256(identity_path)})
            refs.append(f"sha256:{sha256(identity_path)}")
        claim = ClaimRecord(
            claim_id="benchmark-local-development",
            claim_class=ClaimClass.SIMULATED,
            statement=(
                "Arm64-emulated B0/B1/O1 comparison with deterministic simulated sensor inputs; "
                "results are not Raspberry Pi 5 performance measurements"
            ),
            artifact_refs=tuple(refs),
        )
    else:
        report = json.loads(legacy_report_path.read_text(encoding="utf-8"))
        target_allowed = bool(report.get("target_measurement_claim_allowed"))
        quality_guardrails_passed = bool(report.get("quality_guardrails_passed", False))
        target_host_qualified = bool(report.get("target_host_qualified", False))
        source_class = str(report.get("source_class") or "development")
        source_artifacts.extend([
            {"path": "qualification/benchmark-evidence-report.json", "sha256": sha256(legacy_report_path)},
            {"path": "qualification/benchmark-identity-report.json", "sha256": sha256(identity_path)},
        ])
        claim = ClaimRecord(
            claim_id="benchmark-local-development",
            claim_class=ClaimClass.TARGET if target_allowed else ClaimClass.SIMULATED,
            statement=("Target benchmark measurement claim" if target_allowed else "Development replay reference; not a target performance measurement"),
            artifact_refs=(f"sha256:{sha256(legacy_report_path)}", f"sha256:{sha256(identity_path)}"),
        )

    registry = ClaimRegistry()
    registry.add(claim)
    payload = {
        "schema": "sentinel-edge-claim-registry/1.0",
        "source_artifacts": source_artifacts,
        "claim_ceiling": {
            "target_measurement_claim_allowed": target_allowed,
            "source_class": source_class,
            "quality_guardrails_passed": quality_guardrails_passed,
            "target_host_qualified": target_host_qualified,
            "raspberry_pi_performance_claim_allowed": False if emulated_path.is_file() else target_allowed,
        },
        "claims": [item.model_dump(mode="json") for item in registry.records()],
    }
    table = render_claim_table(registry, target_allowed=target_allowed)
    return payload, table


def write(root: Path, payload: dict, table: str) -> None:
    directory = root / "qualification"
    directory.mkdir(parents=True, exist_ok=True)
    registry_path = directory / "claim-registry.json"
    registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (directory / "claim-table.md").write_text(table, encoding="utf-8", newline="\n")
    # This generated artifact is itself listed in the evidence registry. Keep
    # that binding current whenever benchmark timing/output changes.
    evidence_path = root / "registries/evidence.yaml"
    evidence_text = evidence_path.read_text(encoding="utf-8")
    digest = sha256(registry_path)
    pattern = r"(id: EV-R00-CLAIM-REGISTRY-20260812\n(?:  .*\n)*?  sha256: )([0-9a-f]{64})"
    updated, count = re.subn(pattern, rf"\g<1>{digest}", evidence_text, count=1)
    if count != 1:
        raise RuntimeError("evidence registry claim-registry binding is missing or malformed")
    evidence_path.write_text(updated, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    payload, table = generate(args.root.resolve())
    write(args.root.resolve(), payload, table)
    print(json.dumps({"claims": len(payload["claims"]), "target_measurement_claim_allowed": payload["claim_ceiling"]["target_measurement_claim_allowed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
