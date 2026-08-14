from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def _text(path: str | Path) -> str | None:
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace').strip('\x00\n ')
    except OSError:
        return None


def _digest_if_file(path: Path) -> str | None:
    try:
        return sha256_file(path) if path.is_file() else None
    except OSError:
        return None


def _command(args: list[str]) -> dict[str, Any]:
    if not shutil.which(args[0]):
        return {'available': False, 'command': args, 'returncode': None, 'stdout': None}
    try:
        completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=3)
        return {'available': True, 'command': args, 'returncode': completed.returncode, 'stdout': completed.stdout.strip()[:4096]}
    except (OSError, subprocess.SubprocessError):
        return {'available': True, 'command': args, 'returncode': None, 'stdout': None}


def observe_host_trust() -> dict[str, Any]:
    kernel_path = Path('/boot') / f'vmlinuz-{platform.release()}'
    initramfs_candidates = sorted(Path('/boot').glob(f'initr*{platform.release()}*')) if Path('/boot').exists() else []
    root_mount = None
    mountinfo = _text('/proc/self/mountinfo') or ''
    for line in mountinfo.splitlines():
        fields = line.split()
        if len(fields) > 5 and fields[4] == '/':
            root_mount = line
            break
    vc_bootloader = _command(['vcgencmd', 'bootloader_version'])
    vc_config = _command(['vcgencmd', 'get_config', 'int'])
    lockdown = _text('/sys/kernel/security/lockdown')
    lsm = _text('/sys/kernel/security/lsm')
    secure_boot_evidence = {
        'raspberry_pi_bootloader': vc_bootloader,
        'raspberry_pi_config': vc_config,
        'uefi_secure_boot_variable_present': Path('/sys/firmware/efi/efivars').is_dir(),
        'kernel_lockdown': lockdown,
    }
    measured = any([
        vc_bootloader.get('stdout'), _digest_if_file(kernel_path), lockdown, _text('/proc/device-tree/model')
    ])
    secure_boot_proven = False
    trust_class = 'measured_partial' if measured else 'unmeasured'
    base = {
        'schema': 'sentinel-edge-host-trust-observation/1.0',
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'system': platform.system(),
        'machine': platform.machine(),
        'board_model': _text('/proc/device-tree/model'),
        'bootloader': vc_bootloader,
        'kernel': {
            'release': platform.release(),
            'proc_version_sha256': _digest_if_file(Path('/proc/version')),
            'image_path': str(kernel_path) if kernel_path.is_file() else None,
            'image_sha256': _digest_if_file(kernel_path),
            'lockdown': lockdown,
            'lsm': lsm,
        },
        'initramfs': [{'path': str(path), 'sha256': _digest_if_file(path)} for path in initramfs_candidates],
        'root_filesystem': {
            'mountinfo': root_mount,
            'mountinfo_sha256': sha256_bytes(root_mount.encode()) if root_mount else None,
            'dm_verity_observed': bool(root_mount and ('verity' in root_mount or '/dev/dm-' in root_mount)),
        },
        'firmware': {
            'device_tree_model_sha256': sha256_bytes((_text('/proc/device-tree/model') or '').encode()) if _text('/proc/device-tree/model') else None,
            'raspberry_pi_config_sha256': sha256_bytes((vc_config.get('stdout') or '').encode()) if vc_config.get('stdout') else None,
        },
        'secure_boot_evidence': secure_boot_evidence,
        'trust_class': trust_class,
        'secure_boot_proven': secure_boot_proven,
        'application_artifact_trust_separate': True,
        'privileged_host_compromise_not_covered': True,
        'judge_h0_secure_boot_required': False,
        'key_purpose_domains': ['boot-signing', 'release-signing', 'device-identity', 'backup-decryption'],
        'limitations': [
            'Application hashes and signatures do not protect against a compromised running kernel or privileged host.',
            'No customer-key Raspberry Pi secure-boot qualification is claimed.',
            'Unavailable platform evidence is reported as unavailable rather than inferred.',
        ],
    }
    return {**base, 'observation_digest': sha256_bytes(canonical_json_bytes(base))}


def evaluate_host_trust(observation: dict[str, Any], *, require_secure_boot: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    if observation.get('schema') != 'sentinel-edge-host-trust-observation/1.0':
        failures.append('unsupported_observation_schema')
    if observation.get('application_artifact_trust_separate') is not True:
        failures.append('application_and_host_trust_conflated')
    if observation.get('privileged_host_compromise_not_covered') is not True:
        failures.append('residual_host_risk_not_declared')
    domains = observation.get('key_purpose_domains', [])
    if len(domains) != len(set(domains)) or set(domains) != {'boot-signing', 'release-signing', 'device-identity', 'backup-decryption'}:
        failures.append('key_purpose_domains_not_separate')
    if require_secure_boot and observation.get('secure_boot_proven') is not True:
        failures.append('secure_boot_not_proven')
    return {
        'schema': 'sentinel-edge-host-trust-report/1.0',
        'observation_digest': observation.get('observation_digest'),
        'trust_class': observation.get('trust_class', 'unknown'),
        'secure_boot_proven': observation.get('secure_boot_proven', False),
        'require_secure_boot': require_secure_boot,
        'valid': not failures,
        'release_eligible': not failures and (not require_secure_boot or observation.get('secure_boot_proven') is True),
        'failures': failures,
        'residual_limitations': observation.get('limitations', []),
    }


def write_host_trust_report(output: str | Path, *, require_secure_boot: bool = False) -> Path:
    observation = observe_host_trust()
    report = evaluate_host_trust(observation, require_secure_boot=require_secure_boot)
    payload = {'observation': observation, 'evaluation': report}
    output = Path(output)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return output


def verify_host_trust_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    observation = payload.get('observation', {})
    base = {k: v for k, v in observation.items() if k != 'observation_digest'}
    failures: list[str] = []
    if sha256_bytes(canonical_json_bytes(base)) != observation.get('observation_digest'):
        failures.append('host_observation_digest_mismatch')
    expected = evaluate_host_trust(observation, require_secure_boot=payload.get('evaluation', {}).get('require_secure_boot', False))
    if expected != payload.get('evaluation'):
        failures.append('host_evaluation_mismatch')
    return {'valid': not failures, 'release_eligible': payload.get('evaluation', {}).get('release_eligible', False) and not failures, 'failures': failures, 'trust_class': observation.get('trust_class')}
