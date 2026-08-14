from __future__ import annotations

"""Provision the local Judge/developer checkout without a PYTHONPATH hack.

The final Arm64 candidate is always exercised in the separately pinned AArch64
container.  This bootstrap exists for the host-side Judge flow.  It prefers the
hash-pinned ``requirements-dev.lock.txt`` environment, but can reuse an already
provisioned compatible Python environment for ordinary local/demo work when the
package index is unavailable.  Release preflight sets
``SENTINEL_SETUP_REQUIRE_LOCKED=1`` and therefore requires the exact lock.

The repository itself is made importable with a standard ``.pth`` installation
pointing at the checkout's declared source roots.  No PYTHONPATH environment
variable or mutable package build is required.
"""

import importlib.metadata as metadata
import json
import os
import re
import site
import subprocess
import sys
import sysconfig
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "requirements-dev.lock.txt"
PYPROJECT = ROOT / "pyproject.toml"
REPORT = ROOT / ".tmp/setup-environment.json"
PTH_NAME = "000-sentinel-edge-checkout.pth"
LEGACY_PTH_NAMES = ("sentinel-edge-checkout.pth",)


def _canon(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_requirements() -> list[str]:
    payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    values = list(project.get("dependencies", []))
    values.extend(project.get("optional-dependencies", {}).get("test", []))
    return [str(item) for item in values]


def _source_roots() -> list[Path]:
    payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    pytest_roots = payload.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("pythonpath", [])
    roots = [ROOT / str(item) for item in pytest_roots]
    # Keep only existing directories and preserve declaration order.
    return [path.resolve() for path in roots if path.is_dir()]


def _lock_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    pattern = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;\\]+)")
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            versions[_canon(match.group(1))] = match.group(2)
    return versions


def _requirement_name(requirement: str) -> str:
    # PEP 508 names precede extras/specifiers/markers.  This standard-library
    # fallback is sufficient to locate the exact version in the uv export.
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    if not match:
        raise ValueError(f"invalid_requirement:{requirement}")
    return _canon(match.group(1))


def _installed_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def exact_lock_state() -> tuple[bool, list[dict[str, str | None]]]:
    locked = _lock_versions()
    rows: list[dict[str, str | None]] = []
    valid = True
    for declaration in _declared_requirements():
        name = _requirement_name(declaration)
        expected = locked.get(name)
        actual = _installed_version(name)
        row = {"name": name, "expected": expected, "actual": actual}
        rows.append(row)
        if not expected or actual != expected:
            valid = False
    return valid, rows


def compatible_state() -> tuple[bool, list[dict[str, str | None]]]:
    """Check declared ranges when packaging is already available.

    A completely pristine interpreter does not have to contain ``packaging``;
    in that case the caller installs the exact hash-pinned lock first.
    """

    try:
        from packaging.requirements import Requirement
        from packaging.version import Version
    except ModuleNotFoundError:
        return False, [{"name": "packaging", "expected": "declared project range", "actual": None}]

    rows: list[dict[str, str | None]] = []
    valid = True
    for declaration in _declared_requirements():
        requirement = Requirement(declaration)
        name = _canon(requirement.name)
        actual = _installed_version(name)
        accepted = actual is not None and (not requirement.specifier or Version(actual) in requirement.specifier)
        rows.append({"name": name, "expected": str(requirement.specifier) or "installed", "actual": actual})
        if not accepted:
            valid = False
    python_spec = tomllib.loads(PYPROJECT.read_text(encoding="utf-8")).get("project", {}).get("requires-python", "")
    if python_spec:
        try:
            from packaging.specifiers import SpecifierSet

            if Version(".".join(map(str, sys.version_info[:3]))) not in SpecifierSet(str(python_spec)):
                valid = False
                rows.append({"name": "python", "expected": str(python_spec), "actual": sys.version.split()[0]})
        except Exception:
            valid = False
    return valid, rows


def install_locked_requirements() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "--require-hashes", "-r", str(LOCK)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _writable_site_dir() -> Path:
    candidates: list[Path] = []
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        candidates.append(Path(sysconfig.get_paths()["purelib"]))
    else:
        for raw in site.getsitepackages():
            candidates.append(Path(raw))
        candidates.append(Path(site.getusersitepackages()))
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".sentinel-edge-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    raise RuntimeError("no_writable_site_packages_for_checkout_install")


def install_checkout_pth() -> Path:
    roots = _source_roots()
    if not roots:
        raise RuntimeError("no_declared_source_roots")
    site_dir = _writable_site_dir()
    target = site_dir / PTH_NAME
    # Executable .pth lines are processed during normal Python site startup.
    # Prepending the declared checkout roots guarantees that a stale editable
    # install elsewhere on the machine cannot shadow the checkout being judged.
    source_list = json.dumps([str(path) for path in roots])
    target.write_text(f"import sys; sys.path[0:0]={source_list}\n", encoding="utf-8", newline="\n")
    for legacy_name in LEGACY_PTH_NAMES:
        legacy = site_dir / legacy_name
        if legacy != target and legacy.is_file():
            try:
                legacy.unlink()
            except OSError:
                pass
    return target


def verify_checkout_import() -> dict[str, object]:
    code = (
        "from pathlib import Path; import sentinel_edge; "
        "print(Path(sentinel_edge.__file__).resolve())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    observed = completed.stdout.strip()
    expected_root = (ROOT / "src").resolve()
    valid = False
    try:
        valid = completed.returncode == 0 and Path(observed).resolve().is_relative_to(expected_root)
    except (OSError, ValueError):
        valid = False
    return {
        "valid": valid,
        "observed": observed or None,
        "expected_root": str(expected_root),
        "exit_code": completed.returncode,
        "stderr_tail": completed.stderr[-2000:],
    }


def _write_report(payload: dict[str, object]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    require_locked = os.environ.get("SENTINEL_SETUP_REQUIRE_LOCKED", "0") == "1"
    exact_before, exact_rows_before = exact_lock_state()
    compatible_before, compatible_rows_before = compatible_state()
    mode = "exact_locked_preinstalled" if exact_before else None
    pip_result: subprocess.CompletedProcess[str] | None = None

    if not exact_before:
        # In ordinary local mode, a compatible pre-provisioned environment is a
        # valid offline fallback.  Release preflight deliberately disables it.
        if compatible_before and not require_locked:
            mode = "compatible_preprovisioned"
        else:
            pip_result = install_locked_requirements()
            exact_after, exact_rows_after = exact_lock_state()
            if pip_result.returncode != 0 or not exact_after:
                payload = {
                    "schema": "sentinel-edge.setup-environment.v1",
                    "status": "fail",
                    "mode": "locked_install_failed",
                    "require_locked": require_locked,
                    "exact_before": exact_before,
                    "compatible_before": compatible_before,
                    "exact_requirements": exact_rows_after,
                    "pip_exit_code": pip_result.returncode,
                    "pip_stdout_tail": pip_result.stdout[-4000:],
                    "pip_stderr_tail": pip_result.stderr[-4000:],
                }
                _write_report(payload)
                print(json.dumps(payload, indent=2, sort_keys=True))
                return 2
            mode = "exact_locked_installed"
            exact_rows_before = exact_rows_after

    pth_path = install_checkout_pth()
    checkout_import = verify_checkout_import()
    if checkout_import["valid"] is not True:
        payload = {
            "schema": "sentinel-edge.setup-environment.v1",
            "status": "fail",
            "mode": mode,
            "require_locked": require_locked,
            "pth_path": str(pth_path),
            "checkout_import": checkout_import,
        }
        _write_report(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    exact_final, exact_rows_final = exact_lock_state()
    compatible_final, compatible_rows_final = compatible_state()
    payload = {
        "schema": "sentinel-edge.setup-environment.v1",
        "status": "pass",
        "mode": mode,
        "require_locked": require_locked,
        "exact_locked": exact_final,
        "compatible": compatible_final,
        "python": sys.version.split()[0],
        "pth_path": str(pth_path),
        "source_roots": [str(path) for path in _source_roots()],
        "checkout_import": checkout_import,
        "exact_requirements": exact_rows_final,
        "compatible_requirements": compatible_rows_final,
        "lock_file": LOCK.name,
        "hash_required_for_install": True,
    }
    _write_report(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
