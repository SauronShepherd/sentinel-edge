from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).parents[2]


def test_client_boundary_checker_rejects_backend_and_persistence_mutations():
    source = ROOT / "modules/client-applications/shared-domain/src/index.ts"
    original = source.read_text(encoding="utf-8")
    for mutation in ("import fs from 'node:fs';\n", "import transport from 'internal-transport';\n"):
        with tempfile.TemporaryDirectory(prefix="sentinel-client-boundary-") as directory:
            temp = Path(directory)
            for name in ("architecture", "modules/client-applications", "scripts"):
                shutil.copytree(ROOT / name, temp / name, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns(".git", ".venv", "build", "node_modules", ".pytest_cache", "__pycache__"))
            target = temp / source.relative_to(ROOT)
            target.write_text(mutation + original, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(temp / "scripts/check_client_boundaries.py")],
                cwd=temp,
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0
            assert "forbidden client boundary references" in result.stdout
