from __future__ import annotations

import os
from pathlib import Path


def inspect_container_network(*, sys_class_net: Path = Path('/sys/class/net'), proc_route: Path = Path('/proc/net/route')) -> dict[str, object]:
    """Inspect the guest namespace used by the canonical Arm64 runner.

    Docker ``--network none`` creates a separate network namespace containing
    loopback only.  We validate that observable kernel state rather than relying
    solely on an application-layer socket guard.
    """
    declared_mode = os.environ.get('SENTINEL_ARM64_NETWORK_MODE')
    try:
        interfaces = sorted(path.name for path in sys_class_net.iterdir())
    except OSError:
        interfaces = []
    default_route_present = False
    try:
        lines = proc_route.read_text(encoding='utf-8').splitlines()[1:]
    except OSError:
        lines = []
    for line in lines:
        fields = line.split()
        if len(fields) >= 2 and fields[1] == '00000000':
            default_route_present = True
            break
    non_loopback = [name for name in interfaces if name != 'lo']
    valid = declared_mode == 'none' and not non_loopback and not default_route_present
    return {
        'schema': 'sentinel-edge.arm64-network-isolation.v1',
        'declared_mode': declared_mode,
        'namespace_interfaces': interfaces,
        'non_loopback_interfaces': non_loopback,
        'default_route_present': default_route_present,
        'below_application_layer_proven': valid,
        'valid': valid,
        'reason_codes': ['docker_network_none_namespace_verified'] if valid else [
            reason for reason, failed in (
                ('network_mode_not_none', declared_mode != 'none'),
                ('non_loopback_interface_present', bool(non_loopback)),
                ('default_route_present', default_route_present),
            ) if failed
        ],
    }
