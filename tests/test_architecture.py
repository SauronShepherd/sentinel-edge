from pathlib import Path
import yaml


def test_exactly_six_component_packages_exist() -> None:
    root = Path("src/sentinel_edge")
    components = {"collector","analysis","runtime","incidents","gateway","clients"}
    assert all((root / name).is_dir() for name in components)


def test_owned_namespaces_define_single_writer_for_critical_resources() -> None:
    policy = yaml.safe_load(Path("architecture/owned-namespaces.yaml").read_text())
    authorities = policy["authorities"]
    assert authorities["incident_lifecycle"] == "incident-event-engine"
    for resource_group in ("databases", "artifacts", "secrets"):
        owners = policy["resources"][resource_group]
        assert len(owners) == len(set(owners))
        assert set(owners) == {"collector", "analyzer", "runtime", "incidents", "api"}


def test_connector_and_acquisition_imports_are_collector_owned() -> None:
    forbidden = ("import requests", "import httpx", "import urllib", "from urllib", "import socket", "from socket")
    violations = []
    for path in Path("src/sentinel_edge").rglob("*.py"):
        relative = path.relative_to("src/sentinel_edge")
        if relative.parts[:1] == ("collector",) or relative.as_posix() == "release/reproducibility.py":
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in forbidden):
            violations.append(relative.as_posix())
    assert violations == []


def test_no_makefile_or_powershell_files() -> None:
    forbidden = [
        path
        for path in Path('.').rglob('*')
        if ".venv" not in path.parts
        and "node_modules" not in path.parts
        and path.is_file()
        and (path.name.lower() == 'makefile' or path.suffix.lower() in {'.ps1', '.psm1', '.psd1'})
    ]
    assert forbidden == []
