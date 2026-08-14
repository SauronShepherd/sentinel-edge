from datetime import datetime, timezone

from sentinel_edge.domain.models import CoverageState, IncidentState
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.release.claim_lineage import ClaimDisposition, ClaimInfluenceManifest, resolve_claim_lineage
from tests.test_incidents import result


def test_history_requirements_preserve_knowledge_order_and_supersession() -> None:
    accepted = datetime(2026, 8, 1, 10, tzinfo=timezone.utc)
    event_time = datetime(2026, 8, 1, 9, tzinfo=timezone.utc)
    engine = IncidentEventEngine()
    first = engine.apply_analysis(result(0.6, IncidentState.SUSPECTED).model_copy(update={"event_time": event_time}), accepted_at=accepted)
    late = engine.apply_analysis(result(0.9, IncidentState.CONFIRMED).model_copy(update={"event_time": datetime(2026, 8, 1, 8, tzinfo=timezone.utc)}), accepted_at=datetime(2026, 8, 1, 11, tzinfo=timezone.utc))
    assert first.first_observed_at == event_time
    assert late.last_observed_at >= first.last_observed_at
    assert late.event_time_watermark == event_time
    assert "late_context_correction" in late.reason_codes
    manifest = ClaimInfluenceManifest("dataset-v2", "a" * 64, "b" * 64, "c" * 64)
    decision = resolve_claim_lineage("claim-old", manifest, available_variant_ids={"dataset-v2"}, replacement_claim_id="claim-new")
    assert decision.disposition is ClaimDisposition.SUPERSEDED
    assert decision.replacement_claim_id == "claim-new"
