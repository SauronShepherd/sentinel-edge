import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
CHECKER = ROOT / "scripts/check_architecture_boundaries.py"

def run_mutation(relative: str, marker: str, replacement: str) -> str:
    with tempfile.TemporaryDirectory(prefix="sentinel-architecture-") as directory:
        temp = Path(directory)
        for name in ("architecture", "modules", "docs/baseline/v0.13.0", "scripts"):
            shutil.copytree(ROOT / name, temp / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".git", ".venv", "build", "node_modules", ".pytest_cache", "__pycache__"))
        target = temp / relative
        target.write_text(target.read_text(encoding="utf-8").replace(marker, replacement), encoding="utf-8")
        result = subprocess.run([sys.executable, str(temp / "scripts/check_architecture_boundaries.py")], cwd=temp, text=True, capture_output=True)
        return result.stdout + result.stderr

def test_cross_owned_database_mutation_fails():
    output = run_mutation("modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/bootstrap/runtime.py", "from dataclasses import dataclass", "CROSS_DB = 'runtime/incidents/incidents.db'\nfrom dataclasses import dataclass")
    assert "cross-owned namespace" in output


def test_cross_owned_artifact_and_secret_mutations_fail():
    for marker, replacement in (
        ("from dataclasses import dataclass", "CROSS_ARTIFACT = 'runtime/incidents/artifacts'\nfrom dataclasses import dataclass"),
        ("from dataclasses import dataclass", "CROSS_SECRET = 'runtime/incidents/secrets'\nfrom dataclasses import dataclass"),
    ):
        output = run_mutation("modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/bootstrap/runtime.py", marker, replacement)
        assert "cross-owned namespace" in output

def test_business_dependency_mutation_fails():
    output = run_mutation("modules/analysis-enrichment-engine/pyproject.toml", 'dependencies = ["sentinel-contracts>=1.0,<2.0"]', 'dependencies = ["sentinel-contracts>=1.0,<2.0", "sentinel-incident-event-engine>=0.1"]')
    assert "forbidden business dependencies" in output


def test_direct_business_import_mutation_fails():
    output = run_mutation(
        "modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/bootstrap/runtime.py",
        "from dataclasses import dataclass",
        "from sentinel_incident_event_engine import forbidden\nfrom dataclasses import dataclass",
    )
    assert "forbidden module implementation import" in output

def test_policy_disable_mutation_fails_closed():
    output = run_mutation("architecture/import-rules.toml", "forbidden_cross_module_imports = true", "forbidden_cross_module_imports = false")
    assert "disables cross-module" in output


def test_policy_prefix_mutation_changes_controlled_behavior():
    output = run_mutation("architecture/import-rules.toml", '"sentinel_analysis_enrichment_engine",', '"sentinel_analysis_enrichment_engine",\n  "sentinel_fake_module",')
    assert "architecture boundary gate: PASS" in output or "forbidden module implementation import" in output
