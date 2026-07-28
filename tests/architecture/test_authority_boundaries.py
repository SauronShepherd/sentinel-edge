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
