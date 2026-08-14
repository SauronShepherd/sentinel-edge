from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from sentinel_edge.domain.models import CapabilityState, HostObservation, HostQualificationReport
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip("\x00\n ")
    except (OSError, UnicodeError):
        return None


def _parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    text = _read_text(path)
    if not text:
        return {}
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _memory_mb() -> int:
    text = _read_text(Path("/proc/meminfo")) or ""
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            try:
                return int(line.split()[1]) // 1024
            except (IndexError, ValueError):
                return 0
    return 0


def _cpu_model() -> str | None:
    text = _read_text(Path("/proc/cpuinfo")) or ""
    candidates = []
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() in {"model name", "hardware", "processor"} and value.strip():
            candidates.append(value.strip())
    return candidates[0] if candidates else None


def _thermal() -> tuple[int, float | None]:
    values: list[float] = []
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp")):
        text = _read_text(path)
        if not text:
            continue
        try:
            value = float(text)
        except ValueError:
            continue
        if value > 1000:
            value /= 1000.0
        values.append(value)
    return len(values), max(values) if values else None


def _power_evidence() -> str:
    command = shutil.which("vcgencmd")
    if not command:
        return "unavailable"
    try:
        completed = subprocess.run(
            [command, "get_throttled"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    value = completed.stdout.strip()
    return value or "unavailable"


def observe_host() -> HostObservation:
    os_release = _parse_os_release()
    observed_files: dict[str, str] = {}
    for path in (
        Path("/etc/os-release"),
        Path("/proc/cpuinfo"),
        Path("/proc/meminfo"),
        Path("/proc/pressure/cpu"),
        Path("/proc/pressure/memory"),
        Path("/proc/pressure/io"),
    ):
        if path.is_file():
            try:
                observed_files[str(path)] = sha256_file(path)
            except OSError:
                pass
    board_model = _read_text(Path("/proc/device-tree/model"))
    boot_id = _read_text(Path("/proc/sys/kernel/random/boot_id"))
    thermal_count, maximum_temperature = _thermal()
    return HostObservation(
        system=platform.system(),
        machine=platform.machine(),
        kernel_release=platform.release(),
        os_id=os_release.get("ID"),
        os_version_id=os_release.get("VERSION_ID"),
        board_model=board_model,
        cpu_model=_cpu_model(),
        cpu_count=max(1, os.cpu_count() or 1),
        memory_mb=_memory_mb(),
        architecture_64bit=platform.architecture()[0] == "64bit",
        psi_available=all(Path(f"/proc/pressure/{name}").is_file() for name in ("cpu", "memory", "io")),
        cgroup_v2=Path("/sys/fs/cgroup/cgroup.controllers").is_file(),
        thermal_sensor_count=thermal_count,
        maximum_temperature_c=maximum_temperature,
        power_evidence=_power_evidence(),
        boot_id_sha256=sha256_bytes(boot_id.encode("utf-8")) if boot_id else None,
        observed_files=observed_files,
    )


def load_host_profile(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported host qualification profile schema")
    if not payload.get("profile_id"):
        raise ValueError("host qualification profile requires profile_id")
    return payload


def qualify_host(profile: dict[str, Any], observation: HostObservation | None = None) -> HostQualificationReport:
    observation = observation or observe_host()
    reasons: list[str] = []
    required_system = profile.get("required_system", "Linux")
    if observation.system != required_system:
        reasons.append("system_mismatch")
    allowed_machines = {str(value).lower() for value in profile.get("allowed_machines", ["aarch64", "arm64"])}
    if observation.machine.lower() not in allowed_machines:
        reasons.append("architecture_mismatch")
    board_patterns = [str(value).lower() for value in profile.get("board_model_contains", [])]
    board = (observation.board_model or "").lower()
    if board_patterns and not any(pattern in board for pattern in board_patterns):
        reasons.append("board_model_mismatch")
    if observation.cpu_count < int(profile.get("minimum_cpu_count", 1)):
        reasons.append("insufficient_cpu_count")
    if observation.memory_mb < int(profile.get("minimum_memory_mb", 0)):
        reasons.append("insufficient_memory")
    if profile.get("require_64bit", True) and not observation.architecture_64bit:
        reasons.append("not_64bit")
    if profile.get("require_psi", False) and not observation.psi_available:
        reasons.append("psi_unavailable")
    if profile.get("require_cgroup_v2", False) and not observation.cgroup_v2:
        reasons.append("cgroup_v2_unavailable")
    if profile.get("require_thermal_sensor", False) and observation.thermal_sensor_count == 0:
        reasons.append("thermal_evidence_unavailable")
    if profile.get("require_power_evidence", False) and observation.power_evidence == "unavailable":
        reasons.append("power_evidence_unavailable")
    max_temp = profile.get("maximum_temperature_c")
    if max_temp is not None and observation.maximum_temperature_c is not None:
        if observation.maximum_temperature_c > float(max_temp):
            reasons.append("temperature_above_profile_limit")
    elif max_temp is not None and profile.get("require_thermal_sensor", False):
        reasons.append("temperature_unobserved")
    if observation.power_evidence not in {"unavailable", "throttled=0x0"}:
        reasons.append("power_or_throttle_flag_present")

    profile_sha = sha256_bytes(canonical_json_bytes(profile))
    observation_sha = sha256_bytes(canonical_json_bytes(observation.model_dump(mode="json")))
    matched = not reasons
    return HostQualificationReport(
        profile_id=profile["profile_id"],
        profile_sha256=profile_sha,
        observation_sha256=observation_sha,
        state=CapabilityState.TARGET_QUALIFIED if matched else CapabilityState.FAILED,
        host_profile_match=matched,
        target_device_claim_allowed=matched,
        benchmark_claim_allowed=matched,
        reason_codes=tuple(sorted(set(reasons))) if reasons else ("host_profile_matched",),
        observation=observation,
    )
