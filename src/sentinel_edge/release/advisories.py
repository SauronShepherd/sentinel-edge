from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


class AdvisoryObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str
    advisory_id: str
    source: str
    source_mode: str
    authority: str
    observed_at: datetime
    package: str
    affected_versions: tuple[str, ...] = ()
    platform_predicates: tuple[str, ...] = ()
    feature_predicates: tuple[str, ...] = ()
    status: str
    source_artifact_sha256: str
    source_class: str | None = None
    ecosystem: str = "pypi"
    package_purl: str | None = None
    commit: str | None = None
    build_id: str | None = None
    known_exploited: bool = False
    exploit_maturity: str = "unknown"
    reachable: str = "unknown"
    operational_exposure: str = "unknown"
    severity_score: float | None = None
    toolchain_role: str = "runtime"


class VexDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    advisory_observation_id: str
    advisory_id: str
    subject_digest: str
    component_purl: str
    status: str
    justification: str
    predicate: str
    evidence: tuple[str, ...]
    approver: str
    policy_version: str
    issued_at: datetime
    expires_at: datetime
    invalidation_triggers: tuple[str, ...]

    @model_validator(mode="after")
    def validate_vex(self) -> "VexDecision":
        if self.expires_at <= self.issued_at:
            raise ValueError("VEX expiry must follow issue time")
        if self.status not in {"affected", "not_affected", "fixed", "under_investigation"}:
            raise ValueError("unsupported VEX status")
        if not self.evidence or not self.invalidation_triggers:
            raise ValueError("VEX requires evidence and invalidation triggers")
        return self


def load_advisory_snapshot(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["snapshot_sha256"] = sha256_file(path)
    return payload


def build_security_review(
    sbom: dict[str, Any],
    snapshots: list[dict[str, Any]],
    *,
    vex_decisions: list[VexDecision] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    vex_decisions = vex_decisions or []
    components = {item["purl"]: item for item in sbom.get("components", [])}
    observations: list[AdvisoryObservation] = []
    source_states = []
    for snapshot in snapshots:
        source_states.append({
            "source": snapshot["source"],
            "source_mode": snapshot.get("source_mode", "fixture"),
            "completeness": snapshot.get("completeness", "unknown"),
            "snapshot_sha256": snapshot.get("snapshot_sha256"),
            "source_class": snapshot.get("source_class", snapshot.get("source")),
        })
        for item in snapshot.get("advisories", []):
            observations.append(AdvisoryObservation.model_validate(item))
    subject = sha256_bytes(canonical_json_bytes({"components": sorted(components), "versions": {p: components[p]["version"] for p in components}}))
    matches = []
    conflicts = []
    blocking = []
    vex_by_key = {(item.advisory_observation_id, item.component_purl): item for item in vex_decisions}
    by_advisory: dict[tuple[str, str], set[str]] = {}
    for observation in observations:
        for purl, component in components.items():
            if component["name"].lower() != observation.package.lower():
                continue
            exact_affected = component["version"] in observation.affected_versions
            key = (observation.advisory_id, purl)
            by_advisory.setdefault(key, set()).add(observation.status)
            vex = vex_by_key.get((observation.observation_id, purl))
            vex_state = None
            if vex is not None:
                if vex.subject_digest != subject or vex.advisory_id != observation.advisory_id:
                    vex_state = "subject_or_advisory_mismatch"
                else:
                    vex_state = vex.status if vex.expires_at > now else "expired"
            record = {
                "observation_id": observation.observation_id,
                "advisory_id": observation.advisory_id,
                "source": observation.source,
                "component_purl": purl,
                "component_version": component["version"],
                "exact_version_affected": exact_affected,
                "platform_predicates": list(observation.platform_predicates),
                "feature_predicates": list(observation.feature_predicates),
                "advisory_status": observation.status,
                "vex_status": vex_state,
                "known_exploited": observation.known_exploited,
                "exploit_maturity": observation.exploit_maturity,
                "reachable": observation.reachable,
                "operational_exposure": observation.operational_exposure,
                "severity_score": observation.severity_score,
                "toolchain_role": observation.toolchain_role,
                "triage_priority": (
                    "critical_exploited_reachable" if observation.known_exploited and observation.reachable == "reachable"
                    else "high_reachable" if observation.reachable == "reachable"
                    else "review"
                ),
            }
            matches.append(record)
            if exact_affected and vex_state not in {"not_affected", "fixed"}:
                blocking.append(record)
    for (advisory_id, purl), statuses in by_advisory.items():
        if len(statuses) > 1:
            conflicts.append({"advisory_id": advisory_id, "component_purl": purl, "statuses": sorted(statuses)})
    completeness = "complete" if source_states and all(item["completeness"] == "complete" for item in source_states) else "bounded_or_unknown"
    return {
        "schema": "sentinel-edge-security-advisory-review/1.0",
        "generated_at": now.isoformat(),
        "subject_digest": subject,
        "source_states": source_states,
        "completeness": completeness,
        "observations_count": len(observations),
        "matches": matches,
        "conflicts": conflicts,
        "blocking_findings": blocking,
        "vex_decisions": [item.model_dump(mode="json") for item in vex_decisions],
        "release_eligible": completeness == "complete" and not blocking and not conflicts,
        "limitations": [
            "A bounded or fixture advisory snapshot cannot prove absence of vulnerabilities.",
            "Package-name/version matching does not prove reachability; exact platform and feature predicates remain visible.",
        ],
    }


def write_security_review(root: str | Path, snapshots: list[str | Path], output: str | Path | None = None) -> Path:
    root = Path(root).resolve()
    sbom = json.loads((root / "sbom.cdx.json").read_text(encoding="utf-8"))
    loaded = [load_advisory_snapshot(path) for path in snapshots]
    review = build_security_review(sbom, loaded)
    output = Path(output) if output else root / "security-review.json"
    output.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def verify_security_review(path: str | Path, sbom_path: str | Path) -> dict[str, Any]:
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    sbom = json.loads(Path(sbom_path).read_text(encoding="utf-8"))
    components = {item["purl"]: item["version"] for item in sbom.get("components", [])}
    subject = sha256_bytes(canonical_json_bytes({"components": sorted(components), "versions": components}))
    failures = []
    if subject != review.get("subject_digest"):
        failures.append("security_review_subject_mismatch")
    if review.get("release_eligible") and review.get("completeness") != "complete":
        failures.append("incomplete_review_marked_release_eligible")
    return {"valid": not failures, "failures": failures, "subject_digest": subject}

class AdvisoryCoveragePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    required_source_classes: tuple[str, ...] = ("osv", "github_advisory", "cisa_kev", "vendor")
    minimum_independent_sources: int = 2
    require_runtime_inventory: bool = True
    require_build_toolchain_inventory: bool = True


class ToolchainDenyRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    package: str
    denied_versions: tuple[str, ...]
    incident_id: str
    required_actions: tuple[str, ...] = ("credential_review", "runner_review", "clean_rebuild")


ASYNCAPI_JULY_2026_DENY_RULES: tuple[ToolchainDenyRule, ...] = (
    ToolchainDenyRule(package="@asyncapi/specs", denied_versions=("6.11.2-alpha.1", "6.11.2"), incident_id="ASYNCAPI-NPM-2026-07"),
    ToolchainDenyRule(package="@asyncapi/generator", denied_versions=("3.3.1",), incident_id="ASYNCAPI-NPM-2026-07"),
    ToolchainDenyRule(package="@asyncapi/generator-components", denied_versions=("0.7.1",), incident_id="ASYNCAPI-NPM-2026-07"),
    ToolchainDenyRule(package="@asyncapi/generator-helpers", denied_versions=("1.1.1",), incident_id="ASYNCAPI-NPM-2026-07"),
)


def _walk_json_packages(value: Any, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        name = value.get("name")
        version = value.get("version")
        if isinstance(name, str) and isinstance(version, str):
            found.append({"name": name, "version": version, "path": path or "/"})
        for key, item in value.items():
            found.extend(_walk_json_packages(item, f"{path}/{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk_json_packages(item, f"{path}/{index}"))
    return found


def scan_toolchain_inventory(
    paths: list[str | Path],
    *,
    deny_rules: tuple[ToolchainDenyRule, ...] = ASYNCAPI_JULY_2026_DENY_RULES,
    exposure_attestations: dict[str, dict[str, bool]] | None = None,
) -> dict[str, Any]:
    exposure_attestations = exposure_attestations or {}
    packages: list[dict[str, str]] = []
    files: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            files.append({"path": str(path), "state": "missing"})
            continue
        files.append({"path": str(path), "state": "read", "sha256": sha256_file(path)})
        if path.suffix == ".json":
            try:
                packages.extend(_walk_json_packages(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError):
                files[-1]["state"] = "invalid_json"
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            for rule in deny_rules:
                for version in rule.denied_versions:
                    if rule.package in text and version in text:
                        packages.append({"name": rule.package, "version": version, "path": "text-match"})
    findings: list[dict[str, Any]] = []
    rules_by_package = {rule.package: rule for rule in deny_rules}
    for package in packages:
        rule = rules_by_package.get(package["name"])
        if rule and package["version"] in rule.denied_versions:
            attestation = exposure_attestations.get(rule.incident_id, {})
            actions = {action: bool(attestation.get(action, False)) for action in rule.required_actions}
            findings.append({
                "package": package["name"], "version": package["version"], "incident_id": rule.incident_id,
                "source_path": package.get("path"), "required_actions": actions,
                "clean_environment_proven": all(actions.values()),
            })
    return {
        "schema": "sentinel-edge-toolchain-deny-review/1.0",
        "files": files,
        "packages_observed": sorted(packages, key=lambda item: (item["name"], item["version"], item.get("path", ""))),
        "findings": findings,
        "release_eligible": not findings or all(item["clean_environment_proven"] for item in findings),
        "limitations": ["Text lockfile parsing is deny-rule-specific; it is not a general dependency resolver."],
    }


def apply_coverage_policy(review: dict[str, Any], policy: AdvisoryCoveragePolicy, *, toolchain_review: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = review.get("source_states", [])
    classes = {item.get("source_class", item.get("source")) for item in sources}
    missing = sorted(set(policy.required_source_classes) - classes)
    authoritative = {item.get("source") for item in sources if item.get("source_mode") in {"live", "signed_snapshot", "fixture"}}
    failures: list[str] = []
    if missing:
        failures.append("required_advisory_source_classes_missing")
    if len(authoritative) < policy.minimum_independent_sources:
        failures.append("insufficient_independent_advisory_sources")
    if policy.require_build_toolchain_inventory and toolchain_review is None:
        failures.append("build_toolchain_inventory_missing")
    if toolchain_review is not None and not toolchain_review.get("release_eligible", False):
        failures.append("toolchain_incident_unresolved")
    coverage = {
        "schema": "sentinel-edge-advisory-coverage/1.0",
        "policy": policy.model_dump(mode="json"),
        "observed_source_classes": sorted(str(item) for item in classes if item),
        "missing_source_classes": missing,
        "independent_source_count": len(authoritative),
        "toolchain_review": toolchain_review,
        "complete": not failures and review.get("completeness") == "complete",
        "release_eligible": not failures and review.get("release_eligible", False),
        "failures": failures,
    }
    return {**review, "coverage": coverage, "release_eligible": coverage["release_eligible"]}
