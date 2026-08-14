from pathlib import Path
import tomllib

ROOT = Path(__file__).parents[2]

def test_ownership_metadata_has_one_incident_authority():
    data = tomllib.loads((ROOT / "modules/incident-event-engine/pyproject.toml").read_text())
    assert data["tool"]["sentinel-edge"]["incident_authority"] is True

def test_owned_namespaces_are_unique():
    text = (ROOT / "architecture/owned-namespaces.yaml").read_text()
    paths = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.strip().startswith("path:")]
    assert len(paths) == len(set(paths))


def test_hazard_and_analysis_facets_have_no_component4_mutator_or_store_imports():
    roots = (ROOT / "src/sentinel_edge/hazards", ROOT / "src/sentinel_edge/analysis")
    forbidden = ("sentinel_edge.incidents", "IncidentEventEngine", "IncidentJournalStore")
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert not any(marker in text for marker in forbidden), path


def test_hazard_facets_are_analysis_only_and_component4_is_separate():
    hazard_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src/sentinel_edge/hazards").glob("*.py"))
    assert "IncidentEventEngine" not in hazard_text
    assert "IncidentJournalStore" not in hazard_text
    analysis_text = (ROOT / "src/sentinel_edge/analysis/service.py").read_text(encoding="utf-8")
    assert "IncidentEventEngine" not in analysis_text
    incident_text = (ROOT / "src/sentinel_edge/incidents/engine.py").read_text(encoding="utf-8")
    assert "component-4-incidents" in incident_text
