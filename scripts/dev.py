from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

COMMANDS: dict[str, list[list[str]]] = {
    "format": [[PY, "scripts/check_format.py"]],
    "lint": [[PY, "-m", "pytest", "-q"]],
    "type": [[PY, "scripts/check_python_types.py"]],
    "governance": [[PY, "scripts/validate_capability_status.py"], [PY, "scripts/validate_requirement_ledger.py"]],
    "architecture": [[PY, "scripts/check_architecture_boundaries.py"], [PY, "scripts/check_client_boundaries.py"]],
    "contracts": [[PY, "scripts/generate_contracts.py"], [PY, "-m", "pytest", "-q", "tests/contracts"]],
    "plugins": [[PY, "-m", "pytest", "-q", "sdk/sentinel-plugin-sdk/tests"]],
    "testkit": [[PY, "-m", "pytest", "-q", "sdk/sentinel-testkit/tests"]],
    "components": [[PY, "-m", "pytest", "-q", "tests/component"], [PY, "scripts/record_lifecycle_evidence.py"], [PY, "scripts/record_state_migration_evidence.py"]],
    "compatibility": [[PY, "-m", "pytest", "-q", "tests/contracts/test_compatibility.py"]],
    "generated": [[PY, "scripts/generate_contracts.py"], [PY, "-m", "pytest", "-q", "tests/contracts/test_generated_bindings.py"]],
    "provenance": [[PY, "scripts/validate_capability_status.py"], [PY, "scripts/generate_architecture_evidence.py"], [PY, "scripts/record_package_evidence.py"]],
    "docs": [[PY, "scripts/check_markdown_links.py"]],
    "clients": [["npm.cmd", "--prefix", "modules/client-applications", "ci", "--ignore-scripts"], ["npm.cmd", "--prefix", "modules/client-applications", "run", "build"], ["npm.cmd", "--prefix", "modules/client-applications", "test"]],
    "test-all": [[PY, "-m", "pytest", "-q", "contracts/sentinel-contracts/tests", "sdk/sentinel-plugin-sdk/tests", "sdk/sentinel-testkit/tests", "tests"]],
    "test-arm": [[PY, "-c", "print('Arm gate planned: no hardware claim made')"]],
}

def run(name: str) -> int:
    if name == "setup":
        bootstrap = [PY, "-m", "pip", "install", "setuptools==75.8.0", "wheel==0.45.1", "uv==0.10.0", "pytest==9.0.2", "PyYAML==6.0.3", "jsonschema==4.26.0"]
        result = subprocess.run(bootstrap, cwd=ROOT)
        if result.returncode: return result.returncode
        return subprocess.run([PY, "-m", "pip", "install", "--no-build-isolation", "-e", "contracts/sentinel-contracts", "-e", "sdk/sentinel-plugin-sdk", "-e", "sdk/sentinel-testkit"], cwd=ROOT).returncode
    if name in {"test-all", "gates"}:
        setup_code = run("setup")
        if setup_code: return setup_code
    commands = COMMANDS.get(name)
    if commands is None:
        print(f"unknown command: {name}", file=sys.stderr); return 2
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode: return result.returncode
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Sentinel Edge cross-platform developer runner")
    parser.add_argument("command", choices=[*COMMANDS, "setup", "gates"])
    args = parser.parse_args()
    if args.command == "gates":
        for name in ("format", "type", "governance", "architecture", "contracts", "plugins", "testkit", "components", "compatibility", "generated", "clients", "test-all", "provenance", "docs"):
            code = run(name)
            if code: return code
        return 0
    return run(args.command)

if __name__ == "__main__": raise SystemExit(main())
