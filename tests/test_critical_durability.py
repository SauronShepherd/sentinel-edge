from uuid import UUID, uuid4

from sentinel_edge.domain.models import AnalysisResult, CoverageState, HazardKind, IncidentState
from sentinel_edge.incidents import IncidentEventEngine
from sentinel_edge.storage import IncidentJournalStore


def test_full_durability_profile_and_committed_truth_survive_restart(tmp_path) -> None:
    path = tmp_path / "critical.sqlite3"
    store = IncidentJournalStore(path)
    assert store.durability_profile() == {
        "journal_mode": "wal",
        "synchronous": 2,
        "critical_truth_full_durability": True,
    }
    analysis = AnalysisResult(
        analysis_id=uuid4(), observation_id=uuid4(),
        correlation_id=UUID("22222222-2222-2222-2222-222222222222"),
        boot_id="boot-durable", hazard=HazardKind.FLOOD, score=0.9,
        state_hint=IncidentState.CONFIRMED, features={"durability_probe": 1.0},
        coverage=CoverageState.SUFFICIENT,
    )
    IncidentEventEngine(store).apply_analysis(analysis)
    store.close()

    restarted = IncidentEventEngine(IncidentJournalStore(path))
    assert restarted.current()[0].state is IncidentState.CONFIRMED
    assert analysis.analysis_id in restarted.journal()[0].analysis_ids
