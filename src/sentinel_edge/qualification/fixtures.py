from __future__ import annotations

import re
from pathlib import Path


_NETWORK_URI = re.compile(rb"(?:https?|rtsp|ftp)://", re.IGNORECASE)
_REQUIRED = (
    Path("scenarios/simultaneous-event.json"),
    Path("scenarios/benchmark-open-loop.json"),
    Path("camera/wildfire-camera-5fps-development.jsonl"),
    Path("models/wildfire-smoke-quality.manifest.json"),
    Path("sensors/earthquake-imu-chain-v1.signed.json"),
)


def verify_judge_fixture_bundle(root: str | Path) -> dict[str, object]:
    """Verify the bundled judge inputs are present and contain no network URI."""
    base = Path(root)
    missing: list[str] = []
    network_markers: list[str] = []
    for relative in _REQUIRED:
        path = base / relative
        if not path.is_file():
            missing.append(relative.as_posix())
            continue
        if _NETWORK_URI.search(path.read_bytes()):
            network_markers.append(relative.as_posix())
    return {
        "required_files": [item.as_posix() for item in _REQUIRED],
        "missing": missing,
        "network_markers": network_markers,
        "valid": not missing and not network_markers,
    }
