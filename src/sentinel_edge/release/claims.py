from __future__ import annotations

import json
import re
from pathlib import Path

from sentinel_edge.domain.models import ClaimClass, ClaimRecord
from sentinel_edge.storage import ArtifactPolicy, ArtifactRef, ArtifactScope, ContentAddressedArtifactStore


class ClaimRegistry:
    def __init__(self) -> None:
        self._claims: dict[str, ClaimRecord] = {}

    def add(self, claim: ClaimRecord) -> None:
        if claim.claim_id in self._claims and self._claims[claim.claim_id] != claim:
            raise ValueError("claim identifiers are immutable")
        if claim.claim_class is ClaimClass.MEASURED and not (
            claim.artifact_refs and claim.capability_hashes and claim.config_hashes
        ):
            raise ValueError("measured claims require raw artifacts, capability hashes, and configuration hashes")
        self._claims[claim.claim_id] = claim

    def records(self) -> tuple[ClaimRecord, ...]:
        return tuple(self._claims[key] for key in sorted(self._claims))

    def classification_report(self) -> dict[str, object]:
        """Return a machine-readable label for every registered value."""
        rows = [
            {
                "claim_id": claim.claim_id,
                "statement": claim.statement,
                "value_class": claim.claim_class.value,
                "label": claim.claim_class.value,
            }
            for claim in self.records()
        ]
        return {
            "schema": "sentinel-edge-claim-classification-report/1.0",
            "values": rows,
            "unlabelled_count": sum(1 for row in rows if not row["label"]),
        }

    @staticmethod
    def verify_measured_claim(claim: ClaimRecord, *, artifact_digests: set[str], capability_hashes: set[str], config_hashes: set[str], model_hashes: set[str]) -> tuple[str, ...]:
        if claim.claim_class is not ClaimClass.MEASURED:
            return ("claim_not_measured",)
        failures: list[str] = []
        if any(ref.removeprefix("sha256:") not in artifact_digests for ref in claim.artifact_refs):
            failures.append("raw_artifact_digest_unresolved")
        for label, values, available in (("capability", claim.capability_hashes, capability_hashes), ("config", claim.config_hashes, config_hashes), ("model", claim.model_hashes, model_hashes)):
            if any(not re.fullmatch(r"[0-9a-f]{64}", value) or value not in available for value in values):
                failures.append(f"{label}_hash_unresolved")
        return tuple(failures)

    def write(self, store: ContentAddressedArtifactStore) -> ArtifactRef:
        payload = {
            "schema": "sentinel-edge-claim-registry/1.0",
            "claims": [claim.model_dump(mode="json") for claim in self.records()],
        }
        return store.put_bytes(
            (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            media_type="application/json",
            policy=ArtifactPolicy.claim_registry(),
            scope=ArtifactScope(scenario_run_id="claim-registry"),
        )

    @classmethod
    def read(cls, path: str | Path) -> "ClaimRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        registry = cls()
        for raw in payload["claims"]:
            registry.add(ClaimRecord.model_validate(raw))
        return registry
