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
        shutil.copytree(ROOT, temp, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", ".venv", "build", "node_modules", ".pytest_cache"))
        target = temp / relative
        target.write_text(target.read_text(encoding="utf-8").replace(marker, replacement), encoding="utf-8")
        result = subprocess.run([sys.executable, str(temp / "scripts/check_architecture_boundaries.py")], cwd=temp, text=True, capture_output=True)
        return result.stdout + result.stderr

def test_cross_owned_database_mutation_fails():
    output = run_mutation("modules/analysis-enrichment-engine/src/sentinel_analysis_enrichment_engine/bootstrap/runtime.py", "from dataclasses import dataclass", "CROSS_DB = 'runtime/incidents/incidents.db'\nfrom dataclasses import dataclass")
    assert "cross-owned namespace" in output

def test_business_dependency_mutation_fails():
    output = run_mutation("modules/analysis-enrichment-engine/pyproject.toml", 'dependencies = ["sentinel-contracts>=1.0,<2.0"]', 'dependencies = ["sentinel-contracts>=1.0,<2.0", "sentinel-incident-event-engine>=0.1"]')
    assert "forbidden business dependencies" in output

def test_policy_disable_mutation_fails_closed():
    output = run_mutation("architecture/import-rules.toml", "forbidden_cross_module_imports = true", "forbidden_cross_module_imports = false")
    assert "disables cross-module" in output
