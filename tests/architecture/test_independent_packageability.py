from __future__ import annotations

import subprocess
import sys
import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[2]
BACKEND_MODULES = (
    "streaming-source-collector",
    "analysis-enrichment-engine",
    "model-workload-runtime",
    "incident-event-engine",
    "rest-api-integration-gateway",
)


def test_backend_modules_have_standalone_build_metadata_and_importable_source():
    for module_name in BACKEND_MODULES:
        module_root = ROOT / "modules" / module_name
        metadata = tomllib.loads((module_root / "pyproject.toml").read_text(encoding="utf-8"))
        distribution = metadata["project"]["name"]
        package_name = distribution.replace("-", "_")
        package_root = module_root / "src" / package_name
        assert (module_root / "pyproject.toml").is_file()
        assert package_root.is_dir(), f"{module_name} has no source package"
        source_files = tuple(package_root.rglob("*.py"))
        assert source_files, f"{module_name} has no Python implementation"
        result = subprocess.run(
            [sys.executable, "-c", f"import {package_name}"],
            cwd=Path.cwd(),
            env={"PATH": str(Path(sys.executable).parent), "PYTHONPATH": str(module_root / "src")},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_client_package_has_no_backend_installation_dependency():
    package = json.loads((ROOT / "modules/client-applications/package.json").read_text(encoding="utf-8"))
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert not any(name.startswith("sentinel-") for name in dependencies)
