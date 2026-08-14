from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable

from packaging.utils import canonicalize_name, parse_wheel_filename

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def inspect_wheel(path: str | Path) -> dict[str, Any]:
    wheel = Path(path)
    failures: list[str] = []
    try:
        parsed_name, parsed_version, build, tags = parse_wheel_filename(wheel.name)
    except Exception:
        return {
            "path": wheel.name,
            "valid": False,
            "failures": ["invalid_wheel_filename"],
            "sha256": sha256_file(wheel) if wheel.is_file() else None,
            "bytes": wheel.stat().st_size if wheel.is_file() else None,
        }
    metadata_name = None
    metadata_version = None
    record_present = False
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                failures.append("unsafe_wheel_member_path")
            metadata_paths = [name for name in names if name.endswith(".dist-info/METADATA")]
            if len(metadata_paths) != 1:
                failures.append("wheel_metadata_member_count_invalid")
            else:
                text = archive.read(metadata_paths[0]).decode("utf-8", errors="replace")
                for line in text.splitlines():
                    if line.startswith("Name:"):
                        metadata_name = line.split(":", 1)[1].strip()
                    elif line.startswith("Version:"):
                        metadata_version = line.split(":", 1)[1].strip()
            record_present = any(name.endswith(".dist-info/RECORD") for name in names)
            if not record_present:
                failures.append("wheel_record_missing")
            bad = archive.testzip()
            if bad:
                failures.append("wheel_zip_crc_failure")
    except (OSError, zipfile.BadZipFile):
        failures.append("wheel_archive_invalid")
    if metadata_name and canonicalize_name(metadata_name) != canonicalize_name(str(parsed_name)):
        failures.append("wheel_name_metadata_mismatch")
    if metadata_version and metadata_version != str(parsed_version):
        failures.append("wheel_version_metadata_mismatch")
    base = {
        "path": wheel.name,
        "name": str(parsed_name),
        "canonical_name": canonicalize_name(str(parsed_name)),
        "version": str(parsed_version),
        "build": list(build) if build else None,
        "tags": sorted(str(tag) for tag in tags),
        "metadata_name": metadata_name,
        "metadata_version": metadata_version,
        "record_present": record_present,
        "sha256": sha256_file(wheel),
        "bytes": wheel.stat().st_size,
        "failures": sorted(set(failures)),
    }
    return {**base, "valid": not failures, "entry_digest": sha256_bytes(canonical_json_bytes(base))}


def build_wheelhouse_manifest(directory: str | Path, output: str | Path | None = None) -> dict[str, Any]:
    root = Path(directory).resolve()
    entries = [inspect_wheel(path) for path in sorted(root.glob("*.whl"))]
    base = {
        "schema": "sentinel-edge-wheelhouse-manifest/1.0",
        "directory_name": root.name,
        "entries": entries,
        "wheel_count": len(entries),
        "valid": bool(entries) and all(item.get("valid") for item in entries),
        "limitations": [
            "A manifest proves only the wheel files present in this directory.",
            "Platform compatibility and complete lock closure are evaluated separately.",
        ],
    }
    payload = {**base, "manifest_digest": sha256_bytes(canonical_json_bytes(base))}
    if output:
        Path(output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _lock_requirements(lock: dict[str, Any]) -> dict[str, str]:
    return {
        canonicalize_name(item["name"]): str(item["version"])
        for item in lock.get("resolved", [])
        if item.get("state") == "resolved" and item.get("version")
    }


def verify_wheelhouse(
    lock_path: str | Path,
    wheelhouse: str | Path,
    *,
    compatible_tags: Iterable[str] | None = None,
    install_rehearsal: bool = False,
) -> dict[str, Any]:
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    manifest = build_wheelhouse_manifest(wheelhouse)
    required = _lock_requirements(lock)
    entries = manifest["entries"]
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in entries:
        by_name.setdefault(item.get("canonical_name", ""), []).append(item)
    tags = set(compatible_tags or [])
    missing: list[str] = []
    wrong_version: list[str] = []
    incompatible: list[str] = []
    for name, version in sorted(required.items()):
        candidates = by_name.get(name, [])
        if not candidates:
            missing.append(f"{name}=={version}")
            continue
        exact = [item for item in candidates if item.get("version") == version and item.get("valid")]
        if not exact:
            wrong_version.append(f"{name}=={version}")
            continue
        if tags and not any(tags.intersection(item.get("tags", [])) for item in exact):
            incompatible.append(f"{name}=={version}")
    unexpected = sorted(
        f"{item.get('canonical_name')}=={item.get('version')}"
        for item in entries
        if item.get("canonical_name") not in required
    )
    rehearsal: dict[str, Any] = {"requested": install_rehearsal, "performed": False, "success": False}
    if install_rehearsal and not missing and not wrong_version and not incompatible and manifest["valid"]:
        requirements_lines = [
            f"{name}=={version} --hash=sha256:{next(item['sha256'] for item in by_name[name] if item.get('version') == version and item.get('valid'))}"
            for name, version in sorted(required.items())
        ]
        with tempfile.TemporaryDirectory(prefix="sentinel-wheelhouse-rehearsal-") as temp:
            temp_path = Path(temp)
            req = temp_path / "requirements.txt"
            target = temp_path / "site-packages"
            req.write_text("\n".join(requirements_lines) + "\n", encoding="utf-8")
            env = dict(os.environ)
            env.update({"PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONNOUSERSITE": "1"})
            completed = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-index", "--require-hashes", "--no-deps", "--find-links", str(Path(wheelhouse).resolve()), "--target", str(target), "-r", str(req)],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
                env=env,
            )
            rehearsal = {
                "requested": True,
                "performed": True,
                "success": completed.returncode == 0,
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
                "network_disabled_by_pip": True,
                "installed_file_count": sum(1 for path in target.rglob("*") if path.is_file()),
            }
    failures: list[str] = []
    if not manifest["valid"]:
        failures.append("wheelhouse_manifest_invalid_or_empty")
    if missing:
        failures.append("locked_wheels_missing")
    if wrong_version:
        failures.append("locked_wheel_version_mismatch")
    if incompatible:
        failures.append("locked_wheels_incompatible_with_target_tags")
    if install_rehearsal and not rehearsal.get("success"):
        failures.append("offline_install_rehearsal_failed")
    base = {
        "schema": "sentinel-edge-wheelhouse-verification/1.0",
        "lock_sha256": sha256_file(lock_path),
        "manifest": manifest,
        "required_count": len(required),
        "missing": missing,
        "wrong_version": wrong_version,
        "incompatible": incompatible,
        "unexpected": unexpected,
        "install_rehearsal": rehearsal,
        "complete": not failures,
        "release_eligible": not failures and install_rehearsal,
        "failures": failures,
        "limitations": [
            "OS packages, firmware and dynamically loaded native libraries are outside this Python wheelhouse.",
            "Release eligibility requires a successful no-index installation rehearsal for the exact lock.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def verify_wheelhouse_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    claimed = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    failures = []
    if sha256_bytes(canonical_json_bytes(base)) != claimed:
        failures.append("wheelhouse_report_digest_mismatch")
    if payload.get("schema") != "sentinel-edge-wheelhouse-verification/1.0":
        failures.append("unsupported_wheelhouse_report_schema")
    return {"valid": not failures, "release_eligible": payload.get("release_eligible", False) and not failures, "failures": failures}


def _record_hash(data: bytes) -> str:
    import base64
    digest = base64.urlsafe_b64encode(__import__("hashlib").sha256(data).digest()).decode("ascii").rstrip("=")
    return f"sha256={digest}"


def mirror_installed_distribution(name: str, version: str, output_dir: str | Path) -> Path:
    """Repack one installed distribution into a deterministic wheel for the current platform.

    This is a capture of the installed environment, not the publisher's original wheel.
    """
    from importlib import metadata

    dist = metadata.distribution(name)
    if dist.version != version:
        raise ValueError(f"installed version mismatch for {name}: {dist.version} != {version}")
    files = list(dist.files or [])
    metadata_members = [f for f in files if str(f).endswith(".dist-info/METADATA")]
    if len(metadata_members) != 1:
        raise ValueError(f"cannot identify one dist-info directory for {name}")
    dist_info = Path(str(metadata_members[0])).parent.as_posix()
    wheel_metadata_path = dist.locate_file(Path(dist_info) / "WHEEL")
    if not wheel_metadata_path.is_file():
        raise ValueError(f"WHEEL metadata missing for {name}")
    tags = [line.split(":", 1)[1].strip() for line in wheel_metadata_path.read_text(encoding="utf-8").splitlines() if line.startswith("Tag:")]
    if not tags:
        raise ValueError(f"wheel tag missing for {name}")
    tag = tags[0]
    safe_name = (dist.metadata.get("Name") or name).replace("-", "_")
    safe_version = version.replace("-", "_")
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    wheel_path = output / f"{safe_name}-{safe_version}-{tag}.whl"
    members: dict[str, bytes] = {}
    site_root = Path(dist.locate_file("")).resolve()
    for file in files:
        rel = Path(str(file))
        if rel.is_absolute() or ".." in rel.parts or rel.suffix == ".pyc" or "__pycache__" in rel.parts:
            continue
        source = Path(dist.locate_file(file)).resolve()
        try:
            source.relative_to(site_root)
        except ValueError:
            continue
        if not source.is_file():
            continue
        member = rel.as_posix()
        if member == f"{dist_info}/RECORD":
            continue
        members[member] = source.read_bytes()
    record_path = f"{dist_info}/RECORD"
    record_lines = [f"{member},{_record_hash(data)},{len(data)}" for member, data in sorted(members.items())]
    record_lines.append(f"{record_path},,")
    members[record_path] = ("\n".join(record_lines) + "\n").encode("utf-8")
    timestamp = (2023, 11, 14, 22, 13, 20)
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as archive:
        for member, data in sorted(members.items()):
            info = zipfile.ZipInfo(member, date_time=timestamp)
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    inspected = inspect_wheel(wheel_path)
    if not inspected.get("valid"):
        wheel_path.unlink(missing_ok=True)
        raise ValueError(f"generated wheel invalid for {name}: {inspected.get('failures')}")
    return wheel_path


def mirror_installed_resolution(lock_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for item in lock.get("resolved", []):
        if item.get("state") != "resolved" or not item.get("version"):
            failures.append({"name": str(item.get("name")), "reason": "lock_entry_unresolved"})
            continue
        try:
            path = mirror_installed_distribution(str(item["name"]), str(item["version"]), output)
            generated.append(inspect_wheel(path))
        except (ValueError, OSError) as exc:
            failures.append({"name": str(item.get("name")), "reason": str(exc)})
    return {
        "schema": "sentinel-edge-wheelhouse-capture/1.0",
        "lock_sha256": sha256_file(lock_path),
        "generated": generated,
        "failures": failures,
        "complete": not failures and len(generated) == len(_lock_requirements(lock)),
        "capture_kind": "deterministic_repack_of_installed_distribution",
        "publisher_original_wheels": False,
        "limitations": [
            "Captured wheels are deterministic repacks of installed distributions, not publisher-signed original archives.",
            "The wheelhouse is valid only for the Python ABI and platform tags recorded in each wheel.",
        ],
    }


def verify_target_wheelhouse(
    lock_path: str | Path,
    acquisition_manifest_path: str | Path,
    *,
    root: str | Path,
    required_target_tags: Iterable[str],
) -> dict[str, Any]:
    """Verify publisher-origin target wheel evidence without downloading anything.

    The acquisition manifest is evidence, not a download instruction. Every local file is
    verified against the declared digest and every locked package must have an exact target-
    compatible entry. A target installation rehearsal is a separate signed receipt.
    """
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    manifest = json.loads(Path(acquisition_manifest_path).read_text(encoding="utf-8"))
    root_path = Path(root).resolve()
    required = _lock_requirements(lock)
    tags = set(required_target_tags)
    failures: list[str] = []
    if manifest.get("schema") != "sentinel-edge-target-wheel-acquisition/1.0":
        failures.append("target_wheel_manifest_schema_mismatch")
    entries = manifest.get("entries", [])
    by_name: dict[str, list[dict[str, Any]]] = {}
    inspected: list[dict[str, Any]] = []
    for raw in entries:
        name = canonicalize_name(str(raw.get("name", "")))
        version = str(raw.get("version", ""))
        path_value = str(raw.get("path", ""))
        item_failures: list[str] = []
        if raw.get("origin_kind") not in {"publisher_index", "publisher_release", "publisher_attestation"}:
            item_failures.append("publisher_origin_kind_invalid")
        if raw.get("publisher_origin_proven") is not True:
            item_failures.append("publisher_origin_not_proven")
        if not raw.get("origin_url"):
            item_failures.append("origin_url_missing")
        target_entry_tags = set(str(value) for value in raw.get("tags", []))
        if not tags.intersection(target_entry_tags):
            item_failures.append("target_tag_incompatible")
        observed_sha = None
        observed_bytes = None
        if path_value:
            path = (root_path / path_value).resolve()
            try:
                path.relative_to(root_path)
            except ValueError:
                item_failures.append("wheel_path_outside_root")
            else:
                if not path.is_file():
                    item_failures.append("wheel_file_missing")
                else:
                    observed_sha = sha256_file(path)
                    observed_bytes = path.stat().st_size
                    if observed_sha != raw.get("sha256"):
                        item_failures.append("wheel_digest_mismatch")
                    if observed_bytes != raw.get("bytes"):
                        item_failures.append("wheel_size_mismatch")
                    wheel_info = inspect_wheel(path)
                    if not wheel_info.get("valid"):
                        item_failures.append("wheel_archive_invalid")
                    if wheel_info.get("canonical_name") != name or wheel_info.get("version") != version:
                        item_failures.append("wheel_identity_mismatch")
        else:
            item_failures.append("wheel_path_missing")
        record = {
            "name": name,
            "version": version,
            "path": path_value,
            "declared_sha256": raw.get("sha256"),
            "observed_sha256": observed_sha,
            "declared_bytes": raw.get("bytes"),
            "observed_bytes": observed_bytes,
            "origin_kind": raw.get("origin_kind"),
            "origin_url": raw.get("origin_url"),
            "publisher_origin_proven": raw.get("publisher_origin_proven") is True,
            "tags": sorted(target_entry_tags),
            "valid": not item_failures,
            "failures": sorted(set(item_failures)),
        }
        inspected.append(record)
        by_name.setdefault(name, []).append(record)
    missing: list[str] = []
    invalid: list[str] = []
    for name, version in sorted(required.items()):
        exact = [item for item in by_name.get(name, []) if item["version"] == version]
        if not exact:
            missing.append(f"{name}=={version}")
        elif not any(item["valid"] for item in exact):
            invalid.append(f"{name}=={version}")
    unexpected = sorted(
        f"{item['name']}=={item['version']}"
        for item in inspected
        if item["name"] not in required
    )
    rehearsal = manifest.get("installation_rehearsal", {})
    rehearsal_valid = (
        rehearsal.get("success") is True
        and rehearsal.get("no_index") is True
        and rehearsal.get("require_hashes") is True
        and rehearsal.get("machine") in {"aarch64", "arm64"}
        and rehearsal.get("installed_lock_sha256") == sha256_file(lock_path)
    )
    if missing:
        failures.append("target_locked_wheels_missing")
    if invalid:
        failures.append("target_locked_wheels_invalid")
    if unexpected:
        failures.append("target_wheelhouse_contains_unlocked_packages")
    if not rehearsal_valid:
        failures.append("target_offline_install_rehearsal_missing_or_invalid")
    base = {
        "schema": "sentinel-edge-target-wheelhouse-report/1.0",
        "target_platform": manifest.get("target_platform"),
        "required_target_tags": sorted(tags),
        "lock_sha256": sha256_file(lock_path),
        "acquisition_manifest_sha256": sha256_file(acquisition_manifest_path),
        "required_count": len(required),
        "entries": inspected,
        "missing": missing,
        "invalid": invalid,
        "unexpected": unexpected,
        "installation_rehearsal": rehearsal,
        "target_platform_complete": not failures,
        "release_eligible": not failures,
        "failures": sorted(set(failures)),
        "limitations": [
            "The verifier does not download wheels and trusts no URL without a local hash-bound artifact.",
            "Publisher origin is a declared evidence field and requires independent provenance outside this verifier.",
            "A current-platform wheelhouse cannot qualify an Arm64 target by tag substitution.",
        ],
    }
    return {**base, "report_digest": sha256_bytes(canonical_json_bytes(base))}


def verify_target_wheelhouse_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    failures: list[str] = []
    if payload.get("schema") != "sentinel-edge-target-wheelhouse-report/1.0":
        failures.append("target_wheelhouse_report_schema_mismatch")
    claimed = payload.get("report_digest")
    base = {key: value for key, value in payload.items() if key != "report_digest"}
    if claimed != sha256_bytes(canonical_json_bytes(base)):
        failures.append("target_wheelhouse_report_digest_mismatch")
    if payload.get("target_platform_complete") and payload.get("failures"):
        failures.append("target_wheelhouse_complete_with_failures")
    return {
        "valid": not failures,
        "release_eligible": bool(payload.get("release_eligible")) and not failures,
        "target_platform_complete": bool(payload.get("target_platform_complete")) and not failures,
        "failures": failures,
    }
