from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from sentinel_edge.domain.models import (
    ConfigurationActivationRecord,
    ConfigurationBundle,
    ConfigurationState,
    CriticalityTier,
)
from sentinel_edge.security import canonical_json_bytes, sha256_bytes
from sentinel_edge.storage import ArtifactPolicy, ArtifactScope, ConfigurationStore, ContentAddressedArtifactStore

SelfTest = Callable[[ConfigurationBundle], tuple[bool, tuple[str, ...]]]
Canary = Callable[[ConfigurationBundle], tuple[bool, tuple[str, ...]]]
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_configuration_bundle(path: str | Path) -> ConfigurationBundle:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))
    return ConfigurationBundle.model_validate(raw)


class ConfigurationManager:
    """Validate → stage → self-test → activate → canary → rollback configuration lifecycle."""

    def __init__(
        self,
        store: ConfigurationStore,
        artifacts: ContentAddressedArtifactStore,
        *,
        self_test: SelfTest | None = None,
    ) -> None:
        self.store = store
        self.artifacts = artifacts
        self._self_test = self_test or self._default_self_test

    @staticmethod
    def validate(raw: ConfigurationBundle | dict[str, Any]) -> ConfigurationBundle:
        bundle = raw if isinstance(raw, ConfigurationBundle) else ConfigurationBundle.model_validate(raw)
        for label, values in (("model", bundle.model_hashes), ("source", bundle.source_hashes)):
            invalid = [key for key, value in values.items() if not _SHA256.fullmatch(value)]
            if invalid:
                raise ValueError(f"invalid {label} SHA-256 for: {','.join(sorted(invalid))}")
        return bundle

    @staticmethod
    def _default_self_test(bundle: ConfigurationBundle) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        profile_ids = [item.profile_id for item in bundle.workloads]
        if len(profile_ids) != len(set(profile_ids)):
            reasons.append("duplicate_profile_id")
        if not any(item.tier is CriticalityTier.A_IMMEDIATE for item in bundle.workloads):
            reasons.append("tier_a_workload_missing")
        if any(item.memory_mb > int(bundle.settings.get("available_memory_mb", 1024)) for item in bundle.workloads):
            reasons.append("workload_exceeds_memory_envelope")
        if any(item.deadline_ms < item.estimated_cost_ms for item in bundle.workloads):
            reasons.append("service_budget_exceeds_deadline")
        return (not reasons, tuple(sorted(reasons)))

    def stage(self, raw: ConfigurationBundle | dict[str, Any]) -> tuple[ConfigurationBundle, str, str]:
        bundle = self.validate(raw)
        payload = canonical_json_bytes(bundle.model_dump(mode="json"))
        ref = self.artifacts.put_bytes(
            payload, media_type="application/json", policy=ArtifactPolicy.configuration_bundle(),
            scope=ArtifactScope(scenario_run_id=f"configuration:{bundle.bundle_id}"),
        )
        self.store.stage(bundle, bundle_sha256=ref.sha256, artifact_ref=f"sha256:{ref.sha256}")
        return bundle, ref.sha256, ref.relative_path

    def activate(
        self,
        raw: ConfigurationBundle | dict[str, Any],
        *,
        canary: Canary | None = None,
    ) -> ConfigurationActivationRecord:
        previous = self.store.active()
        bundle, bundle_sha256, _ = self.stage(raw)
        previous_payload = previous.model_dump(mode="json") if previous else {}
        diff_sha256 = sha256_bytes(
            canonical_json_bytes({"from": previous_payload, "to": bundle.model_dump(mode="json")})
        )
        passed, reasons = self._self_test(bundle)
        if not passed:
            rejected = ConfigurationActivationRecord(
                bundle_id=bundle.bundle_id,
                version=bundle.version,
                state=ConfigurationState.REJECTED,
                actor=bundle.actor,
                bundle_sha256=bundle_sha256,
                diff_sha256=diff_sha256,
                previous_bundle_id=previous.bundle_id if previous else None,
                reason_codes=("self_test_failed",) + reasons,
            )
            self.store.record(rejected)
            return rejected
        activated = ConfigurationActivationRecord(
            bundle_id=bundle.bundle_id,
            version=bundle.version,
            state=ConfigurationState.ACTIVE,
            actor=bundle.actor,
            bundle_sha256=bundle_sha256,
            diff_sha256=diff_sha256,
            previous_bundle_id=previous.bundle_id if previous else None,
            reason_codes=("self_test_passed",),
        )
        self.store.activate(bundle, activated)
        if canary is not None:
            canary_passed, canary_reasons = canary(bundle)
            if not canary_passed:
                rolled_back = ConfigurationActivationRecord(
                    bundle_id=bundle.bundle_id,
                    version=bundle.version,
                    state=ConfigurationState.ROLLED_BACK,
                    actor=bundle.actor,
                    bundle_sha256=bundle_sha256,
                    diff_sha256=diff_sha256,
                    previous_bundle_id=previous.bundle_id if previous else None,
                    reason_codes=("canary_failed",) + tuple(canary_reasons),
                )
                self.store.rollback(bundle, previous, rolled_back)
                return rolled_back
        return activated

    def state(self) -> dict[str, Any]:
        return self.store.state()
