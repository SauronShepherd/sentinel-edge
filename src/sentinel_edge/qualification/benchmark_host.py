from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes


def _read(path: str | Path) -> str | None:
    try: return Path(path).read_text(encoding='utf-8', errors='replace').strip()
    except OSError: return None


def observe_benchmark_host(*, provider_threads: int | None = None, process_affinity: list[int] | None = None) -> dict[str, Any]:
    governors = {}
    frequencies = {}
    for cpu in sorted(Path('/sys/devices/system/cpu').glob('cpu[0-9]*')):
        governor = _read(cpu / 'cpufreq/scaling_governor')
        frequency = _read(cpu / 'cpufreq/scaling_cur_freq')
        if governor: governors[cpu.name] = governor
        if frequency: frequencies[cpu.name] = frequency
    meminfo = _read('/proc/meminfo') or ''
    mem = {}
    for line in meminfo.splitlines():
        if line.startswith(('Cached:', 'Buffers:', 'MemAvailable:', 'Dirty:', 'Writeback:', 'SwapTotal:', 'SwapFree:')):
            key, rest = line.split(':', 1); mem[key] = rest.strip()
    # Preserve the contract shape on non-Linux development hosts. Missing
    # telemetry is explicit and cannot be mistaken for target qualification.
    for key in ('Cached', 'Buffers', 'MemAvailable', 'Dirty', 'Writeback', 'SwapTotal', 'SwapFree'):
        mem.setdefault(key, None)
    vmstat = _read('/proc/vmstat') or ''
    major_faults = None
    for line in vmstat.splitlines():
        if line.startswith('pgmajfault '):
            try: major_faults = int(line.split()[1])
            except (ValueError, IndexError): major_faults = None
    cpu_psi = _read('/proc/pressure/cpu')
    memory_psi = _read('/proc/pressure/memory')
    io_psi = _read('/proc/pressure/io')
    zram_devices = {}
    for device in sorted(Path('/sys/block').glob('zram*')):
        zram_devices[device.name] = {
            'disksize': _read(device / 'disksize'),
            'mem_used_total': (_read(device / 'mm_stat') or '').split()[2] if _read(device / 'mm_stat') else None,
        }
    load = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
    affinity = process_affinity or sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else []
    process_names: list[str] = []
    for proc in sorted(Path('/proc').glob('[0-9]*'))[:4096]:
        name = _read(proc / 'comm')
        if name:
            process_names.append(name)
    base = {
        'schema': 'sentinel-edge-benchmark-host-observation/1.0',
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'kernel_release': platform.release(),
        'machine': platform.machine(),
        'cpu_governors': governors,
        'cpu_frequencies_khz': frequencies,
        'process_affinity': affinity,
        'process_cpuset_effective': _read('/sys/fs/cgroup/cpuset.cpus.effective'),
        'process_cgroup': _read('/proc/self/cgroup'),
        'irq_affinity_default': _read('/proc/irq/default_smp_affinity'),
        'provider_threads': provider_threads,
        'load_average': list(load),
        'page_cache': mem,
        'major_faults_total': major_faults,
        'cpu_pressure': cpu_psi,
        'memory_pressure': memory_psi,
        'io_pressure': io_psi,
        'zram_devices': zram_devices,
        'background_process_count': len(process_names),
        'background_process_names': sorted(set(process_names))[:256],
        'background_service_evidence': 'bounded_proc_comm_snapshot',
    }
    return {**base, 'observation_digest': sha256_bytes(canonical_json_bytes(base))}


def evaluate_idle_noise(samples: list[dict[str, float]], *, max_load1: float, max_cpu_psi_avg10: float, max_dirty_kb: float, max_memory_psi_avg10: float = 0.0, max_io_psi_avg10: float = 0.0, max_writeback_kb: float = 0.0, max_major_fault_delta: float = 0.0) -> dict[str, Any]:
    reasons: list[str] = []
    if not samples:
        reasons.append('no_samples')
    for sample in samples:
        if sample.get('load1', 0) > max_load1: reasons.append('load_above_envelope')
        if sample.get('cpu_psi_avg10', 0) > max_cpu_psi_avg10: reasons.append('cpu_psi_above_envelope')
        if sample.get('dirty_kb', 0) > max_dirty_kb: reasons.append('dirty_pages_above_envelope')
        if sample.get('memory_psi_avg10', 0) > max_memory_psi_avg10: reasons.append('memory_psi_above_envelope')
        if sample.get('io_psi_avg10', 0) > max_io_psi_avg10: reasons.append('io_psi_above_envelope')
        if sample.get('writeback_kb', 0) > max_writeback_kb: reasons.append('writeback_above_envelope')
        if sample.get('major_fault_delta', 0) > max_major_fault_delta: reasons.append('major_faults_above_envelope')
    return {'schema': 'sentinel-edge-idle-noise-envelope/1.0', 'sample_count': len(samples), 'valid': not reasons, 'reason_codes': sorted(set(reasons)) or ['idle_noise_envelope_passed'], 'thresholds': {'max_load1': max_load1, 'max_cpu_psi_avg10': max_cpu_psi_avg10, 'max_dirty_kb': max_dirty_kb, 'max_memory_psi_avg10': max_memory_psi_avg10, 'max_io_psi_avg10': max_io_psi_avg10, 'max_writeback_kb': max_writeback_kb, 'max_major_fault_delta': max_major_fault_delta}}


def evaluate_network_isolation(evidence: dict[str, Any]) -> dict[str, Any]:
    mode = evidence.get('mode')
    below = mode in {'network_namespace', 'firewall'} and evidence.get('egress_probe_blocked') is True and evidence.get('misbehaving_adapter_blocked') is True
    failures = [] if below else ['below_application_network_denial_not_proven']
    return {'schema': 'sentinel-edge-benchmark-network-isolation/1.0', 'mode': mode, 'below_application_layer_proven': below, 'valid': below, 'failures': failures, 'evidence_digest': sha256_bytes(canonical_json_bytes(evidence))}
